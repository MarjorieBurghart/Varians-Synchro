VARIANS-SYNCHRO {version} — ГОТОВАЯ К ИСПОЛЬЗОВАНИЮ ВЕРСИЯ

Этот архив содержит Varians-Synchro и всё, что ему нужно (Python, Qt):
больше ничего устанавливать не требуется.


УСТАНОВКА И ЗАПУСК
------------------
Windows (10 или 11, 64 бита)
  1. Распакуйте весь архив (правая кнопка → «Извлечь все…»), например в
     папку «Документы». Не запускайте Varians-Synchro прямо из zip-архива.
  2. Дважды щёлкните Varians-Synchro.exe в папке Varians-Synchro-{version}.
  3. Первый запуск: Varians-Synchro не подписан, поэтому Windows может
     показать «Система Windows защитила ваш компьютер». Нажмите
     «Подробнее», затем «Выполнить в любом случае». Антивирус тоже может
     проверить программу перед запуском.
  Ярлык на рабочем столе: правая кнопка на Varians-Synchro.exe →
  «Отправить» → «Рабочий стол (создать ярлык)» (в Windows 11 сначала
  «Показать дополнительные параметры»).

macOS (архив «macos-arm64» для Mac с Apple Silicon: M1, M2…, «macos-x64»
для Mac с процессором Intel)
  1. Дважды щёлкните архив и перетащите Varians-Synchro.app в папку
     «Программы».
  2. Первый запуск: Varians-Synchro не подписан Apple, поэтому macOS
     отказывается его открыть («Apple не может проверить…»). Закройте
     сообщение и откройте «Системные настройки» → «Конфиденциальность и
     безопасность»: внизу, рядом с сообщением о Varians-Synchro, нажмите
     «Всё равно открыть» и подтвердите. В macOS 14 и более ранних
     достаточно щёлкнуть Varians-Synchro.app правой кнопкой (или с нажатой
     клавишей Control) → «Открыть» → «Открыть». macOS спрашивает только
     один раз.
  Если macOS сообщает, что Varians-Synchro «повреждён», введите в Терминале:
     xattr -dr com.apple.quarantine /Applications/Varians-Synchro.app

Linux (64 бита x86; Ubuntu 22.04, Debian 12, Fedora 36 или новее)
  1. Распакуйте архив:  unzip Varians-Synchro-{version}-linux-x64.zip
  2. Запустите:         ./Varians-Synchro-{version}/Varians-Synchro
  Varians-Synchro использует графические библиотеки, которые есть на любом
  рабочем столе Linux (OpenGL, libxcb, fontconfig). Если какой-то не
  хватает, например в Debian или Ubuntu:
     sudo apt install libegl1 libgl1 libxcb1 libxkbcommon0 libfontconfig1


ПЕРВЫЙ ОПЫТ
-----------
Папка demo_local_ALTO рядом с Varians-Synchro содержит небольшой пример
проекта (exemple.vsynch: два свидетеля по одной странице, с их файлами
ALTO). Скопируйте эту папку в другое место, например в «Документы», затем
откройте exemple.vsynch и следуйте разделу «2. Первый опыт: пример
проекта» руководства.

Varians-Synchro готовит проекты для Varians, который скачивается отдельно:
  https://github.com/MarjorieBurghart/Varians/releases


ОБНОВЛЕНИЕ
----------
Скачайте новый архив со страницы версий,
  https://github.com/MarjorieBurghart/Varians-Synchro/releases
и замените старую папку (или Varians-Synchro.app) новой. Ваши проекты и
настройки находятся не в этой папке: они сохранятся.

Чтобы удалить Varians-Synchro, просто удалите эту папку (или
Varians-Synchro.app).


ПРОВЕРКА
--------
Архив: у каждого архива есть контрольная сумма SHA-256 (файл .sha256 на
странице версий). Чтобы вычислить её:
  Windows (PowerShell):  Get-FileHash Varians-Synchro-{version}-windows-x64.zip
  macOS:                 shasum -a 256 Varians-Synchro-{version}-macos-arm64.zip
  Linux:                 sha256sum Varians-Synchro-{version}-linux-x64.zip

Установка: при неполадках Varians-Synchro может сам проверить свои
переводы, справку, ресурсы, пример проекта, одну синхронизацию с её
экспортом в Varians и своё окно и записать отчёт (несколько секунд):
  Windows (командная строка, в папке Varians-Synchro):
     start /wait Varians-Synchro.exe --self-test otchet.json
  macOS:
     /Applications/Varians-Synchro.app/Contents/MacOS/Varians-Synchro --self-test ~/otchet.json
  Linux:
     ./Varians-Synchro --self-test otchet.json
Приложите этот отчёт к сообщению о проблеме:
  https://github.com/MarjorieBurghart/Varians-Synchro/issues


СПРАВКА
-------
Руководство находится в самой программе: кнопка
«Открыть руководство пользователя» (F1), на языке, выбранном вверху окна
(«Язык»).


КОМПОНЕНТЫ
----------
В составе Varians-Synchro: Python (лицензия PSF); Qt и PySide6 (LGPL v3:
отдельные заменяемые библиотеки; исходный код на https://code.qt.io);
certifi (MPL 2.0); в Linux — библиотеки системы, на которой собрана
программа (например, GLib, LGPL v2.1). Тексты этих лицензий находятся в
папке licences.
