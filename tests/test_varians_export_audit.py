"""Regression: exporting zero secondary base_keys must never be silent."""
import json

from varians_synchro.core import new_project, create_witness
from varians_synchro.physical_alignment import create_pair_session, add_pair_link
from varians_synchro.varians_export import inspect_varians_export, export_varians_alignments
from test_varians_export import _page


def test_base_intentionally_has_no_base_keys_and_secondary_unaligned_is_flagged():
    p = new_project()
    a = create_witness(p, 'Mu')
    f = create_witness(p, 'F')
    _page(a); _page(f)
    audit = inspect_varians_export(p, 'Mu')
    assert 'Mu' not in audit['witnesses']
    assert audit['witnesses']['F']['validated_linked_lines'] == 0
    assert audit['witnesses']['F']['working_linked_lines'] == 0
    assert audit['witnesses']['F']['reason'] == 'no_direct_session'


def test_all_proposed_links_emit_validated_zero_working_positive_warning(tmp_path):
    p = new_project()
    a = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    mu = _page(a); ff = _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, mu[:1], ff[:1], state='proposed')
    audit = inspect_varians_export(p, 'Mu')
    stat = audit['witnesses']['F']
    assert (stat['validated_linked_lines'], stat['working_linked_lines']) == (0, 1)
    assert stat['reason'] == 'working_only'
    rep = export_varians_alignments(p, 'Mu', tmp_path/'out')
    assert rep['audit']['witnesses']['F']['reason'] == 'working_only'
    validated = json.loads((tmp_path/'out/validated/F.json').read_text())
    working = json.loads((tmp_path/'out/working/F.json').read_text())
    assert not validated['pages'][0]['lines'][0].get('base_keys')
    assert working['pages'][0]['lines'][0]['base_keys'] == [f'{a["pages"][0]["id"]}::1']
    assert json.loads((tmp_path/'out/rapport_export.json').read_text())['audit']['base'] == 'Mu'


def test_validated_pair_does_not_generate_false_warnings():
    p = new_project()
    mu = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    a = _page(mu); b = _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, [a[1]], [b[1]], state='validated')
    audit = inspect_varians_export(p, 'Mu')
    assert not audit['warnings']
    assert audit['witnesses']['F']['validated_linked_lines'] == 1
    assert audit['witnesses']['F']['working_linked_lines'] == 1


def test_absence_only_is_not_falsely_reported_as_correspondence():
    p = new_project()
    mu = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    a = _page(mu); _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, a[:1], [], state='validated', kind='absence')
    audit = inspect_varians_export(p, 'Mu')
    assert audit['witnesses']['F']['reason'] == 'absence_only'
