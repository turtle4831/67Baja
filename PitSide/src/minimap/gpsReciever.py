import math
import time

from minimap.maryland_endurance_path import ENDURANCE_WAYPOINTS

# ponytail: mock walks the Baja SAE Maryland endurance polyline until real
# NMEA/serial is wired on `port`. Upgrade path is live GNSS.


def _segment_lengths(waypoints: list[tuple[float, float]]) -> list[float]:
    """Meters between consecutive waypoints, including closing edge."""
    n = len(waypoints)
    out: list[float] = []
    for i in range(n):
        lat1, lon1 = waypoints[i]
        lat2, lon2 = waypoints[(i + 1) % n]
        mid_lat = (lat1 + lat2) / 2.0
        m_lat = 111320.0
        m_lon = 111320.0 * math.cos(math.radians(mid_lat))
        out.append(math.hypot((lat2 - lat1) * m_lat, (lon2 - lon1) * m_lon))
    return out


def _point_on_loop(
    waypoints: list[tuple[float, float]],
    lengths: list[float],
    total: float,
    distance_m: float,
) -> tuple[float, float]:
    if total <= 0 or not waypoints:
        return waypoints[0] if waypoints else (0.0, 0.0)
    d = distance_m % total
    for i, seg in enumerate(lengths):
        if d <= seg or i == len(lengths) - 1:
            t = 0.0 if seg <= 0 else min(d / seg, 1.0)
            lat1, lon1 = waypoints[i]
            lat2, lon2 = waypoints[(i + 1) % len(waypoints)]
            return lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t
        d -= seg
    return waypoints[0]


class GpsReciever:
    def __init__(self, port=None, speed_mps: float = 12.0):
        self.port = port
        self._t0 = time.monotonic()
        # ~12 m/s ≈ 27 mph — leisurely endurance pace for the mock
        self._speed_mps = speed_mps
        self._waypoints = list(ENDURANCE_WAYPOINTS)
        self._lengths = _segment_lengths(self._waypoints)
        self._lap_m = sum(self._lengths)
        self.gps_data = {"latitude": None, "longitude": None}

    def read_gps_data(self):
        dist = (time.monotonic() - self._t0) * self._speed_mps
        lat, lon = _point_on_loop(self._waypoints, self._lengths, self._lap_m, dist)
        self.gps_data["latitude"] = lat
        self.gps_data["longitude"] = lon

    def get_coordinates(self):
        self.read_gps_data()
        lat = self.gps_data["latitude"]
        lon = self.gps_data["longitude"]
        if lat is None or lon is None:
            return None
        return lat, lon


def _self_check():
    gps = GpsReciever()
    assert len(gps._waypoints) >= 8
    assert gps._lap_m > 1000.0

    gps._t0 = time.monotonic()
    a = gps.get_coordinates()
    gps._t0 = time.monotonic() - 5.0
    b = gps.get_coordinates()
    assert a is not None and b is not None
    assert a != b

    # one full lap returns near the start
    gps._t0 = time.monotonic() - (gps._lap_m / gps._speed_mps)
    c = gps.get_coordinates()
    assert abs(c[0] - gps._waypoints[0][0]) < 1e-4
    assert abs(c[1] - gps._waypoints[0][1]) < 1e-4

    # interpolation stays inside waypoint bbox
    lats = [p[0] for p in gps._waypoints]
    lons = [p[1] for p in gps._waypoints]
    for frac in (0.0, 0.25, 0.5, 0.75):
        p = _point_on_loop(gps._waypoints, gps._lengths, gps._lap_m, gps._lap_m * frac)
        assert min(lats) - 1e-6 <= p[0] <= max(lats) + 1e-6
        assert min(lons) - 1e-6 <= p[1] <= max(lons) + 1e-6


_self_check()
