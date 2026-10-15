import math
import random
import time

# ponytail: mean-reverting air temp plus an 8s probe lag. A gap longer than
# 5s counts as 5s. Upgrade path is the real sensor time-constant.


class TempatureSensor:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self._air = 20.0
        self._temp = 20.0
        self._t = time.monotonic()
        self._rng = random.Random()

    def read_temperature(self):
        now = time.monotonic()
        dt = min(max(now - self._t, 0.0), 5.0)
        self._t = now
        self._air += 0.03 * (20.0 - self._air) * dt
        if dt:
            self._air += self._rng.gauss(0, 0.8 * math.sqrt(dt))
        self._air = min(35.0, max(-5.0, self._air))
        self._temp += (self._air - self._temp) * (dt / 8.0)
        return round(min(40.0, max(-10.0, self._temp)), 2)


def _self_check():
    sensor = TempatureSensor(1)
    sensor._rng = random.Random(1)
    prev = sensor._temp
    moved = 0.0
    for _ in range(180):
        sensor._t -= 1 / 3
        temp = sensor.read_temperature()
        assert -10.0 <= temp <= 40.0
        jump = abs(temp - prev)
        assert jump < 0.5
        moved += jump
        prev = temp
    assert moved > 1.0


_self_check()
