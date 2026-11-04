"""« Créer un projet Varians pré-renseigné… » sans édition TEI associée au
pivot : plus de refus. Le projet reçoit une édition TEI vide, et les
messages disent comment y préparer les <pb/> et <lb/> du pivot dans Varians."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets
from varians_synchro.guided_ui import make_guided_window
from varians_synchro.i18n import tr
from varians_synchro.project_state import ProjectChangeTracker
from test_varians_094_compat import _project

YES = ui_widgets.QtMessageBox.StandardButton.Yes


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _export(monkeypatch, tmp_path, project):
    messages = []
    destination = tmp_path / 'vers-varians'
    destination.mkdir()

    def record(kind):
        def show(parent, title, text, *args):
            messages.append((kind, text))
            return YES
        return staticmethod(show)
    for kind in ('question', 'information', 'warning', 'critical'):
        monkeypatch.setattr(ui_widgets.QMessageBox, kind, record(kind))
    monkeypatch.setattr(ui_widgets.QtFileDialog, 'getExistingDirectory',
                        staticmethod(lambda *a, **k: str(destination)))
    window = make_guided_window()()
    window.project = project
    window._changes = ProjectChangeTracker(project)
    window.refresh()
    window.export_varians_project()
    window._suppress_close_confirmation = True
    window.close()
    return destination, messages


def test_without_tei_the_project_is_created_with_a_blank_edition(app, monkeypatch, tmp_path):
    project = _project(tmp_path)
    project['text_resources'] = []
    destination, messages = _export(monkeypatch, tmp_path, project)
    assert (destination / 'project.xml').is_file()
    assert 'Édition en préparation.' in (destination / 'xml' / 'edition.xml').read_text(encoding='utf-8')
    kinds = [kind for kind, _text in messages]
    assert kinds == ['question', 'information']
    question, done = messages[0][1], messages[1][1]
    assert tr('ui.final.export_project.no_tei') in question
    assert tr('ui.final.export_project.prepare_pivot') in question
    assert tr('ui.final.export_project.prepare_pivot') in done


def test_with_a_tei_the_messages_do_not_mention_a_blank_edition(app, monkeypatch, tmp_path):
    project = _project(tmp_path)
    destination, messages = _export(monkeypatch, tmp_path, project)
    assert (destination / 'project.xml').is_file()
    assert [kind for kind, _text in messages] == ['question', 'information']
    assert all(tr('ui.final.export_project.prepare_pivot') not in text for _kind, text in messages)
