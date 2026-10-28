import asyncio

import flet as ft

from top_bar.connectivity_sensor import ConnectivitySensor


class ConnectivityDisplay(ft.ProgressBar):
    def __init__(self, connectivity_sensor: ConnectivitySensor):
        super().__init__(width=220, height=10, border_radius=4)
        self.connectivity_sensor = connectivity_sensor
        self._task = None
        self._apply_quality(self.connectivity_sensor.get_link_quality())

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.update_loop)

    def will_unmount(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _apply_quality(self, quality: float):
        self.value = quality / 100
        self.color = (
            "#4FC3F7"
            if quality > 50
            else "#FFFF33"
            if quality > 20
            else "#FF5733"
        )

    async def update_loop(self):
        while self.running:
            self._apply_quality(self.connectivity_sensor.get_link_quality())
            self.update()
            await asyncio.sleep(1 / 3)

    def getWidget(self):
        return self
