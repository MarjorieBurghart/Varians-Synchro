import json
import pytest
from varians_synchro.core import new_project, create_witness
from varians_synchro.alignment import create_session, add_link, remove_link, export_varians, target_lines


def fixture_project():
    project = new_project('Alignement')
    create_witness(project,'A')
    w=create_witness(project,'B')
    r={'id':'tei1','kind':'tei','witness_id':'A','path':'base.xml',
       'lines':[{'page_id':'A-p1','ordinal':1,'text':'salve'},
                {'page_id':'A-p1','ordinal':2,'text':'mundi'},
                {'page_id':'A-p1','ordinal':3,'text':'amen'}]}
    project['text_resources'].append(r)
    w['alto_sources'].append({'id':'alto1','path':'b.xml','line_count':3,'htr_line_count':3,
      'pages':[{'width':'1000','height':'1500','lines':[
        {'alto_id':f'Line{i}','text':t,'bbox':{'HPOS':'10','VPOS':str(100*i),'WIDTH':'400','HEIGHT':'40'}}
        for i,t in enumerate(['salve','mundi','amen'],1)]}]})
    w['pages']=[{'id':'B-p1','label':'1r','image_kind':'local','image_path':'img.jpg',
                 'alto_binding':{'source_id':'alto1','page_index':0}}]
    return project,w


def test_many_to_many_export(tmp_path):
    p,w=fixture_project()
    s=create_session(p,'tei1','B')
    add_link(p,s,['A-p1::1','A-p1::2'],['B-p1::1','B-p1::2'])
    add_link(p,s,['A-p1::3'],['B-p1::3'])
    out=tmp_path/'export.json'
    info=export_varians(p,s,out)
    data=json.loads(out.read_text())
    assert info['mapped_lines']==3
    assert data['pages'][0]['lines'][0]['base_keys']==['A-p1::1','A-p1::2']
    assert data['pages'][0]['lines'][2]['bbox']['vpos']==300
    assert data['meta']['format']=='tei-manuscript-alignment'


def test_collision_and_removal():
    p,_=fixture_project();s=create_session(p,'tei1','B')
    l=add_link(p,s,['A-p1::1'],['B-p1::1'])
    with pytest.raises(ValueError):add_link(p,s,['A-p1::1'],['B-p1::2'])
    with pytest.raises(ValueError):add_link(p,s,['A-p1::2'],['B-p1::1'])
    remove_link(s,l['id'])
    assert add_link(p,s,['A-p1::1'],['B-p1::2'])


def test_confirmed_absence_and_unresolved(tmp_path):
    p,_=fixture_project();s=create_session(p,'tei1','B')
    add_link(p,s,['A-p1::1'],[],kind='absence')
    add_link(p,s,[],['B-p1::2'],kind='absence')
    result=export_varians(p,s,tmp_path/'export.json')
    assert result['base_absences_not_exported']==1
    data=json.loads((tmp_path/'export.json').read_text())
    assert all(l['base_keys']==[] for l in data['pages'][0]['lines'])
    assert len(s['links'])==2


def test_reject_unknown_refs():
    p,_=fixture_project();s=create_session(p,'tei1','B')
    with pytest.raises(ValueError):add_link(p,s,['A-p1::99'],['B-p1::1'])
    with pytest.raises(ValueError):add_link(p,s,[],[],kind='absence')
    with pytest.raises(ValueError):add_link(p,s,['A-p1::1'],[],kind='correspondence')
