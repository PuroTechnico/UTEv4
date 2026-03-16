# crypto_taxonomy.py
# Version: 1.0.0
#
# Canonical classification of all Crypto series into product families.
# This module is the routing brain for:
#   - helper selection
#   - ticker computation strategy
#   - strike/bucket discovery
#   - execution engine routing
#   - backtest loader routing
#
# It does NOT compute tickers. It classifies series.

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CryptoSeriesInfo:
    family: str
    frequency: str
    needs_event_ticker: bool
    needs_full_ticker: bool
    needs_strike_discovery: bool
    mutually_exclusive: bool


def classify_crypto_series(series_ticker: str, frequency: str, mutually_exclusive: bool) -> CryptoSeriesInfo:
    """
    Classify a Crypto series into one of the canonical product families.
    """

    # -----------------------------
    # FAMILY 1 — 15m directional
    # -----------------------------
    if frequency == "fifteen_min":
        return CryptoSeriesInfo(
            family="crypto_15m_directional",
            frequency="15m",
            needs_event_ticker=False,
            needs_full_ticker=True,      # compute full ticker
            needs_strike_discovery=False,
            mutually_exclusive=False,
        )

    # -----------------------------
    # FAMILY 2 — Hourly directional
    # -----------------------------
    if frequency == "hourly" and series_ticker.endswith("D") and series_ticker != "KXBTC":
        return CryptoSeriesInfo(
            family="crypto_hourly_directional",
            frequency="hourly",
            needs_event_ticker=True,     # compute event ticker only
            needs_full_ticker=False,
            needs_strike_discovery=True, # fetch strikes
            mutually_exclusive=False,
        )

    # -----------------------------
    # FAMILY 3 — Hourly range
    # -----------------------------
    if frequency == "hourly" and series_ticker == "KXBTC":
        return CryptoSeriesInfo(
            family="crypto_hourly_range",
            frequency="hourly",
            needs_event_ticker=True,
            needs_full_ticker=False,
            needs_strike_discovery=True, # fetch buckets
            mutually_exclusive=True,
        )

    # -----------------------------
    # FAMILY 4 — Daily directional
    # -----------------------------
    if frequency == "daily":
        return CryptoSeriesInfo(
            family="crypto_daily_directional",
            frequency="daily",
            needs_event_ticker=True,
            needs_full_ticker=False,
            needs_strike_discovery=True,
            mutually_exclusive=False,
        )

    # -----------------------------
    # FAMILY 5 — Annual min/max
    # -----------------------------
    if frequency == "annual":
        return CryptoSeriesInfo(
            family="crypto_annual_minmax",
            frequency="annual",
            needs_event_ticker=True,
            needs_full_ticker=False,
            needs_strike_discovery=True,
            mutually_exclusive=mutually_exclusive,
        )

    # -----------------------------
    # FAMILY 6 — One-off events
    # -----------------------------
    if frequency == "one_off":
        return CryptoSeriesInfo(
            family="crypto_one_off",
            frequency="one_off",
            needs_event_ticker=False,
            needs_full_ticker=False,
            needs_strike_discovery=False,
            mutually_exclusive=mutually_exclusive,
        )

    # -----------------------------
    # FAMILY 7 — Custom crypto events
    # -----------------------------
    return CryptoSeriesInfo(
        family="crypto_custom",
        frequency="custom",
        needs_event_ticker=False,
        needs_full_ticker=False,
        needs_strike_discovery=False,
        mutually_exclusive=mutually_exclusive,
    )
