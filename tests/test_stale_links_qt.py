"""Interface des correspondances périmées : avertissement avant de donner un
autre XML à une page, marque dans la liste des groupes, revalidation."""
import os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication

from varians_synchro.guided_ui import make_guided_window
from varians_synchro.i18n import tr
from varians_synchro.physical_alignment import stale_link_ids
from varians_synchro.reading_stream import rebind_page
from test_stale_links import setting  # noqa: F401  (fixture)


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def _nested(method, name):
    return next(cell.cell_contents for cell in method.__closure__
                if getattr(cell.cell_contents, '__name__', '') == name)


def _closure(method):
    return {getattr(cell.cell_contents, '__name__', None): cell.cell_contents
            for cell in method.__closure__}


def _assign(app, monkeypatch, project, witness, answer):
    window_type = make_guided_window(lambda: None)
    pages_class = _nested(window_type.manage_pages, 'PagesDialog')
    names = _closure(pages_class.assign)
    asked = []
    target = witness['alto_sources'][-1]

    def choose(parent, title, label, labels, *args, **kwargs):
        return next(text for text in labels if Path(target['path']).name in text), True
    monkeypatch.setattr(names['QInputDialog'], 'getItem', staticmethod(choose))
    monkeypatch.setattr(names['QMessageBox'], 'question',
                        staticmethod(lambda parent, title, text, *a, **k: asked.append(text) or answer))
    dialog = pages_class(project, witness)
    dialog.pages.item(0).setSelected(True)
    dialog.assign()
    dialog.close()
    return asked


def test_a_new_xml_for_a_page_says_which_groups_it_affects(app, monkeypatch, setting):
    from PySide6.QtWidgets import QMessageBox
    project, a, _b, session, _first, _last = setting
    asked = _assign(app, monkeypatch, project, a, QMessageBox.StandardButton.Yes)
    assert asked == [tr('ui.xml.replace_impact', links=2, validated=2)]
    assert a['pages'][0]['alto_binding']['source_id'] == a['alto_sources'][-1]['id']
    assert len(stale_link_ids(project, session)) == 2


def test_declining_keeps_the_page_and_its_groups(app, monkeypatch, setting):
    from PySide6.QtWidgets import QMessageBox
    project, a, _b, session, _first, _last = setting
    before = dict(a['pages'][0]['alto_binding'])
    _assign(app, monkeypatch, project, a, QMessageBox.StandardButton.No)
    assert a['pages'][0]['alto_binding'] == before
    assert stale_link_ids(project, session) == set()


def test_stale_groups_are_marked_and_can_be_revalidated(app, monkeypatch, setting):
    from PySide6.QtWidgets import QMessageBox
    project, a, _b, session, first, _last = setting
    rebind_page(a, a['pages'][0]['id'], a['alto_sources'][-1]['id'], 0)
    window_type = make_guided_window(lambda: None)
    pair_class = _nested(window_type.open_physical_alignment, 'PairDialog')
    names = _closure(pair_class.revalidate_selection)
    monkeypatch.setattr(names['QMessageBox'], 'question',
                        staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    dialog = pair_class(project, session)
    dialog.review_filter.setCurrentIndex(dialog.review_filter.findData('stale'))
    dialog.populate()
    texts = [dialog.links.item(i).text() for i in range(dialog.links.count())]
    assert len(texts) == 2 and all(text.startswith(tr('alignment.stale.tag')) for text in texts)
    for i in range(dialog.links.count()):
        item = dialog.links.item(i)
        item.setSelected(item.data(0x0100) == first['id'])     # Qt.UserRole
    dialog.revalidate_selection()
    assert stale_link_ids(project, session) == {_last['id']}
    assert dialog.links.count() == 1
    dialog.close()
