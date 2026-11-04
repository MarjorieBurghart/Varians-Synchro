#!/usr/bin/env python3
"""Generate a source-grounded module inventory without executing application code.

Usage: python tools/generate_module_inventory.py
Outputs MAINTENANCE_PASSATION_V0856/annexes/INVENTAIRE_MODULES_AUTOGENERE.md
"""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'MAINTENANCE_PASSATION_V0856'/'annexes'/'INVENTAIRE_MODULES_AUTOGENERE.md'


def inventory_text() -> str:
    import re
    version = re.search(r"^VERSION = '([^']+)'", (ROOT/'varians_synchro'/'core.py').read_text(encoding='utf-8'),
                        re.MULTILINE).group(1)
    rows = [
        f'# Inventaire technique généré automatiquement (code v{version})',
        '',
        'Génération reproductible : `python tools/generate_module_inventory.py` depuis la racine.',
        'Inspection statique AST : **aucun module applicatif n’est importé ni exécuté**.',
        'Les numéros de ligne sont ceux de **cette livraison uniquement**.',
        '',
    ]
    modules = sorted((ROOT/'varians_synchro').glob('*.py'))
    rows += [f'**{len(modules)} fichiers Python** dans `varians_synchro/` (dont `__init__.py`).', '']
    for file in modules:
        source = file.read_text(encoding='utf-8')
        mod = ast.parse(source)
        functions = [n for n in mod.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n for n in mod.body if isinstance(n, ast.ClassDef)]
        internal = set()
        for node in ast.walk(mod):
            if isinstance(node, ast.ImportFrom) and node.level and node.module:
                internal.add(node.module.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('varians_synchro.'):
                internal.add(node.module.split('.')[1])
        rows.append(f'## `varians_synchro/{file.name}` ({len(source.splitlines())} lignes)')
        doc = ast.get_docstring(mod) or ''
        if doc:
            rows.append('**Objet (docstring source)** : ' + ' '.join(doc.split())[:650])
        if internal:
            rows.append('**Dépendances internes observées** : ' + ', '.join('`'+i+'`' for i in sorted(internal)))
        if classes:
            rows.append('**Classes déclarées au premier niveau** : ' + ', '.join('`'+n.name+'` (l.'+str(n.lineno)+')' for n in classes))
        if functions:
            rows.append('**Fonctions au premier niveau** : ' + ', '.join('`'+n.name+'` (l.'+str(n.lineno)+')' for n in functions))
        if not classes and not functions:
            rows.append('Pas de fonction ou classe déclarée au premier niveau.')
        rows.append('')
    rows += [
        '## Attention à la lecture', '',
        'Les méthodes des classes (notamment celles des fenêtres `ui_*`), les fonctions de tests et les importations dynamiques ne sont pas détaillés ici. Cette liste est **un point d’entrée**, pas une analyse d’appels complète. Les dépendances proviennent d’une inspection syntaxique (AST) et peuvent inclure des chemins conditionnels. Pour les contrats, consulter les chapitres métiers du dossier.', ''
    ]
    return '\n'.join(rows)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(inventory_text(), encoding='utf-8')
    print('Inventaire écrit :', OUTPUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
