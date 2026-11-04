"""Lignes ignorées et nouvelle segmentation d'une page (red team A1).

Une ligne ignorée n'est connue que par sa page et son rang. Quand la page
recevait un autre fichier ALTO/PAGE, ou que son fichier était retiré, la
marque passait sans avertissement à la ligne qui prenait ce rang : un titre
courant revenait dans le pivot exporté, une vraie ligne de texte en sortait.

Décision : la ligne retrouvée à l'identique dans le nouveau fichier (même
identifiant ALTO, même texte) reste ignorée ; les autres marques sont
retirées, et la confirmation le dit avant."""
from varians_synchro.core import create_witness, new_project
from varians_synchro.imaging import bind_alto
from varians_synchro.physical_alignment import page_links_impact, physical_lines
from varians_synchro.reading_stream import rebind_page
from varians_synchro.resource_removal import removal_impact, remove_resource


def _source(witness, source_id, lines):
    witness['alto_sources'].append({'id': source_id, 'path': f'/absent/{source_id}.xml', 'pages': [
        {'width': '1000', 'height': '1600', 'line_count': len(lines), 'lines': [
            {'alto_id': alto_id, 'text': text,
             'bbox': {'HPOS': '20', 'VPOS': str(40 * rank), 'WIDTH': '500', 'HEIGHT': '30'}}
            for rank, (alto_id, text) in enumerate(lines)]}]})


def _setting():
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    witness['pages'].append({'id': 'p1', 'label': '1r', 'image_kind': 'local', 'image_path': '/absent/1r.jpg',
                             'alto_binding': None})
    _source(witness, 'old', [('t', 'TITRE COURANT'), ('l1', 'alpha 1'), ('l2', 'alpha 2')])
    bind_alto(witness, 'p1', 'old', 0)
    title = physical_lines(witness)[0]
    witness['ignored_line_ids'] = [title['id']]
    return project, witness


def _ignored_texts(witness):
    ignored = set(witness['ignored_line_ids'])
    return [line['text'] for line in physical_lines(witness) if line['id'] in ignored]


def test_the_ignored_line_follows_its_text_to_the_new_segmentation():
    project, witness = _setting()
    _source(witness, 'new', [('n', 'note marginale'), ('t', 'TITRE COURANT'), ('l1', 'alpha 1'), ('l2', 'alpha 2')])
    assert page_links_impact(project, 'A', 'p1', 'new', 0)['ignored_lost'] == 0
    rebind_page(witness, 'p1', 'new', 0)
    assert _ignored_texts(witness) == ['TITRE COURANT']


def test_an_ignored_line_absent_from_the_new_file_is_announced_then_released():
    project, witness = _setting()
    _source(witness, 'new', [('l1', 'alpha 1'), ('l2', 'alpha 2')])
    assert page_links_impact(project, 'A', 'p1', 'new', 0)['ignored_lost'] == 1
    rebind_page(witness, 'p1', 'new', 0)
    assert _ignored_texts(witness) == [] and witness['ignored_line_ids'] == []


def test_the_same_text_with_another_identifier_is_not_the_same_line():
    project, witness = _setting()
    _source(witness, 'new', [('autre', 'TITRE COURANT'), ('l1', 'alpha 1')])
    rebind_page(witness, 'p1', 'new', 0)
    assert witness['ignored_line_ids'] == []


def test_binding_the_same_file_again_keeps_the_marks():
    project, witness = _setting()
    before = list(witness['ignored_line_ids'])
    rebind_page(witness, 'p1', 'old', 0)
    assert witness['ignored_line_ids'] == before


def test_removing_the_file_releases_its_ignored_lines_and_says_so():
    project, witness = _setting()
    assert removal_impact(project, 'A', 'xml', 'old')['ignored'] == 1
    remove_resource(project, 'A', 'xml', 'old')
    witness = project['witnesses'][0]
    assert witness['ignored_line_ids'] == []
    _source(witness, 'new', [('n', 'note marginale'), ('l1', 'alpha 1')])
    bind_alto(witness, 'p1', 'new', 0)
    assert _ignored_texts(witness) == []


def test_a_mark_left_on_an_unbound_page_does_not_land_on_its_next_file():
    project, witness = _setting()
    witness['pages'][0]['alto_binding'] = None            # projet ancien : marque restée en place
    _source(witness, 'new', [('n', 'note marginale'), ('l1', 'alpha 1')])
    bind_alto(witness, 'p1', 'new', 0)
    assert _ignored_texts(witness) == []


def test_the_pages_window_announces_the_released_marks(monkeypatch):
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    import pytest
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from varians_synchro.i18n import tr
    from varians_synchro.ui_pages import PagesDialog
    from varians_synchro.ui_widgets import QInputDialog, QMessageBox
    project, witness = _setting()
    _source(witness, 'new', [('l1', 'alpha 1'), ('l2', 'alpha 2')])
    from varians_synchro import ui_pages
    monkeypatch.setattr(ui_pages, 'create_pages', lambda witness: witness['pages'])   # pas d'images
    monkeypatch.setattr(PagesDialog, '_load_visible_thumbnails', lambda self: None)
    asked = []
    monkeypatch.setattr(QMessageBox, 'question', staticmethod(
        lambda parent, title, text, *a, **k: asked.append(text) or QMessageBox.StandardButton.No))
    dialog = PagesDialog(project, witness)
    try:
        dialog.pages.item(0).setSelected(True)
        labels = []
        monkeypatch.setattr(QInputDialog, 'getItem', staticmethod(
            lambda parent, title, label, items, *a, **k: labels.extend(items) or (items[-1], True)))
        dialog.assign()
    finally:
        dialog.deleteLater()
    assert len(asked) == 1 and tr('ui.xml.replace_ignored', count=1) in asked[0]
    assert len(witness['ignored_line_ids']) == 1               # « Non » : rien n'a changé
