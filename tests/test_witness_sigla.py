"""Sigles des témoins : comme dans Varians (red team A4, B7, D5).

Un sigle comme « BnF lat. 123 » ou « Ms.12 » était accepté à la création,
puis refusé par les deux exports (point interdit), sans moyen de le
corriger : le sigle entre dans l'identifiant de chaque ligne. Décision :
les sigles sont libres, comme dans Varians ; les exports en tirent
l'identifiant XML par la même règle que Varians (« BnF lat. 123 » →
« BnF_lat._123 ») et gardent le sigle pour l'affichage. Deux sigles qui
donneraient le même identifiant ou le même nom de fichier sont refusés dès la
création. « Ajouter un témoin » avec un sigle déjà pris ne complète plus le
témoin existant en silence.
"""
import importlib.util
import json
import xml.etree.ElementTree as ET
import zipfile

import pytest

from varians_synchro.core import add_alto_source, add_image_source, create_witness, new_project
from varians_synchro.errors import localized_text
from varians_synchro.i18n import tr
from varians_synchro.imaging import bind_alto, create_pages
from varians_synchro.physical_alignment import add_pair_link, create_pair_session, physical_lines
from varians_synchro.resource_workflow import apply_witness_draft
from varians_synchro.tei_binding import extract_witness_tei
from varians_synchro.varians_export import export_varians_alignments
from varians_synchro.varians_project_export import export_varians_project
from varians_synchro.witness_ids import witness_id_for_siglum
from varians_runtime import open_in_varians, varians_source

PAGE = ('<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
        '<Page imageFilename="x.jpg" imageWidth="500" imageHeight="800"><TextRegion id="r">'
        '<Coords points="1,1 490,1 490,700 1,700"/>{lines}</TextRegion></Page></PcGts>')
PIVOT, OTHER = 'BnF lat. 123', 'Ms.12'


@pytest.mark.parametrize('siglum, identifier', [
    ('A', 'A'), ('Ms.12', 'Ms.12'), ('BnF lat. 123', 'BnF_lat._123'), ('1760', '_1760'),
    ('T 2', 'T_2'), ('../../x', '_.._.._x'), ('  ', '')])
