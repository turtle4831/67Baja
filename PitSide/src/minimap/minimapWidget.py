import asyncio
import math

import flet as ft
import flet.canvas as cv

from minimap.gpsReciever import GpsReciever

_PAD = 0.15
_MIN_SPAN = 1e-6
# ponytail: cap trail so redraw stays O(n) cheap; raise if you need longer history
_TRAIL_CAP = 500


def project_to_pixels(
    points: list[tuple[float, float]], width: float, height: float
) -> list[tuple[float, float]]:
    """Map lat/lon to widget pixels, north-up, aspect-corrected, padded, centered."""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    mid_lat = (min(lats) + max(lats)) / 2.0
    cos_lat = max(math.cos(math.radians(mid_lat)), 1e-6)

    # local meters-ish so a lat/lon circle stays round on screen
    xs = [lon * cos_lat for lon in lons]
    ys = lats
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, _MIN_SPAN)
    span_y = max(max_y - min_y, _MIN_SPAN)
    min_x -= span_x * _PAD
    max_x += span_x * _PAD
    min_y -= span_y * _PAD
    max_y += span_y * _PAD
    span_x = max_x - min_x
    span_y = max_y - min_y

    scale = min(width / span_x, height / span_y)
    ox = (width - span_x * scale) / 2.0
    oy = (height - span_y * scale) / 2.0

    out: list[tuple[float, float]] = []
    for lat, lon in points:
        x = ox + (lon * cos_lat - min_x) * scale
        y = oy + (max_y - lat) * scale
        out.append((x, y))
    return out


class MinimapWidget(ft.Container):
    def __init__(self, gps_reciever: GpsReciever, width: int = 280, height: int = 280):
        self.gps_reciever = gps_reciever
        self._trail: list[tuple[float, float]] = []
        self._task = None
        self.running = False
        self._canvas = cv.Canvas(width=width, height=height, shapes=[]) # type: ignore
        super().__init__(
            content=self._canvas, # type: ignore
            width=width,
            height=height,
            bgcolor="#1a1a1a",
            border_radius=ft.BorderRadius.all(10),
            border=ft.Border.all(1, "#444444"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def did_mount(self):
        self.running = True
        self._task = self.page.run_task(self.update_loop)

    def will_unmount(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _redraw(self):
        coords = self.gps_reciever.get_coordinates()
        if coords is not None:
            self._trail.append(coords)
            if len(self._trail) > _TRAIL_CAP:
                self._trail = self._trail[-_TRAIL_CAP:]

        if not self._trail:
            return
        
        pixels = project_to_pixels(self._trail, self.width, self.height)#type: ignore
        
        shapes: list[cv.Shape] = []
        if len(pixels) >= 2:
            elements: list[cv.Path.PathElement] = [cv.Path.MoveTo(*pixels[0])]
            elements.extend(cv.Path.LineTo(x, y) for x, y in pixels[1:])
            shapes.append(
                cv.Path(
                    elements,
                    paint=ft.Paint(
                        color="#4CAF50",
                        stroke_width=2,
                        style=ft.PaintingStyle.STROKE,
                    ),
                )
            )
        cx, cy = pixels[-1]
        shapes.append(
            cv.Circle(cx, cy, 5, paint=ft.Paint(color="#FF5252", style=ft.PaintingStyle.FILL))
        )
        self._canvas.shapes = shapes

    async def update_loop(self):
        while self.running:
            self._redraw()
            self.update()
            await asyncio.sleep(1 / 5)

    def getWidget(self):
        return self


def _self_check():
    # unit square in lat/lon near equator → roughly fills padded view
    pts = [(0.0, 0.0), (0.0, 0.001), (0.001, 0.001), (0.001, 0.0)]
    pix = project_to_pixels(pts, 200, 200)
    assert len(pix) == 4
    xs = [p[0] for p in pix]
    ys = [p[1] for p in pix]
    assert min(xs) > 0 and max(xs) < 200
    assert min(ys) > 0 and max(ys) < 200
    # north (higher lat) draws higher on screen (smaller y)
    assert pix[3][1] < pix[0][1]


_self_check()
