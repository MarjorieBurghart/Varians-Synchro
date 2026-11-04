"""Spyder / console Qt singleton regression tests, without PySide6."""
from varians_synchro.qt_lifecycle import launch


class FakeWindow:
    def __init__(self):
        self.visible = False
        self.minimized = False
        self.raise_calls = 0
        self.activate_calls = 0
        self.icon = None

    def setWindowIcon(self, icon):
        self.icon = icon

    def show(self):
        self.visible = True

    def isVisible(self):
        return self.visible

    def isMinimized(self):
        return self.minimized

    def showNormal(self):
        self.minimized = False

    def raise_(self):
        self.raise_calls += 1

    def activateWindow(self):
        self.activate_calls += 1


class FakeApplication:
    current = None
    constructions = 0

    def __init__(self, argv):
        assert argv == ['run.py']
        FakeApplication.current = self
        FakeApplication.constructions += 1
        self.exec_calls = 0
        self.icon = None

    def setWindowIcon(self, icon):
        self.icon = icon

    @classmethod
    def instance(cls):
        return cls.current

    def exec(self):
        self.exec_calls += 1
        return 7


def reset():
    FakeApplication.current = None
    FakeApplication.constructions = 0


def test_direct_launch_creates_single_application_and_runs_loop():
    reset()
    result = launch(FakeApplication, FakeWindow, ['run.py'])
    assert result == 7
    assert FakeApplication.constructions == 1
    app = FakeApplication.instance()
    assert app.exec_calls == 1
    assert app._varians_synchro_window.visible


def test_spyder_reuses_qapplication_without_starting_second_event_loop():
    reset()
    app = FakeApplication(['run.py'])
    result = launch(FakeApplication, FakeWindow, ['run.py'])
    assert result == 0
    assert FakeApplication.constructions == 1
    assert app.exec_calls == 0
    assert app._varians_synchro_window.visible


def test_repeated_spyder_run_refocuses_existing_window_preserving_work():
    reset()
    app = FakeApplication(['run.py'])
    launch(FakeApplication, FakeWindow, ['run.py'])
    window = app._varians_synchro_window
    window.minimized = True
    launch(FakeApplication, FakeWindow, ['run.py'])
    assert app._varians_synchro_window is window
    assert window.raise_calls == 1
    assert window.activate_calls == 1
    assert not window.minimized
    assert FakeApplication.constructions == 1


def test_spyder_can_reopen_after_window_was_closed():
    reset()
    app = FakeApplication(['run.py'])
    launch(FakeApplication, FakeWindow, ['run.py'])
    old = app._varians_synchro_window
    old.visible = False
    launch(FakeApplication, FakeWindow, ['run.py'])
    assert app._varians_synchro_window is not old
    assert app._varians_synchro_window.visible
    assert app.exec_calls == 0


def test_deleted_qt_window_reference_is_handled():
    reset()
    app = FakeApplication(['run.py'])

    class DeletedWindow:
        def isVisible(self):
            raise RuntimeError('Internal C++ object already deleted')

    app._varians_synchro_window = DeletedWindow()
    assert launch(FakeApplication, FakeWindow, ['run.py']) == 0
    assert isinstance(app._varians_synchro_window, FakeWindow)


def test_the_icon_is_given_to_the_application_and_its_window():
    """L'icône (créée une fois l'application construite) vaut pour toutes
    ses fenêtres, y compris les boîtes sans parent."""
    reset()
    made = []
    launch(FakeApplication, FakeWindow, ['run.py'], icon=lambda: made.append('logo') or 'logo')
    app = FakeApplication.instance()
    assert made == ['logo']
    assert app.icon == 'logo' and app._varians_synchro_window.icon == 'logo'


def test_a_host_application_keeps_its_own_icon():
    """Lancée dans la console Qt d'un autre programme, seule la fenêtre de
    Varians-Synchro prend le logo."""
    reset()
    host = FakeApplication(['run.py'])
    launch(FakeApplication, FakeWindow, ['run.py'], icon=lambda: 'logo')
    assert host.icon is None
    assert host._varians_synchro_window.icon == 'logo'
