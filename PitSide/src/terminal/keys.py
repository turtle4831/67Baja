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


def key_bytes(key: str, shift: bool, ctrl: bool) -> bytes | None:
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
    assert key_bytes("C", False, True) == b"\x03"
    assert key_bytes("Enter", False, False) == b"\r"
    assert key_bytes("A", False, False) == b"a"
    assert key_bytes("A", True, False) == b"A"
    assert key_bytes("1", True, False) == b"!"
    assert key_bytes("Arrow Up", False, False) == b"\x1b[A"
    assert key_bytes("Backspace", False, False) == b"\x7f"
    assert key_bytes("Shift Left", False, False) is None


_self_check()
