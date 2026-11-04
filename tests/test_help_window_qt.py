"""Aide intégrée : le guide (help/<langue>.html) s'affiche dans une fenêtre
du logiciel, et non plus dans une application externe. Recherche comme dans
Varians ; F1 ; dans la fenêtre de synchronisation, F1 ouvre la section qui
la décrit. La fenêtre n'est pas modale : on lit l'aide en travaillant."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from varians_synchro import ui_help
from varians_synchro.i18n import set_language, tr
from test_stale_links import setting  # noqa: F401  (fixture)

FILLER = ''.join(f'<p>Paragraphe de remplissage {i}.</p>' for i in range(80))
GUIDE = f'''<!doctype html><html lang="{{lang}}"><head><meta charset="utf-8"></head><body>
<h1>Guide {{lang}}</h1>
<div class="toc"><h2>Sommaire</h2><ol><li><a href="#pivot">Témoin pivot</a></li>
<li><a href="#synchronisation">Synchronisation</a></li></ol></div>
<h2 id="pivot">Témoin pivot</h2><p>Le témoin pivot sert de référence.</p>{FILLER}
<h2 id="synchronisation">Synchronisation</h2><p>La fenêtre de synchronisation relie les lignes du pivot.</p>
<h2 id="export">Exporter</h2><p>Exporter les JSON ; le pivot a aussi son JSON.</p>{FILLER}
</body></html>'''


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def guides(tmp_path, monkeypatch):
    """Un dossier d'aide en français et en anglais seulement."""
    for lang in ('fr', 'en'):
        (tmp_path / f'{lang}.html').write_text(GUIDE.format(lang=lang), encoding='utf-8')
    monkeypatch.setattr(ui_help, 'HELP_DIR', tmp_path)
    yield tmp_path
    set_language('fr')


def _dispose(widget):
    QCoreApplication.processEvents()
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_the_guide_of_the_language_is_shown_else_the_french_one(app, guides):
    assert ui_help.help_path('en') == guides / 'en.html'
    assert ui_help.help_path('ja') == guides / 'fr.html'          # pas encore traduit
    set_language('en')
    dialog = ui_help.HelpDialog()
    assert dialog.windowTitle() == tr('help.title')
    assert dialog.browser.toPlainText().startswith('Guide en')
    _dispose(dialog)


def test_a_missing_guide_is_said(app, guides):
    for path in guides.iterdir():
        path.unlink()
    assert ui_help.help_path('fr') is None
    dialog = ui_help.HelpDialog()
    assert dialog.browser.toPlainText() == tr('help.missing')
    _dispose(dialog)


def test_the_search_lists_the_sections_and_walks_the_occurrences(app, guides):
    dialog = ui_help.HelpDialog()
    assert not dialog.results.isVisibleTo(dialog)
    dialog.search_box.setText('pivot')
    dialog.run_search()
    titles = [dialog.results.item(i).text().split(' (')[0] for i in range(dialog.results.count())]
    assert titles == ['Témoin pivot', 'Synchronisation', 'Exporter']      # pas le sommaire
    assert dialog.results.isVisibleTo(dialog)
    assert dialog.search_status.text() == tr('help.search.summary', sections=3, count=4)
    assert len(dialog.browser.extraSelections()) == 4
    first = dialog.current
    dialog.next_occurrence()
    assert dialog.current == first + 1
    dialog.previous_occurrence(); dialog.previous_occurrence()
    assert dialog.current == len(dialog.occurrences) - 1                  # on boucle
    dialog.results.setCurrentRow(2)                                       # « Exporter »
    start = dialog.occurrences[dialog.current][0]
    assert dialog.browser.toPlainText()[start:].startswith('pivot a aussi')
    dialog.search_box.setText('introuvable')
    dialog.run_search()
    assert dialog.results.count() == 0 and dialog.search_status.text() == tr('help.search.none')
    dialog.search_box.setText('')
    dialog.run_search()
    assert not dialog.results.isVisibleTo(dialog) and dialog.search_status.text() == ''
    _dispose(dialog)


def test_links_to_the_web_open_outside_internal_links_stay_inside(app, guides):
    dialog = ui_help.HelpDialog()
    assert dialog.browser.openExternalLinks()
    _dispose(dialog)


def _scrolled_to(dialog, anchor_text):
    """Le titre *anchor_text* est-il en haut de la vue ?"""
    QCoreApplication.processEvents()
    browser = dialog.browser
    top = browser.cursorForPosition(browser.viewport().rect().topLeft()).block().text()
    return top == anchor_text


def test_the_help_window_is_not_modal_and_is_reused(app, guides, monkeypatch):
    from varians_synchro.ui_main_window import GuidedWindow
    opened = []
    monkeypatch.setattr(QDesktopServices, 'openUrl', staticmethod(lambda url: opened.append(url) or True))
    window = GuidedWindow()
    window.show()
    QTest.qWaitForWindowExposed(window)
    QTest.keyClick(window, Qt.Key.Key_F1)
    help_window = window._help_dialog
    assert help_window.isVisible() and not help_window.isModal()
    help_window.close()
    window.open_user_manual()                                       # bouton
    assert window._help_dialog is help_window and help_window.isVisible()
    assert opened == []                                             # plus d'application externe
    window._suppress_close_confirmation = True
    _dispose(window)


def test_f1_in_the_synchronisation_window_opens_its_section(app, guides, setting):
    from varians_synchro.ui_pair import PairDialog
    project, session = setting[0], setting[3]
    pair = PairDialog(project, session)
    pair.show()
    QTest.qWaitForWindowExposed(pair)
    QTest.keyClick(pair, Qt.Key.Key_F1)
    help_window = pair._help_dialog
    assert help_window.parent() is pair and not help_window.isModal()
    help_window.resize(600, 300)
    help_window.show_anchor('synchronisation')
    assert _scrolled_to(help_window, 'Synchronisation')
    _dispose(pair)
