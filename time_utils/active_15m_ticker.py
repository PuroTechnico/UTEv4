# active_15m_ticker.py
# Version: 1.1.1
#
# Purpose:
#   Deterministically compute the active 15m event ticker.
#
# Why this exists:
#   - Kalshi does NOT expose the active 15m event via API.
#   - 15m markets follow a fixed, permanent schedule (:00, :15, :30, :45 ET).
#   - The syntax is stable and guaranteed by venue design.
#
# UTE v4 Rule:
#   → 15m markets use local generator (source of truth)
#   → Hourly markets use API discovery (source of truth)

from datetime import datetime, timedelta
import pytz

EASTERN = pytz.timezone("US/Eastern")

MONTH_MAP = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}

FIFTEEN_MIN_SERIES = [
    "KXBTC15M",
    "KXETH15M",
    "KXSOL15M",
    "KXXRP15M",
]


def round_up_to_next_15(dt_eastern: datetime) -> datetime:
    minute = dt_eastern.minute
    remainder = minute % 15

    if remainder == 0:
        return dt_eastern + timedelta(minutes=15)

    delta = 15 - remainder
    return dt_eastern + timedelta(minutes=delta)


def format_event_timestamp(dt_eastern: datetime) -> str:
    yy = dt_eastern.strftime("%y")
    mon = MONTH_MAP[dt_eastern.month]
    dd = dt_eastern.strftime("%d")
    hh = dt_eastern.strftime("%H")
    mm = dt_eastern.strftime("%M")
    return f"{yy}{mon}{dd}{hh}{mm}"


def get_active_15m_ticker(series: str, now_utc: datetime) -> str:
    """
    Compute the active 15m event ticker for a given series.
    """
    if now_utc.tzinfo is None:
        now_utc = pytz.utc.localize(now_utc)

    now_eastern = now_utc.astimezone(EASTERN)
    active_dt = round_up_to_next_15(now_eastern)
    event_stamp = format_event_timestamp(active_dt)
    suffix = active_dt.strftime("%M")

    return f"{series}-{event_stamp}-{suffix}"


def get_all_active_15m_tickers(now_utc: datetime) -> dict:
    """
    Returns a dict of all four 15m tickers.
    """
    return {
        series: get_active_15m_ticker(series, now_utc)
        for series in FIFTEEN_MIN_SERIES
    }
