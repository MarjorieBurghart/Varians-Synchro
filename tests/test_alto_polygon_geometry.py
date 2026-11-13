"""Regression tests: PERO-shaped TextLines vs oversized rectangular envelopes."""
from pathlib import Path
from varians_synchro.alto_geometry import (
    parse_alto_points, polygon_contains, page_line_polygons, textline_polygon)
from varians_synchro.core import new_project, create_witness, add_alto_source
from varians_synchro.imaging import bind_alto
from varians_synchro.overlay_selection import choose_line_geometry
import xml.etree.ElementTree as ET


SOURCE = '''<?xml version="1.0" encoding="utf-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout>
<Page ID="p1" WIDTH="1200" HEIGHT="1400"><PrintSpace>
<TextBlock ID="b1">
<TextLine ID="l1" HPOS="100" VPOS="100" WIDTH="820" HEIGHT="100"><Shape><Polygon POINTS="100,100 920,160 920,185 100,125"/></Shape><String CONTENT="prima"/></TextLine>
<TextLine ID="l2" HPOS="100" VPOS="145" WIDTH="820" HEIGHT="110"><Shape><Polygon POINTS="100 155 920 215 920 240 100 180"/></Shape><String CONTENT="secunda"/></TextLine>
</TextBlock></PrintSpace></Page></Layout></alto>'''


def _setup(tmp_path):
    path = tmp_path/'pero.xml'
    path.write_text(SOURCE, encoding='utf-8')
    project = new_project('geom')
    witness = create_witness(project,'A')
    src = add_alto_source(witness,path)
    witness['pages'] = [{'id':'canvas-1','label':'1r','alto_binding':None}]
    bind_alto(witness,'canvas-1',src['id'])
    return witness,witness['pages'][0],src


def test_polygon_parser_accepts_both_point_conventions():
    assert parse_alto_points('10,20 50,20 50,30 10,30') == [[10,20],[50,20],[50,30],[10,30]]
    assert parse_alto_points('10 20 50 20 50 30 10 30') == [[10,20],[50,20],[50,30],[10,30]]
    assert parse_alto_points('10,20 50,20') == []
    assert parse_alto_points('10,10 20,20 30,30') == []
    assert parse_alto_points(None) == []


def test_polygon_import_preserves_shape_and_existing_bbox(tmp_path):
    witness,page,src = _setup(tmp_path)
    lines = src['pages'][0]['lines']
    assert len(lines) == 2
    assert lines[0]['bbox']['HEIGHT'] == '100'
    assert lines[0]['polygon'] == [[100,100],[920,160],[920,185],[100,125]]
    assert lines[0]['text'] == 'prima'


def test_old_project_without_polygons_recovers_from_original_alto(tmp_path):
    witness,page,src = _setup(tmp_path)
    expected = [line.pop('polygon') for line in src['pages'][0]['lines']]
    assert page_line_polygons(witness,page) == expected
    assert 'polygon' not in src['pages'][0]['lines'][0]  # no in-place project mutation


def test_recovery_refuses_different_source_lines(tmp_path):
    witness,page,src = _setup(tmp_path)
    src['pages'][0]['lines'][0].pop('polygon')
    src['pages'][0]['lines'][1].pop('polygon')
    src['pages'][0]['lines'][0]['alto_id'] = 'different'
    assert page_line_polygons(witness,page)[0] is None
    assert page_line_polygons(witness,page)[1]


def test_missing_source_gracefully_falls_back_to_envelopes(tmp_path):
    witness,page,src = _setup(tmp_path)
    for line in src['pages'][0]['lines']:
        line.pop('polygon')
    Path(src['path']).unlink()
    assert page_line_polygons(witness,page) == [None,None]


def test_polygon_geometry_resolves_overlapping_envelopes():
    # Bounding boxes overlap strongly, but the diagonal polygons do not.
    geometry = [
        (0, 100, 100, 820, 100, [[100,100],[920,160],[920,185],[100,125]]),
        (1, 100, 145, 820, 110, [[100,155],[920,215],[920,240],[100,180]]),
    ]
    assert choose_line_geometry((500, 147), geometry) == 0
    assert choose_line_geometry((500, 195), geometry) == 1
    # Between the actual lines: do NOT pick a bounding box as if it were ink.
    assert choose_line_geometry((500, 170), geometry) is None
    # Rectangle fallback is used only when a source has no polygon.
    assert choose_line_geometry((500, 170), [(*geometry[1][:5], None)]) == 1


def test_polygon_boundary_and_exclusion():
    polygon = [[0,0],[10,0],[10,10],[0,10]]
    assert polygon_contains((5,5),polygon)
    assert polygon_contains((0,5),polygon)
    assert not polygon_contains((11,5),polygon)


def test_direct_shape_only_ignores_nested_word_shapes():
    element = ET.fromstring('<TextLine><String><Shape><Polygon POINTS="0 0 50 0 50 20 0 20"/></Shape></String></TextLine>')
    assert textline_polygon(element) == []
