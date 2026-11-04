"""Fenêtre « Ordre de lecture » : pages, régions et lignes d’un témoin."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from .errors import localized_text
from .i18n import tr
from .imaging import mapped_alto_page
from .reading_stream import (anchor_intervals, page_regions, reading_stream,
                             reset_page_line_order, set_line_order, set_page_order,
                             set_region_order)
from .ui_widgets import fit_to_screen, QComboBox, QDialog, QLabel, QListWidget, QMessageBox, QPushButton


class ReadingOrderDialog(QDialog):
    """Review and adjust physical reading order without changing line UIDs.

    Page/region/line changes are persisted only with normal project Save.
    This is a J1 inspection/editor, NOT the new correspondence estimator.
    """
    def __init__(self, project, session, parent=None):
        super().__init__(parent)
        self.project = project
        self.session = session
        self.setWindowTitle(tr('stream.window.title'))
        fit_to_screen(self, 1080, 640)
        main = QVBoxLayout(self)
        hint = QLabel(tr('stream.window.help')); hint.setWordWrap(True)
        main.addWidget(hint)
        top = QHBoxLayout(); main.addLayout(top)
        self.witness_box = QComboBox()
        for w in project['witnesses']:
            if w['id'] in (session['reference_witness_id'], session['target_witness_id']):
                self.witness_box.addItem(f"{w['id']} — {w['label']}", w['id'])
        top.addWidget(QLabel(tr('stream.witness')))
        top.addWidget(self.witness_box)
        top.addStretch(1)
        self.witness_box.currentIndexChanged.connect(self.refresh_pages)

        columns = QHBoxLayout(); main.addLayout(columns, 1)
        self.page_list, self.region_list, self.line_list = QListWidget(), QListWidget(), QListWidget()
        for title, widget, up, down in (
            ('stream.pages', self.page_list, lambda: self.move_page(-1), lambda: self.move_page(1)),
            ('stream.regions', self.region_list, lambda: self.move_region(-1), lambda: self.move_region(1)),
            ('stream.lines', self.line_list, lambda: self.move_line(-1), lambda: self.move_line(1))):
            group = QVBoxLayout()
            group.addWidget(QLabel(tr(title)))
            group.addWidget(widget, 1)
            controls = QHBoxLayout()
            b1 = QPushButton(tr('stream.move_up')); b1.clicked.connect(up); controls.addWidget(b1)
            b2 = QPushButton(tr('stream.move_down')); b2.clicked.connect(down); controls.addWidget(b2)
            group.addLayout(controls)
            columns.addLayout(group, 1 if widget != self.line_list else 2)
        self.page_list.currentRowChanged.connect(self.refresh_regions)
        self.region_list.currentRowChanged.connect(self.refresh_lines)
        footer = QHBoxLayout(); main.addLayout(footer)
        reset = QPushButton(tr('stream.reset_lines')); reset.clicked.connect(self.reset_lines)
        footer.addWidget(reset)
        preview = QPushButton(tr('stream.preview')); preview.clicked.connect(self.preview_intervals)
        footer.addWidget(preview)
        footer.addStretch(1)
        close = QPushButton(tr('common.close')); close.clicked.connect(self.accept)
        footer.addWidget(close)
        self.status = QLabel(); self.status.setWordWrap(True); main.addWidget(self.status)
        self.refresh_pages()

    def witness(self):
        return next(w for w in self.project['witnesses'] if w['id'] == self.witness_box.currentData())

    def _page(self):
        idx = self.page_list.currentRow()
        return self._pages[idx] if 0 <= idx < len(self._pages) else None

    def refresh_pages(self, _=None, page_id=None):
        from .page_order import ordered_pages
        self._pages = [p for p in ordered_pages(self.witness())
                       if mapped_alto_page(self.witness(), p) is not None]
        self.page_list.blockSignals(True)
        self.page_list.clear()
        for page in self._pages:
            self.page_list.addItem(page.get('label') or page['id'])
        position = next((i for i,p in enumerate(self._pages) if p['id'] == page_id), 0)
        self.page_list.setCurrentRow(position if self._pages else -1)
        self.page_list.blockSignals(False)
        self.refresh_regions()

    def refresh_regions(self, _=None, region_id=None):
        page = self._page()
        self._regions = page_regions(self.witness(), page['id']) if page else []
        self.region_list.blockSignals(True)
        self.region_list.clear()
        for region in self._regions:
            self.region_list.addItem(region)
        index = self._regions.index(region_id) if region_id in self._regions else 0
        self.region_list.setCurrentRow(index if self._regions else -1)
        self.region_list.blockSignals(False)
        self.refresh_lines()

    def refresh_lines(self, _=None, line_id=None):
        page = self._page()
        region_idx = self.region_list.currentRow()
        region = self._regions[region_idx] if 0 <= region_idx < len(self._regions) else None
        self._visible_lines = [line for line in reading_stream(self.witness(), include_ignored=True)
                               if page and line['page_id'] == page['id'] and line['region_id'] == region]
        self.line_list.clear()
        for line in self._visible_lines:
            prefix = tr('stream.ignored') if line['ignored'] else ''
            self.line_list.addItem(f"{prefix}{line['ordinal']:>3} · " + (line['text'][:80] or '—'))
        idx = next((i for i,l in enumerate(self._visible_lines) if l['id'] == line_id), 0)
        self.line_list.setCurrentRow(idx if self._visible_lines else -1)
        self.status.setText(tr('stream.status', pages=len(self._pages),
                               lines=len(reading_stream(self.witness()))))

    def _swap(self, values, index, step):
        j = index + step
        if not 0 <= index < len(values) or not 0 <= j < len(values):
            return None
        values[index], values[j] = values[j], values[index]
        return j

    def move_page(self, step):
        from .page_order import ordered_pages
        page = self._page()
        if page is None: return
        displayed = [p['id'] for p in self._pages]
        j = self._swap(displayed, self.page_list.currentRow(), step)
        if j is None: return
        all_ids = [p['id'] for p in ordered_pages(self.witness())]
        selected = set(displayed)
        it = iter(displayed)
        new_ids = [next(it) if pid in selected else pid for pid in all_ids]
        set_page_order(self.witness(), new_ids)
        self.refresh_pages(page_id=page['id'])

    def move_region(self, step):
        page = self._page()
        if page is None: return
        regions = list(self._regions)
        idx = self.region_list.currentRow()
        j = self._swap(regions, idx, step)
        if j is None: return
        region_id = regions[j]
        set_region_order(self.witness(), page['id'], regions)
        self.refresh_regions(region_id=region_id)

    def move_line(self, step):
        page = self._page()
        idx = self.line_list.currentRow()
        if page is None or not 0 <= idx < len(self._visible_lines): return
        chosen = self._visible_lines[idx]['id']
        sequence = [line['id'] for line in reading_stream(self.witness(), include_ignored=True)
                    if line['page_id'] == page['id']]
        pos = sequence.index(chosen)
        # Fine-grained moves stay *within* one region. Regions have separate controls.
        neighbor = idx + step
        if not 0 <= neighbor < len(self._visible_lines): return
        other = self._visible_lines[neighbor]['id']
        other_pos = sequence.index(other)
        sequence[pos], sequence[other_pos] = sequence[other_pos], sequence[pos]
        set_line_order(self.witness(), page['id'], sequence)
        self.refresh_lines(line_id=chosen)

    def reset_lines(self):
        page = self._page()
        if page:
            reset_page_line_order(self.witness(), page['id'])
            self.refresh_regions()

    def preview_intervals(self):
        try:
            result = anchor_intervals(self.project, self.session)
            summary = tr('stream.preview.summary', anchors=len(result['anchors']),
                         intervals=len(result['intervals']), warnings=len(result['warnings']))
            details = []
            for number, section in enumerate(result['intervals'], 1):
                details.append(f"{number}. {self.session['reference_witness_id']}: "
                               f"{section['reference_count']} ({', '.join(section['reference_pages'])}) ↔ "
                               f"{self.session['target_witness_id']}: {section['target_count']} "
                               f"({', '.join(section['target_pages'])})")
            for warning in result['warnings']:
                reason = tr('stream.warning.' + warning['reason'])
                details.append(f"! {reason} ({warning['link_id']})")
            QMessageBox.information(self, tr('stream.preview'), summary + '\n\n' + '\n'.join(details))
        except Exception as exc:
            QMessageBox.warning(self, tr('stream.preview'), localized_text(exc))
