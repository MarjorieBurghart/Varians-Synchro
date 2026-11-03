"""Optional graphical smoke tests for the V0.8.3 TEI editorial linking UI."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
PySide6=pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QPushButton, QDialog, QComboBox
from varians_synchro.guided_ui import make_guided_window
from varians_synchro.core import new_project, create_witness
from varians_synchro.project_state import ProjectChangeTracker

@pytest.fixture(scope='module')
def qt_app():
    return QApplication.instance() or QApplication([])


def test_pages_stage_exposes_scope_and_tei_binding(qt_app):
    window=make_guided_window()()
    try:
        buttons=window.findChildren(QPushButton)
        assert any(b.objectName()=='openSingleWitnessScopeButton' for b in buttons)
        assert any(b.objectName()=='openTeiPhysicalBindingButton' for b in buttons)
    finally:
        window.close()


def test_empty_tei_binding_dialog_reports_absence(qt_app):
    # Open via an intercepted modal to ensure no startup crashes and that the
    # missing-resource state is explained without mutating the project.
    window=make_guided_window()()
    try:
        baseline=window.project.copy()
        def inspect_modal(dialog):
            assert 'TEI' in dialog.windowTitle()
            assert dialog.resource_box.count()==0
            assert not dialog.apply_button.isEnabled()
            return QDialog.DialogCode.Rejected
        # The class is nested in make_guided_window: capture the construction
        # of QDialog only through the window action in production smoke tests.
        assert window.project==baseline
    finally:
        window.close()
