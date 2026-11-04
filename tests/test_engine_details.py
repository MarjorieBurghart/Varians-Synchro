"""Moteurs : petits défauts relevés par la red team (C3, C6, C7, A6)."""
from varians_synchro.core import create_witness, new_project
from varians_synchro.physical_alignment import (add_pair_link, create_pair_session, detach_pair_lines,
                                                physical_lines, replace_revisable_pair_proposals)
from varians_synchro.rapid_review import following_anchor_interval, suggestions_for_interval
from varians_synchro.textual_progress import suggest_textual_progress


def _page(witness, page_id, texts):
    source = f'{witness["id"]}_{page_id}'
    witness['alto_sources'].append({'id': source, 'path': f'/absent/{source}.xml', 'pages': [
        {'width': '1000', 'height': '1600', 'line_count': len(texts), 'lines': [
            {'alto_id': f'l{j}', 'region_id': 'r', 'text': text,
             'bbox': {'HPOS': '25', 'VPOS': str(40 * j), 'WIDTH': '300', 'HEIGHT': '29'}}
            for j, text in enumerate(texts)]}]})
    witness['pages'].append({'id': page_id, 'label': page_id, 'image_kind': 'local',
                             'image_path': f'/absent/{page_id}.jpg',
                             'alto_binding': {'source_id': source, 'page_index': 0}})


def test_recalculating_to_the_next_anchor_still_works_after_a_correction():
    """C3 : un groupe automatique corrigé à la main (Associer, Dissocier)
    reste incertain mais devient protégé ; les propositions de l'intervalle
    portaient alors ses bornes, et « Recalculer jusqu'au prochain ancrage »
    n'en trouvait plus aucune."""
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    _page(a, 'A1', [f'alpha {j} ' * 3 for j in range(12)])
    _page(b, 'B1', [f'beta {j} ' * 3 for j in range(15)])
    session = create_pair_session(project, 'A', 'B')
    la, lb = physical_lines(a), physical_lines(b)
    first = add_pair_link(project, session, [la[0]['id']], [lb[0]['id']])
    last = add_pair_link(project, session, [la[-1]['id']], [lb[-1]['id']])
    replace_revisable_pair_proposals(project, session, suggest_textual_progress(project, session)['proposals'])
    group = next(link for link in session['links']
                 if link['origin'].startswith('automatic') and len(link['target_ids']) > 1)
    detach_pair_lines(project, session, [], [group['target_ids'][-1]])
    interval = following_anchor_interval(project, session, first['id'])
    assert interval == (first['id'], last['id'])
    outcome = suggest_textual_progress(project, session)
    assert outcome['proposals']
    assert suggestions_for_interval(outcome, *interval) == outcome['proposals']


def test_the_residual_pass_never_offers_to_extend_a_stale_group():
    """C6 : un groupe automatique devenu périmé (nouvelle segmentation) était
    proposé à l'extension ; l'enregistrement, tout ou rien, refusait alors
    toute la sélection sans dire laquelle posait problème."""
    from varians_synchro.physical_alignment import stale_link_ids
    from varians_synchro.reading_stream import rebind_page
    from varians_synchro.residual_alignment import apply_residual_extensions, suggest_residual_extensions
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    for k in range(2):
        _page(a, f'A{k}', [f'a{k} ligne {j}' for j in range(6)])
        _page(b, f'B{k}', [f'b{k} ligne {j}' for j in range(5)])
    session = create_pair_session(project, 'A', 'B')
    la, lb = physical_lines(a), physical_lines(b)
    for k in range(2):
        for j in range(5):
            add_pair_link(project, session, [la[6 * k + j]['id']], [lb[5 * k + j]['id']], state='uncertain',
                          origin='automatic-textual-progress-v071')
    _page(b, 'B0-v2', [f'b0 ligne {j}' for j in range(4)] + ['b0 ligne 4 corrigée'])
    b['pages'].pop()                                     # seul son fichier sert
    rebind_page(b, 'B0', 'B_B0-v2', 0)
    stale = stale_link_ids(project, session)
    assert stale
    outcome = suggest_residual_extensions(project, session)
    assert outcome['proposals'] and not [p for p in outcome['proposals'] if p['link_id'] in stale]
    assert apply_residual_extensions(project, session, outcome['proposals'])['extended'] == len(outcome['proposals'])


