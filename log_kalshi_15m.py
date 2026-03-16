# log_kalshi_15m.py
import csv
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

KALSHI_15M_MARKETS = [
    # fill with your 15m market IDs
    # "KXSPY15M", ...
]

def _fetch_15m_market_snapshot(market_id: str) -> dict:
    """
    TODO: wire to your existing Kalshi client.

    Return a dict like:
      {
        "market_id": ...,
        "as_of_utc": ...,
        "bid_yes": ...,
        "ask_yes": ...,
        "last_price": ...,
        "volume": ...,
        ...
      }
    """
    # stub for now
    return {
        "market_id": market_id,
        "as_of_utc": datetime.utcnow().isoformat(),
        "bid_yes": None,
        "ask_yes": None,
        "last_price": None,
        "volume": None,
    }


def _append_15m_log(row: dict) -> None:
    path = os.path.join(DATA_DIR, "kalshi_15m_markets.csv")
    header_needed = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if header_needed:
            writer.writeheader()
        writer.writerow(row)


def run_15m_logger(interval_seconds: int = 60) -> None:
    logger.info("Starting 15m markets logger")
    while True:
        for mid in KALSHI_15M_MARKETS:
            try:
                snap = _fetch_15m_market_snapshot(mid)
                _append_15m_log(snap)
                logger.info(f"Logged 15m snapshot for {mid}")
            except Exception as e:
                logger.error(f"Error logging 15m market {mid}: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_15m_logger()
