"""Fenêtres de propositions de la synchronisation d'une paire de témoins.

Quatre fenêtres : propositions HTR–HTR, progression textuelle, interpolation
géométrique, lignes résiduelles. Ces tests décrivent leur comportement (ce
qu'elles montrent, ce que « Enregistrer », « Annuler », une sélection vide
et la confirmation font au projet), pour qu'il reste le même quand leur
code est mis en commun.
"""
import copy
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QDialog as QtDialog, QListWidget, QPushButton

from varians_synchro import ui_widgets
from varians_synchro.core import new_project, create_witness
from varians_synchro.i18n import tr
from varians_synchro.interpolation import suggest_between_anchors
from varians_synchro.physical_alignment import (add_pair_link, apply_pair_proposals,
    create_pair_session, physical_lines, replace_revisable_pair_proposals,
    suggest_htr_pair_alignment)
from varians_synchro.residual_alignment import apply_residual_extensions, suggest_residual_extensions
from varians_synchro.textual_progress import suggest_textual_progress
from test_full_column_interpolation import witness_page
from test_physical_alignment import add_page
from test_reading_stream import add_test_page

YES = ui_widgets.QtMessageBox.StandardButton.Yes
NO = ui_widgets.QtMessageBox.StandardButton.No


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


# -- Projets d'essai : chacun donne des propositions à sa fenêtre ----------

def htr_project():
    project = new_project('HTR')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    add_page(a, ['Beatus Germanus in hac vita', 'multis miraculis claruit', 'et populum docuit'])
    add_page(b, ['Beatus Germanus in', 'hac vita multis miraculis', 'claruit et populum docuit'])
    return project, create_pair_session(project, 'A', 'B')


def progress_project(*, machine_link=False):
    project = new_project('Quantité')
    a, b = create_witness(project, 'Mu'), create_witness(project, 'F')
    add_test_page(a, '1v', 'a1', [('c1', ['start', 'x' * 90, 'x' * 20, 'x' * 90, 'x' * 60, 'end'])])
    add_test_page(b, '4v', 'b1', [('c1', ['start'] + ['y' * n for n in (32, 35, 28, 34, 33, 31, 36, 31)]
                                   + ['end'])])
    session = create_pair_session(project, 'Mu', 'F')
    al, bl = physical_lines(a), physical_lines(b)
    add_pair_link(project, session, [al[0]['id']], [bl[0]['id']])
    add_pair_link(project, session, [al[-1]['id']], [bl[-1]['id']])
    if machine_link:          # un groupe automatique que le calcul remplacerait
        add_pair_link(project, session, [al[1]['id']], [bl[1]['id']],
                      state='uncertain', origin='automatic-htr-htr')
    return project, session


def geometry_project(*, machine_link=False):
    project = new_project('Géométrie')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    la, lb = witness_page(a, 12), witness_page(b, 14)
    session = create_pair_session(project, 'A', 'B')
    add_pair_link(project, session, [la['A-c0-l0']['id']], [lb['B-c0-l0']['id']])
    add_pair_link(project, session, [la['A-c0-l11']['id']], [lb['B-c0-l13']['id']])
    if machine_link:
        add_pair_link(project, session, [la['A-c0-l1']['id']], [lb['B-c0-l1']['id']],
                      state='uncertain', origin='interpolated-geometry')
    return project, session


def residual_project():
    project = new_project('Résiduelles')
    a, b = create_witness(project, 'A'), create_witness(project, 'B')
    aa, bb = witness_page(a, 17), witness_page(b, 17)
    session = create_pair_session(project, 'A', 'B')
    for left, right in (([3], [1, 2, 3]), ([8], [4, 5, 6, 7, 8])):
        add_pair_link(project, session, [aa[f'A-c0-l{i}']['id'] for i in left],
                      [bb[f'B-c0-l{i}']['id'] for i in right],
                      origin='interpolated-geometry', state='uncertain')
    return project, session


# -- Ce que fait le moteur seul, pour comparer -----------------------------

def _session_of(project, session):
    return next(s for s in project['pair_sessions'] if s['id'] == session['id'])


