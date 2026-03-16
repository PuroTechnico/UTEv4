import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class RuntimeConfig:
    kalshi_api_key: str
    kalshi_base_url: str
    kalshi_private_key_path: Path
    kalshi_private_key_pem: str
    series_path: Path
    db_path: Path
    schema_path: Path


class RuntimeConfigError(ValueError):
    pass


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parent


def _read_private_key(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def validate_runtime_config(strict: bool = True) -> RuntimeConfig:
    repo_root = _default_repo_root()

    kalshi_api_key = os.getenv("KALSHI_API_KEY", "").strip()
    kalshi_base_url = os.getenv(
        "KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2"
    ).strip()

    private_key_path = Path(
        os.path.expanduser(
            os.getenv(
                "KALSHI_PRIVATE_KEY_PATH", "~/.secrets/kalshi/kalshi_full_key.pem"
            )
        )
    )

    series_path = Path(
        os.path.expanduser(
            os.getenv(
                "UTE_SERIES_PATH",
                str(repo_root / "data" / "kalshi_universe" / "series.json"),
            )
        )
    )

    db_path = repo_root / "ute_trading.db"
    schema_path = repo_root / "database" / "schema_v4.sql"

    errors: List[str] = []

    if not kalshi_base_url.startswith("https://"):
        errors.append("KALSHI_BASE_URL must start with https://")

    if "/trade-api/" not in kalshi_base_url:
        errors.append(
            "KALSHI_BASE_URL should include trade-api path, e.g. https://api.elections.kalshi.com/trade-api/v2"
        )

    if strict and not kalshi_api_key:
        errors.append("KALSHI_API_KEY is required")

    if not schema_path.exists():
        errors.append(f"Schema file missing: {schema_path}")

    if strict and not private_key_path.exists():
        errors.append(f"Kalshi private key file missing: {private_key_path}")

    key_pem = ""
    if private_key_path.exists():
        try:
            key_pem = _read_private_key(private_key_path)
            if strict and "PRIVATE KEY" not in key_pem:
                errors.append(
                    "Kalshi private key does not look like a PEM file (missing PRIVATE KEY marker)"
                )
        except Exception as exc:
            errors.append(
                f"Failed reading private key file: {private_key_path} ({exc})"
            )

    if strict and not series_path.exists():
        errors.append(f"Series universe file missing: {series_path}")

    if errors:
        raise RuntimeConfigError(
            "Runtime configuration invalid:\n- " + "\n- ".join(errors)
        )

    return RuntimeConfig(
        kalshi_api_key=kalshi_api_key,
        kalshi_base_url=kalshi_base_url,
        kalshi_private_key_path=private_key_path,
        kalshi_private_key_pem=key_pem,
        series_path=series_path,
        db_path=db_path,
        schema_path=schema_path,
    )
