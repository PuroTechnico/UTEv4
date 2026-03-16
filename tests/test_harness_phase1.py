import asyncio
from datetime import datetime, timezone

from adapters.crypto_s3_adapter import CryptoS3Adapter
from adapters.kalshi_rest_adapter import KalshiRESTAdapter
from dashboard.service import DashboardService
from discovery.market_locator import CryptoMarketLocator
from discovery.universe_builder import build_universe
from health.health_pipeline import HealthPipeline
from pipelines.snapshot_pipeline import SnapshotPipeline
from runtime_config import validate_runtime_config


def run_phase1_harness():
    print("=== UTE v3 Phase 1 Harness ===")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")

    config = validate_runtime_config(strict=True)
    universe = build_universe(str(config.series_path))
    kalshi = KalshiRESTAdapter(
        key_id=config.kalshi_api_key,
        key_secret=config.kalshi_private_key_pem,
        base_url=config.kalshi_base_url,
    )
    locator = CryptoMarketLocator(rest=kalshi)
    crypto_s3 = CryptoS3Adapter.create()
    snapshot_pipeline = SnapshotPipeline(
        universe=universe,
        kalshi=kalshi,
        locator=locator,
        crypto_s3=crypto_s3,
    )
    health_pipeline = HealthPipeline()
    dashboard_service = DashboardService()

    # 1. Run snapshot pipeline once
    snapshots = asyncio.run(snapshot_pipeline.run())
    print("\n[SNAPSHOT PIPELINE]")
    for k, v in snapshots.items():
        print(f"  {k}: {v}")

    # 2. Run health pipeline once
    health = health_pipeline.run()
    print("\n[HEALTH PIPELINE]")
    for k, v in health.items():
        print(f"  {k}: {v}")

    # 3. Build dashboard view models once
    vm = dashboard_service.build()
    print("\n[DASHBOARD VIEW MODELS]")
    print(vm)

    print("\n=== Phase 1 Harness Complete ===")


if __name__ == "__main__":
    run_phase1_harness()
