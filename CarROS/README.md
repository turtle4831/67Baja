# CarROS

Base ROS 2 **Lyrical** layer for the Baja car. One Python package with a `SensorNode` parent; real sensors subclass it.

## Pi 4

Direct Ethernet (this PC is `10.42.0.1`). SSH username is **ubuntu**:

```bash
ssh ubuntu@10.42.0.70
```

The Pi is Ubuntu 24.04, so it runs ROS 2 **Jazzy** (Lyrical has no Noble arm64 debs).

### Deploy

From `CarROS/` on this PC:

```bash
./deploy --setup    # first time: rsync, install ROS 2 + systemd unit
./deploy            # later: rsync + colcon build + restart carros.service
```

Override the target with `CARROS_PI` if the address changes:

```bash
CARROS_PI=ubuntu@10.42.0.70 ./deploy
```

On boot, `carros.service` runs `scripts/start.sh` → `ros2 launch carros sensors.launch.py record:=false`. On the Pi:

```bash
sudo systemctl status carros
sudo systemctl restart carros
journalctl -u carros -f
```

## Setup

```bash
cd CarROS
uv venv --system-site-packages
uv sync
source /opt/ros/lyrical/setup.bash
source .venv/bin/activate
colcon build --symlink-install
source install/setup.bash
```

`uv venv --system-site-packages` is required so ROS apt packages (`em`, `osrf_pycommon`) import. `uv sync` alone makes an isolated env that cannot see them.

## Run

From `CarROS/` (bags land in `./bags/`):

```bash
ros2 launch carros sensors.launch.py
```

Skip recording:

```bash
ros2 launch carros sensors.launch.py record:=false
```

Or run the dummy sensor alone:

```bash
ros2 run carros dummy_sensor
```

Inspect a bag after Ctrl+C:

```bash
ros2 bag info bags/dummy_*
```

## Add a sensor

Subclass `carros.sensor_node.SensorNode`, implement `read()` (return a ROS msg or `None`), register a `console_scripts` entry in `setup.py`, and add the node to `launch/sensors.launch.py`.
