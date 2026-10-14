import flet as ft

from terminal_comp import TerminalComp


def main(page: ft.Page):
    page.title = "PitSide"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.add(TerminalComp(expand=True))


if __name__ == "__main__":
    ft.run(main)
