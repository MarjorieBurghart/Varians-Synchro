"""Witness-centered PySide6 GUI; the V0.7 physical alignment engine is preserved."""
from __future__ import annotations
from pathlib import Path
import copy

from .core import (VERSION, new_project, load_project, save_project, create_witness,
                   check_alto_files)
from .imaging import (create_pages, bind_alto, suggest_alto_bindings,
                      export_iiif_htr_zip, import_htr_results, mapped_alto_page)
from .physical_alignment import (physical_lines, create_pair_session, add_pair_link, extend_pair_link, detach_pair_lines, replace_revisable_pair_proposals,
                                 remove_pair_link, set_pair_link_states, pair_progress,
                                 verify_pair_sessions, suggest_htr_pair_alignment, apply_pair_proposals,
                                 stale_link_ids, revalidate_pair_links, page_links_impact)
from .interpolation import suggest_between_anchors
from .textual_progress import suggest_textual_progress
from .rapid_review import (ordered_links, review_counts, following_anchor_interval,
    suggestions_for_interval, validate_checked, verify_before_review)
from .residual_alignment import suggest_residual_extensions, apply_residual_extensions
from .correspondence_navigation import build_pair_navigation_index
from .overlay_filters import (FILTER_ALL, FILTER_UNLINKED, FILTER_AUTOMATIC_REVIEW,
                              style_for_link)
from .i18n import tr, get_language, set_language, language_labels
from .line_scope import ignored_ids, linked_scope_conflicts, update_ignored_lines
from .reading_stream import (reading_stream, anchor_intervals, set_page_order, rebind_page,
    set_region_order, set_line_order, reset_page_line_order, page_regions)
from .project_state import ProjectChangeTracker
from .exceptions import (preview_confirmed_absence, confirm_absence, pair_exception_summary)



def _run_modal(dialog):
    """``dialog.exec()``, then free the dialog once control returns to the
    event loop. Dialogs had the main window as parent and were never
    deleted: each one kept its images (full-size pixmaps) and project
    copies, and memory grew at every opening. Code right after exec() in
    the same slot can still use the dialog."""
    try:
        return dialog.exec()
    finally:
        dialog.deleteLater()


