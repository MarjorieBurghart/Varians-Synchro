"""V0.7.2.2: page-order UI core and documentary identity regressions."""
from __future__ import annotations

import ast
import json
import pytest

from varians_synchro.core import (new_project, create_witness, add_image_source,
                                 save_project, load_project)
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.page_management import (page_ids_in_reading_order,
    commit_page_order, invert_page_order, move_page_by_id)
from varians_synchro.project_state import ProjectChangeTracker
from varians_synchro.i18n import set_language, tr
from varians_synchro.reading_stream import reading_stream


def _fixture():
    project = new_project('Pages inversées')
    witness = create_witness(project, 'Test')
    for name in ['z_random.png','m_random.png','a_random.png']:
        add_image_source(witness, 'local', '/images/' + name)
    pages = create_pages(witness)
    for idx, page in enumerate(pages):
        source = {'id': 'PAGE-' + str(idx), 'kind': 'page',
                  'path': '/page_xml/' + page['label'] + '.xml',
                  'pages': [{'width': '900', 'height': '1200', 'lines': [
                      {'alto_id': 'id_' + str(idx), 'text': '', 'region_id': 'main',
                       'bbox': {'HPOS': '0', 'VPOS': '0', 'WIDTH': '100', 'HEIGHT': '30'}}]}]}
        witness['alto_sources'].append(source)
        bind_alto(witness, page['id'], source['id'])
    return project, witness


def _identities(witness):
    return {p['id']: (p.get('image_path'), json.dumps(p.get('alto_binding'), sort_keys=True),
                      json.dumps(p.get('reading_line_order'), sort_keys=True))
            for p in witness['pages']}


def test_reverse_random_names_does_not_change_image_or_page_xml(tmp_path):
    project, witness = _fixture()
    baseline = _identities(witness)
    old = page_ids_in_reading_order(witness)
    assert invert_page_order(witness) == list(reversed(old))
    assert _identities(witness) == baseline
    expected = [
        (page['id'], next(source for source in witness['alto_sources']
                          if source['id'] == page['alto_binding']['source_id'])
                      ['pages'][0]['lines'][0]['alto_id'])
        for page in sorted(witness['pages'], key=lambda page: page['reading_order'])]
    assert [(line['page_id'], line['alto_id']) for line in reading_stream(witness)] == expected
    path = tmp_path/'pages.vsynch'
    save_project(project, path)
    loaded = load_project(path)
    assert page_ids_in_reading_order(loaded['witnesses'][0]) == list(reversed(old))
    assert _identities(loaded['witnesses'][0]) == baseline


def test_dragged_order_transactional_and_complete():
    _, witness = _fixture()
    before = page_ids_in_reading_order(witness)
    moved = [before[1], before[2], before[0]]
    assert commit_page_order(witness, moved) == moved
    assert page_ids_in_reading_order(witness) == moved
    identities = _identities(witness)
    with pytest.raises(ValueError):
        commit_page_order(witness, [before[0], before[0], before[1]])
    with pytest.raises(ValueError):
        commit_page_order(witness, [before[0]])
    assert page_ids_in_reading_order(witness) == moved
    assert _identities(witness) == identities


def test_up_down_uses_page_id_not_sorted_filename():
    _, witness = _fixture()
    original = page_ids_in_reading_order(witness)
    assert move_page_by_id(witness, original[2], -1) == [original[0], original[2], original[1]]
    assert move_page_by_id(witness, original[2], +1) == original
    assert move_page_by_id(witness, original[0], -1) == original
    with pytest.raises(ValueError):
        move_page_by_id(witness, 'no-such-page', -1)


def test_unsaved_tracker_marks_reorder_and_reverts():
    project, witness = _fixture()
    tracker = ProjectChangeTracker(project)
    assert not tracker.is_modified(project)
    invert_page_order(witness)
    assert tracker.is_modified(project)
    tracker.mark_saved(project)
    assert not tracker.is_modified(project)
    move_page_by_id(witness, page_ids_in_reading_order(witness)[0], 1)
    assert tracker.is_modified(project)


def test_ui_exposes_order_actions_and_stable_ids():
    from ui_source import ui_class
    ui, pages, _path = ui_class('PagesDialog')
    methods = {item.name for item in pages.body if isinstance(item, ast.FunctionDef)}
    assert {'update_list','_on_rows_moved','_commit_displayed_order','move_selected','reverse_order',
            '_load_visible_thumbnails','_remote_thumbnail_finished','selected'}.issubset(methods)
    assert 'QAbstractItemView.DragDropMode.InternalMove' in ui
    assert 'Qt.ItemDataRole.UserRole' in ui
    assert 'QImageReader' in ui
    assert 'pageReverseOrder' in ui


def test_ui_translations_reversible():
    try:
        for lang in ('fr', 'en'):
            set_language(lang)
            for key in ('pages.order.tab_help','pages.order.open','pages.order.help',
                        'pages.order.heading','pages.order.up','pages.order.down',
                        'pages.order.reverse','pages.order.binding_independent',
                        'pages.image.iiif','pages.order.error', 'navigation.pages'):
                assert tr(key) and tr(key) != key
            assert '3' in tr('pages.order.status', assigned=3, total=5)
            assert '40' in tr('pages.binding.assigned', count=40, htr=30)
    finally:
        set_language('fr')


def test_newly_imported_images_do_not_reset_an_existing_manual_order():
    project, witness = _fixture()
    original = page_ids_in_reading_order(witness)
    invert_page_order(witness)
    add_image_source(witness, 'local', '/images/b_random.png')
    create_pages(witness)
    reordered = page_ids_in_reading_order(witness)
    assert reordered[:3] == list(reversed(original))
    assert len(reordered) == 4
    assert len(set(reordered)) == 4
