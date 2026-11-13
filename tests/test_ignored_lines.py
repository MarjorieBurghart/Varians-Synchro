"""Witness-level ALTO exclusions: non-destructive and pair-independent."""
from copy import deepcopy
from pathlib import Path
import tempfile
import pytest

from test_physical_alignment import add_page
from test_full_column_interpolation import witness_page
from varians_synchro.core import new_project, create_witness, save_project, load_project
from varians_synchro.line_scope import ignored_ids, linked_scope_conflicts, update_ignored_lines
from varians_synchro.physical_alignment import (
    physical_lines, create_pair_session, add_pair_link, pair_progress,
    suggest_htr_pair_alignment,
)
from varians_synchro.interpolation import suggest_between_anchors
from varians_synchro.overlay_filters import overlay_visible, FILTER_UNLINKED, FILTER_ALL, FILTER_AUTOMATIC_REVIEW
from varians_synchro.i18n import reload_catalogs, set_language, tr


def make_project():
    project = new_project('Œuvre manuscrite')
    witnesses = [create_witness(project, x) for x in 'ABC']
    for w in witnesses:
        add_page(w, ['other work', 'Beatus Germanus in hac vita', 'claruit multis miraculis', 'finis'])
    return project, witnesses


def test_old_project_needs_no_migration():
    project, (a,b,c) = make_project()
    for w in project['witnesses']:
        w.pop('ignored_line_ids', None)
    assert ignored_ids(a) == set()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'old.vsynch'
        save_project(project, path)
        result = load_project(path)
        assert result['witnesses'][0].get('ignored_line_ids') is None
    update_ignored_lines(project, {'A':[physical_lines(a)[0]['id']]})
    assert len(ignored_ids(a)) == 1


def test_excluding_lines_in_one_witness_affects_all_pairs():
    project, (a,b,c) = make_project()
    ab = create_pair_session(project,'A','B')
    ac = create_pair_session(project,'A','C')
    la = physical_lines(a)
    result = update_ignored_lines(project, {'A':[la[0]['id'],la[1]['id']]})
    assert result['changed'] == 2
    assert pair_progress(project, ab)['reference_ignored'] == 2
    assert pair_progress(project, ac)['reference_ignored'] == 2
    assert pair_progress(project, ab)['reference_total'] == 2
    assert pair_progress(project, ab)['reference_alto_total'] == 4
    assert pair_progress(project, ab)['reference_unresolved'] == 2
    assert pair_progress(project, ab)['target_total'] == 4
    assert ignored_ids(b) == set()
    assert update_ignored_lines(project, {'A':[la[0]['id']]})['changed'] == 0
    assert update_ignored_lines(project, {'A':[la[1]['id']]}, ignored=False)['changed'] == 1


def test_atomic_confirm_remove_links_in_all_pairs():
    project, (a,b,c) = make_project()
    ab = create_pair_session(project,'A','B')
    ac = create_pair_session(project,'A','C')
    la,lb,lc = (physical_lines(w) for w in (a,b,c))
    add_pair_link(project,ab,[la[1]['id']],[lb[1]['id'],lb[2]['id']])
    add_pair_link(project,ac,[la[1]['id']],[lc[1]['id']])
    existing=[deepcopy(ab['links']),deepcopy(ac['links'])]
    changes={'A':[la[1]['id']]}
    assert sum(linked_scope_conflicts(project,changes).values()) == 2
    with pytest.raises(ValueError,match='confirmation'):
        update_ignored_lines(project,changes)
    assert [ab['links'],ac['links']] == existing
    assert not ignored_ids(a)
    result=update_ignored_lines(project,changes,unlink_existing=True)
    assert result == {'changed':1, 'affected_groups':2, 'deleted_groups':2}
    assert ab['links'] == [] and ac['links'] == []
    assert ignored_ids(a)=={la[1]['id']}
    assert len(lb)==4 and len(lc)==4
    with pytest.raises(ValueError,match='ignorées'):
        add_pair_link(project,ab,[la[1]['id']],[lb[1]['id']])
    update_ignored_lines(project,changes,ignored=False)
    add_pair_link(project,ab,[la[1]['id']],[lb[1]['id']])


