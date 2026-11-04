"""Fenêtre « Images et associations ALTO/PAGE » d’un témoin : ordre des pages, association des XML, copies HD et export pour une HTR."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QIcon, QImage, QImageReader, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (QAbstractItemView, QGroupBox, QHBoxLayout, QListWidgetItem,
                               QProgressDialog, QVBoxLayout)

from .errors import localized_text
from .i18n import tr
from .imaging import create_pages, import_htr_results, mapped_alto_page
from .physical_alignment import page_links_impact
from .reading_stream import rebind_page
from .ui_batch_binding import BatchBindingDialog
from .ui_widgets import (_run_modal, call_soon, QDialog, QFileDialog, QInputDialog, QLabel, QListWidget,
                         QMessageBox, QPushButton)


class DraggablePagesList(QListWidget):
    """Persist Qt internal drops even when Qt emits insert/remove, not rowsMoved."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_order_changed = None

    def dropEvent(self, event):
        super().dropEvent(event)
        if event.isAccepted() and self.on_order_changed is not None:
            # Defer until Qt has finished its internal item movement.
            call_soon(self, self.on_order_changed)


class HDDownloadThread(QThread):
    progressed = Signal(int, int)
    # The worker, not QProgressDialog's visibility, owns the final outcome.
    # status = success | cancelled | failed
    done = Signal(str, int, str)

    def __init__(self, witness, selected, output_directory, cancellation, parent=None):
        super().__init__(parent)
        self.witness = witness
        self.selected = tuple(selected)
        self.output_directory = output_directory
        self.cancellation = cancellation
        self.validated_hd_batch = None
        self.registry_error = None

    def run(self):
        try:
            from .imaging import export_iiif_hd_images
            count = export_iiif_hd_images(
                self.witness, self.selected, self.output_directory,
                cancelled=self.cancellation.is_set,
                progress=lambda done, total: self.progressed.emit(done, total))
            from .hd_registry import inspect_hd_folder
            # Hash large JPEGs in the worker, never on the GUI thread.
            # A bookkeeping problem does NOT turn a published download
            # into a "failed" download: it can be reattached later.
            try:
                self.validated_hd_batch = inspect_hd_folder(self.witness, self.output_directory)
            except Exception as exc:
                self.registry_error = localized_text(exc)
            self.done.emit('success', count, '')
        except InterruptedError as exc:
            self.done.emit('cancelled', 0, localized_text(exc))
        except Exception as exc:
            self.done.emit('failed', 0, localized_text(exc))


class HTRExportThread(QThread):
    """Export of IIIF images for an external HTR, off the interface
    thread (it downloads every page: the window froze for minutes)."""
    progressed = Signal(int, int)
    done = Signal(str, int, str)   # success | cancelled | failed

    def __init__(self, witness, selected, path, cancellation, parent=None):
        super().__init__(parent)
        self.witness, self.selected, self.path = witness, tuple(selected), path
        self.cancellation = cancellation

    def run(self):
        try:
            from .imaging import export_iiif_htr_zip
            count = export_iiif_htr_zip(
                self.witness, list(self.selected), self.path,
                cancelled=self.cancellation.is_set,
                progress=lambda done, total: self.progressed.emit(done, total))
            self.done.emit('success', count, '')
        except InterruptedError as exc:
            self.done.emit('cancelled', 0, localized_text(exc))
        except Exception as exc:
            self.done.emit('failed', 0, localized_text(exc))


