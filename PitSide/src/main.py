import sys

import flet as ft

from accel_bar.accel_sensor import AccelSensor
from minimap.gpsReciever import GpsReciever
from minimap.minimapWidget import MinimapWidget
from speed_bar.speed_sensor import SpeedSensor
from temp_bar.temp_sensor import TempatureSensor
from temp_bar.widget import SensorBarWidget
from top_bar.battery_display import BatteryDisplay
from top_bar.battery_sensor import BatterySensor
from top_bar.connectivity_display import ConnectivityDisplay
from top_bar.connectivity_sensor import ConnectivitySensor

if sys.platform == "win32":
    from terminal.windows import TerminalComp
else:
    from terminal.posix import TerminalComp


def _temp_color(temperature: float) -> str:
    if temperature > 30:
        return "#FF5733"
    if temperature < 0:
        return "#33FF57"
    return "#FFFF33"


def _speed_color(speed: float) -> str:
    if speed > 30:
        return "#FF5733"
    if speed > 15:
        return "#FFFF33"
    return "#33FF57"


def _accel_color(accel: float) -> str:
    if abs(accel) > 6:
        return "#FF5733"
    if abs(accel) > 3:
        return "#FFFF33"
    return "#33FF57"


def main(page: ft.Page):
    page.title = "PitSide"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16

    tempSensor = TempatureSensor(sensor_id=1)
    tempBarWidget = SensorBarWidget()
    tempBarWidget.setup(
        tempSensor.read_temperature,
        -10.0,
        40.0,
        format_value=lambda v: f"{v:.1f}°C",
        color_for=_temp_color,
        thickness=70,
    )

    speedSensor = SpeedSensor()
    speedBarWidget = SensorBarWidget()
    speedBarWidget.setup(
        speedSensor.read_speed,
        0.0,
        40.0,
        format_value=lambda v: f"{v:.0f} mph",
        color_for=_speed_color,
        thickness=70,
    )

    accelSensor = AccelSensor()
    accelBarWidget = SensorBarWidget()
    accelBarWidget.setup(
        accelSensor.read_accel,
        -10.0,
        10.0,
        format_value=lambda v: f"{v:.1f} m/s²",
        color_for=_accel_color,
        thickness=70,
    )

    batterySensor = BatterySensor()
    batteryDisplay = BatteryDisplay(battery_sensor=batterySensor)
    connectivitySensor = ConnectivitySensor()
    connectivityDisplay = ConnectivityDisplay(connectivity_sensor=connectivitySensor)

    gps = GpsReciever()
    minimap = MinimapWidget(gps_reciever=gps)

    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    top_bar = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            tight=True,
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                connectivityDisplay.getWidget(),
                batteryDisplay.getWidget(),
            ],
        ),
    )

    dash = ft.Container(
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=minimap.getWidget(),
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=speedBarWidget.getWidget(),
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER_LEFT,
                    padding=ft.Padding.only(left=90),
                    content=accelBarWidget.getWidget(),
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER_RIGHT,
                    content=tempBarWidget.getWidget(),
                ),
            ],
        ),
    )
    page.add(top_bar)
    page.add(dash)
    page.add(TerminalComp())


if __name__ == "__main__":
    ft.run(main)
