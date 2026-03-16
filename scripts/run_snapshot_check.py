"""Simple harness to validate SnapshotPipeline and Engine integration."""

import asyncio
import logging
from orchestrator import Orchestrator


def main():
    logging.basicConfig(level=logging.INFO)
    orch = Orchestrator(loop_interval_seconds=1.0)

    try:
        print("Running one SnapshotPipeline cycle...")
        results = asyncio.run(orch.snapshot_pipeline.run())
        print("Snapshot results:", {k: len(v) for k, v in results.items()})
    finally:
        # gracefully stop any running adapter sessions
        if hasattr(orch, "kalshi"):
            try:
                asyncio.run(orch.kalshi.close())
            except Exception:
                pass


if __name__ == "__main__":
    main()
