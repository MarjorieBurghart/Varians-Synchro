import pytest
from test_alignment import fixture_project
from varians_synchro.alignment import create_session,add_link
from varians_synchro.review import (configure_session,prepare_proposals,bulk_set_state,
                                    session_progress,project_progress)


def test_policies_keep_rapid_uncertain_and_filter_rigorous():
    candidates=[{'base_keys':['A::1'],'target_refs':['B::1'],'confidence':.25},
                {'base_keys':['A::2'],'target_refs':['B::2'],'confidence':.91}]
    fast=prepare_proposals(candidates,'rapid',.7)
    strict=prepare_proposals(candidates,'rigorous',.7)
    assert [p['state'] for p in fast]==['uncertain','proposed']
    assert len(strict)==1 and strict[0]['confidence']==.91
    assert 'state' not in candidates[0]


def test_bulk_validation_and_progress():
    project,_=fixture_project();s=create_session(project,'tei1','B')
    link=add_link(project,s,['A-p1::1'],['B-p1::1'],state='proposed')
    stats=session_progress(project,s)
    assert stats['links']==1 and stats['base_covered']==1 and stats['base_validated']==0
    assert bulk_set_state(s,[link['id']],'validated')==1
    assert session_progress(project,s)['target_validated']==1
    assert session_progress(project,s)['by_state']['validated']==1
    assert len(project_progress(project))==1
    assert bulk_set_state(s,[link['id']],'uncertain')==1
    assert 'reviewed_at' not in link


def test_bulk_is_atomic_and_settings_persist():
    project,_=fixture_project();s=create_session(project,'tei1','B')
    link=add_link(project,s,['A-p1::1'],['B-p1::1'],state='proposed')
    with pytest.raises(ValueError):
        bulk_set_state(s,[link['id'],'missing'],'validated')
    assert link['state']=='proposed'
    assert configure_session(s,'rapid',.33)=={'mode':'rapid','threshold':.33}
    with pytest.raises(ValueError):configure_session(s,'unknown',.3)
