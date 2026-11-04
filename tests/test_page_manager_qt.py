"""Optional offscreen checks for the actual page editor; requires PySide6."""
from __future__ import annotations

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
pytest.importorskip('PySide6.QtWidgets')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from varians_synchro.core import new_project, create_witness, add_image_source
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.page_management import page_ids_in_reading_order
from varians_synchro.ui_pages import PagesDialog


def test_page_dialog_reverse_drag_selection_and_thumbnails(tmp_path):
    app = QApplication.instance() or QApplication([])
    project = new_project()
    witness = create_witness(project, 'X')
    for name in ('z.png', 'm.png', 'a.png'):
        image = QImage(48, 32, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.green)
        assert image.save(str(tmp_path/name))
        add_image_source(witness, 'local', str(tmp_path/name))
    pages = create_pages(witness)
    for i,p in enumerate(pages):
        witness['alto_sources'].append({'id':str(i), 'path':'xml'+str(i)+'.xml',
            'pages':[{'lines':[], 'line_count':0, 'htr_line_count':0}]})
        bind_alto(witness,p['id'],str(i))
    before = page_ids_in_reading_order(witness)
    bindings = {p['id']:p['alto_binding'].copy() for p in pages}

    # The window opens on its own, without the main window.
    dialog = PagesDialog(project, witness)
    dialog.show()
    app.processEvents()
    assert dialog.pages.count() == 3
    dialog._load_visible_thumbnails()
    assert len(dialog._thumb_cache) == 3

    dialog.reverse_order()
    assert page_ids_in_reading_order(witness) == before[::-1]
    assert {p['id']:p['alto_binding'] for p in witness['pages']} == bindings

    # Simulate the exact item ordering produced by an internal Qt drag/drop.
    first = dialog.pages.takeItem(0)
    dialog.pages.insertItem(2, first)
    dialog._commit_displayed_order()
    assert page_ids_in_reading_order(witness) == dialog._item_ids()
    dialog.pages.item(0).setSelected(True)
    assert dialog.selected()[0]['id'] == dialog._item_ids()[0]
    dialog.close()
