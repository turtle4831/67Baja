import fcntl
import os
import pty
import re
import struct
import subprocess
import termios
import threading

import flet as ft

# ponytail: line-oriented screen. Full-screen cursor apps (vim, htop) will
# look wrong. Upgrade path is a real emulator such as pyte.
_CSI = re.compile(r"\x1b\[([0-9;?]*)([@A-Za-z])")

_SPECIAL = {
    "Enter": b"\r",
    "Numpad Enter": b"\r",
    "Backspace": b"\x7f",
    "Tab": b"\t",
    "Escape": b"\x1b",
    "Delete": b"\x1b[3~",
    "Arrow Up": b"\x1b[A",
    "Arrow Down": b"\x1b[B",
    "Arrow Right": b"\x1b[C",
    "Arrow Left": b"\x1b[D",
    "Home": b"\x1b[H",
    "End": b"\x1b[F",
    "Page Up": b"\x1b[5~",
    "Page Down": b"\x1b[6~",
    " ": b" ",
    "Numpad Add": b"+",
    "Numpad Subtract": b"-",
    "Numpad Multiply": b"*",
    "Numpad Divide": b"/",
    "Numpad Decimal": b".",
}

_SHIFTED = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    "\\": "|",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "`": "~",
}

_MODIFIERS = {
    "Shift Left",
    "Shift Right",
    "Control Left",
    "Control Right",
    "Alt Left",
    "Alt Right",
    "Meta Left",
    "Meta Right",
    "Caps Lock",
}


class _Screen:
    def __init__(self):
        self.lines = [""]
        self.col = 0
        self._pending = ""

    def text(self) -> str:
        return "\n".join(self.lines[-400:])

    def feed(self, data: str) -> None:
        data = self._pending + data
        self._pending = ""
        i = 0
        while i < len(data):
            if data[i] != "\x1b":
                self._put(data[i])
                i += 1
                continue
            rest = data[i:]
            match = _CSI.match(rest)
            if match:
                self._csi(match.group(1), match.group(2))
                i += match.end()
                continue
            if rest.startswith("\x1b[") and len(rest) < 32 and not re.search(
                r"[@A-Za-z]", rest[2:]
            ):
                self._pending = rest
                return
            if rest.startswith("\x1b]") and "\x07" not in rest and len(rest) < 256:
                self._pending = rest
                return
            if len(rest) == 1:
                self._pending = rest
                return
            end = rest.find("\x07")
            i += (end + 1) if rest.startswith("\x1b]") and end != -1 else 2
        if len(self.lines) > 400:
            self.lines = self.lines[-400:]

    def _put(self, ch: str) -> None:
        if ch == "\n":
            self.lines.append("")
            self.col = 0
        elif ch == "\r":
            self.col = 0
        elif ch == "\b":
            self.col = max(0, self.col - 1)
        elif ch == "\t":
            self.col += 8 - (self.col % 8)
        elif ch >= " ":
            line = self.lines[-1]
            if self.col > len(line):
                line += " " * (self.col - len(line))
            if self.col == len(line):
                line += ch
            else:
                line = line[: self.col] + ch + line[self.col + 1 :]
            self.lines[-1] = line
            self.col += 1

    def _csi(self, params: str, cmd: str) -> None:
        nums = [int(part) for part in params.split(";") if part.isdigit()]
        n = nums[0] if nums else 1
        line = self.lines[-1]
        if cmd == "K":
            mode = nums[0] if nums else 0
            if mode == 1:
                self.lines[-1] = " " * self.col + line[self.col :]
            elif mode == 2:
                self.lines[-1] = ""
                self.col = 0
            else:
                self.lines[-1] = line[: self.col]
        elif cmd == "P":
            self.lines[-1] = line[: self.col] + line[self.col + n :]
        elif cmd == "D":
            self.col = max(0, self.col - n)
        elif cmd == "C":
            self.col += n
        elif cmd == "G":
            self.col = max(0, n - 1)
        elif cmd == "J" and n == 2:
            self.lines = [""]
            self.col = 0


