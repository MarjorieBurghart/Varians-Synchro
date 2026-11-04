"""Reusable manuscript page viewer with clickable ALTO overlay.

Images can be IIIF or local. Full physical lines are the interaction unit;
HTR is supplementary and never needed for visual selection. A 4200px-wide
IIIF request provides useful magnification without downloading all canvases.
"""
from __future__ import annotations
from .imaging import image_bytes, mapped_alto_page
from .page_order import ordered_pages
from .errors import localized_text
from .i18n import tr
from .physical_alignment import line_uid
from .overlay_filters import FILTER_ALL, FILTERS, overlay_visible
from .overlay_selection import choose_line_at, choose_line_geometry
from .alto_geometry import page_line_polygons
from .reading_stream import reading_stream
from .selection_policy import update_line_selection
from .ui_widgets import call_soon
from PySide6.QtCore import Qt, QRectF, QPointF, QThread, Signal, QItemSelectionModel
from PySide6.QtGui import QPixmap, QPen, QColor, QBrush, QImage, QPainter, QPolygonF, QPainterPath
from shiboken6 import isValid
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QListWidget, QHBoxLayout, QComboBox, QPushButton,
    QAbstractItemView, QCheckBox, QSplitter, QSizePolicy)

_ACTIVE_FETCH_THREADS = set()


class FetchThread(QThread):
    loaded = Signal(bytes)
    failed = Signal(str)

    def __init__(self, page, width=4200):
        super().__init__()
        self.page = page
        self.width = width

    def run(self):
        # Some IIIF servers reject a requested resolution above their limit.
        # Retry only explicit size/parameter failures, never rate limits (429).
        from urllib.error import HTTPError
        widths = (self.width, 2500, 1600) if self.page.get('image_kind') == 'iiif' else (self.width,)
        for attempt, width in enumerate(dict.fromkeys(widths)):
            try:
                self.loaded.emit(image_bytes(self.page, max_width=width))
                return
            except HTTPError as exc:
                if exc.code not in (400, 404, 413, 422) or attempt == len(widths)-1:
                    self.failed.emit(f'HTTP {exc.code} : {exc.reason}')
                    return
            except Exception as exc:
                self.failed.emit(localized_text(exc))
                return


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor(38, 41, 45))

    def wheelEvent(self, event):
        if event.angleDelta().y():
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            scale = self.transform().m11()
            if (factor > 1 and scale < 18) or (factor < 1 and scale > 0.025):
                self.scale(factor, factor)
                self.scene().update()  # Recalculate compact markers at new scale
            event.accept()
        else:
            super().wheelEvent(event)


