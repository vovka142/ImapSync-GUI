import tkinter as tk
from tkinter import ttk
from app.Localization import __
from app.Theme import Fonts, Theme

class ResultBanner(tk.Frame):
    # state -> (palette, icon)
    STATES = {
        'idle': ('neutral', '•'),
        'checking': ('busy', '…'),
        'running': ('busy', '▶'),
        'stopping': ('busy', '…'),
        'success': ('success', '✓'),
        'failure': ('danger', '✕'),
        'blocked': ('danger', '!'),
        'stopped': ('warn', '■'),
    }
    # palette -> (tint, accent)
    PALETTES = {
        'neutral': ("#E9E5DA", Theme.MUTED),
        'busy': ("#E3EAF3", Theme.FOCUS),
        'success': ("#E1F0E4", Theme.ACCENT),
        'danger': ("#F8E1DF", Theme.DANGER),
        'warn': ("#F3EBCF", "#7A5A00"),
    }

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Banner.Horizontal.TProgressbar", troughcolor="#C9D6E6", background=Theme.FOCUS,
            bordercolor="#C9D6E6", lightcolor=Theme.FOCUS, darkcolor=Theme.FOCUS,
        )

        self.stripe = tk.Frame(self, width=6)
        self.icon = tk.Label(self, font=Fonts.ui_font(14, bold=True), width=2)
        self.title = tk.Label(self, anchor="w", font=Fonts.ui_font(11, bold=True), fg=Theme.INK)
        self.detail = tk.Label(self, anchor="w", justify="left", font=Fonts.ui_font(9), fg=Theme.INK)
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=120, style="Banner.Horizontal.TProgressbar")

        self.grid_columnconfigure(2, weight=1)
        self.stripe.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.icon.grid(row=0, column=1, rowspan=2, padx=(12, 6), pady=10)
        self.title.grid(row=0, column=2, sticky="sw", pady=(10, 0))
        self.detail.grid(row=1, column=2, sticky="nw", pady=(0, 10))
        self.progress.grid(row=0, column=3, rowspan=2, padx=16)

        self.show('idle')

    def show(self, state: str, **fmt) -> None:
        palette, icon = self.STATES[state]
        tint, accent = self.PALETTES[palette]

        self.config(bg=tint)
        for widget in (self.title, self.detail, self.icon):
            widget.config(bg=tint)
        self.stripe.config(bg=accent)
        self.icon.config(text=icon, fg=accent)
        self.title.config(text=__(f"banner.{state}", **fmt))

        detail = __(f"banner.{state}_detail", **fmt)
        self.detail.config(text=detail)
        self.detail.grid() if detail else self.detail.grid_remove()

        if palette == 'busy':
            self.progress.grid()
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.grid_remove()
