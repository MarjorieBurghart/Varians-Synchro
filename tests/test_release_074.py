"""V0.7.4 release gate: pair-local exceptions, export atomicity, 3 witnesses.

All fixtures synthetic. No network, Qt, original XML or images needed.
"""
import copy
import json
from pathlib import Path
from time import perf_counter

import pytest

from test_varians_export import _page
from varians_synchro.core import new_project, create_witness, load_project, save_project
from varians_synchro.physical_alignment import create_pair_session, add_pair_link
from varians_synchro.reading_stream import anchor_intervals
from varians_synchro.textual_progress import _partition
from varians_synchro.validation import audit_project
from varians_synchro.varians_export import (export_varians_alignments,
    make_varians_alignments, verify_export_payloads)


def test_three_witness_pair_local_links_absence_and_pivot_keys(tmp_path):
    p = new_project()
    mu = create_witness(p, 'Mu'); f = create_witness(p, 'F'); a = create_witness(p, 'A')
    m0 = _page(mu, number=4); f0 = _page(f, number=7); a0 = _page(a, number=3)
    muf = create_pair_session(p, 'Mu', 'F')
    mua = create_pair_session(p, 'Mu', 'A')
    add_pair_link(p, muf, [m0[0]], f0[:2], state='validated')
    add_pair_link(p, muf, [m0[1]], [f0[2]], state='uncertain', origin='automatic-textual-progress-v071')
    add_pair_link(p, muf, [m0[2]], [], state='validated', kind='absence')
    add_pair_link(p, mua, m0[2:4], [a0[0]], state='validated')
    # An absence in F does not affect the very same line when matching A.
    before = json.dumps(p, sort_keys=True)
    dest = tmp_path/'export'
    report = export_varians_alignments(p, 'Mu', dest)
    assert json.dumps(p, sort_keys=True) == before
    validated = json.loads((dest/'validated/F.json').read_text(encoding='utf8'))
    working = json.loads((dest/'working/F.json').read_text(encoding='utf8'))
    a_json = json.loads((dest/'validated/A.json').read_text(encoding='utf8'))
    mu_json = json.loads((dest/'validated/Mu.json').read_text(encoding='utf8'))
    key = f"{mu['pages'][0]['id']}::1"
    assert [row['base_keys'] for row in validated['pages'][0]['lines'][:2]] == [[key], [key]]
    assert 'base_keys' not in validated['pages'][0]['lines'][2]
    assert working['pages'][0]['lines'][2]['base_keys'] == [f"{mu['pages'][0]['id']}::2"]
    assert a_json['pages'][0]['lines'][0]['base_keys'] == [
        f"{mu['pages'][0]['id']}::3", f"{mu['pages'][0]['id']}::4"]
    assert not any('base_keys' in ln for pg in mu_json['pages'] for ln in pg['lines'])
    assert report['validated']['integrity']['all_base_keys_resolve'] is True
    assert report['working']['integrity']['all_base_keys_resolve'] is True
    audit = audit_project(p, base_witness_id='Mu')
    assert audit['ok'], audit['messages']
    assert audit['summary']['pairs']['Mu ↔ F']['confirmed_absences'] == 1


def test_ignore_keeps_true_physical_ordinals_and_referenced_base_keys():
    p = new_project()
    m = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    a = _page(m, number=6); b = _page(f, number=3)
    m['ignored_line_ids'] = a[:2] + a[5:]
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, [a[2]], [b[0]], state='validated')
    payload, _ = make_varians_alignments(p, 'Mu')
    assert [row['line'] for row in payload['Mu']['pages'][0]['lines']] == [3, 4, 5]
    assert payload['F']['pages'][0]['lines'][0]['base_keys'] == [f"{m['pages'][0]['id']}::3"]
    verify_export_payloads(payload, 'Mu')


def test_preflight_detects_duplicate_pair_and_does_not_modify():
    p = new_project()
    m = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    _page(m); _page(f)
    create_pair_session(p, 'Mu', 'F')
    p['pair_sessions'].append(copy.deepcopy(p['pair_sessions'][0]))
    old = copy.deepcopy(p)
    audit = audit_project(p, 'Mu')
    assert 'duplicate_pair_session' in {issue['code'] for issue in audit['messages']}
    assert audit['errors'] > 0
    assert p == old


def test_preflight_reports_ignored_link_conflicts_as_errors():
    p = new_project()
    m = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    ma = _page(m); fa = _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, [ma[0]], [fa[0]])
    f['ignored_line_ids'] = [fa[0]]
    result = audit_project(p, 'Mu')
    assert not result['ok']
    assert any(message['code'] == 'stale_or_ignored_line' for message in result['messages'])


