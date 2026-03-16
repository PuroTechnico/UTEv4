# models/dashboard_view_models.py
# Version: 4.0 — Forward-only crypto view models (S3-based).
#
# Notes:
#   - CryptoVolTile has been updated to align with CryptoSnapshotV3 from CryptoS3Adapter.
#   - It now represents live CF Benchmarks data (price + candles + second-series).
#   - DashboardViewModels now includes crypto_spot_tiles as a forward-only placeholder
#     (currently unused / empty in DashboardService v4.0).

from dataclasses import dataclass
from typing import List, Optional, Any
from .snapshots import MarketSnapshot, WeatherSnapshot
from .opportunities import OpportunitySnapshot
from .positions import PositionRecord
from .execution import TradeRecord, FillRecord, SettlementRecord
from .health import HealthSnapshot
from datetime import datetime


@dataclass
class WeatherModelTile:
    city: str
    date: str
    expected_high: float
    asos_temp: Optional[float]
    pace: Optional[float]
    prob_curve: List[float]


@dataclass
class CryptoVolTile:
    """
    Forward-only crypto volatility tile, backed by CryptoSnapshotV3 (S3).

    Fields map directly from CryptoSnapshotV3:
        - symbol
        - live_price
        - maturity_ts_ms
        - candle_1m / 15m / 1h / 6h
        - second_series
        - snapshot_ts
    """

    symbol: str
    live_price: float
    maturity_ts_ms: int
    candle_1m: Optional[dict]
    candle_15m: Optional[dict]
    candle_1h: Optional[dict]
    candle_6h: Optional[dict]
    second_series: List[float]
    snapshot_ts: datetime


@dataclass
class DashboardViewModels:
    # Forward-only placeholder for future spot tiles (currently [] in DashboardService).
    crypto_spot_tiles: List[Any]

    kalshi_tiles: List[MarketSnapshot]
    weather_tiles: List[WeatherSnapshot]
    weather_model_tile: Optional[WeatherModelTile]
    crypto_vol_tiles: List[CryptoVolTile]
    health_tiles: List[HealthSnapshot]
    heatmap: List[OpportunitySnapshot]
    opportunities: List[OpportunitySnapshot]
    positions: List[PositionRecord]
    trades: List[TradeRecord]
    fills: List[FillRecord]
    settlements: List[SettlementRecord]
