import rclpy
from std_msgs.msg import Float64

from carros.dummy_sensor import DummySensor


def test_dummy_read_returns_float64():
    rclpy.init()
    node = DummySensor()
    try:
        msg = node.read()
        assert isinstance(msg, Float64)
        assert isinstance(msg.data, float)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
