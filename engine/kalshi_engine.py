# engine/kalshi_engine.py — v2.2.0 (UTE v3‑aligned)
# ---------------------------------------------------------
# Phase‑2 Kalshi strategy engine (multi‑market version).
#
# Responsibilities:
#   • Take MANY MarketSnapshots per loop.
#   • Compute Kalshi alpha for each snapshot.
#   • Gate on edge threshold.
#   • Emit canonical OrderIntent objects.
#
# Still NO:
#   • Adapters
#   • REST/WS calls
#   • Event loops
#   • Execution
#   • DB writes
# ---------------------------------------------------------

import logging
from dataclasses import dataclass
from typing import List, Dict

from engine.alpha.base import StrategyEngine, AlphaSignal
from engine.market_snapshot import MarketSnapshot
from engine.alpha.kalshi_alpha import kalshi_alpha_from_snapshot
from models.order_intent import OrderIntent, OrderSide, IntentType

logger = logging.getLogger("kalshi-engine")


@dataclass
class KalshiEngineConfig:
    """
    Minimal config for Phase‑2 Kalshi strategy.

    Extendable with:
        - per‑asset edge thresholds
        - per‑asset max size
        - regime filters
        - time‑of‑day filters
    """
    edge_trigger: float = 0.08
    logging_only: bool = False
    default_size: float = 1.0  # contracts per trade


class KalshiEngine(StrategyEngine):
    """
    Phase‑2 Kalshi strategy engine.

    Pure function:
        Dict[ticker → MarketSnapshot] → list[OrderIntent]

    All I/O, execution, and risk are handled by the centralized executor.
    """

    STRATEGY_ID = "kalshi"

    def __init__(self, config: KalshiEngineConfig | None = None):
        self.config = config or KalshiEngineConfig()

    # ---------------------------------------------------------
    # Alpha → Intent
    # ---------------------------------------------------------
    def _alpha_to_intent(self, alpha: AlphaSignal, snapshot: MarketSnapshot) -> OrderIntent | None:
        """
        Convert a single AlphaSignal + MarketSnapshot into an OrderIntent,
        applying a simple edge threshold.
        """
        edge = alpha.edge
        if abs(edge) < self.config.edge_trigger:
            logger.info(
                f"ALPHA | {snapshot.ticker} | edge={edge:.4f} "
                f"< trigger={self.config.edge_trigger:.4f} → no intent"
            )
            return None

        # Direction: yes/long → BUY, no/short → SELL
        if alpha.direction in ("yes", "long"):
            side = OrderSide.BUY
            limit_price = snapshot.yes_price
        else:
            side = OrderSide.SELL
            limit_price = snapshot.no_price

        size = self.config.default_size

        logger.info(
            f"INTENT | {snapshot.ticker} | dir={alpha.direction} "
            f"edge={edge:.4f} size={size} price={limit_price:.4f}"
        )

        if self.config.logging_only:
            logger.info("INTENT | logging_only=True (no live execution expected)")

        return OrderIntent(
            venue_id="kalshi",
            asset=snapshot.ticker,
            side=side,
            size=size,
            limit_price=limit_price,
            intent_type=IntentType.OPEN,
            strategy_id=self.STRATEGY_ID,
            timestamp=snapshot.timestamp,
        )

    # ---------------------------------------------------------
    # Main Strategy Entry Point (multi‑market)
    # ---------------------------------------------------------
    def generate_intents(self, snapshots: Dict[str, MarketSnapshot]) -> List[OrderIntent]:
        """
        Given MANY MarketSnapshots, compute Kalshi alpha for each and
        emit zero or more OrderIntent objects.
        """
        intents: List[OrderIntent] = []

        for ticker, snapshot in snapshots.items():
            alpha = kalshi_alpha_from_snapshot(snapshot)
            if not alpha:
                logger.info(f"ALPHA | {ticker} | no kalshi_alpha → no intents")
                continue

            logger.info(
                f"ALPHA | {ticker} | dir={alpha.direction} "
                f"edge={alpha.edge:.4f} conf={alpha.confidence:.4f}"
            )

            intent = self._alpha_to_intent(alpha, snapshot)
            if intent:
                intents.append(intent)

        return intents
