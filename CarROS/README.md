# CarROS

Base ROS 2 **Lyrical** layer for the Baja car. One Python package with a `SensorNode` parent; real sensors subclass it.

## Pi 4

Direct Ethernet (this PC is `10.42.0.1`). SSH username is **ubuntu**:

```bash
ssh ubuntu@10.42.0.70
```

Joystick is analog (GND, VCC, VRx, VRy, SW). **VRy cannot go on GP18** — that pin is digital, and 5V full-scale can damage it. Unplug VRy from the Pi GPIO.

The Pi 4 has no ADC. VRy goes to an **ADS1115** (I2C); servo stays on **GP17**. Power the stick from **3.3V**, not 5V, so VRy stays in range.

```
Joystick GND -> Pi GND
Joystick VCC -> Pi 3.3V
Joystick VRy -> ADS1115 A0
ADS1115 VDD  -> Pi 3.3V
ADS1115 GND  -> Pi GND
ADS1115 SDA  -> GP2 (pin 3)
ADS1115 SCL  -> GP3 (pin 5)
Servo signal -> GP17
```

The Pi has no ROS; copy the script and run it there (needs `python3-lgpio`, user in `dialout`):

```bash
scp src/carros/carros/joy_servo.py ubuntu@10.42.0.70:
ssh ubuntu@10.42.0.70
python3 joy_servo.py record --file joy.csv          # live follow; Ctrl+C to stop
python3 joy_servo.py replay --file joy.csv
```

`--seconds 10` records a fixed window instead of until Ctrl+C. Stick position maps to 1000–2000 µs on the servo.

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
