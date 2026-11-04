"""UI translation, non-destructive HD IIIF export, and Varians-project bundle."""
from __future__ import annotations

import copy
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from varians_synchro.core import new_project, create_witness
from varians_synchro.i18n import tr, set_language
from varians_synchro.imaging import iiif_hd_url, export_iiif_hd_images
from varians_synchro.varians_project_export import export_varians_project
from varians_synchro.project_state import project_fingerprint
from varians_synchro.varians_export import verify_export_payloads
from varians_synchro.resource_workflow import store_tei_reference


def fixture(tmp_path):
    p = new_project('Édition scientifique')
    w = create_witness(p, 'Mu')
    im = tmp_path / 'Mu.jpg'
    im.write_bytes(b'test-image')
    xml = tmp_path / 'Mu.xml'
    xml.write_text('<alto/>', encoding='utf-8')
    source_id = 'my-alto'
    w['image_sources'].append({'id': 'image', 'kind': 'local', 'reference': str(im)})
    w['alto_sources'].append({'id': source_id, 'path': str(xml),
                              'pages': [{'width': 100, 'height': 100,
                                         'lines': [{'alto_id':'L1','text':'L','bbox': {'HPOS':0,'VPOS':0,'WIDTH':40,'HEIGHT':20}}]}]})
    w['pages'].append({'id': 'my-image', 'label': '1r', 'image_kind': 'local',
                       'image_path': str(im),
                       'alto_binding': {'source_id':source_id, 'page_index':0}})
    tei = tmp_path / 'edition.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><lb edRef="#Mu"/>L</p></body></text></TEI>', encoding='utf-8')
    store_tei_reference(p, 'Mu', tei)
    return p


def test_english_french_labels_and_tips():
    try:
        for lang, expected in [('fr', '1 · Ajout des témoins'), ('en', '1 · Add witnesses')]:
            set_language(lang)
            assert tr('navigation.project') == expected
            assert tr('ui.pages.scope.tip') != 'ui.pages.scope.tip'
            assert tr('ui.final.export_project.tip') != 'ui.final.export_project.tip'
    finally:
        set_language('fr')


def test_project_export_validates_and_preserves_tei_sources(tmp_path):
    project = fixture(tmp_path)
    original = project_fingerprint(project)
    dest = tmp_path / 'destination'
    result = export_varians_project(project, 'Mu', dest)
    assert result['base'] == 'Mu'
    config = ET.parse(dest/'project.xml').getroot()
    assert config.tag == 'teiManuscriptProject'
    assert config.find('witnesses').get('base') == 'Mu'
    witness = config.find('witnesses/witness')
    assert witness.get('id') == 'Mu'
    assert witness.find('images').get('type') == 'files'
    # Pas de <alto> : le JSON porte déjà lignes, géométrie et texte ; des
    # fichiers ALTO/PAGE déclarés seraient superposés au JSON par Varians
    # (lignes hors périmètre réintroduites ; voir test_varians_094_compat).
    assert witness.find('alto') is None
    assert (dest/'xml'/'edition.xml').read_bytes() == Path(project['text_resources'][0]['path']).read_bytes()
    mapping = json.loads((dest/'alignments'/'Mu.json').read_text())
    assert verify_export_payloads({'Mu':mapping},'Mu')['all_base_keys_resolve']
    assert project_fingerprint(project) == original
    with pytest.raises(FileExistsError):
        export_varians_project(project, 'Mu', dest)


def test_project_export_without_tei_gets_a_blank_edition(tmp_path):
    """Comme une « transcription vierge » créée dans Varians : une TEI vide,
    où Varians peut ensuite préparer les <pb/> et <lb/> du pivot."""
    p = fixture(tmp_path)
    p['text_resources'] = []
    result = export_varians_project(p, 'Mu', tmp_path/'blank')
    assert result['tei'] is None and result['edition'] == 'blank'
    text = (tmp_path/'blank'/'xml'/'edition.xml').read_text(encoding='utf-8')
    assert text.count('<?xml-model ') == 2
    root = ET.fromstring(text)
    ns = {'t': 'http://www.tei-c.org/ns/1.0'}
    assert root.find('t:teiHeader/t:fileDesc/t:titleStmt/t:title', ns).text == 'Édition scientifique'
    assert [w.get('{http://www.w3.org/XML/1998/namespace}id')
            for w in root.findall('.//t:listWit/t:witness', ns)] == ['Mu']
    body = root.find('t:text/t:body', ns)
    assert [child.tag for child in body] == ['{http://www.tei-c.org/ns/1.0}p'] and not body[0].text
    report = (tmp_path/'blank'/'RAPPORT_EXPORT_VARIANS.txt').read_text(encoding='utf-8')
    assert 'TEI vide' in report and 'Paramètres du projet' in report


def test_project_export_with_two_editions_of_the_pivot_is_rejected(tmp_path):
    p = fixture(tmp_path)
    second = tmp_path / 'autre.xml'
    second.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p/></body></text></TEI>',
                      encoding='utf-8')
    store_tei_reference(p, 'Mu', second)
    with pytest.raises(ValueError, match='édition TEI'):
        export_varians_project(p, 'Mu', tmp_path/'nope')


