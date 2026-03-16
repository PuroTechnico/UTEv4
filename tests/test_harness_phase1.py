from datetime import datetime

from ute.pipelines.snapshot_pipeline import SnapshotPipeline
from ute.health.health_pipeline import HealthPipeline
from ute.dashboard.service import DashboardService


def run_phase1_harness():
    print("=== UTE v3 Phase 1 Harness ===")
    print(f"Started at: {datetime.utcnow().isoformat()}")

    snapshot_pipeline = SnapshotPipeline()
    health_pipeline = HealthPipeline()
    dashboard_service = DashboardService()

    # 1. Run snapshot pipeline once
    snapshots = snapshot_pipeline.run()
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
