class WeatherObservation:
    """Represents METAR-based real-time observations."""

    def __init__(self, temp_f: float, dewpoint_f: float, wind_mph: float, timestamp: str):
        self.temp_f = temp_f
        self.dewpoint_f = dewpoint_f
        self.wind_mph = wind_mph
        self.timestamp = timestamp
