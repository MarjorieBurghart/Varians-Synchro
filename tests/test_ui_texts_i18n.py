"""Textes de l'interface : tous traduits.

- Aucune phrase en dur dans les fenêtres (``ui_*.py``, ``viewer.py``) : chaque
  texte affiché passe par une clé du catalogue (ou par son texte français,
  alias de la clé). Les formats de fichiers (« XML (*.xml) ») et le nom du
  logiciel ne se traduisent pas.
- Chaque code que les moteurs renvoient pour un avertissement (repères, contrôle
  de cohérence, propositions, export) a son message dans le catalogue.
- La liste des groupes de la synchronisation dit l'état et le type d'un groupe
  dans la langue de l'interface, pas « [validated] … · correspondence ».
"""
from __future__ import annotations

import ast
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'varians_synchro'
CATALOG = ET.parse(ROOT / 'i18n' / 'fr.xml').getroot()
FRENCH = {entry.text for entry in CATALOG}
KEYS = {entry.get('key') for entry in CATALOG}
WINDOWS = sorted(CODE.glob('ui_*.py')) + [CODE / 'viewer.py']
CSS = re.compile(r'^\s*([a-z-]+\s*:\s*[^;]+;\s*)+$')
FILE_PATTERN = re.compile(r'\*?[\w-]*\.\w+')       # *.xml, images.json
NAMES = re.compile(r'Varians(-Synchro)?')


def _not_displayed(tree):
    """Nœuds dont le texte n'est pas montré : docstrings et chaînes isolées
    (commentaires), messages d'exception (traités par le lot des moteurs)."""
    hidden = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            hidden.add(id(node.value))
        if isinstance(node, ast.Raise) and node.exc is not None:
            hidden.update(id(inner) for inner in ast.walk(node.exc))
    return hidden


def _prose(text):
    """Une phrase à traduire : des mots, en dehors des motifs de fichiers, des
    sigles en capitales et du nom du logiciel."""
    if CSS.match(text) or not re.search(r'\s', text):
        return False
    words = re.findall(r'[A-Za-zÀ-ÿ]{3,}', NAMES.sub('', FILE_PATTERN.sub('', text)))
    return any(not word.isupper() for word in words)


def test_the_windows_display_no_untranslated_sentence():
    found = []
    for path in WINDOWS:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        hidden = _not_displayed(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in hidden
                    and node.value not in FRENCH and node.value not in KEYS and _prose(node.value)):
                found.append(f'{path.name}:{node.lineno}: {node.value!r}')
    assert found == []


def test_translated_literals_are_in_the_catalog():
    """``tr('…')`` avec un texte absent du catalogue l'affiche tel quel."""
    found = []
    for path in sorted(CODE.glob('*.py')):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'tr' and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value not in KEYS and node.args[0].value not in FRENCH):
                found.append(f'{path.name}:{node.lineno}: {node.args[0].value!r}')
    assert found == []


def _codes(module, pattern):
    return set(re.findall(pattern, (CODE / module).read_text(encoding='utf-8')))


ANCHORS = _codes('reading_stream.py', r"'reason': '([a-z_]+)'")
AUDIT = _codes('validation.py', r"_item\('[a-z]+', '([a-z_]+)'") - {'anchor_'}


@pytest.mark.parametrize('key', sorted(
    {'stream.warning.' + code for code in ANCHORS}
    | {'ui.audit.issue.anchor_' + code for code in ANCHORS}
    | {'ui.audit.issue.' + code for code in AUDIT}
    | {'progress.warning.' + code.replace('outside_anchors_', 'outside_anchors_start')
       for code in _codes('textual_progress.py', r"'reason': '([a-z_]+)'")}
    | {'progress.warning.outside_anchors_end'}
    | {'export.varians.reason.' + code for code in _codes('varians_export.py', r"reason = '([a-z_]+)'")}
    | {'tei.binding.status.' + code for code in _codes('tei_binding.py', r"'status':'([a-z_]+)'")}
    | {'ui.final.audit.severity.' + code for code in _codes('validation.py', r"_item\('([a-z]+)'")}
    | {'alignment.state.' + code for code in ('proposed', 'uncertain', 'validated')}
    | {'alignment.kind.correspondence'}))
def test_each_code_has_its_message(key):
    assert key in KEYS


def test_the_engines_still_produce_these_codes():
    """Garde-fou du test précédent : l'extraction trouve bien les codes."""
    assert {'stale_anchor', 'empty_anchor', 'crossing_or_overlapping_anchors'} <= ANCHORS
    assert {'invalid_reading_stream', 'stale_or_ignored_line'} <= AUDIT


# --- Dans les fenêtres -------------------------------------------------------

pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication  # noqa: E402

from varians_synchro.i18n import get_language, set_language, tr  # noqa: E402
from test_stale_links import setting  # noqa: E402,F401  (fixture)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def german():
    previous = get_language()
    set_language('de')
    yield
    set_language(previous)


def test_the_group_list_states_the_group_in_the_interface_language(app, german, setting):
    from varians_synchro.ui_pair import PairDialog
    project, _a, _b, session, first, _last = setting
    first['state'] = 'uncertain'
    dialog = PairDialog(project, session)
    dialog.review_filter.setCurrentIndex(dialog.review_filter.findData('all'))
    dialog.populate()
    texts = [dialog.links.item(i).text() for i in range(dialog.links.count())]
    dialog.close()
    assert len(texts) == 2
    for text in texts:
        assert 'validated' not in text and 'uncertain' not in text and 'correspondence' not in text
        assert tr('alignment.kind.correspondence') in text
    assert any(tr('alignment.state.uncertain') in text for text in texts)
    assert any(tr('alignment.state.validated') in text for text in texts)


def test_a_non_empty_folder_for_hd_copies_is_refused_with_its_own_message(app, setting, tmp_path,
                                                                        monkeypatch):
    from varians_synchro import imaging
    from varians_synchro.ui_pages import PagesDialog
    from varians_synchro.ui_widgets import QFileDialog, QMessageBox
    project, a, _b, _session, _first, _last = setting
    folder = tmp_path / 'occupé'
    folder.mkdir()
    (folder / 'autre.txt').write_text('x', encoding='utf-8')
    warnings = []
    monkeypatch.setattr(imaging, 'iiif_hd_url', lambda page: 'https://example.org/full.jpg')
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', staticmethod(lambda *a, **k: str(folder)))
    monkeypatch.setattr(QMessageBox, 'warning', staticmethod(lambda parent, title, text, *a, **k: warnings.append(text)))
    dialog = PagesDialog(project, a)
    monkeypatch.setattr(dialog, 'selected', lambda: [{'id': 'p', 'image_kind': 'iiif'}])
    dialog.download_hd()
    dialog.close()
    assert warnings == [tr('ui.pages.hd.choose_empty')]
    assert 'JSON' not in warnings[0]