def expected_after_saving_all(window, project, session):
    project = copy.deepcopy(project)
    session = _session_of(project, session)
    if window == 'automatic':
        apply_pair_proposals(project, session, suggest_htr_pair_alignment(project, session)['proposals'])
    elif window == 'interpolate':
        replace_revisable_pair_proposals(project, session,
                                         suggest_textual_progress(project, session)['proposals'])
    elif window == 'interpolate_geometry':
        replace_revisable_pair_proposals(project, session, suggest_between_anchors(
            project, session, regenerate_automatic=True)['proposals'])
    else:
        apply_residual_extensions(project, session,
                                  suggest_residual_extensions(project, session)['proposals'])
    return links(session)


def links(session):
    return sorted((tuple(sorted(link['reference_ids'])), tuple(sorted(link['target_ids'])),
                   link['state'], link.get('origin'), link.get('kind'))
                  for link in session['links'])


# -- Ouvrir une fenêtre de propositions et agir dedans ---------------------

class Run:
    """Une ouverture de fenêtre : ce qu'elle montrait, les messages."""
    def __init__(self):
        self.title = None
        self.items = []
        self.selected = []
        self.buttons = []
        self.messages = []          # (type, titre, texte)
        self.closed_by = None       # 'accept', 'reject' ou None (restée ouverte)


def open_window(monkeypatch, project, session, window, action, *, answer=NO):
    """Ouvre la fenêtre ``window`` de PairDialog, puis : ``save`` (tout
    sélectionner, enregistrer), ``keep`` (enregistrer la sélection
    initiale), ``none`` (rien de sélectionné, enregistrer) ou ``cancel``."""
    from varians_synchro.ui_pair import PairDialog
    run = Run()

    def record(kind):
        def show(parent, title, text, *args):
            run.messages.append((kind, title, text))
            return answer if kind == 'question' else None
        return staticmethod(show)
    for kind in ('information', 'warning', 'question'):
        monkeypatch.setattr(ui_widgets.QMessageBox, kind, record(kind))

    def exec_(dialog):
        options = dialog.findChild(QListWidget)
        run.title = dialog.windowTitle()
        run.items = [options.item(i).text() for i in range(options.count())]
        run.selected = sorted(index.row() for index in options.selectedIndexes())
        buttons = dialog.findChildren(QPushButton)
        run.buttons = [button.text() for button in buttons]
        dialog.accepted.connect(lambda: setattr(run, 'closed_by', 'accept'))
        dialog.rejected.connect(lambda: setattr(run, 'closed_by', 'reject'))
        if action == 'save':
            options.selectAll()
        elif action == 'none':
            options.clearSelection()
        target = buttons[-1] if action == 'cancel' else buttons[-2]   # … Enregistrer, Annuler
        target.click()
        return 0
    monkeypatch.setattr(QtDialog, 'exec', exec_)
    pair = PairDialog(project, session)
    getattr(pair, window)()
    QCoreApplication.processEvents()
    pair.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    return run


WINDOWS = {
    # Rien n'est présélectionné : la HTR n'est qu'une aide, on choisit.
    'automatic': dict(build=htr_project, title='Propositions HTR–HTR (facultatives)',
                      buttons=['common.select_all', 'common.select_none', 'progress.save',
                               'common.cancel'], preselected=False,
                      saved='Propositions enregistrées'),
    'interpolate': dict(build=progress_project, title='progress.title',
                        buttons=['common.select_all', 'common.select_none', 'progress.save',
                                 'common.cancel'], preselected=True, saved='progress.title'),
    'interpolate_geometry': dict(build=geometry_project,
                                 title='Compléter les lignes entre ancrages — prévisualisation',
                                 buttons=['Tout sélectionner', 'Ne rien sélectionner',
                                          'Enregistrer les propositions sélectionnées', 'Annuler'],
                                 preselected=True, saved='Interpolation enregistrée'),
    'residual': dict(build=residual_project, title='alignment.residual.title',
                     buttons=['common.select_all', 'common.select_none', 'alignment.residual.save',
                              'common.cancel'], preselected=True, saved='alignment.residual.title'),
}