def test_the_identifier_follows_the_rule_of_varians(siglum, identifier):
    assert witness_id_for_siglum(siglum) == identifier
    source = varians_source()
    if source is not None:
        spec = importlib.util.spec_from_file_location('varians_witness_ids', source / 'witness_ids.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.witness_id_for_siglum(siglum) == identifier


@pytest.mark.parametrize('first, second', [('T 2', 'T_2'), ('a', 'A'), ('Ms 1', 'ms_1')])
def test_two_sigla_that_would_give_the_same_file_are_refused(first, second):
    project = new_project('Essai')
    create_witness(project, first)
    with pytest.raises(ValueError) as refused:
        create_witness(project, second)
    assert localized_text(refused.value) == tr('error.witness.siglum_conflict', witness=second, other=first)


@pytest.mark.parametrize('siglum', ['CON', 'nul', 'Com1'])
def test_a_siglum_windows_cannot_use_as_a_file_name_is_refused(siglum):
    with pytest.raises(ValueError) as refused:
        create_witness(new_project('Essai'), siglum)
    assert localized_text(refused.value) == tr('error.witness.siglum_reserved', witness=siglum)


def test_adding_a_witness_with_a_siglum_already_used_is_refused():
    project = new_project('Essai')
    create_witness(project, 'A', 'Premier manuscrit')
    with pytest.raises(ValueError) as refused:
        apply_witness_draft(project, identifier='A', label='Nouveau manuscrit', new_witness=True)
    assert localized_text(refused.value) == tr('error.witness.siglum_taken', witness='A')
    assert project['witnesses'][0]['label'] == 'Premier manuscrit'


def _project(tmp_path):
    project = new_project('Essai')
    for wid, texts in ((PIVOT, ['un', 'deux']), (OTHER, ['b1', 'b2'])):
        witness = create_witness(project, wid)
        image = tmp_path / f'{len(project["witnesses"])}.jpg'
        image.write_bytes(b'\xff\xd8\xffimage')
        add_image_source(witness, 'local', str(image))
        xml = tmp_path / f'{len(project["witnesses"])}.xml'
        xml.write_text(PAGE.format(lines=''.join(
            f'<TextLine id="l{j}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} 10,{j*30+20}"/>'
            f'<TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>' for j, text in enumerate(texts))),
            encoding='utf-8')
        add_alto_source(witness, xml)
        create_pages(witness)
        bind_alto(witness, witness['pages'][0]['id'], witness['alto_sources'][0]['id'], 0)
    project['pivot_witness_id'] = PIVOT
    a, b = (physical_lines(w) for w in project['witnesses'])
    session = create_pair_session(project, PIVOT, OTHER)
    for x, y in zip(a, b):
        add_pair_link(project, session, [x['id']], [y['id']])
    return project


def test_the_json_export_accepts_sigla_with_a_dot(tmp_path):
    export_varians_alignments(_project(tmp_path), PIVOT, tmp_path / 'out')
    assert sorted(p.name for p in (tmp_path / 'out' / 'validated').iterdir()) == \
        ['BnF_lat._123.json', 'Ms.12.json']


def test_the_project_export_gives_varians_identifiers_and_keeps_the_sigla(tmp_path):
    export_varians_project(_project(tmp_path), PIVOT, tmp_path / 'out')
    root = ET.parse(tmp_path / 'out' / 'project.xml').getroot()
    witnesses = root.find('witnesses')
    assert witnesses.get('base') == 'BnF_lat._123'
    assert [(w.get('id'), w.get('siglum'), w.get('alignment')) for w in witnesses] == [
        ('BnF_lat._123', PIVOT, 'alignments/BnF_lat._123.json'), ('Ms.12', None, 'alignments/Ms.12.json')]
    assert json.loads((tmp_path / 'out' / 'alignments' / 'BnF_lat._123.json').read_text())['pages']
    tei = (tmp_path / 'out' / 'xml' / 'edition.xml').read_text(encoding='utf-8')
    assert '<witness xml:id="BnF_lat._123"><idno type="siglum">BnF lat. 123</idno>BnF lat. 123</witness>' in tei


def test_varians_opens_a_project_whose_sigla_have_dots_and_spaces(tmp_path):
    export_varians_project(_project(tmp_path), PIVOT, tmp_path / 'out')
    opened = open_in_varians(tmp_path / 'out' / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    assert set(opened['witnesses']) == {'BnF_lat._123', 'Ms.12'}
    assert opened['witnesses']['BnF_lat._123']['texts'] == ['un', 'deux']
    assert opened['witnesses']['Ms.12']['base_keys']


def test_the_tei_of_a_pivot_names_it_by_its_xml_identifier(tmp_path):
    tei = tmp_path / 'edition.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><lb edRef="#BnF_lat._123"/>un '
                   '<lb edRef="#BnF_lat._123"/>deux</p></body></text></TEI>', encoding='utf-8')
    assert [line['text'] for line in extract_witness_tei(tei, PIVOT)['lines']] == ['un', 'deux']


def test_the_zip_for_an_htr_names_its_images_safely(tmp_path, monkeypatch):
    from varians_synchro import imaging
    project = new_project('Essai')
    witness = create_witness(project, '../../Startup/x')
    witness['image_sources'].append({'id': 'iiif', 'kind': 'iiif', 'reference': 'https://example.org/m',
                                     'status': 'inspected', 'manifest': {'canvases': [
                                         {'id': 'c1', 'label': '1r', 'image_service': 'https://example.org/i/1',
                                          'iiif_image_version': 2, 'width': 100, 'height': 100}]}})
    create_pages(witness)
    monkeypatch.setattr(imaging, 'image_bytes', lambda page, width: b'\xff\xd8\xffimage')
    imaging.export_iiif_htr_zip(witness, [witness['pages'][0]['id']], str(tmp_path / 'htr.zip'))
    names = zipfile.ZipFile(tmp_path / 'htr.zip').namelist()
    assert names and all('/' not in name and '\\' not in name for name in names)
