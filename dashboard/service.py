# dashboard/service.py
# Version: 4.0 — Forward-only crypto integration (S3-based).
#
# Notes:
#   - All DB-backed crypto snapshot usage has been removed.
#   - Crypto is now sourced exclusively from CryptoS3Adapter (S3 → CryptoSnapshotV3).
#   - This service converts S3 snapshots → CryptoVolTile for dashboard display.
#   - No legacy Coinbase or DB crypto paths remain.

from typing import Optional, List
from dashboard.queries import DashboardQueries
from models.dashboard_view_models import (
    DashboardViewModels,
    WeatherModelTile,
    CryptoVolTile,
)
from adapters.crypto_s3_adapter import CryptoS3Adapter, CryptoSnapshotV3


class DashboardService:
    """
    Converts typed DB rows + S3 crypto → typed dashboard view models.
    No business logic (Phase 1).
    """

    def __init__(self):
        self.q = DashboardQueries()
        self.crypto_s3 = CryptoS3Adapter.create()

        # Forward-only: supported crypto symbols for dashboard tiles
        self.crypto_symbols: List[str] = ["BTC", "ETH", "SOL", "DOGE", "XRP"]

    # ---------------------------------------------------------
    # Internal helper: build crypto volatility tiles from S3
    # ---------------------------------------------------------
    def _build_crypto_vol_tiles(self) -> List[CryptoVolTile]:
        tiles: List[CryptoVolTile] = []

        for sym in self.crypto_symbols:
            snap: Optional[CryptoSnapshotV3] = self.crypto_s3.build_snapshot(sym)
            if not snap:
                continue

            # Convert S3 snapshot → CryptoVolTile
            tile = CryptoVolTile(
                symbol=sym,
                live_price=snap.live_price,
                maturity_ts_ms=snap.maturity_ts_ms,
                candle_1m=snap.candle_1m,
                candle_15m=snap.candle_15m,
                candle_1h=snap.candle_1h,
                candle_6h=snap.candle_6h,
                second_series=snap.second_series,
                snapshot_ts=snap.snapshot_ts,
            )
            tiles.append(tile)

        return tiles

    # ---------------------------------------------------------
    # Main dashboard builder
    # ---------------------------------------------------------
    def build(self) -> DashboardViewModels:
        # DB-backed components
        market = self.q.get_latest_market_snapshots()
        weather = self.q.get_weather_snapshots()
        opportunities = self.q.get_opportunities()
        positions = self.q.get_positions()
        trades = self.q.get_trades()
        fills = self.q.get_fills()
        settlements = self.q.get_settlements()
        health = self.q.get_health_history()

        # Forward-only crypto (S3)
        crypto_vol_tiles = self._build_crypto_vol_tiles()

        # Phase 1 placeholder
        weather_model_tile: Optional[WeatherModelTile] = None

        return DashboardViewModels(
            crypto_spot_tiles=[],          # Not implemented yet (Phase 2)
            kalshi_tiles=market,
            weather_tiles=weather,
            weather_model_tile=weather_model_tile,
            crypto_vol_tiles=crypto_vol_tiles,
            health_tiles=health,
            heatmap=opportunities,
            opportunities=opportunities,
            positions=positions,
            trades=trades,
            fills=fills,
            settlements=settlements,
        )

