"""Fiche du témoin et paires (red team D4, D13).

- D4 : les associations faites avec « Associer automatiquement… » dans la
  fiche d'un nouveau témoin étaient perdues si l'on touchait ensuite à la
  description, à la case pivot ou ajoutait une image : la fiche reconstruit
  son brouillon à partir du projet. Elles sont désormais refaites.
- D13a : « Réessayer » après avoir marqué « − » un Manifest indisponible
  levait une KeyError.
- D13b : la confirmation des associations « par ordre » comptait aussi les
  lignes que l'on avait changées à la main.
- D13c : décocher la case pivot dans la fiche du pivot était sans effet, sans
  rien dire ; la case est désactivée, avec une infobulle.
- D13d : ouvrir puis fermer une paire sans rien y faire créait une session
  vide et marquait le projet modifié.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets
from varians_synchro.core import add_alto_source, add_image_source, create_witness, new_project
from varians_synchro.i18n import tr
from varians_synchro.ui_widgets import QMessageBox

YES, NO = ui_widgets.QtMessageBox.StandardButton.Yes, ui_widgets.QtMessageBox.StandardButton.No
PAGE = ('<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
        '<Page imageFilename="{image}" imageWidth="500" imageHeight="800">'
        '<TextRegion id="r"><Coords points="1,1 490,1 490,700 1,700"/>{lines}</TextRegion></Page></PcGts>')


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def messages(monkeypatch):
    shown = []
    for kind in ('information', 'warning', 'critical'):
        monkeypatch.setattr(QMessageBox, kind, staticmethod(
            lambda parent, title, text, *a, _kind=kind, **k: shown.append((_kind, text))))
    monkeypatch.setattr(QMessageBox, 'question', staticmethod(
        lambda parent, title, text, *a, **k: shown.append(('question', text)) or YES))
    return shown


def _free(*widgets):
    for widget in widgets:
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _files(folder, sigil, pages):
    images, xmls = [], []
    for n in range(1, pages + 1):
        image = QImage(20, 30, QImage.Format.Format_RGB32)
        image.fill(QColor(240, 230, 210))
        image_path = folder / f'{sigil}_f{n}.png'
        image.save(str(image_path), 'PNG')
        lines = ''.join(f'<TextLine id="{sigil}{n}_{j}"><Coords points="10,{j * 30 + 1} 400,{j * 30 + 1} '
                        f'400,{j * 30 + 20} 10,{j * 30 + 20}"/><TextEquiv><Unicode>{sigil} {n} {j}'
                        '</Unicode></TextEquiv></TextLine>' for j in range(2))
        xml_path = folder / f'{sigil}_f{n}.xml'
        xml_path.write_text(PAGE.format(image=image_path.name, lines=lines), encoding='utf-8')
        images.append(str(image_path))
        xmls.append(str(xml_path))
    return images, xmls


def _bound(project, wid):
    witness = next(w for w in project['witnesses'] if w['id'] == wid)
    return sum(bool(p.get('alto_binding')) for p in witness['pages']), len(witness['pages'])


@pytest.mark.parametrize('change', ['nothing', 'label', 'pivot', 'image'])
def test_bindings_made_in_the_card_survive_later_edits(app, tmp_path, monkeypatch, messages, change):
    from varians_synchro import ui_batch_binding
    from varians_synchro.ui_resources import WitnessResourceDialog
    monkeypatch.setattr(ui_batch_binding.BatchBindingDialog, '_load_visible_thumbnails', lambda self, *a: None)
    monkeypatch.setattr(ui_batch_binding.BatchBindingDialog, 'exec', lambda self: self.commit() or self.result())
    project = new_project('Essai')
    create_witness(project, 'A')
    images, xmls = _files(tmp_path, 'C', 4)
    dialog = WitnessResourceDialog(project)
    try:
        dialog.sigil.setText('C')
        dialog._add('images', images)
        dialog._add('xml_files', xmls)
        dialog.preview_bindings()                          # « Appliquer les associations »
        assert _bound(dialog.stage_current(), 'C') == (4, 4)
        if change == 'label':
            dialog.label_edit.setText('Paris, BnF, lat. 1234')
        elif change == 'pivot':
            dialog.pivot.setChecked(not dialog.pivot.isChecked())
        elif change == 'image':
            dialog._add('images', _files(tmp_path, 'D', 1)[0])
        dialog.commit()
        assert _bound(project, 'C') == (4, 5 if change == 'image' else 4)
        assert not [m for m in messages if m[0] == 'warning']
    finally:
        _free(dialog)


def test_a_binding_is_not_replayed_once_its_xml_is_withdrawn(app, tmp_path, monkeypatch, messages):
    from varians_synchro import ui_batch_binding
    from varians_synchro.ui_resources import WitnessResourceDialog
    monkeypatch.setattr(ui_batch_binding.BatchBindingDialog, '_load_visible_thumbnails', lambda self, *a: None)
    monkeypatch.setattr(ui_batch_binding.BatchBindingDialog, 'exec', lambda self: self.commit() or self.result())
    project = new_project('Essai')
    images, xmls = _files(tmp_path, 'C', 2)
    dialog = WitnessResourceDialog(project)
    try:
        dialog.sigil.setText('C')
        dialog._add('images', images)
        dialog._add('xml_files', xmls)
        dialog.preview_bindings()
        dialog.pending['xml_files'].remove(xmls[1])           # « Supprimer » le second XML
        dialog.staged_project = None
        dialog.commit()
        assert _bound(project, 'C') == (1, 2)
    finally:
        _free(dialog)


def test_retry_after_marking_an_unavailable_manifest_for_removal(app, monkeypatch, messages):
    from varians_synchro import resource_workflow
    from varians_synchro.ui_resources import WitnessResourceDialog
    project = new_project('Essai')
    create_witness(project, 'A')
    witness = create_witness(project, 'B')
    source = add_image_source(witness, 'iiif', 'https://example.org/iiif/B/manifest')
    source['status'], source['error'] = 'unavailable', 'timeout'
    monkeypatch.setattr(resource_workflow, 'inspect_manifest', lambda url: {'canvases': [
        {'id': f'https://example.org/c{i}', 'label': f'f{i}', 'image_service': 'https://example.org/s'}
        for i in (1, 2)]})
    dialog = WitnessResourceDialog(project, witness)
    try:
        assert dialog.retry_button.isEnabled()
        manifests = dialog.lists['manifests']
        manifests.setCurrentRow(0)
        dialog.remove_pending('manifests')                     # marqué « − »
        assert not dialog.retry_button.isEnabled()
        dialog.retry_manifests()                               # le bouton cliqué malgré tout
        assert messages[-1] == ('information', tr('resources.witness.retry_none'))
        manifests.setCurrentRow(0)
        dialog.remove_pending('manifests')                     # de nouveau gardé
        assert dialog.retry_button.isEnabled()
    finally:
        _free(dialog)


def test_ordinal_confirmation_counts_only_rows_left_as_proposed(app, tmp_path, monkeypatch, messages):
    from varians_synchro import ui_batch_binding
    from varians_synchro.imaging import create_pages
    monkeypatch.setattr(ui_batch_binding.BatchBindingDialog, '_load_visible_thumbnails', lambda self, *a: None)
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    for n in range(1, 4):
        image = tmp_path / f'img{n}.png'
        image.write_bytes(b'x')
        add_image_source(witness, 'local', str(image))
    for xml in _files(tmp_path, 'autre', 3)[1]:
        add_alto_source(witness, xml)
    create_pages(witness)
    dialog = ui_batch_binding.BatchBindingDialog(witness)
    try:
        ordinal = [r for r in dialog.plan['rows'] if r['method'] == 'ordinal']
        assert len(ordinal) == 3
        first, second = (dialog.choices[r['page_id']] for r in ordinal[:2])
        a, b = first.currentIndex(), second.currentIndex()
        first.setCurrentIndex(b)                               # échangés à la main
        second.setCurrentIndex(a)
        dialog.commit()
        assert ('question', tr('resources.binding.ordinal_confirm', count=1)) in messages
    finally:
        _free(dialog)


def test_the_pivot_box_cannot_be_unchecked_in_the_pivot_card(app):
    from varians_synchro.ui_resources import WitnessResourceDialog
    project = new_project('Essai')
    pivot = create_witness(project, 'A')
    other = create_witness(project, 'B')
    project['pivot_witness_id'] = 'A'
    card = WitnessResourceDialog(project, pivot)
    other_card = WitnessResourceDialog(project, other)
    try:
        assert card.pivot.isChecked() and not card.pivot.isEnabled()
        assert card.pivot.toolTip() == tr('resources.witness.pivot_kept.tip')
        assert other_card.pivot.isEnabled() and not other_card.pivot.isChecked()
    finally:
        _free(card, other_card)


def test_an_untouched_new_witness_card_closes_without_question(app):
    from varians_synchro.ui_resources import WitnessResourceDialog
    card = WitnessResourceDialog(new_project('Essai'))     # pas encore de pivot : case pré-cochée
    try:
        assert card.pivot.isChecked() and not card.has_unsaved_draft()
        card.sigil.setText('C')
        assert card.has_unsaved_draft()                # un sigle saisi est un brouillon
    finally:
        _free(card)


def _pair_project(tmp_path):
    from varians_synchro.imaging import bind_alto, create_pages
    project = new_project('Essai')
    for wid in ('A', 'B'):
        witness = create_witness(project, wid)
        images, xmls = _files(tmp_path, wid, 1)
        add_image_source(witness, 'local', images[0])
        add_alto_source(witness, xmls[0])
        create_pages(witness)
        bind_alto(witness, witness['pages'][0]['id'], witness['alto_sources'][0]['id'], 0)
    project['pivot_witness_id'] = 'A'
    return project


@pytest.mark.parametrize('linked', [False, True])
def test_a_new_pair_left_empty_is_not_kept(app, tmp_path, monkeypatch, messages, linked):
    from varians_synchro import ui_main_window
    from varians_synchro.physical_alignment import add_pair_link, pair_indices
    from varians_synchro.project_state import ProjectChangeTracker

    class FakePairDialog:
        def __init__(self, project, session, parent):
            if linked:
                left, right = pair_indices(project, session)
                add_pair_link(project, session, list(left)[:1], list(right)[:1])

    monkeypatch.setattr(ui_main_window, 'PairDialog', FakePairDialog)
    monkeypatch.setattr(ui_main_window, '_run_modal', lambda dialog: 0)
    window = ui_main_window.GuidedWindow()
    try:
        window.project = _pair_project(tmp_path)
        window._changes = ProjectChangeTracker(window.project)
        window.refresh()
        window._open_pair('A', 'B')
        assert len(window.project['pair_sessions']) == (1 if linked else 0)
        assert window._changes.is_modified(window.project) == linked
        assert not messages
    finally:
        window._suppress_close_confirmation = True
        window.close()
        _free(window)
