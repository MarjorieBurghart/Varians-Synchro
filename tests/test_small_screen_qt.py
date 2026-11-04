"""Petit écran (red team D3).

La fenêtre de synchronisation demandait au moins 1 600 px environ
(1 700 en allemand, italien, russe) : sur un portable de 1 366 px, ou un
écran de 1 920 px à 125 %, le bord droit sortait de l'écran (◀ ▶, « Texte
HTR », « Recalcul local… », « Revalider… »). Décision : les commandes des
panneaux d'image et la barre de révision passent sur deux rangées ; la
largeur minimale reste sous 1 280 px dans les sept langues. La liaison TEI
et le périmètre sont bornés à l'écran.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from varians_synchro.core import create_witness, new_project
from varians_synchro.i18n import get_language, set_language

LANGUAGES = ['fr', 'en', 'de', 'cs', 'it', 'ru', 'ja']


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def language():
    previous = get_language()
    yield set_language
    set_language(previous)


def _free(*widgets):
    for widget in widgets:
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _project():
    project = new_project('Essai')
    for wid in ('A', 'B'):
        witness = create_witness(project, wid)
        witness['alto_sources'].append({'id': wid, 'path': f'/absent/{wid}.xml', 'pages': [
            {'width': '100', 'height': '100', 'line_count': 1, 'lines': [
                {'alto_id': 'l', 'text': 'x', 'bbox': {'HPOS': '1', 'VPOS': '1', 'WIDTH': '50', 'HEIGHT': '9'}}]}]})
        witness['pages'].append({'id': f'{wid}1', 'label': '1r', 'image_kind': 'local',
                                 'image_path': '/absent/1.jpg', 'alto_binding': {'source_id': wid, 'page_index': 0}})
    return project


@pytest.mark.parametrize('lang', LANGUAGES)
def test_the_pair_window_fits_a_laptop_screen(app, language, lang):
    from varians_synchro.physical_alignment import create_pair_session
    from varians_synchro.ui_pair import PairDialog
    language(lang)
    project = _project()
    dialog = PairDialog(project, create_pair_session(project, 'A', 'B'))
    try:
        assert dialog.minimumSizeHint().width() <= 1280, dialog.minimumSizeHint().width()
    finally:
        _free(dialog)


def test_the_tei_binding_and_scope_windows_stay_within_the_screen(app):
    from varians_synchro.ui_scope import SingleWitnessScopeDialog
    from varians_synchro.ui_tei_binding import TEIPhysicalBindingDialog
    project = _project()
    available = QApplication.primaryScreen().availableGeometry()
    for dialog in (SingleWitnessScopeDialog(project, 'A'), TEIPhysicalBindingDialog(project)):
        try:
            assert dialog.width() <= available.width() and dialog.height() <= available.height()
        finally:
            _free(dialog)
