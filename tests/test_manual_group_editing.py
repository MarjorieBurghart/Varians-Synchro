"""Regression: add an omitted physical line to an existing correspondence.

A user can click a line of an existing 1:1 link and an overlooked line in
another witness. Manual correction must be safe, reversible and self-contained.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import pytest

from test_physical_alignment import add_page
from varians_synchro.core import new_project, create_witness, save_project, load_project
from varians_synchro.physical_alignment import (
    create_pair_session, physical_lines, add_pair_link,
    extend_pair_link, detach_pair_lines, pair_progress, is_revisable_automatic,
    remove_pair_link,
)


def example():
    project = new_project('Médiéval')
    a = create_witness(project, 'A')
    b = create_witness(project, 'B')
    add_page(a, ['start', 'continued', 'finish', 'end'])
    add_page(b, ['start', 'continued', 'more continued', 'finish', 'end'])
    session = create_pair_session(project, 'A', 'B')
    la = [line['id'] for line in physical_lines(a)]
    lb = [line['id'] for line in physical_lines(b)]
    return project, session, la, lb


def test_extend_existing_1_to_1_to_1_to_2_preserves_group_identity():
    project, session, a, b = example()
    anchor = add_pair_link(project, session, [a[1]], [b[1]])
    before_id = anchor['id']
    outcome = extend_pair_link(project, session, [a[1]], [b[2]])
    assert outcome['action'] == 'extended'
    assert len(session['links']) == 1
    assert anchor['id'] == before_id
    assert anchor['reference_ids'] == [a[1]]
    assert anchor['target_ids'] == [b[1], b[2]]
    assert anchor['origin'] == 'manual-correction'
    assert anchor['state'] == 'validated'
    assert pair_progress(project, session)['target_covered'] == 2


def test_extend_second_side_to_2_to_1():
    project, session, a, b = example()
    link = add_pair_link(project, session, [a[0]], [b[0]])
    out = extend_pair_link(project, session, [a[0], a[1]], [b[0]])
    assert out['added_reference'] == 1
    assert out['added_target'] == 0
    assert link['reference_ids'] == [a[0], a[1]]


def test_create_new_group_as_before():
    project, session, a, b = example()
    result = extend_pair_link(project, session, [a[0]], [b[0]])
    assert result['action'] == 'created'
    assert result['link']['state'] == 'validated'


def test_duplicate_extension_noop_not_duplicate_link():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    original = deepcopy(session['links'])
    assert extend_pair_link(project, session, [a[0]], [b[0]])['action'] == 'unchanged'
    assert session['links'] == original


def test_auto_uncertain_after_manual_edit_remains_uncertain_and_is_protected():
    project, session, a, b = example()
    link = add_pair_link(project, session, [a[1]], [b[1]], origin='interpolated-geometry',
                         state='uncertain', confidence=.44,
                         evidence={'anchors': ['x', 'y']})
    outcome = extend_pair_link(project, session, [a[1]], [b[2]])
    assert outcome['action'] == 'extended'
    assert link['state'] == 'uncertain'
    assert link['origin'] == 'manual-correction'
    assert not is_revisable_automatic(link)
    assert 'confidence' not in link
    assert link['evidence']['anchors'] == ['x', 'y']
    assert link['evidence']['manual_corrections'][-1]['target_added'] == [b[2]]


def test_reject_merging_two_existing_groups_atomically():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    add_pair_link(project, session, [a[1]], [b[1]])
    before = deepcopy(session['links'])
    with pytest.raises(ValueError, match='plusieurs groupes'):
        extend_pair_link(project, session, [a[0]], [b[1]])
    assert session['links'] == before


def test_reject_confirmed_absence_without_explicit_unlink():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [], kind='absence')
    before = deepcopy(session['links'])
    with pytest.raises(ValueError, match='absence'):
        extend_pair_link(project, session, [a[0]], [b[0]])
    assert session['links'] == before


def test_reject_unknown_line_atomically():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    before = deepcopy(session['links'])
    with pytest.raises(ValueError, match='absente'):
        extend_pair_link(project, session, [a[0]], ['bad-line-id'])
    assert session['links'] == before


def test_detach_single_target_line_preserves_rest_of_link():
    project, session, a, b = example()
    link = add_pair_link(project, session, [a[1]], [b[1], b[2], b[3]],
                         origin='interpolated-geometry', state='uncertain')
    result = detach_pair_lines(project, session, [], [b[2]])
    assert result == {'affected_groups': 1, 'deleted_groups': 0, 'removed_lines': 1}
    updated = session['links'][0]
    assert updated['id'] == link['id']
    assert updated['target_ids'] == [b[1], b[3]]
    assert updated['origin'] == 'manual-correction'
    assert updated['state'] == 'uncertain'
    assert updated['evidence']['manual_corrections'][-1]['target_removed'] == [b[2]]
    assert pair_progress(project, session)['target_unresolved'] == 3


def test_detach_sole_side_of_link_deletes_group_not_false_absence():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0], b[1]])
    assert detach_pair_lines(project, session, [a[0]], [])['deleted_groups'] == 1
    assert session['links'] == []
    assert pair_progress(project, session)['target_unresolved'] == len(b)


def test_detach_validated_1_to_1_by_clicking_one_line():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    assert detach_pair_lines(project, session, [a[0]], [])['affected_groups'] == 1
    assert session['links'] == []


def test_detach_multiple_groups_by_selecting_image_lines():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    add_pair_link(project, session, [a[1]], [b[1], b[2]])
    result = detach_pair_lines(project, session, [], [b[0], b[2]])
    assert result['affected_groups'] == 2
    assert result['deleted_groups'] == 1
    assert len(session['links']) == 1
    assert session['links'][0]['target_ids'] == [b[1]]


def test_detach_one_member_of_confirmed_absence():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0], a[1]], [], kind='absence')
    result = detach_pair_lines(project, session, [a[1]], [])
    assert result['affected_groups'] == 1
    assert session['links'][0]['kind'] == 'absence'
    assert session['links'][0]['reference_ids'] == [a[0]]


def test_detach_nonlinked_is_noop_and_other_links_untouched():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    old = deepcopy(session['links'])
    assert detach_pair_lines(project, session, [a[3]], [])['affected_groups'] == 0
    assert session['links'] == old


def test_partial_edit_survives_save_load():
    project, session, a, b = example()
    add_pair_link(project, session, [a[1]], [b[1]], origin='interpolated-geometry', state='uncertain')
    extend_pair_link(project, session, [a[1]], [b[2]])
    detach_pair_lines(project, session, [], [b[1]])
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/'working.vsynch'
        save_project(project, path)
        reloaded = load_project(path)
        assert reloaded['pair_sessions'][0]['links'] == session['links']
        assert len(reloaded['pair_sessions'][0]['links'][0]['target_ids']) == 1


def test_undo_extension_by_removing_extra_line():
    project, session, a, b = example()
    add_pair_link(project, session, [a[0]], [b[0]])
    extend_pair_link(project, session, [a[0]], [b[1]])
    detach_pair_lines(project, session, [], [b[1]])
    assert session['links'][0]['target_ids'] == [b[0]]
    assert session['links'][0]['reference_ids'] == [a[0]]


def test_explicit_remove_entire_group_still_works():
    project, session, a, b = example()
    link = add_pair_link(project, session, [a[0]], [b[0]])
    remove_pair_link(session, link['id'])
    assert len(session['links']) == 0
