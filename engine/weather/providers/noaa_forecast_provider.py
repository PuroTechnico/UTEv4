# engine/weather/providers/noaa_forecast_provider.py — v1.1.0
# NOAA gridpoint forecast provider.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class NoaaForecastProvider:
    """
    Wraps NOAA gridpoint forecast endpoints.
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

        raise RuntimeError(f"NOAA forecast request failed after retries: {url}")

    async def fetch_hourly_forecast(self, forecast_hourly_url: str) -> Dict[str, Any]:
        """
        Fetch hourly forecast JSON from a forecastHourly URL.
        """
        return await self._request_with_retries(forecast_hourly_url)
