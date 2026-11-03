"""Safe Spyder entrypoint: start the Qt GUI in a separate Python process.

No Qt imports are permitted here. A single Spyder kernel may load a different
Qt binding or platform plugin; creating Qt widgets in that same native process
can terminate the kernel without raising a Python exception.
"""
from __future__ import annotations

import builtins
import datetime as _dt
import os
from pathlib import Path
import subprocess
import sys
import tempfile

CHILD_MARKER = "VARIANS_SYNCHRO_ISOLATED"


def in_spyder_kernel(modules=None, environ=None, ipython=None):
    modules = sys.modules if modules is None else modules
    environ = os.environ if environ is None else environ
    if environ.get(CHILD_MARKER) == "1":
        return False
    if environ.get("VARIANS_SYNCHRO_IN_PROCESS") == "1":
        return False
    if any(n == 'spyder_kernels' or n.startswith('spyder_kernels.') for n in modules):
        return True
    if environ.get('SPYDER_KERNEL') == '1':
        return True
    if ipython is None:
        get_ipython = getattr(builtins, 'get_ipython', None)
        if callable(get_ipython):
            try:
                ipython = get_ipython()
            except Exception:
                pass
    return ipython is not None and 'spyder' in (
        type(ipython).__module__ + '.' + type(ipython).__name__).lower()


def isolated_environment(environ=None):
    """Strip Qt paths injected by another GUI; preserve Python/conda paths."""
    env = dict(os.environ if environ is None else environ)
    for key in ('QT_QPA_PLATFORM_PLUGIN_PATH', 'QT_PLUGIN_PATH', 'QT_QPA_FONTDIR'):
        env.pop(key, None)
    env[CHILD_MARKER] = '1'
    env['PYTHONFAULTHANDLER'] = '1'
    env['PYTHONUNBUFFERED'] = '1'
    return env


def log_directory(home=None):
    root = (Path.home() if home is None else Path(home)) / '.varians_synchro' / 'logs'
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        root = Path(tempfile.gettempdir()) / 'varians_synchro_logs'
        root.mkdir(parents=True, exist_ok=True)
    return root


def launch_isolated(script=None, *, popen=subprocess.Popen, executable=None, log_dir=None):
    """Spawn detached GUI with the interpreter actually used by Spyder.

    Return log path + child PID for diagnostics, not a false 'success' promise.
    """
    script = (Path(__file__).resolve().parent.parent / 'run.py') if script is None else Path(script).resolve()
    executable = executable or sys.executable
    folder = log_directory() if log_dir is None else Path(log_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    path = folder / f'demarrage_{stamp}.log'
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0
    with path.open('wb') as stream:
        stream.write(f'Varians-Synchro launch | {stamp} | Python: {executable}\n'.encode())
        stream.flush()
        child = popen([str(executable), '-X', 'faulthandler', '-u', str(script)],
                      cwd=str(script.parent), env=isolated_environment(),
                      stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                      creationflags=flags)
    return path, child.pid
