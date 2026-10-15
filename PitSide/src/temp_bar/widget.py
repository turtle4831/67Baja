import asyncio
import math

from temp_bar.temp_sensor import TempatureSensor
import flet as ft

class TempatureBarWidget(ft.ProgressBar):

    def setup(self, sensor: TempatureSensor, min_temp=-10.0, max_temp=40.0):
        self.sensor = sensor
        self.min_temp = min_temp
        self.max_temp = max_temp
        
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
            temperature = self.sensor.read_temperature()
            self.value = (temperature - self.min_temp) / (self.max_temp - self.min_temp)
            self.color = "#FF5733" if temperature > 30 else "#33FF57" if temperature < 0 else "#FFFF33"
            self.rotate = -math.pi/2
            self.width = 500
            self.height = 50
            self.update()
            await asyncio.sleep(1 / 3)

    def getWidget(self):
        self.rotate = -math.pi / 2
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
