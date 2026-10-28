import math
import random
import time

# ponytail: slow drain with noise until real Pi telemetry is wired.


class BatterySensor:
    def __init__(self):
        self._level = 100.0
        self._t = time.monotonic()
        self._rng = random.Random()

    def get_battery_level(self):
        now = time.monotonic()
        dt = min(max(now - self._t, 0.0), 5.0)
        self._t = now
        # ~1% per minute plus small noise; clamp to 0–100
        self._level -= 1.0 / 60.0 * dt
        if dt:
            self._level += self._rng.gauss(0, 0.15 * math.sqrt(dt))
        self._level = min(100.0, max(0.0, self._level))
        return round(self._level, 1)


def _self_check():
    sensor = BatterySensor()
    sensor._rng.gauss = lambda mu, sigma: 0.0
    sensor._level = 50.0
    before = sensor._level
    sensor._t -= 60  # clamped to 5s inside get_battery_level
    after = sensor.get_battery_level()
    assert 0.0 <= after <= 100.0
    assert after == round(before - 1.0 / 60.0 * 5.0, 1)


_self_check()
