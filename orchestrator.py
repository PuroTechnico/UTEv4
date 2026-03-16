# orchestrator.py
# Version: 4.2.0 — Async-ready orchestrator with unified SnapshotPipeline

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from dotenv import load_dotenv
from discovery.universe_builder import build_universe

from database.db import init_schema_v4
from adapters.crypto_s3_adapter import CryptoS3Adapter


# ---------------------------------------------------------
# Load .env (contains KALSHI_API_KEY and KALSHI_API_SECRET)
# ---------------------------------------------------------
load_dotenv()

# API key from .env
KALSHI_KEY_ID = os.getenv("KALSHI_API_KEY")

# Private key stored in ~/.secrets/kalshi/kalshi_full_key.pem
KALSHI_KEY_SECRET_PATH = os.path.expanduser("~/.secrets/kalshi/kalshi_full_key.pem")
with open(KALSHI_KEY_SECRET_PATH, "r") as f:
    KALSHI_KEY_SECRET = f.read()

# Base URL (fallback to elections API if not in .env)
KALSHI_BASE_URL = os.getenv("KALSHI_BASE_URL", "https://api.elections.kalshi.com")


def setup_logging() -> None:
    """Configure global logging for UTE processes."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        "ute.log", maxBytes=8 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


# ---------------------------------------------------------
# Universe loader (your real JSON universe file)
# ---------------------------------------------------------


def load_universe():
    series_path = "/home/maureces/ute/data/kalshi_universe/series.json"
    return build_universe(series_path)


# ---------------------------------------------------------
# Imports for orchestrator wiring
# ---------------------------------------------------------
from engine.main import Engine
from dashboard.service import DashboardService
from pipelines.snapshot_pipeline import SnapshotPipeline
from adapters.kalshi_rest_adapter import KalshiRESTAdapter
from discovery.market_locator import CryptoMarketLocator


class Orchestrator:
    """
    UTE v4.2 Orchestrator
    - Wires together Engine + SnapshotPipeline + DashboardService
    - Engine uses the unified multi-market snapshot pipeline
    """

    def __init__(self, loop_interval_seconds: float = 5.0):

        # Initialize database schema if missing
        init_schema_v4()

        # -----------------------------------------------------
        # 1. Load universe (15m, hourly, daily, weather)
        # -----------------------------------------------------
        self.universe = load_universe()

        # -----------------------------------------------------
        # 2. Kalshi REST adapter (async)
        # -----------------------------------------------------
        self.kalshi = KalshiRESTAdapter(
            key_id=KALSHI_KEY_ID,
            key_secret=KALSHI_KEY_SECRET,
            base_url=KALSHI_BASE_URL,
        )

        # -----------------------------------------------------
        # 2b. Crypto S3 adapter (public no auth)
        # -----------------------------------------------------
        self.crypto_s3 = CryptoS3Adapter.create()

        # -----------------------------------------------------
        # 3. Crypto locator (async)
        # -----------------------------------------------------
        self.locator = CryptoMarketLocator(rest=self.kalshi)

        # -----------------------------------------------------
        # 4. Snapshot pipeline (async)
        # -----------------------------------------------------
        self.snapshot_pipeline = SnapshotPipeline(
            universe=self.universe,
            kalshi=self.kalshi,
            locator=self.locator,
            crypto_s3=self.crypto_s3,
        )

        # -----------------------------------------------------
        # 5. Engine (async snapshot + alpha + intent)
        # -----------------------------------------------------
        self.engine = Engine(
            loop_interval_seconds=loop_interval_seconds,
            snapshot_pipeline=self.snapshot_pipeline,
        )

        # -----------------------------------------------------
        # 6. Dashboard (forward-only)
        # -----------------------------------------------------
        self.dashboard_service = DashboardService()

    # ---------------------------------------------------------
    # Engine control
    # ---------------------------------------------------------
    def start_engine(self):
        """Start the engine loop (blocking)."""
        self.engine.start()

    def stop_engine(self):
        """Stop the engine loop."""
        self.engine.stop()

    # ---------------------------------------------------------
    # Dashboard data access
    # ---------------------------------------------------------
    def get_dashboard_view_models(self):
        """Build and return the current dashboard view models."""
        return self.dashboard_service.build()


def main(loop_interval_seconds: float = 5.0):
    setup_logging()
    orch = Orchestrator(loop_interval_seconds=loop_interval_seconds)
    orch.start_engine()


if __name__ == "__main__":
    main()
