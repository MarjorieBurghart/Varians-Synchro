"""Le journal des erreurs dans l'interface : ouvert au démarrage, cité par
la boîte « Action impossible » (erreur imprévue), qui ouvre son dossier,
comme le bouton « Journal des erreurs » de la fenêtre d'aide (pour joindre
le fichier à un signalement)."""
import os
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMessageBox

from varians_synchro import error_log, error_log_ui, error_report, ui_help
from varians_synchro.core import VERSION
from varians_synchro.i18n import set_language, tr


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def journal_folder(tmp_path, monkeypatch):
    """Dossier du journal propre au test ; le journal est refermé à la fin,
    les crochets d'exceptions rendus."""
    folder = tmp_path / 'journal'
    monkeypatch.setenv(error_log.ENVIRONMENT, str(folder))
    monkeypatch.setattr(sys, 'excepthook', lambda *args: None)          # console : sans bruit
    error_log.uninstall()
    yield folder
    error_log.uninstall()


@pytest.fixture
def opened(monkeypatch):
    """Dossiers que le logiciel demande au système d'ouvrir."""
    folders = []
    monkeypatch.setattr(error_log_ui.QDesktopServices, 'openUrl',
                        lambda url: folders.append(Path(url.toLocalFile())) or True)   # « / » sous Windows aussi
    return folders


@pytest.fixture
def boxes(monkeypatch):
    """Boîtes montrées : (liste de {titre, textes, boutons}, réponse). Mettre
    dans la réponse ``click`` : le texte du bouton sur lequel cliquer."""
    from varians_synchro.ui_widgets import title_of
    seen, answer = [], {}

    def exec_box(box):
        seen.append({'title': title_of(box), 'text': box.text() + '\n' + box.informativeText(),
                     'buttons': [button.text() for button in box.buttons()]})
        for button in box.buttons():
            if button.text() == answer.get('click'):
                button.click()
        return 0
    monkeypatch.setattr(QMessageBox, 'exec', exec_box)
    return seen, answer


def test_the_journal_opens_at_startup_with_the_versions(app, journal_folder):
    path = error_log_ui.install_for_application()
    assert path == journal_folder / error_log.FILE_NAME
    header = path.read_text(encoding='utf-8')
    assert f'Varians-Synchro {VERSION}' in header and f'Qt {QtCore.qVersion()}' in header


def test_the_application_opens_the_journal_and_the_unexpected_error_is_written_and_shown(
        app, journal_folder, boxes, monkeypatch):
    import varians_synchro.gui as gui
    monkeypatch.setattr(gui, 'launch', lambda *args: 0)
    assert gui.main() == 0
    assert error_log.installed()
    seen, _answer = boxes
    sys.excepthook(ValueError, ValueError('inattendue'), None)
    assert 'ValueError: inattendue' in (journal_folder / error_log.FILE_NAME).read_text(encoding='utf-8')
    assert len(seen) == 1 and seen[0]['title'] == tr('error.unexpected.title')


def test_the_unexpected_error_says_where_the_journal_is_and_opens_its_folder(app, journal_folder, boxes, opened):
    path = error_log_ui.install_for_application()
    seen, answer = boxes
    answer['click'] = tr('error_log.title')
    error_report.show(ValueError('inattendue'))
    [box] = seen
    assert tr('error_log.noted', file=str(path)) in box['text']
    assert tr('error_log.title') in box['buttons']
    assert opened == [journal_folder]


def test_without_journal_the_unexpected_error_does_not_mention_it(app, journal_folder, boxes, opened):
    seen, _answer = boxes
    error_report.show(ValueError('inattendue'))
    [box] = seen
    assert tr('error_log.title') not in box['buttons']
    assert tr('error.unexpected.text', error='inattendue') in box['text']
    assert tr('error.unexpected.console') in box['text']


def test_the_help_window_opens_the_folder_of_the_journal(app, journal_folder, opened):
    dialog = ui_help.HelpDialog()
    try:
        button = dialog.error_log_button
        assert button.text() == tr('error_log.title') and button.toolTip() == tr('error_log.open.tip')
        assert not button.autoDefault()                       # Entrée ne l'active pas
        button.click()
        assert opened == [journal_folder]
        assert journal_folder.is_dir()                        # créé s'il manquait
    finally:
        dialog.deleteLater()


def test_a_folder_that_cannot_be_made_is_said(app, journal_folder, opened, boxes, monkeypatch, tmp_path):
    blocked = tmp_path / 'fichier'
    blocked.write_text('pas un dossier', encoding='utf-8')
    monkeypatch.setenv(error_log.ENVIRONMENT, str(blocked / 'journal'))
    seen, _answer = boxes
    assert error_log_ui.open_log_folder(None) is False
    [box] = seen
    assert box['title'] == tr('error_log.title')
    assert tr('error_log.unavailable', folder=str(blocked / 'journal')) in box['text']
    assert opened == []


def test_the_texts_follow_the_language(app, journal_folder):
    set_language('en')
    try:
        dialog = ui_help.HelpDialog()
        assert dialog.error_log_button.text() == tr('error_log.title') == 'Error Log'
        dialog.deleteLater()
    finally:
        set_language('fr')
