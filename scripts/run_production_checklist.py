"""Automated production readiness checks derived from docs/production_readiness_checklist.py."""

from pathlib import Path
from database.db import get_connection


def run_check():
    db_path = Path(__file__).resolve().parent.parent / "ute_trading.db"
    if not db_path.exists():
        raise FileNotFoundError(
            "Database not initialized. Run orchestrator at least once."
        )

    with get_connection() as conn:
        summary = {}
        for table in [
            "market_snapshot",
            "crypto_snapshot",
            "weather_snapshot",
            "opportunity_snapshot",
            "health_snapshot",
            "metrics_record",
        ]:
            cur = conn.execute(f"SELECT COUNT(*) as c FROM {table}")
            summary[table] = cur.fetchone()["c"]

    print("Production readiness summary:")
    for table, count in summary.items():
        print(f"  {table}: {count}")

    if summary["market_snapshot"] == 0:
        raise RuntimeError(
            "No market_snapshot records found; snapshot pipeline did not persist data."
        )

    if summary["health_snapshot"] == 0:
        raise RuntimeError(
            "No health_snapshot records found; health pipeline not running."
        )

    print("Checklist basic validation passed.")


if __name__ == "__main__":
    run_check()
