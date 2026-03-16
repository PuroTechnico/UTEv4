from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MetricsRecord:
    timestamp: datetime
    sharpe: Optional[float]
    sortino: Optional[float]
    calmar: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    avg_win: Optional[float]
    avg_loss: Optional[float]
    slippage: Optional[float]
    liquidity_cost: Optional[float]
