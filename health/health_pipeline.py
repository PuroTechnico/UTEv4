from datetime import datetime
from typing import Dict, Any

from database.db import insert, to_json
from models.health import HealthSnapshot


class HealthPipeline:
    """
    UTE v3 Health Pipeline
    - Writes engine heartbeat
    - Writes venue health (stubbed for Phase 1)
    - Writes pipeline health (stubbed for Phase 1)
    """

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def run(self):
        """
        Write all health snapshots.
        """
        engine = self._write_engine_heartbeat()
        kalshi = self._write_venue_health("kalshi")
        coinbase = self._write_venue_health("coinbase")
        weather = self._write_venue_health("weather")

        return {
            "engine": engine,
            "kalshi": kalshi,
            "coinbase": coinbase,
            "weather": weather,
        }

    # ---------------------------------------------------------
    # Engine Heartbeat
    # ---------------------------------------------------------
    def _write_engine_heartbeat(self) -> HealthSnapshot:
        snapshot = HealthSnapshot(
            component="engine",
            status="OK",
            timestamp=datetime.utcnow(),
            metadata={"message": "heartbeat"},
        )

        insert(
            "health_snapshot",
            {
                "component": snapshot.component,
                "status": snapshot.status,
                "timestamp": snapshot.timestamp.isoformat(),
                "metadata": to_json(snapshot.metadata),
            },
        )

        return snapshot

    # ---------------------------------------------------------
    # Venue Health (Phase 1 stubs)
    # ---------------------------------------------------------
    def _write_venue_health(self, venue_id: str) -> HealthSnapshot:
        """
        Phase 1: Always OK.
        Phase 2: Will include API connectivity checks.
        """
        snapshot = HealthSnapshot(
            component=f"venue:{venue_id}",
            status="OK",
            timestamp=datetime.utcnow(),
            metadata={"message": "stub"},
        )

        insert(
            "health_snapshot",
            {
                "component": snapshot.component,
                "status": snapshot.status,
                "timestamp": snapshot.timestamp.isoformat(),
                "metadata": to_json(snapshot.metadata),
            },
        )

        return snapshot
