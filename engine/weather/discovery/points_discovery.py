# engine/weather/discovery/points_discovery.py — v1.0.0
# Smart Discovery: NOAA /points/{lat},{lon} metadata

from typing import Dict, Any, Tuple

from engine.weather.providers.noaa_points_provider import NoaaPointsProvider


class PointsDiscovery:
    """
    Discovers NOAA gridpoint metadata for a given lat/lon.
    Uses caching because gridpoints never change.
    """

    def __init__(self, provider: NoaaPointsProvider):
        self._provider = provider
        self._cache: Dict[Tuple[float, float], Dict[str, Any]] = {}

    async def get_points(self, lat: float, lon: float) -> Dict[str, Any]:
        key = (round(lat, 4), round(lon, 4))

        if key in self._cache:
            return self._cache[key]

        data = await self._provider.fetch_points(lat, lon)
        self._cache[key] = data
        return data
