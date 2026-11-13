"""V0.8.0–0.8.1: witness transaction, pivot, and batch XML-image association."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from varians_synchro.core import (new_project, create_witness, save_project, load_project)
from varians_synchro.resource_workflow import (apply_witness_draft, resource_summary)
from varians_synchro.bulk_binding import (propose_bindings, apply_binding_choices)
from varians_synchro.project_state import project_fingerprint
from varians_synchro.page_order import ordered_pages
from varians_synchro.i18n import set_language, tr

PAGE = '''<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
<Page imageFilename="{filename}" imageWidth="800" imageHeight="900">
 <TextRegion id="r1"><Coords points="10,20 700,20 700,500 10,500"/>
  <TextLine id="l1"><Coords points="10,20 200,20 200,40 10,40"/>
   <TextEquiv><Unicode>exemplar</Unicode></TextEquiv></TextLine>
 </TextRegion>
</Page></PcGts>'''
TEI = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><lb edRef="#Mu"/>Bonjour</p></body></text></TEI>'


def files(tmp, image_names, xml_names=None, filenames=None):
    img_dir=tmp/'images';img_dir.mkdir(exist_ok=True)
    xml_dir=tmp/'xml';xml_dir.mkdir(exist_ok=True)
    ims=[];xml=[]
    for name in image_names:
        f=img_dir/name;f.write_bytes(b'FAKE_IMAGE')
        ims.append(str(f))
    for i,name in enumerate(xml_names or []):
        f=xml_dir/name;f.write_text(PAGE.format(filename=(filenames or ['no-match']*len(xml_names))[i]),encoding='utf-8')
        xml.append(str(f))
    return ims,xml


def test_witness_minimal_and_pivot(tmp_path):
    p=new_project('Edition')
    w=apply_witness_draft(p,identifier='Mu')
    assert p['pivot_witness_id']=='Mu' and w['id']=='Mu'
    assert resource_summary(p,'Mu')['pages']==0
    apply_witness_draft(p,identifier='F')
    assert p['pivot_witness_id']=='Mu'
    apply_witness_draft(p,identifier='F',is_pivot=True,label='Fribourg')
    assert p['pivot_witness_id']=='F'
    assert next(w for w in p['witnesses'] if w['id']=='F')['label']=='Fribourg'
    path=tmp_path/'test.vsynch';save_project(p,path)
    assert load_project(path)['pivot_witness_id']=='F'


def test_resource_batch_import_natural_order_no_id_change(tmp_path):
    ims,xml=files(tmp_path,['p10.png','p2.png','p1.png'],['a.xml','b.xml','c.xml'])
    p=new_project()
    w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    assert [x['label'] for x in ordered_pages(w)]==['p1','p2','p10']
    ids={x['label']:x['id'] for x in w['pages']}
    sources=[x['id'] for x in w['alto_sources']]
    apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml,label='Edited')
    w=p['witnesses'][0]
    assert ids=={x['label']:x['id'] for x in w['pages']}
    assert sources==[x['id'] for x in w['alto_sources']]
    assert w['label']=='Edited'


def test_invalid_xml_aborts_whole_import(tmp_path):
    ims,xml=files(tmp_path,['p1.png'])
    invalid=tmp_path/'wrong.xml';invalid.write_text('<TEI/>')
    p=new_project();create_witness(p,'F')
    fingerprint=project_fingerprint(p)
    with pytest.raises(ValueError):
        apply_witness_draft(p,identifier='F',images=ims,xml_files=[invalid],is_pivot=True)
    assert project_fingerprint(p)==fingerprint


def test_missing_image_aborts_import(tmp_path):
    p=new_project()
    baseline=project_fingerprint(p)
    with pytest.raises(FileNotFoundError):
        apply_witness_draft(p,identifier='F',images=[tmp_path/'absent.jpg'])
    assert project_fingerprint(p)==baseline


def test_tei_registered_without_fictitious_lb_mapping(tmp_path):
    tei=tmp_path/'edition.xml';tei.write_text(TEI,encoding='utf-8')
    p=new_project()
    apply_witness_draft(p,identifier='Mu',tei_files=[tei])
    resource=p['text_resources'][0]
    assert resource['status']=='tei_unaligned' and resource['lines']==[]
    assert tei.read_text(encoding='utf-8')==TEI
    apply_witness_draft(p,identifier='Mu',tei_files=[tei])
    assert len(p['text_resources'])==1


def test_invalid_tei_and_no_partial_commit(tmp_path):
    ims,_=files(tmp_path,['p1.png'])
    wrong=tmp_path/'wrong.tei';wrong.write_text('<doc/>')
    p=new_project();fingerprint=project_fingerprint(p)
    with pytest.raises(ValueError):
        apply_witness_draft(p,identifier='Mu',images=ims,tei_files=[wrong])
    assert project_fingerprint(p)==fingerprint


def test_unique_xml_page_image_filename_matching(tmp_path):
    ims,xml=files(tmp_path,['folio_2v.jpg','folio_3r.jpg'],
                  ['randomZ.xml','randomA.xml'],['folio_2v.jpg','folio_3r.jpg'])
    p=new_project()
    w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    assert len(plan['rows'])==2
    assert {r['method'] for r in plan['rows']}=={'name'}
    result=apply_binding_choices(w,plan,{r['page_id']:r['target'] for r in plan['rows']})
    assert result['associated']==2
    assert all(x['alto_binding'] for x in w['pages'])


def test_secondary_natural_order_is_explicit(tmp_path):
    ims,xml=files(tmp_path,['im10.png','im2.png','im1.png'],
                  ['page10.xml','page2.xml','page1.xml'])
    p=new_project()
    w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    assert plan['needs_review']==3
    assert [r['method'] for r in plan['rows']]==['ordinal']*3
    # Preview alone must have no side effects.
    assert all(not x['alto_binding'] for x in w['pages'])
    ids_before={pg['id']:(pg.get('image_path'),pg.get('reading_order')) for pg in w['pages']}
    apply_binding_choices(w,plan,{r['page_id']:r['target'] for r in plan['rows']})
    ids_after={pg['id']:(pg.get('image_path'),pg.get('reading_order')) for pg in w['pages']}
    assert ids_before==ids_after


def test_different_cardinalities_never_zip_by_index(tmp_path):
    ims,xml=files(tmp_path,['a1.png','a2.png','a3.png'],['b1.xml','b2.xml'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    assert all(r['method']=='unresolved' for r in plan['rows'])


def test_iiif_canvas_subset_never_ordinal_guess(tmp_path):
    p=new_project();w=create_witness(p,'F')
    w['pages']=[{'id':'canvas:14v','label':'14v','image_kind':'iiif',
                 'canvas':{'id':'canvas:14v'},'alto_binding':None}]
    xmlfile=tmp_path/'random.xml';xmlfile.write_text(PAGE.format(filename='other.jpg'))
    from varians_synchro.core import add_alto_source
    add_alto_source(w,xmlfile)
    plan=propose_bindings(w)
    assert plan['rows'][0]['method']=='unresolved'


def test_manifest_import_missing_network_preserves_url_and_pivot(tmp_path):
    p=new_project()
    w=apply_witness_draft(p,identifier='F',manifests=['https://example.invalid/iiif.json'],
                          manifest_loader=lambda url: (_ for _ in ()).throw(OSError('offline')))
    assert w['image_sources'][0]['status']=='unavailable'
    assert w['image_sources'][0]['reference']=='https://example.invalid/iiif.json'
    assert w['pages']==[]


def test_batch_confirm_reject_duplicate_xml_and_preserve_existing(tmp_path):
    ims,xml=files(tmp_path,['a1.png','a2.png'],['b1.xml','b2.xml'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    first=plan['rows'][0]
    choice={r['page_id']:first['target'] for r in plan['rows']}
    before=project_fingerprint(p)
    with pytest.raises(ValueError, match='même page XML'):
        apply_binding_choices(w,plan,choice)
    assert project_fingerprint(p)==before
    result=apply_binding_choices(w,plan,{first['page_id']:first['target']})
    assert result['associated']==1
    new_plan=propose_bindings(w)
    assert len(new_plan['rows'])==1
    with pytest.raises(ValueError, match='changé'):
        apply_binding_choices(w,plan,choice)


def test_existing_binding_is_never_overridden(tmp_path):
    ims,xml=files(tmp_path,['a1.png','a2.png'],['b1.xml','b2.xml'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    p1,p2=plan['rows']
    apply_binding_choices(w,plan,{p1['page_id']:p1['target']})
    original=copy.deepcopy(next(pg['alto_binding'] for pg in w['pages'] if pg['id']==p1['page_id']))
    plan=propose_bindings(w)
    assert all(r['page_id']!=p1['page_id'] for r in plan['rows'])
    apply_binding_choices(w,plan,{r['page_id']:r['target'] for r in plan['rows']})
    assert original==next(pg['alto_binding'] for pg in w['pages'] if pg['id']==p1['page_id'])


def test_original_project_save_and_manual_order_survive_edit(tmp_path):
    ims,xml=files(tmp_path,['p1.png','p2.png'],['pageA.xml','pageB.xml'])
    p=new_project()
    w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    apply_binding_choices(w,plan,{r['page_id']:r['target'] for r in plan['rows']})
    ids=[pg['id'] for pg in ordered_pages(w)]
    from varians_synchro.page_management import invert_page_order
    invert_page_order(w)
    key={pg['id']:pg['alto_binding'] for pg in w['pages']}
    apply_witness_draft(p,identifier='Mu',tei_files=[])
    assert key=={pg['id']:pg['alto_binding'] for pg in p['witnesses'][0]['pages']}
    assert [pg['id'] for pg in ordered_pages(p['witnesses'][0])]==ids[::-1]
    file=tmp_path/'p.vsynch';save_project(p,file)
    saved=load_project(file)
    assert saved['witnesses'][0]['pages']==p['witnesses'][0]['pages']


def test_new_translations_in_both_catalogs():
    try:
        for lang in ('fr','en'):
            set_language(lang)
            for key in ('resources.project.heading','resources.witness.new',
                        'resources.witness.manifests','resources.binding.title',
                        'resources.binding.ordinal_confirm','resources.project.choose_path'):
                assert tr(key) and tr(key)!=key
            assert '3' in tr('resources.binding.ordinal_confirm',count=3)
    finally:
        set_language('fr')


def test_ui_has_single_resource_entry_and_retired_old_widgets():
    from ui_source import ui_class, ui_files, ui_method
    for name in ('WitnessResourceDialog', 'BatchBindingDialog', 'GuidedWindow'):
        ui_class(name)
    assert 'addWitnessResourcesButton' in ui_method('GuidedWindow', '_build_project_tab')
    source = ''.join(path.read_text(encoding='utf-8') for path in ui_files())
    assert 'Outils historiques V0.5' not in source
    assert 'Importer texte TXT' not in source
    assert 'Texte pivot TXT' not in (Path(__file__).resolve().parents[1]/'varians_synchro'/'gui.py').read_text()


def test_explicit_page_image_filename_overrides_misleading_xml_basename(tmp_path):
    ims,xml=files(tmp_path,['im1.jpg','im2.jpg'],['im1.xml','im2.xml'],
                  ['im2.jpg','im1.jpg'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    assert {r['method'] for r in plan['rows']}=={'name'}
    src_by_id={s['id']:s for s in w['alto_sources']}
    for row in plan['rows']:
        page=next(x for x in w['pages'] if x['id']==row['page_id'])
        src=src_by_id[row['target'][0]]
        assert Path(page['image_path']).name==src['pages'][row['target'][1]]['image_filename']


def test_ambiguous_image_filename_cannot_silently_fall_back_to_ordinal(tmp_path):
    ims,xml=files(tmp_path,['im1.jpg','im2.jpg'],['a.xml','b.xml'],
                  ['im1.jpg','im1.jpg'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    assert all(r['method']=='unresolved' for r in plan['rows'])
    assert not any(r['target'] for r in plan['rows'])


def test_edit_without_new_images_preserves_orphan_pages_in_legacy_project():
    p=new_project()
    w=create_witness(p, 'Mu')
    w['pages']=[{'id':'old-manual-page', 'image_kind':'iiif', 'label':'2v',
                 'image_source_id':'missing-old-reference', 'alto_binding':None}]
    apply_witness_draft(p, identifier='Mu', label='New label')
    assert p['witnesses'][0]['pages'][0]['id']=='old-manual-page'


def test_adding_new_images_refuses_to_silently_delete_orphan_pages(tmp_path):
    imgs,_=files(tmp_path,['new_image.jpg'])
    p=new_project()
    w=create_witness(p,'Mu')
    w['pages']=[{'id':'old-manual-page', 'image_kind':'iiif', 'label':'2v',
                 'image_source_id':'missing-old-reference', 'alto_binding':None}]
    before=project_fingerprint(p)
    with pytest.raises(ValueError,match='supprimerait des pages'):
        apply_witness_draft(p, identifier='Mu', images=imgs)
    assert project_fingerprint(p)==before


def test_external_xml_changed_between_preview_and_commit_is_detected(tmp_path):
    ims,xml=files(tmp_path,['im1.jpg'],['random.xml'],['im1.jpg'])
    p=new_project();w=apply_witness_draft(p,identifier='Mu',images=ims,xml_files=xml)
    plan=propose_bindings(w)
    before=project_fingerprint(p)
    path=Path(xml[0]);path.write_text(path.read_text()+'\n<!-- externally changed -->')
    with pytest.raises(ValueError,match='changé'):
        apply_binding_choices(w,plan,{plan['rows'][0]['page_id']:plan['rows'][0]['target']})
    assert project_fingerprint(p)==before


def test_duplicate_binding_diagnostic_lists_xml_and_both_folios(tmp_path):
    """A 469-canvas IIIF manifest can hide duplicates outside the viewport."""
    from varians_synchro.bulk_binding import binding_selection_conflicts
    p = new_project()
    w = create_witness(p, 'F')
    w['pages'] = [
        {'id': f'canvas:{i}', 'label': f'folio {i}', 'image_kind': 'iiif',
         'canvas': {'id': f'canvas:{i}'}, 'alto_binding': None}
        for i in range(469)
    ]
    source = tmp_path/'F_0001.xml'
    source.write_text(PAGE.format(filename='unrelated.jpg'), encoding='utf-8')
    from varians_synchro.core import add_alto_source
    add_alto_source(w, source)
    plan = propose_bindings(w)
    assert len(plan['rows']) == 469
    assert not any(row['target'] for row in plan['rows'])
    target = (plan['available'][0]['source_id'], plan['available'][0]['page_index'])
    selections = {'canvas:32': target, 'canvas:400': target}
    conflicts = binding_selection_conflicts(plan, selections, w)
    assert len(conflicts) == 1
    assert 'F_0001.xml' in conflicts[0]['xml']
    assert {item['label'] for item in conflicts[0]['pages']} == {'folio 32', 'folio 400'}
    baseline = project_fingerprint(p)
    with pytest.raises(ValueError, match=r'F_0001.xml.*folio 32.*folio 400'):
        apply_binding_choices(w, plan, selections)
    assert project_fingerprint(p) == baseline
    assert apply_binding_choices(w, plan, {'canvas:32': target})['associated'] == 1