def _key_bytes(key: str, shift: bool, ctrl: bool) -> bytes | None:
    if key in _MODIFIERS:
        return None
    if key.startswith("Numpad ") and key[-1].isdigit():
        key = key[-1]
    if key in _SPECIAL:
        return _SPECIAL[key]
    if len(key) != 1:
        return None
    if ctrl and key.isalpha():
        return bytes([ord(key.lower()) & 0x1F])
    if shift:
        return _SHIFTED.get(key, key.upper()).encode()
    return key.lower().encode()


def _self_check() -> None:
    screen = _Screen()
    screen.feed("hello\r\n")
    assert screen.text() == "hello\n"
    screen = _Screen()
    screen.feed("abc\b\bX")
    assert screen.text() == "aXc"
    screen = _Screen()
    screen.feed("abcd\x1b[2D\x1b[K")
    assert screen.text() == "ab"
    screen = _Screen()
    screen.feed("hello\rX")
    assert screen.text() == "Xello"
    screen = _Screen()
    screen.feed("ab\x1b")
    screen.feed("[K")
    assert screen.text() == "ab"
    assert _key_bytes("C", False, True) == b"\x03"
    assert _key_bytes("Enter", False, False) == b"\r"
    assert _key_bytes("A", False, False) == b"a"
    assert _key_bytes("A", True, False) == b"A"
    assert _key_bytes("1", True, False) == b"!"
    assert _key_bytes("Arrow Up", False, False) == b"\x1b[A"
    assert _key_bytes("Backspace", False, False) == b"\x7f"
    assert _key_bytes("Shift Left", False, False) is None


_self_check()


@ft.control("Column")
class TerminalComp(ft.Column):
    """Expansion tile that opens a local shell. SSH from there if you need a remote host."""

    def init(self):
        self.spacing = 0
        self._master: int | None = None
        self._proc: subprocess.Popen | None = None
        self._gen = 0
        self._shift = False
        self._ctrl = False
        self._screen = _Screen()
        self._output = ft.Text(
            "",
            font_family="DejaVu Sans Mono",
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
        if self._proc and self._proc.poll() is None:
            return
        self._close()
        gen = self._gen
        self._screen = _Screen()
        self._output.value = ""
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
        shell = os.environ.get("SHELL") or "/bin/sh"
        try:
            self._proc = subprocess.Popen(
                [shell, "-i"],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                start_new_session=True,
                env={**os.environ, "TERM": "xterm-256color"},
            )
        except FileNotFoundError:
            os.close(master)
            os.close(slave)
            self._screen.feed(f"{shell} is not installed\n")
            self._output.value = self._screen.text()
            return
        os.close(slave)
        self._master = master
        threading.Thread(target=self._read, args=(gen, master), daemon=True).start()

    def _read(self, gen: int, fd: int):
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk or gen != self._gen:
                break
            self._screen.feed(chunk.decode("utf-8", errors="replace"))
            self._push(gen)
        if gen == self._gen:
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
            self._write(_key_bytes(e.key, self._shift, self._ctrl))

    def _key_up(self, e: ft.KeyUpEvent):
        if e.key in ("Shift Left", "Shift Right"):
            self._shift = False
        elif e.key in ("Control Left", "Control Right"):
            self._ctrl = False

    def _key_repeat(self, e: ft.KeyRepeatEvent):
        self._write(_key_bytes(e.key, self._shift, self._ctrl))

    def _write(self, data: bytes | None):
        if not data or self._master is None:
            return
        try:
            os.write(self._master, data)
        except OSError:
            pass

    def _close(self):
        self._gen += 1
        master, proc = self._master, self._proc
        self._master = None
        self._proc = None
        if master is not None:
            try:
                os.close(master)
            except OSError:
                pass
        if proc and proc.poll() is None:
            proc.terminate()

    def will_unmount(self):
        self._close()
