# engine/weather/http_client.py — v1.0.0
# Shared async HTTP client for Weather Engine.

import httpx


class WeatherHttpClient:
    """
    Shared AsyncClient wrapper for all weather providers.
    Ensures connection pooling and consistent headers.
    """

    def __init__(self, user_agent: str):
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": user_agent,
                "Accept": "application/geo+json, application/json",
            },
            timeout=10.0,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def aclose(self) -> None:
        await self._client.aclose()
