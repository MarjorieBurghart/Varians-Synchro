"""Correspondances périmées après une nouvelle segmentation d'une page.

Une ligne est repérée par sa page et son rang. Si la page est réassociée à
un autre XML (une ligne de plus en tête, par exemple), les correspondances
qui citaient ses lignes désignent d'autres lignes. Elles deviennent
« périmées » (leurs empreintes ne correspondent plus) : jamais supprimées,
mais exclues des ancres et des calculs, et à revalider ou dissocier.
"""
from __future__ import annotations

import pytest

from varians_synchro.core import new_project, create_witness, add_image_source, add_alto_source
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.physical_alignment import (
    create_pair_session, add_pair_link, extend_pair_link, physical_lines, pair_progress,
    stale_link_ids, revalidate_pair_link, page_links_impact)
from varians_synchro.reading_stream import anchor_intervals, set_line_order, rebind_page
from varians_synchro.textual_progress import suggest_textual_progress

PAGE = '''<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
<Page imageFilename="{image}" imageWidth="500" imageHeight="800">
<TextRegion id="r"><Coords points="1,1 490,1 490,700 1,700"/>
{lines}
</TextRegion></Page></PcGts>'''


def _xml(path, texts):
    lines = ''.join(
        f'<TextLine id="{path.stem}_{j}"><Coords points="10,{j*30+1} 400,{j*30+1} 400,{j*30+20} '
        f'10,{j*30+20}"/><TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>'
        for j, text in enumerate(texts))
    path.write_text(PAGE.format(image=path.stem + '.jpg', lines=lines), encoding='utf-8')
    return path


def _uid(witness, text):
    return next(line['id'] for line in physical_lines(witness) if line['text'] == text)


TEXTS_A = [f'alpha {i}' for i in range(1, 7)]
TEXTS_B = [f'beta {i}' for i in range(1, 7)]


@pytest.fixture
def setting(tmp_path):
    project = new_project('Essai')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    for witness, texts in ((a, TEXTS_A), (b, TEXTS_B)):
        image = tmp_path / f'{witness["id"]}.jpg'
        image.write_bytes(b'image')
        add_image_source(witness, 'local', str(image))
        add_alto_source(witness, _xml(tmp_path / f'{witness["id"]}.xml', texts))
        create_pages(witness)
        bind_alto(witness, witness['pages'][0]['id'], witness['alto_sources'][0]['id'], 0)
    session = create_pair_session(project, 'A', 'B')
    first = add_pair_link(project, session, [_uid(a, 'alpha 1')], [_uid(b, 'beta 1')])
    last = add_pair_link(project, session, [_uid(a, 'alpha 6')], [_uid(b, 'beta 6')])
    # Nouvelle segmentation de A : une ligne de plus en tête.
    corrected = _xml(tmp_path / 'A-corrige.xml', ['titre'] + TEXTS_A)
    add_alto_source(a, corrected)
    return project, a, b, session, first, last


def _rebind(a):
    rebind_page(a, a['pages'][0]['id'], a['alto_sources'][-1]['id'], 0)


def test_links_are_fresh_while_the_lines_are_unchanged(setting):
    project, _a, _b, session, _first, _last = setting
    assert stale_link_ids(project, session) == set()
    assert len(anchor_intervals(project, session)['anchors']) == 2


def test_a_new_segmentation_makes_the_links_on_the_page_stale(setting):
    project, a, _b, session, first, last = setting
    _rebind(a)
    assert stale_link_ids(project, session) == {first['id'], last['id']}
    assert len(session['links']) == 2                          # jamais supprimées
    assert pair_progress(project, session)['stale_references'] > 0


def test_stale_links_are_not_used_as_anchors(setting):
    project, a, _b, session, first, last = setting
    _rebind(a)
    result = anchor_intervals(project, session)
    assert result['anchors'] == [] and result['intervals'] == []
    assert {w['link_id'] for w in result['warnings'] if w['reason'] == 'stale_anchor'} == \
        {first['id'], last['id']}


def test_stale_links_do_not_feed_the_text_calculation(setting):
    project, a, _b, session, _first, _last = setting
    _rebind(a)
    assert suggest_textual_progress(project, session)['proposals'] == []


def test_a_stale_group_cannot_be_extended(setting):
    project, a, b, session, first, _last = setting
    _rebind(a)
    before = dict(first)
    with pytest.raises(ValueError, match='périmé'):
        extend_pair_link(project, session, first['reference_ids'], [_uid(b, 'beta 2')])
    assert first == before


def test_revalidation_records_the_checked_lines(setting):
    project, a, _b, session, first, _last = setting
    _rebind(a)
    revalidate_pair_link(project, session, first['id'])
    assert first['id'] not in stale_link_ids(project, session)
    assert first['state'] == 'validated' and first['reviewed_at']
    assert first['evidence']['manual_corrections'][-1]['action'] == 'revalidate'


def test_revalidation_refuses_a_vanished_line(setting, tmp_path):
    project, a, _b, session, first, _last = setting
    # La nouvelle segmentation n'a plus que deux lignes : alpha 6 (rang 6) disparaît.
    add_alto_source(a, _xml(tmp_path / 'A-court.xml', TEXTS_A[:2]))
    rebind_page(a, a['pages'][0]['id'], a['alto_sources'][-1]['id'], 0)
    last = next(link for link in session['links'] if link['id'] != first['id'])
    with pytest.raises(ValueError):
        revalidate_pair_link(project, session, last['id'])


def test_the_impact_of_a_new_segmentation_is_known_beforehand(setting):
    project, a, _b, _session, _first, _last = setting
    page = a['pages'][0]['id']
    set_line_order(a, page, list(reversed([line['id'] for line in physical_lines(a)])))
    impact = page_links_impact(project, 'A', page)
    assert impact['links'] == 2 and impact['validated'] == 2 and impact['reading_order'] is True


def test_a_new_segmentation_drops_the_corrected_reading_order_of_the_page(setting):
    _project, a, _b, _session, _first, _last = setting
    page = a['pages'][0]
    set_line_order(a, page['id'], list(reversed([line['id'] for line in physical_lines(a)])))
    assert rebind_page(a, page['id'], a['alto_sources'][-1]['id'], 0) is True
    assert 'reading_line_order' not in page and 'reading_region_order' not in page
    # Même XML : rien n'est retiré.
    set_line_order(a, page['id'], [line['id'] for line in physical_lines(a)])
    assert rebind_page(a, page['id'], a['alto_sources'][-1]['id'], 0) is False
    assert 'reading_line_order' in page
