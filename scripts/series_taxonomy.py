#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# series_taxonomy.py
# Version: 0.4.0-stable
#
# Deterministic metadata layer over Kalshi series.json.
# Focus: crypto 15m, crypto hourly, crypto daily, weather.
#
# Uses the fields that are actually present in your universe:
#   - category == "Crypto"
#   - frequency in {"fifteen_min", "hourly", "daily", ...}
#   - category == "Climate and Weather" for weather.
#
# IMPORTANT CRYPTO SYNTAX NOTES (DOCUMENTED FROM LIVE DATA):
#
# 1) 15m series (KXBTC15M, KXETH15M, KXSOL15M, KXXRP15M)
#    - Event ticker:  <SERIES>-<YYMMMDDHHMM>
#      e.g. KXBTC15M-26MAR111445
#    - Market ticker: <SERIES>-<YYMMMDDHHMM>-<MM>
#      where <MM> ∈ {00,15,30,45}
#      e.g. KXBTC15M-26MAR111445-45
#    - Time basis: US/Eastern, 24h clock.
#    - Active rule: at wall-clock time T, round UP to the next 15m boundary;
#      the active market is the one ending in -00/-15/-30/-45 for that slot.
#
# 2) Hourly BTC above/below (KXBTCD)
#    - Event ticker:  <SERIES>-<YYMMMDD><HH>
#      e.g. KXBTCD-26MAR1120
#    - Market ticker: <SERIES>-<YYMMMDD><HH>-T<FLOOR_STRIKE>
#      e.g. KXBTCD-26MAR1120-T70249.99
#
# 3) Hourly BTC range (KXBTC)
#    - Event ticker:  <SERIES>-<YYMMMDD><HH>
#      e.g. KXBTC-26MAR1120
#    - Market ticker: <SERIES>-<YYMMMDD><HH>-B<CENTER>
#      e.g. KXBTC-26MAR1120-B70125
#
# This file does NOT compute the active ticker itself; it discovers
# active markets via the Elections API status field for each series.
#

import json
import os
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from adapters.kalshi_rest_adapter import KalshiRESTAdapter


Series = Dict[str, Any]


@dataclass
class SeriesTaxonomyIndex:
    by_ticker: Dict[str, Series]
    by_category: Dict[str, List[Series]]
    by_frequency: Dict[str, List[Series]]
    by_tag: Dict[str, List[Series]]

    # Pre-filtered subsets for current engines
    crypto_15m: List[Series]
    crypto_hourly: List[Series]
    crypto_daily: List[Series]
    weather: List[Series]


def load_universe(path: str) -> List[Series]:
    """
    Load the full Kalshi series universe from series.json.

    Expected top-level structure:
        { "series": [ { ... }, { ... }, ... ] }
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Series file not found: {path}")

    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "series" not in data:
        raise ValueError("Expected top-level object with key 'series'")

    series = data["series"]
    if not isinstance(series, list):
        raise ValueError("Expected 'series' to be a list")

    return series


def is_active_market(ticker: str, client: KalshiRESTAdapter) -> bool:
    """
    Check if a single market is active via /markets/{ticker}.
    """
    try:
        resp = client.get_market_sync(ticker)
        market = resp.get("market", resp)
        return market.get("status") == "active"
    except Exception:
        return False


def filter_active_universe(index: SeriesTaxonomyIndex) -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover active markets (status == 'active') under each series.

    NOTE:
        - We query Elections API /markets with series_ticker.
        - Response shape: { "cursor": "...", "markets": [ ... ] }
        - We filter by market["status"] == "active".
    """

    client = KalshiRESTAdapter(
        key_id="",
        key_secret="",  # PEM contents in production
        base_url="https://api.elections.kalshi.com/trade-api/v2",
    )

    active: Dict[str, List[Dict[str, Any]]] = {
        "crypto_15m": [],
        "crypto_hourly": [],
        "crypto_daily": [],
        "weather": [],
    }

    def fetch_active_markets_for_series(series_ticker: str) -> List[Dict[str, Any]]:
        try:
            resp = client.get_markets_sync(series_ticker=series_ticker, limit=500)
        except Exception:
            return []

        markets = resp.get("markets", [])
        if not isinstance(markets, list):
            return []

        return [m for m in markets if m.get("status") == "active"]

    # Crypto 15m
    for s in index.crypto_15m:
        active["crypto_15m"].extend(fetch_active_markets_for_series(s["ticker"]))

    # Crypto hourly
    for s in index.crypto_hourly:
        active["crypto_hourly"].extend(fetch_active_markets_for_series(s["ticker"]))

    # Crypto daily
    for s in index.crypto_daily:
        active["crypto_daily"].extend(fetch_active_markets_for_series(s["ticker"]))

    # Weather
    for s in index.weather:
        active["weather"].extend(fetch_active_markets_for_series(s["ticker"]))

    # Close the underlying aiohttp session cleanly
    client.close_sync()
    return active


def _safe_category(s: Series) -> str:
    return s.get("category") or ""


def _safe_frequency(s: Series) -> str:
    return s.get("frequency") or ""


def _safe_tags(s: Series) -> List[str]:
    tags = s.get("tags")
    if isinstance(tags, list):
        return [t for t in tags if isinstance(t, str)]
    return []


