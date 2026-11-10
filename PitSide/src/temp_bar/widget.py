import asyncio
import math

import flet as ft


class SensorBarWidget(ft.ProgressBar):
    """Vertical progress bar with the live sensor reading above it."""

    def setup(
        self,
        read,
        min_value,
        max_value,
        *,
        format_value=None,
        color_for=None,
        thickness=70,
        length=500,
    ):
        self._read = read
        self.min_value = min_value
        self.max_value = max_value
        self._format_value = format_value or (lambda v: f"{v:.1f}")
        self._color_for = color_for or (lambda _v: "#FFFF33")
        self.thickness = thickness
        self.length = length
        self._label = ft.Text("—", size=16, weight=ft.FontWeight.BOLD)
        self._task = None

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.update_loop)

    def will_unmount(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _apply(self, value: float):
        span = self.max_value - self.min_value
        self.value = 0.0 if span == 0 else (value - self.min_value) / span
        self.color = self._color_for(value)
        self._label.value = self._format_value(value)
        self.rotate = -math.pi / 2
        self.width = self.length
        self.height = self.thickness

    async def update_loop(self):
        while self.running:
            value = self._read()
            self._apply(value)
            self._label.update()
            self.update()
            await asyncio.sleep(1 / 3)

    def getWidget(self):
        self.rotate = -math.pi / 2
        self.width = self.length
        self.height = self.thickness
        # The bar is rotated around its center, so it paints past the layout box.
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=self._label,
                    margin=ft.Margin.only(bottom=(self.length - self.thickness) / 2),
                ),
                self,
            ],
        )


# ponytail: keep old name so any leftover imports still work
TempatureBarWidget = SensorBarWidget
