"""HD download receipts, full editorial coverage and Varians offline cache."""
from __future__ import annotations

import copy
import io
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from varians_synchro.core import create_witness, load_project, new_project, save_project
from varians_synchro.hd_registry import (inspect_hd_folder, local_copy_plan,
    register_hd_folder, varians_offline_index)
from varians_synchro.imaging import export_iiif_hd_images
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.varians_project_export import export_varians_project
from varians_synchro.project_state import project_fingerprint


def setup(tmp_path):
    p = new_project('Dossier local')
    w = create_witness(p, 'Mu')
    p['pivot_witness_id'] = 'Mu'
    url = 'https://example.test/manifest'
    canvases = []
    for i in range(3):
        c = {'id': 'https://example.test/canvas/'+str(i),
             'label': 'f.'+str(i), 'image_service': 'https://example.test/api/'+str(i),
             'image_url': 'https://example.test/full/'+str(i),
             'iiif_image_version': 3, 'width': 2500, 'height': 3000}
        canvases.append(c)
    w['image_sources'].append({'kind':'iiif','id':'src0','reference':url,
                              'manifest':{'label':'Demo','canvases':canvases}})
    xml = tmp_path / 'segmentation.xml'; xml.write_text('<alto/>',encoding='utf8')
    w['alto_sources'].append({'id':'xml0','path':str(xml),'kind':'alto',
                             'pages':[{'lines':[{'alto_id':'l1', 'text':'A', 'bbox': {'HPOS':'1','VPOS':'1','WIDTH':'15','HEIGHT':'9'}}]}]})
    for i,c in enumerate(canvases):
        w['pages'].append({'id':c['id'],'label':c['label'],'image_kind':'iiif',
                           'image_source_id':'src0','canvas':c,
                           'alto_binding':{'source_id':'xml0','page_index':0} if i<2 else None})
    tei=tmp_path/'edition.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>'
                   '<lb edRef="#Mu"/>A</p></body></text></TEI>',encoding='utf8')
    store_tei_reference(p,'Mu',tei)
    return p, w


class Response(io.BytesIO):
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def fake_http(monkeypatch):
    import varians_synchro.imaging as imaging
    def download(req, timeout=35):
        return Response(b'\xff\xd8\xff'+req.full_url.encode()*5)
    monkeypatch.setattr(imaging,'urlopen',download)


def test_registered_downloads_persist_and_cover_exact_canvas_set(tmp_path,monkeypatch):
    p,w=setup(tmp_path);fake_http(monkeypatch)
    ids=[x['id'] for x in w['pages']]
    # One batch is not enough.
    export_iiif_hd_images(w,[ids[0]],tmp_path/'hd1')
    register_hd_folder(w,tmp_path/'hd1')
    assert local_copy_plan(w)['missing']==[ids[1]]
    save_project(p,tmp_path/'proj.vsynch')
    persisted=load_project(tmp_path/'proj.vsynch')
    assert persisted['witnesses'][0]['hd_downloads'][0]['directory']==str((tmp_path/'hd1').resolve())
    # Another batch makes the editorial subset complete without downloading page 3.
    export_iiif_hd_images(w,[ids[1]],tmp_path/'hd2')
    register_hd_folder(w,tmp_path/'hd2')
    plan=local_copy_plan(w)
    assert plan['eligible'] and not plan['missing'] and len(plan['available'])==2
    original=project_fingerprint(p)
    dest=tmp_path/'Varians'
    report=export_varians_project(p,'Mu',dest)
    assert report['local_hd_copies']=={'Mu':2}
    assert project_fingerprint(p)==original
    root=ET.parse(dest/'project.xml').getroot()
    assert root.find('witnesses/witness/images').attrib['localCopy']=='true'
    assert root.find('witnesses/witness/images').attrib['downloadScope']=='ocr'
    idx=json.loads((dest/'iiif/local/Mu/index.json').read_text())
    assert idx['format']=='varians-iiif-local-1' and len(idx['images'])==2
    for entry in idx['images'].values():
        assert (dest/'iiif/local/Mu'/entry['file']).read_bytes().startswith(b'\xff\xd8\xff')
    cache=json.loads((dest/'iiif/Mu.manifest.json').read_text())
    assert cache['_format']=='varians-iiif-manifest-cache'
    assert len(cache['manifest']['items'])==3


