import tkinter as tk
from app.Localization import __
from app.Theme import Fonts, Theme

class CredentialForm(tk.Frame):
    def __init__(self, master: tk.Widget, keys: list[str], **kwargs):
        super().__init__(master, bg=Theme.CARD, **kwargs)
        self.entries: dict[str, tk.Entry] = {}
        self._placeholder_active: set[str] = set()
        port_check = (self.register(self.__is_port_input), "%P")

        for i, key in enumerate(keys):
            tk.Label(
                self, text=__(f"fields.{key}"), anchor="w", bg=Theme.CARD, fg=Theme.MUTED, font=Fonts.ui_font(9)
            ).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=4)

            holder = tk.Frame(self, bg=Theme.CARD)
            holder.grid(row=i, column=1, sticky="ew", pady=4)
            entry = tk.Entry(
                holder, show="*" if "password" in key else "", font=Fonts.ui_font(10),
                relief="flat", bg=Theme.FIELD, fg=Theme.INK, insertbackground=Theme.INK,
                highlightthickness=1, highlightbackground=Theme.LINE, highlightcolor=Theme.FOCUS,
            )
            entry.pack(side="left", fill="x", expand=True, ipady=4)
            entry.bind("<KeyRelease>", lambda _e, k=key: self.__reset_entry(k))

            if key == "port":
                entry.insert(0, "993")  # default IMAP port
                entry.config(validate="key", validatecommand=port_check)
            elif "password" in key:
                self.__add_visibility_toggle(holder, entry)
            else:
                self.__attach_placeholder(key, entry)

            self.entries[key] = entry

        self.grid_columnconfigure(1, weight=1)

    def get_config(self) -> dict[str, str]:
        return {
            k: "" if k in self._placeholder_active else (e.get() if "password" in k else e.get().strip())
            for k, e in self.entries.items()
        }

    def validate(self) -> dict[str, str]:
        """Map each invalid field key to the locale key of its error."""
        config = self.get_config()
        errors = {k: "validation.required" for k, v in config.items() if not v}
        port = config.get("port", "")
        if port and not 1 <= int(port) <= 65535:
            errors["port"] = "validation.port"
        return errors

    def mark_invalid(self, keys, focus: bool = False) -> None:
        keys = [k for k in keys if k in self.entries]
        for key in keys:
            self.entries[key].config(highlightbackground=Theme.DANGER, highlightcolor=Theme.DANGER)
        if focus and keys:
            self.entries[keys[0]].focus_set()

    def clear_invalid(self) -> None:
        for key in self.entries:
            self.__reset_entry(key)

    def __reset_entry(self, key: str) -> None:
        self.entries[key].config(highlightbackground=Theme.LINE, highlightcolor=Theme.FOCUS)

    @staticmethod
    def __is_port_input(proposed: str) -> bool:
        return proposed == "" or (proposed.isdigit() and len(proposed) <= 5)

    def __attach_placeholder(self, key: str, entry: tk.Entry) -> None:
        text = __(f"placeholders.{key}")
        if text == f"placeholders.{key}":  # no translation, no placeholder
            return

        def show(_event=None):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=Theme.MUTED)
                self._placeholder_active.add(key)

        def hide(_event=None):
            if key in self._placeholder_active:
                entry.delete(0, tk.END)
                entry.config(fg=Theme.INK)
                self._placeholder_active.discard(key)

        entry.bind("<FocusIn>", hide)
        entry.bind("<FocusOut>", show)
        show()

    @staticmethod
    def __add_visibility_toggle(holder: tk.Frame, entry: tk.Entry) -> None:
        def toggle():
            hidden = entry.cget("show") == "*"
            entry.config(show="" if hidden else "*")
            button.config(text=__("password_hide" if hidden else "password_show"))

        button = tk.Button(
            holder, text=__("password_show"), command=toggle, font=Fonts.ui_font(9),
            relief="flat", bg=Theme.CARD, fg=Theme.MUTED, activebackground=Theme.CARD, activeforeground=Theme.INK,
            highlightthickness=2, highlightbackground=Theme.CARD, highlightcolor=Theme.FOCUS, cursor="hand2",
        )
        button.pack(side="left", padx=(6, 0))
