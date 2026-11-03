"""Les fenêtres ouvertes depuis la fenêtre principale sont libérées après
fermeture. Elles restaient enfants de la fenêtre principale avec leurs
images et leurs copies du projet : la mémoire grimpait à chaque ouverture."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QDialog

from varians_synchro.guided_ui import make_guided_window
from test_stale_links import setting  # noqa: F401  (fixture)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_the_alignment_window_is_freed_after_each_opening(app, monkeypatch, setting):
    project = setting[0]
    window = make_guided_window()()
    window.project = project
    window.refresh()
    window.reference_box.setCurrentIndex(window.reference_box.findData('A'))
    window.target_box.setCurrentIndex(window.target_box.findData('B'))
    monkeypatch.setattr(QDialog, 'exec', lambda self: 0)     # fermée aussitôt
    for _ in range(3):
        window.open_physical_alignment()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    assert [type(child).__name__ for child in window.findChildren(QDialog)] == []
    window._suppress_close_confirmation = True
    window.close()
