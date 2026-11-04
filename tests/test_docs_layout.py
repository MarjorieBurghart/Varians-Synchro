"""Rangement de la documentation du dépôt.

- À la racine, seulement le README, le journal des versions et l'index des
  documents : les guides sont l'aide intégrée (``help/``), les références
  techniques sont dans ``docs/developer/``, les anciennes notes de livraison
  restent dans l'historique Git (``docs/HISTORIQUE.md``).
- Aucun document ne renvoie à un fichier ``.md`` absent du dépôt, sauf par un
  lien vers son dernier état dans Git.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_maintenance import DOCUMENTS, check_links  # noqa: E402

ROOT_DOCUMENTS = {'README.md', 'CHANGELOG.md', 'DOCS_INDEX.md'}
DEVELOPER_REFERENCES = {'ARCHITECTURE.md', 'FORMAT_PROJET.md', 'EXPORT_VARIANS.md',
                        'INTERNATIONALISATION.md', 'PORTABILITE.md'}
# Dernier commit qui contient les documents historiques.
HISTORY = 'https://github.com/MarjorieBurghart/Varians-Synchro/blob/f09a9b75b252114b5f416335d0f19cdd6162eaae/'
HISTORY_LINK = re.compile(r'\[[^\]]*\]\(' + re.escape(HISTORY) + r'[^)]*\)')
MENTION = re.compile(r'\b[\w.-]+\.md\b')


def test_only_the_readme_changelog_and_index_are_at_the_root():
    assert {path.name for path in ROOT.glob('*.md')} == ROOT_DOCUMENTS


def test_the_technical_references_are_in_docs_developer():
    assert DEVELOPER_REFERENCES <= {path.name for path in (ROOT / 'docs' / 'developer').glob('*.md')}


def test_every_document_is_checked():
    documents = {path.resolve() for path in DOCUMENTS()}
    for path in [*ROOT.glob('*.md'), *(ROOT / 'docs').rglob('*.md'),
                 *(ROOT / 'MAINTENANCE_PASSATION_V0856').rglob('*.md')]:
        assert path.resolve() in documents, path


def test_relative_links_lead_to_a_file():
    assert [error for path in DOCUMENTS() for error in check_links(path)] == []


def test_mentioned_markdown_files_exist_or_link_to_their_history():
    existing = {path.name for path in ROOT.rglob('*.md') if '.git' not in path.parts}
    missing = []
    for path in DOCUMENTS():
        text = HISTORY_LINK.sub('', path.read_text(encoding='utf-8'))
        missing += [(path.relative_to(ROOT).as_posix(), name)
                    for name in MENTION.findall(text) if name not in existing]
    assert missing == []


def test_the_history_lists_each_removed_file_once():
    text = (ROOT / 'docs' / 'HISTORIQUE.md').read_text(encoding='utf-8')
    linked = re.findall(re.escape(HISTORY) + r'([^)]+)\)', text)
    assert len(linked) == len(set(linked))
    assert not set(linked) & ROOT_DOCUMENTS
    assert not {name for name in linked if (ROOT / name).exists()}
