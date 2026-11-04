"""Widgets Qt qui traduisent leurs textes, ouverture modale d'une fenêtre et
appels différés liés à une fenêtre.

Les fenêtres de l'interface utilisent ces classes à la place de celles de
PySide6 : un texte passé à ``QLabel``, ``setWindowTitle`` ou
``QMessageBox.warning`` est une clé de traduction (ou un texte français
connu des catalogues) et s'affiche dans la langue choisie."""
from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QComboBox as QtComboBox, QDialog as QtDialog,
                               QFileDialog as QtFileDialog, QInputDialog as QtInputDialog,
                               QLabel as QtLabel, QListWidget as QtListWidget,
                               QMainWindow as QtMainWindow, QMessageBox as QtMessageBox,
                               QPushButton as QtButton, QTabWidget as QtTabWidget,
                               QTreeWidget as QtTreeWidget)

from .i18n import tr


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


def call_soon(owner, callback):
    """Call ``callback`` once control returns to the event loop, unless
    ``owner`` (a QObject) has been destroyed by then.

    ``QTimer.singleShot(0, owner.method)`` still called the method on a
    deleted widget (a window closed right after asking for its thumbnails):
    "Internal C++ object already deleted". The timer here is a child of
    ``owner`` and dies with it. ``QTimer.singleShot(0, owner, callback)``
    would do the same but does not exist in PySide6 6.6."""
    timer = QTimer(owner)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.timeout.connect(timer.deleteLater)
    timer.start(0)


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
