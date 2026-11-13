"""Qt-only smoke checks for compact ALTO markers and overlap hit testing."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QApplication
from varians_synchro.viewer import LineImagePanel, ClickableLine


def test_compact_view_keeps_hit_rectangles_and_can_switch_to_full():
    _app = QApplication.instance() or QApplication([])      # gardée en vie pendant le test
    panel = LineImagePanel({'id':'A','pages':[]})
    panel._current_page={'id':'p1'}
    panel._page_lines=[{},{}]
    panel._rectangles=[]
    for i, y in enumerate((100,120)):
        item=ClickableLine(QRectF(0,y,200,35),panel,i)
        panel.scene.addItem(item)
        panel._rectangles.append(item)
    panel.refresh_overlay()
    assert not panel.compact_overlay.isChecked()  # full contours by default
    assert panel.line_at_scene_pos(QPointF(100,122)) == 0
    assert panel.line_at_scene_pos(QPointF(100,135)) == 1
    original=panel._rectangles[0].rect()
    panel.compact_overlay.setChecked(False)
    assert panel._rectangles[0].rect()==original
    panel.compact_overlay.setChecked(True)
    assert panel._rectangles[0].rect()==original
    panel.close()