def make_guided_window(legacy_window_type=None):
    from PySide6.QtCore import Qt, QSize, QTimer, QUrl, QThread, Signal, QPointF
    from PySide6.QtGui import QIcon, QPixmap, QImage, QImageReader, QColor, QBrush, QPainter, QPen, QPolygonF
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
    from PySide6.QtWidgets import (QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
        QWidget, QLabel, QComboBox, QGroupBox, QLineEdit, QPushButton, QMessageBox,
        QFileDialog, QInputDialog, QTreeWidget, QTreeWidgetItem, QListWidget,
        QAbstractItemView, QSplitter, QStackedWidget, QPlainTextEdit, QTabWidget,
        QApplication, QToolButton, QMenu, QSizePolicy, QListWidgetItem, QTableWidget, QTableWidgetItem, QCheckBox, QScrollArea, QFrame, QProgressDialog)
    from PySide6.QtWidgets import (QLabel as QtLabel, QPushButton as QtButton,
       QListWidget as QtListWidget, QTabWidget as QtTabWidget, QTreeWidget as QtTreeWidget,
       QComboBox as QtComboBox, QDialog as QtDialog, QMainWindow as QtMainWindow,
       QMessageBox as QtMessageBox, QInputDialog as QtInputDialog,
       QFileDialog as QtFileDialog)

    class QLabel(QtLabel):
        def __init__(self, *args, **kwargs):
            if args and isinstance(args[0], str):
                args=(tr(args[0]),)+args[1:]
            super().__init__(*args, **kwargs)
        def setText(self, text):
            super().setText(tr(text))

    class QPushButton(QtButton):
        def __init__(self, *args, **kwargs):
            if args and isinstance(args[0], str):
                args=(tr(args[0]),)+args[1:]
            super().__init__(*args, **kwargs)
        def setToolTip(self, text):
            super().setToolTip(tr(text))

    class QListWidget(QtListWidget):
        def addItem(self, item):
            return super().addItem(tr(item) if isinstance(item, str) else item)

    class QComboBox(QtComboBox):
        def addItem(self, *args):
            if args and isinstance(args[0], str):
                args=(tr(args[0]),)+args[1:]
            return super().addItem(*args)

    class QTabWidget(QtTabWidget):
        def addTab(self, widget, label):
            return super().addTab(widget, tr(label))

    class QTreeWidget(QtTreeWidget):
        def setHeaderLabels(self, labels):
            return super().setHeaderLabels([tr(t) for t in labels])

    class QDialog(QtDialog):
        def setWindowTitle(self, title):
            return super().setWindowTitle(tr(title))

    class QMainWindow(QtMainWindow):
        def setWindowTitle(self, title):
            return super().setWindowTitle(tr(title))

    class QMessageBox(QtMessageBox):
        @staticmethod
        def information(parent, title, detail, *args):
            return QtMessageBox.information(parent,tr(title),tr(detail),*args)
        @staticmethod
        def warning(parent, title, detail, *args):
            return QtMessageBox.warning(parent,tr(title),tr(detail),*args)
        @staticmethod
        def critical(parent, title, detail, *args):
            return QtMessageBox.critical(parent,tr(title),tr(detail),*args)
        @staticmethod
        def question(parent, title, detail, *args):
            return QtMessageBox.question(parent,tr(title),tr(detail),*args)


    class QInputDialog(QtInputDialog):
        @staticmethod
        def getText(parent, title, label, *args, **kwargs):
            return QtInputDialog.getText(parent, tr(title), tr(label), *args, **kwargs)
        @staticmethod
        def getItem(parent, title, label, items, *args, **kwargs):
            return QtInputDialog.getItem(parent, tr(title), tr(label), items, *args, **kwargs)

    class QFileDialog(QtFileDialog):
        @staticmethod
        def getOpenFileName(parent=None, caption='', *args, **kwargs):
            return QtFileDialog.getOpenFileName(parent, tr(caption), *args, **kwargs)
        @staticmethod
        def getOpenFileNames(parent=None, caption='', *args, **kwargs):
            return QtFileDialog.getOpenFileNames(parent, tr(caption), *args, **kwargs)
        @staticmethod
        def getSaveFileName(parent=None, caption='', *args, **kwargs):
            return QtFileDialog.getSaveFileName(parent, tr(caption), *args, **kwargs)

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
            self.resize(1080, 640)
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
                QMessageBox.warning(self, tr('stream.preview'), str(exc))

    class PairDialog(QDialog):
        """Visual-first manual alignment; HTR is optional secondary information."""
        def __init__(self, project, session, parent=None):
            super().__init__(parent)
            from .viewer import LineImagePanel
            self.project = project
            self.session = session
            self.setWindowTitle('Synchronisation visuelle entre témoins — Varians-Synchro')
            # Keep the WHOLE dialog inside the usable screen, including title/taskbars.
            screen = QApplication.primaryScreen()
            bounds = screen.availableGeometry() if screen else None
            self.resize(min(1170, max(450, int(bounds.width() * .94))) if bounds else 1050,
                        min(740, max(320, int(bounds.height() * .90))) if bounds else 700)
            base = next(w for w in project['witnesses'] if w['id'] == session['reference_witness_id'])
            target = next(w for w in project['witnesses'] if w['id'] == session['target_witness_id'])
            self.left_witness, self.right_witness = base, target
            from .tei_binding import linked_tei_texts
            self._tei_left = linked_tei_texts(project, base['id'])
            self._tei_right = linked_tei_texts(project, target['id'])
            self._tei_search_hits = []
            self._tei_search_index = -1
            self.left_lines = physical_lines(base)
            self.right_lines = physical_lines(target)
            main = QVBoxLayout(self)
            # Primary action always stays at the TOP: it must never disappear
            # beneath a large image or below a small laptop's visible screen.
            top = QHBoxLayout(); main.addLayout(top)
            self.associate_button = QPushButton(tr('alignment.action.link_lines'))
            self.associate_button.setObjectName('associateLinesButton')
            self.associate_button.setToolTip(tr('alignment.action.link_lines.tip.extended'))
            self.associate_button.setMinimumHeight(34)
            self.associate_button.clicked.connect(lambda: self.attach('correspondence'))
            top.addWidget(self.associate_button)
            self.unlink_button = QPushButton(tr('alignment.action.unlink_lines'))
            self.unlink_button.setObjectName('unlinkSelectedLinesButton')
            self.unlink_button.setToolTip(tr('alignment.action.unlink_lines.tip'))
            self.unlink_button.clicked.connect(self.detach_lines)
            top.addWidget(self.unlink_button)
            self.interpolate_button = QPushButton(tr('progress.action'))
            self.interpolate_button.setToolTip(tr('progress.action.tip'))
            self.interpolate_button.clicked.connect(lambda: self.interpolate())
            top.addWidget(self.interpolate_button)
            self.more_actions = QToolButton()
            self.more_actions.setText(tr('alignment.action.more'))
            self.more_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.more_menu = QMenu(self.more_actions)
            for label,handler in (
                ('exception.action.confirm', self.confirm_selected_absence),
                ('exception.action.revoke', self.revoke_selected_absences),
                ('Dissocier les lignes sélectionnées',self.detach_lines),
                ('Supprimer le(s) groupe(s) sélectionné(s) dans la liste',self.detach_groups),
                ('Valider sélection',lambda: self.review('validated')),
                ('Marquer incertain',lambda: self.review('uncertain')),
                ('Proposer via HTR (facultatif)',self.automatic),
                ('progress.legacy.geometry',self.interpolate_geometry),
                ('progress.legacy.residual',self.residual),
                ('stream.window.action',self.open_reading_order),
            ):
                action = self.more_menu.addAction(tr(label))
                action.triggered.connect(lambda checked=False, f=handler: f())
            self.more_menu.addSeparator()
            self.more_menu.addAction(tr('common.close'), self.accept)
            self.more_actions.setMenu(self.more_menu)
            top.addWidget(self.more_actions)
            self.scope_actions = QToolButton()
            self.scope_actions.setObjectName('witnessScopeButton')
            self.scope_actions.setText(tr('scope.menu'))
            self.scope_actions.setToolTip(tr('scope.menu.tip'))
            self.scope_actions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            scope_menu = QMenu(self.scope_actions)
            scope_menu.addAction(tr('scope.ignore'), lambda: self.change_scope(True))
            scope_menu.addAction(tr('scope.restore'), lambda: self.change_scope(False))
            self.scope_actions.setMenu(scope_menu)
            top.addWidget(self.scope_actions)
            top.addStretch(1)
            from PySide6.QtGui import QShortcut, QKeySequence
            self.assoc_shortcut=QShortcut(QKeySequence('Ctrl+Return'),self)
            self.assoc_shortcut.activated.connect(lambda: self.attach('correspondence'))
            self.assoc_shortcut2=QShortcut(QKeySequence('Ctrl+Enter'),self)
            self.assoc_shortcut2.activated.connect(lambda: self.attach('correspondence'))
            self.absence_shortcut = QShortcut(QKeySequence('Ctrl+Shift+A'), self)
            self.absence_shortcut.activated.connect(self.confirm_selected_absence)
            title = QLabel(tr('ui.cliquez.sur.une.ligne.deja.liee.pour'))
            title.setWordWrap(True); main.addWidget(title)
            filter_row = QHBoxLayout(); main.addLayout(filter_row)
            filter_row.addWidget(QLabel('Cadres visibles :'))
            self.overlay_filter = QComboBox()
            self.overlay_filter.setObjectName('alignmentOverlayFilter')
            self.overlay_filter.addItem(tr('alignment.filter.all'), FILTER_ALL)
            self.overlay_filter.addItem(tr('alignment.filter.unlinked'), FILTER_UNLINKED)
            self.overlay_filter.addItem(tr('alignment.filter.automatic_review'), FILTER_AUTOMATIC_REVIEW)
            self.overlay_filter.setToolTip(tr('alignment.filter.tip'))
            filter_row.addWidget(self.overlay_filter)
            # The V0.6 residual tool remains in the compatibility menu only;
            # do not confuse users with two competing default algorithms.
            filter_row.addStretch(1)
            if self._tei_left or self._tei_right:
                filter_row.addWidget(QLabel(tr('tei.visual.search_label')))
                self.tei_search_side = QComboBox()
                if self._tei_left:
                    self.tei_search_side.addItem(base['id'], 'reference')
                if self._tei_right:
                    self.tei_search_side.addItem(target['id'], 'target')
                filter_row.addWidget(self.tei_search_side)
                self.tei_search_edit = QLineEdit()
                self.tei_search_edit.setPlaceholderText(tr('tei.visual.search'))
                self.tei_search_edit.setMaximumWidth(230)
                self.tei_search_edit.textChanged.connect(self.reset_tei_search)
                self.tei_search_edit.returnPressed.connect(self.next_tei_search)
                filter_row.addWidget(self.tei_search_edit)
                next_match = QPushButton(tr('tei.visual.search_next'))
                next_match.clicked.connect(self.next_tei_search)
                filter_row.addWidget(next_match)
            self.overlay_filter.currentIndexChanged.connect(self._update_overlay_filter)
            self.legend = QLabel()
            self.legend.setWordWrap(True)
            main.addWidget(self.legend)

            self.tabs = QTabWidget()
            main.addWidget(self.tabs, 1)
            visual = QWidget(); visual_layout = QVBoxLayout(visual)
            split = QSplitter(Qt.Orientation.Horizontal)
            self.left_panel = LineImagePanel(base, split)
            self.right_panel = LineImagePanel(target, split)
            self.left_panel.set_tei_line_texts(self._tei_left)
            self.right_panel.set_tei_line_texts(self._tei_right)
            self.left_panel.line_clicked.connect(lambda uid: self._show_counterparts('reference', uid))
            self.right_panel.line_clicked.connect(lambda uid: self._show_counterparts('target', uid))
            self.left_panel.selection_cleared.connect(lambda: self._show_counterparts('reference', None))
            self.right_panel.selection_cleared.connect(lambda: self._show_counterparts('target', None))
            split.addWidget(self.left_panel)
            split.addWidget(self.right_panel)
            split.setChildrenCollapsible(False)
            split.setSizes([760, 760])
            visual_layout.addWidget(split, 1)
            self.tabs.addTab(visual, 'ui.xml.visual_tab')

            text_page = QWidget(); text_layout = QVBoxLayout(text_page)
            text_layout.addWidget(QLabel(tr('tei.visual.pair_help')))
            text_split = QSplitter(Qt.Orientation.Horizontal)
            self.left = QListWidget(); self.right = QListWidget()
            for widget in (self.left, self.right):
                widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                text_split.addWidget(widget)
            for line in self.left_lines:
                rendered = self._tei_left.get(line['id'], '') if self._tei_left else line['text']
                self.left.addItem(f"{line['page_label']} · {line['ordinal']:>3}  " +
                                  (rendered[:140] or tr('tei.visual.no_text' if self._tei_left else 'scope.no_htr')))
            for line in self.right_lines:
                rendered = self._tei_right.get(line['id'], '') if self._tei_right else line['text']
                self.right.addItem(f"{line['page_label']} · {line['ordinal']:>3}  " +
                                   (rendered[:140] or tr('tei.visual.no_text' if self._tei_right else 'scope.no_htr')))
            text_layout.addWidget(text_split, 1)
            self.tabs.addTab(text_page, 'Vue textuelle (facultative)')

            # Links/results area is compact and scrollable, never allowed to
            # push the primary controls below the monitor's visible area.
            # V0.7.2: fast, ordered human review. Display order never changes
            # project/session storage order or stable correspondence IDs.
            review_bar = QHBoxLayout(); main.addLayout(review_bar)
            review_bar.addWidget(QLabel(tr('review.queue.label')))
            self.review_filter = QComboBox()
            for key, value in (
                ('review.filter.all', 'all'),
                ('review.filter.pending', 'pending'),
                ('review.filter.validated', 'validated'),
                ('review.filter.absences', 'absences'),
                ('review.filter.stale', 'stale'),
            ):
                self.review_filter.addItem(tr(key), value)
            self.review_filter.setCurrentIndex(1)  # pending by default
            review_bar.addWidget(self.review_filter)
            self.previous_review_button = QPushButton(tr('review.previous'))
            self.previous_review_button.clicked.connect(lambda: self.move_review(-1))
            review_bar.addWidget(self.previous_review_button)
            self.next_review_button = QPushButton(tr('review.next'))
            self.next_review_button.clicked.connect(lambda: self.move_review(1))
            review_bar.addWidget(self.next_review_button)
            self.validate_review_button = QPushButton(tr('review.validate.next'))
            self.validate_review_button.clicked.connect(self.validate_and_next)
            review_bar.addWidget(self.validate_review_button)
            self.batch_review_button = QPushButton(tr('review.validate.selected'))
            self.batch_review_button.clicked.connect(self.validate_review_selection)
            review_bar.addWidget(self.batch_review_button)
            self.local_review_button = QPushButton(tr('review.recalculate.next'))
            self.local_review_button.clicked.connect(self.recalculate_next_interval)
            review_bar.addWidget(self.local_review_button)
            # Groups whose lines changed after a new segmentation of a page.
            self.revalidate_button = QPushButton(tr('alignment.stale.revalidate'))
            self.revalidate_button.setToolTip(tr('alignment.stale.revalidate.tip'))
            self.revalidate_button.clicked.connect(self.revalidate_selection)
            review_bar.addWidget(self.revalidate_button)
            self.links = QListWidget(); self.links.setMaximumHeight(125)
            self.links.setMinimumHeight(50)
            self.links.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            self._populating_links = False
            self.links.itemDoubleClicked.connect(lambda _: self.focus_link())
            self.links.currentItemChanged.connect(self._review_focus_changed)
            self.review_filter.currentIndexChanged.connect(lambda _: self.populate())
            main.addWidget(self.links)
            # Keyboard shortcuts are attached to the dialog and remain usable
            # while inspecting images. No shortcut validates a whole batch.
            for seq, handler in (('F8', lambda: self.move_review(1)),
                                 ('Shift+F8', lambda: self.move_review(-1)),
                                 ('Alt+V', self.validate_and_next)):
                shortcut = QShortcut(QKeySequence(seq), self)
                shortcut.activated.connect(handler)
                setattr(self, 'review_shortcut_' + seq.replace('+', '_'), shortcut)
            self.status = QLabel(); self.status.setWordWrap(True); main.addWidget(self.status)
            hint = QLabel(tr('alignment.edit.hint'))
            hint.setWordWrap(True)
            hint.setMaximumHeight(48)
            main.addWidget(hint)
            self.tabs.setMinimumHeight(150)
            self.visual_splitter = split
            self.populate()

        def open_reading_order(self):
            try:
                dialog = ReadingOrderDialog(self.project, self.session, self)
                _run_modal(dialog)
                # Immediately refresh textual selections in the new reading
                # order. Image panels remain tied to unchanged physical UIDs.
                self.left_lines = reading_stream(self.left_witness, include_ignored=True)
                self.right_lines = reading_stream(self.right_witness, include_ignored=True)
                for widget, lines in ((self.left, self.left_lines), (self.right, self.right_lines)):
                    widget.clear()
                    for line in lines:
                        widget.addItem(f"{line['page_label']} · {line['ordinal']:>3}  " +
                                       (line['text'][:140] or tr('scope.no_htr')))
                self.populate()
            except Exception as exc:
                QMessageBox.warning(self, tr('stream.window.title'), str(exc))

        def selection(self):
            if self.tabs.currentIndex() == 0:
                return self.left_panel.selected_ids(), self.right_panel.selected_ids()
            return ([self.left_lines[idx.row()]['id'] for idx in self.left.selectedIndexes()],
                    [self.right_lines[idx.row()]['id'] for idx in self.right.selectedIndexes()])

        def _update_overlay_filter(self, _index=None):
            selected = self.overlay_filter.currentData() or FILTER_ALL
            self.left_panel.set_overlay_filter(selected)
            self.right_panel.set_overlay_filter(selected)

        def populate(self):
            # Rebuild links after additions/removals/reviews. Temporary previews
            # are intentionally never written to .vsynch, nor into selections.
            self._navigation_indices = build_pair_navigation_index(self.session)
            self.left_panel.show_counterparts([], navigate=False)
            self.right_panel.show_counterparts([], navigate=False)
            self._navigation_notice = ''
            # Recreate the visible queue, maintaining the selected link by ID.
            previous_id = (self.links.currentItem().data(Qt.ItemDataRole.UserRole)
                           if self.links.currentItem() else None)
            self._populating_links = True
            self.links.clear()
            name_a = {l['id']: f"{l['page_label']}:{l['ordinal']}" for l in self.left_lines}
            name_b = {l['id']: f"{l['page_label']}:{l['ordinal']}" for l in self.right_lines}
            left_styles, right_styles = {}, {}
            for link in self.session['links']:
                style = style_for_link(link)
                for uid in link['reference_ids']:
                    left_styles[uid] = style
                for uid in link['target_ids']:
                    right_styles[uid] = style
            stale = stale_link_ids(self.project, self.session)
            for link in ordered_links(self.project, self.session,
                                      self.review_filter.currentData() or 'all'):
                a = ', '.join(name_a.get(x, '[ligne modifiée]') for x in link['reference_ids']) or '∅'
                b = ', '.join(name_b.get(x, '[ligne modifiée]') for x in link['target_ids']) or '∅'
                from PySide6.QtWidgets import QListWidgetItem
                if link.get('kind') == 'absence':
                    source_label = self.left_witness['id'] if link['reference_ids'] else self.right_witness['id']
                    missing_label = self.right_witness['id'] if link['reference_ids'] else self.left_witness['id']
                    detail = a if link['reference_ids'] else b
                    content = tr('exception.link.label', source=source_label,
                                 lines=detail, missing=missing_label)
                else:
                    content = f"[{link['state']}]  {a} ↔ {b}  · {link['kind']}"
                if link['id'] in stale:
                    content = tr('alignment.stale.tag') + ' ' + content
                entry = QListWidgetItem(content)
                if link['id'] in stale:
                    entry.setToolTip(tr('alignment.stale.revalidate.tip'))
                entry.setData(Qt.ItemDataRole.UserRole, link['id'])
                self.links.addItem(entry)
            self._populating_links = False
            if previous_id:
                for i in range(self.links.count()):
                    if self.links.item(i).data(Qt.ItemDataRole.UserRole) == previous_id:
                        self.links.setCurrentRow(i)
                        break
            self._review_visible_ids = [self.links.item(i).data(Qt.ItemDataRole.UserRole)
                                        for i in range(self.links.count())]
            counts = review_counts(self.session)
            self.review_filter.setToolTip(tr('review.counts', **counts))
            for uid in ignored_ids(self.left_witness):
                left_styles[uid] = 'ignored'
            for uid in ignored_ids(self.right_witness):
                right_styles[uid] = 'ignored'
            self.left_panel.set_line_styles(left_styles)
            self.right_panel.set_line_styles(right_styles)
            for widget, lines, witness in ((self.left, self.left_lines, self.left_witness),
                                           (self.right, self.right_lines, self.right_witness)):
                ignored_set = ignored_ids(witness)
                for index, line in enumerate(lines):
                    prefix = tr('scope.text.prefix') if line['id'] in ignored_set else ''
                    tei_map = self._tei_left if witness['id'] == self.left_witness['id'] else self._tei_right
                    line_text = tei_map.get(line['id'], '') if tei_map else line['text']
                    widget.item(index).setText(prefix + f"{line['page_label']} · {line['ordinal']:>3}  " +
                                             (line_text[:140] or tr('tei.visual.no_text' if tei_map
                                                                    else 'scope.no_htr')))
            self.legend.setText(tr('scope.legend'))
            state = pair_progress(self.project, self.session)
            self._progress_summary = (
                f"{self.left_witness['id']} : {state['reference_covered']}/{state['reference_total']}" + tr('ui.lignes') +
                f"{self.right_witness['id']} : {state['target_covered']}/{state['target_total']}" + tr('ui.lignes') +
                f"{state['links']}" + tr('ui.groupes') + f"{state['stale_references']} " + tr('ui.reference.s.a.controler') +
                '  ·  ' + tr('scope.progress', left=state['reference_ignored'], right=state['target_ignored']) +
                '  ·  ' + tr('exception.status', **pair_exception_summary(self.project, self.session)) +
                ('  ·  ' + tr('alignment.stale.count', count=len(stale)) if stale else ''))
            self._render_navigation_status()

        def reset_tei_search(self, *args):
            self._tei_search_hits = []
            self._tei_search_index = -1

        def next_tei_search(self):
            if not hasattr(self, 'tei_search_edit'):
                return
            term = self.tei_search_edit.text().casefold().strip()
            if not term:
                return
            side = self.tei_search_side.currentData()
            witness = self.left_witness if side == 'reference' else self.right_witness
            text_map = self._tei_left if side == 'reference' else self._tei_right
            panel = self.left_panel if side == 'reference' else self.right_panel
            if not self._tei_search_hits:
                # Preserve physical reading order across folios and columns.
                from .reading_stream import reading_stream
                self._tei_search_hits = [line['id'] for line in reading_stream(witness)
                                         if term in text_map.get(line['id'], '').casefold()]
                self._tei_search_index = -1
            if not self._tei_search_hits:
                self._navigation_notice = tr('tei.visual.search_none')
                self._render_navigation_status()
                return
            self._tei_search_index = (self._tei_search_index + 1) % len(self._tei_search_hits)
            uid = self._tei_search_hits[self._tei_search_index]
            self.tabs.setCurrentIndex(0)
            panel.show_counterparts([uid], navigate=True)
            self._navigation_notice = tr('tei.visual.search_result',
                                        position=self._tei_search_index + 1,
                                        count=len(self._tei_search_hits))
            self._render_navigation_status()

        def _render_navigation_status(self):
            text = self._progress_summary
            if self._navigation_notice:
                text += '  |  ' + self._navigation_notice
            self.status.setText(text)

        def _selected_link_ids(self):
            return [item.data(Qt.ItemDataRole.UserRole)
                    for item in self.links.selectedItems()]

        def _review_focus_changed(self, current, previous):
            if not self._populating_links and current is not None:
                self.focus_link()

        def move_review(self, delta):
            if not self.links.count():
                return
            current = self.links.currentRow()
            next_row = max(0, min(self.links.count()-1, current + delta))
            if current == -1:
                next_row = 0 if delta >= 0 else self.links.count()-1
            self.links.clearSelection()
            self.links.setCurrentRow(next_row)
            self.focus_link()

        def validate_and_next(self):
            selected = self.links.currentItem()
            if selected is None:
                self.move_review(1)
                return
            uid = selected.data(Qt.ItemDataRole.UserRole)
            previous_row = self.links.currentRow()
            current = next((l for l in self.session['links'] if l['id'] == uid), None)
            if current is None or current.get('state') == 'validated':
                self.move_review(1)
                return
            try:
                validate_checked(self.project, self.session, [uid])
            except ValueError as exc:
                QMessageBox.warning(self, tr('review.title'), str(exc))
                return
            self.populate()
            # Pending queue shrinks: next item takes the same row. In all-link
            # mode, advance to the following visible item instead.
            next_row = previous_row if self.review_filter.currentData() == 'pending' else previous_row+1
            if self.links.count():
                self.links.setCurrentRow(min(next_row, self.links.count()-1))
                self.focus_link()

        def validate_review_selection(self):
            ids = self._selected_link_ids()
            if not ids:
                QMessageBox.information(self, tr('review.title'), tr('review.empty'))
                return
            try:
                verify_before_review(self.project, self.session, ids)
            except ValueError as exc:
                QMessageBox.warning(self, tr('review.title'), str(exc))
                return
            decision = QMessageBox.question(
                self, tr('review.title'), tr('review.confirm', count=len(ids)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if decision != QMessageBox.StandardButton.Yes:
                return
            try:
                validate_checked(self.project, self.session, ids)
                self.populate()
            except ValueError as exc:
                QMessageBox.warning(self, tr('review.title'), str(exc))

        def recalculate_next_interval(self):
            selected = self.links.currentItem()
            if selected is None:
                QMessageBox.information(self, tr('review.title'), tr('review.anchor.required'))
                return
            anchor_id = selected.data(Qt.ItemDataRole.UserRole)
            pair = following_anchor_interval(self.project, self.session, anchor_id)
            if pair is None:
                QMessageBox.information(self, tr('review.title'), tr('review.anchor.required'))
                return
            self.interpolate(only_interval=pair)

        def change_scope(self, ignored):
            """Mark ALTO lines outside the studied text, project-wide per witness."""
            left, right = self.selection()
            changes = {}
            for witness, ids in ((self.left_witness, left), (self.right_witness, right)):
                candidates = sorted(set(ids) - ignored_ids(witness)) if ignored else sorted(set(ids) & ignored_ids(witness))
                if candidates:
                    changes[witness['id']] = candidates
            if not changes:
                QMessageBox.information(self, tr('scope.title'), tr('scope.no_selection'))
                return
            try:
                conflicts = linked_scope_conflicts(self.project, changes) if ignored else {}
                authorize_unlink = False
                if conflicts:
                    affected = sum(conflicts.values())
                    answer = QMessageBox.question(
                        self, tr('scope.confirm.title'),
                        tr('scope.confirm.text', count=affected),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                    if answer != QMessageBox.StandardButton.Yes:
                        return
                    authorize_unlink = True
                outcome = update_ignored_lines(self.project, changes,
                    ignored=ignored, unlink_existing=authorize_unlink)
                self._clear_work_selection()
                self.populate()
                self._navigation_notice = tr('scope.changed', count=outcome['changed'])
                self._render_navigation_status()
            except ValueError as exc:
                QMessageBox.warning(self, tr('scope.title'), tr(str(exc)))

        def _show_counterparts(self, side, uid):
            """Show links of the *current witness selection*, never just a stale click.

            Ctrl and Shift can select multiple physical lines. Preview the
            union of their registered counterparts in pink; a plain click
            replaces the selection globally, clearing the previous preview.
            Preview UIDs are never added to the opposite witness selection.
            """
            from_reference = side == 'reference'
            source = self.left_panel if from_reference else self.right_panel
            other = self.right_panel if from_reference else self.left_panel
            from .correspondence_navigation import combined_counterparts
            entries = self._navigation_indices[0 if from_reference else 1]
            targets, has_absence = combined_counterparts(
                entries, source.selected_ids(), clicked=uid)
            source.show_counterparts([], navigate=False)
            if targets:
                found_count = other.show_counterparts(targets, navigate=True)
                label = self.right_witness['id'] if from_reference else self.left_witness['id']
                if found_count:
                    self._navigation_notice = (
                        tr('ui.correspondance.affichee') + f'{found_count}' +
                        tr('ui.ligne.s.dans') + label + tr('ui.rose.non.selectionnees'))
                    if found_count < len(targets):
                        self._navigation_notice += ' ' + tr('ui.certaines.lignes.liees.sont.introuvables.dans.les')
                else:
                    self._navigation_notice = tr('ui.correspondance.enregistree.mais.lignes.introuvables.dans.les')
            else:
                other.show_counterparts([], navigate=False)
                self._navigation_notice = (tr('alignment.counterpart.absent') if has_absence
                                           else tr('alignment.counterpart.none'))
            self._render_navigation_status()

        def focus_link(self):
            item = self.links.currentItem()
            if item is None: return
            uid = item.data(Qt.ItemDataRole.UserRole)
            link = next((l for l in self.session['links'] if l['id'] == uid), None)
            if link is None: return
            self.tabs.setCurrentIndex(0)
            # Double-clicking a link is also read-only visual inspection.
            self.left_panel.show_counterparts(link['reference_ids'], navigate=True)
            self.right_panel.show_counterparts(link['target_ids'], navigate=True)
            self._navigation_notice = tr('alignment.counterpart.hint')
            self._render_navigation_status()

        def _clear_work_selection(self):
            self.left.clearSelection()
            self.right.clearSelection()
            self.left_panel.clear_selection()
            self.right_panel.clear_selection()

        def confirm_selected_absence(self):
            """One-sided exception workflow: inspect, confirm, apply atomically."""
            a, b = self.selection()
            if bool(a) == bool(b):
                QMessageBox.information(self, tr('exception.title'),
                    tr('exception.select_one_side'))
                return
            side = 'reference' if a else 'target'
            try:
                preview = preview_confirmed_absence(
                    self.project, self.session, side, a if a else b)
                message = tr('exception.confirm', count=len(preview['selected_ids']),
                    witness=preview['witness'], missing=preview['missing_in'],
                    affected=preview['automatic_groups_affected'],
                    groups=preview['new_absence_groups'])
                accepted = QMessageBox.question(self, tr('exception.title'), message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if accepted != QMessageBox.StandardButton.Yes:
                    return
                outcome = confirm_absence(self.project, self.session, preview)
                self._clear_work_selection()
                self.populate()
                self._navigation_notice = tr('exception.complete',
                    count=outcome['line_count'], missing=outcome['missing_in'])
                self._render_navigation_status()
            except ValueError as exc:
                QMessageBox.warning(self, tr('exception.title'), str(exc))

        def revoke_selected_absences(self):
            """Explicitly return absence lines to the unresolved pool."""
            ids = self._selected_link_ids()
            if not ids:
                QMessageBox.information(self, tr('exception.title'),
                    tr('exception.revoke.select'))
                return
            matching = {l['id']: l for l in self.session.get('links', [])}
            if len(ids) != len(set(ids)) or any(
                    matching.get(uid, {}).get('kind') != 'absence' for uid in ids):
                QMessageBox.warning(self, tr('exception.title'),
                    tr('exception.revoke.only_absences'))
                return
            approved = QMessageBox.question(self, tr('exception.title'),
                tr('exception.revoke.confirm', count=len(ids)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if approved != QMessageBox.StandardButton.Yes:
                return
            self.session['links'] = [l for l in self.session['links'] if l['id'] not in set(ids)]
            self.populate()
            self._navigation_notice = tr('exception.revoke.done', count=len(ids))
            self._render_navigation_status()

        def attach(self, kind):
            try:
                a, b = self.selection()
                if kind == 'correspondence':
                    result = extend_pair_link(self.project, self.session, a, b)
                    if result['action'] == 'unchanged':
                        QMessageBox.information(self, tr('alignment.edit.title'),
                                                tr('alignment.edit.already_linked'))
                        return
                else:
                    result = None
                    add_pair_link(self.project, self.session, a, b, kind=kind)
                self._clear_work_selection()
                self.populate()
                if result and result['action'] == 'extended':
                    self._navigation_notice = tr('alignment.edit.extended',
                        reference=result['added_reference'], target=result['added_target'])
                    self._render_navigation_status()
            except ValueError as exc:
                QMessageBox.warning(self, tr('ui.association.impossible'), tr(str(exc)))

        def automatic(self):
            try:
                outcome = suggest_htr_pair_alignment(self.project, self.session)
                candidates = outcome['proposals']
                if not candidates:
                    QMessageBox.information(self, 'Aucune proposition',
                        'Aucun rapprochement textuel obtenu. La HTR est facultative : '
                        'vous pouvez travailler directement sur les images.\n'
                        + '\n'.join(outcome['warnings']))
                    return
                review = QDialog(self); review.setWindowTitle('Propositions HTR–HTR (facultatives)')
                review.resize(min(self.width(),900), min(self.height(),550))
                layout = QVBoxLayout(review)
                layout.addWidget(QLabel(f"{len(candidates)} " + tr('ui.groupes.proposes.aucune.validation.automatique.selectionnez.ceux')))
                options = QListWidget(); options.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                names_a = {ln['id']: f"{ln['page_label']}:{ln['ordinal']}" for ln in self.left_lines}
                names_b = {ln['id']: f"{ln['page_label']}:{ln['ordinal']}" for ln in self.right_lines}
                for suggestion in candidates:
                    a = ', '.join(names_a.get(x, '?') for x in suggestion['reference_ids'])
                    b = ', '.join(names_b.get(x, '?') for x in suggestion['target_ids'])
                    options.addItem(f"{suggestion['confidence']:.0%} HTR [{suggestion['state']}] · {a} ↔ {b}")
                layout.addWidget(options)
                buttons = QHBoxLayout(); layout.addLayout(buttons)
                def accept_selection():
                    picked = [candidates[i.row()] for i in options.selectedIndexes()]
                    counts = apply_pair_proposals(self.project, self.session, picked)
                    self.populate(); review.accept()
                    QMessageBox.information(self, 'Propositions enregistrées',
                        f"{counts['added']} " + tr('ui.groupes.sauvegardes') + f" {counts['skipped']} " + tr('ui.ignores.ils.necessitent.une.verification.sur.les'))
                for title, callback in [('Conserver la sélection', accept_selection), ('Annuler', review.reject)]:
                    button = QPushButton(title); button.clicked.connect(callback); buttons.addWidget(button)
                _run_modal(review)
            except Exception as exc:
                QMessageBox.warning(self, 'Alignement HTR–HTR', str(exc))

        def interpolate(self, only_interval=None):
            """Preview the global estimate, optionally limiting to one anchor pair."""
            try:
                outcome = suggest_textual_progress(self.project, self.session)
                proposals = outcome['proposals']
                if only_interval is not None:
                    proposals = suggestions_for_interval(outcome, *only_interval)
                details = tr('progress.summary',
                             intervals=1 if only_interval is not None else outcome['calculated_intervals'],
                             total=1 if only_interval is not None else outcome['eligible_intervals'],
                             ref=(len({uid for p in proposals for uid in p['reference_ids']})
                                  if only_interval is not None else outcome['reference_covered']),
                             target=(len({uid for p in proposals for uid in p['target_ids']})
                                     if only_interval is not None else outcome['target_covered']),
                             count=len(proposals))
                explanations = []
                for diagnostic in outcome['warnings']:
                    reason = diagnostic.get('reason', 'unknown')
                    message = tr('progress.warning.' + reason)
                    if message == 'progress.warning.' + reason:
                        message = reason
                    if reason in ('one_sided_gap', 'outside_anchors_start', 'outside_anchors_end'):
                        message += f" (pivot: {diagnostic.get('reference_count', 0)}, cible: {diagnostic.get('target_count', 0)})"
                    if message not in explanations:
                        explanations.append(message)
                warning_text = '\n'.join(explanations)
                if not proposals:
                    QMessageBox.information(self, tr('progress.title'),
                        details + ('\n' + warning_text if warning_text else ''))
                    return
                review = QDialog(self)
                review.setWindowTitle(tr('progress.title'))
                review.resize(min(self.width(), 940), min(self.height(), 620))
                layout = QVBoxLayout(review)
                if only_interval is not None:
                    details += '\n' + tr('review.local.preview', count=len(proposals))
                label = QLabel(details + '\n' + tr('progress.preview.tip'))
                label.setWordWrap(True)
                layout.addWidget(label)
                names_a = {line['id']:f"{line['page_label']}:{line['ordinal']}" for line in self.left_lines}
                names_b = {line['id']:f"{line['page_label']}:{line['ordinal']}" for line in self.right_lines}
                options = QListWidget()
                options.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                for proposal in proposals:
                    ref_label = ', '.join(names_a.get(uid, '?') for uid in proposal['reference_ids'])
                    target_label = ', '.join(names_b.get(uid, '?') for uid in proposal['target_ids'])
                    evidence = proposal['evidence']
                    method = f"{evidence['reference_method']}/{evidence['target_method']}"
                    options.addItem(f"{ref_label} ↔ {target_label}  [{method}]")
                layout.addWidget(options, 1)
                options.selectAll()
                if warning_text:
                    warnings = QLabel(tr('progress.warnings') + '\n' + warning_text)
                    warnings.setWordWrap(True)
                    layout.addWidget(warnings)
                buttons = QHBoxLayout()
                layout.addLayout(buttons)

                def save_selected():
                    selected = [proposals[i.row()] for i in options.selectedIndexes()]
                    if not selected:
                        QMessageBox.information(review, tr('progress.title'), tr('progress.empty'))
                        return
                    from .physical_alignment import is_revisable_automatic
                    old = [link for link in self.session.get('links', [])
                           if is_revisable_automatic(link)]
                    ids_a = {uid for group in selected for uid in group['reference_ids']}
                    ids_b = {uid for group in selected for uid in group['target_ids']}
                    affected = sum(bool(set(link['reference_ids']) & ids_a or
                                        set(link['target_ids']) & ids_b) for link in old)
                    if affected:
                        decision = QMessageBox.question(review, tr('progress.confirm.title'),
                            tr('progress.confirm.text', count=affected),
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No)
                        if decision != QMessageBox.StandardButton.Yes:
                            return
                    try:
                        result = replace_revisable_pair_proposals(self.project,self.session,selected)
                    except Exception as exc:
                        QMessageBox.warning(review,tr('progress.title'),str(exc))
                        return
                    self.populate()
                    review.accept()
                    QMessageBox.information(self,tr('progress.title'),
                        tr('progress.saved', added=result['added'],
                           replaced=result['replaced'], skipped=result['skipped']))

                for key, callback in (
                    ('common.select_all', options.selectAll),
                    ('common.select_none', options.clearSelection),
                    ('progress.save', save_selected),
                    ('common.cancel', review.reject),
                ):
                    button = QPushButton(tr(key))
                    button.clicked.connect(callback)
                    buttons.addWidget(button)
                _run_modal(review)
            except Exception as exc:
                QMessageBox.warning(self, tr('progress.title'), str(exc))

        def interpolate_geometry(self):
            """Legacy review of conservative column-local geometric suggestions."""
            try:
                outcome = suggest_between_anchors(self.project, self.session,
                                                  regenerate_automatic=True)
                candidates = outcome['proposals']
                details = (f"{outcome['intervals']}" + tr('ui.colonne.s.exploitables') +
                           f"{outcome['skipped_intervals']}" + tr('ui.intervalle.s.ignore.s'))
                warnings = '\n'.join(dict.fromkeys(outcome['warnings']))
                suggested_a = sum(len(p['reference_ids']) for p in candidates)
                suggested_b = sum(len(p['target_ids']) for p in candidates)
                coverage_detail = (tr('alignment.suggested_lines.prefix') +
                                   f"{self.left_witness['id']} {suggested_a} · " +
                                   f"{self.right_witness['id']} {suggested_b}")
                if not candidates:
                    QMessageBox.information(self, 'Interpolation géométrique',
                        details + '\n' + tr('ui.aucune.correspondance.supplementaire.proposee') + '\n' + warnings)
                    return
                review = QDialog(self)
                review.setWindowTitle('Compléter les lignes entre ancrages — prévisualisation')
                review.resize(min(self.width(),930), min(self.height(),570))
                layout = QVBoxLayout(review)
                desc = QLabel(f"{len(candidates)} " + tr('release.groups_estimated') + f" {details}\n" +
                    coverage_detail + '\n' +
                    tr('alignment.recalculate.preview') + '\n' +
                    tr('ui.lhtr.nest.quun.indice.facultatif.les.propositions'))
                desc.setWordWrap(True);layout.addWidget(desc)
                names_a={ln['id']:f"{ln['page_label']}:{ln['ordinal']}" for ln in self.left_lines}
                names_b={ln['id']:f"{ln['page_label']}:{ln['ordinal']}" for ln in self.right_lines}
                options=QListWidget()
                options.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                for p in candidates:
                    a=', '.join(names_a.get(x,'?') for x in p['reference_ids'])
                    b=', '.join(names_b.get(x,'?') for x in p['target_ids'])
                    options.addItem(f"{tr('ui.a.verifier')} {a} ↔ {b}")
                layout.addWidget(options,1)
                options.selectAll()
                if warnings:
                    notes=QLabel(tr('ui.limites.detectees')+' '+warnings)
                    notes.setWordWrap(True);layout.addWidget(notes)
                buttons=QHBoxLayout();layout.addLayout(buttons)
                def accept_selection():
                    picked=[candidates[i.row()] for i in options.selectedIndexes()]
                    if not picked:
                        QMessageBox.information(review,'Sélection vide','Sélectionnez au moins une proposition.')
                        return
                    if any(p.get('reference_ids') or p.get('target_ids') for p in picked):
                        # Recalculation is opt-in: the preview stays read-only
                        # until the user confirms replacing tentative machine links.
                        from .physical_alignment import is_revisable_automatic
                        provisional = [l for l in self.session.get('links', [])
                                       if is_revisable_automatic(l)]
                        pending_a = {uid for p in picked for uid in p['reference_ids']}
                        pending_b = {uid for p in picked for uid in p['target_ids']}
                        possibly_replaced = sum(
                            bool(set(l['reference_ids']) & pending_a or
                                 set(l['target_ids']) & pending_b)
                            for l in provisional)
                        if possibly_replaced:
                            confirm = QMessageBox.question(
                                review, tr('alignment.recalculate.confirm.title'),
                                tr('alignment.recalculate.confirm.text',
                                   count=possibly_replaced),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No)
                            if confirm != QMessageBox.StandardButton.Yes:
                                return
                    try:
                        counts=replace_revisable_pair_proposals(self.project,self.session,picked)
                    except ValueError as exc:
                        QMessageBox.warning(review, tr('alignment.recalculate.error.title'), str(exc))
                        return
                    self.populate();review.accept()
                    QMessageBox.information(self,'Interpolation enregistrée',
                        f"{counts['added']} " + tr('ui.groupe.s.ajoute.s') +
                        f" {counts['replaced']} " + tr('alignment.recalculate.replaced') +
                        f" {counts['skipped']} " + tr('ui.ignore.s.toutes.ces.propositions.restent.incertaines'))
                for label,callback in [
                    ('Tout sélectionner',options.selectAll),
                    ('Ne rien sélectionner',options.clearSelection),
                    ('Enregistrer les propositions sélectionnées',accept_selection),
                    ('Annuler',review.reject)]:
                    btn=QPushButton(label);btn.clicked.connect(callback);buttons.addWidget(btn)
                _run_modal(review)
            except Exception as exc:
                QMessageBox.warning(self,'Interpolation géométrique',str(exc))

        def residual(self):
            """Review isolated-line extensions before any change to the project.

            Only unvalidated, algorithmically generated links can be modified;
            a manually corrected or validated correspondence stays protected.
            """
            try:
                outcome=suggest_residual_extensions(self.project,self.session)
                candidates=outcome['proposals']
                diag=outcome['diagnostics']
                diagnostics=tr('alignment.residual.diagnostics',
                    protected=diag['protected'], ambiguous=diag['ambiguous'],
                    both=diag['both_sides_open'], no_neighbour=diag['no_neighbour'],
                    capped=diag['capped'], unreliable=diag['unreliable'])
                if not candidates:
                    QMessageBox.information(self, tr('alignment.residual.title'),
                        tr('alignment.residual.none') + '\n' + diagnostics)
                    return
                review=QDialog(self)
                review.setWindowTitle(tr('alignment.residual.title'))
                review.resize(min(self.width(),850),min(self.height(),520))
                layout=QVBoxLayout(review)
                heading=QLabel(tr('alignment.residual.preview',count=len(candidates)) +
                    '\n' + tr('alignment.residual.explanation'))
                heading.setWordWrap(True)
                layout.addWidget(heading)
                names_a={ln['id']:f"{ln['page_label']}:{ln['ordinal']}" for ln in self.left_lines}
                names_b={ln['id']:f"{ln['page_label']}:{ln['ordinal']}" for ln in self.right_lines}
                original={ln['id']:ln for ln in self.session['links']}
                options=QListWidget()
                options.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
                for p in candidates:
                    old=original.get(p['link_id'],{})
                    a=', '.join(names_a.get(uid,'?') for uid in p['reference_add_ids']) or '—'
                    b=', '.join(names_b.get(uid,'?') for uid in p['target_add_ids']) or '—'
                    lhs=', '.join(names_a.get(uid,'?') for uid in old.get('reference_ids',[]))
                    rhs=', '.join(names_b.get(uid,'?') for uid in old.get('target_ids',[]))
                    options.addItem(tr('alignment.residual.item',
                        left=a,right=b,old_left=lhs,old_right=rhs))
                layout.addWidget(options,1)
                options.selectAll()
                diag_label=QLabel(diagnostics)
                diag_label.setWordWrap(True)
                layout.addWidget(diag_label)
                row=QHBoxLayout()
                layout.addLayout(row)
                def commit():
                    chosen=[candidates[index.row()] for index in options.selectedIndexes()]
                    if not chosen:
                        QMessageBox.information(review,tr('alignment.residual.title'),
                                                tr('alignment.residual.empty'))
                        return
                    confirm=QMessageBox.question(
                        review,tr('alignment.residual.confirm.title'),
                        tr('alignment.residual.confirm.text',count=len(chosen)),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                    if confirm != QMessageBox.StandardButton.Yes:
                        return
                    try:
                        result=apply_residual_extensions(self.project,self.session,chosen)
                    except ValueError as exc:
                        QMessageBox.warning(review,tr('alignment.residual.title'),str(exc))
                        return
                    review.accept()
                    self.populate()
                    QMessageBox.information(self,tr('alignment.residual.title'),
                        tr('alignment.residual.saved',
                           groups=result['extended'], lines=result['lines_added']))
                for label,action in (
                    ('common.select_all',options.selectAll),
                    ('common.select_none',options.clearSelection),
                    ('alignment.residual.save',commit),
                    ('common.cancel',review.reject)):
                    button=QPushButton(tr(label));button.clicked.connect(action)
                    row.addWidget(button)
                _run_modal(review)
            except (ValueError,KeyError) as exc:
                QMessageBox.warning(self,tr('alignment.residual.title'),str(exc))

        def revalidate_selection(self):
            """Revalidate the selected stale groups, after a human check on the
            images (all or nothing; a group with a vanished line is refused)."""
            stale = stale_link_ids(self.project, self.session)
            selected = [link_id for link_id in self._selected_link_ids() if link_id in stale]
            if not selected:
                QMessageBox.information(self, tr('review.title'), tr('alignment.stale.select'))
                return
            confirm = QMessageBox.question(
                self, tr('review.title'),
                tr('alignment.stale.revalidate_question', count=len(selected)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                count = revalidate_pair_links(self.project, self.session, selected)
            except ValueError as exc:
                QMessageBox.warning(self, tr('review.title'), tr(str(exc)))
                return
            self.populate()
            self._navigation_notice = tr('alignment.stale.revalidated', count=count)
            self._render_navigation_status()

        def detach_lines(self):
            """Remove clicked line(s), keeping the unselected group members."""
            a, b = self.selection()
            if not a and not b:
                QMessageBox.information(self, tr('alignment.edit.title'),
                                        tr('alignment.edit.select_lines'))
                return
            try:
                result = detach_pair_lines(self.project, self.session, a, b)
                if not result['affected_groups']:
                    QMessageBox.information(self, tr('alignment.edit.title'),
                                            tr('alignment.edit.no_group'))
                    return
                self._clear_work_selection()
                self.populate()
                self.status.setText(self.status.text() + '  |  ' +
                    tr('alignment.edit.detached', groups=result['affected_groups'],
                       removed=result['removed_lines']))
            except ValueError as exc:
                QMessageBox.warning(self, tr('alignment.edit.title'), tr(str(exc)))

        def detach_groups(self):
            """Explicitly delete complete groups selected in the bottom list."""
            selected_ids = self._selected_link_ids()
            if not selected_ids:
                QMessageBox.information(self, tr('alignment.edit.title'),
                                        tr('alignment.edit.select_group'))
                return
            confirm = QMessageBox.question(
                self, tr('alignment.edit.delete_groups.title'),
                tr('alignment.edit.delete_groups.question', count=len(selected_ids)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if confirm != QMessageBox.StandardButton.Yes:
                return
            for link_id in selected_ids:
                remove_pair_link(self.session, link_id)
            self._clear_work_selection()
            self.populate()

        def detach(self):
            """Backward-compatible entry point: prefer the image selection."""
            a, b = self.selection()
            if a or b:
                self.detach_lines()
            else:
                self.detach_groups()

        def review(self, state):
            if state == 'validated':
                # All bulk-validation entry points require confirmation.
                self.validate_review_selection()
                return
            try:
                selected = self._selected_link_ids()
                set_pair_link_states(self.session, selected, state)
                self.populate()
            except ValueError as exc:
                QMessageBox.warning(self, tr('review.title'), str(exc))

    class DraggablePagesList(QListWidget):
        """Persist Qt internal drops even when Qt emits insert/remove, not rowsMoved."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.on_order_changed = None

        def dropEvent(self, event):
            super().dropEvent(event)
            if event.isAccepted() and self.on_order_changed is not None:
                # Defer until Qt has finished its internal item movement.
                QTimer.singleShot(0, self.on_order_changed)

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
                    self.registry_error = str(exc)
                self.done.emit('success', count, '')
            except InterruptedError as exc:
                self.done.emit('cancelled', 0, str(exc))
            except Exception as exc:
                self.done.emit('failed', 0, str(exc))

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
            QTimer.singleShot(0, self._load_visible_thumbnails)

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
                QTimer.singleShot(0, self._commit_displayed_order)

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
                QMessageBox.warning(self, tr('pages.order.error'), str(exc))
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
                QMessageBox.warning(self,tr('Aperçu'),str(exc))

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
            if path:
                try:
                    count = export_iiif_htr_zip(self.witness,selected,path)
                    QMessageBox.information(self,tr('Export terminé'),tr('release.images_exported', count=count))
                except Exception as exc:QMessageBox.critical(self,tr('Export IIIF'),str(exc))

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
                QMessageBox.warning(self, tr('ui.pages.hd.title'), str(exc))
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
                QMessageBox.warning(self, tr('ui.pages.hd.attach'), str(exc))
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
            except Exception as exc:QMessageBox.critical(self,tr('Réimportation'),str(exc))

    class ProtectedBindingComboBox(QComboBox):
        """Never change a manuscript-page association by scrolling over a combo.

        Scrolling works normally after the drop-down list is deliberately opened.
        Ignoring the event otherwise lets the surrounding table scroll.
        """
        def wheelEvent(self, event):
            if self.view().isVisible():
                return super().wheelEvent(event)
            event.ignore()

    class BatchBindingDialog(QDialog):
        """Preview strong and ordinal proposals; user may override any entry.

        The source witness is only changed when the user accepts the dialog.
        """
        def __init__(self, witness, parent=None):
            super().__init__(parent)
            from .bulk_binding import propose_bindings
            self.witness = witness
            self.plan = propose_bindings(witness)
            self.setWindowTitle(tr('resources.binding.title'))
            self.resize(950, 610)
            layout = QVBoxLayout(self)
            help_text = QLabel(tr('resources.binding.help'))
            help_text.setWordWrap(True)
            layout.addWidget(help_text)
            note = QLabel(tr('resources.binding.counts', total=len(self.plan['rows']),
                             ordinal=self.plan['needs_review']))
            layout.addWidget(note)
            controls = QHBoxLayout()
            self.assignment_status = QLabel()
            self.assignment_status.setWordWrap(True)
            controls.addWidget(self.assignment_status, 1)
            self.only_chosen = QCheckBox(tr('resources.binding.only_chosen'))
            self.only_chosen.toggled.connect(self._refresh_binding_state)
            controls.addWidget(self.only_chosen)
            layout.addLayout(controls)
            self.table = QTableWidget(len(self.plan['rows']), 4)
            self.table.setHorizontalHeaderLabels([tr('resources.binding.image'),
                                                   tr('resources.binding.xml'),
                                                   tr('resources.binding.method'),
                                                   tr('resources.binding.warning')])
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setColumnWidth(0, 230)
            self.table.setColumnWidth(1, 280)
            self.table.setColumnWidth(2, 115)
            self.choices = {}
            self.row_index_by_id = {}
            for row_index, row in enumerate(self.plan['rows']):
                page = next(p for p in witness['pages'] if p['id'] == row['page_id'])
                label = str(page.get('label') or row['image'])
                item = QTableWidgetItem(label)
                item.setToolTip(str(row['image']))
                self.table.setItem(row_index, 0, item)
                combo = ProtectedBindingComboBox()
                combo.addItem(tr('resources.binding.none'), None)
                for entry in self.plan['available']:
                    combo.addItem(f"{entry['name']} ({entry['lines']} lignes)",
                                  f"{entry['source_id']}::{entry['page_index']}")
                target = tuple(row['target']) if row['target'] is not None else None
                if target is not None:
                    index = combo.findData(f'{target[0]}::{target[1]}')
                    if index >= 0:
                        combo.setCurrentIndex(index)
                self.table.setCellWidget(row_index, 1, combo)
                self.choices[row['page_id']] = combo
                self.row_index_by_id[row['page_id']] = row_index
                combo.currentIndexChanged.connect(self._refresh_binding_state)
                method = QTableWidgetItem(tr('resources.binding.' + row['method']))
                self.table.setItem(row_index, 2, method)
                self.table.setItem(row_index, 3, QTableWidgetItem(
                    tr('resources.binding.review_ordinal') if row['method'] == 'ordinal'
                    else row['warning']))
            self.table.verticalHeader().setDefaultSectionSize(54)
            layout.addWidget(self.table, 1)
            self._thumbnail_attempted = set()
            self.table.verticalScrollBar().valueChanged.connect(self._load_visible_thumbnails)
            QTimer.singleShot(0, self._load_visible_thumbnails)
            self._refresh_binding_state()
            footer = QHBoxLayout()
            layout.addLayout(footer)
            apply = QPushButton(tr('resources.binding.apply'))
            apply.clicked.connect(self.commit)
            footer.addStretch(1)
            footer.addWidget(apply)
            cancel = QPushButton(tr('resources.cancel'))
            cancel.clicked.connect(self.reject)
            cancel.setToolTip(tr('ui.resources.cancel.tip'))
            footer.addWidget(cancel)

        def _load_visible_thumbnails(self, *_):
            """Never decode a whole manuscript's image set at dialog opening."""
            viewport = self.table.viewport().rect()
            by_id = {p['id']: p for p in self.witness.get('pages', [])}
            for index, row in enumerate(self.plan['rows']):
                if index in self._thumbnail_attempted:
                    continue
                item = self.table.item(index, 0)
                if item is None or not self.table.visualItemRect(item).intersects(viewport):
                    continue
                self._thumbnail_attempted.add(index)
                page = by_id.get(row['page_id'])
                if page is None or page.get('image_kind') != 'local':
                    continue
                reader = QImageReader(str(page.get('image_path', '')))
                reader.setAutoTransform(True)
                size = reader.size()
                if size.isValid():
                    reader.setScaledSize(size.scaled(QSize(60, 50), Qt.AspectRatioMode.KeepAspectRatio))
                thumb = reader.read()
                if not thumb.isNull():
                    item.setIcon(QIcon(QPixmap.fromImage(thumb)))

        def _selected_bindings(self):
            selections = {}
            for pid, combo in self.choices.items():
                value = combo.currentData()
                if value is None:
                    selections[pid] = None
                else:
                    sid, index = value.rsplit('::', 1)
                    selections[pid] = (sid, int(index))
            return selections

        def _refresh_binding_state(self, *_):
            from .bulk_binding import binding_selection_conflicts
            selections = self._selected_bindings()
            conflicts = binding_selection_conflicts(self.plan, selections, self.witness)
            in_conflict = {p['page_id'] for conflict in conflicts for p in conflict['pages']}
            selected_count = sum(value is not None for value in selections.values())
            if conflicts:
                self.assignment_status.setText(tr('resources.binding.conflict_status',
                    selected=selected_count, count=len(conflicts)))
                self.assignment_status.setStyleSheet('color: #b42318; font-weight: bold;')
            else:
                self.assignment_status.setText(tr('resources.binding.selected_count',
                    selected=selected_count))
                self.assignment_status.setStyleSheet('')
            for row in self.plan['rows']:
                pid = row['page_id']
                index = self.row_index_by_id[pid]
                chosen = selections[pid]
                prior = tuple(row['target']) if row['target'] is not None else None
                method = ('unresolved' if chosen is None else
                          row['method'] if chosen == prior else 'manual')
                self.table.item(index, 2).setText(tr('resources.binding.' + method))
                warning = (tr('resources.binding.duplicate_row') if pid in in_conflict
                           else (row.get('warning', '') if chosen == prior else ''))
                warning_item = self.table.item(index, 3)
                warning_item.setText(warning)
                warning_item.setBackground(QBrush(QColor('#ffdad5')) if pid in in_conflict
                                           else QBrush())
                self.table.setRowHidden(index, self.only_chosen.isChecked() and chosen is None)
            return conflicts

        def _show_duplicate_conflicts(self, conflicts):
            details = []
            for conflict in conflicts:
                labels = ', '.join(page['label'] for page in conflict['pages'])
                details.append(f"{conflict['xml']} : {labels}")
            first_page = conflicts[0]['pages'][0]['page_id']
            row_index = self.row_index_by_id[first_page]
            self.only_chosen.setChecked(False)
            self.table.scrollToItem(self.table.item(row_index, 0))
            self.table.selectRow(row_index)
            QMessageBox.warning(self, tr('resources.binding.title'),
                tr('resources.binding.duplicate_detail') + '\n\n' + '\n'.join(details))

        def commit(self):
            from .bulk_binding import apply_binding_choices
            selections = self._selected_bindings()
            conflicts = self._refresh_binding_state()
            if conflicts:
                self._show_duplicate_conflicts(conflicts)
                return
            try:
                count = sum(v is not None for v in selections.values())
                if count == 0:
                    QMessageBox.information(self, tr('resources.binding.title'),
                                            tr('resources.binding.empty'))
                    return
                ordinal = [r for r in self.plan['rows']
                           if r['method'] == 'ordinal' and selections[r['page_id']] is not None]
                if ordinal:
                    reply = QMessageBox.question(self, tr('resources.binding.title'),
                        tr('resources.binding.ordinal_confirm', count=len(ordinal)),
                        QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
                        QtMessageBox.StandardButton.No)
                    if reply != QtMessageBox.StandardButton.Yes:
                        return
                apply_binding_choices(self.witness, self.plan, selections)
                self.accept()
            except Exception as exc:
                QMessageBox.warning(self, tr('resources.binding.title'), str(exc))

    class SingleWitnessScopeDialog(QDialog):
        """Define one witness's physical perimeter without needing a pair session.

        Edits occur on a *copy*: Cancel makes no change, including linked groups.
        """
        def __init__(self, project, witness_id, parent=None):
            super().__init__(parent)
            self.original_project = project
            self.staged_project = copy.deepcopy(project)
            self.witness = next(w for w in self.staged_project['witnesses']
                                if w['id'] == witness_id)
            self.setWindowTitle(tr('tei.scope.title'))
            self.resize(1100, 800)
            layout = QVBoxLayout(self)
            hint = QLabel(tr('tei.scope.help'))
            hint.setWordWrap(True)
            layout.addWidget(hint)
            from .viewer import LineImagePanel
            self.panel = LineImagePanel(self.witness, self)
            layout.addWidget(self.panel, 1)
            self.message = QLabel('')
            layout.addWidget(self.message)
            footer = QHBoxLayout();layout.addLayout(footer)
            ignore_button = QPushButton(tr('tei.scope.ignore'))
            ignore_button.clicked.connect(lambda: self.change_scope(True))
            footer.addWidget(ignore_button)
            restore_button = QPushButton(tr('tei.scope.restore'))
            restore_button.clicked.connect(lambda: self.change_scope(False))
            footer.addWidget(restore_button)
            footer.addStretch(1)
            save_button = QPushButton(tr('tei.scope.save'))
            save_button.clicked.connect(self.commit)
            footer.addWidget(save_button)
            cancel = QPushButton(tr('resources.cancel'))
            cancel.clicked.connect(self.reject)
            cancel.setToolTip(tr('ui.resources.cancel.tip'))
            footer.addWidget(cancel)
            self.update_styles()

        def update_styles(self):
            ignored = ignored_ids(self.witness)
            self.panel.set_line_styles({uid:'ignored' for uid in ignored})
            self.message.setText(tr('tei.scope.count', count=len(ignored)))

        def change_scope(self, ignored):
            selected = self.panel.selected_ids()
            if not selected:
                QMessageBox.information(self, tr('tei.scope.title'), tr('scope.no_selection'))
                return
            changes = {self.witness['id']:selected}
            conflicts = linked_scope_conflicts(self.staged_project, changes) if ignored else {}
            allow_unlink = False
            if conflicts:
                answer = QMessageBox.question(self, tr('scope.confirm.title'),
                    tr('scope.confirm.text', count=sum(conflicts.values())),
                    QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
                    QtMessageBox.StandardButton.No)
                if answer != QtMessageBox.StandardButton.Yes:
                    return
                allow_unlink = True
            try:
                update_ignored_lines(self.staged_project, changes,
                                     ignored=ignored, unlink_existing=allow_unlink)
                self.panel.clear_selection()
                self.update_styles()
            except Exception as exc:
                QMessageBox.warning(self, tr('tei.scope.title'), str(exc))

        def commit(self):
            self.original_project.clear()
            self.original_project.update(self.staged_project)
            self.accept()

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
            self.project = project
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
                QMessageBox.information(self, tr('tei.binding.title'),
                    tr('tei.binding.success', count=result['count']))
                self.accept()
            except Exception as exc:
                QMessageBox.warning(self, tr('tei.binding.title'), str(exc))
                self.refresh_preview()

    class WitnessResourceDialog(QDialog):
        """One modal transaction for witness and optional documentary resources."""
        def __init__(self, project, witness=None, parent=None):
            super().__init__(parent)
            self.original_project = project
            self.original_witness = witness
            self.staged_project = None
            self.pending = {'images': [], 'xml_files': [], 'tei_files': [], 'manifests': []}
            self.setWindowTitle(tr('resources.witness.edit' if witness else 'resources.witness.new'))
            self.resize(790, 690)
            layout = QVBoxLayout(self)
            hint = QLabel(tr('resources.witness.help'))
            hint.setWordWrap(True)
            layout.addWidget(hint)
            form = QHBoxLayout()
            form.addWidget(QLabel(tr('resources.witness.sigil')))
            self.sigil = QLineEdit(witness['id'] if witness else '')
            self.sigil.setObjectName('witnessSigilEdit')
            self.sigil.setReadOnly(witness is not None)  # stable key in historical links
            form.addWidget(self.sigil)
            form.addWidget(QLabel(tr('resources.witness.label')))
            self.label_edit = QLineEdit(witness.get('label', '') if witness else '')
            form.addWidget(self.label_edit, 2)
            layout.addLayout(form)
            self.pivot = QCheckBox(tr('resources.witness.pivot'))
            self.pivot.setChecked(project.get('pivot_witness_id') == (witness or {}).get('id'))
            layout.addWidget(self.pivot)
            self.lists = {}
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll_container = QWidget()
            group_content = QVBoxLayout(scroll_container)
            scroll.setWidget(scroll_container)
            layout.addWidget(scroll, 1)
            for category, title, choose in (
                ('images', 'resources.witness.images', self.add_images),
                ('manifests', 'resources.witness.manifests', self.add_manifest),
                ('xml_files', 'resources.witness.xml', self.add_xml),
                ('tei_files', 'resources.witness.tei', self.add_tei)):
                group = QGroupBox(tr(title))
                group_layout = QVBoxLayout(group)
                lst = QListWidget()
                lst.setMaximumHeight(82)
                self.lists[category] = lst
                group_layout.addWidget(lst)
                actions = QHBoxLayout()
                add_button = QPushButton(tr('resources.witness.add'))
                add_button.clicked.connect(choose)
                add_button.setToolTip(tr('ui.resources.add_resource.tip'))
                actions.addWidget(add_button)
                remove = QPushButton(tr('resources.witness.remove_pending'))
                remove.clicked.connect(lambda checked=False, cat=category: self.remove_pending(cat))
                remove.setToolTip(tr('ui.resources.remove_resource.tip'))
                actions.addWidget(remove)
                actions.addStretch(1)
                group_layout.addLayout(actions)
                if category == 'tei_files':
                    tei_note = QLabel(tr('resources.witness.tei_note'))
                    tei_note.setWordWrap(True)
                    group_layout.addWidget(tei_note)
                group_content.addWidget(group)
            group_content.addStretch(1)
            # Existing sources are displayed, but not removable here to avoid
            # invalidating established image/line links silently.
            self.refresh_lists()
            footer = QHBoxLayout()
            layout.addLayout(footer)
            auto = QPushButton(tr('resources.binding.title') + '…')
            auto.clicked.connect(self.preview_bindings)
            auto.setToolTip(tr('ui.resources.auto.tip'))
            footer.addWidget(auto)
            footer.addStretch(1)
            accept = QPushButton(tr('resources.witness.confirm'))
            accept.clicked.connect(self.commit)
            accept.setToolTip(tr('ui.resources.save.tip'))
            footer.addWidget(accept)
            cancel = QPushButton(tr('resources.cancel'))
            cancel.clicked.connect(self.reject)
            cancel.setToolTip(tr('ui.resources.cancel.tip'))
            footer.addWidget(cancel)

        def _existing(self, category):
            if self.original_witness is None:
                return []
            witness = self.original_witness
            if category == 'images':
                return [s['reference'] for s in witness['image_sources'] if s['kind'] == 'local']
            if category == 'manifests':
                return [s['reference'] for s in witness['image_sources'] if s['kind'] == 'iiif']
            if category == 'xml_files':
                return [s['path'] for s in witness['alto_sources']]
            return [r['path'] for r in self.original_project.get('text_resources', [])
                    if r.get('kind') == 'tei' and r.get('witness_id') == witness['id']]

        def refresh_lists(self):
            for category, lst in self.lists.items():
                lst.clear()
                for path in self._existing(category):
                    item = QListWidgetItem('✓  ' + str(path))
                    item.setData(Qt.ItemDataRole.UserRole, None)
                    lst.addItem(item)
                for path in self.pending[category]:
                    item = QListWidgetItem('+  ' + str(path))
                    item.setData(Qt.ItemDataRole.UserRole, str(path))
                    lst.addItem(item)

        def add_images(self):
            paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.images'), '',
                                   'Images (*.jpg *.jpeg *.png *.tif *.tiff *.webp)')
            self._add('images', paths)

        def add_xml(self):
            paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.xml'), '', 'XML (*.xml)')
            self._add('xml_files', paths)

        def add_tei(self):
            paths, _ = QFileDialog.getOpenFileNames(self, tr('resources.witness.tei'), '',
                                   'TEI XML (*.xml *.tei)')
            self._add('tei_files', paths)

        def add_manifest(self):
            url, ok = QInputDialog.getText(self, tr('resources.witness.manifests'),
                                          tr('resources.witness.manifest_url'))
            if ok and url.strip():
                self._add('manifests', [url.strip()])

        def _add(self, category, paths):
            for path in paths:
                if path not in self.pending[category] and path not in self._existing(category):
                    self.pending[category].append(path)
            self.staged_project = None
            self.refresh_lists()

        def remove_pending(self, category):
            item = self.lists[category].currentItem()
            if item is None:
                return
            path = item.data(Qt.ItemDataRole.UserRole)
            if path is not None and path in self.pending[category]:
                self.pending[category].remove(path)
                self.staged_project = None
                self.refresh_lists()
            elif path is None:
                QMessageBox.information(self, tr('resources.witness.edit'),
                                        tr('resources.witness.existing_protected'))

        def build_stage(self):
            from .resource_workflow import apply_witness_draft
            # Build from a fresh snapshot; existing resources remain identical.
            draft = copy.deepcopy(self.original_project)
            apply_witness_draft(draft, identifier=self.sigil.text(),
                                label=self.label_edit.text(), is_pivot=self.pivot.isChecked(),
                                **self.pending)
            self.staged_project = draft
            self._staged_identity = (self.sigil.text(), self.label_edit.text(),
                                     self.pivot.isChecked(), repr(self.pending))
            return draft

        def stage_current(self):
            identity = (self.sigil.text(), self.label_edit.text(),
                        self.pivot.isChecked(), repr(self.pending))
            return self.staged_project if self.staged_project is not None and self._staged_identity == identity else self.build_stage()

        def preview_bindings(self):
            try:
                staged = self.stage_current()
                witness = next(w for w in staged['witnesses'] if w['id'] == self.sigil.text().strip())
                if not witness['pages'] or not witness['alto_sources']:
                    QMessageBox.information(self, tr('resources.binding.title'),
                                            tr('resources.binding.missing'))
                    return
                dialog = BatchBindingDialog(witness, self)
                _run_modal(dialog)
            except Exception as exc:
                QMessageBox.warning(self, tr('resources.witness.edit'), str(exc))

        def commit(self):
            try:
                staged = self.stage_current()
                # All imports and matching were applied to the draft only.
                self.original_project.clear()
                self.original_project.update(staged)
                self.accept()
            except Exception as exc:
                QMessageBox.warning(self, tr('resources.witness.edit'), str(exc))


    class GuidedWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.project = new_project()
            self.path = None
            self._changes = ProjectChangeTracker(self.project)
            self._suppress_close_confirmation = False
            self.setWindowTitle('Varians-Synchro V' + VERSION + tr('ui.atelier.dalignement.2') + '[*]')
            screen = QApplication.primaryScreen()
            bounds = screen.availableGeometry() if screen else None
            self.resize(min(1100, max(450, int(bounds.width() * .93))) if bounds else 1050,
                        min(740, max(340, int(bounds.height() * .89))) if bounds else 690)
            central = QWidget();self.setCentralWidget(central)
            root = QVBoxLayout(central)
            root.addWidget(QLabel('<h2>Varians-Synchro</h2>'))
            top = QHBoxLayout();root.addLayout(top)
            for text,callback in [('Nouveau projet',self.new),('Ouvrir .vsynch',self.open),('Enregistrer',self.save)]:
                button = QPushButton(text);button.clicked.connect(callback);top.addWidget(button)
            self.name_label = QLabel();top.addWidget(self.name_label,1)
            help_button = QPushButton(tr('help.open'))
            help_button.setToolTip(tr('help.title'))
            help_button.clicked.connect(self.open_user_manual)
            top.addWidget(help_button)
            top.addWidget(QLabel(tr('common.language')))
            self.language_box = QComboBox()
            self.language_box.setObjectName('languageSelector')
            for language, label in language_labels().items():
                self.language_box.addItem(label, language)
            self.language_box.setCurrentIndex(max(0, self.language_box.findData(get_language())))
            self.language_box.currentIndexChanged.connect(self.change_language)
            top.addWidget(self.language_box)
            splitter = QSplitter();root.addWidget(splitter,1)
            self.nav = QListWidget();self.nav.setFixedWidth(240)
            for text in (tr('navigation.project'), tr('navigation.pages'),
                         tr('navigation.alignment'), tr('navigation.progress')):
                self.nav.addItem(text)
            splitter.addWidget(self.nav)
            self.stack = QStackedWidget();splitter.addWidget(self.stack)
            self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
            self._build_project_tab()
            self._build_pages_tab()
            self._build_alignment_tab()
            self._build_progress_tab()
            root.addWidget(QLabel('Les sources ne sont jamais modifiées. Enregistrez votre projet .vsynch après les opérations.'))
            self.nav.setCurrentRow(0)
            self.refresh()

        def open_user_manual(self):
            from pathlib import Path
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtWidgets import QMessageBox
            path = Path(__file__).resolve().parent.parent / 'docs' / 'user' / (get_language() + '.md')
            if not path.is_file() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                QMessageBox.warning(self, tr('help.title'), tr('help.missing'))

        def change_language(self):
            requested = self.language_box.currentData()
            if requested == get_language():
                return
            set_language(requested)
            from PySide6.QtCore import QSettings
            QSettings('Varians', 'Varians-Synchro').setValue('language', requested)
            # Rebuild only UI widgets, retaining the exact project in memory
            # (including unsaved links). Avoid restarting Qt under Spyder.
            replacement = type(self)()
            replacement.project = self.project
            replacement.path = self.path
            # The UI is being rebuilt, not closed by the user. Preserve the
            # saved baseline AND unsaved changes; never ask to save or discard.
            replacement._changes = self._changes
            replacement.refresh()
            app = QApplication.instance()
            app._varians_synchro_window = replacement
            replacement.show()
            self._suppress_close_confirmation = True
            self.close()

        def _update_save_indicator(self):
            changed = self._changes.is_modified(self.project)
            self.setWindowModified(changed)
            name = 'Projet : ' + self.project['name'] + (f'  ·  {Path(self.path).name}' if self.path else '  ·  ' + tr('project.unsaved_file'))
            self.name_label.setText(name + (tr('project.unsaved_marker') if changed else ''))

        def _confirm_save_or_discard(self) -> bool:
            """True iff losing the current in-memory state is authorized.

            Cancel is the safe default. Save cancellation or an I/O error
            must also prevent closing/replacing the project.
            """
            if not self._changes.is_modified(self.project):
                return True
            prompt = QtMessageBox(self)
            prompt.setIcon(QtMessageBox.Icon.Warning)
            prompt.setWindowTitle(tr('project.unsaved.title'))
            prompt.setText(tr('project.unsaved.question', name=self.project.get('name', '')))
            prompt.setInformativeText(tr('project.unsaved.explanation'))
            prompt.setStandardButtons(QtMessageBox.StandardButton.Save |
                                      QtMessageBox.StandardButton.Discard |
                                      QtMessageBox.StandardButton.Cancel)
            prompt.button(QtMessageBox.StandardButton.Save).setText(tr('project.unsaved.save'))
            prompt.button(QtMessageBox.StandardButton.Discard).setText(tr('project.unsaved.discard'))
            prompt.button(QtMessageBox.StandardButton.Cancel).setText(tr('project.unsaved.cancel'))
            prompt.setDefaultButton(QtMessageBox.StandardButton.Cancel)
            outcome = prompt.exec()
            if outcome == QtMessageBox.StandardButton.Save:
                return self.save()
            return outcome == QtMessageBox.StandardButton.Discard

        def closeEvent(self, event):
            if self._suppress_close_confirmation or self._confirm_save_or_discard():
                event.accept()
            else:
                event.ignore()

        def notice(self, title, detail):
            QMessageBox.information(self,title,detail)

        def operation(self, task):
            try:
                task()
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self,tr('Opération impossible'),str(exc))

        def _build_project_tab(self):
            page = QWidget()
            main = QVBoxLayout(page)
            main.addWidget(QLabel(tr('resources.project.heading')))
            help_text = QLabel(tr('resources.project.intro'))
            help_text.setWordWrap(True)
            main.addWidget(help_text)
            actions = QHBoxLayout()
            main.addLayout(actions)
            add = QPushButton(tr('resources.witness.new'))
            add.setObjectName('addWitnessResourcesButton')
            add.clicked.connect(self.add_witness)
            add.setToolTip(tr('ui.resources.add.tip'))
            actions.addWidget(add)
            actions.addStretch(1)
            self.inventory = QTreeWidget()
            self.inventory.setObjectName('witnessInventory')
            self.inventory.setHeaderLabels([tr('resources.project.witness'),
                                            tr('resources.project.status')])
            self.inventory.itemClicked.connect(self.edit_inventory_item)
            main.addWidget(self.inventory, 1)
            self.stack.addWidget(page)

        def edit_inventory_item(self, item, column=0):
            witness_id = item.data(0, Qt.ItemDataRole.UserRole)
            if not witness_id:
                parent = item.parent()
                witness_id = parent.data(0, Qt.ItemDataRole.UserRole) if parent else None
            if not witness_id:
                return
            witness = next((w for w in self.project['witnesses'] if w['id'] == witness_id), None)
            if witness:
                dialog = WitnessResourceDialog(self.project, witness, self)
                if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                    self.refresh()
                    self._select_pivot()

        def _select_pivot(self):
            pivot = self.project.get('pivot_witness_id')
            if pivot:
                index = self.reference_box.findData(pivot)
                if index >= 0:
                    self.reference_box.setCurrentIndex(index)

        def _build_pages_tab(self):
            page = QWidget()
            main = QVBoxLayout(page)
            heading = QLabel('ui.xml.check_heading')
            main.addWidget(heading)
            introduction = QLabel(tr('pages.order.tab_help'))
            introduction.setWordWrap(True)
            main.addWidget(introduction)
            main.addWidget(QLabel(tr('ui.pages.actions.help')))
            actions = (
                ('pages.order.open', 'openPageOrderButton', self.manage_pages, 'ui.pages.manage.tip'),
                ('resources.binding.title', 'batchBindingButton', self.batch_bind_from_pages, 'ui.pages.batch.tip'),
                ('tei.scope.action', 'openSingleWitnessScopeButton', self.open_single_witness_scope, 'ui.pages.scope.tip'),
                ('tei.binding.action', 'openTeiPhysicalBindingButton', self.open_tei_binding, 'ui.pages.tei.tip'),
            )
            for pair in (actions[:2], actions[2:]):
                row = QHBoxLayout()
                for label, name, callback, tooltip in pair:
                    button = QPushButton(tr(label))
                    button.setObjectName(name)
                    button.setToolTip(tr(tooltip))
                    button.clicked.connect(callback)
                    row.addWidget(button, 1)
                main.addLayout(row)
            self.page_info = QPlainTextEdit()
            self.page_info.setReadOnly(True)
            main.addWidget(self.page_info, 1)
            self.stack.addWidget(page)

        def open_single_witness_scope(self):
            available = [w['id'] for w in self.project.get('witnesses', [])
                         if physical_lines(w)]
            if not available:
                QMessageBox.information(self, tr('tei.scope.title'), tr('tei.scope.no_pages'))
                return
            chosen, ok = QInputDialog.getItem(self, tr('tei.scope.title'),
                tr('tei.binding.witness'), available, 0, False)
            if not ok:
                return
            dialog = SingleWitnessScopeDialog(self.project, chosen, self)
            if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                self.refresh()

        def open_tei_binding(self):
            dialog = TEIPhysicalBindingDialog(self.project, self)
            if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                self.refresh()

        def _build_alignment_tab(self):
            page=QWidget();main=QVBoxLayout(page)
            main.addWidget(QLabel('<h3>' + tr('ui.alignment.heading') + '</h3>'))
            explanation = QLabel(tr('ui.alignment.intro'))
            explanation.setWordWrap(True)
            main.addWidget(explanation)
            self.align_info=QLabel();self.align_info.setWordWrap(True);main.addWidget(self.align_info)
            selectors=QHBoxLayout();main.addLayout(selectors)
            selectors.addWidget(QLabel('Pivot technique :'))
            self.reference_box=QComboBox();selectors.addWidget(self.reference_box,1)
            selectors.addWidget(QLabel('Témoin à aligner :'))
            self.target_box=QComboBox();selectors.addWidget(self.target_box,1)
            b=QPushButton('ui.xml.open_alignment')
            b.setToolTip(tr('ui.alignment.open.tip'))
            b.clicked.connect(self.open_physical_alignment)
            main.addWidget(b)
            self.align_status=QPlainTextEdit();self.align_status.setReadOnly(True);main.addWidget(self.align_status,1)
            self.stack.addWidget(page)

        def export_varians_json(self):
            # Export both strictly validated and working/proposed link collections.
            # This is a physical-reference export, not a fictitious TEI edition.
            try:
                from .varians_export import export_varians_alignments, inspect_varians_export
                names = [w['id'] for w in self.project.get('witnesses', [])]
                if not names:
                    QMessageBox.warning(self, tr('export.varians.title'), tr('export.varians.no_witness'))
                    return
                default = self.project.get('pivot_witness_id') or self.reference_box.currentData()
                reference, ok = QInputDialog.getItem(self, tr('export.varians.title'),
                    tr('export.varians.choose_base'), names,
                    names.index(default) if default in names else 0, False)
                if not ok:
                    return
                warning = QMessageBox.question(self, tr('export.varians.title'),
                    tr('export.varians.warning'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if warning != QMessageBox.StandardButton.Yes:
                    return
                audit = inspect_varians_export(self.project, reference)
                totals = audit['witnesses']
                if not totals:
                    QMessageBox.warning(self, tr('export.varians.title'),
                                        tr('export.varians.only_base'))
                    return
                issues = []
                for wid, data in totals.items():
                    count = data['working_linked_lines']
                    strict = data['validated_linked_lines']
                    if count == 0:
                        cause = tr('export.varians.reason.' + (data['reason'] or 'no_exportable_correspondence'))
                        issues.append(f'{wid}: 0 / 0 — {cause}')
                    elif strict == 0:
                        issues.append(f'{wid}: 0 / {count} — ' + tr('export.varians.reason.working_only'))
                if issues:
                    msg = (tr('export.varians.audit_warning', base=reference)
                           + '\n\n' + '\n'.join(issues) + '\n\n'
                           + tr('export.varians.audit_confirmation'))
                    confirmed = QMessageBox.question(self, tr('export.varians.title'), msg,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                    if confirmed != QMessageBox.StandardButton.Yes:
                        return
                directory = QFileDialog.getExistingDirectory(
                    self, tr('export.varians.choose_empty'))
                if not directory:
                    return
                reports = export_varians_alignments(self.project, reference, directory)
                summary = '; '.join(
                    f'{wid}: {item["validated_linked_lines"]} / {item["working_linked_lines"]}'
                    for wid, item in reports['audit']['witnesses'].items())
                QMessageBox.information(self, tr('export.varians.title'),
                    tr('export.varians.success', path=directory, summary=summary))
            except Exception as exc:
                QMessageBox.critical(self, tr('export.varians.title'), str(exc))

        def _build_progress_tab(self):
            page = QWidget()
            main = QVBoxLayout(page)
            main.addWidget(QLabel('<h3>' + tr('ui.final.heading') + '</h3>'))
            explanation = QLabel(tr('ui.final.intro'))
            explanation.setWordWrap(True)
            main.addWidget(explanation)
            actions = QHBoxLayout()
            refresh_button = QPushButton(tr('ui.final.refresh'))
            refresh_button.clicked.connect(self.refresh)
            actions.addWidget(refresh_button)
            audit_button = QPushButton(tr('audit.action'))
            audit_button.setObjectName('auditProjectButton')
            audit_button.setToolTip(tr('ui.final.audit.help'))
            audit_button.clicked.connect(self.audit_project_integrity)
            actions.addWidget(audit_button)
            main.addLayout(actions)
            export_actions = QHBoxLayout()
            export_button = QPushButton(tr('export.varians.action'))
            export_button.setObjectName('exportVariansJsonButton')
            export_button.setToolTip(tr('ui.final.export_json.tip'))
            export_button.clicked.connect(self.export_varians_json)
            export_actions.addWidget(export_button)
            project_button = QPushButton(tr('ui.final.export_project.action'))
            project_button.setObjectName('exportVariansProjectButton')
            project_button.setToolTip(tr('ui.final.export_project.tip'))
            project_button.clicked.connect(self.export_varians_project)
            export_actions.addWidget(project_button)
            main.addLayout(export_actions)
            explanation = QLabel(tr('ui.final.audit.help'))
            explanation.setWordWrap(True)
            main.addWidget(explanation)
            self.progress = QPlainTextEdit()
            self.progress.setReadOnly(True)
            main.addWidget(self.progress, 1)
            self.stack.addWidget(page)

        def export_varians_project(self):
            """Build a Varians project in an empty folder; never modify sources."""
            from .varians_project_export import export_varians_project
            base = self.project.get('pivot_witness_id') or self.reference_box.currentData()
            has_tei = any(r.get('kind') == 'tei' and r.get('witness_id') == base
                          for r in self.project.get('text_resources', []))
            if not has_tei:
                QMessageBox.warning(self, tr('ui.final.export_project.action'),
                                    tr('ui.final.export_project.no_tei'))
                return
            decision = QMessageBox.question(
                self, tr('ui.final.export_project.action'),
                tr('ui.final.export_project.confirm'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if decision != QMessageBox.StandardButton.Yes:
                return
            folder = QFileDialog.getExistingDirectory(self, tr('export.varians.choose_empty'))
            if not folder:
                return
            try:
                export_varians_project(self.project, base, folder)
            except Exception as exc:
                QMessageBox.critical(self, tr('ui.final.export_project.action'), str(exc))
            else:
                QMessageBox.information(self, tr('ui.final.export_project.action'),
                    tr('ui.final.export_project.success', path=str(Path(folder) / 'project.xml')))

        def audit_project_integrity(self):
            """Editorial preflight in plain language; data and links remain untouched."""
            try:
                from .validation import audit_project
                base = self.project.get('pivot_witness_id') or self.reference_box.currentData()
                report = audit_project(self.project, base_witness_id=base, check_paths=True)
                headline = tr('ui.final.audit.summary', errors=report['errors'],
                              warnings=report['warnings'])
                summary = [headline, '']
                for wid, stats in report['summary']['witnesses'].items():
                    summary.append(tr('ui.final.audit.witness', witness=wid,
                        active=stats['active_lines'], total=stats['physical_lines'],
                        mapped=stats['mapped_pages'], pages=stats['pages']))
                for pair, stats in report['summary']['pairs'].items():
                    summary.append(tr('ui.final.audit.pair', pair=pair,
                        groups=stats.get('correspondences', 0),
                        validated=stats.get('validated', 0),
                        absences=stats.get('confirmed_absences', 0)))
                summary.append('')
                if report['messages']:
                    for issue in report['messages']:
                        key = 'ui.audit.issue.' + issue['code']
                        translated = tr(key)
                        detail = translated if translated != key else issue['code'].replace('_', ' ')
                        subject = issue.get('witness') or issue.get('pair') or ''
                        extra = issue.get('detail', '')
                        severity = tr('ui.final.audit.severity.' + issue['severity'])
                        summary.append(f"{severity} — {subject} : {detail}" +
                                       (f" ({extra})" if extra else ''))
                else:
                    summary.append(tr('ui.final.audit.noissues'))
                self.progress.setPlainText('\n'.join(summary))
                QMessageBox.information(self, tr('audit.title'), headline + '\n' +
                                        tr('audit.details'))
            except Exception as exc:
                QMessageBox.critical(self, tr('audit.title'), str(exc))

        def refresh(self):
            from .resource_workflow import resource_summary
            self._update_save_indicator()
            self.inventory.clear()
            all_rows = []
            for w in self.project['witnesses']:
                info = resource_summary(self.project, w['id'])
                pivot = ' · ' + tr('resources.witness.pivot_label') if info['pivot'] else ''
                state = tr('resources.project.linked', linked=info['mapped'], pages=info['pages'])
                row = QTreeWidgetItem([f"{w['id']} — {w['label']}" + pivot, state])
                row.setData(0, Qt.ItemDataRole.UserRole, w['id'])
                self.inventory.addTopLevelItem(row)
                for source in w['image_sources']:
                    if source['kind'] == 'iiif':
                        detail = (tr('resources.project.manifest_unavailable')
                                  if source.get('status') == 'unavailable'
                                  else tr('resources.project.manifest_loaded',
                                          pages=len((source.get('manifest') or {}).get('canvases', []))))
                        item = QTreeWidgetItem(row, [tr('resources.witness.manifests'), detail])
                        item.setToolTip(0, str(source['reference']))
                    else:
                        item = QTreeWidgetItem(row, [tr('resources.witness.images') + ' · '
                                                 + Path(source['reference']).name,
                                                 tr('resources.project.image_loaded')])
                        item.setToolTip(0, str(source['reference']))
                for src in w['alto_sources']:
                    QTreeWidgetItem(row, [src.get('kind', 'alto').upper() + ' · '
                                              + Path(src['path']).name,
                        tr('resources.project.xml_loaded', lines=src['line_count'])])
                from .tei_binding import tei_binding_status
                for r in self.project.get('text_resources', []):
                    if r.get('kind') == 'tei' and r.get('witness_id') == w['id']:
                        QTreeWidgetItem(row, ['TEI · ' + Path(r['path']).name,
                            (tr('tei.binding.status.' + tei_binding_status(self.project, w['id'], r['id'])['status'])
                             if r.get('tei_binding') else tr('resources.project.tei_pending'))])
                all_rows.append(f"{w['id']}: {info['pages']} pages, {info['mapped']} avec XML, "
                                f"{len(physical_lines(w))} lignes")
            self.inventory.expandAll()
            self.page_info.setPlainText('\n'.join(all_rows) if all_rows
                                        else tr('resources.project.no_witness'))
            olda = self.reference_box.currentData()
            oldb = self.target_box.currentData()
            for selector, selection in ((self.reference_box, olda), (self.target_box, oldb)):
                selector.blockSignals(True)
                selector.clear()
                for w in self.project['witnesses']:
                    selector.addItem(f"{w['id']} ({len(physical_lines(w))} lignes XML)", w['id'])
                index = selector.findData(selection)
                if (selector is self.reference_box and index < 0
                        and self.project.get('pivot_witness_id')):
                    index = selector.findData(self.project['pivot_witness_id'])
                if index >= 0:
                    selector.setCurrentIndex(index)
                selector.blockSignals(False)
            if oldb is None and self.target_box.count() > 1:
                self.target_box.setCurrentIndex(1)
            self.align_info.setText(tr('resources.project.alignment_help'))
            lines = []
            for session in self.project.get('pair_sessions', []):
                try:
                    progress = pair_progress(self.project, session)
                    lines.append(f"{session['reference_witness_id']} ↔ {session['target_witness_id']}: "
                                 f"{progress['links']} groupes, "
                                 f"{progress['reference_covered']}/{progress['reference_total']} et "
                                 f"{progress['target_covered']}/{progress['target_total']} lignes")
                except ValueError as exc:
                    lines.append(str(exc))
            self.align_status.setPlainText('\n'.join(lines) or tr('resources.project.no_alignment'))
            report = '\n'.join(all_rows) + '\n\n'
            report += tr('ui.final.physical_sessions', count=len(self.project.get('pair_sessions', []))) + '\n'
            legacy_count = len(self.project.get('alignment_sessions', []))
            if legacy_count:
                report += tr('ui.final.legacy_sessions', count=legacy_count) + '\n'
            problems = verify_pair_sessions(self.project) + check_alto_files(self.project)
            report += '\n'.join(problems) if problems else tr('ui.final.no_problems')
            self.progress.setPlainText(report)
            self._update_save_indicator()

        def new(self):
            value, ok = QInputDialog.getText(self, tr('project.new'), tr('project.title'))
            if not ok:
                return
            from .core import save_project
            filename = (value.strip() or tr('project.default_name')) + '.vsynch'
            path, _ = QFileDialog.getSaveFileName(self, tr('resources.project.choose_path'),
                                                  filename, 'Projet Varians-Synchro (*.vsynch)')
            if not path:
                return
            if not path.lower().endswith('.vsynch'):
                path += '.vsynch'
            if self.path and Path(path).resolve() == Path(self.path).resolve():
                QMessageBox.warning(self, tr('project.new'), tr('resources.project.current_path'))
                return
            if not self._confirm_save_or_discard():
                return
            new_data = new_project(value.strip() or tr('project.default_name'))
            try:
                save_project(new_data, path)
            except Exception as exc:
                QMessageBox.critical(self, tr('project.save_error'), str(exc))
                return
            # Only replace the in-memory document after the new file is saved.
            self.project = new_data
            self.path = path
            self._changes.reset(self.project)
            self.refresh()

        def open(self):
            path, _ = QFileDialog.getOpenFileName(self, tr('ui.ouvrir.un.projet'), '', 'Projet (*.vsynch)')
            if not path:
                return
            try:
                incoming = load_project(path)
            except Exception as exc:
                QMessageBox.critical(self, tr('project.open_error'), str(exc))
                return
            if not self._confirm_save_or_discard():
                return
            # The previous indentation made this assignment unreachable:
            # the window displayed an empty project while pointing at the
            # selected .vsynch file. Never reset the saved baseline before
            # replacing the in-memory document.
            self.project = incoming
            self.path = path
            self._changes.reset(self.project)
            self.refresh()

        def save(self) -> bool:
            """Return False on Save As cancellation or write failure."""
            path = self.path or QFileDialog.getSaveFileName(
                self, tr('common.save'), 'projet.vsynch',
                'Projet Varians-Synchro (*.vsynch)')[0]
            if not path:
                return False
            try:
                save_project(self.project, path)
            except Exception as exc:
                QMessageBox.critical(self, tr('project.save_error'), str(exc))
                return False
            self.path = path
            self._changes.mark_saved(self.project)
            self._update_save_indicator()
            return True

        def choose_witness(self):
            opts=[f"{w['id']} — {w['label']}" for w in self.project['witnesses']]
            if not opts:
                self.notice(tr('Témoins'),'Créez d’abord un témoin.');return None
            chosen,ok=QInputDialog.getItem(self,'Témoin','Choisissez un témoin',opts,0,False)
            return self.project['witnesses'][opts.index(chosen)] if ok else None

        def add_witness(self):
            dialog = WitnessResourceDialog(self.project, parent=self)
            if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                self.refresh()
                self._select_pivot()

        def batch_bind_from_pages(self):
            witness = self.choose_witness()
            if witness is None:
                return
            try:
                dialog = BatchBindingDialog(witness, self)
                if _run_modal(dialog) == QDialog.DialogCode.Accepted:
                    self.refresh()
            except Exception as exc:
                QMessageBox.warning(self, tr('resources.binding.title'), str(exc))

        def manage_pages(self):
            w=self.choose_witness()
            if w is None:return
            dlg=PagesDialog(self.project,w,self);_run_modal(dlg);self.refresh()

        def open_physical_alignment(self):
            a=self.reference_box.currentData();b=self.target_box.currentData()
            if not a or not b:
                self.notice(tr('Alignement'),'Ajoutez au moins deux témoins.');return
            try:
                session=create_pair_session(self.project,a,b)
                dlg=PairDialog(self.project,session,self);_run_modal(dlg);self.refresh()
            except Exception as exc:
                QMessageBox.warning(self,tr('Synchronisation'),str(exc))


    return GuidedWindow
