"""Fils détachés (``ui_widgets.start_detached``) : une fois le fil fini, rien
ne reste relié à sa fenêtre.

Le signal « destroyed » de la fenêtre restait relié à une fonction Python
(annuler le fil, pourtant fini). Une fenêtre encore vivante à l'arrêt de
Python était alors détruite par PySide pendant que l'interpréteur se
démontait : plantage à la sortie (``QObject::~QObject`` dans
``PySide::destroyQCoreApplication``), une fois sur huit environ à la fin de
la suite de tests.
"""
import os
import threading
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThread
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _settle(app):
    for _ in range(3):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


class _Waiting(QThread):
    """Un téléchargement : il attend qu'on l'annule, ou qu'on le libère."""
    def __init__(self, cancel, release):
        super().__init__()
        self.cancel, self.release = cancel, release

    def run(self):
        while not (self.cancel.is_set() or self.release.is_set()):
            self.cancel.wait(0.01)


def test_a_finished_thread_leaves_nothing_tied_to_its_window(app):
    owner, cancel, release = QObject(), threading.Event(), threading.Event()
    before = len(ui_widgets._DETACHED_THREADS)
    thread = _Waiting(cancel, release)
    ui_widgets.start_detached(thread, owner, cancel)
    release.set()
    assert thread.wait(5000)
    _settle(app)
    assert len(ui_widgets._DETACHED_THREADS) == before
    owner.deleteLater()
    _settle(app)
    assert not cancel.is_set()                 # plus aucun rappel Python


def test_closing_the_window_still_cancels_a_running_thread(app):
    owner, cancel, release = QObject(), threading.Event(), threading.Event()
    thread = _Waiting(cancel, release)
    ui_widgets.start_detached(thread, owner, cancel)
    try:
        owner.deleteLater()
        _settle(app)
        assert cancel.is_set()
        assert thread.wait(5000)
    finally:
        release.set()
        _settle(app)
