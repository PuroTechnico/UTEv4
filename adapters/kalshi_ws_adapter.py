"""
kalshi_ws_adapter.py — v11.0.0
---------------------------------------------------------
Production‑grade WebSocket client for Kalshi market data.

Key features:
    • HMAC‑SHA256 authentication (WS uses HMAC, not RSA‑PSS)
    • Clean session lifecycle
    • Market‑data subscription (orderbook, trades, prices, events)
    • Optional on_message callback
    • Fully compatible with REST v11.0.0 adapter
"""

from typing import Any, Dict, List, Callable, Optional
import aiohttp
import asyncio
import json
import time
import hmac
import hashlib


class KalshiWebSocketAdapter:
    """
    Thin async WebSocket client for Kalshi streaming market data.

    Docs:
        https://docs.kalshi.com/getting_started/quick_start_websockets

    Usage:
        ws = KalshiWebSocketAdapter(...)
        await ws.connect()
        await ws.subscribe_markets(["KXBTC15M-..."])
        await ws.listen_forever()
    """

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        ws_url: str,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.key_id = key_id
        self.key_secret = key_secret.encode("utf-8")  # HMAC key
        self.ws_url = ws_url
        self.on_message = on_message

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ============================================================
    # AUTH PAYLOAD (HMAC‑SHA256)
    # ============================================================

    def _auth_payload(self) -> Dict[str, Any]:
        """
        WebSocket auth uses HMAC‑SHA256 over the timestamp.
        """
        ts = str(int(time.time()))
        msg = ts.encode("utf-8")

        sig = hmac.new(self.key_secret, msg, hashlib.sha256).hexdigest()

        return {
            "access_key": self.key_id,
            "timestamp": ts,
            "signature": sig,
        }

    # ============================================================
    # CONNECT
    # ============================================================

    async def connect(self) -> None:
        """
        Establish WebSocket connection and authenticate.
        """
        session = await self._get_session()
        self._ws = await session.ws_connect(self.ws_url)

        auth_msg = {
            "type": "auth",
            "data": self._auth_payload(),
        }

        await self._ws.send_str(json.dumps(auth_msg))

    # ============================================================
    # SUBSCRIBE TO MARKET DATA
    # ============================================================

    async def subscribe_markets(self, tickers: List[str]) -> None:
        """
        Subscribe to full market data stream for the given tickers.
        Includes:
            • orderbook updates
            • trades
            • prices
            • events
        """
        if not self._ws:
            raise RuntimeError("WebSocket not connected")

        sub_msg = {
            "type": "subscribe",
            "channels": [
                {
                    "name": "market_data",
                    "tickers": tickers,
                }
            ],
        }

        await self._ws.send_str(json.dumps(sub_msg))

    # ============================================================
    # LISTEN LOOP
    # ============================================================

    async def listen_forever(self) -> None:
        """
        Blocking loop that yields messages until connection closes.
        """
        if not self._ws:
            raise RuntimeError("WebSocket not connected")

        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                if self.on_message:
                    self.on_message(data)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

    # ============================================================
    # CLOSE
    # ============================================================

    async def close(self) -> None:
        """
        Cleanly close WebSocket + session.
        """
        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()
