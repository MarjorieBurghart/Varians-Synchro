#!/usr/bin/env python3
"""Non-destructive delivery checks for Varians-Synchro (version: core.VERSION).

Checks required handoff files, package version and JSON schema, translation
coverage and generated AST inventory. Never edits files. File integrity is
tracked by the Git history (the former SHA-256 release manifests were removed
when the code moved to a Git repository).
"""
from __future__ import annotations
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'MAINTENANCE_PASSATION_V0856'
ESSENTIAL = [f'{n:02d}_{suffix}.md' for n,suffix in [
    (0,'LIRE_EN_PREMIER'), (1,'PREMIERE_REPRISE'), (2,'ARCHITECTURE_ET_FLUX'),
    (3,'CARTE_DU_CODE'), (4,'FORMATS_ET_PERSISTANCE'),
    (5,'MOTEURS_ET_INVARIANTS'), (6,'TEI_ET_EDITIONS'),
    (7,'IMAGES_IIIF_ALTO_PAGE'), (8,'EXPORT_VERS_VARIANS'),
    (9,'INTERFACE_ET_I18N'), (10,'TESTS_ET_RECETTE'),
    (11,'CONVENTIONS_ET_EVOLUTIONS'), (12,'RISQUES_ET_LIMITES'),
    (13,'REGISTRE_DECISIONS'), (14,'CHECKLIST_PASSATION')]]


def DOCUMENTS() -> list[Path]:
    """Les documents Markdown du dépôt : racine, docs/ et dossier de passation."""
    return sorted([*ROOT.glob('*.md'), *(ROOT/'docs').rglob('*.md'), *DOC.rglob('*.md')])


def check_links(markdown: Path) -> list[str]:
    errors = []
    data = markdown.read_text(encoding='utf-8')
    for link in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', data):
        if link.startswith(('https:', 'http:', '#', 'mailto:')):
            continue
        path = (markdown.parent/link.split('#')[0]).resolve()
        if not path.is_file():
            errors.append(f'{markdown.relative_to(ROOT)}: lien introuvable {link}')
    return errors


def app_version() -> str:
    """Version de Varians-Synchro, lue dans ``core.VERSION`` (sans l'importer)."""
    code = (ROOT/'varians_synchro'/'core.py').read_text(encoding='utf-8')
    return re.search(r"^VERSION = '([^']+)'", code, re.MULTILINE).group(1)


def check() -> list[str]:
    errors=[]
    for file in ESSENTIAL + ['annexes/INVENTAIRE_MODULES_AUTOGENERE.md',
                             'annexes/TRACABILITE_CODE_TESTS.md']:
        if not (DOC/file).is_file():errors.append(f'Dossier incomplet : {file}')
    for file in DOCUMENTS():
        errors.extend(check_links(file))
    code = (ROOT/'varians_synchro'/'core.py').read_text(encoding='utf-8')
    version = app_version()
    # La version de core.py est celle qu'annonce le dossier de passation.
    if f'application v{version}' not in (DOC/'00_LIRE_EN_PREMIER.md').read_text(encoding='utf-8'):
        errors.append(f'Version Python non alignée : {version} absente de 00_LIRE_EN_PREMIER.md')
    if "SCHEMA = 'varians-synchro-project'" not in code:errors.append('Nom du format modifié')
    catalog={}
    for lang in 'fr en de cs it ru ja'.split():
        p=ROOT/'i18n'/f'{lang}.xml'
        if not p.exists():errors.append(f'Catalogue absent : {lang}');continue
        vals={}
        for entry in ET.parse(p).getroot():
            key=entry.get('key')
            if not key or key in vals:errors.append(f'Clé invalide/dupliquée : {lang}: {key}')
            vals[key]=entry.text
        # Même nombre de clés que le catalogue français (le premier lu).
        expected = len(vals) if lang == 'fr' else expected
        if len(vals)!=expected:errors.append(f'Couverture {lang}: {len(vals)} au lieu de {expected}')
        catalog[lang]=set(vals)
    if catalog and len(set(map(frozenset,catalog.values())))!=1:
        errors.append('Catalogues : clés différentes')
    from generate_module_inventory import inventory_text
    target=DOC/'annexes'/'INVENTAIRE_MODULES_AUTOGENERE.md'
    if target.exists() and target.read_text(encoding='utf-8')!=inventory_text():
        errors.append('Inventaire AST non synchronisé avec le code')
    return errors


def main():
    problems=check()
    if problems:
        print('ECHEC maintenance:');print('\n'.join(' - '+x for x in problems));return 1
    print(f'OK — dossiers de passation, catalogues (7 langues, mêmes clés), inventaire AST, version {app_version()} et liens cohérents.');return 0


if __name__=='__main__':
    sys.exit(main())
