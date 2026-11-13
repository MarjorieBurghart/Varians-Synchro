"""PAGE-XML / ALTO interoperability and project persistence."""
import json

import pytest

from varians_synchro.core import (new_project, create_witness, add_image_source,
    add_alto_source, inspect_line_source, save_project, load_project, check_alto_files)
from varians_synchro.imaging import (create_pages, bind_alto, mapped_alto_page,
    suggest_alto_bindings, import_htr_results)
from varians_synchro.physical_alignment import (physical_lines, create_pair_session,
    add_pair_link, pair_progress)
from varians_synchro.alto_geometry import page_line_polygons


PAGE = '''<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
 <Metadata><Creator>PERO OCR</Creator></Metadata>
 <Page imageFilename="folio_002r.jpg" imageWidth="1400" imageHeight="2000">
  <ReadingOrder><OrderedGroup id="ro"><RegionRefIndexed regionRef="right" index="1"/>
   <RegionRefIndexed regionRef="left" index="0"/></OrderedGroup></ReadingOrder>
  <TextRegion id="right"><Coords points="800,150 1300,150 1300,300 800,300"/>
   <TextLine id="line-r"><Coords points="820,180 1280,165 1280,195 820,210"/>
    <Baseline points="820,200 1280,185"/>
    <TextEquiv index="0" conf="0.85"><Unicode>Secunda pars</Unicode></TextEquiv>
   </TextLine></TextRegion>
  <TextRegion id="left"><Coords points="100,150 650,150 650,300 100,300"/>
   <TextLine id="line-l"><Coords points="110,180 620,155 625,187 115,210"/>
    <Baseline points="110,194 620,171"/>
    <TextEquiv index="1"><Unicode>Old alternative</Unicode></TextEquiv>
    <TextEquiv index="0"><Unicode>Prima pars</Unicode></TextEquiv>
   </TextLine></TextRegion>
 </Page>
</PcGts>'''
ALTO = '''<?xml version="1.0" encoding="utf-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
 <Layout><Page ID="folio_002r" WIDTH="1400" HEIGHT="2000">
 <PrintSpace><TextBlock><TextLine ID="a1" HPOS="110" VPOS="155" WIDTH="515" HEIGHT="55">
 <String CONTENT="Prima"/><SP/><String CONTENT="pars"/>
 </TextLine></TextBlock></PrintSpace></Page></Layout>
</alto>'''


def test_page_xml_polygon_htr_and_region_order(tmp_path):
    path = tmp_path / 'different_export_name.xml'
    path.write_text(PAGE, encoding='utf-8')
    src = inspect_line_source(path)
    assert src['kind'] == 'page'
    assert src['page_count'] == 1 and src['line_count'] == 2
    assert src['htr_line_count'] == 2
    page = src['pages'][0]
    assert page['image_filename'] == 'folio_002r.jpg'
    assert page['width'] == '1400' and page['height'] == '2000'
    assert [l['alto_id'] for l in page['lines']] == ['line-l', 'line-r']
    line = page['lines'][0]
    assert line['text'] == 'Prima pars'
    assert line['polygon'] == [[110,180],[620,155],[625,187],[115,210]]
    assert line['bbox'] == {'HPOS':110,'VPOS':155,'WIDTH':515,'HEIGHT':55}
    assert page['lines'][1]['text'] == 'Secunda pars'


