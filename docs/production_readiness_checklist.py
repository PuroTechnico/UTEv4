"""Production Readiness Checklist (As-Built v4.x).

This file is documentation-in-code format for operators and reviewers.
Executable baseline checks live in: scripts/run_production_checklist.py
"""

IMPLEMENTED_CHECKS = {
    "runtime_entrypoint": [
        "orchestrator.py starts successfully",
        "Engine loop runs repeatedly",
    ],
    "database_writes": [
        "market_snapshot rows increasing",
        "weather_snapshot rows increasing",
        "crypto_snapshot rows increasing",
        "health_snapshot rows increasing",
        "metrics_record rows increasing",
    ],
    "discovery_and_routing": [
        "universe loads from data/kalshi_universe/series.json",
        "CryptoMarketLocator returns active market candidates",
    ],
    "health_visibility": [
        "engine heartbeat written",
        "venue status rows written (currently stub-level)",
    ],
}


PLANNED_CHECKS = {
    "risk_and_execution": [
        "risk pipeline integrated into canonical live loop",
        "execution flow integrated and validated in canonical live loop",
    ],
    "position_and_pnl": [
        "position lifecycle updates proven in active runtime path",
        "pnl lifecycle updates proven in active runtime path",
    ],
    "alerting_and_slo": [
        "dedicated alerting module wired",
        "automated SLO monitor with routing and deduplication",
    ],
}


OPERATOR_NOTES = [
    "Use python scripts/run_snapshot_check.py for a one-cycle sanity check.",
    "Use python scripts/run_production_checklist.py for baseline DB readiness checks.",
    "Treat archive/ and run_all.py as non-canonical runtime surfaces.",
]


def print_checklist() -> None:
    print("UTE Production Readiness Checklist (As-Built v4.x)\n")

    print("Implemented checks:")
    for section, items in IMPLEMENTED_CHECKS.items():
        print(f"- {section}")
        for item in items:
            print(f"  - [ ] {item}")

    print("\nPlanned checks:")
    for section, items in PLANNED_CHECKS.items():
        print(f"- {section}")
        for item in items:
            print(f"  - [ ] {item}")

    print("\nOperator notes:")
    for note in OPERATOR_NOTES:
        print(f"- {note}")


if __name__ == "__main__":
    print_checklist()
