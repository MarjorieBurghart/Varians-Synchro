"""Icône de l'application : le logo de Varians-Synchro (sans Qt).

Les images de ``icons/`` sont produites à partir du logo (``logo/*.psd``)
par ``tools/generate_icons.py`` : le logo sur une pastille blanche aux coins
arrondis, lisible sur une barre des tâches claire comme sombre."""
import struct
from pathlib import Path
from types import SimpleNamespace

from varians_synchro import app_icon

ROOT = Path(__file__).resolve().parents[1]


def _png_header(path):
    """Largeur, hauteur et type de couleur (6 : RGBA) d'un PNG."""
    data = path.read_bytes()[:26]
    assert data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', path
    width, height = struct.unpack('>II', data[16:24])
    return width, height, data[25]


def test_the_source_logo_is_kept():
    assert sorted(path.name for path in (ROOT / 'logo').glob('*.psd'))


def test_one_square_transparent_png_per_size():
    assert app_icon.ICON_SIZES == (16, 24, 32, 48, 64, 128, 256)
    for size, path in zip(app_icon.ICON_SIZES, app_icon.icon_files()):
        assert path.parent == ROOT / 'icons'
        assert _png_header(path) == (size, size, 6)


def test_the_windows_icon_file_holds_every_size():
    """``icons/varians_synchro.ico``, pour un raccourci Windows."""
    data = (ROOT / 'icons' / 'varians_synchro.ico').read_bytes()
    reserved, kind, count = struct.unpack('<HHH', data[:6])
    assert (reserved, kind) == (0, 1)
    assert sorted(data[6 + 16 * i] or 256 for i in range(count)) == list(app_icon.ICON_SIZES)


class _Shell32:
    def __init__(self):
        self.ids = []

    def SetCurrentProcessExplicitAppUserModelID(self, value):
        self.ids.append(value)
        return 0                                         # S_OK


def test_windows_gives_the_window_its_own_taskbar_entry():
    """Sans identité propre, Windows range la fenêtre sous python.exe et
    montre l'icône de Python dans la barre des tâches."""
    windll = SimpleNamespace(shell32=_Shell32())
    assert app_icon.use_own_taskbar_entry('win32', windll) is True
    assert windll.shell32.ids == ['Varians.VariansSynchro']


def test_other_systems_are_left_alone():
    windll = SimpleNamespace(shell32=_Shell32())
    assert app_icon.use_own_taskbar_entry('linux', windll) is False
    assert app_icon.use_own_taskbar_entry('darwin', windll) is False
    assert windll.shell32.ids == []


def test_a_windows_without_the_function_is_not_an_error():
    assert app_icon.use_own_taskbar_entry('win32', SimpleNamespace(shell32=SimpleNamespace())) is False


def test_the_module_loads_without_pyside6():
    import subprocess
    import sys
    code = 'import sys, varians_synchro.app_icon; print("PySide6" in sys.modules)'
    done = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == 'False'
