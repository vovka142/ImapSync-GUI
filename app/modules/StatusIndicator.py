import tkinter as tk
from app.Localization import __
from app.Theme import Fonts, Theme

class StatusIndicator:
    STYLES = {
        'neutral': ('•', Theme.MUTED),
        'checking': ('…', Theme.MUTED),
        'success': ('✓', Theme.ACCENT),
        'failure': ('✕', Theme.DANGER),
    }

    def __init__(self, parent: tk.Widget, row: int, column: int, **grid_options):
        self.label = tk.Label(
            parent, anchor="nw", justify="left", height=2, wraplength=340,
            bg=parent.cget('bg'), font=Fonts.ui_font(9, bold=True),
        )
        self.label.grid(row=row, column=column, **grid_options)
        self.set_status('neutral')

    def set_status(self, status: str, message: str = "") -> None:
        icon, color = self.STYLES.get(status, self.STYLES['neutral'])
        text = message or __(f"status.{status}")
        self.label.config(text=f"{icon}  {text}", fg=color)
