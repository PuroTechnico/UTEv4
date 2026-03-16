# engine/alpha/kalshi_alpha.py — v1.0.0-production
# ---------------------------------------------------------
# Converts Kalshi 15m snapshots into AlphaSignal objects.
# This wraps your existing logic without changing behavior.
# ---------------------------------------------------------

from typing import Optional
from engine.alpha.base import AlphaSignal


def kalshi_alpha_from_snapshot(snapshot) -> Optional[AlphaSignal]:
    """
    Convert a Kalshi snapshot into a canonical AlphaSignal.
    Behavior is identical to your existing entry logic.
    """

    # If snapshot is not tradable, skip
    if snapshot.readiness < 40.0:
        return None

    # Determine direction ("yes" or "no")
    direction = "yes" if snapshot.edge_score > 0 else "no"

    # Confidence is normalized edge score (0–1)
    confidence = min(1.0, abs(snapshot.edge_score))

    # Build metadata
    metadata = {
        "yes_price": snapshot.yes_price,
        "no_price": snapshot.no_price,
        "spread": snapshot.spread,
        "volume": snapshot.volume,
        "tte_min": snapshot.tte_min,
        "coinbase_price": snapshot.coinbase_price,
        "readiness": snapshot.readiness,
    }

    return AlphaSignal.new(
        source="kalshi_15m",
        asset=snapshot.asset,
        market=snapshot.ticker,
        direction=direction,
        confidence=confidence,
        edge=snapshot.edge_score,
        timeframe="15m",
        expiry=None,
        metadata=metadata,
    )
