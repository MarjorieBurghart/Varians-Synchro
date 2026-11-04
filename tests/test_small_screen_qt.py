"""Petit écran (red team D3).

La fenêtre de synchronisation demandait au moins 1 600 px environ
(1 700 en allemand, italien, russe) : sur un portable de 1 366 px, ou un
écran de 1 920 px à 125 %, le bord droit sortait de l'écran (◀ ▶, « Texte
HTR », « Recalcul local… », « Revalider… »). Décision : les commandes des
panneaux d'image et la barre de révision passent sur deux rangées ; la
largeur minimale reste sous 1 280 px dans les sept langues. La liaison TEI
et le périmètre sont bornés à l'écran.

Les polices de Windows sont environ 2,2 fois plus larges que celles du
serveur de test Linux (mesuré sur la CI : 1 640 px en français sous Windows
pour 745 ici). La largeur est donc aussi mesurée avec une police agrandie
2,2 fois, et avec la recherche dans le texte TEI (pivot lié) : sous Windows,
la consigne de l'onglet texte, non coupée, et la rangée d'actions du haut
dépassaient 1 280 px.
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


@pytest.fixture
def font_scale(app):
    from PySide6.QtGui import QFont
    previous = QFont(app.font())

    def scale(factor):
        font = QFont(previous)
        font.setPointSizeF(previous.pointSizeF() * factor)
        app.setFont(font)
    yield scale
    app.setFont(previous)


@pytest.mark.parametrize('tei', [False, True], ids=['htr', 'tei'])
@pytest.mark.parametrize('scale', [1.0, 2.2], ids=['linux', 'windows'])
@pytest.mark.parametrize('lang', LANGUAGES)
def test_the_pair_window_fits_a_laptop_screen(app, language, font_scale, monkeypatch, lang, scale, tei):
    from varians_synchro import tei_binding, ui_pair
    from varians_synchro.physical_alignment import create_pair_session
    language(lang)
    font_scale(scale)
    if tei:                                      # pivot lié : recherche dans le texte TEI
        monkeypatch.setattr(tei_binding, 'linked_tei_texts', lambda project, wid: {'ligne': 'texte'})
    project = _project()
    dialog = ui_pair.PairDialog(project, create_pair_session(project, 'A', 'B'))
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
