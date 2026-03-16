# ute/database/db.py
# Version: 3.3 — Coinbase removed, schema_v4.1 aligned.
#
# Notes:
#   - DB_PATH now explicitly resolves to ute_trading.db
#   - No Coinbase logic remains
#   - This file will be replaced in Phase 3 with a multi‑DB architecture:
#         market_data.db, weather_data.db, crypto_data.db, opportunities.db, execution.db
#   - For now, this is the stable, canonical single‑DB interface.

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ------------------------------------------------------------
# Canonical DB path (single‑DB mode)
# ------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parent.parent / "ute_trading.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with row_factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema_v4():
    """
    Initialize schema_v4.1.sql (Kalshi + Weather + Crypto S3 only).
    Coinbase schema removed.

    If the DB file already exists, this function assumes schema migrations
    are either already applied or handled elsewhere.
    """
    if DB_PATH.exists():
        return

    schema_path = Path(__file__).parent / "schema_v4.sql"
    with get_connection() as conn:
        conn.executescript(schema_path.read_text())
        conn.commit()


def insert(table: str, data: Dict[str, Any]):
    """
    Generic insert helper.
    Converts dict → INSERT INTO table (keys...) VALUES (...).
    """
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())

    with get_connection() as conn:
        conn.execute(
            f"INSERT INTO {table} ({keys}) VALUES ({placeholders})",
            values,
        )
        conn.commit()


def query(sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """
    Generic SELECT helper.
    Returns list of sqlite3.Row objects.
    """
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def get_table_columns(table: str) -> List[str]:
    """Return ordered list of column names for a table."""
    with get_connection() as conn:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cur.fetchall()]


def to_json(obj: Any) -> str:
    """
    Serialize Python objects to JSON for DB storage.
    """
    return json.dumps(obj) if obj is not None else None
