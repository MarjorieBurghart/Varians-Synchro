"""Projet exporté pour Varians : il s'ouvre dans Varians (version
``VARIANS_VERIFIED_VERSION``, celle que la CI récupère), dans sa vraie fenêtre
aussi, et Varians y lit exactement les lignes que Varians-Synchro a préparées.

Le projet d'essai est réaliste :
- le pivot Mu (images locales, PAGE XML) a une ligne hors périmètre et une
  page dont l'ordre de lecture a été corrigé à la main ;
- le témoin F (images IIIF) a un Canvas sans segmentation (une garde), à
  côté de deux pages segmentées, liées à Mu par des correspondances validées.

Le projet est ouvert avec le vrai code de Varians (``varians_runtime``).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from varians_synchro.core import new_project, create_witness, add_image_source, add_alto_source
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.line_scope import update_ignored_lines
from varians_synchro.physical_alignment import create_pair_session, add_pair_link, physical_lines
from varians_synchro.reading_stream import reading_stream, set_line_order
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.varians_project_export import (VARIANS_VERIFIED_VERSION, export_varians_project,
                                                    _cache_varians_manifest)
from varians_runtime import open_in_varians, open_in_varians_window

ROOT = Path(__file__).resolve().parents[1]

PAGE = '''<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
<Page imageFilename="{image}" imageWidth="500" imageHeight="800">
<TextRegion id="r"><Coords points="1,1 490,1 490,600 1,600"/>
{lines}
</TextRegion></Page></PcGts>'''
TEI = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>{}</p></body></text></TEI>'
MANIFEST = 'https://example.org/F/manifest.json'


def _page_xml(path, image, texts):
    lines = ''.join(
        f'<TextLine id="{path.stem}_{j}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} '
        f'10,{j*30+20}"/><TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>'
        for j, text in enumerate(texts))
    path.write_text(PAGE.format(image=image, lines=lines), encoding='utf-8')
    return path


def _line(witness, text):
    return next(line['id'] for line in physical_lines(witness) if line['text'] == text)


def _project(tmp_path):
    project = new_project('Essai')
    mu, f = create_witness(project, 'Mu'), create_witness(project, 'F')
    for i, texts in enumerate((('Mu a1', 'Mu a2', 'Mu a3'), ('Mu b1', 'Mu b2'))):
        image = tmp_path / f'mu{i}.jpg'
        image.write_bytes(b'image')
        add_image_source(mu, 'local', str(image))
        add_alto_source(mu, _page_xml(tmp_path / f'mu{i}.xml', image.name, texts))
    create_pages(mu)
    for page, source in zip(mu['pages'], mu['alto_sources']):
        bind_alto(mu, page['id'], source['id'], 0)

    source = add_image_source(f, 'iiif', MANIFEST)
    source['manifest'] = {'label': 'F', 'canvases': [
        {'id': f'https://example.org/F/canvas/{n}', 'label': n, 'width': 500, 'height': 800,
         'image_service': f'https://example.org/iiif/F-{n}', 'iiif_image_version': 2}
        for n in ('garde', '1r', '1v')]}
    create_pages(f)
    for page, texts in zip(f['pages'][1:], (('F a1', 'F a3'), ('F b1', 'F b2'))):
        add_alto_source(f, _page_xml(tmp_path / f'F-{page["label"]}.xml', page['label'], texts))
        bind_alto(f, page['id'], f['alto_sources'][-1]['id'], 0)

    # Une ligne hors du périmètre étudié ; un ordre de lecture corrigé.
    update_ignored_lines(project, {'Mu': [_line(mu, 'Mu a2')]})
    second = mu['pages'][1]['id']
    set_line_order(mu, second, [_line(mu, 'Mu b2'), _line(mu, 'Mu b1')])

    session = create_pair_session(project, 'Mu', 'F')
    for a, b in (('Mu a1', 'F a1'), ('Mu a3', 'F a3'), ('Mu b2', 'F b2'), ('Mu b1', 'F b1')):
        add_pair_link(project, session, [_line(mu, a)], [_line(f, b)])

    edition = tmp_path / 'edition.xml'
    edition.write_text(TEI.format(''.join(
        f'<lb edRef="#Mu"/>{text} ' for text in ('a1', 'a3', 'b2', 'b1'))), encoding='utf-8')
    store_tei_reference(project, 'Mu', edition)
    return project


@pytest.fixture
def exported(tmp_path):
    project = _project(tmp_path)
    destination = tmp_path / 'projet-varians'
    export_varians_project(project, 'Mu', destination)
    return project, destination


def test_the_project_opens_even_with_an_unsegmented_iiif_canvas(exported):
    project, destination = exported
    # Le cache du Manifest est écrit par Varians dès que l'on enregistre les
    # paramètres du projet (et par Varians-Synchro avec des copies HD).
    f = next(w for w in project['witnesses'] if w['id'] == 'F')
    _cache_varians_manifest(f['image_sources'][0], destination, 'F')
    opened = open_in_varians(destination / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    assert set(opened['witnesses']) == {'Mu', 'F'}


def test_varians_reads_the_pivot_lines_of_synchro_in_reading_order(exported):
    project, destination = exported
    opened = open_in_varians(destination / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    mu = next(w for w in project['witnesses'] if w['id'] == 'Mu')
    expected = [line['text'] for line in reading_stream(mu)]
    assert expected == ['Mu a1', 'Mu a3', 'Mu b2', 'Mu b1']
    assert opened['witnesses']['Mu']['texts'] == expected
    # Chaque <lb edRef="#Mu"/> de l'édition a sa ligne, et une seule.
    index = opened['pivot_lb_index']
    assert index['tei_lb_count'] == index['physical_line_count'] == 4
    assert index['unmapped_lb_count'] == 0 and index['physical_without_lb'] == 0


def test_the_links_of_the_other_witnesses_point_to_lines_of_the_pivot(exported):
    _project_, destination = exported
    opened = open_in_varians(destination / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    pivot = opened['witnesses']['Mu']
    assert opened['witnesses']['F']['base_keys']
    assert set(opened['witnesses']['F']['base_keys']) <= set(pivot['keys'])
    by_key = dict(zip(pivot['keys'], pivot['texts']))
    assert sorted(by_key[key] for key in opened['witnesses']['F']['base_keys']) == \
        ['Mu a1', 'Mu a3', 'Mu b1', 'Mu b2']


def test_the_project_opens_in_the_varians_window(exported):
    project, destination = exported
    f = next(w for w in project['witnesses'] if w['id'] == 'F')
    _cache_varians_manifest(f['image_sources'][0], destination, 'F')
    opened = open_in_varians_window(destination / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    if os.environ.get('VARIANS_REF'):                    # la CI : la version récupérée
        assert 'v' + opened['version'] == os.environ['VARIANS_REF']
    assert 'Essai' in opened['title'] and 'edition.xml' in opened['title']
    assert opened['panels'] == ['F', 'Mu']
    assert opened['edition'].count('<lb edRef="#Mu"/>') == 4      # l'édition est dans l'éditeur
    assert opened['dialogs'] == []                       # aucune boîte à l'ouverture


def test_the_ci_opens_the_exports_with_the_version_the_report_names(exported):
    _project_, destination = exported
    workflow = (ROOT / '.github' / 'workflows' / 'tests.yml').read_text(encoding='utf-8')
    ref = re.search(r'^ +VARIANS_REF: v(\S+)$', workflow, re.MULTILINE).group(1)
    assert ref == VARIANS_VERIFIED_VERSION == '0.9.4.6'
    report = (destination / 'RAPPORT_EXPORT_VARIANS.txt').read_text(encoding='utf-8')
    assert f'vérifié avec Varians {VARIANS_VERIFIED_VERSION}' in report


@pytest.mark.parametrize('document', [
    'README.md', 'docs/developer/EXPORT_VARIANS.md', 'docs/developer/ARCHITECTURE.md',
    'MAINTENANCE_PASSATION_V0856/08_EXPORT_VERS_VARIANS.md',
    'MAINTENANCE_PASSATION_V0856/12_RISQUES_ET_LIMITES.md', 'varians_synchro/varians_export.py'])
def test_the_documentation_names_the_verified_version(document):
    text = (ROOT / document).read_text(encoding='utf-8').replace('**', '')
    assert f'Varians {VARIANS_VERIFIED_VERSION}' in text
    assert 'Varians 0.9.4.0' not in text
