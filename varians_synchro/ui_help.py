"""Aide intégrée de Varians-Synchro : le guide ``help/<langue>.html``
affiché dans une fenêtre du logiciel (et non plus un fichier ouvert par une
autre application).

La fenêtre n'est pas modale : on lit l'aide en travaillant. ``open_help``
en garde une par fenêtre parente ; ouverte depuis la fenêtre de
synchronisation (elle-même modale), elle en est l'enfant et reste donc
utilisable. Recherche reprise de Varians (``help_search``) : un champ
(Ctrl+F), la liste des sections qui contiennent tous les mots, avec un
extrait, et les occurrences surlignées, parcourues par ◀ ▶ (F3, Maj+F3).
Le sommaire, fait de liens, n'est pas une section.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QSplitter, QTextBrowser, QTextEdit,
                               QVBoxLayout)

from .help_search import Section, Utf16Positions, search
from .errors import localized_text
from .i18n import get_language, tr
from .ui_widgets import fit_to_screen, QDialog, call_soon

HELP_DIR = Path(__file__).resolve().parent.parent / 'help'


def help_path(language=None):
    """Le guide de *language* (la langue de l'interface par défaut), sinon le
    guide français ; ``None`` s'il n'y en a aucun."""
    for lang in (language or get_language(), 'fr'):
        path = Path(HELP_DIR) / f'{lang}.html'
        if path.is_file():
            return path
    return None


class HelpDialog(QDialog):
    help_anchor = None          # the guide itself: no F1 to open it again
    """Le guide utilisateur, avec sa recherche."""

    # Au-delà, seule l'occurrence courante est surlignée (une lettre seule
    # en donnerait des milliers).
    MAX_HIGHLIGHTS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('help.title'))
        self.setModal(False)
        fit_to_screen(self, 980, 720)
        layout = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.search_box = QLineEdit(self)
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setPlaceholderText(tr('help.search.placeholder'))
        self.search_prev = QPushButton('◀', self)
        self.search_next = QPushButton('▶', self)
        self.search_prev.setToolTip(tr('help.search.prev.tip'))
        self.search_next.setToolTip(tr('help.search.next.tip'))
        self.search_status = QLabel('', self)
        bar.addWidget(self.search_box, 1)
        bar.addWidget(self.search_prev)
        bar.addWidget(self.search_next)
        bar.addWidget(self.search_status)
        layout.addLayout(bar)

        self.results = QListWidget(self)
        self.results.setWordWrap(True)
        self.results.setVisible(False)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        path = help_path()
        if path is None:
            self.browser.setPlainText(tr('help.missing'))
        else:
            try:
                self.browser.setHtml(path.read_text(encoding='utf-8'))
            except (OSError, UnicodeDecodeError) as exc:
                self.browser.setPlainText(tr('help.missing') + '\n\n' + localized_text(exc))
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.results)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 680])
        layout.addWidget(splitter, 1)
        # Bouton à nous : celui de Qt (« Close ») n'est pas traduit.
        buttons = QDialogButtonBox(parent=self)
        buttons.addButton(QPushButton(tr('common.close'), self), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        # Entrée dans le champ passe à l'occurrence suivante : aucun bouton
        # par défaut ne doit fermer l'aide.
        for button in (*buttons.buttons(), self.search_prev, self.search_next):
            button.setAutoDefault(False)
            button.setDefault(False)

        self.occurrences = []          # (début, fin) dans le texte de l'aide
        self.current = -1
        self._positions = []
        self._hits = []
        self._sections = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.run_search)
        self.search_box.textChanged.connect(lambda _text: self._timer.start())
        self.search_box.returnPressed.connect(self.next_occurrence)
        self.search_next.clicked.connect(self.next_occurrence)
        self.search_prev.clicked.connect(self.previous_occurrence)
        self.results.currentRowChanged.connect(self._show_section)
        QShortcut(QKeySequence('Ctrl+F'), self, self._focus_search)
        QShortcut(QKeySequence('F3'), self, self.next_occurrence)
        QShortcut(QKeySequence('Shift+F3'), self, self.previous_occurrence)

    def show_anchor(self, anchor):
        """Fait défiler le guide jusqu'à l'élément ``id="anchor"``."""
        self.browser.scrollToAnchor(anchor)

    def _focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()

    def _help_sections(self):
        """Les sections de l'aide : chaque titre et le texte qui le suit,
        sauf celles qui ne sont faites que de liens (le sommaire)."""
        if self._sections is None:
            document = self.browser.document()
            positions = Utf16Positions(self.browser.toPlainText())
            heads = []
            block = document.begin()
            while block.isValid():
                if block.blockFormat().headingLevel():
                    heads.append(block)
                block = block.next()
            end_of_text = document.characterCount() - 1
            sections = []
            if not heads or heads[0].position() > 0:
                sections.append(Section(self.windowTitle(), 0,
                                        positions.python(heads[0].position() if heads else end_of_text)))
            for index, head in enumerate(heads):
                end = heads[index + 1].position() if index + 1 < len(heads) else end_of_text
                if not self._links_only(head, end):
                    sections.append(Section(head.text().strip(), positions.python(head.position()),
                                            positions.python(end)))
            self._sections = sections
        return self._sections

    @staticmethod
    def _links_only(head, end):
        block = head.next()
        while block.isValid() and block.position() < end:
            fragments = block.begin()
            while not fragments.atEnd():
                fragment = fragments.fragment()
                if fragment.isValid() and fragment.text().strip() and not fragment.charFormat().anchorHref():
                    return False
                fragments += 1
            block = block.next()
        return True

    def run_search(self):
        """Cherche le texte du champ dans l'aide (à la fin du délai de frappe,
        ou aussitôt par ◀ ▶) : liste des sections qui contiennent tous les
        mots, avec leur nombre d'occurrences et un extrait, résumé à côté des
        flèches, puis première occurrence montrée. Un champ vide efface les
        résultats."""
        self._timer.stop()
        query = self.search_box.text()
        text = self.browser.toPlainText()
        self._hits = search(text, self._help_sections(), query) if query.strip() else []
        self.results.blockSignals(True)
        self.results.clear()
        for hit in self._hits:
            item = QListWidgetItem(f'{hit.section.title} ({len(hit.spans)})\n{hit.excerpt}')
            item.setToolTip(hit.excerpt)
            self.results.addItem(item)
        self.results.blockSignals(False)
        appears = bool(query.strip()) and not self.results.isVisible()
        self.results.setVisible(bool(query.strip()))
        self.occurrences = sorted(span for hit in self._hits for span in hit.spans)
        positions = Utf16Positions(text)
        self._positions = [(positions.qt(start), positions.qt(end)) for start, end in self.occurrences]
        if not query.strip():
            self.search_status.setText('')
        elif not self._hits:
            self.search_status.setText(tr('help.search.none'))
        else:
            self.search_status.setText(tr('help.search.summary', sections=len(self._hits),
                                          count=len(self.occurrences)))
        self.current = 0 if self.occurrences else -1
        self._show_current()
        if appears:
            # La liste, en apparaissant, rétrécit le texte, qui se remet en
            # page : on replace la vue sur l'occurrence une fois cela fait.
            call_soon(self, self._scroll_to_current)

    def next_occurrence(self):
        """▶, F3 ou Entrée dans le champ : occurrence suivante, la première
        après la dernière. Une recherche qui attend encore la fin de la frappe
        est d'abord lancée, et l'on reste sur sa première occurrence."""
        if self._timer.isActive():
            self.run_search()
            return
        if self.occurrences:
            self.current = (self.current + 1) % len(self.occurrences)
            self._show_current()

    def previous_occurrence(self):
        """◀ ou Maj+F3 : occurrence précédente, la dernière avant la première.
        Une recherche qui attend encore la fin de la frappe est d'abord
        lancée ; on arrive alors sur sa dernière occurrence."""
        if self._timer.isActive():
            self.run_search()
        if self.occurrences:
            self.current = (self.current - 1) % len(self.occurrences)
            self._show_current()

    def _scroll_to_current(self):
        """L'occurrence courante dans le premier tiers de la vue, pas tout en bas."""
        if self.current < 0:
            return
        bar = self.browser.verticalScrollBar()
        bar.setValue(bar.value() + self.browser.cursorRect().top() - self.browser.viewport().height() // 3)

    def _show_section(self, row):
        if 0 <= row < len(self._hits):
            self.current = self.occurrences.index(self._hits[row].spans[0])
            self._show_current()

    def _show_current(self):
        """Surligne les occurrences (la courante plus vivement), montre la
        courante et sélectionne sa section dans la liste."""
        document = self.browser.document()
        selections = []
        shown = (range(len(self._positions)) if len(self._positions) <= self.MAX_HIGHLIGHTS
                 else ([self.current] if self.current >= 0 else []))
        for index in shown:
            start, end = self._positions[index]
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor('#ff9632' if index == self.current else '#fff000'))
            selection.format.setForeground(QColor('#17120b'))
            selection.cursor = QTextCursor(document)
            selection.cursor.setPosition(start)
            selection.cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selections.append(selection)
        self.browser.setExtraSelections(selections)
        if self.current < 0:
            return
        cursor = QTextCursor(document)
        cursor.setPosition(self._positions[self.current][0])
        self.browser.setTextCursor(cursor)
        self._scroll_to_current()
        start = self.occurrences[self.current][0]
        row = next((row for row, hit in enumerate(self._hits)
                    if hit.section.start <= start < hit.section.end), -1)
        self.results.blockSignals(True)
        self.results.setCurrentRow(row)
        self.results.blockSignals(False)


def open_help(parent, anchor=None):
    """Montre l'aide, non modale, une par fenêtre *parent* (gardée d'une
    ouverture à l'autre, recherche comprise), éventuellement à la section
    ``id="anchor"``."""
    dialog = getattr(parent, '_help_dialog', None)
    if dialog is not None:
        try:
            dialog.isVisible()
        except RuntimeError:                 # détruite avec Qt
            dialog = None
    if dialog is None:
        dialog = HelpDialog(parent)
        parent._help_dialog = dialog
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    if anchor:
        dialog.show_anchor(anchor)
    return dialog
