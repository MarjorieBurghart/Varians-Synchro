"""Fenêtre « Associer automatiquement les images et les ALTO/PAGE » : propositions par lot, que l’utilisateur peut modifier."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QMessageBox as QtMessageBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from .errors import localized_text
from .i18n import tr
from .ui_widgets import fit_to_screen, call_soon, page_image_reader_ok, plain_tip, QComboBox, QDialog, QLabel, QMessageBox, QPushButton


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
        fit_to_screen(self, 950, 610)
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
            item.setToolTip(plain_tip(row['image']))
            self.table.setItem(row_index, 0, item)
            combo = ProtectedBindingComboBox()
            combo.addItem(tr('resources.binding.none'), None)
            for entry in self.plan['available']:
                combo.addItem(tr('resources.binding.entry', name=entry['name'], lines=entry['lines']),
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
                else localized_text(row['warning'])))
        self.table.verticalHeader().setDefaultSectionSize(54)
        layout.addWidget(self.table, 1)
        self._thumbnail_attempted = set()
        self.table.verticalScrollBar().valueChanged.connect(self._load_visible_thumbnails)
        call_soon(self, self._load_visible_thumbnails)
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
            if not page_image_reader_ok(reader):
                continue
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
                       else (localized_text(row.get('warning', '')) if chosen == prior else ''))
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
            # Rows changed by hand are no longer proposals « par ordre ».
            ordinal = [r for r in self.plan['rows'] if r['method'] == 'ordinal'
                       and r['target'] is not None and selections[r['page_id']] == tuple(r['target'])]
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
            QMessageBox.warning(self, tr('resources.binding.title'), localized_text(exc))
