# engine/weather/providers/noaa_station_provider.py — v1.1.0
# NOAA stations provider.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class NoaaStationProvider:
    """
    Wraps NOAA stations endpoints (e.g., /gridpoints/.../stations).
    """

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

        raise RuntimeError(f"NOAA stations request failed after retries: {url}")

    async def fetch_stations(self, stations_url: str) -> Dict[str, Any]:
        """
        Fetch station list for a given gridpoint.
        """
        return await self._request_with_retries(stations_url)
