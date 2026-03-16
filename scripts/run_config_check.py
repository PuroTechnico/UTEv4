"""Validate runtime configuration before startup/deploy."""

import argparse

from runtime_config import RuntimeConfigError, validate_runtime_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require API key/private key/series universe for runtime startup checks.",
    )
    args = parser.parse_args()

    try:
        cfg = validate_runtime_config(strict=args.strict)
    except RuntimeConfigError as exc:
        print(str(exc))
        return 1

    print("Runtime config check passed")
    print(f"- base_url: {cfg.kalshi_base_url}")
    print(f"- series_path: {cfg.series_path}")
    print(f"- schema_path: {cfg.schema_path}")
    print(f"- db_path: {cfg.db_path}")
    print(f"- key_path_exists: {cfg.kalshi_private_key_path.exists()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
