from varians_synchro.core import (add_image_source, create_witness, import_tei, inspect_alto, load_project,
                                  new_project, save_project)

def test_project_roundtrip(tmp_path):
    p = new_project('Test')
    w = create_witness(p, 'A')
    add_image_source(w, 'iiif', 'https://example.org/manifest')
    path = tmp_path / 'test.vsynch'
    save_project(p, path)
    assert load_project(path)['witnesses'][0]['id'] == 'A'

def test_alto(tmp_path):
    p = tmp_path / 'a.xml'
    p.write_text('<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="p1" WIDTH="100" HEIGHT="200"><PrintSpace><TextBlock><TextLine ID="l1" HPOS="1" VPOS="2" WIDTH="20" HEIGHT="5"><String CONTENT="Salve"/><String CONTENT="mundi"/></TextLine><TextLine ID="l2"/></TextBlock></PrintSpace></Page></Layout></alto>')
    result = inspect_alto(p)
    assert result['line_count'] == 2
    assert result['htr_line_count'] == 1
    assert result['pages'][0]['lines'][0]['text'] == 'Salve mundi'

def test_tei(tmp_path):
    src = tmp_path/'text.xml'
    src.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><pb n="1r" facs="#A-p1" edRef="#A"/><lb edRef="#A"/>Ave <hi>Maria</hi><lb edRef="#A"/>gratia plena.</p></body></text></TEI>')
    data = import_tei(new_project(), src, 'A')
    assert len(data['lines']) == 2
    assert data['lines'][0]['text'] == 'Ave Maria'
    assert data['lines'][1]['page_id'] == 'A-p1'

def test_validation():
    p = new_project(); create_witness(p,'A')
    try: create_witness(p,'A')
    except ValueError: pass
    else: assert False
