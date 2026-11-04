"""Clavier : Entrée prudente, « Non » par défaut, brouillon gardé, F1 partout
(red team D2, D6, D9, D10, D12).

- Entrée déclenchait le premier bouton de la fenêtre : dans les pages, une
  page remontait d'un rang (pivot compris) ; dans la synchronisation, un
  groupe manuel validé était créé. Entrée n'active plus aucun bouton par
  défaut ; dans une liste, elle fait comme le double-clic.
- Les questions répondaient « Oui » à Entrée (retrait d'une ressource, du
  témoin, remplacement du XML d'une page) : « Non » par défaut.
- Échap ou la croix jetaient sans rien demander le brouillon d'une fiche ou
  du périmètre : confirmation si le brouillon contient des changements.
- F1 n'ouvrait l'aide que dans la fenêtre principale et la synchronisation.
- La fiche d'un témoin ne s'ouvrait qu'au clic de souris ; ni Ctrl+S, ni
  Ctrl+O, ni Ctrl+N.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets
from varians_synchro.core import create_witness, new_project
from varians_synchro.i18n import tr
from varians_synchro.ui_widgets import QMessageBox

YES, NO = ui_widgets.QtMessageBox.StandardButton.Yes, ui_widgets.QtMessageBox.StandardButton.No


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _free(*widgets):
    for widget in widgets:
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _witness_with_pages(project, wid, count=3):
    witness = create_witness(project, wid)
    for n in range(count):
        source = f'{wid}{n}'
        witness['alto_sources'].append({'id': source, 'path': f'/absent/{source}.xml', 'pages': [
            {'width': '100', 'height': '100', 'line_count': 1, 'lines': [
                {'alto_id': 'l', 'text': f'{wid} {n}', 'bbox': {'HPOS': '1', 'VPOS': '1', 'WIDTH': '50', 'HEIGHT': '9'}}]}]})
        witness['pages'].append({'id': f'{wid}_p{n}', 'label': f'{n}r', 'image_kind': 'local',
                                 'image_path': f'/absent/{n}.jpg', 'reading_order': n,
                                 'alto_binding': {'source_id': source, 'page_index': 0}})
    return witness


def test_enter_in_the_pages_list_shows_the_page_and_moves_nothing(app, monkeypatch):
    from varians_synchro import ui_pages
    project = new_project('Essai')
    witness = _witness_with_pages(project, 'A')
    monkeypatch.setattr(ui_pages, 'create_pages', lambda w: w['pages'])
    monkeypatch.setattr(ui_pages.PagesDialog, '_load_visible_thumbnails', lambda self: None)
    shown = []
    monkeypatch.setattr(ui_pages.PagesDialog, 'preview', lambda self: shown.append(self.selected()[0]['id']))
    dialog = ui_pages.PagesDialog(project, witness)
    try:
        before = [p['id'] for p in witness['pages']]
        dialog.pages.setCurrentRow(1)
        dialog.pages.item(1).setSelected(True)
        QTest.keyClick(dialog.pages, Qt.Key.Key_Return)
        assert sorted(witness['pages'], key=lambda p: p['reading_order']) == \
            sorted(witness['pages'], key=lambda p: before.index(p['id']))
        assert shown == ['A_p1']
    finally:
        _free(dialog)


def test_enter_in_the_groups_list_creates_no_group(app, monkeypatch):
    from varians_synchro.physical_alignment import create_pair_session
    from varians_synchro.ui_pair import PairDialog
    project = new_project('Essai')
    _witness_with_pages(project, 'A', 1)
    _witness_with_pages(project, 'B', 1)
    session = create_pair_session(project, 'A', 'B')
    monkeypatch.setattr(QMessageBox, 'warning', staticmethod(lambda *a, **k: None))
    pair = PairDialog(project, session)
    try:
        pair.left_panel._selected = {pair.left_lines[0]['id']}
        pair.right_panel._selected = {pair.right_lines[0]['id']}
        QTest.keyClick(pair.links, Qt.Key.Key_Return)
        assert session['links'] == []
    finally:
        _free(pair)


def test_questions_answer_no_by_default(app, monkeypatch):
    defaults = []
    monkeypatch.setattr(ui_widgets, '_answer', lambda box: defaults.append(
        box.defaultButton() is box.button(NO)) or NO)
    assert QMessageBox.question(None, 'Titre', 'Retirer ?') == NO
    assert defaults == [True]


def test_escape_asks_before_dropping_a_modified_witness_card(app, monkeypatch):
    from varians_synchro.ui_resources import WitnessResourceDialog
    project = new_project('Essai')
    witness = _witness_with_pages(project, 'A', 1)
    asked = []
    monkeypatch.setattr(QMessageBox, 'question', staticmethod(
        lambda parent, title, text, *a, **k: asked.append(text) or NO))
    dialog = WitnessResourceDialog(project, witness)
    try:
        dialog.show()
        QTest.keyClick(dialog, Qt.Key.Key_Escape)                  # rien de changé : fermée
        assert asked == [] and not dialog.isVisible()
        dialog.show()
        dialog.pending['manifests'].append('https://example.org/m')
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        assert asked == [tr('common.discard_question')] and dialog.isVisible()
    finally:
        dialog.hide()
        _free(dialog)


def test_f1_opens_the_help_from_any_window(app, monkeypatch):
    from varians_synchro import ui_help
    from varians_synchro.ui_resources import WitnessResourceDialog
    opened = []
    monkeypatch.setattr(ui_help, 'open_help', lambda parent, anchor=None: opened.append(parent))
    dialog = WitnessResourceDialog(new_project('Essai'))
    try:
        shortcuts = [s for s in dialog.findChildren(ui_widgets.QShortcut) if s.key() == QKeySequence('F1')]
        assert len(shortcuts) == 1
        shortcuts[0].activated.emit()
        assert opened == [dialog]
    finally:
        _free(dialog)


def test_the_main_window_opens_a_card_with_the_keyboard_and_has_shortcuts(app, monkeypatch):
    from varians_synchro import ui_main_window
    opened = []
    monkeypatch.setattr(ui_main_window.GuidedWindow, 'edit_inventory_item', lambda self, item: opened.append(item))
    window = ui_main_window.GuidedWindow()
    try:
        project = new_project('Essai')
        create_witness(project, 'A')
        window.project = project
        window.refresh()
        window.inventory.itemActivated.emit(window.inventory.topLevelItem(0), 0)
        assert opened
        keys = {s.key().toString() for s in window.findChildren(ui_widgets.QShortcut)}
        assert {QKeySequence(QKeySequence.StandardKey.Save).toString(),
                QKeySequence(QKeySequence.StandardKey.Open).toString(),
                QKeySequence(QKeySequence.StandardKey.New).toString()} <= keys
    finally:
        window._suppress_close_confirmation = True
        window.close()
        _free(window)
