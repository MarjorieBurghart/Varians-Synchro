"""Regression for screenshot report: 3 usable columns but no new suggestions.

V0.6.7 treated old geometric suggestions as barriers, preventing a
whole-column recomputation even though the manual end anchors were sound.
"""
from copy import deepcopy
from test_full_column_interpolation import witness_page

from varians_synchro.core import new_project, create_witness
from varians_synchro.interpolation import suggest_between_anchors
from varians_synchro.physical_alignment import (
    create_pair_session, add_pair_link, replace_revisable_pair_proposals,
    physical_lines, pair_progress, is_revisable_automatic,
)


def _setup_three_columns():
    project = new_project()
    a = create_witness(project, 'A')
    b = create_witness(project, 'B')
    la = witness_page(a, 34, columns=3, order='row')
    lb = witness_page(b, 38, columns=3, order='row')
    sess = create_pair_session(project, 'A', 'B')
    manual_ids = []
    for col in range(3):
        for i, j in ((0, 0), (33, 37)):
            manual = add_pair_link(project, sess,
                [la[f'A-c{col}-l{i}']['id']], [lb[f'B-c{col}-l{j}']['id']])
            manual_ids.append(manual['id'])
        # Tentative machine suggestions occupy almost the full column.
        # This is precisely the situation where V0.6.7 proposed nothing.
        for i in range(1, 33):
            add_pair_link(project, sess,
                [la[f'A-c{col}-l{i}']['id']], [lb[f'B-c{col}-l{i}']['id']],
                state='uncertain', origin='interpolated-geometry')
    return project, sess, manual_ids


def test_existing_uncertain_automatic_groups_no_longer_block_full_columns():
    project, session, manual_ids = _setup_three_columns()
    old_ids = {l['id'] for l in session['links']}
    original = deepcopy(session['links'])
    before = suggest_between_anchors(project, session, regenerate_automatic=False)
    assert before['intervals'] == 3
    assert len(before['proposals']) == 0
    after = suggest_between_anchors(project, session, regenerate_automatic=True)
    assert after['intervals'] == 3
    assert len(after['proposals']) > 55
    assert sum(len(p['reference_ids']) for p in after['proposals']) == 96
    assert sum(len(p['target_ids']) for p in after['proposals']) == 108
    assert session['links'] == original   # the preview is read-only
    result = replace_revisable_pair_proposals(project, session, after['proposals'])
    assert result == {'added': len(after['proposals']), 'replaced': 96, 'skipped': 0}
    assert [l['id'] for l in session['links'][:6]] == manual_ids
    assert all(l['id'] in old_ids for l in session['links'][:6])
    assert all(l['state'] == 'uncertain' for l in session['links'][6:])
    assert not any(l['id'] in old_ids for l in session['links'][6:])
    coverage = pair_progress(project, session)
    assert coverage['reference_covered'] == 102
    assert coverage['target_covered'] == 114


def test_manual_uncertain_and_automatic_validated_are_not_replaced():
    project, session, _ = _setup_three_columns()
    old_links = session['links']
    original_manual = old_links[6]
    original_manual['origin'] = 'manual'
    original_validated = old_links[7]
    original_validated['state'] = 'validated'
    saved_ids = (original_manual['id'], original_validated['id'])
    result = suggest_between_anchors(project, session, regenerate_automatic=True)
    assert result['intervals'] >= 3
    ids_a = {uid for p in result['proposals'] for uid in p['reference_ids']}
    assert original_manual['reference_ids'][0] not in ids_a
    assert original_validated['reference_ids'][0] not in ids_a
    replace_revisable_pair_proposals(project, session, result['proposals'])
    assert all(any(link['id'] == id_ for link in session['links']) for id_ in saved_ids)


def test_partially_selected_new_groups_do_not_erase_uncovered_old_links():
    project, session, _ = _setup_three_columns()
    # Include an uncertain 1->2 old group: its target line must be preserved
    # unless the new selected proposals also cover both old target IDs.
    to_remove = next(l for l in session['links']
                     if l.get('origin') == 'interpolated-geometry'
                     and l['reference_ids'][0] in {
                         x['id'] for x in physical_lines(project['witnesses'][0])})
    old_id = to_remove['id']
    after = suggest_between_anchors(project, session, regenerate_automatic=True)
    # Select just a proposal for an unoccupied stretch on another column.
    colA = {x['id']: x['bbox']['HPOS'] for x in physical_lines(project['witnesses'][0])}
    picks = [p for p in after['proposals'] if all(float(colA[uid]) > 1300 for uid in p['reference_ids'])][:3]
    result = replace_revisable_pair_proposals(project, session, picks)
    assert result['added'] >= 0
    assert any(l['id'] == old_id for l in session['links'])


def test_disallows_unvalidated_manual_link_replacement_by_origin():
    assert not is_revisable_automatic({'state':'uncertain', 'origin':'manual','kind':'correspondence'})
    assert not is_revisable_automatic({'state':'validated', 'origin':'interpolated-geometry','kind':'correspondence'})
    assert is_revisable_automatic({'state':'uncertain', 'origin':'automatic-htr-htr','kind':'correspondence'})


def test_incomplete_selection_does_not_discard_multiline_machine_link():
    project, session, _ = _setup_three_columns()
    # Replace two neighbouring 1:1 old proposals with one old 1:2 group,
    # simulating an earlier HTR/geometry segmentation differing from the new run.
    old = session['links'][7]
    neighbour = session['links'][8]
    merged_a = old['reference_ids']
    merged_b = old['target_ids'] + neighbour['target_ids']
    session['links'].remove(old)
    session['links'].remove(neighbour)
    from varians_synchro.physical_alignment import add_pair_link
    merged = add_pair_link(project, session, merged_a, merged_b,
                           state='uncertain', origin='automatic-htr-htr')
    new = suggest_between_anchors(project, session, regenerate_automatic=True)
    # Select the new group covering just one target side of the old 1:2 link.
    picked = [p for p in new['proposals'] if merged['reference_ids'][0] in p['reference_ids']]
    assert picked
    assert not set(merged_b).issubset({x for p in picked for x in p['target_ids']})
    snapshot = deepcopy(session['links'])
    result = replace_revisable_pair_proposals(project, session, picked)
    assert result['replaced'] == 0
    assert result['added'] == 0
    assert session['links'] == snapshot


def test_invalid_candidates_fail_atomically():
    import pytest
    project = new_project()
    a = create_witness(project, 'A')
    b = create_witness(project, 'B')
    la = witness_page(a, 25)
    lb = witness_page(b, 25)
    session = create_pair_session(project, 'A', 'B')
    for i in (0, 24):
        add_pair_link(project, session, [la[f'A-c0-l{i}']['id']], [lb[f'B-c0-l{i}']['id']])
    proposals = suggest_between_anchors(project, session, regenerate_automatic=True)['proposals']
    snapshot = deepcopy(session['links'])
    bad = deepcopy(proposals)
    bad[0]['reference_ids'][0] = 'not-an-existing-physical-line'
    with pytest.raises(ValueError):
        replace_revisable_pair_proposals(project, session, bad)
    assert session['links'] == snapshot
