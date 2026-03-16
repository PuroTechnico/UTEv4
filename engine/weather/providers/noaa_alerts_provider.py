# engine/weather/providers/noaa_alerts_provider.py — v1.1.0
# NOAA alerts provider.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class NoaaAlertsProvider:
    """
    Wraps NOAA alerts API for a given zone or point.
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

        raise RuntimeError(f"NOAA alerts request failed after retries: {url}")

    async def fetch_alerts(
        self,
        zone: Optional[str] = None,
        point: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch active alerts for a given zone or point.
        """
        params: Dict[str, Any] = {}
        if zone:
            params["zone"] = zone
        if point:
            params["point"] = point

        url = f"{self.BASE_URL}/alerts/active"
        return await self._request_with_retries(url, params=params or None)
