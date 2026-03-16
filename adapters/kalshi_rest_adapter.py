"""
kalshi_rest_adapter.py — v12.0.0 (FULL ASYNC)
---------------------------------------------------------
Production-grade REST client for Kalshi Trade API v2.
"""

from typing import Any, Dict, Optional
import aiohttp
import time
import json
import base64
import asyncio

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization


class KalshiRESTAdapter:
    """
    Fully async REST client for Kalshi Trade API v2.
    """

    def __init__(self, key_id: str, key_secret: str, base_url: str):
        self.key_id = key_id
        self._key_secret_pem = key_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
        self._private_key = None

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ============================================================
    # PRIVATE KEY LOADING
    # ============================================================

    def _load_private_key(self):
        if self._private_key is None:
            self._private_key = serialization.load_pem_private_key(
                self._key_secret_pem,
                password=None,
            )
        return self._private_key

    # ============================================================
    # RSA‑PSS SIGNING
    # ============================================================

    def _sign(self, method: str, full_path: str, body: str = "") -> Dict[str, str]:
        ts = str(int(time.time() * 1000))
        msg = f"{ts}{method.upper()}{full_path}".encode("utf-8")
        private_key = self._load_private_key()

        signature = private_key.sign(
            msg,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        signature_b64 = base64.b64encode(signature).decode()

        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": signature_b64,
            "Content-Type": "application/json",
        }

    # ============================================================
    # CORE REQUEST WRAPPER
    # ============================================================

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        full_path = path
        url = f"{self.base_url}{full_path}"

        body_str = (
            "" if json_body is None else json.dumps(json_body, separators=(",", ":"))
        )
        headers = self._sign(method, full_path, body_str)

        # IMPORTANT: create a new session for each request to avoid reuse across
        # asyncio.run() boundaries and closed event loops.
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                params=params,
                data=body_str or None,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    # ============================================================
    # MARKET ENDPOINTS (ASYNC)
    # ============================================================

    async def get_market(self, ticker: str) -> Dict[str, Any]:
        return await self._request("GET", f"/markets/{ticker}")

    async def get_markets(
        self,
        series_ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        limit: int = 200,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:

        params: Dict[str, Any] = {"limit": limit}
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/markets", params=params)

    async def get_markets_by_event_async(self, event_ticker: str):
        resp = await self.get_markets(event_ticker=event_ticker, limit=200)
        return resp.get("markets", resp)

    # ============================================================
    # SERIES ENDPOINTS (ASYNC)
    # ============================================================

    async def get_series(
        self,
        limit: int = 200,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:

        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/series", params=params)

    # ============================================================
    # EVENTS ENDPOINTS (ASYNC)
    # ============================================================

    async def get_events(
        self,
        series_ticker: Optional[str] = None,
        limit: int = 200,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:

        params: Dict[str, Any] = {"limit": limit}
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/events", params=params)

    async def get_events_by_series_async(self, series_ticker: str):
        resp = await self.get_events(series_ticker=series_ticker, limit=200)
        return resp.get("events", resp)

    # ============================================================
    # CLEANUP
    # ============================================================

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
