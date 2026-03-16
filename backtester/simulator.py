"""
simulator.py — v1.0.0-production
Simulates fills for entry and exit orders.
"""

from typing import Dict, Any


class FillSimulator:
    def __init__(self, slippage=0.01):
        self.slippage = slippage

    # -----------------------------------------------------
    # Entry fill simulation
    # -----------------------------------------------------

    def simulate_entry_fill(self, snapshot, signal) -> Dict[str, Any]:
        side = signal["side"]
        size = signal["size"]

        if side == "yes":
            price = snapshot.yes_price + self.slippage
        else:
            price = snapshot.no_price + self.slippage

        return {
            "timestamp": snapshot.timestamp,
            "ticker": snapshot.ticker,
            "side": side,
            "size": size,
            "price": price,
        }

    # -----------------------------------------------------
    # Exit fill simulation
    # -----------------------------------------------------

    def simulate_exit_fill(self, snapshot, pos, exit_reason) -> Dict[str, Any]:
        side = pos["side"]
        size = pos["count"]

        if side == "yes":
            exit_price = snapshot.yes_price - self.slippage
        else:
            exit_price = snapshot.no_price - self.slippage

        entry_price = pos["entry"]
        direction = 1 if side == "yes" else -1
        pnl = (exit_price - entry_price) * size * direction

        return {
            "timestamp": snapshot.timestamp,
            "ticker": snapshot.ticker,
            "pnl": pnl,
            "payout": exit_price * size,
            "exit_reason": exit_reason,
        }