@pytest.mark.parametrize('window', WINDOWS)
def test_the_window_shows_the_proposals_of_its_engine(app, monkeypatch, window):
    spec = WINDOWS[window]
    project, session = spec['build']()
    run = open_window(monkeypatch, project, session, window, 'cancel')
    assert run.title == tr(spec['title'])
    assert run.buttons == [tr(text) for text in spec['buttons']]
    assert run.items
    assert run.selected == (list(range(len(run.items))) if spec['preselected'] else [])


@pytest.mark.parametrize('window', WINDOWS)
def test_saving_everything_records_what_the_engine_proposes(app, monkeypatch, window):
    spec = WINDOWS[window]
    project, session = spec['build']()
    expected = expected_after_saving_all(window, project, session)
    assert expected != links(session)
    run = open_window(monkeypatch, project, session, window, 'save', answer=YES)
    assert links(session) == expected
    assert run.closed_by == 'accept'
    assert run.messages[-1][:2] == ('information', tr(spec['saved']))


@pytest.mark.parametrize('window', WINDOWS)
def test_cancel_changes_nothing(app, monkeypatch, window):
    project, session = WINDOWS[window]['build']()
    before = copy.deepcopy(project)
    run = open_window(monkeypatch, project, session, window, 'cancel')
    assert project == before
    assert run.closed_by == 'reject' and run.messages == []


@pytest.mark.parametrize('window, title', [
    ('automatic', 'Propositions HTR–HTR (facultatives)'),
    ('interpolate', 'progress.title'),
    ('interpolate_geometry', 'Sélection vide'),
    ('residual', 'alignment.residual.title'),
])
def test_an_empty_selection_is_refused_and_the_window_stays_open(app, monkeypatch, window, title):
    project, session = WINDOWS[window]['build']()
    before = copy.deepcopy(project)
    run = open_window(monkeypatch, project, session, window, 'none')
    assert project == before
    assert run.closed_by is None
    assert run.messages == [('information', tr(title), run.messages[0][2])]


def test_the_htr_window_does_not_save_what_was_not_chosen(app, monkeypatch):
    """Le bouton disait « Conserver la sélection » alors que rien n'était
    sélectionné ; le cliquer enregistrait « 0 groupe » et fermait la fenêtre."""
    project, session = htr_project()
    before = copy.deepcopy(project)
    run = open_window(monkeypatch, project, session, 'automatic', 'keep')
    assert project == before and run.closed_by is None
    assert run.messages == [('information', tr('Propositions HTR–HTR (facultatives)'),
                             tr('progress.empty'))]


@pytest.mark.parametrize('window, build, title', [
    ('interpolate', progress_project, 'progress.confirm.title'),
    ('interpolate_geometry', geometry_project, 'alignment.recalculate.confirm.title'),
])
def test_replacing_machine_groups_asks_first(app, monkeypatch, window, build, title):
    project, session = build(machine_link=True)
    before = copy.deepcopy(project)
    run = open_window(monkeypatch, project, session, window, 'save', answer=NO)
    assert project == before and run.closed_by is None
    assert [m[:2] for m in run.messages] == [('question', tr(title))]
    project, session = build(machine_link=True)
    expected = expected_after_saving_all(window, project, session)
    run = open_window(monkeypatch, project, session, window, 'save', answer=YES)
    assert links(session) == expected and run.closed_by == 'accept'


def test_the_window_does_not_ask_when_no_machine_group_is_replaced(app, monkeypatch):
    project, session = progress_project()
    run = open_window(monkeypatch, project, session, 'interpolate', 'save', answer=NO)
    assert [m[0] for m in run.messages] == ['information'] and run.closed_by == 'accept'


def test_residual_extensions_are_always_confirmed(app, monkeypatch):
    project, session = residual_project()
    before = copy.deepcopy(project)
    run = open_window(monkeypatch, project, session, 'residual', 'save', answer=NO)
    assert project == before and run.closed_by is None
    assert [m[:2] for m in run.messages] == [('question', tr('alignment.residual.confirm.title'))]
