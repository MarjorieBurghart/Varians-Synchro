"""PAGE à structure imbriquée (red team C4, C5).

- Un ReadingOrder à groupes imbriqués (OCR-D, Aletheia) était aplati et trié
  sur des index propres à chaque groupe : régions lues dans le désordre.
- Une TextRegion dans une autre comptait deux fois les lignes de la région
  intérieure.

Décision : corriger pour les nouveaux imports ; l'audit signale les sources
déjà importées que la nouvelle lecture verrait autrement, sans les modifier.
"""
import copy

from varians_synchro.core import add_alto_source, create_witness, new_project
from varians_synchro.imaging import bind_alto
from varians_synchro.page_xml import inspect_page_xml
from varians_synchro.validation import audit_project

NS = 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'


def _line(i, y):
    return (f'<TextLine id="l{i}"><Coords points="10,{y} 400,{y} 400,{y+20} 10,{y+20}"/>'
            f'<TextEquiv><Unicode>ligne {i}</Unicode></TextEquiv></TextLine>')


def _region(rid, y, inner=''):
    return f'<TextRegion id="{rid}"><Coords points="1,{y} 490,{y} 490,{y+60} 1,{y+60}"/>{inner}</TextRegion>'


def _page(body):
    return f'<PcGts xmlns="{NS}"><Page imageFilename="p.jpg" imageWidth="500" imageHeight="800">{body}</Page></PcGts>'


NESTED_ORDER = ('<ReadingOrder><OrderedGroup id="ro">'
                '<RegionRefIndexed index="0" regionRef="r1"/><RegionRefIndexed index="1" regionRef="r2"/>'
                '<RegionRefIndexed index="2" regionRef="r3"/>'
                '<OrderedGroupIndexed id="g" index="3"><RegionRefIndexed index="0" regionRef="r4"/>'
                '<RegionRefIndexed index="1" regionRef="r5"/></OrderedGroupIndexed>'
                '</OrderedGroup></ReadingOrder>')


def test_a_nested_reading_order_is_read_group_by_group(tmp_path):
    path = tmp_path / 'p.xml'
    path.write_text(_page(NESTED_ORDER + ''.join(_region(f'r{k}', 100 * k, _line(k, 100 * k + 5))
                                                 for k in (5, 3, 1, 4, 2))), encoding='utf-8')
    lines = inspect_page_xml(path)['pages'][0]['lines']
    assert [line['region_id'] for line in lines] == ['r1', 'r2', 'r3', 'r4', 'r5']


def test_a_region_inside_another_does_not_count_its_lines_twice(tmp_path):
    path = tmp_path / 'p.xml'
    path.write_text(_page(_region('outer', 0, _line(1, 5) + _region('inner', 30, _line(2, 35)) + _line(3, 70))),
                    encoding='utf-8')
    lines = inspect_page_xml(path)['pages'][0]['lines']
    assert [(line['alto_id'], line['region_id']) for line in lines] == \
        [('l1', 'outer'), ('l3', 'outer'), ('l2', 'inner')]


def test_the_audit_names_a_source_read_otherwise_now(tmp_path):
    path = tmp_path / 'p.xml'
    path.write_text(_page(_region('outer', 0, _line(1, 5) + _region('inner', 30, _line(2, 35)))),
                    encoding='utf-8')
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    witness['pages'].append({'id': 'p1', 'label': '1r', 'image_kind': 'local', 'image_path': str(tmp_path / 'p.jpg'),
                             'alto_binding': None})
    source = add_alto_source(witness, path)
    bind_alto(witness, 'p1', source['id'], 0)
    assert not [m for m in audit_project(project, check_paths=True)['messages']
                if m['code'] == 'xml_source_read_otherwise']
    # Projet importé avant la correction : la ligne intérieure figurait deux fois.
    old = source['pages'][0]['lines']
    source['pages'][0]['lines'] = [old[0], old[1], copy.deepcopy(old[1])]
    found = [m for m in audit_project(project, check_paths=True)['messages']
             if m['code'] == 'xml_source_read_otherwise']
    assert len(found) == 1 and found[0]['witness'] == 'A' and found[0]['detail'] == 'p.xml'
