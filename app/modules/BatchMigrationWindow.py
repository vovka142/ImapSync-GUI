"""Окно пакетной миграции почтовых ящиков из CSV."""

import csv
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.ImapSync import ImapSync
from app.Theme import Fonts, Theme
from app.modules.BatchMigration import load_jobs, write_template


class BatchMigrationWindow:
    """Проверяет учётные записи и запускает миграции из CSV."""

    def __init__(self, master: tk.Tk, source: dict[str, str], target: dict[str, str]):
        self.master = master
        self.window = tk.Toplevel(master)
        self.window.title("Пакетная миграция — ImapSync")
        self.window.geometry("1040x760")
        self.window.minsize(860, 620)
        self.window.configure(bg=Theme.PAPER)

        self.jobs: list[dict[str, str]] = []
        self.results: dict[int, dict[str, str]] = {}
        self.results_lock = threading.Lock()
        self.csv_path = ""
        self.batch_settings = None
        self.stop_event = threading.Event()
        self.process_lock = threading.Lock()
        self.processes: dict[int, object] = {}
        self.running = False

        self.source_host = tk.StringVar(value=source.get("host", ""))
        self.source_port = tk.StringVar(value=source.get("port", "993"))
        self.target_host = tk.StringVar(value=target.get("host", ""))
        self.target_port = tk.StringVar(value=target.get("port", "993"))
        self.mode = tk.StringVar(value="sequential")

        self.__build_ui()
        self.window.transient(master)
        self.window.protocol("WM_DELETE_WINDOW", self.__close)

    def __build_ui(self):
        outer = tk.Frame(self.window, bg=Theme.PAPER, padx=22, pady=18)
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(4, weight=1)
        outer.grid_rowconfigure(6, weight=1)

        tk.Label(
            outer, text="Пакетная миграция из CSV",
            font=Fonts.ui_font(18, bold=True), bg=Theme.PAPER, fg=Theme.INK,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        servers = tk.Frame(outer, bg=Theme.CARD, padx=14, pady=12,
                           highlightthickness=1, highlightbackground=Theme.LINE)
        servers.grid(row=1, column=0, sticky="ew")
        servers.grid_columnconfigure(1, weight=1)
        servers.grid_columnconfigure(5, weight=1)
        tk.Label(servers, text="Исходный сервер", font=Fonts.ui_font(10, bold=True),
                 bg=Theme.CARD, fg=Theme.INK).grid(row=0, column=0, columnspan=4, sticky="w")
        tk.Label(servers, text="Целевой сервер", font=Fonts.ui_font(10, bold=True),
                 bg=Theme.CARD, fg=Theme.INK).grid(row=0, column=4, columnspan=4, sticky="w")
        self.__server_field(servers, 1, 0, "Хост", self.source_host)
        self.__server_field(servers, 1, 2, "Порт", self.source_port, width=7)
        self.__server_field(servers, 1, 4, "Хост", self.target_host)
        self.__server_field(servers, 1, 6, "Порт", self.target_port, width=7)

        csv_bar = tk.Frame(outer, bg=Theme.PAPER)
        csv_bar.grid(row=2, column=0, sticky="ew", pady=(12, 8))
        self.file_label = tk.Label(csv_bar, text="CSV-файл не выбран",
                                   font=Fonts.ui_font(9), bg=Theme.PAPER, fg=Theme.MUTED)
        self.file_label.pack(side="left", fill="x", expand=True)
        self.__button(csv_bar, "Шаблон CSV", self.__save_template, Theme.SECONDARY, Theme.INK).pack(side="right", padx=(6, 0))
        self.__button(csv_bar, "Загрузить CSV", self.__load_csv, Theme.ACCENT, "white").pack(side="right")

        mode_bar = tk.Frame(outer, bg=Theme.PAPER)
        mode_bar.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        tk.Label(mode_bar, text="Режим:", font=Fonts.ui_font(10, bold=True),
                 bg=Theme.PAPER, fg=Theme.INK).pack(side="left", padx=(0, 12))
        tk.Radiobutton(mode_bar, text="Последовательно (1 ящик)",
                       variable=self.mode, value="sequential", bg=Theme.PAPER,
                       activebackground=Theme.PAPER, font=Fonts.ui_font(9)).pack(side="left")
        tk.Radiobutton(mode_bar, text="Параллельно (до 3 ящиков)",
                       variable=self.mode, value="parallel", bg=Theme.PAPER,
                       activebackground=Theme.PAPER, font=Fonts.ui_font(9)).pack(side="left", padx=(12, 0))

        table_frame = tk.Frame(outer, bg=Theme.PAPER)
        table_frame.grid(row=4, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self.table = ttk.Treeview(
            table_frame, columns=("source", "target", "status", "details"),
            show="headings", height=9,
        )
        for column, title, width in (
            ("source", "Исходный ящик", 220),
            ("target", "Целевой ящик", 220),
            ("status", "Статус", 150),
            ("details", "Результат", 300),
        ):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, minwidth=100, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.progress = tk.StringVar(value="Загрузите CSV со списком почтовых ящиков.")
        tk.Label(outer, textvariable=self.progress, font=Fonts.ui_font(9),
                 bg=Theme.PAPER, fg=Theme.MUTED, anchor="w").grid(
                     row=5, column=0, sticky="ew", pady=(8, 6))

        log_frame = tk.Frame(outer, bg=Theme.PAPER)
        log_frame.grid(row=6, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=8, font=Fonts.mono_font(9),
                           wrap="word", state="disabled", bg=Theme.LOG_BG,
                           fg=Theme.LOG_FG, relief="flat", padx=10, pady=8)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        buttons = tk.Frame(outer, bg=Theme.PAPER)
        buttons.grid(row=7, column=0, sticky="ew", pady=(12, 0))
        self.start_button = self.__button(buttons, "Начать перенос", self.__start, Theme.ACCENT, "white")
        self.start_button.pack(side="left")
        self.stop_button = self.__button(buttons, "Остановить", self.__stop, Theme.DANGER, "white")
        self.stop_button.pack(side="left", padx=(8, 0))
        self.stop_button.config(state="disabled")
        self.__button(buttons, "Экспорт результатов", self.__export, Theme.SECONDARY, Theme.INK).pack(side="right")

    @staticmethod
    def __server_field(parent, row, column, label, variable, width=24):
        tk.Label(parent, text=label, font=Fonts.ui_font(9), bg=Theme.CARD,
                 fg=Theme.MUTED).grid(row=row, column=column, sticky="w", padx=(0, 5), pady=(8, 0))
        entry = tk.Entry(parent, textvariable=variable, width=width, font=Fonts.ui_font(9),
                         relief="flat", bg=Theme.FIELD, fg=Theme.INK,
                         highlightthickness=1, highlightbackground=Theme.LINE)
        entry.grid(row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=(8, 0))

    @staticmethod
    def __button(parent, text, command, background, foreground):
        return tk.Button(
            parent, text=text, command=command, font=Fonts.ui_font(9, bold=True),
            bg=background, fg=foreground, activebackground=background,
            activeforeground=foreground, relief="flat", padx=14, pady=8,
            highlightthickness=0, cursor="hand2",
        )

    def __save_template(self):
        path = filedialog.asksaveasfilename(
            parent=self.window, title="Сохранить шаблон CSV",
            defaultextension=".csv", initialfile="imap-migration-template.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            write_template(path)
            messagebox.showinfo("Шаблон создан", f"Файл сохранён:\n{path}", parent=self.window)
        except OSError as error:
            messagebox.showerror("Ошибка", str(error), parent=self.window)

    def __load_csv(self):
        if self.running:
            return
        path = filedialog.askopenfilename(
            parent=self.window, title="Выберите список почтовых ящиков",
            filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            jobs = load_jobs(path)
        except (OSError, UnicodeError, csv.Error, ValueError) as error:
            messagebox.showerror("Ошибка CSV", str(error), parent=self.window)
            return

        self.jobs = jobs
        self.results.clear()
        self.csv_path = path
        self.file_label.config(text=f"{Path(path).name} — {len(jobs)} ящиков")
        for item in self.table.get_children():
            self.table.delete(item)
        for index, job in enumerate(jobs):
            self.table.insert("", "end", iid=str(index), values=(
                job["source_user"], job["target_user"], "Ожидание", ""
            ))
        self.progress.set(f"Загружено заданий: {len(jobs)}. Можно запускать перенос.")
        self.__log(f"Загружен файл: {path}")
        self.__log(f"Количество почтовых ящиков: {len(jobs)}")
        self.__log("ВНИМАНИЕ: CSV содержит пароли в открытом виде. Ограничьте доступ к файлу.")

    def __start(self):
        if self.running:
            return
        if not self.jobs:
            messagebox.showwarning("Нет заданий", "Сначала загрузите CSV-файл.", parent=self.window)
            return
        if not self.source_host.get().strip() or not self.target_host.get().strip():
            messagebox.showwarning("Не заданы серверы", "Укажите адреса обоих IMAP-серверов.", parent=self.window)
            return
        try:
            source_port = int(self.source_port.get())
            target_port = int(self.target_port.get())
            if not (1 <= source_port <= 65535 and 1 <= target_port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Неверный порт", "Порт должен быть числом от 1 до 65535.", parent=self.window)
            return

        self.stop_event.clear()
        self.batch_settings = {
            "source_host": self.source_host.get().strip(),
            "source_port": self.source_port.get().strip(),
            "target_host": self.target_host.get().strip(),
            "target_port": self.target_port.get().strip(),
            "workers": 3 if self.mode.get() == "parallel" else 1,
        }
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        for index, job in enumerate(self.jobs):
            self.__set_row(index, "Проверка", "")
        self.progress.set("Проверка учётных записей перед переносом…")
        self.__log("Начата проверка учётных записей. Проверка выполняется последовательно.")
        threading.Thread(target=self.__preflight_and_run, daemon=True).start()

    def __preflight_and_run(self):
        settings = self.batch_settings
        source_host, source_port = settings["source_host"], settings["source_port"]
        target_host, target_port = settings["target_host"], settings["target_port"]
        ready: list[int] = []

        # PAR::Packer использует общий кэш распаковки. Предварительные проверки
        # запускаются строго по одной, чтобы не повторить гонку распаковки.
        for index, job in enumerate(self.jobs):
            if self.stop_event.is_set():
                break
            try:
                ImapSync.check_credentials(source_host, source_port, job["source_user"], job["source_password"])
                ImapSync.check_credentials(target_host, target_port, job["target_user"], job["target_password"])
                ready.append(index)
                self.__set_row_threadsafe(index, "Готов к переносу", "Подключение успешно")
                self.__log_threadsafe(f"[{job['source_user']}] Проверка подключения пройдена.")
            except Exception as error:
                details = str(error)[:500]
                self.__set_row_threadsafe(index, "Ошибка проверки", details)
                with self.results_lock:
                    self.results[index] = {
                        "source_user": job["source_user"],
                        "target_user": job["target_user"],
                        "status": "Ошибка проверки",
                        "details": details,
                    }
                self.__log_threadsafe(f"[{job['source_user']}] Ошибка проверки: {error}")

            self.__set_progress_threadsafe(f"Проверка ящиков: {index + 1}/{len(self.jobs)}")

        if self.stop_event.is_set():
            self.__finish_threadsafe("Операция остановлена во время проверки.")
            return
        if not ready:
            self.__finish_threadsafe("Нет ящиков с успешно проверенными учётными данными.")
            return

        workers = settings["workers"]
        mode_name = "параллельный (до 3 одновременно)" if workers == 3 else "последовательный"
        self.__log_threadsafe(f"Проверка завершена. Запуск режима: {mode_name}.")
        self.__set_progress_threadsafe(f"Перенос: 0/{len(ready)}")

        completed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.__run_one, index, source_host, source_port, target_host, target_port): index
                for index in ready
            }
            for future in as_completed(futures):
                index = futures[future]
                try:
                    future.result()
                except Exception as error:
                    details = str(error)[:500]
                    self.__set_row_threadsafe(index, "Ошибка", details)
                    with self.results_lock:
                        self.results[index] = {
                            "source_user": self.jobs[index]["source_user"],
                            "target_user": self.jobs[index]["target_user"],
                            "status": "Ошибка",
                            "details": details,
                        }
                    self.__log_threadsafe(f"[{self.jobs[index]['source_user']}] Ошибка: {error}")
                completed += 1
                self.__set_progress_threadsafe(f"Обработано: {completed}/{len(ready)}")

        if self.stop_event.is_set():
            self.__finish_threadsafe("Перенос остановлен пользователем.")
        else:
            successful = sum(1 for result in self.results.values() if result.get("status") == "Успешно")
            failed = len(self.jobs) - successful
            self.__finish_threadsafe(f"Завершено. Успешно: {successful}; с ошибками: {failed}.")

    def __config(self, index, source_host, source_port, target_host, target_port):
        job = self.jobs[index]
        return {
            "host1": source_host, "port1": source_port,
            "user1": job["source_user"], "password1": job["source_password"],
            "host2": target_host, "port2": target_port,
            "user2": job["target_user"], "password2": job["target_password"],
        }

    def __run_one(self, index, source_host, source_port, target_host, target_port):
        if self.stop_event.is_set():
            self.__set_row_threadsafe(index, "Остановлено", "")
            job = self.jobs[index]
            with self.results_lock:
                self.results[index] = {
                    "source_user": job["source_user"],
                    "target_user": job["target_user"],
                    "status": "Остановлено",
                    "details": "Не запускалось: остановлено пользователем",
                }
            return

        job = self.jobs[index]
        cfg = self.__config(index, source_host, source_port, target_host, target_port)
        self.__set_row_threadsafe(index, "Перенос", "Выполняется")
        self.__log_threadsafe(f"[{job['source_user']}] Начат перенос.")
        process = ImapSync(cfg).sync_process()
        with self.process_lock:
            self.processes[index] = process
        if self.stop_event.is_set():
            process.terminate()

        try:
            if process.stdout:
                for line in process.stdout:
                    if line.strip():
                        self.__log_threadsafe(f"[{job['source_user']}] {line.rstrip()}")
            returncode = process.wait()
        finally:
            with self.process_lock:
                self.processes.pop(index, None)

        if self.stop_event.is_set():
            status, details = "Остановлено", "Прервано пользователем"
        elif returncode == 0:
            status, details = "Успешно", "Перенос завершён"
        else:
            status, details = "Ошибка", f"Код завершения: {returncode}"

        self.__set_row_threadsafe(index, status, details)
        with self.results_lock:
            self.results[index] = {
                "source_user": job["source_user"],
                "target_user": job["target_user"],
                "status": status,
                "details": details,
            }
        self.__log_threadsafe(f"[{job['source_user']}] {details}.")

    def __set_row(self, index, status, details):
        if self.table.exists(str(index)):
            values = list(self.table.item(str(index), "values"))
            values[2], values[3] = status, details
            self.table.item(str(index), values=values)

    def __set_row_threadsafe(self, index, status, details):
        self.window.after(0, self.__set_row, index, status, details)

    def __set_progress_threadsafe(self, value):
        self.window.after(0, self.progress.set, value)

    def __log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def __log_threadsafe(self, message):
        self.window.after(0, self.__log, message)

    def __finish_threadsafe(self, message):
        self.window.after(0, self.__finish, message)

    def __finish(self, message):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress.set(message)
        self.__log(message)

    def __stop(self):
        if not self.running:
            return
        self.stop_event.set()
        self.stop_button.config(state="disabled")
        self.progress.set("Остановка заданий…")
        self.__log("Запрошена остановка. Активные процессы будут завершены.")
        with self.process_lock:
            active = list(self.processes.values())
        for process in active:
            try:
                process.terminate()
            except OSError:
                pass

    def __export(self):
        if not self.results:
            messagebox.showinfo("Нет результатов", "Пока нет завершённых заданий для экспорта.", parent=self.window)
            return
        path = filedialog.asksaveasfilename(
            parent=self.window, title="Экспорт результатов",
            defaultextension=".csv", initialfile="imap-migration-results.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            with self.results_lock:
                export_rows = [self.results[index].copy() for index in sorted(self.results)]
            with open(path, "w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=("source_user", "target_user", "status", "details")
                )
                writer.writeheader()
                for result in export_rows:
                    writer.writerow(result)
            messagebox.showinfo("Экспорт завершён", f"Результаты сохранены:\n{path}", parent=self.window)
        except OSError as error:
            messagebox.showerror("Ошибка экспорта", str(error), parent=self.window)

    def __close(self):
        if self.running:
            messagebox.showinfo(
                "Миграция выполняется",
                "Сначала остановите пакетную миграцию и дождитесь завершения процессов.",
                parent=self.window,
            )
            return
        self.window.destroy()
