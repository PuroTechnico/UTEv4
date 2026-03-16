# engine/weather/providers/noaa_points_provider.py — v1.1.0
# NOAA /points endpoint provider.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class NoaaPointsProvider:
    """
    Wraps NOAA /points/{lat},{lon} endpoint.
    """

    BASE_URL = "https://api.weather.gov"

    def __init__(self, http: WeatherHttpClient):
        self._http = http

    async def _request_with_retries(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        for attempt in range(3):
            try:
                resp = await self._http.client.get(url, params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(1.5)
                    continue
                if resp.status_code == 503:
                    await asyncio.sleep(2.5)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.RequestError:
                await asyncio.sleep(0.5 * (2 ** attempt))

        raise RuntimeError(f"NOAA points request failed after retries: {url}")

    async def fetch_points(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch gridpoint metadata for a given lat/lon.
        """
        url = f"{self.BASE_URL}/points/{lat},{lon}"
        return await self._request_with_retries(url)
