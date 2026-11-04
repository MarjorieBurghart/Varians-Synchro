"""Vérification d'une installation : ``Varians-Synchro --self-test RAPPORT``.

Elle sert à vérifier, sur chaque système, la version prête à l'emploi
construite par PyInstaller (packaging/) : traductions, aide, ressources,
projet d'exemple, synchronisation et exports, fenêtre. Une application
Windows sans console n'a pas de sortie standard, d'où le rapport écrit dans
un fichier ; le code de sortie dit si tout va bien.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _files(folder):
    return sorted(p.relative_to(folder).as_posix() for p in Path(folder).rglob('*'))


def test_every_check_passes_on_the_sources(tmp_path):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from varians_synchro.core import VERSION
    from varians_synchro.self_test import CHECKS, run
    demo_before = _files(ROOT / 'demo_local_ALTO')
    report_path = tmp_path / 'rapport.json'
    assert run(report_path) == 0
    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert report['ok'] is True and report['version'] == VERSION and report['frozen'] is False
    assert [check['name'] for check in report['checks']] == list(CHECKS)
    assert all(check['ok'] for check in report['checks']), report['checks']
    assert _files(ROOT / 'demo_local_ALTO') == demo_before        # l'exemple est copié, jamais modifié


def test_a_missing_resource_fails_with_its_name(tmp_path):
    from varians_synchro.self_test import run
    root = tmp_path / 'installation'
    for name in ('i18n', 'icons', 'demo_local_ALTO'):
        shutil.copytree(ROOT / name, root / name)
    (root / 'help').mkdir()                                       # aide absente
    report_path = tmp_path / 'rapport.json'
    assert run(report_path, root=root, only=('translations', 'help', 'resources')) == 1
    report = json.loads(report_path.read_text(encoding='utf-8'))
    checks = {check['name']: check for check in report['checks']}
    assert checks['translations']['ok'] and checks['resources']['ok']
    assert not checks['help']['ok'] and 'help/fr.html' in checks['help']['detail']
    assert report['ok'] is False


def test_the_launcher_runs_the_self_test(tmp_path):
    """« run.py --self-test RAPPORT » : le même point d'entrée que
    l'exécutable construit."""
    pytest.importorskip('PySide6')
    report_path = tmp_path / 'rapport.json'
    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    completed = subprocess.run([sys.executable, str(ROOT / 'run.py'), '--self-test', str(report_path)],
                               cwd=tmp_path, env=environment, capture_output=True, timeout=120)
    assert completed.returncode == 0, completed.stderr.decode('utf-8', 'replace')[-2000:]
    assert json.loads(report_path.read_text(encoding='utf-8'))['ok'] is True


def test_a_built_version_moved_elsewhere_still_checks_itself(tmp_path, monkeypatch):
    """Version construite : le projet d'exemple vérifié est celui que
    l'exécutable emporte avec ses données, et non la copie posée à côté de
    lui pour l'utilisateur. Un paquet ``.app`` glissé dans Applications, loin
    du dossier de l'archive, se vérifie donc toujours."""
    from varians_synchro.self_test import run
    moved = tmp_path / 'Applications' / 'Varians-Synchro.app' / 'Contents' / 'MacOS' / 'Varians-Synchro'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(moved))
    report_path = tmp_path / 'rapport.json'
    assert run(report_path, only=('resources', 'project')) == 0, report_path.read_text(encoding='utf-8')
    assert json.loads(report_path.read_text(encoding='utf-8'))['frozen'] is True
