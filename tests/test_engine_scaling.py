"""Coût des moteurs sur un grand manuscrit (red team C1, C8).

- Enregistrer des propositions relisait toutes les lignes des deux témoins
  (identifiants, empreintes) pour chaque groupe : 3,5 minutes pour 3 000
  lignes, fenêtre figée. Les lignes sont désormais lues une fois par
  enregistrement.
- L'interpolation géométrique normalisait le texte HTR et le comparait pour
  chaque transition de son calcul : chaque morceau n'est normalisé qu'une
  fois, et une comparaison qui ne peut pas atteindre le seuil est écartée
  sans calcul complet (même résultat).

Les tests comptent les appels plutôt que de mesurer un temps."""
import random

import pytest

from varians_synchro import interpolation, physical_alignment
from varians_synchro.core import create_witness, new_project
from varians_synchro.physical_alignment import (add_pair_link, apply_pair_proposals, create_pair_session,
                                                physical_lines, replace_revisable_pair_proposals)
from varians_synchro.textual_progress import suggest_textual_progress

WORDS = ('dominus deus pater filius spiritus sanctus ecclesia rex regina miles terra caelum aqua '
         'ignis panis vinum liber scriptor monachus abbas frater soror mater virgo gratia').split()


def _lines(texts, pitch=40, height=29):
    return [{'alto_id': f'l{j}', 'region_id': 'r', 'text': text,
             'bbox': {'HPOS': '25', 'VPOS': str(j * pitch), 'WIDTH': '300', 'HEIGHT': str(height)}}
            for j, text in enumerate(texts)]


def _page(witness, page_id, lines, height=1600):
    source = f'{witness["id"]}_{page_id}'
    witness['alto_sources'].append({'id': source, 'path': f'/absent/{source}.xml', 'line_count': len(lines),
                                    'pages': [{'width': '1000', 'height': str(height), 'lines': lines,
                                               'line_count': len(lines)}]})
    witness['pages'].append({'id': page_id, 'label': page_id, 'image_kind': 'local',
                             'image_path': f'/absent/{page_id}.jpg',
                             'alto_binding': {'source_id': source, 'page_index': 0}})


def _project(pages, per_page):
    rng = random.Random(1)
    project = new_project('Essai')
    for wid in 'AB':
        witness = create_witness(project, wid)
        for number in range(pages):
            _page(witness, f'{wid}{number:03d}',
                  _lines([' '.join(rng.choice(WORDS) for _ in range(6)) for _ in range(per_page)]))
    session = create_pair_session(project, 'A', 'B')
    a, b = (physical_lines(w) for w in project['witnesses'])
    add_pair_link(project, session, [a[0]['id']], [b[0]['id']])
    add_pair_link(project, session, [a[-1]['id']], [b[-1]['id']])
    return project, session


@pytest.fixture
def counted(monkeypatch):
    calls = []
    original = physical_alignment.physical_lines

    def counting(witness):
        calls.append(witness['id'])
        return original(witness)
    monkeypatch.setattr(physical_alignment, 'physical_lines', counting)
    return calls


def test_saving_textual_proposals_reads_the_lines_once(counted):
    project, session = _project(5, 20)
    proposals = suggest_textual_progress(project, session)['proposals']
    assert len(proposals) > 50
    counted.clear()
    result = replace_revisable_pair_proposals(project, session, proposals)
    assert result['added'] == len(proposals)
    assert len(counted) <= 4, len(counted)


def test_saving_htr_proposals_reads_the_lines_once(counted):
    project, session = _project(3, 20)
    a, b = (physical_lines(w) for w in project['witnesses'])
    proposals = [{'reference_ids': [x['id']], 'target_ids': [y['id']], 'state': 'uncertain'}
                 for x, y in zip(a[1:-1], b[1:-1])]
    counted.clear()
    assert apply_pair_proposals(project, session, proposals) == {'added': len(proposals), 'skipped': 0}
    assert len(counted) <= 4, len(counted)


def test_saving_proposals_still_refuses_lines_already_linked():
    project, session = _project(1, 6)
    a, b = (physical_lines(w) for w in project['witnesses'])
    twice = [{'reference_ids': [a[1]['id']], 'target_ids': [b[1]['id']], 'state': 'uncertain'},
             {'reference_ids': [a[1]['id']], 'target_ids': [b[2]['id']], 'state': 'uncertain'},
             {'reference_ids': [a[0]['id']], 'target_ids': [b[3]['id']], 'state': 'uncertain'}]
    assert apply_pair_proposals(project, session, twice) == {'added': 1, 'skipped': 2}


def test_interpolation_normalises_each_piece_of_text_once(monkeypatch):
    rng = random.Random(3)
    texts = [' '.join(rng.choice(WORDS) for _ in range(8)) for _ in range(60)]
    project = new_project('Essai')
    for wid in 'AB':
        _page(create_witness(project, wid), f'{wid}1', _lines(texts, pitch=12, height=10), height=4000)
    session = create_pair_session(project, 'A', 'B')
    a, b = (physical_lines(w) for w in project['witnesses'])
    add_pair_link(project, session, [a[0]['id']], [b[0]['id']])
    add_pair_link(project, session, [a[-1]['id']], [b[-1]['id']])
    calls = []
    original = interpolation.normalize
    monkeypatch.setattr(interpolation, 'normalize', lambda text: calls.append(1) or original(text))
    outcome = interpolation.suggest_between_anchors(project, session, regenerate_automatic=True)
    assert outcome['proposals']
    assert len(calls) <= 6 * 2 * len(texts), len(calls)
