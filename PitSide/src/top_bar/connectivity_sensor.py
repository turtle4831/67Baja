import math
import random
import time

# ponytail: fake radio link quality until CC1101 serial modem is wired.


class ConnectivitySensor:
    def __init__(self):
        self._quality = 80.0
        self._t = time.monotonic()
        self._rng = random.Random()

    def get_link_quality(self):
        now = time.monotonic()
        dt = min(max(now - self._t, 0.0), 5.0)
        self._t = now
        self._quality += 0.05 * (75.0 - self._quality) * dt
        if dt:
            self._quality += self._rng.gauss(0, 4.0 * math.sqrt(dt))
        self._quality = min(100.0, max(0.0, self._quality))
        return round(self._quality, 1)


def _self_check():
    sensor = ConnectivitySensor()
    sensor._rng = random.Random(1)
    q = sensor.get_link_quality()
    assert 0.0 <= q <= 100.0


_self_check()
