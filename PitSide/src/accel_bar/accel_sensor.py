import math
import random
import time

# ponytail: mean-reverting longitudinal accel mock until real IMU is wired.


class AccelSensor:
    def __init__(self):
        self._accel = 0.0
        self._t = time.monotonic()
        self._rng = random.Random()

    def read_accel(self):
        now = time.monotonic()
        dt = min(max(now - self._t, 0.0), 5.0)
        self._t = now
        self._accel += 0.25 * (0.0 - self._accel) * dt
        if dt:
            self._accel += self._rng.gauss(0, 0.6 * math.sqrt(dt))
        self._accel = min(10.0, max(-10.0, self._accel))
        return round(self._accel, 2)


def _self_check():
    sensor = AccelSensor()
    sensor._rng = random.Random(1)
    prev = sensor._accel
    moved = 0.0
    for _ in range(180):
        sensor._t -= 1 / 3
        accel = sensor.read_accel()
        assert -10.0 <= accel <= 10.0
        jump = abs(accel - prev)
        assert jump < 2.0
        moved += jump
        prev = accel
    assert moved > 0.5


_self_check()
