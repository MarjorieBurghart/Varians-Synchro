"""Export des images IIIF pour une HTR externe : progression et annulation,
pour que l'interface puisse le faire hors du fil principal (elle gelait
pendant tout le téléchargement)."""
import pytest

import varians_synchro.imaging as imaging
from varians_synchro.core import new_project, create_witness

JPEG = b'\xff\xd8' + b'0' * 32


def _witness():
    project = new_project()
    witness = create_witness(project, 'F')
    witness['pages'] = [{'id': f'canvas-{n}', 'label': n, 'image_kind': 'iiif',
                         'canvas': {'image_service': f'https://example.org/iiif/{n}',
                                    'iiif_image_version': 2}} for n in ('1r', '1v', '2r')]
    return witness


def test_the_export_reports_its_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(imaging, 'image_bytes', lambda page, width: JPEG)
    steps = []
    count = imaging.export_iiif_htr_zip(_witness(), ['canvas-1r', 'canvas-1v', 'canvas-2r'],
                                        tmp_path / 'F.zip', progress=lambda d, t: steps.append((d, t)))
    assert count == 3 and steps == [(1, 3), (2, 3), (3, 3)]


def test_a_cancelled_export_leaves_no_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(imaging, 'image_bytes', lambda page, width: JPEG)
    done = []
    with pytest.raises(InterruptedError):
        imaging.export_iiif_htr_zip(_witness(), ['canvas-1r', 'canvas-1v', 'canvas-2r'],
                                    tmp_path / 'F.zip', cancelled=lambda: len(done) >= 1,
                                    progress=lambda d, t: done.append(d))
    assert list(tmp_path.iterdir()) == []


def test_the_window_stays_responsive_during_the_export(monkeypatch, tmp_path):
    """The export runs in a worker: export() returns at once, the bar moves,
    and the end is reported (it used to freeze the window until the end)."""
    import os
    import threading
    import time
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    from varians_synchro.i18n import tr
    from varians_synchro.ui_pages import PagesDialog as pages_class

    app = QApplication.instance() or QApplication([])
    from varians_synchro.ui_widgets import QFileDialog, QMessageBox
    monkeypatch.setattr(QFileDialog, 'getSaveFileName',
                        staticmethod(lambda *a, **k: (str(tmp_path / 'F_HTR.zip'), '')))
    notices = []
    monkeypatch.setattr(QMessageBox, 'information',
                        staticmethod(lambda parent, title, text, *a: notices.append(text)))
    monkeypatch.setattr(pages_class, '_load_visible_thumbnails', lambda self: None)
    gate = threading.Event()

    def slow_export(witness, selected, path, max_width=2500, *, cancelled, progress):
        progress(1, len(selected))
        gate.wait(20)
        return len(selected)
    monkeypatch.setattr(imaging, 'export_iiif_htr_zip', slow_export)
    from varians_synchro.imaging import create_pages
    project = new_project()
    witness = create_witness(project, 'F')
    witness['image_sources'].append({'id': 'iiif-source', 'kind': 'iiif',
        'reference': 'https://example.org/manifest',
        'manifest': {'canvases': [{'id': f'canvas-{n}', 'label': n,
            'image_service': f'https://example.org/iiif/{n}', 'iiif_image_version': 2}
            for n in ('1r', '1v', '2r')]}})
    create_pages(witness)
    dialog = pages_class(project, witness)
    for row in range(dialog.pages.count()):
        dialog.pages.item(row).setSelected(True)
    dialog.export()                               # rend la main aussitôt
    assert notices == [], notices
    assert dialog._htr_export_thread is not None and not gate.is_set()
    progress = dialog._htr_export_progress
    deadline = time.monotonic() + 20
    while progress.value() != 1 and time.monotonic() < deadline:
        app.processEvents(); time.sleep(.01)
    seen = progress.value()
    gate.set()
    while dialog._htr_export_thread is not None and time.monotonic() < deadline:
        app.processEvents(); time.sleep(.01)
    dialog.close()
    assert seen == 1
    assert notices == [tr('release.images_exported', count=3)]
