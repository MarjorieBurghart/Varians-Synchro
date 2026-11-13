"""macOS : titre des boîtes de message, touche Entrée dans les listes.

Sous macOS, Qt n'affiche pas le titre d'une boîte de message
(``QMessageBox.setWindowTitle`` n'y fait rien, selon les règles d'Apple) :
« Fichier introuvable », « Projet modifié »… n'étaient pas vus. Sous macOS,
le titre devient le message principal et le texte passe dessous, comme une
alerte du Mac ; ailleurs, rien ne change. Ici, Qt sous macOS est simulé :
``setWindowTitle`` ne retient rien.

Sous macOS aussi, Qt n'« active » pas un élément de liste par Entrée (il la
réserve à l'édition) : Entrée ne rouvrait ni une page (étape 1), ni une
fiche de témoin, ni un lien de la synchronisation. Les listes de
Varians-Synchro le font elles-mêmes, partout. Ici, Qt sous macOS est simulé :
la liste de base ne fait rien d'Entrée.
"""
from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QLabel, QListWidget as QtListWidget, QMessageBox as QtMessageBox,
                               QTreeWidget as QtTreeWidget, QTreeWidgetItem)

from varians_synchro import ui_widgets
from varians_synchro.core import create_witness, new_project
from varians_synchro.i18n import tr

BUTTON = QtMessageBox.StandardButton


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def macos(app, monkeypatch):
    """Qt comme sous macOS (le titre d'une boîte n'est pas retenu), et
    Varians-Synchro qui le sait."""
    monkeypatch.setattr(QtMessageBox, 'setWindowTitle', lambda box, title: None)
    monkeypatch.setattr(ui_widgets, 'on_macos', lambda: True)


@pytest.fixture
def shown(monkeypatch):
    """Boîtes montrées : (texte, texte informatif, titre) ; on y répond
    « Annuler »."""
    seen = []

    def exec_box(box):
        seen.append((box.text(), box.informativeText(), ui_widgets.title_of(box)))
        return BUTTON.Cancel
    monkeypatch.setattr(QtMessageBox, 'exec', exec_box)
    return seen


def test_elsewhere_a_box_keeps_its_title_and_its_text(app, monkeypatch):
    monkeypatch.setattr(ui_widgets, 'on_macos', lambda: False)
    box = ui_widgets.message_box(None, QtMessageBox.Icon.Warning, 'Fichier introuvable', 'F.xml a disparu.')
    assert (box.text(), box.informativeText()) == ('F.xml a disparu.', '')
    assert ui_widgets.title_of(box) == 'Fichier introuvable'               # windowTitle() hors macOS


def test_on_macos_the_title_becomes_the_main_message(macos):
    box = ui_widgets.message_box(None, QtMessageBox.Icon.Warning, 'Fichier introuvable', 'F.xml a disparu.')
    assert box.windowTitle() == ''                                    # comme sous macOS
    assert (box.text(), box.informativeText()) == ('Fichier introuvable', 'F.xml a disparu.')
    assert ui_widgets.title_of(box) == 'Fichier introuvable'


def test_on_macos_the_texts_stay_plain_text(macos):
    """Le texte cite souvent une donnée (sigle, chemin, réponse d'un
    serveur) : sous le titre aussi, Qt ne doit pas la lire comme du HTML."""
    box = ui_widgets.message_box(None, QtMessageBox.Icon.Warning, 'Titre <b>', '<b>F</b> & <i>x</i>')
    for name in ('qt_msgbox_label', 'qt_msgbox_informativelabel'):
        assert box.findChild(QLabel, name).textFormat() == Qt.TextFormat.PlainText


@pytest.mark.parametrize('kind', ['information', 'warning', 'critical', 'question'])
def test_on_macos_the_ready_made_boxes_show_their_title(macos, shown, kind):
    getattr(ui_widgets.QMessageBox, kind)(None, 'resources.binding.title', 'Texte du message')
    assert shown == [(tr('resources.binding.title'), 'Texte du message', tr('resources.binding.title'))]


