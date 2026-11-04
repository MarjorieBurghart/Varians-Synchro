"""Retirer un témoin ou une ressource enregistrée (moteur, sans Qt).

Décisions :
- les groupes qui touchent des lignes retirées sont gardés : ils deviennent
  périmés, comme après un changement de fichier ALTO/PAGE (exclus des calculs
  et de l'export ; l'utilisateur les dissocie ensuite) ;
- le témoin pivot ne peut pas être retiré tant qu'un autre témoin n'est pas
  choisi comme pivot ;
- aucun fichier n'est supprimé du disque ;
- tout ou rien : un retrait refusé ne change rien au projet.
"""
import copy
from pathlib import Path

import pytest

from varians_synchro.core import add_image_source
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.imaging import create_pages
from varians_synchro.physical_alignment import physical_lines, stale_link_ids
from varians_synchro.resource_removal import removal_impact, remove_resource, remove_witness
from test_stale_links import setting  # noqa: F401  (fixture)


def _witness(project, wid):
    return next((w for w in project['witnesses'] if w['id'] == wid), None)


def _tei(tmp_path, wid):
    path = tmp_path / f'{wid}.xml'
    path.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><lb/>x</p></body></text></TEI>',
                    encoding='utf-8')
    return path


def test_the_impact_of_removing_an_xml_file_counts_lines_and_groups(setting):
    project, a, _b, _session, _first, _last = setting
    source = a['alto_sources'][0]['id']
    impact = removal_impact(project, 'A', 'xml', source)
    assert impact == {'pages': 1, 'lines': len(physical_lines(a)), 'groups': 2, 'validated': 2, 'sessions': 0,
                      'ignored': 0}


def test_removing_an_xml_file_unbinds_its_pages_and_makes_their_groups_stale(setting):
    project, a, _b, session, first, last = setting
    source = a['alto_sources'][0]['id']
    path = Path(a['alto_sources'][0]['path'])
    remove_resource(project, 'A', 'xml', source)
    a = _witness(project, 'A')
    assert source not in {s['id'] for s in a['alto_sources']}
    assert a['pages'][0]['alto_binding'] is None
    assert physical_lines(a) == []
    session = project['pair_sessions'][0]
    assert {link['id'] for link in session['links']} == {first['id'], last['id']}   # gardés
    assert stale_link_ids(project, session) == {first['id'], last['id']}            # périmés
    assert path.is_file()                                                           # rien sur le disque


def test_removing_an_image_source_removes_its_pages(setting, tmp_path):
    project, a, _b, session, first, last = setting
    image = tmp_path / 'A-bis.jpg'
    image.write_bytes(b'image')
    add_image_source(a, 'local', str(image))
    create_pages(a)
    assert len(a['pages']) == 2
    first_source = a['image_sources'][0]['id']
    impact = removal_impact(project, 'A', 'images', first_source)
    assert (impact['pages'], impact['groups'], impact['validated']) == (1, 2, 2)
    remove_resource(project, 'A', 'images', first_source)
    a = _witness(project, 'A')
    assert [s['id'] for s in a['image_sources']] == [a['image_sources'][0]['id']] != [first_source]
    assert len(a['pages']) == 1 and a['pages'][0]['image_path'] == str(image)
    assert stale_link_ids(project, project['pair_sessions'][0]) == {first['id'], last['id']}


def test_removing_a_tei_edition(setting, tmp_path):
    project, *_ = setting
    resource = store_tei_reference(project, 'A', str(_tei(tmp_path, 'A')))
    assert removal_impact(project, 'A', 'tei', resource['id'])['groups'] == 0
    remove_resource(project, 'A', 'tei', resource['id'])
    assert project['text_resources'] == []


def test_removing_a_witness_removes_its_synchronisations_and_editions(setting, tmp_path):
    project, a, _b, _session, _first, _last = setting
    project['pivot_witness_id'] = 'A'
    store_tei_reference(project, 'B', str(_tei(tmp_path, 'B')))
    impact = removal_impact(project, 'B')
    assert impact['sessions'] == 1 and impact['groups'] == 2 and impact['validated'] == 2
    remove_witness(project, 'B')
    assert [w['id'] for w in project['witnesses']] == ['A']
    assert project['pair_sessions'] == [] and project['text_resources'] == []
    assert _witness(project, 'A')['pages'] == a['pages']


