"""Fenêtre « Liaison TEI ↔ lignes physiques » : contrôle visuel d’une ligne TEI sur l’image, sur un brouillon du projet."""
from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QLineEdit, QListWidgetItem,
                               QMessageBox as QtMessageBox, QPlainTextEdit, QScrollArea,
                               QSplitter, QVBoxLayout, QWidget)

from .i18n import tr
from .ui_widgets import (_run_modal, QComboBox, QDialog, QLabel, QListWidget, QMessageBox,
                         QPushButton)


# A running fetch must outlive a dialog closed before IIIF answers.
_tei_preview_threads = set()


class TEILineFetchThread(QThread):
    loaded = Signal(bytes)
    failed = Signal(str)

    def __init__(self, descriptor):
        super().__init__()
        self.descriptor = descriptor

    def run(self):
        from .tei_visual import fetch_preview_bytes
        try:
            self.loaded.emit(fetch_preview_bytes(self.descriptor))
        except Exception as exc:
            self.failed.emit(str(exc))


class TEIReviewCard(QGroupBox):
    """TEI text + true ALTO/PAGE crop; no project mutation.

    A fresh request serial prevents a slow, stale IIIF response from being
    shown next to a newer TEI line. Image loading never blocks the dialog.
    """
    def __init__(self, title, inspect_callback, parent=None):
        super().__init__(tr(title), parent)
        self.inspect_callback = inspect_callback
        self._request_serial = 0
        self._descriptor = None
        self.status = 'unavailable'
        self.pair = None
        layout = QVBoxLayout(self)
        self.meta = QLabel()
        self.meta.setWordWrap(True)
        layout.addWidget(self.meta)
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.text.setTextFormat(Qt.TextFormat.PlainText)
        self.text.setObjectName('teiVisualLineText')
        self.text.setStyleSheet('font-weight: 600; padding: 4px 0;')
        layout.addWidget(self.text)
        self.picture = QLabel(tr('tei.visual.no_preview'))
        self.picture.setMinimumHeight(90)
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture.setStyleSheet('background-color: #303236; color: #eee; border-radius: 4px; padding: 8px;')
        self.picture.setWordWrap(True)
        layout.addWidget(self.picture)
        self.image_notice = QLabel()
        self.image_notice.setWordWrap(True)
        layout.addWidget(self.image_notice)
        actions = QHBoxLayout()
        self.inspect_button = QPushButton(tr('tei.visual.inspect'))
        self.inspect_button.setEnabled(False)
        self.inspect_button.clicked.connect(self.inspect)
        actions.addWidget(self.inspect_button)
        actions.addStretch()
        layout.addLayout(actions)

    def inspect(self):
        if self.pair:
            self.inspect_callback(self.pair)

    def clear_card(self):
        self._request_serial += 1
        self.pair = None
        self._descriptor = None
        self.status = 'unavailable'
        self.meta.setText('')
        self.text.setText('')
        self.picture.setPixmap(QPixmap())
        self.picture.setText(tr('tei.visual.no_preview'))
        self.image_notice.setText('')
        self.inspect_button.setEnabled(False)

    def set_pair(self, project, witness_id, pair):
        from .tei_visual import line_preview_descriptor
        self.clear_card()
        if not pair:
            return
        self.pair = pair
        self.meta.setText(tr('tei.visual.identification',
                    index=pair['tei_ordinal'], page=pair.get('page_label') or '?',
                    line=pair['physical_ordinal'], key=pair['tei_key']))
        self.text.setText(pair.get('tei_text') or tr('tei.visual.empty_text'))
        self.inspect_button.setEnabled(True)
        try:
            self._descriptor = line_preview_descriptor(project, witness_id, pair)
        except (ValueError, OSError) as exc:
            self.status = 'unavailable'
            self.picture.setText(tr('tei.visual.unavailable'))
            self.image_notice.setText(str(exc))
            return
        self.status = 'loading'
        self.picture.setText(tr('tei.visual.loading'))
        serial = self._request_serial
        worker = TEILineFetchThread(self._descriptor)
        _tei_preview_threads.add(worker)
        worker.finished.connect(lambda w=worker: _tei_preview_threads.discard(w))
        worker.loaded.connect(lambda data, current=serial: self._show_image(data, current))
        worker.failed.connect(lambda error, current=serial: self._show_error(error, current))
        worker.start()

    def _show_error(self, error, serial):
        from shiboken6 import isValid
        if not isValid(self) or serial != self._request_serial:
            return
        self.status = 'unavailable'
        self.picture.setPixmap(QPixmap())
        self.picture.setText(tr('tei.visual.unavailable'))
        self.image_notice.setText(error)

    def _show_image(self, data, serial):
        from shiboken6 import isValid
        if not isValid(self) or serial != self._request_serial or not self._descriptor:
            return
        from .tei_visual import render_transform
        try:
            image = QImage.fromData(data)
            if image.isNull():
                raise ValueError(tr('tei.visual.decode_error'))
            model = render_transform(self._descriptor, image.width(), image.height())
            x, y, w, h = model['crop']
            cropped = image.copy(x, y, w, h).convertToFormat(QImage.Format.Format_ARGB32)
            if cropped.isNull():
                raise ValueError(tr('tei.visual.decode_error'))
            painter = QPainter(cropped)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                points = QPolygonF([QPointF(float(px), float(py)) for px, py in model['polygon']])
                painter.setPen(QPen(QColor(255, 190, 35, 240), max(2.0, min(w, h) / 100.0)))
                painter.setBrush(QBrush(QColor(255, 190, 35, 45)))
                painter.drawPolygon(points)
            finally:
                painter.end()
            pix = QPixmap.fromImage(cropped)
            self.picture.setPixmap(pix.scaled(690, 178, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
            self.status = 'ready'
            self.image_notice.setText(tr('tei.visual.highlight'))
        except (ValueError, TypeError, OSError) as exc:
            self._show_error(str(exc), serial)


class TEIPhysicalBindingDialog(QDialog):
    """V0.8.4.1: a single, selected TEI line and its physical image.

    Only the selected line is fetched; navigating to the last line or any
    intermediate line replaces the existing preview. An explicit warning
    is retained when both endpoints were not successfully previewed.
    """
    def __init__(self, project, parent=None):
        super().__init__(parent)
        # A draft: « Réanalyser » and the binding change only this copy,
        # written back to the project by « Appliquer » (commit). « Annuler »
        # thus closes without changing anything, as its tooltip says.
        self._live_project = project
        self.project = copy.deepcopy(project)
        self.preview = None
        self._pairs = []
        self._previewed_endpoints = set()
        self.setWindowTitle(tr('tei.binding.title'))
        self.resize(1200, 850)
        layout = QVBoxLayout(self)
        hint = QLabel(tr('tei.binding.help'))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QHBoxLayout()
        form.addWidget(QLabel(tr('tei.binding.witness')))
        self.witness_box = QComboBox()
        for witness in project.get('witnesses', []):
            if any(r.get('kind') == 'tei' and r.get('witness_id') == witness['id']
                   for r in project.get('text_resources', [])):
                self.witness_box.addItem(witness['id'], witness['id'])
        form.addWidget(self.witness_box, 1)
        form.addWidget(QLabel(tr('tei.binding.edition')))
        self.resource_box = QComboBox()
        form.addWidget(self.resource_box, 2)
        layout.addLayout(form)

        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMaximumHeight(115)
        self.summary.setObjectName('teiPhysicalBindingPreview')
        layout.addWidget(self.summary)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel(tr('tei.visual.line_list')))
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('tei.visual.search'))
        self.search.textChanged.connect(self.filter_lines)
        left_layout.addWidget(self.search)
        self.tei_line_list = QListWidget()
        self.tei_line_list.setObjectName('teiVisualLineList')
        self.tei_line_list.currentItemChanged.connect(self.show_selected_line)
        left_layout.addWidget(self.tei_line_list, 1)
        nav = QHBoxLayout()
        beginning = QPushButton(tr('tei.visual.begin'))
        beginning.clicked.connect(lambda: self.select_ordinal(1))
        nav.addWidget(beginning)
        ending = QPushButton(tr('tei.visual.end'))
        ending.clicked.connect(self.select_last)
        nav.addWidget(ending)
        left_layout.addLayout(nav)
        splitter.addWidget(left)

        visual_scroll = QScrollArea()
        visual_scroll.setWidgetResizable(True)
        visual_content = QWidget()
        visual_layout = QVBoxLayout(visual_content)
        visual_layout.addWidget(QLabel(tr('tei.visual.single_help')))
        self.line_card = TEIReviewCard('tei.visual.selected', self.open_line_viewer)
        self.line_card.setObjectName('teiVisualSelectedCard')
        visual_layout.addWidget(self.line_card)
        visual_layout.addStretch()
        visual_scroll.setWidget(visual_content)
        splitter.addWidget(visual_scroll)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        footer = QHBoxLayout()
        layout.addLayout(footer)
        refresh_button = QPushButton(tr('tei.binding.preview'))
        refresh_button.clicked.connect(self.refresh_preview)
        footer.addWidget(refresh_button)
        reload_button = QPushButton(tr('tei.binding.reload'))
        reload_button.clicked.connect(self.reload_tei_source)
        footer.addWidget(reload_button)
        self.apply_button = QPushButton(tr('tei.binding.apply'))
        self.apply_button.setObjectName('applyTeiPhysicalBindingButton')
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.commit)
        footer.addWidget(self.apply_button)
        cancel = QPushButton(tr('resources.cancel'))
        cancel.clicked.connect(self.reject)
        cancel.setToolTip(tr('ui.resources.cancel.tip'))
        footer.addWidget(cancel)
        self.witness_box.currentIndexChanged.connect(self.reload_resources)
        self.resource_box.currentIndexChanged.connect(self.refresh_preview)
        self.reload_resources()

    def reload_resources(self, *args):
        self.resource_box.blockSignals(True)
        self.resource_box.clear()
        witness_id = self.witness_box.currentData()
        for r in self.project.get('text_resources', []):
            if r.get('kind') == 'tei' and r.get('witness_id') == witness_id:
                self.resource_box.addItem(Path(r['path']).name, r['id'])
        self.resource_box.blockSignals(False)
        self.refresh_preview()

    def refresh_preview(self, *args):
        from .tei_binding import preview_tei_binding, tei_binding_status
        self.preview = None
        self._pairs = []
        self._previewed_endpoints.clear()
        self.apply_button.setEnabled(False)
        self.tei_line_list.clear()
        self.line_card.clear_card()
        # A different TEI/witness should always reopen at its first line,
        # even if a search was active for the previous edition.
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        witness_id = self.witness_box.currentData()
        resource_id = self.resource_box.currentData()
        if not witness_id or not resource_id:
            self.summary.setPlainText(tr('tei.binding.no_resource'))
            return
        try:
            proposal = preview_tei_binding(self.project, witness_id, resource_id)
            current = tei_binding_status(self.project, witness_id, resource_id)
            lines = [tr('tei.binding.counts', tei=proposal['tei_count'],
                        physical=proposal['physical_count']),
                     tr('tei.binding.current', state=tr('tei.binding.status.' + current['status']))]
            for problem in proposal['diagnostics']:
                lines.append('⚠ ' + problem['message'])
            lines.append(tr('tei.binding.ready') if proposal['eligible']
                         else tr('tei.binding.not_ready'))
            self.summary.setPlainText('\n'.join(lines))
            self.preview = proposal
            self.apply_button.setText(tr('tei.binding.replace') if current['status'] == 'stale'
                                      else tr('tei.binding.apply'))
            self.apply_button.setEnabled(proposal['eligible'] and current['status'] != 'valid')
            if not proposal['eligible']:
                return  # Never display dubious lines as certified correspondences.
            self._pairs = proposal['pairs']
            # Show only the first image on entry. The list selects it
            # after signals are unblocked in filter_lines().
            self.filter_lines(select_first=True)
        except Exception as exc:
            self.summary.setPlainText(str(exc))

    def filter_lines(self, *args, select_first=False):
        query = self.search.text().casefold().strip()
        # Preserve the current preview when typing a search: a remote IIIF
        # request must be launched by choosing a result, not every keystroke.
        active = self.line_card.pair
        selected_ordinal = active['tei_ordinal'] if active else None
        same_row = -1
        self.tei_line_list.blockSignals(True)
        self.tei_line_list.clear()
        for pair in self._pairs:
            caption = (f"{pair['tei_ordinal']:>4}  {pair.get('tei_text') or '∅'}"
                       f"   [{pair.get('page_label') or '?'}:{pair['physical_ordinal']}]")
            if query and query not in caption.casefold():
                continue
            item = QListWidgetItem(caption)
            item.setData(Qt.ItemDataRole.UserRole, pair['tei_ordinal'])
            self.tei_line_list.addItem(item)
            if pair['tei_ordinal'] == selected_ordinal:
                same_row = self.tei_line_list.count() - 1
        if same_row >= 0:
            self.tei_line_list.setCurrentRow(same_row)
        self.tei_line_list.blockSignals(False)
        if select_first and self.tei_line_list.count():
            # The default selection triggers exactly one preview fetch.
            self.tei_line_list.setCurrentRow(0)

    def select_ordinal(self, ordinal):
        self.search.clear()
        for i in range(self.tei_line_list.count()):
            item = self.tei_line_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == ordinal:
                self.tei_line_list.setCurrentRow(i)
                self.tei_line_list.scrollToItem(item)
                return

    def select_last(self):
        if self._pairs:
            self.select_ordinal(self._pairs[-1]['tei_ordinal'])

    def _remember_loaded_endpoint(self):
        pair = self.line_card.pair
        if pair and self.line_card.status == 'ready' and self._pairs:
            ordinal = pair['tei_ordinal']
            if ordinal in (self._pairs[0]['tei_ordinal'], self._pairs[-1]['tei_ordinal']):
                self._previewed_endpoints.add(ordinal)

    def show_selected_line(self, current, previous=None):
        if not current or not self.preview or not self.preview['eligible']:
            return
        ordinal = current.data(Qt.ItemDataRole.UserRole)
        if self.line_card.pair and self.line_card.pair['tei_ordinal'] == ordinal:
            return  # Filtering must not download the same image again.
        pair = next((p for p in self._pairs if p['tei_ordinal'] == ordinal), None)
        if pair:
            self._remember_loaded_endpoint()
            self.line_card.set_pair(self.project, self.witness_box.currentData(), pair)

    def open_line_viewer(self, pair):
        # Reuse the existing, zoomable page image and polygon overlays.
        from .viewer import LineImagePanel
        witness = next(w for w in self.project['witnesses']
                       if w['id'] == self.witness_box.currentData())
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('tei.visual.viewer_title'))
        dialog.resize(1060, 750)
        layout = QVBoxLayout(dialog)
        panel = LineImagePanel(witness, dialog, initial_page_id=pair['page_id'])
        layout.addWidget(panel, 1)
        layout.addWidget(QLabel(pair.get('tei_text') or tr('tei.visual.empty_text')))
        close = QPushButton(tr('common.close'))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        panel.show_counterparts([pair['physical_line_id']], navigate=True)
        _run_modal(dialog)

    def reload_tei_source(self):
        from .tei_binding import refresh_tei_source
        witness_id = self.witness_box.currentData()
        resource_id = self.resource_box.currentData()
        if not resource_id:
            return
        resource = next(r for r in self.project['text_resources'] if r['id'] == resource_id)
        has_binding = bool(resource.get('tei_binding'))
        if has_binding:
            answer = QMessageBox.question(self, tr('tei.binding.title'),
                tr('tei.binding.reload_confirm'),
                QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
                QtMessageBox.StandardButton.No)
            if answer != QtMessageBox.StandardButton.Yes:
                return
        try:
            refresh_tei_source(self.project, witness_id, resource_id,
                               replace_binding=has_binding)
            self.refresh_preview()
        except Exception as exc:
            QMessageBox.warning(self, tr('tei.binding.title'), str(exc))

    def commit(self):
        from .tei_binding import apply_tei_binding, tei_binding_status
        if not self.preview or not self.preview['eligible']:
            return
        reply = QMessageBox.question(self, tr('tei.binding.title'),
            tr('tei.binding.confirm', count=len(self.preview['pairs'])),
            QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
            QtMessageBox.StandardButton.No)
        if reply != QtMessageBox.StandardButton.Yes:
            return
        # Visual verification may fail independently of the TEI/physical
        # signature (e.g. Gallica temporarily unavailable). Never imply
        # that the user actually inspected an image that did not load.
        self._remember_loaded_endpoint()
        endpoints = {self._pairs[0]['tei_ordinal'], self._pairs[-1]['tei_ordinal']}
        if not endpoints.issubset(self._previewed_endpoints):
            response = QMessageBox.question(
                self, tr('tei.binding.title'), tr('tei.visual.no_images_confirm'),
                QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
                QtMessageBox.StandardButton.No)
            if response != QtMessageBox.StandardButton.Yes:
                return
        try:
            current = tei_binding_status(self.project, self.witness_box.currentData(),
                                         self.resource_box.currentData())
            result = apply_tei_binding(self.project, self.witness_box.currentData(),
                                       self.resource_box.currentData(), self.preview,
                                       replace=current['status'] == 'stale')
            # Reloads and binding of the draft, now confirmed (only TEI
            # resources are changed by this window).
            self._live_project['text_resources'] = self.project['text_resources']
            QMessageBox.information(self, tr('tei.binding.title'),
                tr('tei.binding.success', count=result['count']))
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, tr('tei.binding.title'), str(exc))
            self.refresh_preview()
