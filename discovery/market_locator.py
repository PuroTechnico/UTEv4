# discovery/market_locator.py — v2.2.0 (timezone fix)

from datetime import datetime
from typing import List, Dict

from discovery.crypto_taxonomy import classify_crypto_series
from time_utils.active_15m_ticker import get_active_15m_ticker, EASTERN


class CryptoMarketLocator:
    """
    Async router for locating active Crypto markets.
    """

    def __init__(self, rest):
        self.rest = rest

    async def locate(self, series: Dict, now_utc: datetime) -> List[str]:
        series_ticker = series["ticker"]
        frequency = series.get("frequency", "")
        mutually_exclusive = series.get("mutually_exclusive", False)

        info = classify_crypto_series(series_ticker, frequency, mutually_exclusive)

        # --------------------------------------------------------
        # 15m directional markets — NO /events CALLS
        # --------------------------------------------------------
        if info.family == "crypto_15m_directional":
            ticker = get_active_15m_ticker(series_ticker, now_utc)
            return [ticker]

        # --------------------------------------------------------
        # Hourly directional or range — USE /events
        # --------------------------------------------------------
        if info.family in ("crypto_hourly_directional", "crypto_hourly_range"):
            events = await self.rest.get_events_by_series_async(series_ticker)
            active = [e for e in events if e.get("status") == "active"]

            if not active:
                return []

            event_ticker = active[0]["event_ticker"]
            markets = await self.rest.get_markets_by_event_async(event_ticker)
            return [m["ticker"] for m in markets if m.get("status") == "active"]

        # --------------------------------------------------------
        # Daily directional — USE /events
        # --------------------------------------------------------
        if info.family == "crypto_daily_directional":
            event_ticker = self._compute_daily_event_ticker(now_utc)
            markets = await self.rest.get_markets_by_event_async(event_ticker)
            return [m["ticker"] for m in markets if m.get("status") == "active"]

        # --------------------------------------------------------
        # Annual, one-off, custom — DO NOT CALL /events
        # --------------------------------------------------------
        resp = await self.rest.get_markets(series_ticker=series_ticker)
        markets = resp.get("markets", resp)
        return [m["ticker"] for m in markets]

    def _compute_daily_event_ticker(self, now_utc: datetime) -> str:
        dt = now_utc.astimezone(EASTERN)
        return f"{dt:%y}{dt:%b}{dt:%d}".upper()
