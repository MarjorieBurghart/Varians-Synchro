"""Non-Qt regression tests for project-save safety."""
import ast
from pathlib import Path

from varians_synchro.core import new_project, save_project, load_project, create_witness
from varians_synchro.project_state import ProjectChangeTracker, project_fingerprint
from varians_synchro.i18n import set_language, tr


def test_clean_start_change_and_save(tmp_path):
    project = new_project()
    tracker = ProjectChangeTracker(project)
    assert not tracker.is_modified(project)
    create_witness(project, 'Mu')
    assert tracker.is_modified(project)
    file = tmp_path / 'p.vsynch'
    save_project(project, file)
    tracker.mark_saved(project)
    assert not tracker.is_modified(project)
    assert not ProjectChangeTracker(load_project(file)).is_modified(load_project(file))


def test_nested_changes_and_reversion():
    project = new_project()
    create_witness(project, 'Mu')
    tracker = ProjectChangeTracker(project)
    project['witnesses'][0]['pages'].append({'id': 'p1', 'label': '3r', 'alto_binding': 'test'})
    assert tracker.is_modified(project)
    project['witnesses'][0]['pages'][0]['label'] = '3v'
    assert tracker.is_modified(project)
    project['witnesses'][0]['pages'].clear()
    assert not tracker.is_modified(project)


def test_session_and_ignored_line_changes():
    project = new_project()
    create_witness(project, 'Mu')
    tracker = ProjectChangeTracker(project)
    project['pair_sessions'].append({'links': []})
    assert tracker.is_modified(project)
    tracker.mark_saved(project)
    project['pair_sessions'][0]['links'].append({'id': 'x', 'state': 'validated'})
    assert tracker.is_modified(project)
    tracker.mark_saved(project)
    project['witnesses'][0]['ignored_line_ids'].append('Mu:p1:12')
    assert tracker.is_modified(project)


def test_new_project_is_marked_unsaved():
    p = new_project('Nouvelle édition')
    tracker = ProjectChangeTracker(p, newly_created=True)
    assert tracker.is_modified(p)
    tracker.mark_saved(p)
    assert not tracker.is_modified(p)
    other = new_project('Projet B')
    tracker.reset(other, newly_created=True)
    assert tracker.is_modified(other)
    tracker.reset(other)
    assert not tracker.is_modified(other)


def test_fingerprint_ignores_dict_order_but_not_values():
    a = {'a': [1, {'x': 3}], 'b': 'texte'}
    b = {'b': 'texte', 'a': [1, {'x': 3}]}
    assert project_fingerprint(a) == project_fingerprint(b)
    b['a'][1]['x'] = 4
    assert project_fingerprint(a) != project_fingerprint(b)


def test_ui_guards_close_new_open_and_language_handoff():
    source = Path(__file__).resolve().parents[1] / 'varians_synchro' / 'guided_ui.py'
    code = source.read_text(encoding='utf-8')
    tree = ast.parse(code)
    guided = next(n for f in tree.body if isinstance(f, ast.FunctionDef) and f.name=='make_guided_window'
                  for n in f.body if isinstance(n, ast.ClassDef) and n.name=='GuidedWindow')
    methods = {n.name: n for n in guided.body if isinstance(n, ast.FunctionDef)}
    for name in ('closeEvent','new','open','save','change_language'):
        assert name in methods
    for name in ('closeEvent','new','open'):
        assert '_confirm_save_or_discard' in ast.get_source_segment(code, methods[name])
    assert 'self._suppress_close_confirmation = True' in ast.get_source_segment(code,methods['change_language'])
    assert 'self._changes.mark_saved(self.project)' in ast.get_source_segment(code,methods['save'])
    assert 'return False' in ast.get_source_segment(code,methods['save'])


def test_new_strings_translated_both_languages():
    try:
        for lang in ('fr','en'):
            set_language(lang)
            for key in ('project.unsaved.title','project.unsaved.question',
                        'project.unsaved.save','project.unsaved.discard',
                        'project.unsaved.cancel','project.save_error'):
                assert tr(key)
                assert tr(key) != key
            assert tr('project.unsaved.question',name='Mu')
    finally:
        set_language('fr')
