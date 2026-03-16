# v4.0.0 — WeatherSnapshot

class WeatherSnapshot:
    def __init__(self, observation, forecast, alerts, station, settlement=None):
        self.observation = observation
        self.forecast = forecast
        self.alerts = alerts
        self.station = station
        self.settlement = settlement