class ClickableLine(QGraphicsRectItem):
    def __init__(self, rectangle, panel, ordinal, polygon=None):
        # Keep the underlying ALTO bounding rectangle for zoom and coordinate
        # diagnostics. When available, use the precise TextLine polygon for
        # both display AND mouse hit-testing; it may be slanted.
        super().__init__(rectangle)
        self.panel = panel
        self.ordinal = ordinal
        self.alto_polygon = QPolygonF([QPointF(x, y) for x, y in polygon]) if polygon else None
        if self.alto_polygon is not None:
            self.setRect(self.alto_polygon.boundingRect())
        self.setAcceptHoverEvents(True)
        self.setZValue(10)
        self.setToolTip(f"{tr('common.line')} {ordinal + 1} — " + tr('ui.cliquer.pour.selectionner.ctrl.maj.selection.multiple'))

    def paint(self, painter, option, widget=None):
        """Compact, readable markers over the unchanged original ALTO hit box.

        A full rectangle can be useful diagnostically, but at page overview a
        long TextLine rectangle often runs across whitespace or overlaps with
        its neighbours. Display a short coloured stroke at the line's start
        instead; active/corresponding lines are still shown as full boxes.
        """
        if not self.panel.compact_overlay.isChecked() or self.panel.is_emphasized(self.ordinal):
            if self.alto_polygon is not None:
                painter.setPen(self.pen())
                painter.setBrush(self.brush())
                painter.drawPolygon(self.alto_polygon)
            else:
                super().paint(painter, option, widget)
            return
        bounds = self.rect()
        if bounds.isEmpty():
            return
        scale = max(0.001, abs(self.panel.view.transform().m11()))
        # A clearly visible 18 screen-pixel stroke, clipped inside the source
        # rectangle; kept crisp at any zoom by the cosmetic pen.
        length = min(bounds.width(), 18.0 / scale)
        y = bounds.center().y()
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(bounds.left(), y), QPointF(bounds.left() + length, y))
        painter.drawEllipse(QPointF(bounds.left(), y), 2.5 / scale, 2.5 / scale)

    def shape(self):
        if self.alto_polygon is None:
            return super().shape()
        path = QPainterPath()
        path.addPolygon(self.alto_polygon)
        path.closeSubpath()
        return path

    def scene_polygon(self):
        if self.alto_polygon is None:
            return None
        return [[p.x(), p.y()] for p in self.mapToScene(self.alto_polygon)]

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.panel.select_overlay_at(self.ordinal, event.scenePos(), event.modifiers())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.panel.zoom_to_line(self.panel.line_at_scene_pos(event.scenePos(), fallback=self.ordinal))
        event.accept()


class WitnessLineList(QListWidget):
    """Apply the same click modifiers in the text list and the image overlay.

    Qt's ExtendedSelection ordinarily selects only the *visible page*. Our
    documentary selection may include other folios, so route deliberate clicks
    through the witness-wide policy instead of Qt's local-page selection model.
    """
    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self._panel = panel

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                self.setFocus()
                self._panel.select_overlay_line(index.row(), event.modifiers())
                event.accept()
                return
        super().mousePressEvent(event)


