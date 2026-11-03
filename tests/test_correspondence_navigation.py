"""Read-only reciprocal navigation; no Qt needed."""
import copy
from varians_synchro.correspondence_navigation import build_pair_navigation_index


def session_fixture():
    return {'links': [
        {'id': 'l1', 'reference_ids': ['A1'], 'target_ids': ['B1', 'B2'],
         'kind': 'correspondence', 'state': 'validated', 'origin': 'manual'},
        {'id': 'l2', 'reference_ids': ['A2', 'A3'], 'target_ids': ['B3', 'B4'],
         'kind': 'correspondence', 'state': 'uncertain', 'origin': 'interpolated-geometry'},
        {'id': 'l3', 'reference_ids': ['A4'], 'target_ids': [],
         'kind': 'absence', 'state': 'validated', 'origin': 'manual'},
        {'id': 'l4', 'reference_ids': [], 'target_ids': ['B5'],
         'kind': 'absence', 'state': 'validated', 'origin': 'manual'},
    ]}


def test_many_to_many_is_reciprocal_and_keeps_order():
    a, b = build_pair_navigation_index(session_fixture())
    assert a['A1']['counterpart_ids'] == ['B1', 'B2']
    assert b['B1']['counterpart_ids'] == ['A1']
    assert b['B2']['counterpart_ids'] == ['A1']
    for uid in ('A2', 'A3'):
        assert a[uid]['counterpart_ids'] == ['B3', 'B4']
    for uid in ('B3', 'B4'):
        assert b[uid]['counterpart_ids'] == ['A2', 'A3']
    assert a['A2']['state'] == 'uncertain'
    assert a['A2']['origin'] == 'interpolated-geometry'


def test_absence_has_no_fabricated_correspondence():
    a, b = build_pair_navigation_index(session_fixture())
    assert a['A4']['kind'] == 'absence'
    assert a['A4']['counterpart_ids'] == []
    assert b['B5']['kind'] == 'absence'
    assert b['B5']['counterpart_ids'] == []
    assert 'A5' not in a
    assert 'B6' not in b


def test_navigation_never_mutates_saved_session():
    s = session_fixture()
    before = copy.deepcopy(s)
    indices = build_pair_navigation_index(s)
    indices[0]['A1']['counterpart_ids'].append('temporary-preview-only')
    assert s == before


def test_indices_rebuild_after_link_removal_or_review():
    s = session_fixture()
    assert 'A2' in build_pair_navigation_index(s)[0]
    s['links'] = [link for link in s['links'] if link['id'] != 'l2']
    assert 'A2' not in build_pair_navigation_index(s)[0]
    s['links'][0]['state'] = 'uncertain'
    assert build_pair_navigation_index(s)[1]['B2']['state'] == 'uncertain'


def test_legacy_missing_origin_or_empty_session():
    a, b = build_pair_navigation_index({'links': [
        {'reference_ids': ['A'], 'target_ids': ['B'], 'kind': 'correspondence'}
    ]})
    assert a['A']['origin'] == 'manual'
    assert b['B']['counterpart_ids'] == ['A']
    assert build_pair_navigation_index({}) == ({}, {})


def test_preview_aggregates_selected_correspondences_and_replaces_old():
    from varians_synchro.correspondence_navigation import combined_counterparts
    refs, _ = build_pair_navigation_index(session_fixture())
    assert combined_counterparts(refs, ['A1']) == (['B1', 'B2'], False)
    assert combined_counterparts(refs, ['A1', 'A3'], clicked='A3') == (
        ['B3', 'B4', 'B1', 'B2'], False)
    # After plain click, the policy has removed A1: no lingering B1/B2.
    assert combined_counterparts(refs, ['A3'], clicked='A3') == (['B3', 'B4'], False)
    assert combined_counterparts(refs, []) == ([], False)
    assert combined_counterparts(refs, ['A4']) == ([], True)
