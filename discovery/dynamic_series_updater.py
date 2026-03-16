# ute/discovery/dynamic_series_updater.py
# Version: 1.1.0 — Dynamic Kalshi Series Updater (Corrected for v11.2.0 REST Adapter)
#
# Responsibilities:
#   • Fetch the full Kalshi series universe from Elections REST
#   • Retry on failure with exponential backoff
#   • Write atomically to ~/ute/data/kalshi_universe/series.json
#   • Zero drift: taxonomy always stays fresh

import json
import os
import time
import logging
import asyncio
from typing import Any, Dict

from adapters.kalshi_rest_adapter import KalshiRESTAdapter

# -------------------------------------------------------------------
# Credentials (PEM CONTENTS REQUIRED)
# -------------------------------------------------------------------
KALSHI_KEY_ID = os.getenv("KALSHI_API_KEY", "")
KALSHI_KEY_PATH = os.path.expanduser(
    os.getenv("KALSHI_PRIVATE_KEY_PATH", "~/.secrets/kalshi/kalshi_full_key.pem")
)
KALSHI_BASE_URL = os.getenv(
    "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
)

# -------------------------------------------------------------------
# Logging Setup
# -------------------------------------------------------------------
logger = logging.getLogger("dynamic_series_updater")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
SERIES_PATH = os.path.expanduser("~/ute/data/kalshi_universe/series.json")
TMP_PATH = SERIES_PATH + ".tmp"

MAX_RETRIES = 5
BACKOFF_SECONDS = 2


# -------------------------------------------------------------------
# Helper: Atomic Write
# -------------------------------------------------------------------
def _atomic_write(path: str, data: Dict[str, Any]) -> None:
    """
    Write JSON atomically:
        • Write to .tmp
        • fsync
        • Rename to final path
    Ensures no partial writes.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(TMP_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())

    os.replace(TMP_PATH, path)


# -------------------------------------------------------------------
# Main Updater
# -------------------------------------------------------------------
def update_series_file() -> bool:
    """
    Fetch the full series universe from Kalshi and overwrite series.json.
    Returns True on success, False on failure.
    """

    if not KALSHI_KEY_ID:
        logger.error("Missing KALSHI_API_KEY environment variable")
        return False

    # Load PEM contents (KalshiRESTAdapter requires PEM, not a path)
    with open(KALSHI_KEY_PATH, "r") as f:
        key_pem = f.read()

    # REST client
    client = KalshiRESTAdapter(
        key_id=KALSHI_KEY_ID,
        key_secret=key_pem,
        base_url=KALSHI_BASE_URL,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Fetching Kalshi series universe (attempt {attempt}/{MAX_RETRIES})"
            )

            resp = asyncio.run(client.get_series())
            series = resp.get("series", resp)

            if not isinstance(series, list):
                raise ValueError("Invalid series response structure")

            logger.info(f"Fetched {len(series)} series — writing to disk")

            _atomic_write(SERIES_PATH, {"series": series})

            logger.info(f"[OK] Updated series.json successfully → {SERIES_PATH}")
            return True

        except Exception as e:
            logger.error(f"Error fetching series: {e}")

            if attempt < MAX_RETRIES:
                sleep_time = BACKOFF_SECONDS**attempt
                logger.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.critical("Max retries reached — update failed")
                return False
