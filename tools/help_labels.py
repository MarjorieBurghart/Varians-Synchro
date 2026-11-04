#!/usr/bin/env python3
"""Libellés d'interface cités dans le guide (``help/<langue>.html``).

Le guide balise chaque libellé qu'il cite :

- ``<b class="ui" data-tr="clé">…</b>`` : un texte de Varians-Synchro, clé
  du catalogue ``i18n/<langue>.xml`` ou texte littéral du code (un texte
  d'interface pas encore traduit, qui s'affiche alors en français) ;
- ``<b class="varians" data-varians="clé">…</b>`` : un texte de Varians, clé
  de son catalogue (``VARIANS_SOURCE``, sinon ``../Varians``).

Le texte de la balise est celui de l'écran dans la langue du guide, sans
les deux-points finaux. ``python tools/help_labels.py`` le remplit d'après
les catalogues ; ``--check`` liste seulement les écarts (le test
``tests/test_help_guides.py`` fait de même).
"""
from __future__ import annotations

import html
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELP_DIR = ROOT / 'help'
MARK = re.compile(r'<b class="(ui|varians)" data-(tr|varians)="([^"]+)">([^<]*)</b>')


def screen_text(text: str) -> str:
    """Le libellé tel que le guide le cite : sans deux-points final (« : » ou « ： »)."""
    return re.sub(r'[\s  ]*[:：]$', '', text.strip())


def synchro_label(key: str, language: str) -> str:
    sys.path.insert(0, str(ROOT))
    from varians_synchro.i18n import get_language, set_language, tr
    previous = get_language()
    set_language(language)
    try:
        return screen_text(tr(key))
    finally:
        set_language(previous)


def varians_source():
    for candidate in (os.environ.get('VARIANS_SOURCE'), ROOT.parent / 'Varians', ROOT.parent / 'varians'):
        if candidate and (Path(candidate) / 'i18n' / 'fr.xml').is_file():
            return Path(candidate)
    return None


def varians_catalog(language: str, source=None) -> dict | None:
    source = source or varians_source()
    if source is None:
        return None
    path = Path(source) / 'i18n' / f'{language}.xml'
    if not path.is_file():
        path = Path(source) / 'i18n' / 'fr.xml'
    return {entry.get('key'): entry.text or '' for entry in ET.parse(path).getroot()}


def marks(text: str):
    """(classe, clé, texte affiché) de chaque libellé balisé."""
    return [(kind, key, html.unescape(shown)) for kind, _attr, key, shown in MARK.findall(text)]


def expected(kind, key, language, catalog):
    if kind == 'ui':
        return synchro_label(key, language)
    if catalog is None:
        return None
    if key not in catalog:
        return f'<clé Varians inconnue : {key}>'
    return screen_text(catalog[key])


def check(path: Path, source=None):
    """Écarts de *path* : (clé, cité, attendu)."""
    language = path.stem
    catalog = varians_catalog(language, source)
    problems = []
    for kind, key, shown in marks(path.read_text(encoding='utf-8')):
        wanted = expected(kind, key, language, catalog)
        if wanted is not None and shown != wanted:
            problems.append((key, shown, wanted))
    return problems


def fill(path: Path, source=None) -> int:
    language = path.stem
    catalog = varians_catalog(language, source)
    changed = 0

    def replace(match):
        nonlocal changed
        kind, attr, key, shown = match.groups()
        wanted = expected(kind, key, language, catalog)
        if wanted is None or html.unescape(shown) == wanted:
            return match.group(0)
        changed += 1
        return f'<b class="{kind}" data-{attr}="{key}">{html.escape(wanted, quote=False)}</b>'

    text = path.read_text(encoding='utf-8')
    path.write_text(MARK.sub(replace, text), encoding='utf-8', newline='\n')
    return changed


def main(argv) -> int:
    only_check = '--check' in argv
    status = 0
    for path in sorted(HELP_DIR.glob('*.html')):
        if only_check:
            for key, shown, wanted in check(path):
                print(f'{path.name}: {key}: « {shown} » au lieu de « {wanted} »')
                status = 1
        else:
            print(f'{path.name}: {fill(path)} libellé(s) mis à jour')
    if varians_source() is None:
        print('Code source de Varians introuvable : libellés de Varians non vérifiés.')
    return status


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
