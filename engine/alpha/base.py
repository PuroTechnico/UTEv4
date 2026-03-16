# engine/alpha/base.py — v2.0.0
# ---------------------------------------------------------
# Phase‑2 canonical alpha + strategy interface.
# - AlphaSignal remains unchanged (still used by some engines)
# - Legacy TradeIntent removed
# - New StrategyEngine abstract base added
# - Strategies now emit OrderIntent objects
# ---------------------------------------------------------

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import uuid
import datetime

# Phase‑2 canonical order intent
from ute.models.order_intent import OrderIntent


# ---------------------------------------------------------
# AlphaSignal (unchanged)
# ---------------------------------------------------------

@dataclass
class AlphaSignal:
    """
    Canonical representation of a model's belief about a market.
    """
    id: str
    source: str              # "kalshi_15m", "weather", "pairs", etc.
    asset: str               # "BTC", "ETH", etc.
    market: str              # venue-specific ticker
    direction: str           # "yes", "no", "long", "short"
    confidence: float        # 0–1
    edge: float              # model-specific edge score
    timeframe: str           # "15m", "1h", "event"
    expiry: Optional[datetime.datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(
        source: str,
        asset: str,
        market: str,
        direction: str,
        confidence: float,
        edge: float,
        timeframe: str,
        expiry: Optional[datetime.datetime],
        metadata: Dict[str, Any],
    ):
        return AlphaSignal(
            id=str(uuid.uuid4()),
            source=source,
            asset=asset,
            market=market,
            direction=direction,
            confidence=confidence,
            edge=edge,
            timeframe=timeframe,
            expiry=expiry,
            metadata=metadata or {},
        )


# ---------------------------------------------------------
# StrategyEngine (new for Phase‑2)
# ---------------------------------------------------------

class StrategyEngine(ABC):
    """
    Base class for all strategy engines (turtle, pairs, coinbase, kalshi).
    Every strategy must implement generate_intents() and return a list
    of canonical OrderIntent objects.
    """

    @abstractmethod
    def generate_intents(self, snapshot: Any) -> List[OrderIntent]:
        """
        Given the latest snapshot(s), return a list of OrderIntent objects.
        """
        ...
