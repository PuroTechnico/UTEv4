from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class ExecutionIntent:
    venue_id: str
    ticker: str
    side: str  # "BUY" / "SELL"
    size: float
    limit_price: float
    strategy_id: str
    alpha_id: str
    metadata: Optional[Dict[str, str]] = None
    risk_reason: Optional[str] = None
    risk_approved: bool = True


@dataclass
class ExecutionRecord:
    venue_id: str
    ticker: str
    side: str
    size: float
    price: float
    timestamp: datetime
    intent_id: str


@dataclass
class FillRecord:
    venue_id: str
    ticker: str
    side: str
    size: float
    price: float
    fee_cost: float
    is_taker: bool
    created_time: datetime
    trade_id: Optional[str] = None


@dataclass
class TradeRecord:
    venue_id: str
    ticker: str
    side: str
    size: float
    price: float
    status: str  # "OPEN" / "FILLED" / "CANCELED" / "PARTIAL"
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class SettlementRecord:
    venue_id: str
    ticker: str
    pnl: float
    payout: float
    settled_time: datetime
    trade_id: Optional[str] = None
