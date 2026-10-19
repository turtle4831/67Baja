import sys

import flet as ft

from temp_bar.temp_sensor import TempatureSensor
from temp_bar.widget import TempatureBarWidget
from top_bar.battery_display import BatteryDisplay
from top_bar.battery_sensor import BatterySensor

if sys.platform == "win32":
    from terminal.windows import TerminalComp
else:
    from terminal.posix import TerminalComp


def main(page: ft.Page):
    page.title = "PitSide"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16

    tempSensor = TempatureSensor(sensor_id=1)
    tempBarWidget = TempatureBarWidget()
    tempBarWidget.setup(sensor=tempSensor, min_temp=-10.0, max_temp=40.0)

    batterySensor = BatterySensor()
    batteryDisplay = BatteryDisplay(battery_sensor=batterySensor)

    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    dash = ft.Container(
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.END,
            controls=[
                tempBarWidget.getWidget(),
            ],
        ),
    )
    page.add(dash)
    page.add(TerminalComp())


if __name__ == "__main__":
    ft.run(main)
