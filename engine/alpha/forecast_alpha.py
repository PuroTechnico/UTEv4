"""
forecast_alpha.py — v1.0.0
---------------------------------------------------------
Consumes MarketSnapshot v6.0.0 and produces forecast-aware alpha signals.

Inputs:
    • MarketSnapshot (with kalshi_forecast*, implied_prob_*)
Outputs:
    • dict with edge_forecast, edge_vs_price, regime, confidence
"""

from dataclasses import asdict
from typing import Dict, Any
from engine.market_snapshot import MarketSnapshot


def compute_forecast_alpha(snapshot: MarketSnapshot) -> Dict[str, Any]:
    """
    Core forecast alpha:
        • edge_forecast: model-agnostic edge from Kalshi forecast vs implied prob
        • edge_vs_price: forecast vs yes_price
        • regime: low/med/high forecast volatility
        • confidence: scaled by slope + divergence
    """
    f = snapshot.kalshi_forecast
    div = snapshot.kalshi_forecast_divergence
    vol = snapshot.kalshi_forecast_volatility
    slope = snapshot.kalshi_forecast_slope
    imp_mid = snapshot.implied_prob_mid
    yes_price = snapshot.yes_price

    edge_forecast = f - imp_mid
    edge_vs_price = f - yes_price

    if vol < 2:
        regime = "low_vol"
    elif vol < 5:
        regime = "med_vol"
    else:
        regime = "high_vol"

    # crude but monotone confidence
    confidence = max(0.0, min(1.0, (abs(edge_forecast) / 10.0) + (abs(slope) / 10.0)))

    return {
        "edge_forecast": edge_forecast,
        "edge_vs_price": edge_vs_price,
        "regime": regime,
        "confidence": confidence,
        "raw": {
            "kalshi_forecast": f,
            "divergence": div,
            "volatility": vol,
            "slope": slope,
            "implied_mid": imp_mid,
        },
        "snapshot_meta": {
            "asset": snapshot.asset,
            "ticker": snapshot.ticker,
            "event_ticker": snapshot.event_ticker,
            "market_ticker": snapshot.market_ticker,
            "created_at": snapshot.created_at,
        },
    }