def test_partial_detach_still_valid_for_other_side():
    project,(a,b,c)=make_project()
    ab=create_pair_session(project,'A','B')
    la,lb=physical_lines(a),physical_lines(b)
    link=add_pair_link(project,ab,[la[0]['id'],la[1]['id']],[lb[1]['id']])
    update_ignored_lines(project,{'A':[la[0]['id']]},unlink_existing=True)
    assert len(ab['links'])==1
    assert link['reference_ids']==[la[0]['id'],la[1]['id']]  # original reference not mutated
    assert ab['links'][0]['reference_ids']==[la[1]['id']]
    assert pair_progress(project,ab)['reference_unresolved']==2


def test_invalid_scope_change_is_atomic():
    project,(a,b,c)=make_project()
    before=deepcopy(project)
    with pytest.raises(ValueError):
        update_ignored_lines(project,{'A':[physical_lines(a)[0]['id']], 'C':['nonexistent']})
    assert project==before


def test_saved_scope_survives_load_and_uses_stable_line_ids():
    project,(a,b,c)=make_project()
    uid=physical_lines(a)[2]['id']
    update_ignored_lines(project,{'A':[uid]})
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'corpus.vsynch'
        save_project(project,path)
        reloaded=load_project(path)
        assert uid in ignored_ids(reloaded['witnesses'][0])
        assert [x['id'] for x in physical_lines(reloaded['witnesses'][0])]==[x['id'] for x in physical_lines(a)]


def test_excluded_lines_are_not_htr_proposals():
    project,(a,b,c)=make_project()
    ab=create_pair_session(project,'A','B')
    a_id=physical_lines(a)[0]['id'];b_id=physical_lines(b)[0]['id']
    update_ignored_lines(project,{'A':[a_id], 'B':[b_id]})
    result=suggest_htr_pair_alignment(project,ab,min_support=.05)
    assert all(a_id not in p['reference_ids'] and b_id not in p['target_ids'] for p in result['proposals'])


def test_geometry_does_not_include_ignored_lines_even_in_column_detection():
    project=new_project()
    a=create_witness(project,'A'); b=create_witness(project,'B')
    la=witness_page(a,18);lb=witness_page(b,18)
    ab=create_pair_session(project,'A','B')
    for i in (0,17):
        add_pair_link(project,ab,[la[f'A-c0-l{i}']['id']],[lb[f'B-c0-l{i}']['id']])
    ignored=[la['A-c0-l6']['id'],la['A-c0-l7']['id']]
    update_ignored_lines(project,{'A': ignored})
    result=suggest_between_anchors(project,ab)
    assert result['intervals']==1, result['warnings']
    ids={x for p in result['proposals'] for x in p['reference_ids']}
    assert not (ids & set(ignored))
    assert len(ids)==14


def test_overlay_ignored_is_not_unlinked_or_auto_review():
    assert overlay_visible('ignored', FILTER_ALL)
    assert not overlay_visible('ignored', FILTER_UNLINKED)
    assert not overlay_visible('ignored', FILTER_AUTOMATIC_REVIEW)
    assert overlay_visible('ignored', FILTER_UNLINKED, selected=True)


def test_new_xml_messages_match_and_are_translated():
    reload_catalogs()
    try:
        set_language('fr')
        assert 'ignor' in tr('scope.ignore').lower()
        set_language('en')
        assert tr('scope.ignore') == 'Ignore selected lines'
        assert '2' in tr('scope.progress',left=2,right=5)
    finally:
        set_language('fr')


def test_legacy_tei_links_cannot_be_silently_invalidated():
    project,(a,b,c)=make_project()
    aid=physical_lines(a)[1]
    project['alignment_sessions']=[{
        'id':'old-tei', 'target_witness_id':'A', 'base_witness_id':'B',
        'links':[{'id':'legacy-link', 'base_keys':['other::1'],
                  'target_refs':[f"{aid['page_id']}::{aid['ordinal']}"],
                  'kind':'correspondence','state':'validated'}]}]
    before=deepcopy(project)
    with pytest.raises(ValueError,match='TEI'):
        update_ignored_lines(project,{'A':[aid['id']]},unlink_existing=True)
    assert project==before
