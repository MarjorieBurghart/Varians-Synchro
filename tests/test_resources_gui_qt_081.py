"""Optional PySide6 smoke tests for the V0.8.0–V0.8.1 witness workflow.

Run in an isolated process on Windows/Linux/macOS with PySide6 installed.
CI without Qt marks the module skipped instead of pretending to test widgets.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
PySide6 = pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QPushButton, QFileDialog, QInputDialog
from PySide6.QtCore import Qt

from varians_synchro.guided_ui import make_guided_window
from varians_synchro.core import create_witness, new_project
from varians_synchro.project_state import ProjectChangeTracker


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_new_witness_entry_is_single_and_old_tools_gone(app):
    window = make_guided_window()()
    try:
        buttons = window.findChildren(QPushButton)
        assert len([x for x in buttons if x.objectName() == 'addWitnessResourcesButton']) == 1
        assert not any('TXT' in x.text() or 'V0.5' in x.text() for x in buttons)
    finally:
        window.close()


def test_create_project_cancel_path_preserves_current_project(app, monkeypatch):
    window = make_guided_window()()
    old = window.project
    try:
        monkeypatch.setattr(QInputDialog, 'getText', lambda *args, **kwargs: ('Projet test', True))
        monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: ('', ''))
        window.new()
        assert window.project is old
        assert window.path is None
    finally:
        window.close()


def test_resource_tree_shows_pivot_without_changing_identity(app):
    window = make_guided_window()()
    try:
        project = new_project('Projet réel')
        create_witness(project, 'Mu')
        create_witness(project, 'F')
        project['pivot_witness_id'] = 'Mu'
        window.project = project
        window._changes = ProjectChangeTracker(project)
        window.refresh()
        assert window.inventory.topLevelItemCount() == 2
        assert 'Mu' in window.inventory.topLevelItem(0).text(0)
        assert window.reference_box.currentData() == 'Mu'
        assert window.inventory.topLevelItem(1).data(0, Qt.ItemDataRole.UserRole) == 'F'
    finally:
        window.close()


def test_open_real_project_updates_visible_inventory(app, monkeypatch, tmp_path):
    """Actual PySide6 integration test; requires a Qt-capable test machine."""
    from varians_synchro.core import save_project
    project = new_project('Édition importée')
    create_witness(project, 'Mu')
    create_witness(project, 'F')
    project['pivot_witness_id'] = 'Mu'
    project_path = tmp_path / 'saved.vsynch'
    save_project(project, project_path)
    window = make_guided_window()()
    try:
        monkeypatch.setattr(QFileDialog, 'getOpenFileName',
                            lambda *args, **kwargs: (str(project_path), ''))
        window.open()
        assert window.path == str(project_path)
        assert window.project['name'] == 'Édition importée'
        assert window.inventory.topLevelItemCount() == 2
        assert window.reference_box.currentData() == 'Mu'
    finally:
        window.close()


def test_create_new_project_updates_visible_inventory(app, monkeypatch, tmp_path):
    window = make_guided_window()()
    project_path = tmp_path / 'new.vsynch'
    try:
        # There must be no leftover witness after making a new document.
        create_witness(window.project, 'Mu')
        monkeypatch.setattr(window, '_confirm_save_or_discard', lambda: True)
        monkeypatch.setattr(QInputDialog, 'getText',
                            lambda *args, **kwargs: ('Nouveau test', True))
        monkeypatch.setattr(QFileDialog, 'getSaveFileName',
                            lambda *args, **kwargs: (str(project_path), ''))
        window.new()
        assert window.project['name'] == 'Nouveau test'
        assert window.project['witnesses'] == []
        assert window.inventory.topLevelItemCount() == 0
        assert window.path == str(project_path)
        assert project_path.is_file()
    finally:
        window.close()
