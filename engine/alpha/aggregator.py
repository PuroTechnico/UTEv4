# engine/alpha/aggregator.py — v3.3 (UTE canonical)
# ---------------------------------------------------------
# Aggregates multiple AlphaSignals (Kalshi, Weather, Forecast)
# into a single combined view per asset/market.
#
# Coinbase-domain alphas (pairs, turtle, vol, microstructure)
# have been removed from UTE and now live in the Coinbase project.
# ---------------------------------------------------------

from dataclasses import dataclass
from typing import Dict, List, Optional

from engine.alpha.base import AlphaSignal


@dataclass
class AggregatedAlpha:
    asset: str
    market: str
    combined_direction: str
    combined_confidence: float
    components: Dict[str, AlphaSignal]


def aggregate_alpha(signals: List[AlphaSignal]) -> Optional[AggregatedAlpha]:
    """
    Combine multiple AlphaSignals into a single aggregated view.

    Rules:
        • Kalshi is required. If missing → return None.
        • Direction always follows Kalshi.
        • Confidence starts from Kalshi and is adjusted by:
              - forecast_alpha (custom weighting)
              - weather_alpha (simple boost/dampen)
    """

    if not signals:
        return None

    components = {s.source: s for s in signals}

    # Kalshi is mandatory
    kalshi = components.get("kalshi_15m")
    if kalshi is None:
        return None

    direction = kalshi.direction
    confidence = kalshi.confidence

    # ---------------------------------------------------------
    # Forecast alpha (custom weighting)
    # ---------------------------------------------------------
    forecast_sig = components.get("forecast_alpha")
    if forecast_sig:
        if forecast_sig.direction == direction:
            confidence += 0.10 * forecast_sig.confidence
        else:
            confidence -= 0.175 * forecast_sig.confidence

    # ---------------------------------------------------------
    # Weather alpha (simple boost/dampen)
    # ---------------------------------------------------------
    weather_sig = components.get("weather_alpha")
    if weather_sig:
        if weather_sig.direction == direction:
            confidence += 0.10 * weather_sig.confidence
        else:
            confidence -= 0.15 * weather_sig.confidence

    # Clamp to [0, 1]
    confidence = max(0.0, min(1.0, confidence))

    return AggregatedAlpha(
        asset=kalshi.asset,
        market=kalshi.market,
        combined_direction=direction,
        combined_confidence=confidence,
        components=components,
    )
