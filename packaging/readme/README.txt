VARIANS-SYNCHRO {version} — READY-TO-USE VERSION

This archive contains Varians-Synchro and everything it needs (Python, Qt):
there is nothing else to install.


INSTALL AND START
-----------------
Windows (10 or 11, 64-bit)
  1. Extract the whole archive (right-click → "Extract All…"), for example
     into Documents. Do not start Varians-Synchro from inside the zip file.
  2. Double-click Varians-Synchro.exe, in the Varians-Synchro-{version}
     folder.
  3. First start: since Varians-Synchro is not signed, Windows may display
     "Windows protected your PC". Click "More info", then "Run anyway". An
     antivirus program may also scan the program before letting it start.
  For a desktop shortcut: right-click Varians-Synchro.exe → "Send to" →
  "Desktop (create shortcut)" (on Windows 11, first "Show more options").

macOS ("macos-arm64" archive for Apple Silicon Macs: M1, M2…, "macos-x64"
for Intel Macs)
  1. Double-click the archive, then drag Varians-Synchro.app into the
     Applications folder.
  2. First start: since Varians-Synchro is not signed by Apple, macOS
     refuses to open it ("Apple could not verify…"). Close the message, then
     open System Settings → Privacy & Security: at the bottom, next to the
     message about Varians-Synchro, click "Open Anyway" and confirm. On
     macOS 14 or earlier, you can simply right-click (or Control-click)
     Varians-Synchro.app → Open → Open. macOS asks only once.
  If macOS says that Varians-Synchro "is damaged", type in the Terminal:
     xattr -dr com.apple.quarantine /Applications/Varians-Synchro.app

Linux (64-bit x86; Ubuntu 22.04, Debian 12, Fedora 36 or later)
  1. Extract the archive:  unzip Varians-Synchro-{version}-linux-x64.zip
  2. Start:                ./Varians-Synchro-{version}/Varians-Synchro
  Varians-Synchro uses the graphics libraries found on every Linux desktop
  (OpenGL, libxcb, fontconfig). If one is missing, for example on Debian or
  Ubuntu:
     sudo apt install libegl1 libgl1 libxcb1 libxkbcommon0 libfontconfig1


FIRST TRY
---------
The demo_local_ALTO folder, next to Varians-Synchro, contains a small
sample project (exemple.vsynch: two witnesses of one page each, with their
ALTO files). Copy this folder elsewhere, for example into Documents, then
open exemple.vsynch and follow the section "2. First try: the sample
project" of the guide.

Varians-Synchro prepares projects for Varians, which is downloaded
separately:
  https://github.com/MarjorieBurghart/Varians/releases


UPDATE
------
Download the new archive from the releases page,
  https://github.com/MarjorieBurghart/Varians-Synchro/releases
then replace the old folder (or Varians-Synchro.app) with the new one. Your
projects and your settings are not in this folder: they are kept.

To uninstall Varians-Synchro, simply delete this folder (or
Varians-Synchro.app).


CHECK
-----
The archive: each archive has its SHA-256 checksum (.sha256 file on the
releases page). To compute it:
  Windows (PowerShell):  Get-FileHash Varians-Synchro-{version}-windows-x64.zip
  macOS:                 shasum -a 256 Varians-Synchro-{version}-macos-arm64.zip
  Linux:                 sha256sum Varians-Synchro-{version}-linux-x64.zip

The installation: if something goes wrong, Varians-Synchro can check its own
translations, help, resources, the sample project, a synchronisation with
its exports to Varians, and its window, and write a report (a few seconds):
  Windows (command prompt, in the Varians-Synchro folder):
     start /wait Varians-Synchro.exe --self-test report.json
  macOS:
     /Applications/Varians-Synchro.app/Contents/MacOS/Varians-Synchro --self-test ~/report.json
  Linux:
     ./Varians-Synchro --self-test report.json
Attach this report to your issue:
  https://github.com/MarjorieBurghart/Varians-Synchro/issues


HELP
----
The guide is inside Varians-Synchro: "Open user guide" button (F1), in the
language chosen at the top of the window ("Language").


COMPONENTS
----------
Varians-Synchro comes with: Python (PSF license); Qt and PySide6 (LGPL v3:
separate libraries, which can be replaced; sources at https://code.qt.io);
certifi (MPL 2.0); on Linux, libraries of the build system (for example
GLib, LGPL v2.1). The texts of these licenses are in the licences folder.
