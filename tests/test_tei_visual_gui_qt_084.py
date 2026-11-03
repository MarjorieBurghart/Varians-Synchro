"""Optional PySide6 smoke tests: run on Windows/Spyder with PySide6 installed."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from varians_synchro.guided_ui import make_guided_window
from varians_synchro.resource_workflow import store_tei_reference
from test_tei_binding_083 import fixture, tei

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_one_visual_preview_follows_selected_tei_line(monkeypatch, app, tmp_path):
    project, witness = fixture(tmp_path)
    doc = tei(tmp_path, ''.join(f'<lb edRef="#Mu"/>texte {i}' for i in range(4)))
    store_tei_reference(project, 'Mu', doc)
    parent = make_guided_window()()
    parent.project = project
    observed=[]
    def inspect(dialog):
        assert dialog.preview is not None and dialog.preview['eligible']
        assert dialog.tei_line_list.count() == 4
        assert dialog.line_card.pair['tei_ordinal'] == 1
        assert dialog.tei_line_list.currentItem().data(Qt.ItemDataRole.UserRole) == 1
        assert dialog.findChild(type(dialog.line_card), 'teiVisualSelectedCard') is dialog.line_card
        assert not hasattr(dialog, 'first_card') and not hasattr(dialog, 'last_card')
        assert not hasattr(dialog, 'middle_card')
        initial_serial = dialog.line_card._request_serial
        dialog.tei_line_list.setCurrentRow(1)
        assert dialog.line_card.pair['tei_ordinal'] == 2
        assert 'texte 1' in dialog.line_card.text.text()
        assert dialog.line_card._request_serial == initial_serial + 1
        dialog.select_last()
        assert dialog.line_card.pair['tei_ordinal'] == 4
        dialog.select_ordinal(1)
        assert dialog.line_card.pair['tei_ordinal'] == 1
        dialog.search.setText('texte 3')
        assert dialog.tei_line_list.count() == 1
        # Merely filtering must not launch another IIIF fetch.
        before_filter_selection = dialog.line_card._request_serial
        dialog.tei_line_list.setCurrentRow(0)
        assert dialog.line_card.pair['tei_ordinal'] == 4
        assert dialog.line_card._request_serial == before_filter_selection + 1
        observed.append(True)
        return QDialog.DialogCode.Rejected
    monkeypatch.setattr(QDialog, 'exec', inspect)
    # À la fermeture, la fenêtre demande à juste titre s'il faut enregistrer
    # le projet (jamais enregistré ici) : on répond « Ne pas enregistrer ».
    # Le patch de QDialog.exec ne doit pas recevoir cette question.
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: QMessageBox.StandardButton.Discard)
    try:
        parent.open_tei_binding()
        assert observed
    finally:
        # Allow pending preview completion signals before the window is destroyed.
        app.processEvents()
        parent.close()