def print_focus_tickers(index: SeriesTaxonomyIndex) -> None:
    """
    Print the actual tickers for the focus subsets:
    - Crypto 15m
    - Crypto hourly
    - Crypto daily
    - Weather
    """
    print("\n=== Crypto 15m Series (tickers) ===")
    for s in index.crypto_15m:
        print(f"  {s['ticker']:20s}  {s.get('title','')}")

    print("\n=== Crypto Hourly Series (tickers) ===")
    for s in index.crypto_hourly:
        print(f"  {s['ticker']:20s}  {s.get('title','')}")

    print("\n=== Crypto Daily Series (tickers) ===")
    for s in index.crypto_daily:
        print(f"  {s['ticker']:20s}  {s.get('title','')}")

    print("\n=== Weather Series (tickers) ===")
    for s in index.weather:
        print(f"  {s['ticker']:20s}  {s.get('title','')}")


def build_taxonomy(series_list: List[Series]) -> SeriesTaxonomyIndex:
    """
    Build all indexes + pre-filtered subsets from the raw series list.
    """
    by_ticker: Dict[str, Series] = {}
    by_category: Dict[str, List[Series]] = defaultdict(list)
    by_frequency: Dict[str, List[Series]] = defaultdict(list)
    by_tag: Dict[str, List[Series]] = defaultdict(list)

    crypto_15m: List[Series] = []
    crypto_hourly: List[Series] = []
    crypto_daily: List[Series] = []
    weather: List[Series] = []

    for s in series_list:
        ticker = s.get("ticker")
        if not ticker or not isinstance(ticker, str):
            continue

        by_ticker[ticker] = s

        cat = _safe_category(s)
        freq = _safe_frequency(s)
        tags = _safe_tags(s)

        by_category[cat].append(s)
        by_frequency[freq].append(s)
        for t in tags:
            by_tag[t].append(s)

        # --- Crypto subsets (what actually works in your universe) ---
        if cat == "Crypto":
            if freq == "fifteen_min":
                crypto_15m.append(s)
            elif freq == "hourly":
                crypto_hourly.append(s)
            else:
                # everything else in Crypto that is not 15m/hourly → daily bucket
                crypto_daily.append(s)

        # --- Weather subset (broad, you can refine later) ---
        if "Daily temperature" in tags:
            weather.append(s)

    return SeriesTaxonomyIndex(
        by_ticker=by_ticker,
        by_category=dict(by_category),
        by_frequency=dict(by_frequency),
        by_tag=dict(by_tag),
        crypto_15m=crypto_15m,
        crypto_hourly=crypto_hourly,
        crypto_daily=crypto_daily,
        weather=weather,
    )


def describe_taxonomy(index: SeriesTaxonomyIndex) -> None:
    """
    Print a compact summary of the taxonomy and key subsets.
    """
    total = len(index.by_ticker)
    print(f"Total series in universe: {total}")

    cat_counts = Counter({k: len(v) for k, v in index.by_category.items()})
    freq_counts = Counter({k: len(v) for k, v in index.by_frequency.items()})

    print("\nBy category (top 10):")
    for cat, count in cat_counts.most_common(10):
        print(f"  {cat:25s} {count:5d}")

    print("\nBy frequency:")
    for freq, count in freq_counts.most_common():
        print(f"  {freq:25s} {count:5d}")

    print("\nFocus subsets:")
    print(f"  Crypto 15m series:   {len(index.crypto_15m)}")
    print(f"  Crypto hourly series:{len(index.crypto_hourly)}")
    print(f"  Crypto daily series: {len(index.crypto_daily)}")
    print(f"  Weather series:      {len(index.weather)}")


def find_series_by_ticker(index: SeriesTaxonomyIndex, ticker: str) -> Optional[Series]:
    return index.by_ticker.get(ticker)


def filter_crypto_15m(index: SeriesTaxonomyIndex) -> List[Series]:
    return list(index.crypto_15m)


def filter_crypto_hourly(index: SeriesTaxonomyIndex) -> List[Series]:
    return list(index.crypto_hourly)


def filter_crypto_daily(index: SeriesTaxonomyIndex) -> List[Series]:
    return list(index.crypto_daily)


def filter_weather(index: SeriesTaxonomyIndex) -> List[Series]:
    return list(index.weather)


def filter_by_tag(index: SeriesTaxonomyIndex, tag: str) -> List[Series]:
    return list(index.by_tag.get(tag, []))


def filter_by_category_and_frequency(
    index: SeriesTaxonomyIndex,
    category: str,
    frequency: str,
) -> List[Series]:
    out: List[Series] = []
    for s in index.by_category.get(category, []):
        if _safe_frequency(s) == frequency:
            out.append(s)
    return out


def load_default_taxonomy() -> SeriesTaxonomyIndex:
    default_path = os.path.expanduser(
        "~/ute/data/kalshi_universe/series.json"
    )
    series_list = load_universe(default_path)
    return build_taxonomy(series_list)


if __name__ == "__main__":
    idx = load_default_taxonomy()
    describe_taxonomy(idx)
    print_focus_tickers(idx)
    for ticker in ["KXBTC15M", "ETHD", "KXSOLD", "KXETHEU"]:
        s = find_series_by_ticker(idx, ticker)
        if s:
            print(
                f"\n[INFO] {ticker}: "
                f"category={s.get('category')} "
                f"frequency={s.get('frequency')} "
                f"title={s.get('title')!r}"
            )
        else:
            print(f"\n[WARN] {ticker} not found in taxonomy.")

def filter_daily_temperature(index: SeriesTaxonomyIndex) -> List[Series]:
    return index.by_tag.get("Daily temperature", [])
