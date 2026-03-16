# engine/weather/discovery/wfo_discovery.py — v1.0.0
# Smart Discovery: WFO office + zone metadata

from typing import Dict, Any

from engine.weather.providers.noaa_station_provider import NoaaStationProvider


class WfoDiscovery:
    """
    Discovers WFO (Weather Forecast Office) metadata.
    NOAA embeds WFO info inside station/gridpoint metadata.
    Cached because WFO zones are static.
    """

    def __init__(self, provider: NoaaStationProvider):
        self._provider = provider
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_wfo(self, stations_url: str) -> Dict[str, Any]:
        if stations_url in self._cache:
            return self._cache[stations_url]

        # WFO metadata is embedded in the station list response
        data = await self._provider.fetch_stations(stations_url)
        self._cache[stations_url] = data
        return data