def test_incomplete_downloads_never_copied(tmp_path,monkeypatch):
    p,w=setup(tmp_path);fake_http(monkeypatch)
    export_iiif_hd_images(w,[w['pages'][0]['id']],tmp_path/'hd')
    register_hd_folder(w,tmp_path/'hd')
    report=export_varians_project(p,'Mu',tmp_path/'partial')
    assert report['local_hd_copies']=={}
    images=ET.parse(tmp_path/'partial/project.xml').getroot().find('witnesses/witness/images')
    assert images.get('type')=='iiif' and images.get('localCopy') is None
    assert not (tmp_path/'partial/iiif/local/Mu').exists()


def test_tampering_move_or_wrong_canvas_rejects_offline_copy(tmp_path,monkeypatch):
    p,w=setup(tmp_path);fake_http(monkeypatch)
    ids=[x['id'] for x in w['pages'][:2]]
    export_iiif_hd_images(w,ids,tmp_path/'hd')
    register_hd_folder(w,tmp_path/'hd')
    assert local_copy_plan(w)['eligible']
    jpg=next((tmp_path/'hd').glob('*.jpg'))
    jpg.write_bytes(jpg.read_bytes()+b'corrupted')
    assert not local_copy_plan(w)['eligible']
    # Source changes invalidate the cached copy, too.
    jpg.write_bytes(jpg.read_bytes()[:-9])
    w['pages'][0]['canvas']['image_service']='https://changed.test/api/0'
    assert not local_copy_plan(w)['eligible']
    with pytest.raises(ValueError, match='Source IIIF'):
        inspect_hd_folder(w,tmp_path/'hd')


def test_existing_downloads_can_be_reattached_without_redownloading(tmp_path,monkeypatch):
    p,w=setup(tmp_path);fake_http(monkeypatch)
    ids=[x['id'] for x in w['pages'][:2]]
    export_iiif_hd_images(w,ids,tmp_path/'earlier')
    assert not w.get('hd_downloads')
    batch=register_hd_folder(w,tmp_path/'earlier')
    assert len(batch['pages'])==2 and local_copy_plan(w)['eligible']
    # Re-registering must not duplicate records.
    register_hd_folder(w,tmp_path/'earlier')
    assert len(w['hd_downloads'])==1


def test_unsegmented_iiif_witness_is_not_eligible(tmp_path,monkeypatch):
    p,w=setup(tmp_path);fake_http(monkeypatch)
    for page in w['pages']:page['alto_binding']=None
    export_iiif_hd_images(w,[w['pages'][0]['id']],tmp_path/'hd')
    register_hd_folder(w,tmp_path/'hd')
    assert not local_copy_plan(w)['eligible']
    assert local_copy_plan(w)['required']==[]


def test_gui_groups_old_htr_actions_away_from_hd_workflow():
    from ui_source import ui_class
    s = ui_class('PagesDialog')[0]
    assert "htr_group = QGroupBox(tr('ui.pages.htr.group'))" in s
    assert "def attach_hd_folder(self):" in s
    assert "thread.validated_hd_batch" in s


def test_corrupted_extra_page_cannot_block_complete_editorial_subset(tmp_path, monkeypatch):
    p, w = setup(tmp_path)
    fake_http(monkeypatch)
    ids = [x['id'] for x in w['pages']]
    export_iiif_hd_images(w, ids, tmp_path / 'all')
    register_hd_folder(w, tmp_path / 'all')
    receipt = json.loads((tmp_path/'all/images.json').read_text(encoding='utf-8'))
    extra_name = next(row['file'] for row in receipt['pages'] if row['canvas_id'] == ids[2])
    (tmp_path/'all'/extra_name).write_bytes(b'broken-extra-copy')
    plan = local_copy_plan(w)
    assert plan['eligible'] and not plan['missing']
    assert len(plan['available']) == 2
    assert plan['problems']
    result = export_varians_project(p, 'Mu', tmp_path/'Varians')
    assert result['local_hd_copies'] == {'Mu':2}


def test_project_rejects_corrupted_hd_registry_structure(tmp_path):
    from varians_synchro.core import validate_project
    project, witness = setup(tmp_path)
    witness['hd_downloads'] = {'oops':'not-a-list'}
    with pytest.raises(ValueError, match='téléchargements HD'):
        validate_project(project)
