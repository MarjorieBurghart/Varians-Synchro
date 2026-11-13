"""Optional graphical smoke tests for the V0.8.3 TEI editorial linking UI."""
import copy
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
PySide6=pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QPushButton
from varians_synchro.guided_ui import make_guided_window

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
    # The window opens without crashing and explains the missing resource
    # without changing the project.
    from varians_synchro.ui_tei_binding import TEIPhysicalBindingDialog
    window=make_guided_window()()
    try:
        baseline=copy.deepcopy(window.project)
        dialog=TEIPhysicalBindingDialog(window.project, window)
        assert 'TEI' in dialog.windowTitle()
        assert dialog.resource_box.count()==0
        assert not dialog.apply_button.isEnabled()
        dialog.reject()
        assert window.project==baseline
    finally:
        window.close()
