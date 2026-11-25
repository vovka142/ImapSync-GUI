# ImapSync-GUI — русская версия

Русифицированная версия графической оболочки [jnloos/ImapSync-GUI](https://github.com/jnloos/ImapSync-GUI).

## Что изменено
- Русский язык включён по умолчанию.
- Добавлена локализация интерфейса: `locales/ru.json`.
- Английский и немецкий языки сохранены (запуск с аргументом `en` или `de`).
- Добавлена автоматическая сборка Windows x64 EXE через GitHub Actions.

## Скачать EXE
Откройте **Actions → Сборка Windows EXE**, выберите последний успешный запуск и скачайте артефакт
`ImapSync-GUI-RU-Windows-x64`. При публикации GitHub Release EXE автоматически прикладывается к релизу.

## Локальная сборка Windows 10/11
Требуется Python 3.10+ с Tkinter и установленный PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name ImapSync-GUI-RU --add-data "locales;locales" main.py
```

Готовый файл: `dist\ImapSync-GUI-RU.exe`.

## Важно: imapsync
Программа является графической оболочкой. Для фактического переноса почты требуется отдельный исполняемый
`imapsync`, доступный через PATH. Он и его Perl-зависимости не входят в EXE. Проверьте установку командой
`imapsync --version`.

Перед переносом рабочих ящиков проверьте настройки на тестовых учётных записях.

## Лицензия
Сохранена MIT License исходного проекта. См. файл `LICENSE`.
