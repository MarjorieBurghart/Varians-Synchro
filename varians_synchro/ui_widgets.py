"""Widgets Qt qui traduisent leurs textes, ouverture modale d'une fenêtre et
appels différés liés à une fenêtre.

Les fenêtres de l'interface utilisent ces classes à la place de celles de
PySide6 : un texte passé à ``QLabel``, ``setWindowTitle`` ou
``QMessageBox.warning`` est une clé de traduction (ou un texte français
connu des catalogues) et s'affiche dans la langue choisie.

Sous macOS, deux comportements de Qt sont compensés ici : le titre d'une
boîte de message, que Qt n'y affiche pas, en devient le message principal
(``set_alert_texts``) ; Entrée ouvre l'élément choisi d'une liste, ce que Qt
n'y fait pas (``_ReturnOpens``)."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import Qt as QtGuiNamespace, QKeySequence, QShortcut
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


_DETACHED_THREADS = {}


def start_detached(thread, owner, cancel):
    """Start ``thread`` (a QThread without parent) so that it outlives
    ``owner``, its window. A worker that was a child of its window was
    destroyed with it while still running (a download waiting for a slow
    server): « QThread: Destroyed while thread is still running », then the
    whole program stopped and unsaved work was lost.

    Closing ``owner`` sets ``cancel`` (a threading.Event); the thread ends at
    its next check and is freed then. When the application quits, every
    such thread is cancelled and waited for briefly. Callbacks connected to
    the thread must check that their window still exists (``isValid``)."""
    from PySide6.QtCore import QCoreApplication
    import shiboken6
    _DETACHED_THREADS[thread] = cancel

    def owner_destroyed(*_):
        cancel.set()
    owner.destroyed.connect(owner_destroyed)

    def finished():
        _DETACHED_THREADS.pop(thread, None)
        # Nothing left tied to the window: a window still alive when Python
        # stops was destroyed by PySide during the shutdown, and this
        # callback then ran in a half-dismantled interpreter (crash at exit).
        if shiboken6.isValid(owner):
            try:
                owner.destroyed.disconnect(owner_destroyed)
            except (RuntimeError, TypeError):
                pass
        thread.deleteLater()
    thread.finished.connect(finished)
    app = QCoreApplication.instance()
    if app is not None and not getattr(app, '_vsynch_waits_threads', False):
        app._vsynch_waits_threads = True
        app.aboutToQuit.connect(_stop_detached_threads)
    thread.start()


_QT_TRANSLATOR = None


def install_qt_translation(language):
    """Translate Qt's own texts (standard buttons « Yes », « No », « OK »,
    « Cancel »…) into ``language``, with the translations PySide6 ships
    (none for English, Qt's own language). Without it they stayed in
    English whatever the language chosen. Returns True when installed."""
    global _QT_TRANSLATOR
    from PySide6.QtCore import QCoreApplication, QLibraryInfo, QTranslator
    app = QCoreApplication.instance()
    if app is None:
        return False
    if _QT_TRANSLATOR is not None:
        app.removeTranslator(_QT_TRANSLATOR)
        _QT_TRANSLATOR = None
    translator = QTranslator(app)
    if not translator.load(f'qtbase_{language}', QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        translator.deleteLater()
        return False
    app.installTranslator(translator)
    _QT_TRANSLATOR = translator
    return True


def fit_to_screen(widget, width, height):
    """``widget.resize(width, height)``, bounded to the usable area of its
    screen: a window of 1 200 × 850 px did not fit a laptop screen, and its
    bottom buttons were out of reach."""
    from PySide6.QtWidgets import QApplication
    screen = widget.screen() or QApplication.primaryScreen()
    if screen is None:
        widget.resize(width, height)
        return
    area = screen.availableGeometry()
    widget.resize(min(width, int(area.width() * .95)), min(height, int(area.height() * .90)))


def _stop_detached_threads():
    for thread, cancel in list(_DETACHED_THREADS.items()):
        cancel.set()
        thread.wait(5000)


def _text_format(original):
    """Rich text only for a heading of the catalogs (« <h3>… »). Any other
    text, above all a text received (siglum, HTR or TEI text, project name,
    server answer), is shown as it is: Qt's « AutoText » took it for HTML as
    soon as it looked like a tag (``<img src=…>`` loaded local files)."""
    from .i18n import is_catalog_text
    if is_catalog_text(original) and tr(original).lstrip().startswith('<'):
        return Qt.TextFormat.RichText
    return Qt.TextFormat.PlainText


def plain_tip(text):
    """A tooltip showing ``text`` as it is (tooltips are rich text as soon
    as they look like HTML)."""
    return QtGuiNamespace.convertFromPlainText(str(text))


# Raster formats a page image may have. Qt also decodes SVG or PDF, which
# may load other files (local, or network shares under Windows): a received
# « image » in such a format is not shown.
PAGE_IMAGE_FORMATS = frozenset({b'jpeg', b'jpg', b'png', b'tif', b'tiff', b'webp', b'jp2'})


def page_image_reader_ok(reader):
    """True when ``reader`` (a QImageReader) reads a raster page format."""
    return bytes(reader.format()).lower() in PAGE_IMAGE_FORMATS


def decode_page_image(data):
    """QImage of a page image received as bytes; a null QImage when it is
    not in a raster page format."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QImage, QImageReader
    buffer = QBuffer()
    buffer.setData(QByteArray(bytes(data)))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    return reader.read() if page_image_reader_ok(reader) else QImage()


class QLabel(QtLabel):
    """Label translating its text, shown as plain text (``rich=True`` for
    markup written by the program itself)."""
    def __init__(self, *args, rich=False, **kwargs):
        original = args[0] if args and isinstance(args[0], str) else None
        if original is not None:
            args=(tr(original),)+args[1:]
        super().__init__(*args, **kwargs)
        self._rich = rich
        self.setTextFormat(Qt.TextFormat.RichText if rich else _text_format(original))
    def setText(self, text):
        super().setText(tr(text))
        if not self._rich:
            self.setTextFormat(_text_format(text))


class QPushButton(QtButton):
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            args=(tr(args[0]),)+args[1:]
        super().__init__(*args, **kwargs)
    def setToolTip(self, text):
        super().setToolTip(tr(text))


def on_macos() -> bool:
    """Vrai sous macOS."""
    return sys.platform == 'darwin'


class _ReturnOpens:
    """Entrée (ou Entrée du pavé numérique) ouvre l'élément courant d'une
    liste, comme un double-clic (``itemActivated``). Qt le fait sous Linux et
    Windows, pas sous macOS, où il réserve Entrée à l'édition d'un élément :
    la liste le fait donc elle-même, une seule fois, partout. Sans élément
    courant, rien."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self.currentItem()
            if item is not None:
                self._open(item)
            event.accept()
            return
        super().keyPressEvent(event)


class QListWidget(_ReturnOpens, QtListWidget):
    def _open(self, item):
        self.itemActivated.emit(item)

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


class QTreeWidget(_ReturnOpens, QtTreeWidget):
    def _open(self, item):
        self.itemActivated.emit(item, max(self.currentColumn(), 0))

    def setHeaderLabels(self, labels):
        return super().setHeaderLabels([tr(t) for t in labels])


class QDialog(QtDialog):
    """Dialog translating its title, with three behaviours common to all
    windows of the program:

    - Enter never presses a button the user did not choose: Qt pressed the
      first « default » button (in the pages, a page moved up a rank; in the
      synchronisation, a validated group was created). In a list, Enter
      does what a double click does (``itemActivated``).
    - F1 opens the user guide, at ``help_anchor`` (None: no F1).
    - Escape, the close button or « Cancel » (``cancel``) ask before dropping
      a draft with changes (``has_unsaved_draft``), No being the default.
    """
    help_anchor = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help_anchor is not None:
            self._help_shortcut = QShortcut(QKeySequence('F1'), self)
            self._help_shortcut.activated.connect(self.open_help)

    def setWindowTitle(self, title):
        return super().setWindowTitle(tr(title))

    def open_help(self):
        from . import ui_help
        ui_help.open_help(self, self.help_anchor or None)

    def has_unsaved_draft(self):
        return False

    def confirm_discard(self):
        if not self.has_unsaved_draft():
            return True
        return QMessageBox.question(self, tr('common.discard_title'), tr('common.discard_question')) \
            == QtMessageBox.StandardButton.Yes

    def cancel(self):
        """For « Cancel » buttons: reject, after asking if needed."""
        if self.confirm_discard():
            self.reject()

    def keyPressEvent(self, event):
        from PySide6.QtWidgets import QAbstractButton
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not isinstance(self.focusWidget(), QAbstractButton):
            event.accept()
            return
        if key == Qt.Key.Key_Escape and not self.confirm_discard():
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if event.spontaneous() and self.isVisible() and not self.confirm_discard():
            event.ignore()
            return
        super().closeEvent(event)


class QMainWindow(QtMainWindow):
    def setWindowTitle(self, title):
        return super().setWindowTitle(tr(title))


TITLE_PROPERTY = 'synchroTitle'


def title_of(box) -> str:
    """Titre d'une boîte de message, même sous macOS, où Qt ne le retient pas."""
    title = box.property(TITLE_PROPERTY)
    return str(title) if title else box.windowTitle()


def set_alert_texts(box, title, text, more=''):
    """Titre, texte et texte informatif (``more``) d'une boîte de message.

    Sous macOS, Qt n'affiche pas le titre d'une boîte de message, selon les
    règles d'Apple (``setWindowTitle`` n'y fait rien) : le titre devient le
    message principal, et le texte passe dessous, comme une alerte du Mac.
    Ailleurs, rien ne change. Le titre est retenu dans une propriété de la
    boîte (``title_of``)."""
    box.setProperty(TITLE_PROPERTY, title)
    box.setWindowTitle(title)
    if on_macos():
        text, more = title, '\n\n'.join(part for part in (text, more) if part)
    box.setText(text)
    box.setInformativeText(more)


def message_box(parent, icon, title, text, buttons=QtMessageBox.StandardButton.Ok,
                default=QtMessageBox.StandardButton.NoButton):
    """A message box translating its texts and showing them as plain text
    (``text`` often carries a file name, a siglum or a server's answer).
    Under macOS, its title is its main message (``set_alert_texts``)."""
    box = QtMessageBox(icon, '', '', buttons, parent)
    box.setTextFormat(Qt.TextFormat.PlainText)
    set_alert_texts(box, tr(title), tr(text))
    if default != QtMessageBox.StandardButton.NoButton:
        box.setDefaultButton(default)
    return box


def _answer(box):
    try:
        box.exec()
        clicked = box.clickedButton()
        return box.standardButton(clicked) if clicked is not None else QtMessageBox.StandardButton.NoButton
    finally:
        box.deleteLater()


class QMessageBox(QtMessageBox):
    @staticmethod
    def information(parent, title, detail, buttons=QtMessageBox.StandardButton.Ok,
                    default=QtMessageBox.StandardButton.NoButton):
        return _answer(message_box(parent, QtMessageBox.Icon.Information, title, detail, buttons, default))
    @staticmethod
    def warning(parent, title, detail, buttons=QtMessageBox.StandardButton.Ok,
                default=QtMessageBox.StandardButton.NoButton):
        return _answer(message_box(parent, QtMessageBox.Icon.Warning, title, detail, buttons, default))
    @staticmethod
    def critical(parent, title, detail, buttons=QtMessageBox.StandardButton.Ok,
                 default=QtMessageBox.StandardButton.NoButton):
        return _answer(message_box(parent, QtMessageBox.Icon.Critical, title, detail, buttons, default))
    @staticmethod
    def question(parent, title, detail,
                 buttons=QtMessageBox.StandardButton.Yes | QtMessageBox.StandardButton.No,
                 default=QtMessageBox.StandardButton.No):
        # « No » by default: Enter answered Yes to « Remove the witness? ».
        return _answer(message_box(parent, QtMessageBox.Icon.Question, title, detail, buttons, default))


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
