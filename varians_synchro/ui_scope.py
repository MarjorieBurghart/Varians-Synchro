"""Fenêtre « Périmètre » : lignes d’un témoin exclues de l’étude."""
from __future__ import annotations

import copy

from PySide6.QtWidgets import QHBoxLayout, QMessageBox as QtMessageBox, QVBoxLayout

from .errors import localized_text
from .i18n import tr
from .line_scope import ignored_ids, linked_scope_conflicts, update_ignored_lines
from .ui_widgets import QDialog, QLabel, QMessageBox, QPushButton


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
        cancel.clicked.connect(self.cancel)
        cancel.setToolTip(tr('ui.resources.cancel.tip'))
        footer.addWidget(cancel)
        self.update_styles()

    def has_unsaved_draft(self):
        return self.staged_project != self.original_project

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
            QMessageBox.warning(self, tr('tei.scope.title'), localized_text(exc))

    def commit(self):
        self.original_project.clear()
        self.original_project.update(self.staged_project)
        self.accept()