class LineImagePanel(QWidget):
    line_clicked = Signal(str)  # deliberate click on a physical ALTO line UID
    selection_cleared = Signal()  # explicit clear must also clear pink previews

    """A witness viewer with page selector, zoom, overlay and persistent selection.

    Selected line IDs survive page changes; link groups may span pages.
    `selected_ids()` returns IDs ordered by documentary page/line order.
    A caller may also provide per-line synchronisation styles so that already
    linked lines are visible directly on the manuscript image.
    """
    def __init__(self, witness, parent=None, *, initial_page_id=None, only_alto=True):
        super().__init__(parent)
        self.witness = witness
        self.pages = ordered_pages(witness)
        if only_alto:
            self.pages = [page for page in self.pages if mapped_alto_page(witness, page)]
        self._selected = set()
        self._tei_text_by_line = {}
        self._rectangles = []
        self._page_lines = []
        self._last_anchor = None  # Stable physical UID, even across folios.
        # Explicit per-page/region/line reading order also drives Shift ranges.
        self._line_order = self._reading_order()
        self._worker = None
        self._current_page = None
        self._pixmap_item = None
        self._request_serial = 0
        self._closed = False
        self._line_styles = {}
        self._compact_user_modified = False
        self._updating_compact = False
        self._overlay_filter = FILTER_ALL
        self._counterpart_ids = set()  # transient; NEVER in selected_ids()
        self._preview_focus_pending = False
        self._preview_switched_page = False
        self._line_to_page = {}
        for page in self.pages:
            data = mapped_alto_page(self.witness, page) or {}
            for index, _ in enumerate(data.get('lines', []), 1):
                self._line_to_page[line_uid(self.witness['id'], page['id'], index)] = page['id']
        if not self._line_order:
            self._line_order = tuple(self._line_to_page)

        root = QVBoxLayout(self)
        root.setContentsMargins(3, 3, 3, 3)
        root.setSpacing(5)
        header = QHBoxLayout(); root.addLayout(header)
        header.addWidget(QLabel(f'<b>{witness["id"]}</b>'))
        self.page_combo = QComboBox(); self.page_combo.setMinimumWidth(110)
        for page in self.pages:
            available = '●' if mapped_alto_page(witness, page) else '○'
            self.page_combo.addItem(f'{available} {page.get("label") or page["id"]}', page['id'])
        header.addWidget(self.page_combo, 1)
        self.prev = QPushButton('◀'); self.prev.setToolTip(tr('viewer.previous_page'))
        self.next = QPushButton('▶'); self.next.setToolTip(tr('viewer.next_page'))
        for b in (self.prev, self.next): header.addWidget(b)
        self.prev.clicked.connect(lambda: self.switch_offset(-1))
        self.next.clicked.connect(lambda: self.switch_offset(1))
        self.page_combo.currentIndexChanged.connect(self._on_page_changed)

        controls = QHBoxLayout(); root.addLayout(controls)
        for label, tip, handler in (
            ('−', 'Dézoomer', lambda: self.view.scale(0.8, 0.8)),
            ('+', 'Agrandir', lambda: self.view.scale(1.25, 1.25)),
            ('Adapter', 'Afficher la page entière', self.fit_page),
            ('Ligne', 'Agrandir la ligne sélectionnée', self.focus_selected),
        ):
            button = QPushButton(tr(label)); button.setToolTip(tr(tip))
            button.clicked.connect(handler); controls.addWidget(button)
        self.overlay_toggle = QCheckBox(tr('viewer.alto.toggle')); self.overlay_toggle.setChecked(True)
        self.overlay_toggle.toggled.connect(self.refresh_overlay)
        controls.addWidget(self.overlay_toggle)
        self.compact_overlay = QCheckBox(tr('viewer.compact_overlay'))
        self.compact_overlay.setChecked(False)
        self.compact_overlay.setToolTip(tr('viewer.compact_overlay.tip'))
        self.compact_overlay.toggled.connect(self._compact_toggled)
        controls.addWidget(self.compact_overlay)
        self.show_htr = QCheckBox(tr('viewer.htr.toggle')); self.show_htr.setChecked(False)
        # Do not merely remove HTR words from the list: the complete HTR pane
        # must disappear so the manuscript can use the reclaimed height.
        self.show_htr.toggled.connect(self._toggle_htr_panel)
        controls.addWidget(self.show_htr)
        controls.addStretch(1)

        # The line list is still the internal selection model when hidden:
        # overlay clicks update it programmatically, preserving Ctrl/Shift,
        # selected IDs across folios and the manually validated links.
        clear = QPushButton(tr('viewer.clear_selection'))
        clear.setToolTip(tr('viewer.clear_selection.tip'))
        clear.clicked.connect(self.clear_selection)
        controls.addWidget(clear)

        self.scene = QGraphicsScene(self)
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Splitter allows resizing HTR *when enabled*, while hiding that entire
        # widget gives 100% of the available splitter area back to the image.
        self.content_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(self.view)
        self.htr_panel = QWidget(self.content_splitter)
        htr_layout = QVBoxLayout(self.htr_panel)
        htr_layout.setContentsMargins(0, 0, 0, 0)
        htr_layout.setSpacing(0)
        self.lines = WitnessLineList(self, self.htr_panel)
        self.lines.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.lines.itemSelectionChanged.connect(self._record_selection)
        self.lines.currentRowChanged.connect(self.focus_line)
        htr_layout.addWidget(self.lines)
        self.content_splitter.addWidget(self.htr_panel)
        self.content_splitter.setStretchFactor(0, 5)
        self.content_splitter.setStretchFactor(1, 1)
        self._htr_height = 105  # restored on first activation, adjustable later
        self.htr_panel.hide()   # HTR is optional and OFF by default
        root.addWidget(self.content_splitter, 1)
        self.status = QLabel(tr('viewer.select_page')); self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.selection_status = QLabel(tr('ui.0.ligne.selectionnee')); root.addWidget(self.selection_status)
        if self.pages:
            if initial_page_id:
                ix = next((i for i, p in enumerate(self.pages) if p['id'] == initial_page_id), 0)
                self.page_combo.setCurrentIndex(ix)
            if self._current_page is None:
                self._on_page_changed(self.page_combo.currentIndex())

    def _compact_toggled(self, checked):
        if not self._updating_compact:
            self._compact_user_modified = True
        self.refresh_overlay()

    def _set_default_overlay_mode(self, has_polygons):
        """Always default to full ALTO/PAGE outlines (user can opt in to compact).

        Image loading, page switching and polygon detection must never change
        the checkbox behind the user's back.
        """
        return

    def _toggle_htr_panel(self, checked):
        """Expand/collapse HTR without losing manuscript zoom or line selection.

        The QSplitter redistributes the freed space to QGraphicsView.  The
        centre of the visible image is restored after the layout settles.
        """
        previous_center = self.view.mapToScene(self.view.viewport().rect().center())
        if not checked and self.htr_panel.isVisible():
            sizes = self.content_splitter.sizes()
            if len(sizes) >= 2 and sizes[1] > 0:
                self._htr_height = sizes[1]
        self.htr_panel.setVisible(bool(checked))
        self._update_line_texts()
        if checked:
            def restore_htr_height():
                if not self.show_htr.isChecked():
                    return
                total = self.content_splitter.height()
                if total > 0:
                    htr = min(self._htr_height, max(45, total // 2))
                    self.content_splitter.setSizes([max(1, total - htr), htr])
            call_soon(self, restore_htr_height)
        # Layout size changes are asynchronous; never call fit_page() here.
        # That would destroy the user's custom zoom on every checkbox click.
        call_soon(self, lambda p=previous_center: self.view.centerOn(p))


    def set_line_styles(self, styles):
        """Assign an overlay style per line UID.

        Styles are semantic keys such as ``manual_validated`` or
        ``automatic_uncertain``. Unknown keys fall back to the unsynchronised
        appearance. Selection always has priority over these styles.
        """
        self._line_styles = dict(styles or {})
        self.refresh_overlay()

    def set_overlay_filter(self, filter_name):
        """Hide unrelated line boxes without changing zoom, data or selection.

        The filter is scoped to the current pair session, not the whole corpus.
        Active selections remain visible so researchers can finish their work.
        """
        if filter_name not in FILTERS:
            raise ValueError(f'Unknown overlay filter: {filter_name}')
        self._overlay_filter = filter_name
        self.refresh_overlay()

    def show_counterparts(self, line_ids, *, navigate=True):
        """Highlight related lines without changing manual selections.

        A preview may span several folios. Show every related line when its
        folio is opened, preferring the currently displayed folio when useful.
        Automatically switch/centre only when the user clicks a linked line.
        """
        self._counterpart_ids = set(line_ids or [])
        self._preview_focus_pending = False
        self._preview_switched_page = False
        self.refresh_overlay()
        available = set(self._counterpart_ids) & self._line_to_page.keys()
        if not navigate or not available:
            return len(available)
        current_id = self._current_page['id'] if self._current_page else None
        current_matches = any(self._line_to_page[uid] == current_id for uid in available)
        if current_matches:
            target_page_id = current_id
        else:
            target_page_id = next(
                (p['id'] for p in self.pages if any(self._line_to_page[uid] == p['id'] for uid in available)),
                None,
            )
        if target_page_id is None:
            return 0
        changed_page = target_page_id != current_id
        self._preview_focus_pending = True
        self._preview_switched_page = changed_page
        if changed_page:
            # The page image is fetched asynchronously; _on_image will zoom to
            # its correspondences once the new image + ALTO overlay are ready.
            if not self.set_page(target_page_id):
                self._preview_focus_pending = False
                return 0
        elif self._pixmap_item is not None:
            self._focus_counterparts()
        return len(available)

    def _focus_counterparts(self):
        if not self._preview_focus_pending or not self._current_page or self._pixmap_item is None:
            return
        rectangles = []
        for i, item in enumerate(self._rectangles, 1):
            uid = line_uid(self.witness['id'], self._current_page['id'], i)
            if uid in self._counterpart_ids and item is not None:
                rectangles.append(item.sceneBoundingRect())
        self._preview_focus_pending = False
        if not rectangles:
            return
        combined = QRectF(rectangles[0])
        for rect in rectangles[1:]:
            combined = combined.united(rect)
        if self._preview_switched_page:
            # Leave enough page context to read the passage, not just a crop
            # of a single line. On the same folio, preserve the user's zoom.
            scene = self.scene.sceneRect()
            dx = max(scene.width() * 0.07, combined.width() * 0.28)
            dy = max(scene.height() * 0.05, combined.height() * 1.6)
            region = combined.adjusted(-dx, -dy, dx, dy).intersected(scene)
            if region.isValid() and not region.isEmpty():
                self.view.fitInView(region, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.centerOn(combined.center())
        self._preview_switched_page = False

    def _style_parameters(self, key, active=False, counterpart=False):
        if active:
            return QColor(255, 160, 30), QColor(255, 155, 25, 78), 3.0, Qt.PenStyle.SolidLine
        if counterpart:
            # Magenta: a linked line displayed for inspection, not selected.
            return QColor(245, 70, 216), QColor(245, 70, 216, 85), 3.4, Qt.PenStyle.SolidLine
        styles = {
            'default': (QColor(116, 42, 201), QColor(116, 42, 201, 38), 2.15, Qt.PenStyle.SolidLine),
            'ignored': (QColor(119, 119, 119), QColor(119, 119, 119, 19), 1.45, Qt.PenStyle.DashLine),
            'manual_validated': (QColor(24, 143, 74), QColor(24, 143, 74, 58), 2.3, Qt.PenStyle.SolidLine),
            'manual_uncertain': (QColor(24, 143, 74), QColor(24, 143, 74, 30), 2.2, Qt.PenStyle.DashLine),
            'automatic_validated': (QColor(24, 97, 209), QColor(24, 97, 209, 55), 2.3, Qt.PenStyle.SolidLine),
            'automatic_uncertain': (QColor(24, 97, 209), QColor(24, 97, 209, 28), 2.2, Qt.PenStyle.DashLine),
            'absence': (QColor(214, 70, 70), QColor(214, 70, 70, 35), 2.0, Qt.PenStyle.DotLine),
        }
        return styles.get(key, styles['default'])

    def closeEvent(self, event):
        self._closed = True
        self._request_serial += 1
        super().closeEvent(event)

    def switch_offset(self, delta):
        index = self.page_combo.currentIndex() + delta
        if 0 <= index < self.page_combo.count():
            self.page_combo.setCurrentIndex(index)

    def set_page(self, page_id):
        index = self.page_combo.findData(page_id)
        if index >= 0:
            self.page_combo.setCurrentIndex(index)
            if self._current_page is None:
                self._on_page_changed(index)
            return True
        return False

    def _on_page_changed(self, index):
        if not 0 <= index < len(self.pages): return
        page = self.pages[index]
        self._current_page = page
        self._page_lines = (mapped_alto_page(self.witness, page) or {}).get('lines', [])
        self._rectangles = []
        self._pixmap_item = None
        self.scene.clear()
        # Preserve the stable selection anchor when navigating between folios.
        self._update_line_texts()
        self._request_serial += 1
        serial = self._request_serial
        self.status.setText(tr('viewer.loading') if page.get('image_kind') == 'iiif'
                            else tr('viewer.open_local'))
        worker = FetchThread(page)
        self._worker = worker
        _ACTIVE_FETCH_THREADS.add(worker)
        worker.finished.connect(lambda w=worker: _ACTIVE_FETCH_THREADS.discard(w))
        worker.loaded.connect(lambda data, s=serial: self._on_image(data, s))
        worker.failed.connect(lambda error, s=serial: self._on_error(error, s))
        worker.start()

    def _reading_order(self):
        try:
            return tuple(line['id'] for line in reading_stream(self.witness, include_ignored=True))
        except (ValueError, KeyError, TypeError):
            # A stale manual reading-order override is diagnosed elsewhere.
            # It must not make the visual viewer itself unusable.
            return ()

    def refresh_reading_order(self):
        """Read the reading order again (after « Reading order and
        intervals… »): Shift ranges followed the order of the opening."""
        self._line_order = self._reading_order() or tuple(self._line_to_page)

    def _gone(self):
        # The panel is destroyed with its dialog without its own closeEvent:
        # an image arriving afterwards must not reach deleted widgets.
        return self._closed or not isValid(self) or not isValid(self.status)

    def _on_error(self, error, serial):
        if not self._gone() and serial == self._request_serial:
            self.status.setText(tr('viewer.image_unavailable.prefix') + error)
            self._preview_focus_pending = False

    def _on_image(self, data, serial):
        if self._gone() or serial != self._request_serial: return
        image = QImage.fromData(data)
        if image.isNull():
            self._on_error(tr('ui.format.dimage.non.reconnu.par.qt'), serial)
            return
        pix = QPixmap.fromImage(image)
        self.scene.clear()
        self._pixmap_item = self.scene.addPixmap(pix)
        self.scene.setSceneRect(QRectF(0, 0, pix.width(), pix.height()))
        self._rectangles = []
        ap = mapped_alto_page(self.witness, self._current_page)
        warning = ''
        polygon_count = 0
        if ap:
            polygons = page_line_polygons(self.witness, self._current_page, ap)
            try:
                width = float(ap['width']); height = float(ap['height'])
                if width <= 0 or height <= 0: raise ValueError('dimensions nulles')
                sx, sy = pix.width() / width, pix.height() / height
                if abs(sx / sy - 1) > 0.04:
                    warning = tr('ui.attention.proportions.image.alto.differentes.verifier.les')
            except (ValueError, TypeError, ZeroDivisionError):
                width = height = None
                warning = tr('ui.dimensions.alto.inconnues.cadres.indisponibles')
            for index, line in enumerate(self._page_lines):
                try:
                    if width is None: raise ValueError()
                    bbox = line['bbox']
                    rect = QRectF(float(bbox['HPOS']) * sx, float(bbox['VPOS']) * sy,
                                  float(bbox['WIDTH']) * sx, float(bbox['HEIGHT']) * sy)
                    if not rect.isValid() or rect.width() <= 0 or rect.height() <= 0: raise ValueError()
                    polygon = None
                    if index < len(polygons) and polygons[index]:
                        polygon = [(float(x) * sx, float(y) * sy)
                                   for x, y in polygons[index]]
                        if len(polygon) >= 3:
                            polygon_count += 1
                    item = ClickableLine(rect, self, index, polygon=polygon)
                    self.scene.addItem(item)
                    self._rectangles.append(item)
                except (ValueError, TypeError, KeyError):
                    self._rectangles.append(None)
        if polygon_count:
            warning += tr('viewer.polygon_count').format(count=polygon_count)
        else:
            warning += tr('viewer.no_polygon')
        self._set_default_overlay_mode(polygon_count > 0)
        self.status.setText(tr('viewer.status', width=pix.width(), height=pix.height()) + warning)
        self.refresh_overlay()
        self.fit_page()
        self._focus_counterparts()

    def fit_page(self):
        if self._pixmap_item:
            self.view.resetTransform()
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_to_line(self, index):
        if not 0 <= index < len(self._rectangles): return
        item = self._rectangles[index]
        if item:
            rect = item.rect().adjusted(-35, -45, 35, 45)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.view.centerOn(item)

    def focus_selected(self):
        row = self.lines.currentRow()
        if row >= 0:
            self.zoom_to_line(row)

    def focus_line(self, index):
        if 0 <= index < len(self._rectangles):
            item = self._rectangles[index]
            if item:
                self.view.centerOn(item)

    def set_tei_line_texts(self, text_by_uid):
        """Show validated TEI text in the optional line pane, never alter HTR."""
        self._tei_text_by_line = dict(text_by_uid or {})
        self.show_htr.setText(tr('tei.visual.text_toggle') if self._tei_text_by_line
                              else tr('viewer.htr.toggle'))
        if self._current_page:
            self._update_line_texts()

    def _update_line_texts(self):
        was_blocked = self.lines.blockSignals(True)
        try:
            self.lines.clear()
            for i, line in enumerate(self._page_lines):
                uid = line_uid(self.witness['id'], self._current_page['id'], i + 1)
                text = (self._tei_text_by_line.get(uid, '') if self._tei_text_by_line
                        else (line.get('text') or '').strip())
                label = f'{i + 1:>3}'
                if self.show_htr.isChecked() and text:
                    label += '   ' + text[:135]
                self.lines.addItem(label)
                self.lines.item(i).setData(Qt.ItemDataRole.UserRole, uid)
                self.lines.item(i).setSelected(uid in self._selected)
        finally:
            self.lines.blockSignals(was_blocked)
        self.refresh_overlay()

    def _sync_visible_selection(self, *, current_index=None):
        """Update the optional HTR/TEI list without Qt re-entering selection."""
        was_blocked = self.lines.blockSignals(True)
        try:
            for i in range(self.lines.count()):
                uid = self.lines.item(i).data(Qt.ItemDataRole.UserRole)
                self.lines.item(i).setSelected(uid in self._selected)
            if current_index is not None and 0 <= current_index < self.lines.count():
                item = self.lines.item(current_index)
                self.lines.setCurrentItem(item, QItemSelectionModel.SelectionFlag.NoUpdate)
                self.lines.scrollToItem(item)
        finally:
            self.lines.blockSignals(was_blocked)
        self._refresh_selection_visuals()

    def _refresh_selection_visuals(self):
        self.refresh_overlay()
        self.selection_status.setText(f'{len(self._selected)}' + tr('ui.ligne.s.selectionnee.s'))

    def _record_selection(self):
        """Keep programmatic / keyboard list changes synchronised.

        Deliberate mouse clicks go through WitnessLineList and the complete
        cross-folio selection policy; this fallback is for Qt keyboard changes.
        """
        if not self._current_page:
            return
        visible = {line_uid(self.witness['id'], self._current_page['id'], i + 1)
                   for i in range(len(self._page_lines))}
        selected_visible = {item.data(Qt.ItemDataRole.UserRole)
                            for item in self.lines.selectedItems()}
        self._selected.difference_update(visible)
        self._selected.update(selected_visible)
        self._refresh_selection_visuals()

    def select_overlay_line(self, index, modifiers):
        """Click = replace across entire witness; Ctrl = toggle; Shift = range."""
        if not 0 <= index < self.lines.count() or not self._current_page:
            return
        uid = line_uid(self.witness['id'], self._current_page['id'], index + 1)
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        self._selected, self._last_anchor = update_line_selection(
            self._selected, uid, self._line_order, anchor=self._last_anchor,
            ctrl=ctrl, shift=shift)
        self._sync_visible_selection(current_index=index)
        self.focus_line(index)
        # Only genuine clicks drive cross-witness previews (never file data).
        self.line_clicked.emit(uid)

    def is_emphasized(self, ordinal):
        """Selected or cross-witness preview lines retain their full outline."""
        if not self._current_page:
            return False
        uid = line_uid(self.witness['id'], self._current_page['id'], ordinal + 1)
        return uid in self._selected or uid in self._counterpart_ids

    def line_at_scene_pos(self, scene_pos, *, fallback=None):
        """Pick a line by location, not by the item's arbitrary stacking order."""
        if scene_pos is None:
            return fallback
        geometry = []
        for ordinal, item in enumerate(self._rectangles):
            if item is None or not item.isVisible():
                continue
            rect = item.sceneTransform().mapRect(item.rect())
            geometry.append((ordinal, rect.x(), rect.y(), rect.width(), rect.height(),
                             item.scene_polygon()))
        return choose_line_geometry((scene_pos.x(), scene_pos.y()), geometry, fallback=fallback)

    def select_overlay_at(self, fallback_ordinal, scene_pos, modifiers):
        ordinal = self.line_at_scene_pos(scene_pos, fallback=fallback_ordinal)
        if ordinal is not None:
            self.select_overlay_line(ordinal, modifiers)

    def refresh_overlay(self):
        if not self._current_page: return
        for index, item in enumerate(self._rectangles):
            if item is None: continue
            uid = line_uid(self.witness['id'], self._current_page['id'], index + 1)
            active = uid in self._selected
            counterpart = uid in self._counterpart_ids
            style_key = self._line_styles.get(uid, 'default')
            visible = (self.overlay_toggle.isChecked() and
                       overlay_visible(style_key, self._overlay_filter, selected=active,
                                       counterpart=counterpart))
            item.setVisible(visible)
            pen_color, fill_color, width, line_style = self._style_parameters(
                style_key, active=active, counterpart=counterpart)
            if self.compact_overlay.isChecked() and not (active or counterpart):
                # Do not spread 2-pixel cosmetic borders over a page reduced
                # to a few hundred display pixels. Full ALTO geometry remains
                # available for hit testing and line-to-line alignment.
                width = min(width, 1.5)
            pen = QPen(pen_color, width)
            pen.setStyle(line_style)
            pen.setCosmetic(True)
            item.setPen(pen)
            item.setBrush(QBrush(fill_color))
            item.update()  # Required when changing from compact marker to box

    def selected_ids(self):
        """Selected lines in documentary order, including previous folios.

        Use the cached reading stream rather than reparsing every PAGE/ALTO
        file on every click, especially with large IIIF manifests.
        """
        return [uid for uid in self._line_order if uid in self._selected]

    def clear_selection(self):
        self._selected.clear()
        self._last_anchor = None
        self._sync_visible_selection()
        self.selection_cleared.emit()

    def focus_ids(self, ids):
        self._selected = set(ids)
        for page in self.pages:
            contents = (mapped_alto_page(self.witness, page) or {}).get('lines', [])
            if any(line_uid(self.witness['id'], page['id'], i + 1) in self._selected
                   for i in range(len(contents))):
                self.set_page(page['id'])
                self._update_line_texts()
                index = next((i for i in range(len(contents))
                              if line_uid(self.witness['id'], page['id'], i + 1) in self._selected), 0)
                self.lines.setCurrentRow(index)
                break
        self._record_selection()


class PageViewer(QDialog):
    """Compatible single-page preview, now with full zoom/navigation controls."""
    def __init__(self, witness, page, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(f"{witness['id']} · {page.get('label', tr('common.page'))}")
        from PySide6.QtWidgets import QApplication
        screen=QApplication.primaryScreen()
        avail=screen.availableGeometry() if screen else None
        self.resize(min(1020,int(avail.width()*.91)) if avail else 1020,
                    min(710,int(avail.height()*.87)) if avail else 710)
        lay = QVBoxLayout(self)
        self.panel = LineImagePanel(witness, self, initial_page_id=page['id'], only_alto=False)
        lay.addWidget(self.panel)
        self.lines = self.panel.lines

    def focus_line(self, index):
        self.panel.focus_line(index)
