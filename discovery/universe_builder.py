# discovery/universe_builder.py
# Version: 1.1.0 — Correct 15m handling (NO inference)

import json
from pathlib import Path
from typing import Dict, Any, List

from discovery.crypto_taxonomy import classify_crypto_series
from time_utils.active_15m_ticker import FIFTEEN_MIN_SERIES


def _load_raw_series(series_path: Path) -> List[Dict[str, Any]]:
    with series_path.open() as f:
        data = json.load(f)

    if isinstance(data, dict) and "series" in data:
        return data["series"]
    if isinstance(data, list):
        return data

    raise ValueError("Unexpected series.json structure.")


def _is_crypto(series: Dict[str, Any]) -> bool:
    return series.get("category") == "Crypto"


def _is_weather(series: Dict[str, Any]) -> bool:
    return series.get("category") in ("Weather", "Climate", "Weather & Climate")


def _is_15m_crypto(series: Dict[str, Any]) -> bool:
    """
    15m crypto series:
      • ONLY the four deterministic series defined in active_15m_ticker.py
      • Never infer from frequency or ticker patterns
    """
    return series.get("ticker") in FIFTEEN_MIN_SERIES


def _classify_crypto_frequency(series: Dict[str, Any]) -> str:
    ticker = series.get("ticker", "")
    freq = series.get("frequency", "")
    mutually_exclusive = series.get("mutually_exclusive", False)

    info = classify_crypto_series(ticker, freq, mutually_exclusive)

    if (
        info.family == "crypto_hourly_directional"
        or info.family == "crypto_hourly_range"
    ):
        return "crypto_hourly"

    if info.family == "crypto_daily_directional":
        return "crypto_daily"

    return "other"


def build_universe(series_path: str) -> Dict[str, Any]:
    path = Path(series_path).expanduser()
    raw_series = _load_raw_series(path)

    crypto_15m: List[Dict[str, Any]] = []
    crypto_hourly: List[Dict[str, Any]] = []
    crypto_daily: List[Dict[str, Any]] = []
    weather: List[Dict[str, Any]] = []
    climate: List[Dict[str, Any]] = []

    for s in raw_series:

        # Weather / Climate
        if _is_weather(s):
            cat = s.get("category")
            if cat == "Weather":
                weather.append(s)
            elif cat == "Climate":
                climate.append(s)
            else:
                weather.append(s)
                climate.append(s)
            continue

        # Crypto
        if _is_crypto(s):

            # 15m crypto — ONLY the deterministic four
            if _is_15m_crypto(s):
                crypto_15m.append(s)
                continue

            # Hourly / Daily
            bucket = _classify_crypto_frequency(s)
            if bucket == "crypto_hourly":
                crypto_hourly.append(s)
            elif bucket == "crypto_daily":
                crypto_daily.append(s)

    return {
        "crypto_15m": crypto_15m,
        "crypto_hourly": crypto_hourly,
        "crypto_daily": crypto_daily,
        "weather": weather,
        "climate": climate,
    }
