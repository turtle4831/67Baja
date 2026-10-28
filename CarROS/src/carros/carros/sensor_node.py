from rclpy.node import Node


class SensorNode(Node):
    """Parent for car sensors. Subclass and implement read()."""

    def __init__(self, node_name, msg_type, topic, period_s=0.2):
        super().__init__(node_name)
        self.declare_parameter('topic', topic)
        self.declare_parameter('period_s', float(period_s))
        topic = self.get_parameter('topic').value
        period = float(self.get_parameter('period_s').value)
        self._pub = self.create_publisher(msg_type, topic, 10)
        self.create_timer(period, self._tick)
        self.get_logger().info(f'sensor up on {topic} every {period}s')

    def read(self):
        raise NotImplementedError

    def _tick(self):
        try:
            msg = self.read()
        except Exception as e:
            self.get_logger().error(f'read failed: {e}')
            return
        if msg is None:
            self.get_logger().warning('no sample', throttle_duration_sec=5.0)
            return
        self._pub.publish(msg)
        self.get_logger().debug(f'published {msg}')
