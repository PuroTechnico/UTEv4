# engine/alpha/intent_builder.py — v2.3.0-production
# ---------------------------------------------------------
# Pure quant intent builder.
#
# v2.3.0:
#   • Removed all legacy “simple logic”.
#   • Removed buy_trigger_simple entirely.
#   • Introduced EDGE_TRIGGER (hard gate on |edge|).
#   • Confidence is now used ONLY for sizing.
#   • No simple thresholds influence trade/no-trade decisions.
# ---------------------------------------------------------

from typing import Optional, Tuple
from engine.alpha.base import AlphaSignal, TradeIntent


# ============================================================
# INTERNAL: Cross-domain sizing logic (confidence-based only)
# ============================================================
def _compute_size_from_alpha(
    alpha: AlphaSignal,
    max_contracts: int,
    edge_trigger: float,
) -> int:
    """
    Cross-domain-aware sizing rule.

    Behavior:
        • Default = 1 contract.
        • Aggregated alpha may size up based on:
              - confidence above edge_trigger
              - number of contributing engines
              - presence/strength of forecast_alpha
        • Never exceed max_contracts.
    """

    size = 1

    if alpha.source == "aggregated":
        components = alpha.metadata.get("components") or {}
        num_components = len(components)
        conf = alpha.confidence  # normalized |edge|

        # Base sizing from components + confidence
        if num_components >= 2 and conf >= edge_trigger + 0.10:
            size = min(2, max_contracts)

        if num_components >= 3 and conf >= edge_trigger + 0.20:
            size = min(3, max_contracts)

        # Forecast-aware bump
        has_forecast = "forecast_alpha" in components
        if has_forecast and conf >= edge_trigger + 0.25:
            size = min(size + 1, max_contracts)

    return max(1, min(size, max_contracts))


# ============================================================
# PUBLIC: Alpha → Intent (edge-gated)
# ============================================================
def intent_from_alpha(
    alpha: AlphaSignal,
    portfolio,
    risk_engine,
    cash: float,
    edge_trigger: float,        # NEW: pure quant gate
    slippage: float,
    max_contracts: int,
    max_total_exposure: int,
    logging_only: bool = False,
) -> Tuple[Optional[TradeIntent], float]:
    """
    Convert a single AlphaSignal into a TradeIntent.

    Behavior:
        • Hard gate: abs(edge) >= edge_trigger
        • Confidence used ONLY for sizing
        • Risk engine enforces exposure
        • Slippage applied to limit price
        • No legacy simple logic anywhere
    """

    # Hard edge gate
    if alpha.edge is None:
        return None, cash

    if abs(alpha.edge) < edge_trigger:
        return None, cash

    # Direction → side
    if alpha.direction in ("yes", "long"):
        side = "buy"
    elif alpha.direction in ("no", "short"):
        side = "sell"
    else:
        return None, cash

    venue = "kalshi"
    symbol = alpha.market

    # Position sizing
    size = _compute_size_from_alpha(
        alpha=alpha,
        max_contracts=max_contracts,
        edge_trigger=edge_trigger,
    )

    # Per-position cap
    if hasattr(portfolio, "get_position"):
        pos = portfolio.get_position(symbol)
        existing = pos["size"] if pos else 0
        if existing + size > max_contracts:
            return None, cash

    # Risk engine exposure check
    yes_price = alpha.metadata.get("yes_price")
    no_price = alpha.metadata.get("no_price")
    price_for_risk = yes_price if side == "buy" else no_price

    if hasattr(risk_engine, "can_open"):
        if not risk_engine.can_open(
            asset=alpha.asset,
            side=side,
            size=size,
            price=price_for_risk or 0.0,
            portfolio=portfolio,
            cash=cash,
        ):
            return None, cash

    # Limit price with slippage
    if side == "buy" and yes_price is not None:
        limit_price = yes_price + slippage
    elif side == "sell" and no_price is not None:
        limit_price = no_price - slippage
    else:
        return None, cash

    # Cash accounting
    notional = limit_price * size
    new_cash = cash if logging_only else max(0.0, cash - notional)

    # Build TradeIntent
    intent = TradeIntent(
        venue=venue,
        symbol=symbol,
        side=side,
        size=size,
        price=limit_price,
        alpha_id=alpha.id,
        risk_tag=alpha.source,
        metadata={
            "edge": alpha.edge,
            "confidence": alpha.confidence,
            "timeframe": alpha.timeframe,
        },
    )

    return intent, new_cash
