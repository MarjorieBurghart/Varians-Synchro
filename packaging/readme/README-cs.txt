VARIANS-SYNCHRO {version} — VERZE PŘIPRAVENÁ K POUŽITÍ

Tento archiv obsahuje Varians-Synchro a vše, co potřebuje (Python, Qt): nic
dalšího není třeba instalovat.


INSTALACE A SPUŠTĚNÍ
--------------------
Windows (10 nebo 11, 64 bitů)
  1. Rozbalte celý archiv (pravé tlačítko → „Extrahovat vše…“), například do
     složky Dokumenty. Nespouštějte Varians-Synchro přímo z archivu zip.
  2. Poklepejte na Varians-Synchro.exe ve složce Varians-Synchro-{version}.
  3. První spuštění: Varians-Synchro není podepsaný, a Windows proto může
     zobrazit „Systém Windows ochránil váš počítač“. Klikněte na „Další
     informace“ a potom na „Přesto spustit“. Program může před spuštěním
     prověřit také antivirus.
  Zástupce na ploše: pravé tlačítko na Varians-Synchro.exe → „Odeslat“ →
  „Plocha (vytvořit zástupce)“ (ve Windows 11 nejprve „Zobrazit další
  možnosti“).

macOS (archiv „macos-arm64“ pro Macy s čipem Apple Silicon: M1, M2…,
„macos-x64“ pro Macy s procesorem Intel)
  1. Poklepejte na archiv a přetáhněte Varians-Synchro.app do složky
     Aplikace.
  2. První spuštění: Varians-Synchro není podepsaný společností Apple, a
     macOS ho proto odmítne otevřít („Apple nemůže ověřit…“). Zavřete
     zprávu a otevřete Nastavení systému → Soukromí a zabezpečení: dole,
     vedle zprávy o Varians-Synchro, klikněte na „Přesto otevřít“ a
     potvrďte. V macOS 14 nebo starším stačí kliknout pravým tlačítkem (nebo
     s klávesou Ctrl) na Varians-Synchro.app → Otevřít → Otevřít. macOS se
     zeptá jen jednou.
  Pokud macOS hlásí, že je Varians-Synchro „poškozený“, zadejte v Terminálu:
     xattr -dr com.apple.quarantine /Applications/Varians-Synchro.app

Linux (64 bitů x86; Ubuntu 22.04, Debian 12, Fedora 36 nebo novější)
  1. Rozbalte archiv:  unzip Varians-Synchro-{version}-linux-x64.zip
  2. Spusťte:          ./Varians-Synchro-{version}/Varians-Synchro
  Varians-Synchro používá grafické knihovny, které jsou na každém linuxovém
  desktopu (OpenGL, libxcb, fontconfig). Pokud některá chybí, například v
  Debianu nebo Ubuntu:
     sudo apt install libegl1 libgl1 libxcb1 libxkbcommon0 libfontconfig1


PRVNÍ POKUS
-----------
Složka demo_local_ALTO vedle Varians-Synchro obsahuje malý ukázkový projekt
(exemple.vsynch: dva textové svědky o jedné stránce, s jejich soubory
ALTO). Zkopírujte tuto složku jinam, například do složky Dokumenty, potom
otevřete exemple.vsynch a postupujte podle oddílu „2. První pokus: ukázkový
projekt“ příručky.

Varians-Synchro připravuje projekty pro Varians, který se stahuje zvlášť:
  https://github.com/MarjorieBurghart/Varians/releases


AKTUALIZACE
-----------
Stáhněte nový archiv ze stránky verzí,
  https://github.com/MarjorieBurghart/Varians-Synchro/releases
a nahraďte starou složku (nebo Varians-Synchro.app) novou. Vaše projekty a
nastavení nejsou v této složce: zůstanou zachovány.

Chcete-li Varians-Synchro odinstalovat, stačí smazat tuto složku (nebo
Varians-Synchro.app).


KONTROLA
--------
Archiv: každý archiv má svůj otisk SHA-256 (soubor .sha256 na stránce
verzí). Výpočet:
  Windows (PowerShell):  Get-FileHash Varians-Synchro-{version}-windows-x64.zip
  macOS:                 shasum -a 256 Varians-Synchro-{version}-macos-arm64.zip
  Linux:                 sha256sum Varians-Synchro-{version}-linux-x64.zip

Instalace: při potížích může Varians-Synchro sám zkontrolovat své překlady,
nápovědu, zdroje, ukázkový projekt, jednu synchronizaci s jejími exporty do
Varians a své okno a zapsat o tom zprávu (několik sekund):
  Windows (příkazový řádek, ve složce Varians-Synchro):
     start /wait Varians-Synchro.exe --self-test zprava.json
  macOS:
     /Applications/Varians-Synchro.app/Contents/MacOS/Varians-Synchro --self-test ~/zprava.json
  Linux:
     ./Varians-Synchro --self-test zprava.json
Připojte tuto zprávu k hlášení problému:
  https://github.com/MarjorieBurghart/Varians-Synchro/issues


NÁPOVĚDA
--------
Příručka je přímo ve Varians-Synchro: tlačítko
„Otevřít uživatelskou příručku“ (F1), v jazyce zvoleném nahoře v okně
(„Jazyk“).


SOUČÁSTI
--------
Varians-Synchro obsahuje: Python (licence PSF); Qt a PySide6 (LGPL v3:
samostatné, nahraditelné knihovny; zdrojové kódy na https://code.qt.io);
certifi (MPL 2.0); v Linuxu knihovny systému, na kterém byl program
sestaven (například GLib, LGPL v2.1). Texty těchto licencí jsou ve složce
licences.
