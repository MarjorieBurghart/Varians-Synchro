"""Lecture du code source de l'interface pour les tests statiques (AST).

Les fenêtres sont réparties dans les modules ``varians_synchro/ui_*.py`` ;
``ui_class`` trouve une classe par son nom, où qu'elle soit déclarée."""
from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / 'varians_synchro'


def ui_files():
    return sorted(PACKAGE.glob('ui_*.py'))


def ui_class(name):
    """(source du module, nœud ClassDef, chemin) de la classe ``name``."""
    for path in ui_files():
        source = path.read_text(encoding='utf-8')
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ClassDef) and node.name == name:
                return source, node, path
    raise LookupError(name)


def ui_method(class_name, method_name):
    """Code source de la méthode ``class_name.method_name``."""
    source, cls, _path = ui_class(class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    return ast.get_source_segment(source, method)
