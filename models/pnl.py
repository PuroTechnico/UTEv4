from dataclasses import dataclass
from datetime import datetime


@dataclass
class PnLRecord:
    timestamp: datetime
    equity: float
    realized: float
    unrealized: float
