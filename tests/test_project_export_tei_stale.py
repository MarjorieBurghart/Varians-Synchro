"""« Exporter un projet Varians » refuse une liaison TEI du pivot périmée.

Red team A2 : la liaison TEI ↔ lignes du pivot validée, puis rendue périmée
(par exemple par une fausse manœuvre dans « Ordre de lecture »), l'export
réussissait et mettait les <lb/> de la TEI en face des mauvaises lignes,
sans que Varians puisse le voir. Décision : refuser, avec le motif."""
from pathlib import Path

import pytest

from varians_synchro.core import add_alto_source, add_image_source, create_witness, new_project
from varians_synchro.errors import localized_text
from varians_synchro.i18n import tr
from varians_synchro.imaging import bind_alto, create_pages
from varians_synchro.reading_stream import reading_stream, set_line_order
from varians_synchro.resource_workflow import store_tei_reference
from varians_synchro.tei_binding import apply_tei_binding, preview_tei_binding, tei_binding_status
from varians_synchro.varians_project_export import export_varians_project

PAGE = ('<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">'
        '<Page imageFilename="x.jpg" imageWidth="500" imageHeight="800"><TextRegion id="r">'
        '<Coords points="1,1 490,1 490,700 1,700"/>{lines}</TextRegion></Page></PcGts>')


def _project(tmp_path):
    project = new_project('Essai')
    for wid, texts in (('A', ['un', 'deux', 'trois']), ('B', ['b1', 'b2', 'b3'])):
        witness = create_witness(project, wid)
        image = tmp_path / f'{wid}.jpg'
        image.write_bytes(b'\xff\xd8\xffimage')
        add_image_source(witness, 'local', str(image))
        xml = tmp_path / f'{wid}.xml'
        xml.write_text(PAGE.format(lines=''.join(
            f'<TextLine id="{wid}{j}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} 10,{j*30+20}"/>'
            f'<TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>' for j, text in enumerate(texts))),
            encoding='utf-8')
        add_alto_source(witness, xml)
        create_pages(witness)
        bind_alto(witness, witness['pages'][0]['id'], witness['alto_sources'][0]['id'], 0)
    project['pivot_witness_id'] = 'A'
    tei = tmp_path / 'edition.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text><body><p><lb edRef="#A"/>un '
                   '<lb edRef="#A"/>deux <lb edRef="#A"/>trois</p></body></text></TEI>', encoding='utf-8')
    resource = store_tei_reference(project, 'A', str(tei))
    apply_tei_binding(project, 'A', resource['id'], preview_tei_binding(project, 'A', resource['id']))
    return project, resource


def test_a_valid_tei_binding_is_exported(tmp_path):
    project, resource = _project(tmp_path)
    assert tei_binding_status(project, 'A', resource['id'])['status'] == 'valid'
    export_varians_project(project, 'A', tmp_path / 'out')
    assert (tmp_path / 'out' / 'project.xml').is_file()


def test_a_stale_tei_binding_of_the_pivot_refuses_the_export(tmp_path):
    project, resource = _project(tmp_path)
    witness = project['witnesses'][0]
    ids = [line['id'] for line in reading_stream(witness, include_ignored=True)]
    set_line_order(witness, witness['pages'][0]['id'], [ids[0], ids[2], ids[1]])
    assert tei_binding_status(project, 'A', resource['id'])['status'] == 'stale'
    with pytest.raises(ValueError) as refused:
        export_varians_project(project, 'A', tmp_path / 'out')
    assert localized_text(refused.value) == tr('error.project_export.tei_binding_stale', witness='A')
    assert not (tmp_path / 'out').exists()
