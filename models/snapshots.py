# ute/models/snapshots.py
# Version: 3.3 — Coinbase removed, S3 snapshot model lives in CryptoS3Adapter.
#
# Notes:
#   - WeatherSnapshot unchanged (v3.1)
#   - MarketSnapshot unchanged
#   - Legacy Coinbase CryptoSnapshot removed
#   - Crypto S3 uses its own model (CryptoSnapshotV3) defined in the adapter
#     and should NOT be duplicated here.

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Literal

StrikeType = Literal["greater", "less", "between"]


# ---------------------------------------------------------
# WeatherSnapshot v3.1 — canonical schema
# ---------------------------------------------------------
@dataclass
class WeatherSnapshot:
    # Location metadata
    location_name: str
    lat: float
    lon: float
    station_id: str

    # Oracle data
    expected_high: float
    asos_temp: Optional[float]
    oracle_timestamp: datetime

    # Strike universe
    strikes_f: List[float]
    strike_type_by_strike: Dict[float, str]
    kalshi_ticker_by_strike: Dict[float, str]

    # Kalshi prices (converted to probabilities)
    yes_bid: Dict[float, float]
    yes_ask: Dict[float, float]
    no_bid: Dict[float, float]
    no_ask: Dict[float, float]

    # Model probabilities
    model_prob_by_strike: Dict[float, float]


# ---------------------------------------------------------
# MarketSnapshot (unchanged)
# ---------------------------------------------------------
@dataclass
class MarketSnapshot:
    venue_id: str
    ticker: str
    yes_price: float
    no_price: float
    spread: float
    volume: int
    tte_minutes: float
    timestamp: datetime
    liquidity_metrics: Optional[Dict[str, float]] = None
    volatility_metrics: Optional[Dict[str, float]] = None


# ---------------------------------------------------------
# CryptoSnapshot REMOVED (Coinbase)
# Crypto S3 uses its own model: CryptoSnapshotV3
# ---------------------------------------------------------
# (Intentionally omitted)
