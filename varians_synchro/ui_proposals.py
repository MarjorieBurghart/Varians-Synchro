"""Fenêtre où l'on choisit, parmi des propositions calculées, celles à
enregistrer ; outils communs aux fenêtres de propositions de la
synchronisation (HTR–HTR, progression textuelle, interpolation
géométrique, lignes résiduelles).

La fenêtre ne fait que montrer et sélectionner : chaque appelant garde ses
vérifications, ses confirmations et son enregistrement (``add_buttons``).
"""
from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QVBoxLayout

from .ui_widgets import QDialog, QLabel, QListWidget, QMessageBox, QPushButton


def line_names(lines):
    """Nom court de chaque ligne physique : ``page:rang``."""
    return {line['id']: f"{line['page_label']}:{line['ordinal']}" for line in lines}


def named(names, ids):
    """Noms des lignes ``ids``, séparés par des virgules (« ? » si inconnue)."""
    return ', '.join(names.get(uid, '?') for uid in ids)


def replaced_machine_groups(session, proposals):
    """Nombre de groupes automatiques non validés qu'enregistrer
    ``proposals`` remplacerait (ils touchent une des lignes proposées)."""
    from .physical_alignment import is_revisable_automatic
    reference = {uid for group in proposals for uid in group['reference_ids']}
    target = {uid for group in proposals for uid in group['target_ids']}
    return sum(bool(set(link['reference_ids']) & reference or set(link['target_ids']) & target)
               for link in session.get('links', []) if is_revisable_automatic(link))


def ask(parent, title, text):
    """Question Oui/Non, « Non » par défaut ; vrai si la réponse est « Oui »."""
    buttons = QMessageBox.StandardButton
    return QMessageBox.question(parent, title, text, buttons.Yes | buttons.No,
                                buttons.No) == buttons.Yes


class ProposalReviewDialog(QDialog):
    """Une explication, la liste des propositions (sélection multiple), des
    notes facultatives, puis les boutons ajoutés par ``add_buttons``.

    ``size`` est la taille voulue, limitée à celle de ``parent``.
    ``preselect`` : toutes les propositions sélectionnées à l'ouverture.
    ``list_stretch`` : part de la hauteur donnée à la liste."""

    def __init__(self, parent, *, title, size, intro, items, notes=None,
                 preselect=True, wrap_intro=True, list_stretch=1):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(min(parent.width(), size[0]), min(parent.height(), size[1]))
        layout = QVBoxLayout(self)
        heading = QLabel(intro)
        if wrap_intro:
            heading.setWordWrap(True)
        layout.addWidget(heading)
        self.options = QListWidget()
        self.options.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for text in items:
            self.options.addItem(text)
        layout.addWidget(self.options, list_stretch)
        if preselect:
            self.options.selectAll()
        if notes:
            label = QLabel(notes)
            label.setWordWrap(True)
            layout.addWidget(label)
        self._buttons = QHBoxLayout()
        layout.addLayout(self._buttons)

    def selection_buttons(self, select_all, select_none):
        """Les boutons « tout » et « rien », à passer à ``add_buttons``."""
        return [(select_all, self.options.selectAll), (select_none, self.options.clearSelection)]

    def add_buttons(self, actions):
        """Ajoute un bouton par ``(texte, fonction)``, de gauche à droite."""
        for text, callback in actions:
            button = QPushButton(text)
            button.clicked.connect(callback)
            self._buttons.addWidget(button)

    def picked(self, proposals):
        """Les propositions sélectionnées, dans l'ordre de la sélection."""
        return [proposals[index.row()] for index in self.options.selectedIndexes()]
