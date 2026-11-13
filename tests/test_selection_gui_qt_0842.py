"""Interactive selection checks; execute with PySide6 on Windows / CI Qt."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from varians_synchro.viewer import LineImagePanel
from varians_synchro.physical_alignment import line_uid


def panel_fixture():
    app = QApplication.instance() or QApplication([])
    panel = LineImagePanel({'id':'Mu', 'pages':[]})
    folio1 = [line_uid('Mu','a',i) for i in (1,2,3)]
    folio2 = [line_uid('Mu','b',i) for i in (1,2,3)]
    panel._line_order = tuple(folio1 + folio2)
    panel._current_page = {'id':'a'}
    panel._page_lines = [{'text': f'line {i}'} for i in (1,2,3)]
    panel._update_line_texts()
    return app, panel, folio1, folio2


def test_default_full_contours_and_modifiers_across_folios():
    app, panel, one, two = panel_fixture()
    try:
        assert not panel.compact_overlay.isChecked()
        panel.select_overlay_line(0, Qt.KeyboardModifier.NoModifier)
        panel.select_overlay_line(2, Qt.KeyboardModifier.ControlModifier)
        assert panel.selected_ids() == [one[0], one[2]]
        panel._current_page = {'id':'b'}
        panel._update_line_texts()
        panel.select_overlay_line(1, Qt.KeyboardModifier.NoModifier)
        assert panel.selected_ids() == [two[1]]
        panel.select_overlay_line(2, Qt.KeyboardModifier.ShiftModifier)
        assert panel.selected_ids() == two[1:3]
        panel.select_overlay_line(0, Qt.KeyboardModifier.ControlModifier)
        assert panel.selected_ids() == two
    finally:
        panel.close()


def test_clicking_text_list_uses_same_policy_and_clears_other_folio():
    app, panel, one, two = panel_fixture()
    try:
        panel._selected = {two[2]}
        panel._sync_visible_selection()
        panel.show()
        panel.show_htr.setChecked(True)
        panel.lines.show()
        app.processEvents()
        panel.lines.resize(360, 200)
        app.processEvents()
        item = panel.lines.item(1)
        rect = panel.lines.visualItemRect(item)
        QTest.mouseClick(panel.lines.viewport(), Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, rect.center())
        assert panel.selected_ids() == [one[1]]
    finally:
        panel.close()
