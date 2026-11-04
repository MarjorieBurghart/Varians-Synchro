# -*- mode: python ; coding: utf-8 -*-
"""Recette PyInstaller de la version prête à l'emploi de Varians-Synchro
(V0.8.6.0), sur le modèle de celle de Varians.

Lancée par ``packaging/build.py`` (qui construit, vérifie avec
``--self-test`` et zippe) ; à la main :
``python -m PyInstaller --noconfirm packaging/varians_synchro.spec``.

Un dossier (pas un exécutable unique) : démarrage rapide, rien n'est
décompressé à chaque lancement, et les bibliothèques Qt restent des
fichiers distincts (LGPL). Les fichiers de données sont lus à côté du
paquet (``Path(__file__).resolve().parent.parent / 'i18n'``…) : ils sont
placés dans ``_internal/`` (``Contents/Resources`` d'un paquet macOS), sous
le même nom de dossier que dans les sources. Le point d'entrée est
``run.py``, qui reconnaît aussi ``--self-test``."""
import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH).resolve().parent
NAME = "Varians-Synchro"
VERSION = re.search(r"^VERSION = '([^']+)'", (ROOT / "varians_synchro" / "core.py").read_text(encoding="utf-8"),
                    re.MULTILINE).group(1)

# Dossiers de données, copiés tels quels (sans __pycache__) : traductions,
# aide, icônes des fenêtres, et le projet d'exemple que vérifie
# « --self-test » (build.py en pose aussi une copie à côté de l'exécutable,
# pour l'utilisateur). tests/test_packaging.py vérifie que tout dossier lu
# par le code y figure.
DATA_FOLDERS = ("i18n", "help", "icons", "demo_local_ALTO")
# Icône de l'exécutable Windows (.ico, toutes tailles) et du paquet
# Varians-Synchro.app (PNG converti en .icns par PyInstaller, avec Pillow) :
# le logo, comme celui des fenêtres (app_icon.py).
ICON = "icons/varians_synchro.ico" if sys.platform == "win32" else "icons/varians_synchro_256.png"


def _data_files():
    files = []
    for folder in DATA_FOLDERS:
        for path in sorted((ROOT / folder).rglob("*")):
            if (path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".bak")):
                files.append((str(path), str(path.parent.relative_to(ROOT))))
    return files


datas = _data_files() + copy_metadata("certifi")     # licence de certifi

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["certifi"],
    runtime_hooks=[str(Path(SPECPATH) / "rthook_certificates.py")],
    excludes=[
        "tkinter", "_tkinter", "pytest", "_pytest", "pytestqt", "IPython", "matplotlib", "numpy",
        "PySide6.QtTest", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml",
        "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.Qt3DCore", "PySide6.QtMultimedia",
        "PySide6.QtPdf", "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtBluetooth",
        "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtSql", "PySide6.QtXml",
    ],
    noarchive=False,
)


# Greffons Qt inutiles à une application de bureau, et les bibliothèques
# qu'eux seuls emportent : clavier virtuel (QML, Qt Quick), images PDF,
# plateformes embarquées (eglfs, linuxfb, vnc…), entrées evdev, thème GTK et
# la pile GTK de la machine de construction (sous Linux : conflits de
# versions avec celle du système ; Qt garde ses propres boîtes de dialogue).
# Gardés : windows, cocoa, xcb, wayland, offscreen (vérification), formats
# d'images (TIFF, WebP…), TLS (vignettes IIIF par QtNetwork),
# méthodes de saisie (ibus, compose), portails.
UNUSED_QT = re.compile(
    r"plugins/(platforminputcontexts/[^/]*virtualkeyboard|imageformats/[^/]*qpdf|platformthemes/[^/]*gtk3"
    r"|platforms/[^/]*(eglfs|linuxfb|vnc|minimal|vkkhrdisplay)|egldeviceintegrations/|generic/)"
    r"|Qt6?(VirtualKeyboard|Qml|Quick|Pdf|EglFS|EglFsKms)")
UNUSED_LINUX = re.compile(
    r"^lib(gtk-3|gdk-3|atk-1\.0|atk-bridge-2\.0|atspi|gdk_pixbuf-2\.0|cairo-gobject|cairo|pangocairo-1\.0"
    r"|pangoft2-1\.0|pango-1\.0|epoxy|pixman-1|thai|datrie|fribidi|Xcomposite|Xdamage|Xinerama|Xi|Xrandr"
    r"|Xcursor)\.so")


def _wanted(entry):
    name = entry[0].replace("\\", "/")
    if UNUSED_QT.search(name):
        return False
    return not (sys.platform.startswith("linux") and "/" not in name and UNUSED_LINUX.match(name))


# Les liens symboliques vers ces bibliothèques sont rangés avec les données.
a.binaries = [entry for entry in a.binaries if _wanted(entry)]
a.datas = [entry for entry in a.datas if _wanted(entry)]
pyz = PYZ(a.pure)
icon = str(ROOT / ICON)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NAME,
    console=False,                  # application fenêtrée (pas de console sous Windows)
    upx=False,                      # UPX : fausses alertes des antivirus
    strip=False,
    icon=icon,
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False, strip=False)

if sys.platform == "darwin":
    short_version = ".".join(VERSION.split(".")[:3])
    app = BUNDLE(
        coll,
        name=f"{NAME}.app",
        icon=icon,
        bundle_identifier="io.github.marjorieburghart.varians-synchro",
        version=short_version,
        info_plist={
            "CFBundleName": NAME,
            "CFBundleDisplayName": NAME,
            "CFBundleShortVersionString": short_version,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "Varians-Synchro",
        },
    )
