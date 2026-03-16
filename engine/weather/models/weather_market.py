# engine/weather/models/weather_market.py — v4.0.0


class WeatherMarket:
    """
    Represents a Kalshi weather market in the engine.
    """

    def __init__(self, ticker: str, cli_url: str, lat: float, lon: float):
        self.ticker = ticker
        self.cli_url = cli_url
        self.lat = lat
        self.lon = lon
