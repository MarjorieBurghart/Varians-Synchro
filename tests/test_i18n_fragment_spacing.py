"""Fragments de messages mis bout à bout par l'interface (« 12/40 » +
« lignes · » + …) : quand le français commence ou finit par une espace, la
traduction aussi, sinon les mots se collent à l'écran (« 12/40Zeilen ·F »).

Japonais : pas d'espace exigée en tête (« 12/40行 ») ni en fin après une
ponctuation pleine chasse (« ： », « 、 »…), qui porte déjà son blanc."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LANGS = ['en', 'de', 'cs', 'it', 'ru', 'ja']
FULL_WIDTH = tuple('：、。，）」』】・；！？')


def _catalog(lang):
    return {e.get('key'): (e.text or '') for e in ET.parse(ROOT / 'i18n' / f'{lang}.xml').getroot()}


def problems(lang):
    french, values = _catalog('fr'), _catalog(lang)
    found = []
    for key, source in french.items():
        text = values.get(key, '')
        if not text.strip():
            continue
        if source[:1].isspace() and not text[:1].isspace() and lang != 'ja':
            found.append((key, 'début'))
        if source[-1:].isspace() and not text[-1:].isspace() and not (
                lang == 'ja' and text.rstrip().endswith(FULL_WIDTH)):
            found.append((key, 'fin'))
    return found


@pytest.mark.parametrize('lang', LANGS)
def test_joined_fragments_keep_their_spaces(lang):
    assert problems(lang) == []
