"""
crypto_s3_adapter.py — v3.0.0
---------------------------------------------------------
CF Benchmarks-derived crypto feed via Kalshi public S3.

Provides:
    • CryptoS3Adapter — class-based adapter.
    • get_live_price(symbol) — latest CF live price (second-level).
    • get_candles(symbol, interval) — OHLC candlestick for given interval.
    • build_snapshot(symbol) — UTE v3-compatible snapshot object.

Supported symbols:
    • BTC, ETH, XRP, SOL, DOGE
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal, List

import requests

logger = logging.getLogger("crypto-s3-adapter")

CF_INTERVAL = Literal["6H", "1H", "15M", "1M"]

CF_S3_ENDPOINTS: Dict[str, str] = {
    "BTC": "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/btc_current.json",
    "ETH": "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/eth_current.json",
    "XRP": "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/xrp_current.json",
    "SOL": "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/sol_current.json",
    "DOGE": "https://kalshi-public-docs.s3.amazonaws.com/external/crypto/doge_current.json",
}


@dataclass
class CryptoSnapshotV3:
    symbol: str
    maturity_ts_ms: int
    live_price: float
    candle_1m: Optional[Dict[str, Any]]
    candle_15m: Optional[Dict[str, Any]]
    candle_1h: Optional[Dict[str, Any]]
    candle_6h: Optional[Dict[str, Any]]
    second_series: List[float]
    snapshot_ts: datetime


class CryptoS3Adapter:
    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    # ---------------------------------------------------------
    # Factory
    # ---------------------------------------------------------
    @classmethod
    def create(cls) -> "CryptoS3Adapter":
        """
        Factory constructor for parity with CoinbaseAdapter.from_env().
        No auth required for S3 endpoints.
        """
        logger.info("[CryptoS3Adapter] Initialized (public S3 endpoints, no auth).")
        return cls()

    # ---------------------------------------------------------
    # Internal fetch helper
    # ---------------------------------------------------------
    def _fetch_raw(self, symbol: str) -> Optional[Dict[str, Any]]:
        sym = symbol.upper()
        url = CF_S3_ENDPOINTS.get(sym)
        if not url:
            logger.warning(f"[CryptoS3Adapter] Unsupported symbol: {symbol}")
            return None

        try:
            resp = self.session.get(url, timeout=2.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"[CryptoS3Adapter] Error fetching CF S3 data for {symbol}: {e}")
            return None

    # ---------------------------------------------------------
    # Live price (second-level)
    # ---------------------------------------------------------
    def get_live_price(self, symbol: str) -> Optional[float]:
        """
        Return the latest CF live price for the given symbol.

        Uses:
            data["timeseries"]["second"][-1]
        """
        data = self._fetch_raw(symbol)
        if not data:
            return None

        try:
            series = data.get("timeseries", {}).get("second") or []
            if not series:
                logger.warning(f"[CryptoS3Adapter] No second-level timeseries for {symbol}")
                return None
            return float(series[-1])
        except Exception as e:
            logger.warning(f"[CryptoS3Adapter] Failed to parse live price for {symbol}: {e}")
            return None

    # ---------------------------------------------------------
    # Candlesticks (OHLC)
    # ---------------------------------------------------------
    def get_candles(
        self,
        symbol: str,
        interval: CF_INTERVAL = "15M",
    ) -> Optional[Dict[str, Any]]:
        """
        Return OHLC candlestick for the given symbol and interval.

        Example intervals:
            • "6H"
            • "1H"
            • "15M"
            • "1M"
        """
        data = self._fetch_raw(symbol)
        if not data:
            return None

        try:
            candles = data.get("candlesticks", {})
            c = candles.get(interval)
            if not c:
                logger.warning(
                    f"[CryptoS3Adapter] Missing candlestick interval {interval} for {symbol}"
                )
                return None
            return {
                "maturity_ts_ms": int(data.get("maturity_ts_ms", 0)),
                "open_ts_ms": int(c.get("open_ts_ms", 0)),
                "open": float(c.get("open", 0.0)),
                "high": float(c.get("high", 0.0)),
                "low": float(c.get("low", 0.0)),
                "close": float(c.get("close", 0.0)),
                "interval": interval,
                "symbol": symbol.upper(),
            }
        except Exception as e:
            logger.warning(
                f"[CryptoS3Adapter] Failed to parse candlestick for {symbol} {interval}: {e}"
            )
            return None

    # ---------------------------------------------------------
    # UTE v3 snapshot builder
    # ---------------------------------------------------------
    def build_snapshot(self, symbol: str) -> Optional[CryptoSnapshotV3]:
        """
        Build a UTE v3-compatible crypto snapshot for the given symbol.

        Uses:
            • maturity_ts_ms
            • candlesticks: 1M, 15M, 1H, 6H
            • timeseries.second (full series, last = live price)
        """
        data = self._fetch_raw(symbol)
        if not data:
            return None

        try:
            maturity_ts_ms = int(data.get("maturity_ts_ms", 0))
            candles = data.get("candlesticks", {}) or {}
            series = data.get("timeseries", {}).get("second") or []

            candle_1m = candles.get("1M")
            candle_15m = candles.get("15M")
            candle_1h = candles.get("1H")
            candle_6h = candles.get("6H")

            if not series:
                logger.warning(f"[CryptoS3Adapter] No second-level series for {symbol}")
                return None

            live_price = float(series[-1])

            snap = CryptoSnapshotV3(
                symbol=symbol.upper(),
                maturity_ts_ms=maturity_ts_ms,
                live_price=live_price,
                candle_1m=candle_1m,
                candle_15m=candle_15m,
                candle_1h=candle_1h,
                candle_6h=candle_6h,
                second_series=[float(x) for x in series],
                snapshot_ts=datetime.now(timezone.utc),
            )
            logger.info(f"[CryptoS3Adapter] Built snapshot for {symbol}: live={live_price}")
            return snap
        except Exception as e:
            logger.warning(f"[CryptoS3Adapter] Failed to build snapshot for {symbol}: {e}")
            return None
