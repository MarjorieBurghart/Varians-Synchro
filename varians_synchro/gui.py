"""Minimal PySide6 application shell for witness-centered Varians-Synchro.

The historical V0.5 editor and its TXT interface were retired in V0.8.0.
The legacy project *data* are still readable: no project migration discards
older text resources or alignment sessions. The historical algorithm modules
remain in the package for backwards-compatible project introspection.
"""
from __future__ import annotations

import sys
import traceback

from .app_icon import application_icon, use_own_taskbar_entry
from .i18n import available_languages, set_language
from .qt_lifecycle import launch


def main():
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings
    except ImportError as exc:
        print('Varians-Synchro : échec de chargement de PySide6.', file=sys.stderr)
        print(f'Python utilisé : {sys.executable}', file=sys.stderr)
        print(f'Erreur exacte : {type(exc).__name__}: {exc}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print('Exécutez diagnostic_spyder.py avec le même Python.', file=sys.stderr)
        return 2

    lang = QSettings('Varians', 'Varians-Synchro').value('language', 'fr')
    set_language(lang if lang in available_languages() else 'fr')
    from .guided_ui import make_guided_window
    # An unexpected error in a click is shown, not only written to the console.
    from .error_report import install
    install()
    # Windows : la barre des tâches montre le logo, pas l'icône de Python
    # (seulement quand l'application est la nôtre, avant toute fenêtre).
    if QApplication.instance() is None:
        use_own_taskbar_entry()
    return launch(QApplication, make_guided_window(), sys.argv, application_icon)
