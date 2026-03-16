# scripts/validate_kalshi_markets.py
# Version: 0.2.0-crypto-series-filtered
#
# Validation harness: Kalshi markets schema + basic invariants.
#
# Usage (from project root):
#     python -m scripts.validate_kalshi_markets --series KXBTC15M
#

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from adapters.kalshi_rest_adapter import KalshiRESTAdapter


def dump_raw_markets(markets: List[Dict[str, Any]], outdir: str, series: str) -> str:
    """
    Dump the raw markets payload to a timestamped JSON file for forensic inspection.
    """
    os.makedirs(outdir, exist_ok=True)

    # Use timezone-aware UTC to avoid deprecation warnings and keep filenames deterministic.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"kalshi_markets_{series}_{ts}.json"
    fpath = os.path.join(outdir, fname)

    with open(fpath, "w") as f:
        json.dump(markets, f, indent=2, sort_keys=True)

    return fpath


def validate_markets(markets: List[Dict[str, Any]]) -> List[str]:
    """
    Return a list of human-readable error strings.
    Empty list means "passes validation".
    """
    errors: List[str] = []

    if not isinstance(markets, list):
        errors.append(f"Expected list of markets, got {type(markets)}")
        return errors

    if len(markets) == 0:
        errors.append("No markets returned (empty list).")
        return errors

    # Core fields we expect on *real* binary markets (Elections + crypto 15m).
    required_keys = [
        "ticker",
        "strike_type",
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
    ]

    # Optional but highly expected in Elections/crypto schema.
    numeric_strike_keys = ["floor_strike", "cap_strike"]

    for i, m in enumerate(markets):
        prefix = f"market[{i}]"

        # Basic type check.
        if not isinstance(m, dict):
            errors.append(f"{prefix}: expected dict, got {type(m)}")
            continue

        # Required keys present.
        for k in required_keys:
            if k not in m:
                errors.append(f"{prefix}: missing required key '{k}'")

        # Strike keys (if present) should be numeric.
        for k in numeric_strike_keys:
            if k in m and m[k] is not None:
                try:
                    float(m[k])
                except (TypeError, ValueError):
                    errors.append(f"{prefix}: key '{k}' not numeric: {m[k]!r}")

        # Price sanity checks.
        try:
            yes_bid = m.get("yes_bid", None)
            yes_ask = m.get("yes_ask", None)
            no_bid = m.get("no_bid", None)
            no_ask = m.get("no_ask", None)

            # All should be numeric if present.
            for label, v in [
                ("yes_bid", yes_bid),
                ("yes_ask", yes_ask),
                ("no_bid", no_bid),
                ("no_ask", no_ask),
            ]:
                if v is None:
                    errors.append(f"{prefix}: {label} is None")
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    errors.append(f"{prefix}: {label} not numeric: {v!r}")
                    continue
                if fv < 0 or fv > 100:
                    errors.append(f"{prefix}: {label} out of [0,100] range: {fv}")

            # Ordering invariants (only if all numeric).
            try:
                yb = float(yes_bid)
                ya = float(yes_ask)
                nb = float(no_bid)
                na = float(no_ask)

                if yb > ya:
                    errors.append(f"{prefix}: yes_bid ({yb}) > yes_ask ({ya})")
                if nb > na:
                    errors.append(f"{prefix}: no_bid ({nb}) > no_ask ({na})")
            except Exception:
                # Already logged above if non-numeric; skip ordering checks.
                pass

        except Exception as e:
            errors.append(f"{prefix}: unexpected error during price checks: {e!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Kalshi markets schema and invariants.")
    parser.add_argument(
        "--series",
        required=True,
        help="Kalshi series ID (e.g. KXBTC15M, KXHIGHTSEA, etc.)",
    )
    parser.add_argument(
        "--outdir",
        default="data/raw_dumps/kalshi",
        help="Directory to write raw JSON dumps (default: data/raw_dumps/kalshi)",
    )
    args = parser.parse_args()

    series = args.series
    outdir = args.outdir

    # ---------------------------------------------------------------------
    # CREDENTIALS: Load Kalshi REST credentials from environment.
    # This keeps the harness aligned with the production engine.
    # ---------------------------------------------------------------------
    key_id = os.environ.get("KALSHI_KEY_ID")
    key_secret = os.environ.get("KALSHI_PRIVATE_KEY_PATH")
    base_url = os.environ.get("KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")

    if not key_id or not key_secret:
        print("[FATAL] Missing Kalshi credentials in environment variables.", file=sys.stderr)
        print("Required: KALSHI_KEY_ID and KALSHI_PRIVATE_KEY_PATH", file=sys.stderr)
        return 1

    # Instantiate REST adapter (signing, routing, error handling).
    kalshi = KalshiRESTAdapter(
        key_id=key_id,
        key_secret=key_secret,
        base_url=base_url,
    )

    # ---------------------------------------------------------------------
    # FETCH: Pull full series markets payload from Kalshi.
    # ---------------------------------------------------------------------
    try:
        markets = kalshi.get_markets_sync(series)
    except Exception as e:
        print(f"[FATAL] Error fetching markets for series {series}: {e!r}", file=sys.stderr)
        return 1

    # ---------------------------------------------------------------------
    # FILTER: Keep only real, active binary markets.
    #
    # Kalshi returns:
    #   - metadata objects (no market_type)
    #   - finalized/expired markets
    #   - upcoming + current active markets
    #
    # For validation and snapshot design, we only care about:
    #   - market_type == "binary"
    #   - status != "finalized"
    # ---------------------------------------------------------------------
    filtered: List[Dict[str, Any]] = []
    for m in markets:
        if m.get("market_type") != "binary":
            continue
        if m.get("status") == "finalized":
            continue
        filtered.append(m)

    markets = filtered

    dump_path = dump_raw_markets(markets, outdir, series)
    print(f"[INFO] Dumped raw markets JSON to: {dump_path}")

    errors = validate_markets(markets)
    if errors:
        print(f"[FAIL] Validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for err in errors:
            print("  -", err, file=sys.stderr)
        return 2

    print("[OK] Validation passed: markets schema and basic invariants look good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
