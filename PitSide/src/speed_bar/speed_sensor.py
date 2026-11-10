import math
import random
import time

# ponytail: mean-reverting speed mock until real wheel/GPS telemetry is wired.


class SpeedSensor:
    def __init__(self):
        self._speed = 15.0
        self._t = time.monotonic()
        self._rng = random.Random()

    def read_speed(self):
        now = time.monotonic()
        dt = min(max(now - self._t, 0.0), 5.0)
        self._t = now
        self._speed += 0.08 * (18.0 - self._speed) * dt
        if dt:
            self._speed += self._rng.gauss(0, 1.2 * math.sqrt(dt))
        self._speed = min(40.0, max(0.0, self._speed))
        return round(self._speed, 1)


def _self_check():
    sensor = SpeedSensor()
    sensor._rng = random.Random(1)
    prev = sensor._speed
    moved = 0.0
    for _ in range(180):
        sensor._t -= 1 / 3
        speed = sensor.read_speed()
        assert 0.0 <= speed <= 40.0
        jump = abs(speed - prev)
        assert jump < 3.0
        moved += jump
        prev = speed
    assert moved > 1.0


_self_check()
