# engine/main.py
# ---------------------------------------------------------
# Version: 3.2.0 — Engine with injected SnapshotPipeline
#
# Responsibilities:
#   • Run SnapshotPipeline (Crypto + Weather + S3)
#   • Run HealthPipeline
#   • Maintain loop timing
#
# Notes:
#   • SnapshotPipeline is now injected by Orchestrator
#   • Engine no longer constructs its own pipeline
#   • This enables v4.4 multi‑market crypto routing
#   • Strategy/risk/execution still disabled in Phase 2
# ---------------------------------------------------------

import time
import asyncio
import logging
from datetime import datetime

from health.health_pipeline import HealthPipeline
from database.db import insert


logger = logging.getLogger("Engine")


class Engine:
    """
    UTE v3.2 Engine (Phase 2)
    - Runs injected SnapshotPipeline (v4.4+)
    - Runs HealthPipeline
    - No strategy/risk/execution yet
    """

    def __init__(self, loop_interval_seconds: float = 5.0, snapshot_pipeline=None):
        self.loop_interval_seconds = loop_interval_seconds

        # SnapshotPipeline is now dependency-injected
        if snapshot_pipeline is None:
            raise ValueError(
                "Engine requires a SnapshotPipeline instance (v4.4+). "
                "Pass snapshot_pipeline=SnapshotPipeline() from Orchestrator."
            )

        self.snapshot_pipeline = snapshot_pipeline
        self.health_pipeline = HealthPipeline()
        self.running = False

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def start(self):
        """
        Start the engine loop.
        """
        self.running = True
        logger.info("[ENGINE] Starting UTE v3.2 engine loop...")

        while self.running:
            loop_start = datetime.utcnow()

            # -----------------------------
            # 1. Run Snapshot Pipeline (async)
            # -----------------------------
            snapshot_result = asyncio.run(self.snapshot_pipeline.run())

            # -----------------------------
            # 2. Run Health Pipeline
            # -----------------------------
            health_result = self.health_pipeline.run()

            # -----------------------------
            # 3. Loop Timing + Logging
            # -----------------------------
            loop_end = datetime.utcnow()
            elapsed = (loop_end - loop_start).total_seconds()

            market_keys = list(snapshot_result["market"].keys())
            crypto_keys = list(snapshot_result["crypto_s3"].keys())

            logger.info(
                "[ENGINE] Loop completed in %.3fs (markets=%d crypto_s3=%d)",
                elapsed,
                len(market_keys),
                len(crypto_keys),
            )

            # Write basic loop metrics for observability
            try:
                insert(
                    "metrics_record",
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "sharpe": None,
                        "sortino": None,
                        "calmar": None,
                        "max_drawdown": None,
                        "win_rate": None,
                        "avg_win": None,
                        "avg_loss": None,
                        "slippage": None,
                        "liquidity_cost": None,
                    },
                )
            except Exception as e:
                logger.warning("Failed to insert metrics record: %s", e)

            # Sleep until next loop
            time.sleep(self.loop_interval_seconds)

    def stop(self):
        """
        Stop the engine loop.
        """
        self.running = False
        print("[ENGINE] Stopping UTE v3.2 engine loop...")
