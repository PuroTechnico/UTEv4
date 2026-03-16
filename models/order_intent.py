from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class IntentType(str, Enum):
    OPEN = "OPEN"          # opening a new position
    CLOSE = "CLOSE"        # closing an existing position
    FLIP = "FLIP"          # reversing direction
    SCALE_IN = "SCALE_IN"  # increasing size
    SCALE_OUT = "SCALE_OUT" # reducing size


@dataclass
class OrderIntent:
    venue_id: str                 # "kalshi", "coinbase", "weather"
    asset: str                    # "BTC-USD", "YES:KXHIGHTSEA", etc.
    side: OrderSide               # BUY or SELL
    size: float                   # number of contracts or units
    limit_price: Optional[float]  # None for market orders
    intent_type: IntentType       # OPEN, CLOSE, FLIP, SCALE_IN, SCALE_OUT
    strategy_id: str              # "turtle", "pairs", "coinbase", etc.
    timestamp: datetime           # when the intent was generated
