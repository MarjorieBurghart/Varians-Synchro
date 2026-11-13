"""Optional real-Qt test; run in a Windows Spyder environment with PySide6."""
import os
import pytest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6', reason='PySide6 required for graphical overlay tests')
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication
from varians_synchro.physical_alignment import line_uid
from varians_synchro.viewer import LineImagePanel, ClickableLine
from varians_synchro.overlay_filters import FILTER_UNLINKED, FILTER_AUTOMATIC_REVIEW, FILTER_ALL


def test_visual_filters_keep_data_zoom_and_selection():
    _app = QApplication.instance() or QApplication([])      # gardée en vie pendant le test
    panel = LineImagePanel({'id': 'A', 'pages': []})
    panel._current_page = {'id': 'p1'}
    panel._page_lines = [{}, {}, {}]
    panel._rectangles = []
    for i in range(3):
        rectangle = ClickableLine(QRectF(0, i * 25, 100, 20), panel, i)
        panel.scene.addItem(rectangle)
        panel._rectangles.append(rectangle)
    first, second, third = (line_uid('A', 'p1', i) for i in range(1, 4))
    panel.set_line_styles({second: 'automatic_uncertain', third: 'manual_validated'})
    panel.view.scale(1.3, 1.3)
    original_zoom = panel.view.transform().m11()

    panel.set_overlay_filter(FILTER_UNLINKED)
    assert [rect.isVisible() for rect in panel._rectangles] == [True, False, False]
    panel.set_overlay_filter(FILTER_AUTOMATIC_REVIEW)
    assert [rect.isVisible() for rect in panel._rectangles] == [False, True, False]
    panel._selected.add(third)
    panel.refresh_overlay()
    assert [rect.isVisible() for rect in panel._rectangles] == [False, True, True]
    panel.set_overlay_filter(FILTER_ALL)
    assert all(rect.isVisible() for rect in panel._rectangles)
    assert panel._selected == {third}
    assert panel._line_styles == {second: 'automatic_uncertain', third: 'manual_validated'}
    assert abs(panel.view.transform().m11() - original_zoom) < 0.000001
    panel.close()