def test_preflight_detects_overlap_without_touching_links():
    p = new_project()
    m = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    ma = _page(m); fa = _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    a = add_pair_link(p, s, [ma[0]], [fa[0]])
    b = add_pair_link(p, s, [ma[1]], [fa[1]])
    b['reference_ids'] = [ma[0]]
    before = copy.deepcopy(s)
    result = audit_project(p)
    assert not result['ok']
    assert any(m['code'] == 'line_in_multiple_groups' for m in result['messages'])
    assert s == before


def test_preflight_export_working_only_is_warning_not_error():
    p = new_project(); m = create_witness(p,'Mu'); f=create_witness(p,'F')
    ma=_page(m); fa=_page(f)
    s=create_pair_session(p,'Mu','F')
    add_pair_link(p,s,[ma[0]],[fa[0]],state='uncertain')
    result=audit_project(p,'Mu')
    assert result['ok']
    assert 'secondary_only_uncertain' in {e['code'] for e in result['messages']}


def test_atomic_export_preparation_failure_leaves_existing_empty_dir(tmp_path):
    p = new_project(); m=create_witness(p,'Mu'); f=create_witness(p,'F')
    _page(m); _page(f)
    f['id'] = '../bad'  # Invalid output filename; must reject BEFORE writing.
    dest=tmp_path/'export'; dest.mkdir()
    with pytest.raises(ValueError):
        export_varians_alignments(p,'Mu',dest)
    assert dest.is_dir() and list(dest.iterdir()) == []
    assert not list(tmp_path.glob('.varians-synchro-export-*'))


def test_atomic_export_write_failure_cleans_stage(tmp_path, monkeypatch):
    p=new_project(); m=create_witness(p,'Mu'); f=create_witness(p,'F')
    _page(m); _page(f)
    dest=tmp_path/'out'
    original = Path.write_text
    def fail_on_target(self, data, *args, **kwargs):
        if self.name == 'F.json':
            raise OSError('simulated disk full')
        return original(self, data, *args, **kwargs)
    monkeypatch.setattr(Path, 'write_text', fail_on_target)
    with pytest.raises(OSError, match='simulated disk full'):
        export_varians_alignments(p,'Mu',dest)
    assert not dest.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_export_refuses_nonempty_destination(tmp_path):
    p=new_project(); m=create_witness(p,'Mu'); _page(m)
    dest=tmp_path/'out'; dest.mkdir()
    existing=dest/'working'; existing.write_text('leave intact')
    with pytest.raises(FileExistsError):
        export_varians_alignments(p, 'Mu', dest)
    assert existing.read_text() == 'leave intact'


def test_export_payload_verifier_rejects_dangling_base_keys():
    p=new_project();m=create_witness(p,'Mu');f=create_witness(p,'F')
    _page(m);_page(f)
    payload,_=make_varians_alignments(p,'Mu')
    payload['F']['pages'][0]['lines'][0]['base_keys']=['unknown-page::900']
    with pytest.raises(ValueError,match='absentes'):
        verify_export_payloads(payload,'Mu')


def test_crossed_anchor_poison_adjacent_intervals_without_deleting_other_ones():
    p=new_project(); a=create_witness(p,'A'); b=create_witness(p,'B')
    aa=_page(a,number=9); bb=_page(b,number=9)
    s=create_pair_session(p,'A','B')
    add_pair_link(p,s,[aa[0]],[bb[3]],state='validated')
    add_pair_link(p,s,[aa[2]],[bb[1]],state='validated')
    add_pair_link(p,s,[aa[5]],[bb[5]],state='validated')
    add_pair_link(p,s,[aa[8]],[bb[8]],state='validated')
    results=anchor_intervals(p,s)
    # First two contradict each other: B->C must not be computed as trustworthy.
    assert len(results['intervals']) == 1
    assert results['intervals'][0]['reference_count'] == 2
    assert results['intervals'][0]['target_count'] == 2
    assert results['intervals'][0]['start_link_id'] == s['links'][2]['id']


def test_500_by_500_cumulative_partition_is_linear_enough():
    def rows(prefix, count):
        return [{'id': f'{prefix}-{i}', 'page_id':f'{prefix}-page',
                 'region_id':'column_1', 'text': 'quisque igitur textus est',
                 'bbox':{'WIDTH':270, 'HEIGHT':25}} for i in range(count)]
    aa=rows('a',500); bb=rows('b',500)
    start=perf_counter()
    groups=_partition(aa,bb)
    elapsed=perf_counter()-start
    assert len(groups)==500
    assert {x for group in groups for x in group['reference_ids']} == {r['id'] for r in aa}
    assert {x for group in groups for x in group['target_ids']} == {r['id'] for r in bb}
    assert elapsed < 2.0, f'500x500 partition took {elapsed:.3f}s'


def test_project_roundtrip_unchanged_after_audit(tmp_path):
    p=new_project();m=create_witness(p,'Mu');_page(m)
    src=tmp_path/'check.vsynch';save_project(p,src)
    before=src.read_bytes()
    loaded=load_project(src)
    audit_project(loaded,'Mu')
    assert src.read_bytes()==before
