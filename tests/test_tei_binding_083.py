"""Editorial TEI ↔ PAGE/ALTO tests: source integrity and honest apparatus."""
from __future__ import annotations

import copy

import pytest

from varians_synchro.core import new_project, create_witness, add_image_source, add_alto_source, save_project, load_project
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.reading_stream import reading_stream
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.project_state import project_fingerprint
from varians_synchro.tei_binding import (extract_witness_tei, preview_tei_binding,
    apply_tei_binding, tei_binding_status)

NS='http://www.tei-c.org/ns/1.0'
PAGE='''<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
<Page imageFilename="{image}" imageWidth="500" imageHeight="800">
<TextRegion id="r"><Coords points="1,1 490,1 490,600 1,600"/>
{lines}
</TextRegion></Page></PcGts>'''


def fixture(tmp_path, counts=(2,2)):
    proj = new_project(); w=create_witness(proj,'Mu'); create_witness(proj,'F')
    for i,n in enumerate(counts):
        f = tmp_path/f'p{i+1}.jpg'; f.write_bytes(b'image')
        add_image_source(w,'local',str(f))
        lines=''.join(f'<TextLine id="l{i}_{j}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} 10,{j*30+20}"/><TextEquiv><Unicode>lectio</Unicode></TextEquiv></TextLine>' for j in range(n))
        xml=tmp_path/f'p{i+1}.xml';xml.write_text(PAGE.format(image=f.name,lines=lines))
        add_alto_source(w,xml)
    create_pages(w)
    for index,page in enumerate(w['pages']):
        # standard binding lookup, as used in real PAGE workflow
        src=w['alto_sources'][index]
        bind_alto(w,page['id'],src['id'],0)
    return proj,w


def tei(tmp_path, content):
    p=tmp_path/'edition.tei';p.write_text(f'<TEI xmlns="{NS}"><text><body><p>{content}</p></body></text></TEI>',encoding='utf-8')
    return p


def test_tei_extract_strict_edref_and_choice_and_apparatus(tmp_path):
    p=tei(tmp_path, '<pb n="1r" edRef="#Mu"/><lb xml:id="m1" edRef="#Mu"/>Ave '
          '<app><lem wit="#Mu">Maria</lem><rdg wit="#F">Marta</rdg></app> '
          '<choice><orig>mundi</orig><reg>mundo</reg></choice> '
          '<lb edRef="#F"/>intercalatum <lb xml:id="m2" edRef="#Mu"/>salve')
    result=extract_witness_tei(p,'Mu')
    assert len(result['lines'])==2
    assert 'Maria' in result['lines'][0]['text'] and 'Marta' not in result['lines'][0]['text']
    assert 'mundo' in result['lines'][0]['text'] and 'mundi' not in result['lines'][0]['text']
    assert result['ignored_other_witness_lb']==1
    assert result['lines'][0]['page_label']=='1r'
    assert not result['blocking']


def test_ambiguous_app_never_contaminates_target_and_blocks(tmp_path):
    p=tei(tmp_path,'<lb edRef="#Mu"/>A<app><lem>AAA</lem><rdg>BBB</rdg></app>Z')
    x=extract_witness_tei(p,'Mu')
    assert x['blocking'] and x['lines'][0]['text']=='AZ'
    assert x['diagnostics'][0]['code']=='apparatus_unresolved'


def test_tei_count_and_cross_folio_binding(tmp_path):
    p,w=fixture(tmp_path)
    doc=tei(tmp_path,'<lb edRef="#Mu" xml:id="m1"/>one<lb edRef="#Mu"/>two'
          '<pb n="2r"/><lb edRef="#Mu"/>three<lb edRef="#Mu"/>four')
    r=store_tei_reference(p,'Mu',doc)
    preview=preview_tei_binding(p,'Mu',r['id'])
    assert preview['eligible'] and (preview['tei_count'],preview['physical_count'])==(4,4)
    assert len({q['page_id'] for q in preview['pairs']})==2
    before=copy.deepcopy(p['pair_sessions'])
    assert apply_tei_binding(p,'Mu',r['id'],preview)['count']==4
    assert p['pair_sessions']==before
    assert tei_binding_status(p,'Mu',r['id'])['status']=='valid'
    f=tmp_path/'edit.vsynch';save_project(p,f)
    assert tei_binding_status(load_project(f),'Mu',r['id'])['status']=='valid'


def test_ignored_lines_are_required_to_make_counts_equal(tmp_path):
    p,w=fixture(tmp_path)
    w['ignored_line_ids']=[reading_stream(w)[0]['id']]
    doc=tei(tmp_path,'<lb edRef="#Mu"/>one<lb edRef="#Mu"/>two<lb edRef="#Mu"/>three')
    r=store_tei_reference(p,'Mu',doc)
    prev=preview_tei_binding(p,'Mu',r['id'])
    assert prev['eligible'] and prev['physical_count']==3
    assert prev['pairs'][0]['physical_line_id']!=w['ignored_line_ids'][0]


