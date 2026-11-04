"""Appels différés liés à leur fenêtre.

``QTimer.singleShot(0, fenêtre.méthode)`` appelait la méthode même si la
fenêtre avait été détruite entre-temps (vignettes demandées juste avant la
fermeture, par exemple) : « Internal C++ object already deleted », affiché
comme une erreur imprévue. ``call_soon(fenêtre, fonction)`` est abandonné
avec la fenêtre. (La forme ``singleShot(0, fenêtre, fonction)`` n'existe pas
dans PySide6 6.6, version minimale du projet.)
"""
import os
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from test_stale_links import setting  # noqa: F401  (fixture)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def errors(monkeypatch):
    """Exceptions levées dans la boucle d'événements de Qt."""
    caught = []
    monkeypatch.setattr(sys, 'excepthook', lambda kind, value, trace: caught.append(value))
    return caught


def _destroy(widget):
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_a_deferred_call_runs_while_its_owner_exists(app):
    from varians_synchro.ui_widgets import call_soon
    owner, calls = QWidget(), []
    call_soon(owner, lambda: calls.append('appelé'))
    assert calls == []                                   # pas tout de suite
    QCoreApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert calls == ['appelé']
    assert owner.findChildren(QTimer) == []              # rien ne s'accumule
    _destroy(owner)


def test_a_deferred_call_is_dropped_with_its_owner(app, errors):
    from varians_synchro.ui_widgets import call_soon
    owner, calls = QWidget(), []
    call_soon(owner, lambda: calls.append('appelé'))
    _destroy(owner)
    assert calls == [] and errors == []


def test_the_pages_window_closed_before_its_thumbnails(app, errors, setting):
    from varians_synchro.ui_pages import PagesDialog
    project, a = setting[0], setting[1]
    dialog = PagesDialog(project, a)
    dialog._schedule_thumbnails()
    _destroy(dialog)
    assert errors == []


def test_the_batch_binding_window_closed_before_its_thumbnails(app, errors, setting):
    from varians_synchro.ui_batch_binding import BatchBindingDialog
    witness = setting[1]
    del witness['pages'][0]['alto_binding']
    dialog = BatchBindingDialog(witness)                 # vignettes demandées à l'ouverture
    _destroy(dialog)
    assert errors == []


def test_the_viewer_closed_right_after_showing_the_htr_text(app, errors, setting):
    from varians_synchro.viewer import LineImagePanel
    panel = LineImagePanel(setting[1])
    QCoreApplication.processEvents()
    panel.show_htr.setChecked(True)                      # recentrage différé
    _destroy(panel)
    assert errors == []
