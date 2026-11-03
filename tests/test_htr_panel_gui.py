"""Optional actual-Qt regression tests (skipped when PySide6 is unavailable).

Run on Windows in the user's normal Python environment, or offscreen on Linux.
"""
import os
import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6', reason='PySide6 needed for Qt widget tests')
from PySide6.QtWidgets import QApplication
from varians_synchro.viewer import LineImagePanel


def test_htr_checkbox_reclaims_image_space_and_keeps_zoom_and_selection():
    app = QApplication.instance() or QApplication([])
    panel = LineImagePanel({'id': 'T1', 'pages': []})
    panel.resize(750, 520)
    panel.show()
    app.processEvents()

    assert not panel.show_htr.isChecked()
    assert panel.htr_panel.isHidden()
    assert not panel.htr_panel.isVisible()
    hidden_image_height = panel.view.height()

    panel.view.scale(1.5, 1.5)
    original_zoom = panel.view.transform().m11()
    panel._selected = {'T1::example::line1'}
    panel.show_htr.setChecked(True)
    app.processEvents()
    assert panel.htr_panel.isVisible()
    assert panel.view.height() < hidden_image_height
    assert abs(panel.view.transform().m11() - original_zoom) < 0.000001
    assert panel._selected == {'T1::example::line1'}

    # The researcher may adjust the text height, or hide the text completely.
    panel.content_splitter.setSizes([240, 180])
    app.processEvents()
    panel.show_htr.setChecked(False)
    app.processEvents()
    assert panel.htr_panel.isHidden()
    assert panel.view.height() >= hidden_image_height - 2
    assert abs(panel.view.transform().m11() - original_zoom) < 0.000001
    assert panel._selected == {'T1::example::line1'}
    panel.close()
