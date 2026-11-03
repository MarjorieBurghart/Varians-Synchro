from test_alignment import fixture_project
from varians_synchro.alignment import create_session, add_link
from varians_synchro.automatic import normalize, propose_alignment, apply_proposals


def test_normalization():
    assert normalize('Iohánnes, CONVENIT!') == normalize('Johannes conuenit')


def test_proposes_without_mutation():
    p,_=fixture_project();s=create_session(p,'tei1','B')
    out=propose_alignment(p,s,min_match=3,min_support=.3)
    assert len(out['proposals'])>=1
    assert s['links']==[]
    result=apply_proposals(p,s,out['proposals'],include_uncertain=True)
    assert result['added']>=1
    assert all(x['state']!='validated' for x in s['links'])
    assert all(x['origin']=='automatic' for x in s['links'])
    assert apply_proposals(p,s,out['proposals'],include_uncertain=True)['added']==0


def test_preserves_manual_links():
    p,_=fixture_project();s=create_session(p,'tei1','B')
    fixed=add_link(p,s,['A-p1::1'],['B-p1::1'])
    proposals=propose_alignment(p,s,min_match=3)['proposals']
    assert all('A-p1::1' not in x['base_keys'] and 'B-p1::1' not in x['target_refs'] for x in proposals)
    apply_proposals(p,s,proposals,include_uncertain=True)
    assert fixed in s['links']


def test_missing_htr_is_graceful():
    p,w=fixture_project();s=create_session(p,'tei1','B')
    for line in w['alto_sources'][0]['pages'][0]['lines']:line['text']=''
    out=propose_alignment(p,s)
    assert out['proposals']==[]
    assert out['unmatched_target']==3


def test_split_line():
    p,w=fixture_project();r=p['text_resources'][0]
    r['lines']=[{'page_id':'A-p1','ordinal':1,'text':'beatus germanus in hac vita'}]
    w['alto_sources'][0]['pages'][0]['lines']=[
        {'alto_id':'x','text':'beatus germanus','bbox':{}},
        {'alto_id':'y','text':'in hac vita','bbox':{}}]
    s=create_session(p,'tei1','B')
    out=propose_alignment(p,s,min_match=4,min_support=.2)
    assert any(len(x['target_refs'])==2 and len(x['base_keys'])==1 for x in out['proposals'])
