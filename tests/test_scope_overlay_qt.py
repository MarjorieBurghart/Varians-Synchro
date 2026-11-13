"""Optional Qt visual regression checks; needs PySide6 on the test machine."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from varians_synchro.viewer import LineImagePanel


def test_palette_is_distinct_and_ignores_have_dashed_grey_box():
    _app = QApplication.instance() or QApplication([])      # gardée en vie pendant le test
    panel = LineImagePanel.__new__(LineImagePanel)
    purple = panel._style_parameters('default')
    green = panel._style_parameters('manual_validated')
    blue = panel._style_parameters('automatic_validated')
    grey = panel._style_parameters('ignored')
    assert len({purple[0].name(),green[0].name(),blue[0].name(),grey[0].name()}) == 4
    assert purple[2] > 2.0
    assert grey[3] == Qt.PenStyle.DashLine
    assert panel._style_parameters('ignored', active=True)[0].name() != grey[0].name()
