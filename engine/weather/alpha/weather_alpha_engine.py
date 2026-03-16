# engine/weather/alpha/weather_alpha_engine.py — v1.0.0
# Computes alpha signals from WeatherSnapshot.

from typing import Dict, Any

from engine.weather.models.weather_snapshot import WeatherSnapshot


class WeatherAlphaEngine:
    """
    Consumes WeatherSnapshot and produces alpha metrics.

    Responsibilities:
      - Derive expected high temperature
      - Compare observation vs forecast (pace)
      - Produce a directional signal
      - Return a structured alpha dict
    """

    def compute_alpha(self, snapshot: WeatherSnapshot) -> Dict[str, Any]:
        """
        Compute alpha metrics from a WeatherSnapshot.

        Expected output shape:
          {
            "expected_high": float | None,
            "asos_temp_f": float | None,
            "pace": float | None,
            "signal": str | None,
            "raw": dict,   # any intermediate values
          }
        """
        # TODO: implement real logic:
        #  - derive expected_high from forecast
        #  - derive asos_temp_f from observation
        #  - compute pace (obs vs forecast)
        #  - map to signal (e.g., STRONG_BUY / BUY / NEUTRAL / SELL / STRONG_SELL)
        raise NotImplementedError
