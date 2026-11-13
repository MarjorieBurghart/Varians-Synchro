"""Erreur imprévue dans une action de l'interface : un message à l'écran.

Sans crochet, une exception levée dans un clic (slot Qt) n'allait qu'à la
console ou au journal : pour l'utilisateur, rien ne se passait."""
import os
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from varians_synchro import error_report
from varians_synchro.i18n import tr
from varians_synchro.ui_widgets import title_of


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_an_error_in_a_click_is_shown(app, monkeypatch):
    shown = []
    monkeypatch.setattr(sys, 'excepthook', lambda *args: None)     # console : sans bruit
    # La boîte est construite en texte brut (red team B1), puis montrée.
    # Titre et textes lus comme sous tous les systèmes (sous macOS, le titre
    # est le message principal : ui_widgets.set_alert_texts).
    monkeypatch.setattr(QMessageBox, 'exec', lambda box: shown.append(
        (title_of(box), box.text() + '\n' + box.informativeText())) or 0)
    error_report.install()
    button = QPushButton()

    def failing():
        raise ValueError('Ordre de lecture des lignes incomplet, dupliqué ou périmé.')
    button.clicked.connect(failing)
    button.click()
    app.processEvents()
    assert len(shown) == 1
    title, text = shown[0]
    assert title == tr('error.unexpected.title')
    assert 'Ordre de lecture des lignes incomplet' in text


def test_the_application_installs_it_at_start(app, monkeypatch):
    import varians_synchro.gui as gui
    monkeypatch.setattr(sys, 'excepthook', sys.__excepthook__)
    monkeypatch.setattr(gui, 'launch', lambda *args: 0)
    assert gui.main() == 0
    assert getattr(sys.excepthook, 'varians_synchro_error_report', False)
