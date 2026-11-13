"""Systèmes des tests de GitHub Actions.

La suite des tests passe sous Ubuntu, Windows et macOS. Sous macOS, le
dossier temporaire est pris hors de /var/folders (lien symbolique vers
/private/var, qui fausserait les comparaisons de chemins). Un test bloqué ne
retient pas le job ; les tests en échec sont nommés en fin de passe."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github' / 'workflows' / 'tests.yml').read_text(encoding='utf-8')


def _step(name):
    step = WORKFLOW[WORKFLOW.index(f'      - name: {name}\n'):]
    return step[:step.index('\n\n')] if '\n\n' in step else step


def test_the_tests_run_on_ubuntu_windows_and_macos():
    assert 'os: [ubuntu-latest, windows-latest, macos-latest]' in WORKFLOW


def test_macos_takes_its_temporary_folder_outside_var_folders():
    step = _step('Dossier temporaire sans lien symbolique (macOS)')
    assert "if: runner.os == 'macOS'" in step and 'echo "TMPDIR=$RUNNER_TEMP" >> "$GITHUB_ENV"' in step


def test_a_blocked_test_cannot_hold_the_job_and_failures_are_named():
    """Un test bloqué ne retient pas le job jusqu'à la limite de GitHub
    (6 heures) ; au-delà de 5 minutes, pytest affiche sa pile d'appels
    (faulthandler, sans dépendance de plus)."""
    assert '    timeout-minutes: 30\n' in WORKFLOW[WORKFLOW.index('  tests:'):]
    command = _step('Tests')
    for option in ('python -m pytest -q', '-rfE', '-o faulthandler_timeout=300'):
        assert option in command, option


def test_the_readme_names_the_tested_systems():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'sous Linux, Windows et macOS' in readme
