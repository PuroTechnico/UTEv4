# engine/weather/builder/weather_snapshot_builder.py — v1.1.0
# Async WeatherSnapshotBuilder — fuses providers + discovery into a WeatherSnapshot.

from typing import Dict, Any, Optional, List

from engine.weather.models.weather_market import WeatherMarket
from engine.weather.models.weather_snapshot import WeatherSnapshot
from engine.weather.models.weather_observation import WeatherObservation
from engine.weather.models.weather_forecast import WeatherForecast
from engine.weather.models.weather_alerts import WeatherAlerts
from engine.weather.models.weather_station import WeatherStation

from engine.weather.providers.noaa_cli_provider import NoaaCliProvider
from engine.weather.providers.noaa_points_provider import NoaaPointsProvider
from engine.weather.providers.noaa_forecast_provider import NoaaForecastProvider
from engine.weather.providers.noaa_station_provider import NoaaStationProvider
from engine.weather.providers.noaa_alerts_provider import NoaaAlertsProvider
from engine.weather.providers.metar_provider import MetarProvider

from engine.weather.discovery.points_discovery import PointsDiscovery
from engine.weather.discovery.station_discovery import StationDiscovery
from engine.weather.discovery.wfo_discovery import WfoDiscovery
from engine.weather.discovery.cli_discovery import CliDiscovery


