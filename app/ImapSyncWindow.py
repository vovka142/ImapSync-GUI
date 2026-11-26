import subprocess
import tkinter as tk
from threading import Lock, Thread
from typing import Optional
from app.ImapSync import ImapSync
from app.Localization import __
from app.Theme import Fonts, Theme
from app.modules.CredentialForm import CredentialForm
from app.modules.OutputBox import OutputBox
from app.modules.ResultBanner import ResultBanner
from app.modules.StatusIndicator import StatusIndicator

CheckError = tuple[str, tuple[str, ...]]  # (message, keys of the fields to mark)

class ImapSyncWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._process_lock = Lock()
        self._running_process = None
        self._stop_requested = False
        self._state = "idle"
        Fonts.load()
        self.root.title("IMAPSync — перенос почты")
        self.root.geometry("1120x790")
        self.root.minsize(940, 700)
        self.root.configure(bg=Theme.PAPER)

        # Основная рабочая область
        self.container = tk.Frame(self.root, bg=Theme.PAPER, padx=34, pady=30)
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(5, weight=1)

        self.__build_header()
        self.__build_forms()
        self.__build_actions()
        self.__build_output()
        self.root.bind("<Return>", self.__on_return)

    def __build_header(self):
        header = tk.Frame(self.container, bg=Theme.PAPER)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 28))
        header.grid_columnconfigure(1, weight=1)

        mark = tk.Frame(header, bg=Theme.ACCENT, width=48, height=48)
        mark.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
        mark.grid_propagate(False)
        tk.Label(mark, text="IM", font=Fonts.ui_font(16, bold=True), bg=Theme.ACCENT, fg="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(header, text="IMAPSync", font=Fonts.ui_font(23, bold=True), bg=Theme.PAPER, fg=Theme.INK).grid(row=0, column=1, sticky="sw")
        tk.Label(header, text=__("app_subtitle"), font=Fonts.ui_font(10), bg=Theme.PAPER, fg=Theme.MUTED).grid(row=1, column=1, sticky="nw", pady=(2, 0))

        pill = tk.Frame(header, bg="#EAE9FF", padx=12, pady=7)
        pill.grid(row=0, column=2, rowspan=2, sticky="e")
        tk.Label(pill, text="MAIL TRANSFER", font=Fonts.ui_font(8, bold=True), bg="#EAE9FF", fg=Theme.ACCENT).pack()

    def __build_forms(self):
        forms_frame = tk.Frame(self.container, bg=Theme.PAPER)
        forms_frame.grid(row=1, column=0, sticky="ew")
        forms_frame.grid_columnconfigure(0, weight=1, uniform="card")
        forms_frame.grid_columnconfigure(2, weight=1, uniform="card")
        tk.Label(forms_frame, text="→", font=Fonts.ui_font(20), bg=Theme.PAPER, fg=Theme.MUTED).grid(row=0, column=1, padx=14)

        self.source_form, self.source_status = self.__build_card(forms_frame, 0, "sections.source")
        self.target_form, self.target_status = self.__build_card(forms_frame, 2, "sections.target")

    @staticmethod
    def __build_card(parent: tk.Widget, column: int, title_key: str) -> tuple[CredentialForm, StatusIndicator]:
        card = tk.Frame(parent, bg=Theme.CARD, highlightthickness=1, highlightbackground=Theme.LINE, highlightcolor=Theme.LINE, padx=22, pady=22)
        card.grid(row=0, column=column, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text=__(title_key), font=Fonts.ui_font(12, bold=True), bg=Theme.CARD, fg=Theme.INK).grid(row=0, column=0, sticky="w", pady=(0, 12))
        form = CredentialForm(card, ["host", "port", "user", "password"])
        form.grid(row=1, column=0, sticky="ew")
        status = StatusIndicator(card, row=2, column=0, sticky="w", pady=(8, 0))
        return form, status

    def __build_actions(self):
        actions = tk.Frame(self.container, bg=Theme.PAPER)
        actions.grid(row=2, column=0, sticky="ew", pady=(22, 16))
        self.action_button = self.__make_button(actions, __("button_start"), self.__start_sync, Theme.ACCENT, "white", 11, bold=True)
        self.action_button.pack(side="left")

        self.banner = ResultBanner(self.container)
        self.banner.grid(row=3, column=0, sticky="ew")

    def __build_output(self):
        bar = tk.Frame(self.container, bg=Theme.PAPER)
        bar.grid(row=4, column=0, sticky="ew", pady=(20, 8))
        self.details_button = tk.Button(
            bar, command=lambda: self.__set_details_visible(not self._details_visible), font=Fonts.ui_font(10, bold=True),
            relief="flat", bg=Theme.PAPER, fg=Theme.INK, activebackground=Theme.PAPER, activeforeground=Theme.INK,
            highlightthickness=0, cursor="hand2",
        )
        self.details_button.pack(side="left")
        self.__make_button(bar, __("button_clear"), self.__clear_output, Theme.SECONDARY, Theme.INK, 9).pack(side="right")

        self.output_box = OutputBox(self.container, height=14, width=40)  # width stretches with the window
        self.output_box.widget().grid(row=5, column=0, sticky="nsew")
        self.__set_details_visible(False)

    @staticmethod
    def __make_button(parent: tk.Widget, text: str, command, bg: str, fg: str, size: int, bold: bool = False) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command, font=Fonts.ui_font(size, bold), bg=bg, fg=fg,
            activebackground=bg, activeforeground=fg, relief="flat", padx=22 if bold else 14, pady=11 if bold else 6,
            highlightthickness=0, cursor="hand2",
        )

    def __set_details_visible(self, visible: bool):
        self._details_visible = visible
        if visible:
            self.output_box.widget().grid()
        else:
            self.output_box.widget().grid_remove()
        arrow = "▾" if visible else "▸"
        self.details_button.config(text=f"{arrow} {__('details_hide' if visible else 'details_show')}")

    def __clear_output(self):
        self.output_box.clear()

    def __set_state(self, state: str):
        self._state = state
        label, bg, command, enabled = {
            "idle": (__("button_start"), Theme.ACCENT, self.__start_sync, True),
            "checking": (__("button_checking"), Theme.MUTED, self.__start_sync, False),
            "running": (__("button_stop"), Theme.DANGER, self.__stop_sync, True),
            "stopping": (__("button_stopping"), Theme.MUTED, self.__stop_sync, False),
        }[state]
        self.action_button.config(
            text=label, bg=bg, activebackground=bg, command=command,
            state="normal" if enabled else "disabled", disabledforeground="white",
        )
        self.banner.show(state)

    def __on_return(self, _event):
        focused = self.root.focus_get()
        if self._state == "idle" and (isinstance(focused, tk.Entry) or focused is self.action_button):
            self.__start_sync()

    def __start_sync(self):
        if not self.__validate_inputs():
            self.banner.show("blocked")
            return

        for form, status in ((self.source_form, self.source_status), (self.target_form, self.target_status)):
            form.clear_invalid()
            status.set_status('checking')
        self.__set_state("checking")
        Thread(target=self.__check_credentials, args=(self.__build_config(),), daemon=True).start()

    def __validate_inputs(self) -> bool:
        valid, focus = True, True
        for form, status in ((self.source_form, self.source_status), (self.target_form, self.target_status)):
            errors = form.validate()
            if not errors:
                status.set_status('neutral')
                continue
            valid = False
            form.mark_invalid(errors, focus=focus)
            focus = False
            status.set_status('failure', __(next(iter(errors.values()))))
        return valid

    def __check_credentials(self, cfg: dict[str, str]):
        # Worker thread: no widget access here, results go back through root.after
        # PAR::Packer использует общий временный кэш для одного EXE.
        # Не запускаем два экземпляра одновременно: параллельная распаковка
        # одного кэша может завершиться ошибкой Permission denied.
        source = self.__check_side(cfg['host1'], cfg['port1'], cfg['user1'], cfg['password1'])
        target = self.__check_side(cfg['host2'], cfg['port2'], cfg['user2'], cfg['password2'])
        self.root.after(0, self.__on_checked, source, target)

    @staticmethod
    def __check_side(host: str, port: str, user: str, password: str) -> Optional[CheckError]:
        try:
            ImapSync.check_credentials(host, port, user, password)
        except FileNotFoundError:
            return __("check_imapsync_missing"), ()
        except subprocess.TimeoutExpired:
            return __("check_timeout", host=host, port=port), ("host", "port")
        except RuntimeError as e:
            return __("check_failed_detail", detail=e), ("user", "password")
        return None

    def __on_checked(self, source_error: Optional[CheckError], target_error: Optional[CheckError]):
        sides = (
            (self.source_form, self.source_status, source_error, "sections.source"),
            (self.target_form, self.target_status, target_error, "sections.target"),
        )
        for form, status, error, section_key in sides:
            if error is None:
                status.set_status('success')
                continue
            message, keys = error
            status.set_status('failure', message)
            form.mark_invalid(keys)
            self.output_box.append(f"{__(section_key)}: {message}")

        if source_error or target_error:
            self.__set_state("idle")
            self.banner.show("blocked")
            return

        # Start migration if valid
        self.output_box.append(__("migration_starting"))
        self._stop_requested = False
        self.__set_state("running")
        Thread(target=self.__run_sync, daemon=True).start()

    def __stop_sync(self):
        self._stop_requested = True
        self.__set_state("stopping")
        self.output_box.append(__("migration_stopping"))

        with self._process_lock:
            process = self._running_process

        if process is None:
            return

        try:
            process.terminate()
        except Exception:
            pass

    def __run_sync(self):
        # Run process and display logs
        cfg = self.__build_config()
        process = ImapSync(cfg).sync_process()
        with self._process_lock:
            self._running_process = process

        if self._stop_requested:
            try:
                process.terminate()
            except Exception:
                pass

        for line in process.stdout:
            self.output_box.append(line.strip())
        process.wait()

        with self._process_lock:
            self._running_process = None

        # Feedback and reset
        if process.returncode == 0:
            self.output_box.append(__("migration_success"))
        elif self._stop_requested:
            self.output_box.append(__("migration_stopped"))
        else:
            self.output_box.append(f"{__('migration_failed')} (Code {process.returncode})")
        self.root.after(0, self.__finish, process.returncode)

    def __finish(self, returncode: int):
        self.__set_state("idle")
        if returncode == 0:
            self.banner.show("success")
        elif self._stop_requested:
            self.banner.show("stopped")
        else:
            self.banner.show("failure", code=returncode)
            self.__set_details_visible(True)

    def __build_config(self) -> dict[str, str]:
        src = self.source_form.get_config()
        tgt = self.target_form.get_config()

        return {
            'host1': src['host'], 'port1': src['port'], 'user1': src['user'], 'password1': src['password'],
            'host2': tgt['host'],  'port2': tgt['port'], 'user2': tgt['user'], 'password2': tgt['password'],
        }
