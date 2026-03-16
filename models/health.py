from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class HealthSnapshot:
    component: str  # e.g. "engine", "kalshi", "coinbase", "dashboard"
    status: str     # "OK" / "WARN" / "ERROR"
    timestamp: datetime
    metadata: Optional[Dict[str, str]] = None
