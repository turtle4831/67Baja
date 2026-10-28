import asyncio

import flet as ft

from top_bar.battery_sensor import BatterySensor


class BatteryDisplay(ft.ProgressBar):
    def __init__(self, battery_sensor: BatterySensor):
        super().__init__(width=220, height=14, border_radius=4)
        self.battery_sensor = battery_sensor
        self._task = None
        self._apply_level(self.battery_sensor.get_battery_level())

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.update_loop)

    def will_unmount(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _apply_level(self, battery_level: float):
        self.value = battery_level / 100
        self.color = (
            "#33FF57"
            if battery_level > 50
            else "#FFFF33"
            if battery_level > 20
            else "#FF5733"
        )

    async def update_loop(self):
        while self.running:
            self._apply_level(self.battery_sensor.get_battery_level())
            self.update()
            await asyncio.sleep(1)

    def getWidget(self):
        return self
