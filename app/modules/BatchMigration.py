"""Загрузка и проверка списка почтовых ящиков для пакетной миграции."""

import csv
from pathlib import Path

REQUIRED_COLUMNS = (
    "source_user",
    "source_password",
    "target_user",
    "target_password",
)
OPTIONAL_COLUMNS = ("label",)


def load_jobs(csv_path: str | Path) -> list[dict[str, str]]:
    """Загрузить задания из CSV (UTF-8/UTF-8 BOM, разделитель запятая или точка с запятой)."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        sample = stream.read(4096)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(stream, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV-файл пустой или не содержит заголовков.")

        headers = [str(name or "").strip().lower() for name in reader.fieldnames]
        missing = [name for name in REQUIRED_COLUMNS if name not in headers]
        if missing:
            raise ValueError(
                "В CSV отсутствуют обязательные столбцы: " + ", ".join(missing)
            )

        jobs: list[dict[str, str]] = []
        for line_number, raw in enumerate(reader, start=2):
            row = {
                str(key or "").strip().lower(): (value or "")
                for key, value in raw.items()
                if key is not None
            }
            if not any(value.strip() for value in row.values()):
                continue

            job = {
                "source_user": row.get("source_user", "").strip(),
                "source_password": row.get("source_password", ""),
                "target_user": row.get("target_user", "").strip(),
                "target_password": row.get("target_password", ""),
                "label": row.get("label", "").strip(),
            }
            missing_values = [
                column for column in REQUIRED_COLUMNS if not job[column]
            ]
            if missing_values:
                raise ValueError(
                    f"Строка {line_number}: не заполнены поля "
                    + ", ".join(missing_values)
                )

            if not job["label"]:
                job["label"] = job["source_user"]
            job["csv_line"] = str(line_number)
            jobs.append(job)

    if not jobs:
        raise ValueError("В CSV нет ни одного задания для переноса.")
    return jobs


def write_template(csv_path: str | Path) -> None:
    """Создать пустой CSV-шаблон с обязательными заголовками."""
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("label", *REQUIRED_COLUMNS))
