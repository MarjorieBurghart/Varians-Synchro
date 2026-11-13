"""Versions testées des dépendances.

``requirements.txt`` nomme les dépendances avec une plage large, pour
qu'une installation depuis les sources prenne des versions récentes. Les
tests de GitHub Actions et la construction des archives prennent, eux, les
versions testées de ``constraints.txt`` : une nouvelle version de PySide6
(ou de lxml et Saxon, pour les tests de compatibilité qui ouvrent les
projets exportés avec le vrai code de Varians) ne change pas une release
sans qu'on l'ait voulu."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ('requirements.txt', 'requirements-dev.txt', 'packaging/requirements.txt')


def _names(path):
    """Paquets nommés par un fichier de dépendances (sans ``-r``, ni
    commentaires), avec leur version si elle est fixée."""
    found = {}
    for line in (ROOT / path).read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line or line.startswith('-'):
            continue
        match = re.match(r'([A-Za-z0-9_.\-]+)\s*(?:==\s*([^\s;,]+))?', line)
        found[match.group(1).lower().replace('_', '-')] = match.group(2)
    return found


def test_every_dependency_has_a_tested_version():
    pinned = _names('constraints.txt')
    assert pinned and all(pinned.values()), pinned
    for path in REQUIREMENTS:
        for name, version in _names(path).items():
            assert version or name in pinned, (path, name)


def test_the_qt_packages_share_one_version():
    pinned = _names('constraints.txt')
    qt = {name: pinned.get(name) for name in ('pyside6', 'pyside6-essentials', 'pyside6-addons', 'shiboken6')}
    assert None not in qt.values() and len(set(qt.values())) == 1, qt


def test_the_dependencies_of_varians_for_the_compatibility_tests_are_pinned_too():
    """La CI installe aussi les dépendances de Varians (lxml, Saxon) pour
    ouvrir les projets exportés avec son vrai code."""
    pinned = _names('constraints.txt')
    assert {'lxml', 'saxonche'} <= set(pinned)


def test_the_workflows_install_the_tested_versions():
    for workflow in (ROOT / '.github' / 'workflows').glob('*.yml'):
        for line in workflow.read_text(encoding='utf-8').splitlines():
            if 'pip install' in line and ' -r ' in line:
                assert '-c constraints.txt' in line, (workflow.name, line.strip())


def test_the_development_guides_explain_the_tested_versions():
    for document in ('README.md', 'packaging/LISEZMOI.md', 'MAINTENANCE_PASSATION_V0856/01_PREMIERE_REPRISE.md'):
        text = (ROOT / document).read_text(encoding='utf-8')
        assert '-c constraints.txt' in text, document
    assert 'constraints.txt' in (ROOT / 'docs' / 'developer' / 'PORTABILITE.md').read_text(encoding='utf-8')
