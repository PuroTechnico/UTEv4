"""
engine_state.py — v5.0.0-production
---------------------------------------------------------
Canonical engine state tracker for the unified Kalshi engine.

Responsibilities:
    • Track loop count
    • Track loop start timestamps
    • Track last error message
    • Provide timing metrics for diagnostics
    • Provide reset hooks for circuit breaker integration

This module intentionally remains lightweight but now includes
production-grade structure and documentation.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EngineState:
    """
    Tracks engine loop state and timing.

    Fields:
        loop_counter      Total number of loops executed
        last_loop_start   Timestamp of the most recent loop start
        last_error        Last error message (if any)
        last_loop_duration  Duration of the previous loop (seconds)
    """

    loop_counter: int = 0
    last_loop_start: float = field(default_factory=time.time)
    last_error: Optional[str] = None
    last_loop_duration: float = 0.0

    def start_loop(self) -> None:
        """
        Mark the beginning of a new engine loop.
        """
        now = time.time()
        self.loop_counter += 1
        self.last_loop_duration = now - self.last_loop_start
        self.last_loop_start = now

    def record_error(self, msg: str) -> None:
        """
        Store the last error message for diagnostics.
        """
        self.last_error = msg

    def reset_error(self) -> None:
        """
        Clear the last error message.
        """
        self.last_error = None

    def get_loop_metrics(self) -> dict:
        """
        Return a dictionary of loop timing metrics.
        Useful for debugging, logging, or dashboard health tiles.
        """
        return {
            "loop_counter": self.loop_counter,
            "last_loop_duration": round(self.last_loop_duration, 4),
            "last_error": self.last_error,
        }