class PagesDialog(QDialog):
    """Direct, image-backed page order editor and independent XML binding.

    The QListWidget items carry stable page IDs, not array positions. Moving
    them changes only each page's ``reading_order`` field. Thumbnails are
    intentionally loaded for visible rows only: a IIIF Manifest may contain
    hundreds of Canvas objects.
    """
    THUMBNAIL_SIZE = QSize(118, 84)

    def __init__(self, project, witness, parent=None):
        super().__init__(parent)
        self.project = project
        self.witness = witness
        self._display_pages = []
        self._thumb_cache = {}
        self._thumb_attempted = set()
        self._remote_replies = {}
        self._network = QNetworkAccessManager(self)
        self._rebuilding = False
        self.setWindowTitle(tr('ui.xml.pages_title') + witness['id'])
        self.resize(1020, 700)
        main = QVBoxLayout(self)
        hint = QLabel(tr('ui.xml.pages_hint')); hint.setWordWrap(True)
        main.addWidget(hint)
        order_help = QLabel(tr('pages.order.help'))
        order_help.setWordWrap(True)
        main.addWidget(order_help)
        self.pages = DraggablePagesList()
        self.pages.on_order_changed = self._commit_displayed_order
        self.pages.setObjectName('pageOrderList')
        self.pages.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pages.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.pages.setDragEnabled(True)
        self.pages.setAcceptDrops(True)
        self.pages.setDropIndicatorShown(True)
        self.pages.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.pages.setIconSize(self.THUMBNAIL_SIZE)
        self.pages.setSpacing(3)
        self.pages.setUniformItemSizes(True)
        self.pages.model().rowsMoved.connect(self._on_rows_moved)
        self.pages.verticalScrollBar().valueChanged.connect(self._schedule_thumbnails)
        main.addWidget(self.pages, 1)
        order_row = QHBoxLayout(); main.addLayout(order_row)
        order_row.addWidget(QLabel(tr('pages.order.heading')))
        for label, action, object_name in (
            ('pages.order.up', lambda: self.move_selected(-1), 'pageMoveUp'),
            ('pages.order.down', lambda: self.move_selected(1), 'pageMoveDown'),
            ('pages.order.reverse', self.reverse_order, 'pageReverseOrder')):
            button = QPushButton(tr(label)); button.setObjectName(object_name)
            button.clicked.connect(action)
            order_row.addWidget(button)
        order_row.addStretch(1)
        self.status = QLabel(); main.addWidget(self.status)
        association_help = QLabel(tr('pages.order.binding_independent'))
        association_help.setWordWrap(True)
        main.addWidget(association_help)
        row = QHBoxLayout();main.addLayout(row)
        for text, handler in (
            (tr('ui.afficher.page'), self.preview),
            (tr('ui.xml.link_source'), self.assign),
            (tr('ui.appliquer.suggestions'), self.suggest),
            (tr('common.close'), self.accept)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            row.addWidget(button)
        hd_group = QGroupBox(tr('ui.pages.hd.group'))
        hd_layout = QVBoxLayout(hd_group)
        hd_label = QLabel(tr('ui.pages.hd.group.explanation'))
        hd_label.setWordWrap(True)
        hd_layout.addWidget(hd_label)
        hd_row = QHBoxLayout()
        for text, handler, help_text in (
            (tr('ui.pages.hd.action'), self.download_hd, tr('ui.pages.hd.tip')),
            (tr('ui.pages.hd.attach'), self.attach_hd_folder, tr('ui.pages.hd.attach.tip'))):
            button = QPushButton(text)
            button.clicked.connect(handler)
            button.setToolTip(help_text)
            hd_row.addWidget(button)
        hd_row.addStretch(1)
        hd_layout.addLayout(hd_row)
        main.addWidget(hd_group)
        htr_group = QGroupBox(tr('ui.pages.htr.group'))
        htr_layout = QVBoxLayout(htr_group)
        htr_explanation = QLabel(tr('ui.pages.htr.explanation'))
        htr_explanation.setWordWrap(True)
        htr_layout.addWidget(htr_explanation)
        htr_row = QHBoxLayout()
        for label, action, hint in (
            ('ui.exporter.pour.htr', self.export, 'ui.pages.htr.export.tip'),
            ('ui.reimporter.htr', self.reimport, 'ui.pages.htr.import.tip')):
            button = QPushButton(tr(label))
            button.setToolTip(tr(hint))
            button.clicked.connect(action)
            htr_row.addWidget(button)
        htr_row.addStretch(1)
        htr_layout.addLayout(htr_row)
        main.addWidget(htr_group)
        self.pages.itemDoubleClicked.connect(lambda _: self.preview())
        self.update_list()

    def _item_ids(self):
        return [self.pages.item(index).data(Qt.ItemDataRole.UserRole)
                for index in range(self.pages.count())]

    def selected(self):
        """Resolve selection through page UID even after a drag/drop move."""
        by_id = {p['id']: p for p in self.witness.get('pages', [])}
        return [by_id[self.pages.item(index.row()).data(Qt.ItemDataRole.UserRole)]
                for index in self.pages.selectedIndexes()
                if self.pages.item(index.row()).data(Qt.ItemDataRole.UserRole) in by_id]

    def _page_label(self, page, index):
        label = page.get('label') or page['id']
        ap = mapped_alto_page(self.witness, page)
        if ap:
            xml_description = tr('pages.binding.assigned', count=ap.get('line_count', len(ap.get('lines', []))),
                                 htr=ap.get('htr_line_count', 0))
            binding = page.get('alto_binding') or {}
            src = next((s for s in self.witness.get('alto_sources', [])
                        if s['id'] == binding.get('source_id', binding.get('alto_source_id'))), None)
            if src:
                xml_description += ' · ' + Path(src['path']).name
        else:
            xml_description = tr('ui.xml.not_linked')
        origin = (Path(page.get('image_path', '')).name if page.get('image_kind') == 'local'
                  else tr('pages.image.iiif'))
        hd_pages = {entry.get('canvas_id') for batch in self.witness.get('hd_downloads', [])
                    for entry in batch.get('pages', [])}
        if page['id'] in hd_pages:
            origin += ' · ' + tr('ui.pages.hd.registered')
        return f'{index+1:>3}.  {label}  —  {origin}\n{xml_description}'

    def update_list(self, selection_ids=None):
        from .page_order import ordered_pages
        create_pages(self.witness)
        if selection_ids is None:
            selection_ids = {p['id'] for p in self.selected()} if self.pages.count() else set()
        self._display_pages = ordered_pages(self.witness)
        self._rebuilding = True
        try:
            self.pages.clear()
            for index, page in enumerate(self._display_pages):
                item = QListWidgetItem(self._page_label(page, index))
                item.setData(Qt.ItemDataRole.UserRole, page['id'])
                item.setSizeHint(QSize(0, 98))
                item.setToolTip(tr('pages.order.tooltip', image=(page.get('image_path') or
                                  (page.get('canvas') or {}).get('id') or ''),
                                  page_id=page['id']))
                cached = self._thumb_cache.get(page['id'])
                if cached is not None:
                    item.setIcon(cached)
                self.pages.addItem(item)
                if page['id'] in selection_ids:
                    item.setSelected(True)
        finally:
            self._rebuilding = False
        self._refresh_status()
        self._schedule_thumbnails()

    def _refresh_status(self):
        assigned = sum(mapped_alto_page(self.witness, p) is not None
                       for p in self.witness['pages'])
        self.status.setText(tr('pages.order.status', assigned=assigned,
                               total=len(self.witness['pages'])))

    def _schedule_thumbnails(self, *_):
        call_soon(self, self._load_visible_thumbnails)

    def _visible_item_ids(self):
        viewport = self.pages.viewport().rect()
        for index in range(self.pages.count()):
            item = self.pages.item(index)
            if self.pages.visualItemRect(item).intersects(viewport):
                yield item.data(Qt.ItemDataRole.UserRole)

    def _load_visible_thumbnails(self):
        by_id = {p['id']: p for p in self.witness.get('pages', [])}
        for page_id in self._visible_item_ids():
            if page_id in self._thumb_attempted:
                continue
            self._thumb_attempted.add(page_id)
            page = by_id.get(page_id)
            if page is None:
                continue
            if page.get('image_kind') == 'local':
                path = page.get('image_path')
                if path:
                    reader = QImageReader(str(path))
                    reader.setAutoTransform(True)
                    image_size = reader.size()
                    if image_size.isValid():
                        reader.setScaledSize(image_size.scaled(
                            self.THUMBNAIL_SIZE, Qt.AspectRatioMode.KeepAspectRatio))
                    image = reader.read()
                    if not image.isNull():
                        self._assign_thumbnail(page_id, image)
            elif page.get('image_kind') == 'iiif':
                if len(self._remote_replies) >= 4:
                    # Not attempted yet; retry after an active request ends.
                    self._thumb_attempted.discard(page_id)
                    continue
                # Only bounded IIIF Image API requests; never download a
                # multi-megapixel fallback image to draw a tiny thumbnail.
                canvas = page.get('canvas') or {}
                if not canvas.get('image_service'):
                    continue
                from .imaging import image_request_url
                url = image_request_url(page, max_width=180)
                if url:
                    request = QNetworkRequest(QUrl(url))
                    if hasattr(request, 'setTransferTimeout'):
                        request.setTransferTimeout(12000)
                    reply = self._network.get(request)
                    self._remote_replies[page_id] = reply
                    reply.finished.connect(lambda pid=page_id, r=reply:
                                           self._remote_thumbnail_finished(pid, r))

    def _remote_thumbnail_finished(self, page_id, reply):
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                image = QImage.fromData(bytes(reply.readAll()))
                if not image.isNull():
                    self._assign_thumbnail(page_id, image)
        finally:
            self._remote_replies.pop(page_id, None)
            reply.deleteLater()
            self._schedule_thumbnails()

    def _assign_thumbnail(self, page_id, image):
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return
        icon = QIcon(pixmap.scaled(self.THUMBNAIL_SIZE,
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation))
        self._thumb_cache[page_id] = icon
        for index in range(self.pages.count()):
            item = self.pages.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == page_id:
                item.setIcon(icon)
                break

    def _on_rows_moved(self, *_):
        if not self._rebuilding:
            # Do not update model text inside Qt's internal move operation.
            call_soon(self, self._commit_displayed_order)

    def _commit_displayed_order(self):
        from .page_management import commit_page_order
        ids = self._item_ids()
        from .page_management import page_ids_in_reading_order
        if ids == page_ids_in_reading_order(self.witness):
            return
        try:
            commit_page_order(self.witness, ids)
        except ValueError as exc:
            self.update_list()
            QMessageBox.warning(self, tr('pages.order.error'), localized_text(exc))
            return
        self._display_pages = [next(p for p in self.witness['pages'] if p['id'] == pid)
                               for pid in ids]
        for index, page in enumerate(self._display_pages):
            self.pages.item(index).setText(self._page_label(page, index))
        self._refresh_status()

    def move_selected(self, direction):
        selected = self.selected()
        if len(selected) != 1:
            QMessageBox.information(self, tr('pages.order.heading'),
                                    tr('pages.order.select_one'))
            return
        from .page_management import move_page_by_id
        selected_id = selected[0]['id']
        move_page_by_id(self.witness, selected_id, direction)
        self.update_list(selection_ids={selected_id})

    def reverse_order(self):
        from .page_management import invert_page_order
        if len(self.witness.get('pages', [])) < 2:
            return
        invert_page_order(self.witness)
        self.update_list(selection_ids={p['id'] for p in self.selected()})

    def preview(self):
        sel = self.selected()
        if len(sel) != 1:
            QMessageBox.information(self,tr('Image'),tr('Sélectionnez une seule page.'));return
        try:
            from .viewer import PageViewer
            window = PageViewer(self.witness, sel[0], self)
            self._viewer = window
            window.show()
        except Exception as exc:
            QMessageBox.warning(self,tr('Aperçu'),localized_text(exc))

    def assign(self):
        sel = self.selected()
        if len(sel) != 1:
            QMessageBox.information(self, tr('ui.xml.source'), tr('Sélectionnez exactement une page.'));return
        candidates = [(src,i) for src in self.witness['alto_sources'] for i in range(len(src['pages']))]
        if not candidates:
            QMessageBox.information(self, tr('ui.xml.source'), tr('ui.xml.import_first'));return
        labels = [f"{src.get('kind','alto').upper()} — {Path(src['path']).name} (page {i+1})" for src,i in candidates]
        chosen,ok = QInputDialog.getItem(self,tr('ui.xml.source'),tr('ui.xml.select_page'),labels,0,False)
        if ok:
            src,i = candidates[labels.index(chosen)]
            binding = sel[0].get('alto_binding') or {}
            if binding and (binding.get('source_id'), binding.get('page_index')) != (src['id'], i):
                # Say beforehand what a new segmentation affects: groups citing
                # the page's lines become stale if those lines change.
                impact = page_links_impact(self.project, self.witness['id'], sel[0]['id'])
                text = (tr('ui.xml.replace_impact', links=impact['links'],
                           validated=impact['validated'])
                        if impact['links'] else tr('ui.xml.replace_question'))
                if impact['reading_order']:
                    text += '\n\n' + tr('ui.xml.replace_order')
                answer = QMessageBox.question(self,tr('ui.xml.replace_title'),text)
                if answer != QMessageBox.StandardButton.Yes:return
            rebind_page(self.witness,sel[0]['id'],src['id'],i)
            self.update_list()

    def suggest(self):
        dialog = BatchBindingDialog(self.witness, self)
        if _run_modal(dialog) == QDialog.DialogCode.Accepted:
            self.update_list()

    def export(self):
        selected = [p['id'] for p in self.selected() if p['image_kind']=='iiif']
        if not selected:
            QMessageBox.information(self,tr('Export'),tr('Sélectionnez des pages IIIF dans la liste.'));return
        path,_ = QFileDialog.getSaveFileName(self,tr('ui.images.pour.traitement.externe'),
                                             self.witness['id']+'_HTR.zip','ZIP (*.zip)')
        if not path or getattr(self, '_htr_export_thread', None) is not None:
            return
        import threading
        cancel = threading.Event()
        progress = QProgressDialog(tr('ui.pages.htr.wait', current=0, total=len(selected)),
                                   tr('common.cancel'), 0, len(selected), self)
        progress.setWindowTitle(tr('Export IIIF'))
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        thread = HTRExportThread(self.witness, selected, path, cancel, self)
        self._htr_export_thread = thread
        self._htr_export_progress = progress
        progress.canceled.connect(cancel.set)
        def updated(done, total):
            if not cancel.is_set():
                progress.setValue(done)
                progress.setLabelText(tr('ui.pages.htr.wait', current=done, total=total))
        def complete(status, count, error):
            try:
                progress.canceled.disconnect(cancel.set)
            except (RuntimeError, TypeError):
                pass
            progress.hide()
            if status == 'success':
                QMessageBox.information(self, tr('Export terminé'),
                                        tr('release.images_exported', count=count))
            elif status == 'cancelled':
                QMessageBox.information(self, tr('Export IIIF'), tr('ui.pages.htr.cancelled'))
            else:
                QMessageBox.critical(self, tr('Export IIIF'), error)
            progress.deleteLater()
        thread.progressed.connect(updated)
        thread.done.connect(complete)
        def released():
            thread.deleteLater()
            self._htr_export_thread = None
            self._htr_export_progress = None
        thread.finished.connect(released)
        thread.start()
        progress.show()

    def download_hd(self):
        """Download only explicitly selected IIIF canvases, without mutating .vsynch."""
        if getattr(self, '_hd_download_thread', None) is not None:
            return  # One download transaction per window at a time.
        selected = [p['id'] for p in self.selected() if p.get('image_kind') == 'iiif']
        if not selected:
            QMessageBox.information(self, tr('ui.pages.hd.title'),
                                    tr('ui.pages.hd.no_selection'))
            return
        from .imaging import iiif_hd_url
        try:
            for page in self.selected():
                if page['id'] in selected:
                    iiif_hd_url(page)
        except ValueError as exc:
            QMessageBox.warning(self, tr('ui.pages.hd.title'), localized_text(exc))
            return
        folder = QFileDialog.getExistingDirectory(self, tr('ui.pages.hd.folder'))
        if not folder:
            return
        from pathlib import Path
        target = Path(folder)
        if any(target.iterdir()):
            QMessageBox.warning(self, tr('ui.pages.hd.title'),
                                tr('export.varians.choose_empty'))
            return
        import threading
        cancel = threading.Event()
        progress = QProgressDialog(tr('ui.pages.hd.wait', current=0, total=len(selected)),
                                   tr('common.cancel'), 0, len(selected), self)
        progress.setWindowTitle(tr('ui.pages.hd.title'))
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        # At maximum, QProgressDialog must not dismiss itself: depending on
        # Qt/platform, that can emit canceled() despite a successful export.
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        thread = HDDownloadThread(self.witness, selected, folder, cancel, self)
        self._hd_download_thread = thread
        self._hd_download_progress = progress
        progress.canceled.connect(cancel.set)
        def updated(done, total):
            if not cancel.is_set():
                progress.setValue(done)
                progress.setLabelText(tr('ui.pages.hd.wait', current=done, total=total))
        def complete(status, count, error):
            # Closing a Qt progress dialog can emit canceled(): disconnect
            # before programmatic closure. Never infer a cancelled export
            # from an event set by the progress window *after* publication.
            try:
                progress.canceled.disconnect(cancel.set)
            except (RuntimeError, TypeError):
                pass
            progress.hide()
            if status == 'success':
                if thread.validated_hd_batch is not None:
                    from .hd_registry import register_hd_snapshot
                    register_hd_snapshot(self.witness, thread.validated_hd_batch)
                    self.update_list()
                    message = tr('ui.pages.hd.success', count=count, path=folder)
                else:
                    message = tr('ui.pages.hd.unregistered', count=count, path=folder,
                                 error=thread.registry_error or 'images.json')
                QMessageBox.information(self, tr('ui.pages.hd.title'), message)
            elif status == 'cancelled':
                QMessageBox.information(self, tr('ui.pages.hd.title'),
                                        tr('ui.pages.hd.cancelled'))
            else:
                QMessageBox.warning(self, tr('ui.pages.hd.title'), error)
            progress.deleteLater()
        # Connected before the start, not from complete(): the bar must
        # follow the download (it stayed at 0 and invited a cancellation).
        thread.progressed.connect(updated)
        thread.done.connect(complete)
        def released():
            thread.deleteLater()
            self._hd_download_thread = None
            self._hd_download_progress = None
        thread.finished.connect(released)
        thread.start()
        progress.show()

    def attach_hd_folder(self):
        """Import the receipt of HD images downloaded by older Synchro."""
        mapping, _ = QFileDialog.getOpenFileName(
            self, tr('ui.pages.hd.attach'), '', 'images.json (images.json)')
        if not mapping:
            return
        try:
            from .hd_registry import register_hd_folder
            batch = register_hd_folder(self.witness, Path(mapping).parent)
        except Exception as exc:
            QMessageBox.warning(self, tr('ui.pages.hd.attach'), localized_text(exc))
            return
        self.update_list()
        QMessageBox.information(self, tr('ui.pages.hd.attach'),
            tr('ui.pages.hd.attached', count=len(batch['pages'])))

    def reimport(self):
        mapping,_ = QFileDialog.getOpenFileName(self,tr('ui.pages.json.du.zip.exporte'),'','JSON (*.json)')
        if not mapping:return
        directory = QFileDialog.getExistingDirectory(self,tr('ui.xml.output_folder'))
        if not directory:return
        try:
            outcome = import_htr_results(self.witness,mapping,directory)
            self.update_list()
            QMessageBox.information(self,tr('Réimportation'),
                tr('release.htr_reimported', imported=len(outcome['imported']), missing=len(outcome['missing']), skipped=len(outcome['skipped'])))
        except Exception as exc:QMessageBox.critical(self,tr('Réimportation'),localized_text(exc))
