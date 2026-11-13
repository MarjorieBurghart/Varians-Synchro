"""Le journal des erreurs dans l'interface (voir ``error_log``).

``install_for_application`` l'ouvre au démarrage (``gui.main``), avec les
versions de Varians-Synchro, de PySide6 et de Qt. ``open_log_folder`` ouvre
son dossier dans le gestionnaire de fichiers du système, pour joindre
``varians-synchro.log`` à un signalement : bouton « Journal des erreurs » de
la fenêtre d'aide et de la boîte « Action impossible » (``error_report``).
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from . import error_log
from .i18n import tr


def install_for_application() -> Path | None:
    """Ouvre le journal (une seule fois) ; rend son fichier, ou None s'il ne
    peut pas être écrit (rien ne change alors)."""
    import PySide6
    from PySide6.QtCore import qVersion
    from .core import VERSION
    return error_log.install(f'Varians-Synchro {VERSION} ; PySide6 {PySide6.__version__} ; Qt {qVersion()}')


def log_folder() -> Path:
    """Dossier du journal : celui du fichier ouvert, sinon celui où il le
    serait."""
    path = error_log.journal_path()
    return path.parent if path is not None else error_log.log_dir()


def open_log_folder(parent) -> bool:
    """Ouvre le dossier du journal (créé s'il manque) ; s'il ne peut pas être
    créé, le dit. Rend vrai si le dossier a été ouvert."""
    from .ui_widgets import QMessageBox
    folder = log_folder()
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        QMessageBox.warning(parent, 'error_log.title', tr('error_log.unavailable', folder=str(folder)))
        return False
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
    return True
