import re

# ponytail: line-oriented screen. Full-screen cursor apps (vim, htop) will
# look wrong. Upgrade path is a real emulator such as pyte.
_CSI = re.compile(r"\x1b\[([0-9;?]*)([@A-Za-z])")


class Screen:
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


def _self_check() -> None:
    screen = Screen()
    screen.feed("hello\r\n")
    assert screen.text() == "hello\n"
    screen = Screen()
    screen.feed("abc\b\bX")
    assert screen.text() == "aXc"
    screen = Screen()
    screen.feed("abcd\x1b[2D\x1b[K")
    assert screen.text() == "ab"
    screen = Screen()
    screen.feed("hello\rX")
    assert screen.text() == "Xello"
    screen = Screen()
    screen.feed("ab\x1b")
    screen.feed("[K")
    assert screen.text() == "ab"


_self_check()
