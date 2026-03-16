# models/opportunities.py — v3.3
# ---------------------------------------------------------
# Coinbase removed from UTE.
# OpportunitySnapshot now reflects:
#   • Kalshi prices
#   • Spread
#   • Volume
#   • Edge score
#   • Readiness
#   • Time-to-expiry
#   • Skip reason
#   • Timestamp
#
# Matches schema_v4.1.sql and SnapshotPipeline v3.3.

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OpportunitySnapshot:
    asset: str
    kalshi_yes: float
    kalshi_no: float
    spread: float
    volume: int
    edge_score: float
    readiness: float
    tte: float
    skip_reason: Optional[str]
    timestamp: datetime
