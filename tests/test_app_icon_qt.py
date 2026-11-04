"""L'application démarre avec le logo comme icône (fenêtres, barre des
tâches, Dock)."""
import os
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from varians_synchro import app_icon


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def test_the_icon_has_every_size(app):
    icon = app_icon.application_icon()
    assert not icon.isNull()
    assert sorted(size.width() for size in icon.availableSizes()) == list(app_icon.ICON_SIZES)


def test_the_logo_sits_on_a_white_rounded_tile(app):
    """Option B : pastille blanche, coins transparents."""
    image = QImage(str(app_icon.icon_files()[-1]))
    assert image.width() == 256
    assert image.pixelColor(1, 1).alpha() == 0                       # coin arrondi
    assert image.pixelColor(8, 128) == QColor(255, 255, 255, 255)    # bord de la pastille
    assert image.pixelColor(128, 8) == QColor(255, 255, 255, 255)


def _start(monkeypatch, gui):
    calls = []
    monkeypatch.setattr(sys, 'excepthook', sys.__excepthook__)
    monkeypatch.setattr(gui, 'launch', lambda *args: calls.append(args) or 0)
    assert gui.main() == 0
    return calls[0]


def test_the_application_starts_with_its_icon(app, monkeypatch):
    import varians_synchro.gui as gui
    _qapplication, _window, _argv, icon = _start(monkeypatch, gui)
    icon = icon()
    assert sorted(size.width() for size in icon.availableSizes()) == list(app_icon.ICON_SIZES)


def test_the_taskbar_identity_is_only_taken_by_its_own_application(app, monkeypatch):
    """Dans la console Qt d'un autre programme, l'identité du processus
    reste la sienne."""
    import varians_synchro.gui as gui
    taken = []
    monkeypatch.setattr(gui, 'use_own_taskbar_entry', lambda: taken.append(True))
    _start(monkeypatch, gui)
    assert taken == []                                   # application déjà créée
    monkeypatch.setattr(QApplication, 'instance', staticmethod(lambda: None))
    _start(monkeypatch, gui)
    assert taken == [True]