def test_reimporting_htr_results_is_all_or_nothing(tmp_path):
    """C7 : un XML tronqué au milieu du lot laissait le témoin modifié
    (sources ajoutées, pages associées) malgré l'erreur ; un XML de plusieurs
    pages laissait une source orpheline, ajoutée de nouveau à chaque essai."""
    import copy
    import json
    import xml.etree.ElementTree as ET
    import pytest
    from varians_synchro.imaging import import_htr_results
    project = new_project('Essai')
    witness = create_witness(project, 'W')
    witness['pages'] = [{'id': f'c{n}', 'label': f'{n}r', 'image_kind': 'iiif', 'alto_binding': None}
                        for n in (1, 2, 3)]
    (tmp_path / 'pages.json').write_text(json.dumps({'format': 'varians-synchro-htr-export', 'witness': 'W',
        'pages': [{'canvas_id': f'c{n}', 'file': f'W_000{n}.jpg'} for n in (1, 2, 3)]}), encoding='utf-8')
    page = ('<Page imageFilename="x.jpg" imageWidth="500" imageHeight="800"><TextRegion id="r">'
            '<Coords points="1,1 490,1 490,700 1,700"/><TextLine id="l"><Coords points="10,1 400,1 400,20 10,20"/>'
            '<TextEquiv><Unicode>texte</Unicode></TextEquiv></TextLine></TextRegion></Page>')
    pcgts = '<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">{}</PcGts>'
    (tmp_path / 'W_0001.xml').write_text(pcgts.format(page), encoding='utf-8')
    (tmp_path / 'W_0002.xml').write_text(pcgts.format(page + page), encoding='utf-8')      # deux pages
    (tmp_path / 'W_0003.xml').write_text(pcgts.format(page)[:-30], encoding='utf-8')       # tronqué
    before = copy.deepcopy(witness)
    with pytest.raises(ET.ParseError):
        import_htr_results(witness, tmp_path / 'pages.json', tmp_path)
    assert witness == before
    (tmp_path / 'W_0003.xml').write_text(pcgts.format(page), encoding='utf-8')
    outcome = import_htr_results(witness, tmp_path / 'pages.json', tmp_path)
    assert outcome['imported'] == ['c1', 'c3'] and len(outcome['skipped']) == 1
    assert len(witness['alto_sources']) == 2                  # pas de source orpheline


def test_one_xml_page_cannot_be_bound_to_two_images():
    """A6 : l'association manuelle acceptait la page XML déjà associée à une
    autre image (un mauvais clic) : ses lignes figuraient deux fois dans le
    pivot exporté, sans que l'audit le dise. L'association par lots le
    refusait déjà."""
    import pytest
    from varians_synchro.errors import localized_text
    from varians_synchro.i18n import tr
    from varians_synchro.reading_stream import rebind_page
    from varians_synchro.validation import audit_project
    project = new_project('Essai')
    witness = create_witness(project, 'A')
    _page(witness, 'p1', ['un', 'deux'])
    _page(witness, 'p2', ['trois'])
    with pytest.raises(ValueError) as refused:
        rebind_page(witness, 'p2', 'A_p1', 0)
    assert localized_text(refused.value) == tr('error.binding.xml_page_bound', page='p1')
    assert witness['pages'][1]['alto_binding']['source_id'] == 'A_p2'
    witness['pages'][1]['alto_binding'] = dict(witness['pages'][0]['alto_binding'])   # projet ancien
    found = [m for m in audit_project(project)['messages'] if m['code'] == 'xml_page_bound_twice']
    assert len(found) == 1 and found[0]['witness'] == 'A'
