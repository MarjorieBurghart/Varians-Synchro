"""Projet Varians sans édition TEI associée au pivot : Varians-Synchro y met
la même TEI vide que Varians pour une « transcription vierge ». Varians peut
ensuite y préparer les <pb/> et <lb/> du pivot (« Paramètres du projet »),
d'après les JSON d'alignement de Synchro, et chaque <lb/> trouve alors sa
ligne. Vérifié avec le vrai code de Varians (``varians_runtime``)."""
from __future__ import annotations

import re
import shutil

import pytest

from test_varians_094_compat import _project
from varians_runtime import open_in_varians, prepare_pivot_in_varians
from varians_synchro.reading_stream import reading_stream
from varians_synchro.varians_project_export import export_varians_project


@pytest.fixture
def exported(tmp_path):
    project = _project(tmp_path)
    project['text_resources'] = []            # aucune édition TEI
    destination = tmp_path / 'projet-varians'
    export_varians_project(project, 'Mu', destination)
    return project, destination


def test_the_blank_edition_is_the_one_varians_creates(exported):
    _project_, destination = exported
    prepared = prepare_pivot_in_varians(destination / 'project.xml')
    assert 'error' not in prepared, prepared.get('trace')
    assert prepared['empty'] and prepared['same_as_varians_blank']


def test_varians_opens_the_project(exported):
    _project_, destination = exported
    opened = open_in_varians(destination / 'project.xml')
    assert 'error' not in opened, opened.get('trace')
    assert set(opened['witnesses']) == {'Mu', 'F'}


@pytest.mark.parametrize('include_lb', [True, False])
def test_varians_prepares_the_pivot_from_the_synchro_lines(exported, tmp_path, include_lb):
    project, destination = exported
    prepared = prepare_pivot_in_varians(destination / 'project.xml', include_lb=include_lb)
    assert 'error' not in prepared, prepared.get('trace')
    mu = next(w for w in project['witnesses'] if w['id'] == 'Mu')
    pages = [page['label'] for page in mu['pages']]
    lines = reading_stream(mu)                 # lignes du pivot dans le périmètre
    assert [label for label, _count in prepared['pages']] == pages
    assert sum(count for _label, count in prepared['pages']) == len(lines)
    text = prepared['prepared']
    assert len(re.findall(r'<pb ', text)) == len(pages)
    assert len(re.findall(r'<lb ', text)) == (len(lines) if include_lb else 0)
    if include_lb:
        # Le projet, avec l'édition préparée : chaque <lb/> a sa ligne.
        copy = tmp_path / 'prepare'
        shutil.copytree(destination, copy)
        (copy / 'xml' / 'edition.xml').write_text(text, encoding='utf-8')
        opened = open_in_varians(copy / 'project.xml')
        assert 'error' not in opened, opened.get('trace')
        index = opened['pivot_lb_index']
        assert index['tei_lb_count'] == index['physical_line_count'] == len(lines)
        assert index['unmapped_lb_count'] == 0 and index['physical_without_lb'] == 0