def test_on_macos_an_unexpected_error_shows_its_title(macos, shown):
    from varians_synchro import error_report
    error_report.show(ValueError('Ordre de lecture incomplet.'))
    [(text, more, title)] = shown
    assert text == title == tr('error.unexpected.title')
    assert 'Ordre de lecture incomplet.' in more


def test_on_macos_the_question_before_losing_changes_shows_its_title(macos, shown):
    from varians_synchro import ui_main_window
    window = ui_main_window.GuidedWindow()
    try:
        window.project = new_project('Essai')
        window._changes.is_modified = lambda project: True
        assert window._confirm_save_or_discard() is False                # « Annuler »
        assert shown == [(tr('project.unsaved.title'),
                          tr('project.unsaved.question', name='Essai') + '\n\n' + tr('project.unsaved.explanation'),
                          tr('project.unsaved.title'))]
    finally:
        window._suppress_close_confirmation = True
        window.close()
        window.deleteLater()


def _ignore_return(view, event):
    """Qt sous macOS : Entrée ne fait rien dans une liste."""
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        event.ignore()


@pytest.mark.parametrize('key', [Qt.Key.Key_Return, Qt.Key.Key_Enter])
def test_return_opens_the_current_entry_of_a_list(app, monkeypatch, key):
    monkeypatch.setattr(QtListWidget, 'keyPressEvent', _ignore_return)
    entries = ui_widgets.QListWidget()
    entries.addItem('page 1')
    entries.addItem('page 2')
    entries.setCurrentRow(1)
    opened = []
    entries.itemActivated.connect(opened.append)
    QTest.keyClick(entries, key)
    assert opened == [entries.item(1)]
    entries.deleteLater()


def test_return_opens_the_current_entry_of_a_tree(app, monkeypatch):
    monkeypatch.setattr(QtTreeWidget, 'keyPressEvent', _ignore_return)
    tree = ui_widgets.QTreeWidget()
    tree.addTopLevelItems([QTreeWidgetItem(['A']), QTreeWidgetItem(['B'])])
    tree.setCurrentItem(tree.topLevelItem(1))
    opened = []
    tree.itemActivated.connect(lambda item, column: opened.append(item))
    QTest.keyClick(tree, Qt.Key.Key_Return)
    assert opened == [tree.topLevelItem(1)]
    tree.deleteLater()


def test_return_opens_an_entry_once_elsewhere_and_not_without_entry(app):
    """Sous Linux et Windows, Qt active déjà l'élément : une seule fois.
    Sans élément courant, rien."""
    entries = ui_widgets.QListWidget()
    entries.addItem('page 1')
    opened = []
    entries.itemActivated.connect(opened.append)
    QTest.keyClick(entries, Qt.Key.Key_Return)
    assert opened == []
    entries.setCurrentRow(0)
    QTest.keyClick(entries, Qt.Key.Key_Return)
    assert opened == [entries.item(0)]
    entries.deleteLater()


def test_return_in_the_witness_list_opens_its_card(app, monkeypatch):
    from varians_synchro import ui_main_window
    monkeypatch.setattr(QtTreeWidget, 'keyPressEvent', _ignore_return)
    opened = []
    monkeypatch.setattr(ui_main_window.GuidedWindow, 'edit_inventory_item', lambda self, item: opened.append(item))
    window = ui_main_window.GuidedWindow()
    try:
        project = new_project('Essai')
        create_witness(project, 'A')
        window.project = project
        window.refresh()
        window.inventory.setCurrentItem(window.inventory.topLevelItem(0))
        QTest.keyClick(window.inventory, Qt.Key.Key_Return)
        assert opened == [window.inventory.topLevelItem(0)]
    finally:
        window._suppress_close_confirmation = True
        window.close()
        window.deleteLater()
