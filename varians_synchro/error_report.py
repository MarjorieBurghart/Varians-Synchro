"""Erreur imprévue dans une action de l'interface : un message à l'écran.

Sans ce crochet, une exception levée dans un clic (slot Qt) n'allait qu'à la
console ou au journal de démarrage : pour l'utilisateur, rien ne se passait.
Le crochet garde ce comportement (le détail technique reste dans la console)
et montre en plus un message, traduit quand le texte de l'erreur est connu
des catalogues.
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
        from .ui_widgets import _answer, message_box
        _answer(message_box(app.activeWindow(), QMessageBox.Icon.Warning, tr('error.unexpected.title'),
                            tr('error.unexpected.text', error=describe(exc))))
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
