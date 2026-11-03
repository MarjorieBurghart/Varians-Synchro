"""V0.8.4 read-only endpoint/intermediate previews, physical geometry, IIIF regions."""
import copy
from pathlib import Path
import pytest

from test_tei_binding_083 import fixture, tei
from varians_synchro.project_state import project_fingerprint
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.tei_binding import preview_tei_binding, apply_tei_binding
from varians_synchro.tei_visual import (review_pairs, line_preview_descriptor,
                                         render_transform)


def _prepare(tmp_path, counts=(2,2)):
    project, witness = fixture(tmp_path, counts=counts)
    doc=tei(tmp_path, ''.join(f'<lb edRef="#Mu"/>ligne {i}' for i in range(sum(counts))))
    res=store_tei_reference(project, 'Mu', doc)
    proposal=preview_tei_binding(project,'Mu',res['id'])
    assert proposal['eligible']
    return project,witness,res,proposal


def test_ends_are_explicit_not_relabelled_or_saved(tmp_path):
    project,w,r,p = _prepare(tmp_path)
    before=project_fingerprint(project)
    ends=review_pairs(p)
    assert ends['count']==4
    assert ends['first']['tei_ordinal']==1
    assert ends['last']['tei_ordinal']==4
    assert ends['first']['page_id'] != ends['last']['page_id']
    for pair in (ends['first'],ends['last'], p['pairs'][1]):
        model=line_preview_descriptor(project,'Mu',pair)
        assert model['tei_ordinal']==pair['tei_ordinal']
        assert model['physical_line_id']==pair['physical_line_id']
        assert model['polygon_xml']
        assert model['region_url'] is None
        t=render_transform(model,500,800)
        assert t['crop'][2] > 0 and t['crop'][3] > 0
        assert len(t['polygon'])>=3
    assert project_fingerprint(project)==before


def test_clips_crop_to_xml_bounds(tmp_path):
    p,w,r,proposal=_prepare(tmp_path,counts=(1,))
    model=line_preview_descriptor(p,'Mu',proposal['pairs'][0])
    x,y,cw,ch=model['crop_xml']
    assert x>=0 and y>=0 and x+cw<=500 and y+ch<=800
    crop=render_transform(model,250,400)
    assert crop['crop'][0]>=0 and crop['crop'][1]>=0
    assert crop['crop'][0]+crop['crop'][2]<=250


def test_region_on_iiif_canvas_with_different_xml_scale(tmp_path):
    p,w,r,proposal=_prepare(tmp_path,counts=(1,))
    page=w['pages'][0]
    page['image_kind']='iiif'
    page['canvas']={'image_service':'https://iiif.example/image',
                    'iiif_image_version':3, 'width':1000,'height':1600}
    descriptor=line_preview_descriptor(p,'Mu',proposal['pairs'][0])
    assert descriptor['region_canvas'] is not None
    assert '/1300,/0/default.jpg' in descriptor['region_url']
    assert 'full' not in descriptor['region_url']
    crop=render_transform(descriptor,600,200)
    assert crop['crop']==[0,0,600,200]
    assert 0 <= min(point[0] for point in crop['polygon'])
    assert 0 <= min(point[1] for point in crop['polygon'])


def test_iiif_v2_region_and_no_service_fallback(tmp_path):
    p,w,r,proposal=_prepare(tmp_path,counts=(1,))
    page=w['pages'][0]
    page['image_kind']='iiif'
    page['canvas']={'image_service':'https://iiif.example/image',
                    'iiif_image_version':2, 'width':500,'height':800}
    descriptor=line_preview_descriptor(p,'Mu',proposal['pairs'][0])
    assert '/!1300,/0/default.jpg' in descriptor['region_url']
    page['canvas']['image_service']=None
    descriptor=line_preview_descriptor(p,'Mu',proposal['pairs'][0])
    assert descriptor['region_url'] is None


def test_stale_physical_signature_rejected(tmp_path):
    p,w,r,proposal=_prepare(tmp_path,counts=(1,))
    pair=copy.deepcopy(proposal['pairs'][0]);pair['physical_fingerprint']='falsified'
    with pytest.raises(ValueError,match='segmentation'):
        line_preview_descriptor(p,'Mu',pair)


def test_invalid_preview_has_no_fictive_ends():
    assert review_pairs({'eligible':False, 'pairs':[{'tei_ordinal':1}]})['first'] is None
    assert review_pairs({'eligible':True,'pairs':[]})['last'] is None


def test_linked_tei_text_source_never_uses_stale_or_ambiguous_edition(tmp_path):
    from varians_synchro.tei_binding import linked_tei_texts
    from varians_synchro.reading_stream import reading_stream
    project,witness,res,proposal=_prepare(tmp_path,counts=(2,2))
    assert linked_tei_texts(project,'Mu') == {}  # no validated binding yet
    apply_tei_binding(project,'Mu',res['id'],proposal)
    mapped=linked_tei_texts(project,'Mu')
    assert len(mapped)==4
    assert mapped[reading_stream(witness)[0]['id']] == 'ligne 0'
    assert not linked_tei_texts(project,'F')
    # Stale source must *never* be presented as current text.
    Path(res['path']).write_text(Path(res['path']).read_text().replace('ligne 0','altéré 0'))
    assert linked_tei_texts(project,'Mu') == {}


def test_saved_tei_can_be_visually_inspected_after_reopen(tmp_path):
    from varians_synchro.core import save_project, load_project
    from varians_synchro.tei_binding import linked_tei_texts
    project,witness,res,proposal=_prepare(tmp_path,counts=(2,2))
    apply_tei_binding(project,'Mu',res['id'],proposal)
    filename=tmp_path/'session.vsynch'
    save_project(project,filename)
    restored=load_project(filename)
    texts=linked_tei_texts(restored,'Mu')
    assert len(texts)==4
    fresh=preview_tei_binding(restored,'Mu',res['id'])
    assert fresh['eligible']
    assert line_preview_descriptor(restored,'Mu',fresh['pairs'][-1])['tei_text']=='ligne 3'
