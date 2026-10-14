import threading

from terminal.widget import make_terminal
from terminal.win_conpty import open_console


def _read(console, on_chunk, on_done) -> None:
    while True:
        chunk = console.read()
        if not chunk:
            break
        on_chunk(chunk)
    on_done()


def start_shell(on_chunk, on_done):
    console = open_console()
    threading.Thread(target=_read, args=(console, on_chunk, on_done), daemon=True).start()
    return console


TerminalComp = make_terminal(start_shell, font_family="Consolas")
