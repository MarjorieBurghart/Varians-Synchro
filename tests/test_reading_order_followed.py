"""L'ordre de lecture corrigé est suivi partout (red team A3, C2).

- Proposition HTR–HTR : elle parcourait les pages dans leur ordre
  d'enregistrement et ignorait l'ordre des régions et des lignes corrigé.
  Des feuillets reliés dans le désordre, remis en ordre, donnaient
  « Ancrages non monotones » et aucune proposition, ou des propositions
  fausses.
- Ordre des régions : déplacer une région effaçait sans prévenir l'ordre des
  lignes corrigé sur la même page. Il est désormais retrié selon le nouvel
  ordre des régions, l'ordre des lignes de chaque région étant gardé."""
import random

from varians_synchro.core import create_witness, new_project
from varians_synchro.physical_alignment import add_pair_link, create_pair_session, suggest_htr_pair_alignment
from varians_synchro.reading_stream import reading_stream, set_line_order, set_page_order, set_region_order

WORDS = ('dominus deus pater filius spiritus sanctus ecclesia rex regina miles terra caelum aqua ignis '
         'panis vinum liber scriptor monachus abbas frater soror mater virgo gratia gloria pax lux').split()


def _page(witness, page_id, lines):
    source = f'{witness["id"]}_{page_id}'
    witness['alto_sources'].append({'id': source, 'path': f'/absent/{source}.xml', 'pages': [
        {'width': '1000', 'height': '1600', 'line_count': len(lines), 'lines': [
            {'alto_id': f'{region}.{j}', 'region_id': region, 'text': text,
             'bbox': {'HPOS': '25', 'VPOS': str(40 * j), 'WIDTH': '300', 'HEIGHT': '29'}}
            for j, (region, text) in enumerate(lines)]}]})
    witness['pages'].append({'id': page_id, 'label': page_id, 'image_kind': 'local',
                             'image_path': f'/absent/{page_id}.jpg',
                             'alto_binding': {'source_id': source, 'page_index': 0}})


def _texts(count, seed=7):
    rng = random.Random(seed)
    return [' '.join(rng.choice(WORDS) for _ in range(7)) for _ in range(count)]


def _anchored(project, a, b):
    session = create_pair_session(project, 'A', 'B')
    la, lb = reading_stream(a), reading_stream(b)
    add_pair_link(project, session, [la[0]['id']], [lb[0]['id']])
    add_pair_link(project, session, [la[-1]['id']], [lb[-1]['id']])
    return session


def _right(project, outcome):
    text = {line['id']: line['text'] for w in project['witnesses'] for line in reading_stream(w)}
    return [[text[i] for i in p['reference_ids']] == [text[i] for i in p['target_ids']]
            for p in outcome['proposals']]


def test_htr_proposals_follow_the_corrected_page_order():
    texts = _texts(90)
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    for k in range(3):
        _page(a, f'A{k}', [('r', t) for t in texts[30 * k:30 * k + 30]])
    for k, chunk in enumerate((texts[30:60], texts[60:90], texts[0:30])):     # reliés dans le désordre
        _page(b, f'B{k}', [('r', t) for t in chunk])
    set_page_order(b, ['B2', 'B0', 'B1'])
    session = _anchored(project, a, b)
    outcome = suggest_htr_pair_alignment(project, session)
    assert not any('monotone' in str(w) for w in outcome['warnings'])
    assert len(outcome['proposals']) > 40 and all(_right(project, outcome))


def test_htr_proposals_follow_the_corrected_region_order():
    texts = _texts(40, seed=3)
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    _page(a, 'A0', [('c1', t) for t in texts[:20]] + [('c2', t) for t in texts[20:]])
    _page(b, 'B0', [('c2', t) for t in texts[20:]] + [('c1', t) for t in texts[:20]])   # colonnes inversées
    set_region_order(b, 'B0', ['c1', 'c2'])
    session = _anchored(project, a, b)
    outcome = suggest_htr_pair_alignment(project, session)
    assert not any('monotone' in str(w) for w in outcome['warnings'])
    assert len(outcome['proposals']) > 15 and all(_right(project, outcome))


def test_moving_a_region_keeps_the_corrected_line_order():
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    _page(witness, 'p', [('main', 'texte 1'), ('main', 'ajout interlinéaire'), ('main', 'texte 2'),
                         ('marge', 'glose')])
    ids = {line['text']: line['id'] for line in reading_stream(witness)}
    set_line_order(witness, 'p', [ids['texte 1'], ids['texte 2'], ids['ajout interlinéaire'], ids['glose']])
    set_region_order(witness, 'p', ['marge', 'main'])
    assert [line['text'] for line in reading_stream(witness)] == \
        ['glose', 'texte 1', 'texte 2', 'ajout interlinéaire']


def test_the_pair_window_follows_a_reading_order_changed_from_it(monkeypatch):
    """Red team D11 : après « Ordre de lecture et intervalles… », Maj+clic
    dans la fenêtre de synchronisation suivait encore l'ancien ordre."""
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    import pytest
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from varians_synchro import ui_pair
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    _page(a, 'A0', [('r', f'a{k}') for k in range(4)])
    _page(b, 'B0', [('r', f'b{k}') for k in range(4)])
    session = create_pair_session(project, 'A', 'B')

    def reverse_lines(dialog):
        ids = [line['id'] for line in reading_stream(a, include_ignored=True)]
        set_line_order(a, 'A0', ids[::-1])
        dialog.deleteLater()
    monkeypatch.setattr(ui_pair, '_run_modal', reverse_lines)
    pair = ui_pair.PairDialog(project, session)
    try:
        pair.open_reading_order()
        assert list(pair.left_panel._line_order) == [line['id'] for line in reading_stream(a, include_ignored=True)]
    finally:
        pair.deleteLater()
