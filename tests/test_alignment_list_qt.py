"""Étape « 3 · Aligner les témoins » : la liste des paires déjà alignées.

Chaque ligne (« A ↔ B : 2 groupe(s), 2/6 et 2/6 lignes ») est une paire :
un double-clic ou la touche Entrée ouvre sa synchronisation, comme le bouton
« Aligner les témoins » ; un simple clic la choisit dans les deux menus. La
session ouverte est celle de la liste (même sens, aucune session nouvelle)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from varians_synchro import ui_main_window
from varians_synchro.core import create_witness, add_image_source, add_alto_source
from varians_synchro.i18n import set_language, tr
from varians_synchro.imaging import create_pages, bind_alto
from varians_synchro.physical_alignment import create_pair_session, pair_progress
from varians_synchro.project_state import ProjectChangeTracker
from test_stale_links import _xml, setting  # noqa: F401  (fixture)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def project(setting, tmp_path):
    """A ↔ B (2 groupes) et C ↔ A, enregistrée dans ce sens-là."""
    project = setting[0]
    c = create_witness(project, 'C')
    image = tmp_path / 'C.jpg'
    image.write_bytes(b'image')
    add_image_source(c, 'local', str(image))
    add_alto_source(c, _xml(tmp_path / 'C.xml', [f'gamma {i}' for i in range(1, 5)]))
    create_pages(c)
    bind_alto(c, c['pages'][0]['id'], c['alto_sources'][0]['id'], 0)
    create_pair_session(project, 'C', 'A')
    return project


@pytest.fixture
def opened(monkeypatch):
    """Fenêtres de synchronisation ouvertes (sans les afficher)."""
    calls = []

    class FakePairDialog:
        def __init__(self, project, session, parent):
            calls.append(session)

    monkeypatch.setattr(ui_main_window, 'PairDialog', FakePairDialog)
    monkeypatch.setattr(ui_main_window, '_run_modal', lambda dialog: 0)
    return calls


@pytest.fixture
def window(app, project):
    window = ui_main_window.GuidedWindow()
    window.project = project
    window._changes = ProjectChangeTracker(project)
    window.refresh()
    window.nav.setCurrentRow(2)               # « 3 · Aligner les témoins », affichée :
    window.show()                             # Qt ne transmet pas un double-clic
    QTest.qWaitForWindowExposed(window)       # à une liste cachée
    yield window
    QCoreApplication.processEvents()
    window._suppress_close_confirmation = True
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def _row(window, text):
    pairs = window.align_status
    return next(pairs.item(i) for i in range(pairs.count()) if pairs.item(i).text().startswith(text))


def _click(window, item, double=False):
    """Un clic ; un double-clic est un clic suivi du double-clic lui-même
    (Qt n'émet le double-clic que si l'appui a eu lieu sur la même ligne)."""
    pairs = window.align_status
    args = (pairs.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            pairs.visualItemRect(item).center())
    QTest.mouseClick(*args)
    if double:
        QTest.mouseDClick(*args)


def _menus(window):
    return window.reference_box.currentData(), window.target_box.currentData()


def test_each_saved_pair_is_a_line(window, project):
    pairs = window.align_status
    assert [pairs.item(i).text() for i in range(pairs.count())] == [
        'A ↔ B : 2 groupe(s), 2/6 et 2/6 lignes',
        tr('ui.alignment.pair_status', reference='C', target='A', groups=0,
           **{key: pair_progress(project, project['pair_sessions'][1])[key]
              for key in ('reference_covered', 'reference_total', 'target_covered', 'target_total')})]


def test_a_double_click_opens_the_pair_of_the_line(window, project, opened):
    sessions = list(project['pair_sessions'])
    refreshed = []
    window.refresh = lambda: refreshed.append(True)
    _click(window, _row(window, 'C ↔ A'), double=True)
    assert len(opened) == 1 and opened[0] is sessions[1]       # la session de la ligne
    assert project['pair_sessions'] == sessions                # aucune session nouvelle
    assert refreshed                                           # état relu en sortie


def test_enter_opens_the_current_pair(window, project, opened):
    window.align_status.setCurrentItem(_row(window, 'A ↔ B'))
    QTest.keyClick(window.align_status, Qt.Key.Key_Return)
    QTest.keyClick(window.align_status, Qt.Key.Key_Enter)      # pavé numérique
    assert opened == [project['pair_sessions'][0]] * 2


def test_a_single_click_sets_the_two_menus_and_opens_nothing(window, opened):
    assert _menus(window) == ('A', 'B')
    _click(window, _row(window, 'C ↔ A'))
    assert _menus(window) == ('C', 'A')                         # sens de la session
    assert opened == []
    _click(window, _row(window, 'A ↔ B'))
    assert _menus(window) == ('A', 'B')


def test_refreshing_the_list_leaves_the_menus_alone(window):
    _click(window, _row(window, 'C ↔ A'))
    window.reference_box.setCurrentIndex(window.reference_box.findData('B'))
    window.refresh()
    assert _menus(window) == ('B', 'A')
    assert window.align_status.currentItem().text().startswith('C ↔ A')   # ligne gardée


def test_a_line_in_error_opens_nothing(window, project, opened, monkeypatch):
    warnings = []
    monkeypatch.setattr(ui_main_window.QMessageBox, 'warning',
                        staticmethod(lambda *args: warnings.append(args)))
    project['witnesses'] = [w for w in project['witnesses'] if w['id'] != 'C']
    window.refresh()
    broken = window.align_status.item(1)
    assert broken.text() == 'Un témoin de la session est absent du projet'
    before = _menus(window)
    _click(window, broken)
    _click(window, broken, double=True)
    assert opened == [] and warnings == [] and _menus(window) == before


def test_without_any_pair_the_line_opens_nothing(window, project, opened):
    project['pair_sessions'] = []
    window.refresh()
    assert window.align_status.count() == 1
    only = window.align_status.item(0)
    assert only.text() == tr('resources.project.no_alignment')
    _click(window, only, double=True)
    assert opened == []


def test_the_list_says_how_to_open_a_pair(window):
    tip = tr('ui.alignment.list.tip')
    assert tip != 'ui.alignment.list.tip'
    assert window.align_status.toolTip() == tip
    assert tip in [label.text() for label in window.findChildren(QLabel)]


@pytest.fixture
def english():
    set_language('en')
    yield
    set_language('fr')


def test_the_lines_are_translated(english, window):
    assert window.align_status.item(0).text() == 'A ↔ B: 2 group(s), 2/6 and 2/6 lines'
    assert window.align_status.toolTip() == tr('ui.alignment.list.tip')
    assert 'Double-click' in window.align_status.toolTip()


def test_a_refused_pair_is_explained_in_the_chosen_language(english, app, project, monkeypatch):
    """« Aligner les témoins » sur un témoin sans page ALTO : le refus est
    traduit (il ne l'était pas : texte français écrit dans le code)."""
    from varians_synchro.core import create_witness
    shown = []
    monkeypatch.setattr(ui_main_window.QMessageBox, 'warning',
                        staticmethod(lambda parent, title, text, *a: shown.append(text)))
    create_witness(project, 'D')                        # sans images ni ALTO
    window = ui_main_window.GuidedWindow()
    window.project = project
    window._changes = ProjectChangeTracker(project)
    window.refresh()
    window._open_pair('A', 'D')
    assert shown == ['Link ALTO pages to both witnesses before aligning them']
    project['witnesses'] = [w for w in project['witnesses'] if w['id'] != 'C']
    window.refresh()                                    # C ↔ A : témoin absent
    assert window.align_status.item(1).text() == 'A witness of this alignment is missing from the project'
    window._suppress_close_confirmation = True
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
