# engine/weather/providers/noaa_cli_provider.py — v1.1.0
# NOAA climate (CLI) provider for settlement.

import asyncio
from typing import Any, Dict, Optional

import httpx

from engine.weather.http_client import WeatherHttpClient


class NoaaCliProvider:
    """
    Fetches daily climate (CLI) data used for settlement.
    Typically via pre‑mapped CLI URLs from taxonomy.
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

        raise RuntimeError(f"NOAA CLI request failed after retries: {url}")

    async def fetch_cli(self, cli_url: str) -> Dict[str, Any]:
        """
        Fetch CLI data from a pre‑resolved URL.
        """
        return await self._request_with_retries(cli_url)
