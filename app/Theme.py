from tkinter import font as tkfont


class Theme:
    PAPER = "#F3F0E8"
    CARD = "#FFFFFF"
    FIELD = "#FBFAF6"
    INK = "#1C2024"
    MUTED = "#5B6168"
    LINE = "#CFC9BC"
    ACCENT = "#077A27"
    DANGER = "#B3261E"
    FOCUS = "#1A5FB4"
    SECONDARY = "#E2DDD0"
    LOG_BG = "#15191D"
    LOG_FG = "#D7DDE3"


class Fonts:
    ui = "Helvetica"
    mono = "Courier"

    _UI_CANDIDATES = ("IBM Plex Sans", "Noto Sans", "DejaVu Sans", "Segoe UI")
    _MONO_CANDIDATES = ("JetBrains Mono", "IBM Plex Mono", "DejaVu Sans Mono", "Consolas")

    @classmethod
    def load(cls):
        """Pick the first installed family; needs a running Tk root."""
        available = set(tkfont.families())
        cls.ui = next((f for f in cls._UI_CANDIDATES if f in available), cls.ui)
        cls.mono = next((f for f in cls._MONO_CANDIDATES if f in available), cls.mono)

    @classmethod
    def ui_font(cls, size: int = 10, bold: bool = False) -> tuple:
        return (cls.ui, size, "bold") if bold else (cls.ui, size)

    @classmethod
    def mono_font(cls, size: int = 10) -> tuple:
        return (cls.mono, size)