def test_project_export_rejects_missing_external_sources(tmp_path):
    p=fixture(tmp_path)
    p['witnesses'][0]['pages'][0]['image_path']='missing.jpg'
    with pytest.raises(FileNotFoundError):
        export_varians_project(p,'Mu',tmp_path/'bad')
    assert not (tmp_path/'bad').exists()


def _iiif_pages():
    return {'id':'F','pages':[{'id':'canvas-1','image_kind':'iiif', 'label':'14v',
      'canvas':{'image_service':'https://example.org/iiif/14v', 'iiif_image_version':3}},
     {'id':'canvas-2','image_kind':'iiif','label':'15r',
      'canvas':{'image_service':'https://example.org/iiif/15r', 'iiif_image_version':2}}]}


def test_hd_urls_are_native_size():
    w=_iiif_pages()
    assert iiif_hd_url(w['pages'][0]).endswith('/full/max/0/default.jpg')
    assert iiif_hd_url(w['pages'][1]).endswith('/full/full/0/default.jpg')
    with pytest.raises(ValueError):
        iiif_hd_url({'id':'no', 'image_kind':'iiif', 'canvas':{}})


class DummyResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()


def test_hd_download_selected_only_and_atomic(tmp_path, monkeypatch):
    import varians_synchro.imaging as imaging
    calls=[]
    def response(req, timeout=35):
        calls.append(req.full_url)
        return DummyResponse(b'\xff\xd8\xff' + b'x'*100)
    monkeypatch.setattr(imaging, 'urlopen', response)
    w=_iiif_pages()
    snapshot=copy.deepcopy(w)
    dest=tmp_path/'hd'
    assert export_iiif_hd_images(w,['canvas-2'],dest)==1
    assert len(calls)==1 and '/15r/' in calls[0]
    assert [x.name for x in dest.glob('*.jpg')]==['F_0001_15r.jpg']
    assert json.loads((dest/'images.json').read_text())['pages'][0]['canvas_id']=='canvas-2'
    assert w==snapshot
    with pytest.raises(FileExistsError):
        export_iiif_hd_images(w,['canvas-1'],dest)


def test_hd_download_failure_or_cancel_never_publishes(tmp_path, monkeypatch):
    import varians_synchro.imaging as imaging
    w=_iiif_pages()
    monkeypatch.setattr(imaging, 'urlopen', lambda req,timeout=35: DummyResponse(b'NOTJPEG'))
    with pytest.raises(ValueError,match='JPEG'):
        export_iiif_hd_images(w,['canvas-1'],tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
    monkeypatch.setattr(imaging, 'urlopen', lambda req,timeout=35: DummyResponse(b'\xff\xd8\xffOK'))
    with pytest.raises(InterruptedError):
        export_iiif_hd_images(w,['canvas-1'],tmp_path/'cancel', cancelled=lambda:True)
    assert not (tmp_path/'cancel').exists()


def test_hd_rejects_duplicate_pages(tmp_path):
    with pytest.raises(ValueError, match='doublons'):
        export_iiif_hd_images(_iiif_pages(),['canvas-1','canvas-1'],tmp_path/'dest')


def test_varians_project_iiif_selection_and_ocr_links(tmp_path):
    project = fixture(tmp_path)
    witness = project['witnesses'][0]
    witness['image_sources']=[{'kind':'iiif','id':'iiif-1','reference':'https://example.org/manifest.json'}]
    page=witness['pages'][0]
    page.pop('image_path',None)
    page['id']='https://example.org/canvas/14v'
    page['image_kind']='iiif'
    page['canvas']={'id':page['id'], 'image_service':'https://example.org/images/14v',
                    'iiif_image_version':2}
    dest=tmp_path/'varians-export'
    export_varians_project(project,'Mu',dest)
    xml=ET.parse(dest/'project.xml').getroot()
    images=xml.find('witnesses/witness/images')
    assert images.get('type')=='iiif'
    assert images.get('selectionMode')=='selected'
    assert [x.get('ref') for x in images.findall('canvas')]==[page['id']]
    assert images.find('ocrLink').get('canvas')==page['id']
    assert images.find('pageLink').get('page')==page['id']


def test_ui_pages_action_precedes_information_and_final_section_has_exports():
    from ui_source import ui_method
    pages=ui_method('GuidedWindow', '_build_pages_tab')
    assert pages.index('actions = (') < pages.index('self.page_info = QPlainTextEdit()')
    for required in ('ui.pages.manage.tip','ui.pages.batch.tip','ui.pages.scope.tip','ui.pages.tei.tip'):
        assert required in pages
    final=ui_method('GuidedWindow', '_build_progress_tab')
    assert 'exportVariansJsonButton' in final
    assert 'exportVariansProjectButton' in final
    assert 'ui.final.audit.help' in final


def test_iiif_export_unchanged_by_gui_labels(tmp_path):
    p=fixture(tmp_path)
    original=project_fingerprint(p)
    from varians_synchro.varians_export import make_varians_alignments
    data,report=make_varians_alignments(p,'Mu')
    assert data['Mu']['meta']['format']=='tei-manuscript-alignment'
    assert project_fingerprint(p)==original
