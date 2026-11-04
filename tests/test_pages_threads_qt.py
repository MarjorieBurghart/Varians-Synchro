"""Fenêtre des pages : la fermer pendant un téléchargement ne plante pas.

Scénario (red team D1) : on lance « Télécharger les images IIIF
sélectionnées en HD… » ou « Exporter pour HTR », le serveur tarde, on
annule, puis on ferme la fenêtre. Le fil de téléchargement, rattaché à la
fenêtre, était détruit en cours d'exécution : « QThread: Destroyed while
thread is still running », arrêt brutal du logiciel et travail non
enregistré perdu.

Le scénario tourne dans un processus à part : un tel arrêt emporterait la
suite de tests.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip('PySide6')
ROOT = Path(__file__).resolve().parents[1]

SCENARIO = r'''
import sys, tempfile, threading, time
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QEvent, QTimer
from PySide6.QtWidgets import QApplication, QProgressDialog, QPushButton
app = QApplication.instance() or QApplication([])
import varians_synchro.imaging as imaging
from varians_synchro import ui_widgets
from varians_synchro.core import new_project, create_witness
from varians_synchro.imaging import create_pages
from varians_synchro.ui_pages import PagesDialog
from varians_synchro.ui_widgets import QMessageBox

mode = sys.argv[1]
for name in ('information', 'warning', 'critical'):
    setattr(QMessageBox, name, staticmethod(lambda *a, **k: None))
PagesDialog._load_visible_thumbnails = lambda self: None
started = threading.Event()

def slow_server(*args, cancelled=None, progress=None, **kwargs):
    started.set()
    time.sleep(2)                  # urlopen attend le serveur
    raise InterruptedError('annulé')

imaging.export_iiif_hd_images = slow_server
imaging.export_iiif_htr_zip = slow_server
folder = Path(tempfile.mkdtemp())
ui_widgets.QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: str(folder))
ui_widgets.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(folder / 'F.zip'), ''))

project = new_project()
witness = create_witness(project, 'F')
witness['image_sources'].append({'id': 'iiif', 'kind': 'iiif', 'reference': 'https://example.org/m',
    'status': 'inspected', 'manifest': {'canvases': [
        {'id': f'c{n}', 'label': n, 'image_service': f'https://example.org/iiif/{n}',
         'iiif_image_version': 2, 'width': 1000, 'height': 1500} for n in ('1r', '1v')]}})
create_pages(witness)
dialog = PagesDialog(project, witness)

def start():
    for row in range(dialog.pages.count()):
        dialog.pages.item(row).setSelected(True)
    dialog.download_hd() if mode == 'hd' else dialog.export()
    started.wait(3)
    QTimer.singleShot(100, cancel_then_close)

def cancel_then_close():
    progress = [p for p in dialog.findChildren(QProgressDialog) if p.isVisible()][0]
    progress.findChildren(QPushButton)[0].click()
    app.processEvents()
    close = [b for b in dialog.findChildren(QPushButton) if b.text() == ui_widgets.tr('common.close')][0]
    close.click()

QTimer.singleShot(50, start)
ui_widgets._run_modal(dialog)
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
deadline = time.time() + 4
while time.time() < deadline:
    app.processEvents()
    time.sleep(0.05)
print('fin sans plantage')
'''


@pytest.mark.parametrize('mode', ['hd', 'htr'])
def test_closing_the_pages_window_during_a_download_does_not_crash(tmp_path, mode):
    script = tmp_path / 'scenario.py'
    script.write_text(SCENARIO, encoding='utf-8')
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONPATH=str(ROOT))
    run = subprocess.run([sys.executable, str(script), mode], cwd=str(tmp_path), env=env,
                         capture_output=True, text=True, timeout=60)
    output = run.stdout + run.stderr
    assert 'Destroyed while thread' not in output
    assert run.returncode == 0, output
    assert 'fin sans plantage' in run.stdout
