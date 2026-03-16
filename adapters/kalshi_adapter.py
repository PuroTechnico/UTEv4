"""
kalshi_adapter.py — v10.0.0
---------------------------------------------------------
Unified REST + WebSocket Kalshi adapter (SDK‑free).

Implements the MarketAdapter interface:
    • get_markets(series)
    • get_price(ticker)
    • get_market_orderbook(ticker)
    • get_orders(...)
    • get_order(order_id)
    • place_order(...)
    • cancel_order(order_id)

Internally uses:
    • KalshiRESTAdapter       (full REST surface)
    • KalshiWebSocketAdapter  (optional streaming)
"""

import os
from typing import Dict, Any, List, Optional

from adapters.kalshi_rest_adapter import KalshiRESTAdapter
from adapters.kalshi_ws_adapter import KalshiWebSocketAdapter


class KalshiAdapter:
    """
    High‑level adapter that exposes a clean interface to the trading engine.
    Delegates:
        • REST adapter for all authenticated operations
        • WebSocket adapter for streaming (optional)
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, key_id: str, key_path: str, base_url: str):
        """
        key_path is a filesystem path to the PEM private key.
        """
        key_secret = os.path.expanduser(key_path)

        # Full REST client (signing, routing, error handling)
        self.rest = KalshiRESTAdapter(
            key_id=key_id,
            key_secret=key_secret,
            base_url=base_url,
        )

        # Optional WebSocket client (not required for core trading)
        self.ws = KalshiWebSocketAdapter(
            key_id=key_id,
            key_secret=key_secret,
            ws_url="wss://api.elections.kalshi.com/trade-api/ws",
        )

    # ============================================================
    # MARKET DISCOVERY
    # ============================================================

    async def get_markets(self, series: str) -> List[Dict]:
        """
        Old behavior:
            return [{"ticker": <active_ticker>}]

        New behavior:
            Use REST to fetch all markets for the series, then pick the active one.
        """
        resp = await self.rest.get_markets(series_ticker=series)
        markets = resp.get("markets", [])

        if not markets:
            return []

        # Match SDK behavior: choose the active market if present
        active = next((m for m in markets if m.get("status") == "active"), None)
        if not active:
            active = markets[0]

        return [{"ticker": active["ticker"]}]

    # ============================================================
    # PRICE LOOKUP (BID/ASK‑FIRST)
    # ============================================================

    async def get_price(self, ticker: str) -> float:
        """
        Return a tradable YES price for a market.

        Priority:
            1. yes_bid (best bid — most realistic tradable price)
            2. yes_ask (best ask)
            3. last_price (fallback only)
        """
        market_resp = await self.rest.get_market(ticker)
        market = market_resp.get("market", market_resp)

        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        last_price = market.get("last_price")

        if isinstance(yes_bid, (int, float)) and yes_bid > 0:
            return float(yes_bid)

        if isinstance(yes_ask, (int, float)) and yes_ask > 0:
            return float(yes_ask)

        if isinstance(last_price, (int, float)) and last_price > 0:
            return float(last_price)

        return 0.0

    # ============================================================
    # ORDERBOOK
    # ============================================================

    async def get_market_orderbook(self, ticker: str) -> Dict[str, Any]:
        """
        Wrapper for REST get_market_orderbook.
        Returns full depth orderbook for the given ticker.
        """
        return await self.rest.get_market_orderbook(ticker)

    # ============================================================
    # PORTFOLIO ORDER LISTING
    # ============================================================

    async def get_orders(
        self,
        ticker: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        side: Optional[str] = None,
        subaccount: Optional[int] = None,
    ):
        """
        Full wrapper for GET /portfolio/orders.
        Supports filtering by:
            • ticker
            • status
            • action
            • side
            • subaccount
        """
        return await self.rest.get_orders(
            ticker=ticker,
            status=status,
            action=action,
            side=side,
            subaccount=subaccount,
        )

    # ============================================================
    # ORDER PLACEMENT
    # ============================================================

    async def place_order(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Old behavior:
            return await client.create_order(*args, **kwargs)

        New behavior:
            Pass through to REST create_order.
        """
        payload = kwargs if kwargs else args[0]
        return await self.rest.create_order(payload)

    # ============================================================
    # ORDER CANCELLATION
    # ============================================================

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order by ID.
        Returns True if cancellation succeeded.
        """
        try:
            resp = await self.rest.cancel_order(order_id)
            return not resp.get("error")
        except Exception:
            return False

    # ============================================================
    # ORDER STATUS
    # ============================================================

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch a single order by ID.
        """
        try:
            return await self.rest.get_order(order_id)
        except Exception:
            return {}
