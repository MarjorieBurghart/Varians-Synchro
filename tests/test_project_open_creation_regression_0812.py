"""Regression: V0.8.1/0.8.1.1 changed the file path but not self.project.

The critical `GuidedWindow.new/open` methods are extracted and executed without
Qt, so these tests remain active on build servers without PySide6.
"""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from varians_synchro.core import (create_witness, load_project, new_project,
                                  save_project)
from varians_synchro.project_state import ProjectChangeTracker


_SOURCE = Path(__file__).resolve().parents[1] / 'varians_synchro' / 'guided_ui.py'


def _method(name: str, *, open_path='', save_path='', name_value='Nouveau', name_ok=True):
    """Compile actual source method with fake dialogs, not a rewritten copy."""
    tree = ast.parse(_SOURCE.read_text(encoding='utf-8'))
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name == 'make_guided_window')
    cls = next(n for n in factory.body if isinstance(n, ast.ClassDef)
               and n.name == 'GuidedWindow')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    method.decorator_list = []
    code = compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                   str(_SOURCE), 'exec')
    file_dialog = SimpleNamespace(
        getOpenFileName=lambda *a: (str(open_path), ''),
        getSaveFileName=lambda *a: (str(save_path), ''),
    )
    dialogs = []
    message_box = SimpleNamespace(
        critical=lambda *a: dialogs.append(('critical', a)),
        warning=lambda *a: dialogs.append(('warning', a)),
    )
    scope = {'__package__': 'varians_synchro',
             'QFileDialog': file_dialog,
             'QInputDialog': SimpleNamespace(getText=lambda *a: (name_value, name_ok)),
             'QMessageBox': message_box,
             'tr': lambda key: key,
             'new_project': new_project,
             'load_project': load_project,
             'Path': Path}
    exec(code, scope)
    return scope[name], dialogs


class FakeWindow:
    def __init__(self, project=None, path=None, *, allow=True):
        self.project = project if project is not None else new_project()
        self.path = path
        self._changes = ProjectChangeTracker(self.project)
        self.allow = allow
        self.refreshed = 0

    def _confirm_save_or_discard(self):
        return self.allow

    def refresh(self):
        self.refreshed += 1


def _populated_project():
    project = new_project('Édition Mu–F')
    mu = create_witness(project, 'Mu', 'Munich')
    fr = create_witness(project, 'F', 'Fribourg')
    project['pivot_witness_id'] = 'Mu'
    mu['pages'] = [{'id': 'Mu-2v', 'label': '2v', 'alto_binding': {'source_id': 'xml_mu', 'page_index': 0}}]
    mu['ignored_line_ids'] = ['mu_ignored_1']
    fr['pages'] = [{'id': 'canvas_F_14v', 'label': '14v', 'alto_binding': {'source_id': 'xml_f', 'page_index': 0}}]
    project['pair_sessions'].append({'id': 'link-set', 'reference_witness_id': 'Mu',
                                      'target_witness_id': 'F', 'kind': 'physical-pair',
                                      'links': [{'id': 'association-validée', 'state': 'validated'}]})
    return project


def test_open_replaces_document_and_retains_exact_project_contents(tmp_path):
    expected = _populated_project()
    file = tmp_path / 'test.vsynch'
    save_project(expected, file)
    original_bytes = file.read_bytes()
    win = FakeWindow()
    method, dialogs = _method('open', open_path=file)
    method(win)
    assert win.path == str(file)
    assert win.project == expected
    assert win.refreshed == 1
    assert not win._changes.is_modified(win.project)
    assert file.read_bytes() == original_bytes
    assert not dialogs


def test_cancel_open_never_changes_file_pointer_or_document(tmp_path):
    saved = _populated_project()
    file = tmp_path / 'test.vsynch'
    save_project(saved, file)
    current = new_project('Projet courant')
    win = FakeWindow(current, 'ancien.vsynch', allow=False)
    method, _ = _method('open', open_path=file)
    method(win)
    assert win.project is current
    assert win.path == 'ancien.vsynch'
    assert win.refreshed == 0


def test_new_creates_selected_file_and_switches_to_it(tmp_path):
    original = _populated_project()
    win = FakeWindow(original, path=None)
    dest = tmp_path / 'nouvelle_édition.vsynch'
    method, dialogs = _method('new', save_path=dest, name_value='Nouvelle édition')
    method(win)
    assert win.path == str(dest)
    assert win.project['name'] == 'Nouvelle édition'
    assert win.project['witnesses'] == []
    assert load_project(dest) == win.project
    assert win.refreshed == 1
    assert not win._changes.is_modified(win.project)
    assert original['witnesses'][0]['id'] == 'Mu'
    assert not dialogs


def test_new_cancel_at_path_selection_leaves_current_document_intact():
    current = _populated_project()
    win = FakeWindow(current, path='ancien.vsynch')
    method, _ = _method('new', save_path='')
    method(win)
    assert win.project is current
    assert win.path == 'ancien.vsynch'
    assert win.refreshed == 0


def test_open_invalid_file_cannot_replace_existing_document(tmp_path):
    invalid_file = tmp_path / 'invalid.vsynch'
    invalid_file.write_text('{invalide', encoding='utf-8')
    current = _populated_project()
    win = FakeWindow(current, path='ancien.vsynch')
    method, dialogs = _method('open', open_path=invalid_file)
    method(win)
    assert win.project is current
    assert win.path == 'ancien.vsynch'
    assert win.refreshed == 0
    assert dialogs and dialogs[0][0] == 'critical'


def test_no_unreachable_project_assignment_after_return():
    # Static check guards against accidentally reintroducing the indentation
    # error in either of the two UI entry points.
    tree = ast.parse(_SOURCE.read_text(encoding='utf-8'))
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name == 'make_guided_window')
    cls = next(n for n in factory.body if isinstance(n, ast.ClassDef)
               and n.name == 'GuidedWindow')
    for name in ('new', 'open'):
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        for branch in ast.walk(method):
            if isinstance(branch, (ast.If, ast.ExceptHandler, ast.Try)):
                for body in (getattr(branch, 'body', []), getattr(branch, 'orelse', [])):
                    for pos, statement in enumerate(body[:-1]):
                        if isinstance(statement, ast.Return):
                            assert not any(isinstance(n, ast.Assign)
                                           and any(isinstance(t, ast.Attribute) and t.attr == 'project'
                                                   for t in n.targets)
                                           for n in body[pos+1:])
