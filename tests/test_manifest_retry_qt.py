"""Fiche du témoin : un Manifest IIIF indisponible est signalé, et
« Réessayer » l'interroge de nouveau. Le résultat est annoncé ; rien n'est
enregistré dans le projet avant « Enregistrer le témoin »."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QPushButton

from varians_synchro import resource_workflow
from varians_synchro.core import new_project
from varians_synchro.i18n import tr
from varians_synchro.resource_workflow import apply_witness_draft, unavailable_manifests
from varians_synchro.ui_resources import WitnessResourceDialog
from varians_synchro.ui_widgets import QMessageBox
from test_manifest_retry import MANIFEST, URL, offline, online


def _free(dialog):
    """Fermer et libérer la fenêtre : laissée vivante, PySide la détruisait à
    l'arrêt de Python (plantage à la sortie, voir test_detached_threads_qt)."""
    from PySide6.QtCore import QCoreApplication, QEvent
    dialog.close()
    dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def project():
    project = new_project('Essai')
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=offline)
    return project


def _dialog(project):
    witness = next(w for w in project['witnesses'] if w['id'] == 'F')
    return WitnessResourceDialog(project, witness), witness


def _texts(dialog):
    lst = dialog.lists['manifests']
    return [lst.item(i).text() for i in range(lst.count())]


def _retry_button(dialog):
    return next(b for b in dialog.findChildren(QPushButton) if b.objectName() == 'retryManifestsButton')


def test_an_unavailable_manifest_is_marked_in_the_witness_card(app, project):
    dialog, _witness = _dialog(project)
    try:
        assert _texts(dialog) == [f"⚠  {URL} — {tr('resources.witness.manifest_unavailable')}"]
        assert _retry_button(dialog).isEnabled()
    finally:
        _free(dialog)


def test_retrying_announces_the_result_and_saving_keeps_it(app, project, monkeypatch):
    monkeypatch.setattr(resource_workflow, 'inspect_manifest', online)
    told = []
    monkeypatch.setattr(QMessageBox, 'information',
                        staticmethod(lambda parent, title, text, *a, **k: told.append(text)))
    dialog, witness = _dialog(project)
    try:
        _retry_button(dialog).click()
        assert told == [tr('resources.witness.retry_loaded', url=URL, pages=len(MANIFEST['canvases']))]
        assert unavailable_manifests(witness) == [URL]          # pas encore enregistré
        assert _texts(dialog) == [f'↻  {URL}']
        dialog.commit()
    finally:
        _free(dialog)
    witness = next(w for w in project['witnesses'] if w['id'] == 'F')
    assert unavailable_manifests(witness) == []
    assert len(witness['pages']) == 2


def test_a_manifest_still_unavailable_is_said_so(app, project, monkeypatch):
    monkeypatch.setattr(resource_workflow, 'inspect_manifest', offline)
    told = []
    monkeypatch.setattr(QMessageBox, 'information',
                        staticmethod(lambda parent, title, text, *a, **k: told.append(text)))
    dialog, _witness = _dialog(project)
    try:
        _retry_button(dialog).click()
    finally:
        _free(dialog)
    assert told == [tr('resources.witness.retry_failed', url=URL, error='hors ligne')]


def test_without_unavailable_manifest_the_button_is_disabled(app):
    project = new_project('Essai')
    apply_witness_draft(project, identifier='F', manifests=[URL], manifest_loader=online)
    dialog, _witness = _dialog(project)
    try:
        assert _texts(dialog) == [f'✓  {URL}']
        assert not _retry_button(dialog).isEnabled()
    finally:
        _free(dialog)


def test_a_manifest_is_fetched_off_the_interface_thread(app, project, monkeypatch):
    """Red team B4 : le Manifest était chargé dans le fil de l'interface ;
    un serveur lent figeait la fenêtre (45 s observées, sans limite). Il est
    chargé dans un fil à part, la fenêtre continue de répondre."""
    import threading
    import time
    from PySide6.QtCore import QTimer
    threads, ticks = [], []

    def slow(url):
        threads.append(threading.current_thread() is threading.main_thread())
        time.sleep(1.0)
        return online(url)
    monkeypatch.setattr(resource_workflow, 'inspect_manifest', slow)
    monkeypatch.setattr(QMessageBox, 'information', staticmethod(lambda *a, **k: None))
    dialog, witness = _dialog(project)
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start(50)
    try:
        dialog.retry_manifests()
    finally:
        timer.stop()
        _free(dialog)
    assert threads == [False]
    assert len(ticks) >= 5                     # l'interface a continué de tourner
