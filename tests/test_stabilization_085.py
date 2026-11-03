"""V0.8.5 non-Qt hardening and multilingual release gates."""
from __future__ import annotations

import ast
import copy
import json
import os
import stat
from pathlib import Path

import pytest

from varians_synchro import core
from varians_synchro.core import (create_witness, load_project, new_project,
                                  save_project)
from varians_synchro.i18n import (_ALIASES, _CATALOGS,
                                  reload_catalogs, tr)


def _stages(folder):
    return [x for x in folder.iterdir() if x.name.endswith('.tmp')]


def test_atomic_save_first_write_no_backup(tmp_path):
    p = new_project('A'); create_witness(p, 'Mu')
    out = tmp_path/'edition.vsynch'
    save_project(p, out)
    assert load_project(out)['name'] == 'A'
    assert not (tmp_path/'edition.vsynch.bak').exists()
    assert not _stages(tmp_path)


def test_second_save_recovers_exact_previous_project(tmp_path):
    out = tmp_path/'edition.vsynch'
    project = new_project('Première version')
    save_project(project, out)
    initial = out.read_bytes()
    project['name'] = 'Deuxième version'
    save_project(project, out)
    backup = tmp_path/'edition.vsynch.bak'
    assert backup.read_bytes() == initial
    assert load_project(backup)['name'] == 'Première version'
    assert load_project(out)['name'] == 'Deuxième version'
    assert not _stages(tmp_path)


def test_write_failure_leaves_original_file_and_backup_untouched(tmp_path, monkeypatch):
    out = tmp_path/'test.vsynch'
    p = new_project('Un'); save_project(p, out)
    p['name'] = 'Deux'; save_project(p, out)
    before, backup = out.read_bytes(), (tmp_path/'test.vsynch.bak').read_bytes()
    original_replace = core.os.replace
    def reject_new_project(source, destination):
        if Path(destination) == out:
            raise OSError('Simulated interrupted save')
        return original_replace(source, destination)
    monkeypatch.setattr(core.os, 'replace', reject_new_project)
    p['name'] = 'Trois'
    with pytest.raises(OSError, match='interrupted'):
        save_project(p, out)
    assert out.read_bytes() == before
    # The existing .bak is updated to the previous, still-valid save only.
    assert load_project(tmp_path/'test.vsynch.bak')['name'] == 'Deux'
    assert not _stages(tmp_path)


def test_backup_copy_failure_preserves_primary_and_old_backup(tmp_path, monkeypatch):
    out = tmp_path/'test.vsynch'
    p = new_project('Un'); save_project(p, out)
    p['name'] = 'Deux'; save_project(p, out)
    saved = out.read_bytes()
    old_backup = (tmp_path/'test.vsynch.bak').read_bytes()
    def fail(*args, **kwargs):
        raise OSError('Simulated backup failure')
    monkeypatch.setattr(core.shutil, 'copyfileobj', fail)
    p['name'] = 'Trois'
    with pytest.raises(OSError, match='backup failure'):
        save_project(p, out)
    assert out.read_bytes() == saved
    assert (tmp_path/'test.vsynch.bak').read_bytes() == old_backup
    assert not _stages(tmp_path)


def test_invalid_model_does_not_replace_last_saved_version(tmp_path):
    out = tmp_path/'p.vsynch'
    model = new_project('Valide')
    save_project(model, out)
    old = out.read_bytes()
    model['pivot_witness_id'] = 'inexistant'
    with pytest.raises(ValueError):
        save_project(model, out)
    assert out.read_bytes() == old
    assert not (tmp_path/'p.vsynch.bak').exists()


def test_load_legacy_project_in_memory_without_rewriting(tmp_path):
    p = new_project('Historique')
    create_witness(p, 'Mu')
    for key in ('pair_sessions', 'pivot_witness_id', 'workflow_preference'):
        p.pop(key)
    p['text_resources'] = [{'id':'old-txt', 'kind':'pivot', 'text':'Ancien texte'}]
    src = tmp_path/'old.vsynch'
    src.write_text(json.dumps(p, ensure_ascii=False), encoding='utf-8')
    untouched = src.read_bytes()
    loaded = load_project(src)
    assert loaded['workflow_preference'] == 'pivot'
    assert loaded['pair_sessions'] == []
    assert loaded['text_resources'][0]['text'] == 'Ancien texte'
    assert src.read_bytes() == untouched


def test_backup_restoration_is_explicit_not_implicit(tmp_path):
    out=tmp_path/'p.vsynch'; p=new_project('Bon')
    save_project(p,out);p['name']='Révision';save_project(p,out)
    out.write_text('{bad json',encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):
        load_project(out)
    assert load_project(tmp_path/'p.vsynch.bak')['name'] == 'Bon'
    assert out.read_text(encoding='utf8') == '{bad json'


def test_catalogs_cover_all_literal_translation_calls():
    root = Path(__file__).resolve().parents[1]
    aliases = set(_ALIASES)
    symbolic = set(_CATALOGS['fr'])
    missing = []
    for path in list((root/'varians_synchro').glob('*.py')) + list(root.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'tr' and node.args and
                    isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                key = node.args[0].value
                if key not in symbolic and key not in aliases:
                    missing.append(f'{path.name}:{node.lineno}: {key}')
    assert not missing, '\n'.join(missing)
    assert len(_CATALOGS['fr']) == len(_CATALOGS['en'])
    assert tr('release.groups_estimated') != 'release.groups_estimated'


def test_release_preserves_older_file_permissions_on_posix(tmp_path):
    if os.name != 'posix':
        pytest.skip('POSIX mode bits only')
    out=tmp_path/'p.vsynch';p=new_project()
    save_project(p,out)
    out.chmod(0o640)
    p['notes']='Nouvelle note'
    save_project(p,out)
    assert stat.S_IMODE(out.stat().st_mode) == 0o640


def test_release_report_read_only_and_validated_export(tmp_path):
    from recette_v085 import release_report
    from test_varians_export import _page
    from varians_synchro.physical_alignment import create_pair_session, add_pair_link
    p = new_project('Édition')
    mu = create_witness(p, 'Mu'); f = create_witness(p, 'F')
    p['pivot_witness_id'] = 'Mu'
    ml = _page(mu); fl = _page(f)
    s = create_pair_session(p, 'Mu', 'F')
    add_pair_link(p, s, [ml[0]], [fl[0]], state='validated')
    src = tmp_path/'fixture.vsynch'; save_project(p, src)
    old_bytes = src.read_bytes()
    report = release_report(src, 'Mu')
    assert report['audit']['ok']
    assert report['source_sha256_before'] == report['source_sha256_after']
    assert src.read_bytes() == old_bytes
    assert report['varians_export']['validated']['F']['mapped_secondary_lines'] == 1
    assert 'payload_sha256' in report['varians_export']['working']['Mu']


def test_release_report_rejects_overwriting_source_or_backup(tmp_path):
    from recette_v085 import main
    p = tmp_path/'p.vsynch'; save_project(new_project(), p)
    # argparse raises SystemExit(2) and does not open the dangerous output.
    for dangerous in [p, tmp_path/'p.vsynch.bak', tmp_path/'another.vsynch']:
        with pytest.raises(SystemExit) as exc:
            main([str(p), '--output', str(dangerous)])
        assert exc.value.code == 2
    assert load_project(p)['format'] == core.SCHEMA
