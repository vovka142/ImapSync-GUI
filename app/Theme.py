from tkinter import font as tkfont


class Theme:
    # Спокойная SaaS-палитра: светлый холст, контрастные панели и индиго-акцент.
    PAPER = "#F4F5FA"
    CARD = "#FFFFFF"
    FIELD = "#F8F9FC"
    INK = "#191D2E"
    MUTED = "#7A8094"
    LINE = "#E5E8F0"
    ACCENT = "#625BFF"
    DANGER = "#D94B62"
    FOCUS = "#817BFF"
    SECONDARY = "#ECEEF6"
    LOG_BG = "#171B2B"
    LOG_FG = "#DDE2F2"


class Fonts:
    ui = "Helvetica"
    mono = "Courier"

    _UI_CANDIDATES = ("Inter", "IBM Plex Sans", "Noto Sans", "DejaVu Sans", "Segoe UI")
    _MONO_CANDIDATES = ("JetBrains Mono", "IBM Plex Mono", "DejaVu Sans Mono", "Consolas")

    @classmethod
    def load(cls):
        """Выбирает первый доступный шрифт из списка."""
        available = set(tkfont.families())
        cls.ui = next((f for f in cls._UI_CANDIDATES if f in available), cls.ui)
        cls.mono = next((f for f in cls._MONO_CANDIDATES if f in available), cls.mono)

    @classmethod
    def ui_font(cls, size: int = 10, bold: bool = False) -> tuple:
        return (cls.ui, size, "bold") if bold else (cls.ui, size)

    @classmethod
    def mono_font(cls, size: int = 10) -> tuple:
        return (cls.mono, size)
