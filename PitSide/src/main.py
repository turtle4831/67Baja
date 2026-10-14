import sys

import flet as ft

if sys.platform == "win32":
    from terminal.windows import TerminalComp
else:
    from terminal.posix import TerminalComp


def main(page: ft.Page):
    page.title = "PitSide"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.add(TerminalComp(expand=True))


if __name__ == "__main__":
    ft.run(main)
