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


def make_guided_window(legacy_window_type=None):
    from PySide6.QtCore import Qt, QSize, QTimer, QUrl, QThread, Signal, QPointF
    from PySide6.QtGui import QIcon, QPixmap, QImage, QImageReader, QColor, QBrush, QPainter, QPen, QPolygonF
    from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
    from PySide6.QtWidgets import (QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
        QWidget, QLabel, QComboBox, QGroupBox, QLineEdit, QPushButton, QMessageBox,
        QFileDialog, QInputDialog, QTreeWidget, QTreeWidgetItem, QListWidget,
        QAbstractItemView, QSplitter, QStackedWidget, QPlainTextEdit, QTabWidget,
        QApplication, QToolButton, QMenu, QSizePolicy, QListWidgetItem, QTableWidget, QTableWidgetItem, QCheckBox, QScrollArea, QFrame, QProgressDialog)
    from PySide6.QtWidgets import QMessageBox as QtMessageBox
    from .ui_widgets import (_run_modal, QLabel, QPushButton, QListWidget, QComboBox, QTabWidget,
                             QTreeWidget, QDialog, QMainWindow, QMessageBox, QInputDialog,
                             QFileDialog)

    from .ui_reading_order import ReadingOrderDialog

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

    from .ui_pages import PagesDialog

    from .ui_batch_binding import BatchBindingDialog

    from .ui_scope import SingleWitnessScopeDialog

    from .ui_tei_binding import TEIPhysicalBindingDialog

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
