"""
backtester/backtester.py — v1.0.0-production
Unified historical replay engine for Kalshi 15m system.

This module orchestrates:
    • loading historical data
    • replaying snapshots
    • running entry + exit logic
    • simulating fills
    • computing PnL
    • producing metrics
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

from backtester.replay_engine import ReplayEngine
from backtester.simulator import FillSimulator
from backtester.metrics import compute_metrics

from engine.entry_controller import EntryController
from engine.exit_controller import ExitController, ExitThresholds
from engine.market_snapshot import MarketSnapshot
from engine.engine_state import Portfolio
from execution.risk_engine import RiskEngine
from execution.circuit_breaker import CircuitBreaker

import database


class Backtester:
    def __init__(
        self,
        db_path: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        thresholds: Optional[ExitThresholds] = None,
    ):
        self.db_path = db_path
        self.start = start
        self.end = end
        self.thresholds = thresholds or ExitThresholds()

        self.entry_controller = EntryController(logging_only=True)
        self.exit_controller = ExitController(thresholds=self.thresholds, logging_only=True)

        self.portfolio = Portfolio()
        self.risk_engine = RiskEngine()
        self.breaker = CircuitBreaker()
        self.simulator = FillSimulator()

        self.trades: List[Dict[str, Any]] = []
        self.settlements: List[Dict[str, Any]] = []
        self.pnl_curve: List[Dict[str, Any]] = []

    # -----------------------------------------------------
    # Main entrypoint
    # -----------------------------------------------------

    def run(self) -> Dict[str, Any]:
        rows = self._load_opportunities()

        replay = ReplayEngine(
            entry_controller=self.entry_controller,
            exit_controller=self.exit_controller,
            portfolio=self.portfolio,
            simulator=self.simulator,
            risk_engine=self.risk_engine,
            breaker=self.breaker,
            trades=self.trades,
            settlements=self.settlements,
            pnl_curve=self.pnl_curve,
        )

        for row in rows:
            snapshot = self._snapshot_from_row(row)
            replay.process_snapshot(snapshot)

        metrics = compute_metrics(self.trades, self.settlements, self.pnl_curve)

        return {
            "trades": self.trades,
            "settlements": self.settlements,
            "pnl_curve": self.pnl_curve,
            "metrics": metrics,
        }

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def _load_opportunities(self):
        query = """
            SELECT *
            FROM opportunities
            WHERE 1=1
        """

        params = []

        if self.start:
            query += " AND timestamp >= ?"
            params.append(self.start)

        if self.end:
            query += " AND timestamp <= ?"
            params.append(self.end)

        query += " ORDER BY timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()

    def _snapshot_from_row(self, r):
        return MarketSnapshot(
            ticker=f"{r['asset']}-15m",
            asset=r["asset"],
            yes_price=r["kalshi_yes"],
            no_price=r["kalshi_no"],
            spread=r["spread"],
            volume=r["volume"],
            edge_score=r["edge_score"],
            tte_min=r["tte"],
            coinbase_price=r["coinbase_price"],
            readiness=r["readiness"],
            timestamp=r["timestamp"],
        )
