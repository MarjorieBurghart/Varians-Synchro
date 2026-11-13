"""Erreur imprévue dans une action de l'interface : un message à l'écran.

Sans ce crochet, une exception levée dans un clic (slot Qt) n'allait qu'à la
console ou au journal de démarrage : pour l'utilisateur, rien ne se passait.
Le crochet garde ce comportement (le détail technique reste dans la console)
et montre en plus un message, traduit quand le texte de l'erreur est connu
des catalogues. Quand le journal des erreurs est ouvert (``error_log``), le
message dit où le détail est noté, et un bouton « Journal des erreurs » ouvre
son dossier.
"""
from __future__ import annotations

import sys

from .i18n import tr

_showing = False


def describe(exc) -> str:
    """Texte de l'erreur pour l'utilisateur : traduit s'il figure dans les
    catalogues, sinon tel quel (ou le nom du type d'erreur s'il est vide)."""
    text = str(exc).strip()
    return tr(text) if text else type(exc).__name__


def show(exc) -> None:
    """Message d'erreur dans la fenêtre active (rien sans application Qt ;
    jamais deux à la fois)."""
    global _showing
    if _showing:
        return
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
    except ImportError:
        return
    app = QApplication.instance()
    if app is None:
        return
    _showing = True
    try:
        # Texte brut : l'erreur cite souvent une donnée reçue (sigle, chemin,
        # réponse d'un serveur), que Qt aurait lue comme du HTML.
        from . import error_log
        from .ui_widgets import message_box
        journal = error_log.journal_path()
        text = tr('error.unexpected.text', error=describe(exc)) + '\n\n' + (
            tr('error_log.noted', file=str(journal)) if journal is not None else tr('error.unexpected.console'))
        parent = app.activeWindow()
        box = message_box(parent, QMessageBox.Icon.Warning, tr('error.unexpected.title'), text)
        journal_button = (box.addButton(tr('error_log.title'), QMessageBox.ButtonRole.ActionRole)
                          if journal is not None else None)
        try:
            box.exec()
            if journal_button is not None and box.clickedButton() is journal_button:
                from .error_log_ui import open_log_folder
                open_log_folder(parent)
        finally:
            box.deleteLater()
    finally:
        _showing = False


def install() -> None:
    """Pose le crochet sur ``sys.excepthook`` (une seule fois) : l'ancien
    reste appelé, puis le message est montré."""
    if getattr(sys.excepthook, 'varians_synchro_error_report', False):
        return
    previous = sys.excepthook

    def hook(exc_type, exc, tb):
        previous(exc_type, exc, tb)
        if not issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            show(exc)
    hook.varians_synchro_error_report = True
    sys.excepthook = hook
