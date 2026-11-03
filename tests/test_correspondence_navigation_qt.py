"""Optional live Qt tests: run under PySide6 (on Windows or offscreen CI)."""
import os
import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PySide6', reason='PySide6 needed for interactive overlay tests')
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from varians_synchro.physical_alignment import line_uid
from varians_synchro.overlay_filters import FILTER_AUTOMATIC_REVIEW
from varians_synchro.viewer import LineImagePanel, ClickableLine


def fixture_panel():
    app = QApplication.instance() or QApplication([])
    p = LineImagePanel({'id': 'B', 'pages': []})
    p._current_page = {'id': 'folio2'}
    p._page_lines = [{'text': ''}, {'text': ''}]
    p._update_line_texts()
    for n in range(2):
        rectangle = ClickableLine(QRectF(20, 20 + n * 50, 200, 35), p, n)
        p.scene.addItem(rectangle)
        p._rectangles.append(rectangle)
    return app, p


def test_preview_is_magenta_visible_through_filter_and_never_selected():
    app, p = fixture_panel()
    first, second = (line_uid('B', 'folio2', i) for i in (1, 2))
    p.set_line_styles({first: 'manual_validated', second: 'automatic_uncertain'})
    p.set_overlay_filter(FILTER_AUTOMATIC_REVIEW)
    assert not p._rectangles[0].isVisible()
    p.show_counterparts([first], navigate=False)
    assert p._rectangles[0].isVisible()
    assert p._rectangles[0].pen().color() == QColor(245, 70, 216)
    assert p.selected_ids() == []
    p._selected.add(first)
    p.refresh_overlay()
    assert p._rectangles[0].pen().color() == QColor(255, 160, 30)
    p.show_counterparts([], navigate=False)
    assert p._selected == {first}
    p.close()


def test_click_signal_distinct_from_programmatic_preview():
    app, p = fixture_panel()
    clicked = []
    p.line_clicked.connect(clicked.append)
    line = line_uid('B', 'folio2', 1)
    p.show_counterparts([line], navigate=False)
    assert clicked == []
    p.select_overlay_line(0, Qt.KeyboardModifier.NoModifier)
    assert clicked == [line]
    assert p.selected_ids() == []  # no documentary pages in this synthetic panel
    assert p._selected == {line}
    p.close()


def test_preview_can_request_another_folio_without_changing_selection():
    app, p = fixture_panel()
    uid = line_uid('B', 'folio1', 1)
    p._line_to_page[uid] = 'folio1'
    p.pages = [{'id': 'folio1'}, {'id': 'folio2'}]
    visited = []
    p.set_page = lambda page_id: visited.append(page_id) or True
    p._selected = {'some-manually-selected-line'}
    p.show_counterparts([uid], navigate=True)
    assert visited == ['folio1']
    assert p._preview_focus_pending
    assert p._selected == {'some-manually-selected-line'}
    p.close()
