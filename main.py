import sys
import tkinter as tk

from app.Localization import Localization
from app.ImapSyncWindow import ImapSyncWindow


def main():
    # Русский язык используется по умолчанию; можно передать en или de.
    lang = sys.argv[1] if len(sys.argv) > 1 else "ru"
    Localization.load(lang)

    root = tk.Tk()
    ImapSyncWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