def test_mixed_page_alto_pair_alignment_saved(tmp_path):
    left_file = tmp_path/'folio_002r.page.xml'
    right_file = tmp_path/'folio_002r.alto.xml'
    left_file.write_text(PAGE, encoding='utf-8')
    right_file.write_text(ALTO, encoding='utf-8')
    project = new_project('PAGE et ALTO')
    a = create_witness(project, 'P')
    b = create_witness(project, 'A')
    # Images are harmless inventory pointers (no image file is opened here).
    add_image_source(a, 'local', tmp_path/'folio_002r.jpg')
    add_image_source(b, 'local', tmp_path/'folio_002r.jpg')
    create_pages(a); create_pages(b)
    left_src = add_alto_source(a,left_file)
    right_src = add_alto_source(b,right_file)
    assert left_src['kind'] == 'page' and right_src['kind'] == 'alto'
    # PAGE's imageFilename matches the local image, even though source filename differs.
    proposal = suggest_alto_bindings(a)
    assert len(proposal) == 1
    assert proposal[0]['alto_source_id'] == left_src['id']
    for witness, src in [(a,left_src),(b,right_src)]:
        bind_alto(witness,witness['pages'][0]['id'],src['id'])
    assert mapped_alto_page(a,a['pages'][0])['line_count'] == 2
    polygons = page_line_polygons(a,a['pages'][0])
    assert len(polygons) == 2
    assert polygons[0] == [[110,180],[620,155],[625,187],[115,210]]
    a_lines = physical_lines(a); b_lines = physical_lines(b)
    assert len(a_lines) == 2 and len(b_lines) == 1
    session = create_pair_session(project,'P','A')
    add_pair_link(project,session,[a_lines[0]['id']],[b_lines[0]['id']])
    saved = tmp_path/'mixed.vsynch'
    save_project(project,saved)
    reloaded = load_project(saved)
    assert reloaded['pair_sessions'][0]['links'] == session['links']
    assert reloaded['witnesses'][0]['alto_sources'][0]['kind'] == 'page'
    assert pair_progress(reloaded,reloaded['pair_sessions'][0])['links'] == 1
    assert check_alto_files(reloaded) == []


def test_page_without_htr_and_missing_coords_is_reported(tmp_path):
    xml = PAGE.replace('<TextEquiv index="0"><Unicode>Prima pars</Unicode></TextEquiv>', '').replace('<TextEquiv index="1"><Unicode>Old alternative</Unicode></TextEquiv>', '')
    xml = xml.replace('<Coords points="820,180 1280,165 1280,195 820,210"/>', '')
    file = tmp_path/'page.xml'
    file.write_text(xml, encoding='utf-8')
    src = inspect_line_source(file)
    assert src['line_count'] == 1
    assert src['htr_line_count'] == 0
    assert src['pages'][0]['skipped_unsegmented_lines'] == 1


def test_page_and_alto_external_change_detection(tmp_path):
    xml = tmp_path / 'folio.xml'
    xml.write_text(PAGE,encoding='utf-8')
    p = new_project()
    w = create_witness(p,'P')
    add_alto_source(w,xml)
    assert check_alto_files(p) == []
    xml.write_text(PAGE.replace('Prima pars','Altered text'),encoding='utf-8')
    assert check_alto_files(p)


def test_wrong_source_rejected(tmp_path):
    f=tmp_path/'wrong.xml'; f.write_text('<TEI><text/></TEI>',encoding='utf-8')
    with pytest.raises(ValueError,match='ALTO ou PAGE'):
        inspect_line_source(f)


def test_old_alto_session_has_no_migration_side_effect(tmp_path):
    f=tmp_path/'alto.xml'; f.write_text(ALTO,encoding='utf-8')
    p=new_project()
    w=create_witness(p,'A')
    s=add_alto_source(w,f)
    assert s['kind'] == 'alto'
    s.pop('kind')  # V0.6.12 did not have source kind.
    path=tmp_path/'old.vsynch';save_project(p,path)
    result=load_project(path)
    assert result['witnesses'][0]['alto_sources'][0].get('kind','alto')=='alto'


def test_reimport_page_from_iiif_mapping(tmp_path):
    folder=tmp_path/'result';folder.mkdir()
    (folder/'export_0001.xml').write_text(PAGE,encoding='utf-8')
    p=new_project(); w=create_witness(p,'P')
    # Existing image identity comes from manifest canvas; no network necessary.
    w['pages']=[{'id':'canvas1','label':'folio 2r','image_kind':'iiif',
                 'canvas':{'index':0},'alto_binding':None}]
    mapping={'format':'varians-synchro-htr-export','witness':'P',
             'pages':[{'file':'export_0001.jpg','canvas_id':'canvas1'}]}
    file=tmp_path/'pages.json';file.write_text(json.dumps(mapping),encoding='utf-8')
    result=import_htr_results(w,file,folder)
    assert result['imported']==['canvas1']
    assert mapped_alto_page(w,w['pages'][0])['lines'][0]['polygon']

