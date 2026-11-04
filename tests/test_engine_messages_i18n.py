"""Messages des moteurs (erreurs et avertissements) : traduits.

Les moteurs écrivent en français (``str(exc)``, journaux, tests) ; l'interface
les montre dans sa langue par ``errors.localized_text``.

- Un message fixe est la valeur française d'une clé du catalogue.
- Un message avec des valeurs n'est jamais composé à la main (f-string,
  concaténation) : c'est ``localized(Type, 'clé', nom=valeur)`` ou
  ``Localized('clé', nom=valeur)``, et la clé attend exactement ces valeurs.
- Les fenêtres affichent une erreur par ``localized_text(exc)``, jamais par
  ``str(exc)``.
Seules quelques erreurs de programmation, qu'aucun utilisateur ne peut
provoquer, restent hors catalogue.
"""
from __future__ import annotations

import ast
import re
import string
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from varians_synchro.errors import localized_text
from varians_synchro.i18n import get_language, set_language, tr

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'varians_synchro'
CATALOG = {entry.get('key'): entry.text for entry in ET.parse(ROOT / 'i18n' / 'fr.xml').getroot()}
FRENCH = set(CATALOG.values())
# self_test.py écrit un rapport JSON pour la construction et la CI, jamais
# montré dans l'interface : ses messages restent en français.
NOT_ENGINES = {'gui.py', 'guided_ui.py', 'viewer.py', 'i18n.py', 'errors.py', 'self_test.py'}
ENGINES = [path for path in sorted(CODE.glob('*.py'))
           if not path.name.startswith('ui_') and path.name not in NOT_ENGINES]
WINDOWS = sorted(CODE.glob('ui_*.py')) + [CODE / 'viewer.py']
# Erreurs de programmation : paramètres internes, invariants.
PROGRAMMER = {'min_match doit être >= 2', 'min_support doit être entre 0 et 1', 'Unknown review filter',
              'Overlapping tentative textual-progress groups', 'Configuration Varians incomplète',
              "f'Unknown overlay filter: {filter_name}'"}


def _messages():
    """(module, ligne, nœud) des messages d'exception et d'avertissement."""
    for path in ENGINES:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
                yield path.name, node.lineno, node.exc.args[0]
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'append' and node.args
                    and re.search(r'\b(warnings|alerts)\b', ast.unparse(node.func.value))):
                yield path.name, node.lineno, node.args[0]


def test_fixed_messages_are_in_the_catalog():
    missing = [f'{module}:{line}: {node.value!r}' for module, line, node in _messages()
               if isinstance(node, ast.Constant) and isinstance(node.value, str)
               and node.value not in FRENCH and node.value not in PROGRAMMER]
    assert missing == []


def test_no_message_is_composed_by_hand():
    composed = [f'{module}:{line}: {ast.unparse(node)}' for module, line, node in _messages()
                if isinstance(node, (ast.JoinedStr, ast.BinOp)) and ast.unparse(node) not in PROGRAMMER]
    assert composed == []


def _placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_keyed_messages_exist_and_take_their_values():
    problems = []
    for path in ENGINES:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, 'id', None)
            args = node.args[1:] if name == 'localized' else node.args if name == 'Localized' else None
            if args is None or not isinstance(args[0], ast.Constant):
                continue          # clé passée par une variable : voir le test suivant
            key = args[0].value
            given = {keyword.arg for keyword in node.keywords}
            if key not in CATALOG:
                problems.append(f'{path.name}:{node.lineno}: clé inconnue {key}')
            elif _placeholders(CATALOG[key]) != given:
                problems.append(f'{path.name}:{node.lineno}: {key} attend {_placeholders(CATALOG[key])}, reçoit {given}')
    assert problems == []


def test_error_keys_named_in_the_engines_exist():
    named = {node.value for path in ENGINES for node in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
             if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith('error.')}
    assert named and named <= set(CATALOG), sorted(named - set(CATALOG))


def test_the_windows_show_engine_errors_through_localized_text():
    """``str(exc)`` montrerait le français ; ``tr(str(exc))`` perdrait les
    valeurs d'un message à clé."""
    found = []
    for path in WINDOWS:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'str' and len(node.args) == 1
                    and isinstance(node.args[0], ast.Name) and node.args[0].id in ('exc', 'e', 'error', 'err')):
                found.append(f'{path.name}:{node.lineno}')
    assert found == []


@pytest.fixture
def german():
    previous = get_language()
    set_language('de')
    yield
    set_language(previous)


def test_an_error_with_values_is_shown_in_the_interface_language(german):
    from varians_synchro.core import new_project
    from varians_synchro.line_scope import update_ignored_lines
    with pytest.raises(ValueError) as caught:
        update_ignored_lines(new_project('Essai'), {'X': []})
    assert str(caught.value) == 'Témoin inconnu : X'
    shown = localized_text(caught.value)
    assert shown == tr('error.scope.unknown_witness', witness='X') and 'X' in shown
    assert shown != str(caught.value)


def test_a_fixed_error_is_shown_in_the_interface_language(german):
    from varians_synchro.core import new_project
    from varians_synchro.rapid_review import verify_before_review
    with pytest.raises(ValueError) as caught:
        verify_before_review(new_project('Essai'), {'links': []}, [])
    assert localized_text(caught.value) == tr(str(caught.value)) != str(caught.value)


def test_a_keyed_warning_stays_french_text_and_shows_translated(german):
    from varians_synchro.errors import Localized
    warning = Localized('error.core.xml_missing', witness='A', path='/x/A.xml')
    assert warning == 'A : XML (ALTO/PAGE) introuvable : /x/A.xml'
    assert localized_text(warning) == tr('error.core.xml_missing', witness='A', path='/x/A.xml')
