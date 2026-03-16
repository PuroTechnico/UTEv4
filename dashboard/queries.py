# dashboard/queries.py
# Version: 4.0 — Forward-only, DB-backed crypto snapshots removed.
#
# Notes:
#   - This module now exposes ONLY DB-backed entities that are still canonical:
#       • MarketSnapshot (market_snapshot)
#       • WeatherSnapshot (weather_snapshot)
#       • OpportunitySnapshot (opportunity_snapshot)
#       • PositionRecord (position_record)
#       • TradeRecord (trade_record)
#       • FillRecord (fill_record)
#       • SettlementRecord (settlement_record)
#       • HealthSnapshot (health_snapshot)
#   - Legacy DB-backed crypto snapshots (CryptoSnapshot / crypto_snapshot table)
#     have been fully removed from the dashboard query layer.
#   - Crypto data is expected to come from the S3-based pipeline / adapters,
#     not from the DB, and is wired at the service/view-model layer.

from typing import List
from datetime import datetime
import json

from database.db import query
from models.snapshots import MarketSnapshot, WeatherSnapshot
from models.opportunities import OpportunitySnapshot
from models.positions import PositionRecord
from models.execution import TradeRecord, FillRecord, SettlementRecord
from models.health import HealthSnapshot


class DashboardQueries:
    """
    Typed DB access layer for dashboard.
    No business logic. No transformations.

    Forward-only invariant:
        - This layer reflects the DB schema only.
        - Crypto is no longer sourced from the DB here.
    """

    # -----------------------------
    # Snapshots (DB-backed)
    # -----------------------------
    def get_latest_market_snapshots(self) -> List[MarketSnapshot]:
        rows = query(
            """
            SELECT * FROM market_snapshot
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        return [
            MarketSnapshot(
                venue_id=r["venue_id"],
                ticker=r["ticker"],
                yes_price=r["yes_price"],
                no_price=r["no_price"],
                spread=r["spread"],
                volume=r["volume"],
                tte_minutes=r["tte_minutes"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                liquidity_metrics=(
                    json.loads(r["liquidity_metrics"])
                    if r["liquidity_metrics"]
                    else None
                ),
                volatility_metrics=(
                    json.loads(r["volatility_metrics"])
                    if r["volatility_metrics"]
                    else None
                ),
            )
            for r in rows
        ]

    # NOTE:
    #   Legacy method get_latest_crypto_snapshots() has been intentionally removed.
    #   Crypto is now sourced from S3 (CryptoS3Adapter / CryptoSnapshotV3) and
    #   should be wired via the dashboard service / view-model layer, not via DB.

    def get_weather_snapshots(self) -> List[WeatherSnapshot]:
        rows = query(
            """
            SELECT * FROM weather_snapshot
            ORDER BY oracle_timestamp DESC
            LIMIT 50
            """
        )
        return [
            WeatherSnapshot(
                location_name=r["location_name"],
                lat=r["lat"],
                lon=r["lon"],
                station_id=r["station_id"],
                expected_high=r["expected_high"],
                asos_temp=r["asos_temp"],
                oracle_timestamp=datetime.fromisoformat(r["oracle_timestamp"]),
                strikes_f=json.loads(r["strikes_f"]),
                strike_type_by_strike=json.loads(r["strike_type_by_strike"]),
                kalshi_ticker_by_strike=json.loads(r["kalshi_ticker_by_strike"]),
                yes_bid=json.loads(r["yes_bid"]),
                yes_ask=json.loads(r["yes_ask"]),
                no_bid=json.loads(r["no_bid"]),
                no_ask=json.loads(r["no_ask"]),
                model_prob_by_strike=json.loads(r["model_prob_by_strike"]),
            )
            for r in rows
        ]

    # -----------------------------
    # Opportunities
    # -----------------------------
    def get_opportunities(self) -> List[OpportunitySnapshot]:
        rows = query(
            """
            SELECT * FROM opportunity_snapshot
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        return [
            OpportunitySnapshot(
                asset=r["asset"],
                kalshi_yes=r["kalshi_yes"],
                kalshi_no=r["kalshi_no"],
                spread=r["spread"],
                volume=r["volume"],
                edge_score=r["edge_score"],
                readiness=r["readiness"],
                tte=r["tte"],
                skip_reason=r["skip_reason"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
            for r in rows
        ]

    # -----------------------------
    # Positions / Trades / Fills / Settlements
    # -----------------------------
    def get_positions(self) -> List[PositionRecord]:
        rows = query("SELECT * FROM position_record ORDER BY updated_at DESC")
        return [
            PositionRecord(
                venue_id=r["venue_id"],
                ticker=r["ticker"],
                side=r["side"],
                count=r["count"],
                entry_price=r["entry_price"],
                high_water_mark=r["high_water_mark"],
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
            )
            for r in rows
        ]

    def get_trades(self) -> List[TradeRecord]:
        rows = query("SELECT * FROM trade_record ORDER BY created_at DESC LIMIT 50")
        return [
            TradeRecord(
                venue_id=r["venue_id"],
                ticker=r["ticker"],
                side=r["side"],
                size=r["size"],
                price=r["price"],
                status=r["status"],
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=(
                    datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else None
                ),
            )
            for r in rows
        ]

    def get_fills(self) -> List[FillRecord]:
        rows = query("SELECT * FROM fill_record ORDER BY created_time DESC LIMIT 50")
        return [
            FillRecord(
                venue_id=r["venue_id"],
                ticker=r["ticker"],
                side=r["side"],
                size=r["size"],
                price=r["price"],
                fee_cost=r["fee_cost"],
                is_taker=bool(r["is_taker"]),
                created_time=datetime.fromisoformat(r["created_time"]),
                trade_id=r["trade_id"],
            )
            for r in rows
        ]

    def get_settlements(self) -> List[SettlementRecord]:
        rows = query(
            "SELECT * FROM settlement_record ORDER BY settled_time DESC LIMIT 50"
        )
        return [
            SettlementRecord(
                venue_id=r["venue_id"],
                ticker=r["ticker"],
                pnl=r["pnl"],
                payout=r["payout"],
                settled_time=datetime.fromisoformat(r["settled_time"]),
                trade_id=r["trade_id"],
            )
            for r in rows
        ]

    # -----------------------------
    # Health
    # -----------------------------
    def get_health_history(self) -> List[HealthSnapshot]:
        rows = query(
            """
            SELECT * FROM health_snapshot
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        return [
            HealthSnapshot(
                component=r["component"],
                status=r["status"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                metadata=json.loads(r["metadata"]) if r["metadata"] else None,
            )
            for r in rows
        ]
