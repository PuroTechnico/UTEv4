# engine/weather/discovery/station_discovery.py — v1.0.0
# Smart Discovery: NOAA station list for a gridpoint

from typing import Dict, Any

from engine.weather.providers.noaa_station_provider import NoaaStationProvider


class StationDiscovery:
    """
    Discovers ASOS/METAR stations for a gridpoint.
    Cached because station lists rarely change.
    """

    def __init__(self, provider: NoaaStationProvider):
        self._provider = provider
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get_stations(self, stations_url: str) -> Dict[str, Any]:
        if stations_url in self._cache:
            return self._cache[stations_url]

        data = await self._provider.fetch_stations(stations_url)
        self._cache[stations_url] = data
        return data
