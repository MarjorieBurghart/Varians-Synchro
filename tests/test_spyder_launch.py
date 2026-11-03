"""Regression tests without installing PySide6 or starting GUI loops."""
from pathlib import Path
from varians_synchro.spyder_launch import (CHILD_MARKER, in_spyder_kernel,
                                          isolated_environment, launch_isolated)


class DummySpyderShell:
    pass


def test_spyder_detection_from_loaded_kernel():
    assert in_spyder_kernel(modules={'spyder_kernels.console.kernel': object()},
                            environ={}, ipython=None)
    assert not in_spyder_kernel(modules={'PySide6': object()},
                                environ={}, ipython=None)


def test_spyder_detection_skipped_in_child():
    assert not in_spyder_kernel(modules={'spyder_kernels': object()},
                                environ={CHILD_MARKER: '1'}, ipython=None)


def test_qt_environment_isolation():
    env = isolated_environment({'QT_PLUGIN_PATH': '/bad',
                                'QT_QPA_PLATFORM_PLUGIN_PATH': '/spyder/plugins',
                                'QT_QPA_FONTDIR': '/spyder/fonts', 'KEEP': 'yes'})
    assert env['KEEP'] == 'yes'
    assert 'QT_PLUGIN_PATH' not in env
    assert 'QT_QPA_PLATFORM_PLUGIN_PATH' not in env
    assert 'QT_QPA_FONTDIR' not in env
    assert env[CHILD_MARKER] == '1'
    assert env['PYTHONFAULTHANDLER'] == '1'


def test_isolated_launcher_uses_same_interpreter_and_creates_log(tmp_path):
    values = {}
    class Process:
        pid = 1234
    def fake_popen(args, **kwargs):
        values['args'], values['kwargs'] = args, kwargs
        return Process()
    run = tmp_path/'run.py'
    run.write_text('print("test")')
    log, pid = launch_isolated(run, popen=fake_popen,
                               executable='/example/python', log_dir=tmp_path/'logs')
    assert pid == 1234
    assert log.exists()
    assert values['args'] == ['/example/python', '-X', 'faulthandler', '-u', str(run)]
    assert values['kwargs']['env'][CHILD_MARKER] == '1'
    assert values['kwargs']['cwd'] == str(tmp_path)
