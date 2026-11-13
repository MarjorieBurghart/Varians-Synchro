"""Optional Qt smoke tests for PERO polygon drawing and line hit areas."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QApplication
from varians_synchro.viewer import LineImagePanel, ClickableLine


def test_sloping_polygon_hit_region_is_not_bbox():
    _app = QApplication.instance() or QApplication([])      # gardée en vie pendant le test
    panel = LineImagePanel({'id':'A', 'pages': []})
    panel._current_page = {'id':'p1'}
    panel._page_lines = [{},{}]
    panel._rectangles = []
    polygons = [
        [(100,100),(920,160),(920,185),(100,125)],
        [(100,155),(920,215),(920,240),(100,180)],
    ]
    for i, polygon in enumerate(polygons):
        item = ClickableLine(QRectF(100,100+i*45,820,110), panel, i, polygon)
        panel.scene.addItem(item)
        panel._rectangles.append(item)
    panel.refresh_overlay()
    assert panel._rectangles[0].shape().contains(QPointF(500,147))
    assert not panel._rectangles[0].shape().contains(QPointF(500,170))
    assert panel.line_at_scene_pos(QPointF(500,147)) == 0
    assert panel.line_at_scene_pos(QPointF(500,195)) == 1
    assert panel.line_at_scene_pos(QPointF(500,170)) is None
    panel.close()
