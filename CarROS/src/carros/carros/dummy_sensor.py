import time

import rclpy
from std_msgs.msg import Float64

from carros.sensor_node import SensorNode


class DummySensor(SensorNode):
    def __init__(self):
        super().__init__('dummy_sensor', Float64, '/sensors/dummy', 0.2)
        self._t0 = time.monotonic()

    def read(self):
        msg = Float64()
        msg.data = time.monotonic() - self._t0
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = DummySensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
