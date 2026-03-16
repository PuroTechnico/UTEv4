class WeatherStation:
    """Represents metadata for an ASOS/METAR station."""

    def __init__(self, station_id: str, name: str, lat: float, lon: float):
        self.station_id = station_id
        self.name = name
        self.lat = lat
        self.lon = lon
