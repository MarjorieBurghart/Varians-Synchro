"""Tests of the v0.8.5.2 Varians export contract, without requiring Qt."""
import json
import uuid

import pytest

from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import line_uid, add_pair_link, create_pair_session
from varians_synchro.varians_export import (make_varians_alignments,
                                            export_varians_alignments,
                                            _safe_same_segmentation_after_format_change,
                                            _line_fingerprint)


def _page(w, name='f1r', number=3, page_id=None):
    page_id = page_id or str(uuid.uuid4())
    rows = []
    for i in range(number):
        rows.append({'alto_id': f'{w["id"]}-line-{i}', 'text': f'lemma-{i}',
                     'bbox': {'HPOS': 1, 'VPOS': i * 25, 'WIDTH': 70, 'HEIGHT': 20}})
    source_id = str(uuid.uuid4())
    w['alto_sources'].append({'id': source_id, 'path': 'missing.xml',
                              'pages': [{'width': 100, 'height': 200, 'lines': rows}]})
    w['pages'].append({'id': page_id, 'label': name, 'image_kind': 'local',
                       'image_path': f'{w["id"]}.jpg',
                       'alto_binding': {'source_id': source_id, 'page_index': 0}})
    return [line_uid(w['id'], page_id, i) for i in range(1, number + 1)]


def test_exports_1_to_n_and_separates_proposed_from_validated():
    p = new_project()
    a = create_witness(p, 'A')
    b = create_witness(p, 'B')
    aa = _page(a)
    bb = _page(b)
    s = create_pair_session(p, 'A', 'B')
    add_pair_link(p, s, [aa[0]], bb[:2], state='validated')
    add_pair_link(p, s, [aa[1]], [bb[2]], state='uncertain', origin='interpolated-geometry')
    strict, _ = make_varians_alignments(p, 'A', include_uncertain=False)
    loose, _ = make_varians_alignments(p, 'A', include_uncertain=True)
    key = f'{a["pages"][0]["id"]}::1'
    assert strict['B']['pages'][0]['lines'][0]['base_keys'] == [key]
    assert strict['B']['pages'][0]['lines'][1]['base_keys'] == [key]
    assert 'base_keys' not in strict['B']['pages'][0]['lines'][2]
    assert loose['B']['pages'][0]['lines'][2]['base_keys'] == [f'{a["pages"][0]["id"]}::2']
    assert strict['B']['meta']['format'] == 'tei-manuscript-alignment'
    assert strict['B']['meta']['editorial_tei_alignment'] == 'NOT_ESTABLISHED'


def test_exclusions_never_export_as_matches():
    p = new_project()
    a = create_witness(p, 'A')
    b = create_witness(p, 'B')
    a_ids = _page(a)
    b_ids = _page(b)
    s = create_pair_session(p, 'A', 'B')
    add_pair_link(p, s, [a_ids[0]], [b_ids[0]], state='validated')
    b['ignored_line_ids'].append(b_ids[0])
    caches, report = make_varians_alignments(p, 'A')
    assert all(not l.get('base_keys') for pg in caches['B']['pages'] for l in pg['lines'])
    assert report['per_witness']['B']['stale_or_ignored_group'] == 1


def test_proven_uuid_migration_requires_matching_text_bbox_and_old_hash():
    ident = uuid.uuid4()
    bbox = {'HPOS': '14', 'VPOS': '25', 'WIDTH': '99', 'HEIGHT': '19'}
    old = {'alto_id': 'line_' + str(ident), 'bbox': bbox, 'text': 'Vita'}
    new = {'alto_id': 'id_' + str(ident), 'bbox': {k: float(v) for k, v in bbox.items()}, 'text': 'Vita'}
    witness = {'alto_sources': [{'pages': [{'lines': [old]}]}]}
    assert _safe_same_segmentation_after_format_change(witness, 'ignored', new, _line_fingerprint(old))
    assert not _safe_same_segmentation_after_format_change(witness, 'ignored', dict(new, text='Other'), _line_fingerprint(old))
    assert not _safe_same_segmentation_after_format_change(witness, 'ignored', dict(new, bbox=dict(new['bbox'], HEIGHT=22)), _line_fingerprint(old))


def test_export_is_non_destructive_and_refuses_nonempty_output(tmp_path):
    p = new_project()
    _page(create_witness(p, 'A'))
    before = json.dumps(p, sort_keys=True)
    dest = tmp_path / 'export'
    export_varians_alignments(p, 'A', dest)
    assert (dest/'validated'/'A.json').exists()
    assert (dest/'working'/'A.json').exists()
    assert (dest/'rapport_export.json').exists()
    assert json.dumps(p, sort_keys=True) == before
    with pytest.raises(FileExistsError):
        export_varians_alignments(p, 'A', dest)


def test_study_scope_filters_phantom_lb_but_preserves_original_base_keys():
    p = new_project()
    a = create_witness(p, 'A')
    b = create_witness(p, 'B')
    aa = _page(a, number=5)
    bb = _page(b, number=3)
    a['ignored_line_ids'].extend([aa[0], aa[1], aa[4]])
    b['ignored_line_ids'].append(bb[0])
    s = create_pair_session(p, 'A', 'B')
    add_pair_link(p, s, [aa[2]], [bb[1]], state='validated')
    caches, diag = make_varians_alignments(p, 'A')
    assert [r['line'] for r in caches['A']['pages'][0]['lines']] == [3, 4]
    assert [r['line'] for r in caches['B']['pages'][0]['lines']] == [2, 3]
    assert caches['B']['pages'][0]['lines'][0]['base_keys'] == [f'{a["pages"][0]["id"]}::3']
    assert diag['ignored_lines_excluded_from_export'] is True
    # No accidental renumbering, no mutation of the original project.
    assert len(a['ignored_line_ids']) == 3


def test_iiif_source_keeps_canvas_identity_for_download_cache():
    p = new_project()
    a = create_witness(p, 'A')
    _page(a)
    pg = a['pages'][0]
    pg['image_kind'] = 'iiif'
    pg['canvas'] = {
        'id': 'https://example.test/canvas/14v',
        'label': '14v', 'image_service': 'https://example.test/iiif/14v',
        'image_url': 'https://example.test/iiif/14v/full/full/0/default.jpg',
        'width': 2000, 'height': 3000, 'iiif_image_version': 2,
    }
    caches, _ = make_varians_alignments(p, 'A')
    assert caches['A']['pages'][0]['image']['canvas'] == 'https://example.test/canvas/14v'
