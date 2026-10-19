import asyncio
import math

import flet as ft

from top_bar.battery_sensor import BatterySensor

class BatteryDisplay(ft.ProgressBar):
    def __init__(self, battery_sensor:BatterySensor):
        super().__init__()
        self.battery_sensor = battery_sensor
        self.value = self.battery_sensor.get_battery_level() / 100

    def did_mount(self):
        self.running = True
        # Start the continuous update task outliving the handler
        self._task = self.page.run_task(self.update_loop)

    def will_unmount(self):
        # Stop the loop when the component is removed
        self.running = False
        if self._task:
            self._task.cancel()

    async def update_loop(self):
        while self.running:
            battery_level = self.battery_sensor.get_battery_level()
            self.value = battery_level / 100
            self.color = "#33FF57" if battery_level > 50 else "#FFFF33" if battery_level > 20 else "#FF5733"
            self.update()
            await asyncio.sleep(1)
            
    def getWidget(self):
            self.rotate = math.pi 
            self.width = 500
            self.height = 50
            # The bar is rotated around its center, so it paints past the layout box.
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "🔥",
                        size=28,
                        margin=ft.Margin.only(bottom=(self.width - self.height) / 2),
                    ),
                    self,
                ],
            )
