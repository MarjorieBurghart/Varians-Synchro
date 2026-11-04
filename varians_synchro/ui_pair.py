"""Fenêtre « Synchronisation visuelle entre témoins » : groupes de lignes de deux témoins, propositions, révision rapide et revalidation."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QHBoxLayout, QLineEdit, QMenu,
                               QSplitter, QToolButton, QVBoxLayout, QWidget)

from .correspondence_navigation import build_pair_navigation_index
from .exceptions import confirm_absence, pair_exception_summary, preview_confirmed_absence
from .errors import localized_text
from .i18n import tr
from .interpolation import suggest_between_anchors
from .line_scope import ignored_ids, linked_scope_conflicts, update_ignored_lines
from .overlay_filters import (FILTER_ALL, FILTER_AUTOMATIC_REVIEW, FILTER_UNLINKED,
                              style_for_link)
from .physical_alignment import (add_pair_link, apply_pair_proposals, detach_pair_lines,
                                 extend_pair_link, pair_progress, physical_lines,
                                 remove_pair_link, replace_revisable_pair_proposals,
                                 revalidate_pair_links, set_pair_link_states, stale_link_ids,
                                 suggest_htr_pair_alignment)
from .rapid_review import (following_anchor_interval, ordered_links, review_counts,
                           suggestions_for_interval, validate_checked, verify_before_review)
from .reading_stream import reading_stream
from .residual_alignment import apply_residual_extensions, suggest_residual_extensions
from .textual_progress import suggest_textual_progress
from .ui_proposals import ask, line_names, named, ProposalReviewDialog, replaced_machine_groups
from .ui_reading_order import ReadingOrderDialog
from .ui_widgets import (_run_modal, QComboBox, QDialog, QLabel, QListWidget, QMessageBox,
                         QPushButton, QTabWidget)


class PairDialog(QDialog):
    """Visual-first manual alignment; HTR is optional secondary information."""
    # F1 : l'aide, à la section de cette fenêtre (enfant de la fenêtre,
    # donc utilisable bien que celle-ci soit modale).
    help_anchor = 'synchronisation'
    def __init__(self, project, session, parent=None):
        super().__init__(parent)
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
        self._build_actions(main)
        self._build_filters(main)
        self._build_visual_tab(main)
        self._build_text_tab()
        self._build_review_list(main)
        self.status = QLabel(); self.status.setWordWrap(True); main.addWidget(self.status)
        hint = QLabel(tr('alignment.edit.hint'))
        hint.setWordWrap(True)
        hint.setMaximumHeight(48)
        main.addWidget(hint)
        self.tabs.setMinimumHeight(150)
        self.populate()

    def _build_actions(self, main):
        """Barre d'actions en haut de la fenêtre et leurs raccourcis."""
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
        self.assoc_shortcut=QShortcut(QKeySequence('Ctrl+Return'),self)
        self.assoc_shortcut.activated.connect(lambda: self.attach('correspondence'))
        self.assoc_shortcut2=QShortcut(QKeySequence('Ctrl+Enter'),self)
        self.assoc_shortcut2.activated.connect(lambda: self.attach('correspondence'))
        self.absence_shortcut = QShortcut(QKeySequence('Ctrl+Shift+A'), self)
        self.absence_shortcut.activated.connect(self.confirm_selected_absence)


    def _build_filters(self, main):
        """Consigne, cadres visibles, recherche dans le texte TEI, légende."""
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
                self.tei_search_side.addItem(self.left_witness['id'], 'reference')
            if self._tei_right:
                self.tei_search_side.addItem(self.right_witness['id'], 'target')
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

    def _build_visual_tab(self, main):
        """Onglets ; le premier : les images des deux témoins côte à côte."""
        from .viewer import LineImagePanel
        self.tabs = QTabWidget()
        main.addWidget(self.tabs, 1)
        visual = QWidget(); visual_layout = QVBoxLayout(visual)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.left_panel = LineImagePanel(self.left_witness, split)
        self.right_panel = LineImagePanel(self.right_witness, split)
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
        self.visual_splitter = split

    def _build_text_tab(self):
        """Second onglet : les lignes des deux témoins en texte."""
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

    def _build_review_list(self, main):
        """Barre de révision, liste des groupes et raccourcis de révision."""
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
        review_bar.addStretch(1)
        # Second row: the bar did not fit a laptop screen on one row.
        review_actions = QHBoxLayout(); main.addLayout(review_actions)
        self.batch_review_button = QPushButton(tr('review.validate.selected'))
        self.batch_review_button.clicked.connect(self.validate_review_selection)
        review_actions.addWidget(self.batch_review_button)
        self.local_review_button = QPushButton(tr('review.recalculate.next'))
        self.local_review_button.clicked.connect(self.recalculate_next_interval)
        review_actions.addWidget(self.local_review_button)
        # Groups whose lines changed after a new segmentation of a page.
        self.revalidate_button = QPushButton(tr('alignment.stale.revalidate'))
        self.revalidate_button.setToolTip(tr('alignment.stale.revalidate.tip'))
        self.revalidate_button.clicked.connect(self.revalidate_selection)
        review_actions.addWidget(self.revalidate_button)
        review_actions.addStretch(1)
        self.links = QListWidget(); self.links.setMaximumHeight(125)
        self.links.setMinimumHeight(50)
        self.links.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._populating_links = False
        self.links.itemDoubleClicked.connect(lambda _: self.focus_link())
        self.links.itemActivated.connect(lambda _: self.focus_link())        # Entrée
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

    def open_reading_order(self):
        try:
            dialog = ReadingOrderDialog(self.project, self.session, self)
            _run_modal(dialog)
            # Immediately refresh textual selections in the new reading
            # order. Image panels remain tied to unchanged physical UIDs.
            self.left_lines = reading_stream(self.left_witness, include_ignored=True)
            self.right_lines = reading_stream(self.right_witness, include_ignored=True)
            for panel in (self.left_panel, self.right_panel):
                panel.refresh_reading_order()
            for widget, lines in ((self.left, self.left_lines), (self.right, self.right_lines)):
                widget.clear()
                for line in lines:
                    widget.addItem(f"{line['page_label']} · {line['ordinal']:>3}  " +
                                   (line['text'][:140] or tr('scope.no_htr')))
            self.populate()
        except Exception as exc:
            QMessageBox.warning(self, tr('stream.window.title'), localized_text(exc))

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
                content = (f"[{tr('alignment.state.' + link['state'])}]  {a} ↔ {b}"
                           f"  · {tr('alignment.kind.' + link['kind'])}")
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
            QMessageBox.warning(self, tr('review.title'), localized_text(exc))
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
            QMessageBox.warning(self, tr('review.title'), localized_text(exc))
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
            QMessageBox.warning(self, tr('review.title'), localized_text(exc))

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
            QMessageBox.warning(self, tr('scope.title'), localized_text(exc))

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
            QMessageBox.warning(self, tr('exception.title'), localized_text(exc))

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
            QMessageBox.warning(self, tr('ui.association.impossible'), localized_text(exc))

    def automatic(self):
        try:
            outcome = suggest_htr_pair_alignment(self.project, self.session)
            candidates = outcome['proposals']
            if not candidates:
                QMessageBox.information(self, 'Aucune proposition',
                    '\n'.join([tr('alignment.htr.none'), *map(localized_text, outcome['warnings'])]))
                return
            names_a, names_b = line_names(self.left_lines), line_names(self.right_lines)
            review = ProposalReviewDialog(
                self, title='Propositions HTR–HTR (facultatives)', size=(900, 550),
                intro=f"{len(candidates)} " + tr('ui.groupes.proposes.aucune.validation.automatique.selectionnez.ceux'),
                items=[f"{s['confidence']:.0%} HTR [{tr('alignment.state.' + s['state'])}] · "
                       f"{named(names_a, s['reference_ids'])} ↔ {named(names_b, s['target_ids'])}"
                       for s in candidates],
                preselect=False, wrap_intro=False, list_stretch=0)

            def accept_selection():
                picked = review.picked(candidates)
                if not picked:
                    QMessageBox.information(review, 'Propositions HTR–HTR (facultatives)',
                                            tr('progress.empty'))
                    return
                counts = apply_pair_proposals(self.project, self.session, picked)
                self.populate(); review.accept()
                QMessageBox.information(self, 'Propositions enregistrées',
                    f"{counts['added']} " + tr('ui.groupes.sauvegardes') + f" {counts['skipped']} " + tr('ui.ignores.ils.necessitent.une.verification.sur.les'))
            # Nothing is preselected (HTR is only an optional hint): the
            # button must not suggest an existing selection.
            review.add_buttons(review.selection_buttons(tr('common.select_all'), tr('common.select_none'))
                               + [(tr('progress.save'), accept_selection), (tr('common.cancel'), review.reject)])
            _run_modal(review)
        except Exception as exc:
            QMessageBox.warning(self, 'Alignement HTR–HTR', localized_text(exc))

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
                    message += ' ' + tr('progress.warning.counts',
                                        reference=diagnostic.get('reference_count', 0),
                                        target=diagnostic.get('target_count', 0))
                if message not in explanations:
                    explanations.append(message)
            warning_text = '\n'.join(explanations)
            if not proposals:
                QMessageBox.information(self, tr('progress.title'),
                    details + ('\n' + warning_text if warning_text else ''))
                return
            if only_interval is not None:
                details += '\n' + tr('review.local.preview', count=len(proposals))
            names_a, names_b = line_names(self.left_lines), line_names(self.right_lines)
            review = ProposalReviewDialog(
                self, title=tr('progress.title'), size=(940, 620),
                intro=details + '\n' + tr('progress.preview.tip'),
                items=[f"{named(names_a, p['reference_ids'])} ↔ {named(names_b, p['target_ids'])}  "
                       f"[{p['evidence']['reference_method']}/{p['evidence']['target_method']}]"
                       for p in proposals],
                notes=tr('progress.warnings') + '\n' + warning_text if warning_text else None)

            def save_selected():
                selected = review.picked(proposals)
                if not selected:
                    QMessageBox.information(review, tr('progress.title'), tr('progress.empty'))
                    return
                affected = replaced_machine_groups(self.session, selected)
                if affected and not ask(review, tr('progress.confirm.title'),
                                        tr('progress.confirm.text', count=affected)):
                    return
                try:
                    result = replace_revisable_pair_proposals(self.project,self.session,selected)
                except Exception as exc:
                    QMessageBox.warning(review,tr('progress.title'),localized_text(exc))
                    return
                self.populate()
                review.accept()
                QMessageBox.information(self,tr('progress.title'),
                    tr('progress.saved', added=result['added'],
                       replaced=result['replaced'], skipped=result['skipped']))

            review.add_buttons(review.selection_buttons(tr('common.select_all'), tr('common.select_none'))
                               + [(tr('progress.save'), save_selected), (tr('common.cancel'), review.reject)])
            _run_modal(review)
        except Exception as exc:
            QMessageBox.warning(self, tr('progress.title'), localized_text(exc))

    def interpolate_geometry(self):
        """Legacy review of conservative column-local geometric suggestions."""
        try:
            outcome = suggest_between_anchors(self.project, self.session,
                                              regenerate_automatic=True)
            candidates = outcome['proposals']
            details = (f"{outcome['intervals']}" + tr('ui.colonne.s.exploitables') +
                       f"{outcome['skipped_intervals']}" + tr('ui.intervalle.s.ignore.s'))
            warnings = '\n'.join(dict.fromkeys(map(localized_text, outcome['warnings'])))
            suggested_a = sum(len(p['reference_ids']) for p in candidates)
            suggested_b = sum(len(p['target_ids']) for p in candidates)
            coverage_detail = (tr('alignment.suggested_lines.prefix') +
                               f"{self.left_witness['id']} {suggested_a} · " +
                               f"{self.right_witness['id']} {suggested_b}")
            if not candidates:
                QMessageBox.information(self, 'Interpolation géométrique',
                    details + '\n' + tr('ui.aucune.correspondance.supplementaire.proposee') + '\n' + warnings)
                return
            names_a, names_b = line_names(self.left_lines), line_names(self.right_lines)
            review = ProposalReviewDialog(
                self, title='Compléter les lignes entre ancrages — prévisualisation', size=(930, 570),
                intro=(f"{len(candidates)} " + tr('release.groups_estimated') + f" {details}\n" +
                       coverage_detail + '\n' +
                       tr('alignment.recalculate.preview') + '\n' +
                       tr('ui.lhtr.nest.quun.indice.facultatif.les.propositions')),
                items=[f"{tr('ui.a.verifier')} {named(names_a, p['reference_ids'])} ↔ "
                       f"{named(names_b, p['target_ids'])}" for p in candidates],
                notes=tr('ui.limites.detectees')+' '+warnings if warnings else None)

            def accept_selection():
                picked = review.picked(candidates)
                if not picked:
                    QMessageBox.information(review,'Sélection vide','Sélectionnez au moins une proposition.')
                    return
                # Recalculation is opt-in: the preview stays read-only until
                # the user confirms replacing tentative machine links.
                possibly_replaced = replaced_machine_groups(self.session, picked)
                if possibly_replaced and not ask(
                        review, tr('alignment.recalculate.confirm.title'),
                        tr('alignment.recalculate.confirm.text', count=possibly_replaced)):
                    return
                try:
                    counts=replace_revisable_pair_proposals(self.project,self.session,picked)
                except ValueError as exc:
                    QMessageBox.warning(review, tr('alignment.recalculate.error.title'), localized_text(exc))
                    return
                self.populate();review.accept()
                QMessageBox.information(self,'Interpolation enregistrée',
                    f"{counts['added']} " + tr('ui.groupe.s.ajoute.s') +
                    f" {counts['replaced']} " + tr('alignment.recalculate.replaced') +
                    f" {counts['skipped']} " + tr('ui.ignore.s.toutes.ces.propositions.restent.incertaines'))
            review.add_buttons(review.selection_buttons('Tout sélectionner', 'Ne rien sélectionner')
                               + [('Enregistrer les propositions sélectionnées', accept_selection),
                                  ('Annuler', review.reject)])
            _run_modal(review)
        except Exception as exc:
            QMessageBox.warning(self,'Interpolation géométrique',localized_text(exc))

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
            names_a, names_b = line_names(self.left_lines), line_names(self.right_lines)
            original={ln['id']:ln for ln in self.session['links']}
            items = []
            for p in candidates:
                old=original.get(p['link_id'],{})
                items.append(tr('alignment.residual.item',
                    left=named(names_a, p['reference_add_ids']) or '—',
                    right=named(names_b, p['target_add_ids']) or '—',
                    old_left=named(names_a, old.get('reference_ids',[])),
                    old_right=named(names_b, old.get('target_ids',[]))))
            review = ProposalReviewDialog(
                self, title=tr('alignment.residual.title'), size=(850, 520),
                intro=(tr('alignment.residual.preview',count=len(candidates)) +
                       '\n' + tr('alignment.residual.explanation')),
                items=items, notes=diagnostics)

            def commit():
                chosen=review.picked(candidates)
                if not chosen:
                    QMessageBox.information(review,tr('alignment.residual.title'),
                                            tr('alignment.residual.empty'))
                    return
                if not ask(review, tr('alignment.residual.confirm.title'),
                           tr('alignment.residual.confirm.text', count=len(chosen))):
                    return
                try:
                    result=apply_residual_extensions(self.project,self.session,chosen)
                except ValueError as exc:
                    QMessageBox.warning(review,tr('alignment.residual.title'),localized_text(exc))
                    return
                review.accept()
                self.populate()
                QMessageBox.information(self,tr('alignment.residual.title'),
                    tr('alignment.residual.saved',
                       groups=result['extended'], lines=result['lines_added']))
            review.add_buttons(review.selection_buttons(tr('common.select_all'), tr('common.select_none'))
                               + [(tr('alignment.residual.save'), commit), (tr('common.cancel'), review.reject)])
            _run_modal(review)
        except (ValueError,KeyError) as exc:
            QMessageBox.warning(self,tr('alignment.residual.title'),localized_text(exc))

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
            QMessageBox.warning(self, tr('review.title'), localized_text(exc))
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
            QMessageBox.warning(self, tr('alignment.edit.title'), localized_text(exc))

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
            QMessageBox.warning(self, tr('review.title'), localized_text(exc))
