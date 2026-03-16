from dataclasses import dataclass
from datetime import datetime


@dataclass
class PositionRecord:
    venue_id: str
    ticker: str
    side: str  # "LONG" / "SHORT"
    count: int
    entry_price: float
    high_water_mark: float
    created_at: datetime
    updated_at: datetime
