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

## Сборка движка imapsync из исходников

GitHub Actions самостоятельно получает актуальные исходники [imapsync/imapsync](https://github.com/imapsync/imapsync), устанавливает Strawberry Perl и Perl-зависимости, затем собирает автономный `imapsync.exe` через PAR::Packer. Готовый движок встраивается внутрь русифицированного GUI через PyInstaller.

Никакой предварительной загрузки бинарника и ручной установки Perl на компьютере пользователя не требуется. Запустите **Actions → Сборка ImapSync-GUI и движка imapsync** и скачайте артефакт `ImapSync-GUI-RU-Windows-x64` после успешного выполнения.

Сборка берёт текущую ветку `master` upstream-проекта. Исходный код imapsync распространяется под [NO LIMIT PUBLIC LICENSE](https://github.com/imapsync/imapsync/blob/master/LICENSE).


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
