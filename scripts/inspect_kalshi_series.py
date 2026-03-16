#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# scripts/inspect_kalshi_series.py
# Version: 0.1.0-series-introspect
#
# Introspect and validate the full Kalshi series universe (series.json).
#
# Usage (from project root):
#   python -m scripts.inspect_kalshi_series --path /home/kalshi/.secrets/series.json
#

import argparse
import json
import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple


def load_series(path: str) -> List[Dict[str, Any]]:
    """
    Load the full series.json file and return the list of series objects.

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


def summarize_series(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build high-level summary stats over the series universe.
    """
    by_category: Counter = Counter()
    by_frequency: Counter = Counter()
    by_fee_type: Counter = Counter()
    by_tag: Counter = Counter()
    missing_tags = 0

    for s in series:
        cat = s.get("category", "UNKNOWN")
        freq = s.get("frequency", "UNKNOWN")
        fee_type = s.get("fee_type", "UNKNOWN")

        by_category[cat] += 1
        by_frequency[freq] += 1
        by_fee_type[fee_type] += 1

        tags = s.get("tags")
        if tags is None:
            missing_tags += 1
        elif isinstance(tags, list):
            for t in tags:
                by_tag[t] += 1

    return {
        "total_series": len(series),
        "by_category": by_category,
        "by_frequency": by_frequency,
        "by_fee_type": by_fee_type,
        "by_tag": by_tag,
        "missing_tags": missing_tags,
    }


def index_by_ticker(series: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build a ticker -> series map for fast lookup.
    """
    index: Dict[str, Dict[str, Any]] = {}
    for s in series:
        ticker = s.get("ticker")
        if not ticker:
            continue
        index[ticker] = s
    return index


def print_summary(summary: Dict[str, Any]) -> None:
    """
    Pretty-print the summary stats.
    """
    print(f"Total series: {summary['total_series']}")
    print("\nBy category:")
    for cat, count in summary["by_category"].most_common():
        print(f"  {cat:25s} {count:5d}")

    print("\nBy frequency:")
    for freq, count in summary["by_frequency"].most_common():
        print(f"  {freq:25s} {count:5d}")

    print("\nBy fee_type:")
    for ft, count in summary["by_fee_type"].most_common():
        print(f"  {ft:25s} {count:5d}")

    print("\nTop tags:")
    for tag, count in summary["by_tag"].most_common(25):
        print(f"  {tag:25s} {count:5d}")

    print(f"\nSeries with missing tags: {summary['missing_tags']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Kalshi series universe (series.json).")
    parser.add_argument(
        "--path",
        required=True,
        help="Path to series.json (full Kalshi series universe).",
    )
    args = parser.parse_args()

    try:
        series = load_series(args.path)
    except Exception as e:
        print(f"[FATAL] Error loading series file: {e!r}")
        return 1

    summary = summarize_series(series)
    print_summary(summary)

    # Example: sanity check a few key tickers if present.
    ticker_index = index_by_ticker(series)
    for ticker in ["KXBTC15M", "NASDAQ100I", "KXAIRDROPMEGA"]:
        if ticker in ticker_index:
            s = ticker_index[ticker]
            print(f"\n[INFO] Series {ticker}: category={s.get('category')} frequency={s.get('frequency')} title={s.get('title')!r}")
        else:
            print(f"\n[WARN] Series {ticker} not found in universe.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
