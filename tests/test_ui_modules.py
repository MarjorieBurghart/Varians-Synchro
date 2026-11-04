"""L'interface est répartie en modules ``ui_*`` : chaque fenêtre s'importe
directement, sans passer par la fabrique ``make_guided_window``."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_guided_ui_loads_without_pyside6():
    """Le moteur et ses tests tournent sans PySide6 : le point d'entrée de
    l'interface ne charge Qt qu'à la création de la fenêtre."""
    code = 'import sys, varians_synchro.guided_ui; print("PySide6" in sys.modules)'
    done = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == 'False'


@pytest.fixture(scope='module')
def app():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_the_widgets_translate_their_texts(app):
    from varians_synchro.i18n import tr
    from varians_synchro.ui_widgets import QLabel, QPushButton, QDialog
    key = 'ui.pages.htr.group'
    assert tr(key) != key
    assert QLabel(key).text() == tr(key)
    assert QPushButton(key).text() == tr(key)
    dialog = QDialog()
    dialog.setWindowTitle(key)
    assert dialog.windowTitle() == tr(key)
