"""
metrics.py — v1.0.0-production
Computes summary statistics for backtest results.
"""

import math
from typing import List, Dict


def compute_metrics(trades: List[Dict], settlements: List[Dict], pnl_curve: List[Dict]):
    if not pnl_curve:
        return {}

    equity = [p["equity"] for p in pnl_curve]
    returns = [equity[i] - equity[i - 1] for i in range(1, len(equity))]

    win_rate = (
        sum(1 for s in settlements if s["pnl"] > 0) / len(settlements)
        if settlements else 0
    )

    avg_pnl = sum(s["pnl"] for s in settlements) / len(settlements) if settlements else 0

    max_dd = _max_drawdown(equity)

    sharpe = _sharpe_ratio(returns)

    return {
        "win_rate": win_rate,
        "avg_pnl": avg_pnl,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "num_trades": len(trades),
        "num_settlements": len(settlements),
    }


def _max_drawdown(equity):
    peak = equity[0]
    max_dd = 0
    for x in equity:
        peak = max(peak, x)
        max_dd = min(max_dd, x - peak)
    return max_dd


def _sharpe_ratio(returns):
    if not returns:
        return 0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(var)
    return mean / std if std > 0 else 0
