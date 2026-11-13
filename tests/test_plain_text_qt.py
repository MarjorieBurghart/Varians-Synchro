"""Texte reçu affiché tel quel par Qt (red team B1).

Un sigle, un texte HTR ou TEI, un nom de projet, la réponse d'un serveur
IIIF : Qt les interprétait comme du HTML (format « AutoText ») dès qu'ils
ressemblaient à une balise. Un projet reçu dont le sigle contenait
``<img src=…>`` faisait afficher de faux messages et charger des fichiers
locaux, ou réseau sous Windows. Ce texte s'affiche désormais en texte brut ;
seuls les titres du catalogue restent en texte enrichi.
"""
import html
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_widgets
from varians_synchro.core import create_witness, new_project
from varians_synchro.i18n import tr

HOSTILE = '<img src="/tmp/rouge.png"><b>Faux message</b>'


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _free(*widgets):
    for widget in widgets:
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_a_label_shows_received_text_as_plain_text(app):
    label = ui_widgets.QLabel(HOSTILE)
    other = ui_widgets.QLabel('x')
    other.setText(HOSTILE)
    try:
        assert label.textFormat() == Qt.TextFormat.PlainText and label.text() == HOSTILE
        assert other.textFormat() == Qt.TextFormat.PlainText
    finally:
        _free(label, other)


def test_the_headings_of_the_catalog_stay_rich_text(app):
    label = ui_widgets.QLabel('ui.h3.ressources.du.projet.h3')
    try:
        assert label.textFormat() == Qt.TextFormat.RichText
        assert label.text() == tr('ui.h3.ressources.du.projet.h3')
    finally:
        _free(label)


def test_message_boxes_show_received_text_as_plain_text(app):
    box = ui_widgets.message_box(QApplication.activeWindow(), ui_widgets.QMessageBox.Icon.Warning,
                                 'Titre', HOSTILE)
    try:
        # Sous macOS, le texte est sous le titre (texte informatif, brut aussi).
        assert box.textFormat() == Qt.TextFormat.PlainText and HOSTILE in (box.text(), box.informativeText())
    finally:
        _free(box)


def test_a_received_tooltip_is_shown_as_it_is(app):
    tip = ui_widgets.plain_tip(HOSTILE + '\nligne 2')
    from PySide6.QtGui import QTextDocument
    document = QTextDocument()
    document.setHtml(tip)
    assert document.toPlainText() == HOSTILE + '\nligne 2'


def test_the_viewer_shows_a_siglum_and_server_errors_as_text(app):
    from PySide6.QtWidgets import QLabel
    from varians_synchro.viewer import LineImagePanel
    witness = create_witness(new_project('Essai'), HOSTILE)
    panel = LineImagePanel(witness)
    try:
        labels = [label.text() for label in panel.findChildren(QLabel)]
        assert f'<b>{html.escape(HOSTILE)}</b>' in labels
        assert panel.status.textFormat() == Qt.TextFormat.PlainText
    finally:
        _free(panel)


def test_the_unexpected_error_box_shows_the_error_as_plain_text(app, monkeypatch):
    """L'erreur imprévue cite souvent une donnée reçue (sigle, chemin)."""
    from PySide6.QtWidgets import QMessageBox as QtBox
    from varians_synchro import error_report
    seen = []
    monkeypatch.setattr(QtBox, 'warning', staticmethod(lambda *a, **k: seen.append('AutoText')))
    monkeypatch.setattr(QtBox, 'exec',
                        lambda self: seen.append((self.textFormat(), self.text() + self.informativeText())) or 0)
    error_report.show(KeyError(HOSTILE))
    assert len(seen) == 1 and seen[0][0] == Qt.TextFormat.PlainText and HOSTILE in seen[0][1]
