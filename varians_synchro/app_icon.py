"""Icône de l'application : le logo de Varians-Synchro.

Les images de ``icons/`` (à côté de ``run.py``) sont produites à partir du
logo (``logo/*.psd``) par ``tools/generate_icons.py``. Ce module ne charge
PySide6 qu'à l'appel d'``application_icon`` : il s'importe sans Qt.
"""
from __future__ import annotations

import sys
from pathlib import Path

ICON_DIR = Path(__file__).resolve().parent.parent / 'icons'
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
APP_USER_MODEL_ID = 'Varians.VariansSynchro'


def icon_files():
    """Un PNG carré par taille de ``ICON_SIZES``, du plus petit au plus grand."""
    return [ICON_DIR / f'varians_synchro_{size}.png' for size in ICON_SIZES]


def application_icon():
    """L'icône Qt, toutes tailles comprises : Qt prend la mieux adaptée
    (barre de titre, barre des tâches, Dock, écrans haute densité)."""
    from PySide6.QtGui import QIcon
    icon = QIcon()
    for path in icon_files():
        if path.is_file():
            icon.addFile(str(path))
    return icon


def use_own_taskbar_entry(platform=None, windll=None):
    """Sous Windows, donne au processus l'identité de Varians-Synchro : la
    barre des tâches montre alors l'icône de la fenêtre, et non celle de
    ``python.exe`` sous laquelle elle rangerait la fenêtre. À appeler avant
    d'afficher la première fenêtre. Vrai si l'identité a été prise."""
    if (sys.platform if platform is None else platform) != 'win32':
        return False
    try:
        if windll is None:
            import ctypes
            windll = ctypes.windll
        return windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID) == 0
    except (AttributeError, OSError):
        return False
