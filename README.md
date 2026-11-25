# ImapSync-GUI — русская версия

Русифицированная версия графической оболочки [jnloos/ImapSync-GUI](https://github.com/jnloos/ImapSync-GUI).

## Что изменено
- Русский язык включён по умолчанию.
- Добавлена локализация интерфейса: `locales/ru.json`.
- Английский и немецкий языки сохранены (запуск с аргументом `en` или `de`).
- Добавлена автоматическая сборка Windows x64 через GitHub Actions.
- GUI умеет находить встроенный `imapsync.exe` или использовать установленный движок из `PATH`.

## Сборка Windows

Откройте **Actions → Сборка Windows EXE**, выберите последний успешный запуск и скачайте артефакт
`ImapSync-GUI-RU-Windows-x64`. В архиве находится приложение и, если движок был добавлен в исходники перед сборкой, папка `imapsync`.

При публикации GitHub Release архив автоматически прикладывается к релизу.

## Как встроить imapsync.exe

Положите 64-битный Windows-бинарник `imapsync.exe` в каталог:

```
vendor/imapsync/imapsync.exe
```

После этого запустите сборку GitHub Actions. Workflow добавит бинарник внутрь PyInstaller EXE; приложение извлечёт его во временный каталог при запуске и использует автоматически.

Официальная инструкция imapsync описывает Windows-бинарник как автономный файл со встроенными Perl и Perl-модулями: [README_Windows.txt](https://github.com/imapsync/imapsync/blob/master/README_Windows.txt). Не включайте в публичный репозиторий бинарник из платного дистрибутива без проверки условий его распространения. Исходный код imapsync публикуется под NO LIMIT PUBLIC LICENSE.

Если встроенного файла нет, программа продолжит искать `imapsync.exe` в `PATH`. Проверка из командной строки:

```powershell
imapsync.exe --version
```

## Локальная сборка GUI без встроенного движка

Требуется Python 3.10+ с Tkinter и PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name ImapSync-GUI-RU --add-data "locales;locales" main.py
```

Готовый файл: `dist\\ImapSync-GUI-RU.exe`.

Перед переносом рабочих ящиков проверьте настройки на тестовых учётных записях.

## Лицензии

GUI: MIT License исходного проекта. Движок imapsync: NO LIMIT PUBLIC LICENSE; см. [лицензию upstream](https://github.com/imapsync/imapsync/blob/master/LICENSE).