class WeatherSnapshotBuilder:
    """
    Builds a fully fused WeatherSnapshot for a given WeatherMarket.

    Responsibilities:
      - Use discovery to resolve:
          • gridpoints
          • stations
          • WFO / alerts context
          • CLI settlement URL
      - Use providers to fetch:
          • METAR observation
          • hourly forecast
          • alerts
          • station metadata
          • CLI settlement data
      - Normalize into:
          • WeatherObservation
          • WeatherForecast
          • WeatherAlerts
          • WeatherStation
          • WeatherSnapshot
    """

    def __init__(
        self,
        providers: Dict[str, Any],
        discovery: Dict[str, Any],
    ):
        # Providers
        self._cli: NoaaCliProvider = providers["cli"]
        self._points: NoaaPointsProvider = providers["points"]
        self._forecast: NoaaForecastProvider = providers["forecast"]
        self._station: NoaaStationProvider = providers["station"]
        self._alerts: NoaaAlertsProvider = providers["alerts"]
        self._metar: MetarProvider = providers["metar"]

        # Discovery
        self._points_discovery: PointsDiscovery = discovery["points"]
        self._station_discovery: StationDiscovery = discovery["station"]
        self._wfo_discovery: WfoDiscovery = discovery["wfo"]
        self._cli_discovery: CliDiscovery = discovery["cli"]

    async def build_snapshot(self, market: WeatherMarket) -> WeatherSnapshot:
        """
        Main entrypoint: build a WeatherSnapshot for a given market.

        High‑level flow:
          1. Discover gridpoint metadata (points)
          2. Discover stations + WFO
          3. Fetch METAR for primary station
          4. Fetch hourly forecast
          5. Fetch alerts
          6. Discover + fetch CLI settlement (if available)
          7. Normalize into models and return WeatherSnapshot
        """
        # 1. Discover gridpoints
        points_data = await self._points_discovery.get_points(market.lat, market.lon)

        forecast_hourly_url = self._extract_forecast_hourly_url(points_data)
        stations_url = self._extract_stations_url(points_data)

        # 2. Discover stations + WFO
        stations_data = await self._station_discovery.get_stations(stations_url)
        wfo_data = await self._wfo_discovery.get_wfo(stations_url)

        primary_station_id = self._select_primary_station_id(stations_data)

        # 3. Fetch METAR
        observation = await self._build_observation(primary_station_id)

        # 4. Fetch hourly forecast
        forecast = await self._build_forecast(forecast_hourly_url)

        # 5. Fetch alerts
        alerts = await self._build_alerts(points_data, wfo_data)

        # 6. Discover + fetch CLI settlement
        cli_url = await self._cli_discovery.get_cli_url(market.ticker)
        settlement = await self._build_settlement(cli_url) if cli_url else None

        # 7. Build station model
        station = self._build_station(primary_station_id, stations_data)

        # 8. Build snapshot
        snapshot = WeatherSnapshot(
            observation=observation,
            forecast=forecast,
            alerts=alerts,
            station=station,
            settlement=settlement,
        )

        return snapshot

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _extract_forecast_hourly_url(self, points_data: Dict[str, Any]) -> str:
        """
        Extract forecastHourly URL from /points response.
        Expected shape: points_data["properties"]["forecastHourly"]
        """
        props = points_data.get("properties", {}) if isinstance(points_data, dict) else {}
        url = props.get("forecastHourly", "")
        return url or ""

    def _extract_stations_url(self, points_data: Dict[str, Any]) -> str:
        """
        Extract stations URL from /points response.
        Expected shape: points_data["properties"]["observationStations"]
        """
        props = points_data.get("properties", {}) if isinstance(points_data, dict) else {}
        url = props.get("observationStations", "")
        return url or ""

    def _select_primary_station_id(self, stations_data: Dict[str, Any]) -> Optional[str]:
        """
        Select primary station ID from station list.

        Strategy:
          - Use first station in features list.
          - Prefer stations that look like ASOS/AWOS if metadata is present.
        """
        if not isinstance(stations_data, dict):
            return None

        features: List[Dict[str, Any]] = stations_data.get("features", [])
        if not features:
            return None

        # Simple strategy: first feature's stationIdentifier
        first = features[0]
        props = first.get("properties", {})
        station_id = props.get("stationIdentifier") or props.get("id")

        # Fallback: try to parse from full id (e.g., "https://api.weather.gov/stations/KSEA")
        if not station_id:
            full_id = props.get("@id") or first.get("id")
            if isinstance(full_id, str) and "/" in full_id:
                station_id = full_id.rsplit("/", 1)[-1]

        return station_id

    async def _build_observation(self, station_id: Optional[str]) -> Optional[WeatherObservation]:
        """
        Build WeatherObservation from METAR provider (AviationWeather.gov).

        Expected METAR shape (simplified):
          {
            "metar": [
              {
                "temp": { "value": 12.0, "unit": "C" } or "temp": 12.0,
                "dewpoint": { "value": 10.0, "unit": "C" } or "dewpoint": 10.0,
                "windSpeed": { "value": 5.0, "unit": "KT" } or "windSpeed": 5.0,
                "obsTime": "2024-01-01T12:00:00Z"
              },
              ...
            ]
          }

        We normalize to:
          - temp_f
          - dewpoint_f
          - wind_mph
          - timestamp (ISO string)
        """
        if not station_id:
            return None

        raw = await self._metar.fetch_metar(station_id)
        if not isinstance(raw, dict):
            return None

        metars = raw.get("metar") or raw.get("data") or []
        if not metars:
            return None

        m = metars[0]

        def _extract_value(field: str) -> Optional[float]:
            v = m.get(field)
            if isinstance(v, dict):
                return v.get("value")
            if isinstance(v, (int, float)):
                return float(v)
            return None

        temp_c = _extract_value("temp") or _extract_value("temperature")  # in C if provided
        dew_c = _extract_value("dewpoint")
        wind = _extract_value("windSpeed") or _extract_value("wind_speed")  # assume knots

        # Convert C → F if present
        def c_to_f(x: Optional[float]) -> Optional[float]:
            if x is None:
                return None
            return x * 9.0 / 5.0 + 32.0

        temp_f = c_to_f(temp_c)
        dewpoint_f = c_to_f(dew_c)

        # Convert knots → mph if present
        def kt_to_mph(x: Optional[float]) -> Optional[float]:
            if x is None:
                return None
            return x * 1.15078

        wind_mph = kt_to_mph(wind)

        timestamp = (
            m.get("obsTime")
            or m.get("time")
            or m.get("observed")
            or ""
        )

        return WeatherObservation(
            temp_f=temp_f if temp_f is not None else 0.0,
            dewpoint_f=dewpoint_f if dewpoint_f is not None else 0.0,
            wind_mph=wind_mph if wind_mph is not None else 0.0,
            timestamp=str(timestamp),
        )

    async def _build_forecast(self, forecast_hourly_url: str) -> Optional[WeatherForecast]:
        """
        Build WeatherForecast from NOAA hourly forecast.

        Expected shape:
          {
            "properties": {
              "periods": [ ... ]
            }
          }

        We pass periods through as-is into WeatherForecast.hourly_periods.
        """
        if not forecast_hourly_url:
            return None

        raw = await self._forecast.fetch_hourly_forecast(forecast_hourly_url)
        if not isinstance(raw, dict):
            return None

        props = raw.get("properties", {})
        periods = props.get("periods", [])
        if not isinstance(periods, list):
            periods = []

        return WeatherForecast(hourly_periods=periods)

    async def _build_alerts(
        self,
        points_data: Dict[str, Any],
        wfo_data: Dict[str, Any],
    ) -> Optional[WeatherAlerts]:
        """
        Build WeatherAlerts from NOAA alerts API.

        Strategy:
          - Prefer querying by point (lat,lon) from points_data geometry.
          - Fallback to WFO/zone if needed later.
        """
        # Try to derive point "lat,lon" from points_data geometry
        point_str: Optional[str] = None
        if isinstance(points_data, dict):
            geom = points_data.get("geometry", {})
            coords = geom.get("coordinates")
            if (
                isinstance(coords, (list, tuple))
                and len(coords) >= 2
                and isinstance(coords[0], (int, float))
                and isinstance(coords[1], (int, float))
            ):
                lon, lat = coords[0], coords[1]
                point_str = f"{lat},{lon}"

        raw = await self._alerts.fetch_alerts(point=point_str) if point_str else await self._alerts.fetch_alerts()

        if not isinstance(raw, dict):
            return None

        # NOAA alerts typically:
        # {
        #   "features": [ { ... }, ... ]
        # }
        alerts_list = raw.get("features", [])
        if not isinstance(alerts_list, list):
            alerts_list = []

        return WeatherAlerts(alerts=alerts_list)

    async def _build_settlement(self, cli_url: str) -> Dict[str, Any]:
        """
        Build settlement payload from CLI provider.

        For now, we return the raw CLI JSON; higher layers can interpret it.
        """
        if not cli_url:
            return {}

        raw = await self._cli.fetch_cli(cli_url)
        if not isinstance(raw, dict):
            return {}

        return raw

    def _build_station(
        self,
        station_id: Optional[str],
        stations_data: Dict[str, Any],
    ) -> Optional[WeatherStation]:
        """
        Build WeatherStation model from station metadata.

        Expected stations_data shape (NOAA stations collection):
          {
            "features": [
              {
                "properties": {
                  "stationIdentifier": "KSEA",
                  "name": "Seattle-Tacoma International Airport",
                  ...
                },
                "geometry": {
                  "coordinates": [lon, lat, ...]
                }
              },
              ...
            ]
          }
        """
        if not station_id or not isinstance(stations_data, dict):
            return None

        features: List[Dict[str, Any]] = stations_data.get("features", [])
        if not features:
            return None

        target_feature: Optional[Dict[str, Any]] = None

        for f in features:
            props = f.get("properties", {})
            sid = props.get("stationIdentifier")
            if not sid:
                # Try to parse from id if needed
                full_id = props.get("@id") or f.get("id")
                if isinstance(full_id, str) and "/" in full_id:
                    sid = full_id.rsplit("/", 1)[-1]
            if sid == station_id:
                target_feature = f
                break

        if target_feature is None:
            # Fallback: first feature
            target_feature = features[0]

        props = target_feature.get("properties", {})
        geom = target_feature.get("geometry", {})

        name = props.get("name") or station_id
        coords = geom.get("coordinates") or [0.0, 0.0]
        if isinstance(coords, (list, tuple)) and len(coords) >= 2:
            lon, lat = coords[0], coords[1]
        else:
            lon, lat = 0.0, 0.0

        return WeatherStation(
            station_id=station_id,
            name=name,
            lat=float(lat),
            lon=float(lon),
        )

