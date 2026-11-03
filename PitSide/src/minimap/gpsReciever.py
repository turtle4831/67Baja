import math
import time

# ponytail: mock circular walk until real NMEA/serial is wired on `port`.


class GpsReciever:
    def __init__(self, port=None):
        self.port = port
        self._t0 = time.monotonic()
        # arbitrary coastal origin; only relative motion matters for the minimap
        self._origin_lat = 32.7157
        self._origin_lon = -117.1611
        self._radius_deg = 0.001
        self.gps_data = {"latitude": float("nan"), "longitude": float("nan")}

    def read_gps_data(self):
        t = time.monotonic() - self._t0
        self.gps_data["latitude"] = self._origin_lat + self._radius_deg * math.sin(t * 0.35)
        self.gps_data["longitude"] = self._origin_lon + self._radius_deg * math.cos(t * 0.35)

    def get_coordinates(self):
        self.read_gps_data()
        lat = self.gps_data["latitude"]
        lon = self.gps_data["longitude"]
        if lat is None or lon is None:
            return None
        return lat, lon


def _self_check():
    gps = GpsReciever()
    gps._t0 = time.monotonic() - (math.pi / 2) / 0.35
    cords = gps.get_coordinates()
    if cords is None:
        raise AssertionError("get_coordinates() returned None")
    lat, lon = cords
    assert abs(lat - (gps._origin_lat + gps._radius_deg)) < 1e-6
    assert abs(lon - gps._origin_lon) < 1e-6


_self_check()
