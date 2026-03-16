# engine/weather/resolver/weather_market_resolver.py — v1.0.0
# Resolves weather markets using CLI settlement + snapshot context.

from typing import Dict, Any, Optional

from engine.weather.models.weather_market import WeatherMarket
from engine.weather.models.weather_snapshot import WeatherSnapshot


class WeatherMarketResolver:
    """
    Consumes WeatherMarket + WeatherSnapshot and produces resolution info.

    Responsibilities:
      - Interpret CLI settlement data
      - Compare settlement vs market spec (e.g., high temp threshold)
      - Produce a resolution dict (or None if not yet resolvable)
    """

    def resolve(
        self,
        market: WeatherMarket,
        snapshot: WeatherSnapshot,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a weather market if settlement data is available.

        Expected output shape:
          {
            "settled": bool,
            "outcome": "YES" | "NO" | None,
            "settlement_value": float | None,
            "reason": str,
          }

        Returns None if the market cannot yet be resolved.
        """
        # TODO: implement real logic:
        #  - read settlement from snapshot.settlement
        #  - interpret according to market.ticker / spec
        #  - decide YES/NO + settlement_value
        raise NotImplementedError
