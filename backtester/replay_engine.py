"""
replay_engine.py — v1.0.0-production
Processes snapshots in timestamp order and applies:
    • entry logic
    • exit logic
    • fill simulation
    • portfolio updates
"""

from typing import Any, Dict, List


class ReplayEngine:
    def __init__(
        self,
        entry_controller,
        exit_controller,
        portfolio,
        simulator,
        risk_engine,
        breaker,
        trades: List[Dict],
        settlements: List[Dict],
        pnl_curve: List[Dict],
    ):
        self.entry_controller = entry_controller
        self.exit_controller = exit_controller
        self.portfolio = portfolio
        self.simulator = simulator
        self.risk_engine = risk_engine
        self.breaker = breaker

        self.trades = trades
        self.settlements = settlements
        self.pnl_curve = pnl_curve

        self.cash = 0.0

    # -----------------------------------------------------
    # Main snapshot processor
    # -----------------------------------------------------

    def process_snapshot(self, snapshot):
        # ENTRY
        entry_signal = self.entry_controller.evaluate_signal(snapshot)
        if entry_signal:
            trade = self.simulator.simulate_entry_fill(snapshot, entry_signal)
            if trade:
                self._record_trade(trade)
                self.portfolio.open(
                    ticker=snapshot.ticker,
                    side=trade["side"],
                    count=trade["size"],
                    entry=trade["price"],
                )

        # EXIT
        pos = self.portfolio.positions.get(snapshot.ticker)
        if pos:
            exit_signal = self.exit_controller._compute_exit_reason(snapshot, pos)
            if exit_signal:
                settlement = self.simulator.simulate_exit_fill(snapshot, pos, exit_signal)
                if settlement:
                    self._record_settlement(settlement)
                    self.portfolio.close(snapshot.ticker)

        # PnL curve
        self._record_equity(snapshot.timestamp)

    # -----------------------------------------------------
    # Logging helpers
    # -----------------------------------------------------

    def _record_trade(self, trade):
        self.trades.append(trade)

    def _record_settlement(self, settlement):
        self.settlements.append(settlement)

    def _record_equity(self, timestamp):
        total_equity = self.portfolio.total_equity()
        self.pnl_curve.append({"timestamp": timestamp, "equity": total_equity})