def test_the_pivot_cannot_be_removed(setting):
    project, *_ = setting
    project['pivot_witness_id'] = 'A'
    before = copy.deepcopy(project)
    with pytest.raises(ValueError, match='pivot'):
        remove_witness(project, 'A')
    assert project == before


def test_an_unknown_resource_changes_nothing(setting):
    project, *_ = setting
    before = copy.deepcopy(project)
    with pytest.raises(ValueError):
        remove_resource(project, 'A', 'xml', 'inconnue')
    with pytest.raises(ValueError):
        remove_witness(project, 'Z')
    assert project == before


def test_removing_a_resource_keeps_the_same_project_object(setting):
    """Les vues ouvertes partagent l'objet projet : il est mis à jour sur place."""
    project, a, *_ = setting
    identity = id(project)
    remove_resource(project, 'A', 'xml', a['alto_sources'][-1]['id'])
    assert id(project) == identity


def _alto(path, ids, texts):
    lines = ''.join(f'<TextLine ID="line_{i}" HPOS="10" VPOS="{j*30+1}" WIDTH="390" HEIGHT="19">'
                    f'<String CONTENT="{t}"/></TextLine>' for j, (i, t) in enumerate(zip(ids, texts)))
    path.write_text('<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Layout><Page ID="p" WIDTH="500" '
                    f'HEIGHT="800"><PrintSpace><TextBlock ID="b">{lines}</TextBlock></PrintSpace></Page></Layout>'
                    '</alto>', encoding='utf-8')
    return path


def _page_xml(path, ids, texts):
    lines = ''.join(f'<TextLine id="line_{i}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} '
                    f'10,{j*30+20}"/><TextEquiv><Unicode>{t}</Unicode></TextEquiv></TextLine>'
                    for j, (i, t) in enumerate(zip(ids, texts)))
    path.write_text('<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
                    '<Page imageFilename="x.jpg" imageWidth="500" imageHeight="800"><TextRegion id="r">'
                    f'<Coords points="1,1 490,1 490,700 1,700"/>{lines}</TextRegion></Page></PcGts>',
                    encoding='utf-8')
    return path


def test_removing_an_old_alto_counts_the_groups_the_export_would_lose(tmp_path):
    """Red team A5 : un témoin passé de l'ALTO au PAGE de PERO (mêmes UUID)
    garde ses groupes à l'export tant que l'ancien ALTO prouve la continuité.
    Le retrait de cet ALTO annonçait « 0 groupe » et l'export en perdait 3."""
    import uuid
    from varians_synchro.core import add_alto_source, add_image_source, create_witness, new_project
    from varians_synchro.imaging import bind_alto
    from varians_synchro.physical_alignment import add_pair_link, create_pair_session
    from varians_synchro.reading_stream import rebind_page
    from varians_synchro.varians_export import make_varians_alignments
    project = new_project('Essai')
    project['pivot_witness_id'] = 'A'
    data = {}
    for wid in 'AB':
        witness = create_witness(project, wid)
        image = tmp_path / f'{wid}.jpg'
        image.write_bytes(b'x')
        add_image_source(witness, 'local', str(image))
        create_pages(witness)
        data[wid] = ([str(uuid.uuid4()) for _ in range(3)], [f'{wid.lower()}{k}' for k in range(3)])
        add_alto_source(witness, _alto(tmp_path / f'{wid}.alto.xml', *data[wid]))
        bind_alto(witness, witness['pages'][0]['id'], witness['alto_sources'][0]['id'], 0)
    a, b = project['witnesses']
    session = create_pair_session(project, 'A', 'B')
    for k in range(3):
        add_pair_link(project, session, [physical_lines(a)[k]['id']], [physical_lines(b)[k]['id']])
    add_alto_source(b, _page_xml(tmp_path / 'B.page.xml', *data['B']))
    rebind_page(b, b['pages'][0]['id'], b['alto_sources'][-1]['id'], 0)
    assert make_varians_alignments(project, 'A')[1]['per_witness']['B']['exported_groups'] == 3
    impact = removal_impact(project, 'B', 'xml', b['alto_sources'][0]['id'])
    assert (impact['lines'], impact['groups']) == (0, 3)
