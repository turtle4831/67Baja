import fcntl
import os
import pty
import struct
import subprocess
import termios
import threading

from terminal.widget import make_terminal


class _Pty:
    def __init__(self, master: int, proc: subprocess.Popen, on_chunk, on_done):
        self._master = master
        self._proc = proc
        self._on_chunk = on_chunk
        self._on_done = on_done
        threading.Thread(target=self._read, args=(master,), daemon=True).start()

    def write(self, data: bytes) -> None:
        if self._master is None:
            return
        try:
            os.write(self._master, data)
        except OSError:
            pass

    def close(self) -> None:
        master, proc = self._master, self._proc
        self._master = None
        self._proc = None
        if master is not None:
            try:
                os.close(master)
            except OSError:
                pass
        if proc is not None and proc.poll() is None:
            proc.terminate()

    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _read(self, fd: int) -> None:
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            self._on_chunk(chunk)
        self._on_done()


def start_shell(on_chunk, on_done):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
    shell = os.environ.get("SHELL") or "/bin/sh"
    try:
        proc = subprocess.Popen(
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
        raise OSError(f"{shell} is not installed") from None
    except OSError:
        os.close(master)
        os.close(slave)
        raise
    os.close(slave)
    return _Pty(master, proc, on_chunk, on_done)


TerminalComp = make_terminal(start_shell)
