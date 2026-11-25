import os
import shutil
import subprocess
import sys
from pathlib import Path


class ImapSync:
    def __init__(self, config: dict[str, str]):
        self.config = config

    @staticmethod
    def executable() -> str:
        """Найти встроенный imapsync.exe или установленный в PATH движок."""
        executable_name = "imapsync.exe" if os.name == "nt" else "imapsync"

        candidates: list[Path] = []
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            candidates.append(Path(bundle_dir) / "imapsync" / executable_name)

        app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
        candidates.extend([
            app_dir / "imapsync" / executable_name,
            app_dir / "vendor" / "imapsync" / executable_name,
            app_dir / executable_name,
        ])

        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

        found = shutil.which(executable_name)
        if found:
            return found

        raise FileNotFoundError(
            "Не найден imapsync.exe. Поместите движок в папку imapsync рядом с программой "
            "или добавьте его в системный PATH."
        )

    @staticmethod
    def check_credentials(host: str, port: str, user: str, password: str) -> None:
        """Проверить подключение к почтовому серверу."""
        args = [
            ImapSync.executable(),
            "--host1", host,
            "--port1", port,
            "--user1", user,
            "--password1", password,
            "--justlogin",
            "--nolog",
        ]

        result = subprocess.run(args, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            lines = (result.stderr or result.stdout).strip().splitlines()
            raise RuntimeError(lines[-1] if lines else f"Код завершения: {result.returncode}")

    def sync_process(self) -> subprocess.Popen[str]:
        cfg = self.config
        args = [
            self.executable(),
            "--host1", cfg["host1"],
            "--port1", cfg["port1"],
            "--user1", cfg["user1"],
            "--password1", cfg["password1"],
            "--host2", cfg["host2"],
            "--port2", cfg["port2"],
            "--user2", cfg["user2"],
            "--password2", cfg["password2"],
            "--automap",
            "--syncinternaldates",
            "--nofoldersizes",
            "--nolog",
        ]

        return subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
