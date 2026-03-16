import asyncio
import unittest
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

from pipelines.snapshot_pipeline import SnapshotPipeline


class FakeLocator:
    async def locate(self, series, now_utc):
        ticker = series.get("ticker")
        if ticker == "SERIES-15M":
            return ["KXBTC-TEST"]
        return []


class FakeKalshi:
    async def get_market(self, ticker):
        return {
            "market": {
                "ticker": ticker,
                "yes_bid": 55,
                "no_bid": 44,
                "yes_ask": 56,
                "no_ask": 45,
                "volume": 123,
                "tte_minutes": 30,
            }
        }


class FakeCryptoSnapshot:
    def __init__(self, symbol):
        now = datetime.now(timezone.utc)
        self.symbol = symbol
        self.maturity_ts_ms = 1700000000000
        self.live_price = 100.0
        self.candle_1m = []
        self.candle_15m = []
        self.candle_1h = []
        self.candle_6h = []
        self.second_series = []
        self.snapshot_ts = now


class FakeCryptoS3:
    def build_snapshot(self, symbol):
        if symbol in {"BTC", "ETH"}:
            return FakeCryptoSnapshot(symbol)
        return None


class SnapshotPipelineOfflineContractTest(unittest.TestCase):
    def test_run_contract_shape_offline(self):
        universe = {
            "crypto_15m": [{"ticker": "SERIES-15M"}],
            "crypto_hourly": [],
            "crypto_daily": [],
            "weather": [{"ticker": "WEATHER-TICKER", "title": "Weather Test"}],
        }

        pipeline = SnapshotPipeline(
            universe=universe,
            kalshi=FakeKalshi(),  # type: ignore[arg-type]
            locator=FakeLocator(),  # type: ignore[arg-type]
            crypto_s3=FakeCryptoS3(),  # type: ignore[arg-type]
        )

        with patch("pipelines.snapshot_pipeline.insert") as mocked_insert, patch(
            "pipelines.snapshot_pipeline.get_table_columns",
            return_value=["id", "symbol", "maturity_ts_ms", "live_price"],
        ):
            result = asyncio.run(pipeline.run())

        self.assertIsInstance(result, dict)
        self.assertIn("market", result)
        self.assertIn("crypto_s3", result)
        self.assertIn("weather", result)

        self.assertIsInstance(result["market"], dict)
        self.assertIsInstance(result["crypto_s3"], dict)
        self.assertIsInstance(result["weather"], dict)

        self.assertIn("KXBTC-TEST", result["market"])
        self.assertIn("BTC", result["crypto_s3"])
        self.assertIn("ETH", result["crypto_s3"])
        self.assertIn("WEATHER-TICKER", result["weather"])

        self.assertGreaterEqual(mocked_insert.call_count, 3)


if __name__ == "__main__":
    unittest.main()
