# engine/weather/providers/metar_provider.py — v1.1.0
# METAR provider (ASOS observations) via AviationWeather.gov.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class MetarProvider:
    """
    Fetches METAR/ASOS observations for a given station using AviationWeather.gov API.
    """

    BASE_URL = "https://aviationweather.gov/api/data/metar"

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

        raise RuntimeError(f"METAR request failed after retries: {url}")

    async def fetch_metar(self, station_id: str) -> Dict[str, Any]:
        """
        Fetch latest METAR for a station.
        """
        params = {
            "ids": station_id,
            "format": "json",
        }
        return await self._request_with_retries(self.BASE_URL, params=params)
