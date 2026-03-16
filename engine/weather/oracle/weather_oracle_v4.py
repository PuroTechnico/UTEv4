# v4.1.0 — WeatherOracleV4 (Async)
# Top-level orchestrator for the Weather Engine.

from typing import Dict, Any

from engine.weather.builder.weather_snapshot_builder import WeatherSnapshotBuilder
from engine.weather.alpha.weather_alpha_engine import WeatherAlphaEngine
from engine.weather.resolver.weather_market_resolver import WeatherMarketResolver
from engine.weather.models.weather_market import WeatherMarket
from engine.weather.models.weather_snapshot import WeatherSnapshot


class WeatherOracleV4:
    """
    Async orchestrator for the full weather pipeline:
      - discovery
      - providers
      - snapshot building (async)
      - alpha computation (sync)
      - resolution (sync)
    """

    def __init__(
        self,
        snapshot_builder: WeatherSnapshotBuilder,
        alpha_engine: WeatherAlphaEngine,
        resolver: WeatherMarketResolver,
    ):
        self.snapshot_builder = snapshot_builder
        self.alpha_engine = alpha_engine
        self.resolver = resolver

    async def run(self, market: WeatherMarket) -> Dict[str, Any]:
        """
        Execute the full async oracle pipeline for a weather market.
        """
        # 1. Build snapshot (async)
        snapshot: WeatherSnapshot = await self.snapshot_builder.build_snapshot(market)

        # 2. Compute alpha (sync)
        alpha = self.alpha_engine.compute_alpha(snapshot)

        # 3. Resolve market (sync)
        resolution = self.resolver.resolve(market, snapshot)

        return {
            "snapshot": snapshot,
            "alpha": alpha,
            "resolution": resolution,
        }