def test_mismatch_rejected_without_any_mutation(tmp_path):
    p,w=fixture(tmp_path)
    doc=tei(tmp_path,'<lb edRef="#Mu"/>one<lb edRef="#Mu"/>two')
    r=store_tei_reference(p,'Mu',doc)
    snapshot=project_fingerprint(p)
    preview=preview_tei_binding(p,'Mu',r['id'])
    assert not preview['eligible']
    with pytest.raises(ValueError):apply_tei_binding(p,'Mu',r['id'],preview)
    assert project_fingerprint(p)==snapshot


def test_stale_file_or_scope_blocks_bulk_link(tmp_path):
    p,w=fixture(tmp_path)
    doc=tei(tmp_path,''.join('<lb edRef="#Mu"/>x' for _ in range(4)))
    r=store_tei_reference(p,'Mu',doc)
    preview=preview_tei_binding(p,'Mu',r['id'])
    w['ignored_line_ids']=[reading_stream(w)[0]['id']]
    with pytest.raises(ValueError):apply_tei_binding(p,'Mu',r['id'],preview)
    w['ignored_line_ids']=[]
    apply_tei_binding(p,'Mu',r['id'],preview)
    doc.write_text(doc.read_text().replace('/>x','/>changed'))
    assert tei_binding_status(p,'Mu',r['id'])['status']=='stale'


def test_apparatus_binding_requires_resolution(tmp_path):
    p,w=fixture(tmp_path,counts=(1,))
    doc=tei(tmp_path,'<lb edRef="#Mu"/>a<app><lem>abc</lem><rdg>xyz</rdg></app>')
    r=store_tei_reference(p,'Mu',doc)
    preview=preview_tei_binding(p,'Mu',r['id'])
    assert not preview['eligible'] and any(i['code']=='apparatus_unresolved' for i in preview['diagnostics'])


def test_no_implicit_untagged_lb(tmp_path):
    doc=tei(tmp_path,'<lb/>surplus<lb edRef="#Mu"/>cible<lb edRef="#F"/>autre')
    r=extract_witness_tei(doc,'Mu')
    assert r['lines'][0]['ordinal']==1 and r['diagnostics'][0]['code']=='unattributed_lb'


def test_original_inputs_always_unchanged(tmp_path):
    p,w=fixture(tmp_path)
    doc=tei(tmp_path,''.join('<lb edRef="#Mu"/>x' for _ in range(4)))
    original=doc.read_bytes()
    r=store_tei_reference(p,'Mu',doc)
    preview=preview_tei_binding(p,'Mu',r['id'])
    apply_tei_binding(p,'Mu',r['id'],preview)
    assert doc.read_bytes()==original


def test_explicit_refresh_tei_source_archives_binding_and_preserves_pairs(tmp_path):
    from varians_synchro.tei_binding import refresh_tei_source
    p,w=fixture(tmp_path,counts=(1,))
    doc=tei(tmp_path,'<lb edRef="#Mu"/>x')
    r=store_tei_reference(p,'Mu',doc)
    apply_tei_binding(p,'Mu',r['id'],preview_tei_binding(p,'Mu',r['id']))
    doc.write_text(doc.read_text().replace('/>x','/>new x'), encoding='utf-8')
    prior=project_fingerprint(p)
    with pytest.raises(ValueError):refresh_tei_source(p,'Mu',r['id'])
    assert project_fingerprint(p)==prior
    refresh_tei_source(p,'Mu',r['id'], replace_binding=True)
    assert r['status']=='tei_unaligned' and 'tei_binding' not in r
    assert len(r['tei_binding_history'])==1
    apply_tei_binding(p,'Mu',r['id'],preview_tei_binding(p,'Mu',r['id']))
    assert r['lines'][0]['text']=='new x'


def test_changed_physical_order_never_silently_rebinds_tei(tmp_path):
    from varians_synchro.reading_stream import set_page_order
    p,w=fixture(tmp_path,counts=(1,1))
    doc=tei(tmp_path,'<lb edRef="#Mu"/>alpha<lb edRef="#Mu"/>beta')
    r=store_tei_reference(p,'Mu',doc)
    apply_tei_binding(p,'Mu',r['id'],preview_tei_binding(p,'Mu',r['id']))
    reversed_ids=[x['id'] for x in reversed(w['pages'])]
    set_page_order(w,reversed_ids)
    assert tei_binding_status(p,'Mu',r['id'])['status']=='stale'
    new=preview_tei_binding(p,'Mu',r['id'])
    assert new['eligible']
    with pytest.raises(ValueError):apply_tei_binding(p,'Mu',r['id'],new)
    assert apply_tei_binding(p,'Mu',r['id'],new,replace=True)['count']==2


def test_malformed_saved_binding_is_rejected(tmp_path):
    p,w=fixture(tmp_path,counts=(1,))
    doc=tei(tmp_path,'<lb edRef="#Mu"/>x')
    r=store_tei_reference(p,'Mu',doc)
    r['tei_binding']={'witness_id':'F', 'pairs':[{'tei_key':'lb1','physical_line_id':'whatever'}]}
    from varians_synchro.core import validate_project
    with pytest.raises(ValueError, match='Liaison TEI'):
        validate_project(p)
