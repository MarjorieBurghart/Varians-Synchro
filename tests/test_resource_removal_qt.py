"""Fiche du témoin : retirer une ressource enregistrée, ou le témoin.

- « Supprimer » sur une ressource déjà enregistrée demande confirmation en
  disant ce que le retrait entraîne (pages, lignes, groupes, dont validés) ;
  la ressource est alors marquée « − » et retirée à « Enregistrer le
  témoin » ; « Annuler » ne change rien.
- « Retirer le témoin… » retire le témoin, ses synchronisations et ses
  éditions TEI, après confirmation ; refusé pour le pivot.
"""
import os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from varians_synchro.i18n import tr
from varians_synchro.physical_alignment import physical_lines, stale_link_ids
from varians_synchro.ui_resources import WitnessResourceDialog
from varians_synchro.ui_widgets import QMessageBox
from test_stale_links import setting  # noqa: F401  (fixture)

YES, NO = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def freed_dialogs(monkeypatch):
    """Chaque fiche ouverte par un test est détruite à la fin du test, tant que
    Python tourne encore (et non à la sortie de l'interpréteur)."""
    opened = []
    original = WitnessResourceDialog.__init__

    def init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        opened.append(self)
    monkeypatch.setattr(WitnessResourceDialog, '__init__', init)
    yield
    for dialog in opened:
        dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture(autouse=True)
def no_blocking_boxes(monkeypatch):
    """Une boîte d'information non attendue ne doit pas bloquer le test."""
    shown = []
    for name in ('information', 'warning', 'critical'):
        monkeypatch.setattr(QMessageBox, name,
                            staticmethod(lambda parent, title, text, *a, **k: shown.append(text)))
    return shown


def _answer(monkeypatch, answer):
    asked = []
    monkeypatch.setattr(QMessageBox, 'question',
                        staticmethod(lambda parent, title, text, *a, **k: asked.append(text) or answer))
    return asked


def _select(dialog, category, name):
    lst = dialog.lists[category]
    row = next(i for i in range(lst.count()) if lst.item(i).text().endswith(name))
    lst.setCurrentRow(row)
    return row


def _button(dialog, name):
    return next(b for b in dialog.findChildren(QPushButton) if b.objectName() == name)


def test_removing_a_saved_xml_file_says_what_it_entails_then_applies_on_save(app, monkeypatch, setting):
    project, a, _b, session, first, last = setting
    name = Path(a['alto_sources'][0]['path']).name
    asked = _answer(monkeypatch, YES)
    dialog = WitnessResourceDialog(project, a)
    try:
        row = _select(dialog, 'xml_files', name)
        dialog.remove_pending('xml_files')
        assert asked == [tr('resources.witness.remove_confirm', name=name, pages=1,
                            lines=len(physical_lines(a)), groups=2, validated=2)]
        assert dialog.lists['xml_files'].item(row).text().startswith('−  ')
        assert len(a['alto_sources']) == 2                      # rien avant l'enregistrement
        dialog.commit()
    finally:
        dialog.close()
    witness = next(w for w in project['witnesses'] if w['id'] == 'A')
    assert name not in [Path(s['path']).name for s in witness['alto_sources']]
    assert stale_link_ids(project, project['pair_sessions'][0]) == {first['id'], last['id']}


def test_declining_keeps_the_resource(app, monkeypatch, setting):
    project, a, *_ = setting
    name = Path(a['alto_sources'][0]['path']).name
    _answer(monkeypatch, NO)
    dialog = WitnessResourceDialog(project, a)
    try:
        row = _select(dialog, 'xml_files', name)
        dialog.remove_pending('xml_files')
        assert dialog.lists['xml_files'].item(row).text().startswith('✓  ')
    finally:
        dialog.close()


def test_a_marked_removal_can_be_undone_before_saving(app, monkeypatch, setting):
    project, a, *_ = setting
    name = Path(a['alto_sources'][0]['path']).name
    _answer(monkeypatch, YES)
    dialog = WitnessResourceDialog(project, a)
    try:
        row = _select(dialog, 'xml_files', name)
        dialog.remove_pending('xml_files')
        dialog.lists['xml_files'].setCurrentRow(row)
        dialog.remove_pending('xml_files')                     # de nouveau : on le garde
        assert dialog.lists['xml_files'].item(row).text().startswith('✓  ')
        dialog.commit()
    finally:
        dialog.close()
    assert len(next(w for w in project['witnesses'] if w['id'] == 'A')['alto_sources']) == 2


def test_removing_the_witness(app, monkeypatch, setting):
    project, _a, b, *_ = setting
    project['pivot_witness_id'] = 'A'
    asked = _answer(monkeypatch, YES)
    dialog = WitnessResourceDialog(project, b)
    try:
        _button(dialog, 'removeWitnessButton').click()
        assert asked == [tr('resources.witness.remove_witness_confirm', witness='B', sessions=1,
                            groups=2, validated=2)]
        assert dialog.result() == QDialog.DialogCode.Accepted
    finally:
        dialog.close()
    assert [w['id'] for w in project['witnesses']] == ['A'] and project['pair_sessions'] == []


def test_the_pivot_witness_cannot_be_removed(app, monkeypatch, setting, no_blocking_boxes):
    project, a, *_ = setting
    project['pivot_witness_id'] = 'A'
    _answer(monkeypatch, YES)
    warned = no_blocking_boxes
    dialog = WitnessResourceDialog(project, a)
    try:
        _button(dialog, 'removeWitnessButton').click()
    finally:
        dialog.close()
    assert warned == [tr('Le témoin pivot ne peut pas être retiré : choisissez d’abord un autre témoin comme pivot.')]
    assert [w['id'] for w in project['witnesses']] == ['A', 'B']


def test_a_new_witness_has_no_remove_button(app):
    from varians_synchro.core import new_project
    dialog = WitnessResourceDialog(new_project('Essai'))
    try:
        assert not [b for b in dialog.findChildren(QPushButton) if b.objectName() == 'removeWitnessButton']
    finally:
        dialog.close()
