"""Le guide utilisateur (help/<langue>.html), affiché par la fenêtre d'aide.

- Mêmes sections, dans le même ordre, dans toutes les langues ; liens
  internes valides ; sections ouvertes par F1 présentes.
- Chaque libellé cité (balisé ``data-tr`` ou ``data-varians``) est celui de
  l'écran dans la langue du guide : ``tools/help_labels.py`` le remplit
  d'après les catalogues de Varians-Synchro et de Varians.
- La section « Format des fichiers de synchronisation » décrit exactement les
  champs que l'export écrit : ni champ oublié, ni champ inventé.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELP = ROOT / 'help'
sys.path.insert(0, str(ROOT / 'tools'))
import help_labels  # noqa: E402

GUIDES = sorted(HELP.glob('*.html'))
LANGUAGES = ('fr', 'en', 'de', 'cs', 'it', 'ru', 'ja')
# Sections que le logiciel ouvre directement (F1 dans une fenêtre).
OPENED_BY_THE_SOFTWARE = {'synchronisation'}


class _Outline(HTMLParser):
    """Identifiants, liens internes, langue et champs JSON documentés."""

    def __init__(self):
        super().__init__()
        self.ids, self.links, self.lang, self.fields = [], [], None, []
        self._section = None
        self._field = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = attrs.get('lang')
        if 'id' in attrs:
            self.ids.append(attrs['id'])
            if tag == 'h2':
                self._section = attrs['id']
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.links.append(attrs['href'][1:])
        if tag == 'code' and attrs.get('class') == 'field' and self._section == 'format-json':
            self._field = ''

    def handle_data(self, data):
        if self._field is not None:
            self._field += data

    def handle_endtag(self, tag):
        if tag == 'code' and self._field is not None:
            self.fields.append(self._field.strip())
            self._field = None


def _outline(path):
    parser = _Outline()
    parser.feed(path.read_text(encoding='utf-8'))
    return parser


def test_there_is_a_guide_in_each_language():
    assert {path.stem for path in GUIDES} == set(LANGUAGES)


@pytest.mark.parametrize('path', GUIDES, ids=lambda p: p.stem)
def test_each_guide_has_the_sections_of_the_french_one(path):
    outline = _outline(path)
    assert outline.lang == path.stem
    assert len(outline.ids) == len(set(outline.ids)), 'identifiant répété'
    assert outline.ids == _outline(HELP / 'fr.html').ids
    assert OPENED_BY_THE_SOFTWARE <= set(outline.ids)
    assert set(outline.links) <= set(outline.ids), 'lien interne vers une section absente'


@pytest.mark.parametrize('path', GUIDES, ids=lambda p: p.stem)
def test_the_cited_labels_are_those_of_the_screen(path):
    problems = [(key, shown, wanted) for key, shown, wanted in help_labels.check(path)
                if not wanted.startswith('<clé Varians')]
    assert problems == [], 'lancer python tools/help_labels.py'


def test_the_cited_varians_labels_exist():
    source = help_labels.varians_source()
    if source is None:
        if os.environ.get('VARIANS_REQUIRED'):
            pytest.fail('code source de Varians introuvable (VARIANS_SOURCE)')
        pytest.skip('code source de Varians introuvable')
    for path in GUIDES:
        catalog = help_labels.varians_catalog(path.stem, source)
        keys = {key for kind, key, _shown in help_labels.marks(path.read_text(encoding='utf-8'))
                if kind == 'varians'}
        assert keys and keys <= set(catalog), sorted(keys - set(catalog))


def test_untranslated_labels_are_really_in_the_code():
    """Un libellé cité sans clé de catalogue doit être un texte du code."""
    catalog = {entry.get('key') for entry in ET.parse(ROOT / 'i18n' / 'fr.xml').getroot()}
    code = '\n'.join(path.read_text(encoding='utf-8')
                     for path in (ROOT / 'varians_synchro').glob('*.py'))
    for path in GUIDES:
        for kind, key, _shown in help_labels.marks(path.read_text(encoding='utf-8')):
            if kind == 'ui' and key not in catalog:
                assert repr(key) in code or f'"{key}"' in code, key


def _field_paths(value, prefix=''):
    paths = set()
    if isinstance(value, dict):
        for key, item in value.items():
            path = f'{prefix}{key}'
            paths.add(path)
            paths |= _field_paths(item, path + '.')
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        for item in value:
            paths |= _field_paths(item, prefix[:-1] + '[].')
    return paths


def test_the_json_format_section_documents_exactly_the_exported_fields(tmp_path):
    from test_varians_094_compat import _project
    from varians_synchro.varians_export import make_varians_alignments
    project = _project(tmp_path)
    # Une proposition automatique non validée, avec sa confiance.
    link = project['pair_sessions'][0]['links'][0]
    link.update(state='uncertain', origin='automatic-htr-htr', confidence=0.8)
    caches, _report = make_varians_alignments(project, 'Mu', include_uncertain=True)
    produced = set().union(*(_field_paths(cache) for cache in caches.values()))
    produced.discard('meta')
    documented = set(_outline(HELP / 'fr.html').fields)
    assert produced - documented == set(), 'champ exporté non documenté'
    assert documented - produced == set(), 'champ documenté que l’export n’écrit pas'
    for path in GUIDES:
        assert set(_outline(path).fields) == documented


# LISEZMOI de la version prête à l'emploi (packaging/readme), par langue.
README_OF = {'fr': 'LISEZMOI.txt', 'en': 'README.txt', 'de': 'LIESMICH.txt', 'cs': 'README-cs.txt',
             'it': 'LEGGIMI.txt', 'ru': 'README-ru.txt', 'ja': 'README-ja.txt'}


@pytest.mark.parametrize('path', GUIDES, ids=lambda p: p.stem)
def test_the_guide_explains_how_to_install_and_check(path):
    """Section « Installer et lancer » : la version prête à l'emploi (page
    des versions, LISEZMOI de l'archive dans la langue du guide), avec
    Python, et la vérification ``--self-test``."""
    text = path.read_text(encoding='utf-8')
    start = text.index('id="installation"')
    section = text[start:text.index('<h', text.index('</h', start) + 4)]
    for words in ('https://github.com/MarjorieBurghart/Varians-Synchro/releases', README_OF[path.stem],
                  'demo_local_ALTO', 'requirements.txt', 'run.py', '--self-test',
                  'https://github.com/MarjorieBurghart/Varians-Synchro/issues'):
        assert words in section, (path.stem, words)
    assert (ROOT / 'packaging' / 'readme' / README_OF[path.stem]).is_file()
