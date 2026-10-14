import flet as ft

from terminal.keys import key_bytes
from terminal.screen import Screen


def make_terminal(start_shell, font_family="DejaVu Sans Mono"):
    """Flet shell tile. ``start_shell(on_chunk, on_done)`` returns write/close/alive."""

    @ft.control("Column")
    class TerminalComp(ft.Column):
        """Expansion tile that opens a local shell. SSH from there if you need a remote host."""

        def init(self):
            self.spacing = 0
            self._session = None
            self._gen = 0
            self._shift = False
            self._ctrl = False
            self._screen = Screen()
            self._output = ft.Text(
                "",
                font_family=font_family,
                size=13,
                color="#33FF66",
                no_wrap=True,
                selectable=False,
            )
            self._keys = ft.KeyboardListener(
                on_key_down=self._key_down,
                on_key_up=self._key_up,
                on_key_repeat=self._key_repeat,
                content=ft.Container(
                    bgcolor="#0C0C0C",
                    height=340,
                    padding=10,
                    border_radius=6,
                    on_click=self._focus,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        auto_scroll=True,
                        controls=[self._output],
                    ),
                ),
            )
            self.controls = [
                ft.ExpansionTile(
                    title="Terminal",
                    subtitle="Click the terminal to type",
                    maintain_state=True,
                    expanded_cross_axis_alignment=ft.CrossAxisAlignment.STRETCH,
                    on_change=self._on_expand,
                    controls=[self._keys],
                )
            ]

        def _on_expand(self, e: ft.Event):
            if str(e.data).lower() != "true":
                return
            self._start()
            self.page.run_task(self._focus)

        async def _focus(self, _e=None):
            await self._keys.focus()

        def _start(self):
            if self._session is not None and self._session.alive():
                return
            self._close()
            gen = self._gen
            self._screen = Screen()
            self._output.value = ""
            try:
                self._session = start_shell(
                    lambda chunk: self._on_chunk(gen, chunk),
                    lambda: self._on_done(gen),
                )
            except OSError as exc:
                self._screen.feed(f"{exc}\n")
                self._output.value = self._screen.text()

        def _on_chunk(self, gen: int, chunk: bytes):
            if gen != self._gen:
                return
            self._screen.feed(chunk.decode("utf-8", errors="replace"))
            self._push(gen)

        def _on_done(self, gen: int):
            if gen != self._gen:
                return
            self._screen.feed("\n[session closed]\n")
            self._push(gen)

        def _push(self, gen: int):
            if gen != self._gen:
                return
            text = self._screen.text()
            try:
                self.page.run_task(self._show, text, gen)
            except RuntimeError:
                pass

        async def _show(self, text: str, gen: int):
            if gen != self._gen:
                return
            self._output.value = text
            self._output.update()

        def _key_down(self, e: ft.KeyDownEvent):
            if e.key in ("Shift Left", "Shift Right"):
                self._shift = True
            elif e.key in ("Control Left", "Control Right"):
                self._ctrl = True
            else:
                self._write(key_bytes(e.key, self._shift, self._ctrl))

        def _key_up(self, e: ft.KeyUpEvent):
            if e.key in ("Shift Left", "Shift Right"):
                self._shift = False
            elif e.key in ("Control Left", "Control Right"):
                self._ctrl = False

        def _key_repeat(self, e: ft.KeyRepeatEvent):
            self._write(key_bytes(e.key, self._shift, self._ctrl))

        def _write(self, data: bytes | None):
            if not data or self._session is None:
                return
            self._session.write(data)

        def _close(self):
            self._gen += 1
            session = self._session
            self._session = None
            if session is not None:
                session.close()

        def will_unmount(self):
            self._close()

    return TerminalComp
