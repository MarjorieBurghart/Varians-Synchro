"""Fenêtre « Liaison TEI » : « Annuler » ne modifie pas le projet.

« Réanalyser le fichier TEI » modifiait aussitôt le projet (l'ancienne
liaison passait en historique), et « Annuler », dont l'infobulle dit
« Fermer sans modifier », ne revenait pas en arrière. La fenêtre travaille
désormais sur un brouillon, reporté dans le projet par « Appliquer »."""
import copy
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QMessageBox

from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.tei_binding import preview_tei_binding, apply_tei_binding
from varians_synchro.ui_tei_binding import TEIPhysicalBindingDialog
from varians_synchro.ui_widgets import QMessageBox as Messages
from test_tei_binding_083 import fixture, tei


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _bound_project(tmp_path):
    project, _witness = fixture(tmp_path)
    store_tei_reference(project, 'Mu', tei(tmp_path, ''.join(f'<lb edRef="#Mu"/>texte {i} ' for i in range(4))))
    resource = project['text_resources'][-1]
    apply_tei_binding(project, 'Mu', resource['id'], preview_tei_binding(project, 'Mu', resource['id']))
    return project, resource['id']


def _dialog(monkeypatch, project):
    for name in ('question',):
        monkeypatch.setattr(Messages, name,
                            staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    monkeypatch.setattr(Messages, 'information', staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(Messages, 'warning', staticmethod(lambda *a, **k: None))
    return TEIPhysicalBindingDialog(project)


def test_cancel_after_reanalysing_leaves_the_project_unchanged(app, monkeypatch, tmp_path):
    project, resource_id = _bound_project(tmp_path)
    before = copy.deepcopy(project)
    dialog = _dialog(monkeypatch, project)
    dialog.resource_box.setCurrentIndex(dialog.resource_box.findData(resource_id))
    dialog.reload_tei_source()
    dialog.reject()
    assert project == before


def test_apply_after_reanalysing_records_it_in_the_project(app, monkeypatch, tmp_path):
    project, resource_id = _bound_project(tmp_path)
    dialog = _dialog(monkeypatch, project)
    dialog._previewed_endpoints = {1, 4}              # extrémités vues sur les images
    dialog.resource_box.setCurrentIndex(dialog.resource_box.findData(resource_id))
    dialog.reload_tei_source()
    dialog.commit()
    resource = next(r for r in project['text_resources'] if r['id'] == resource_id)
    assert resource.get('tei_binding_history')            # l'ancienne liaison, en historique
    assert resource.get('tei_binding')                     # la nouvelle, appliquée
