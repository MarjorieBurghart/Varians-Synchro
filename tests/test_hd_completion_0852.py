"""Regression: finishing the HD progress bar must not announce a cancellation."""
from __future__ import annotations

import ast
from pathlib import Path

from varians_synchro.core import VERSION


def test_download_completion_is_driven_by_worker_status_not_progress_close():
    """Always run: guard the actual UI code even when Qt isn't installed."""
    source = (Path(__file__).resolve().parents[1] / 'varians_synchro' / 'guided_ui.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    download = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'download_hd')
    complete = next(n for n in ast.walk(download) if isinstance(n, ast.FunctionDef) and n.name == 'complete')
    code = ast.get_source_segment(source, complete)
    assert 'if status == \'success\':' in code
    assert "elif status == 'cancelled':" in code
    assert 'cancel.is_set()' not in code
    assert 'progress.canceled.disconnect(cancel.set)' in code
    assert 'progress.hide()' in code
    download_code = ast.get_source_segment(source, download)
    assert 'progress.setAutoClose(False)' in download_code
    assert 'progress.setAutoReset(False)' in download_code
    assert tuple(map(int, VERSION.split('.'))) >= (0, 8, 5, 2)


def test_worker_reports_distinct_success_cancel_failure_with_qt(monkeypatch, tmp_path):
    """Runs on installations with PySide6; no IIIF network access required."""
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    import pytest
    pytest.importorskip('PySide6')
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication
    import varians_synchro.imaging as imaging
    from varians_synchro.guided_ui import make_guided_window
    app = QApplication.instance() or QApplication([])
    main_type = make_guided_window(lambda: None)
    # The thread class lives in the lexical closure of PagesDialog/download_hd.
    pages_class = next(c.cell_contents for c in main_type.manage_pages.__closure__
                       if getattr(c.cell_contents, '__name__', None) == 'PagesDialog')
    thread_type = next(c.cell_contents for c in pages_class.download_hd.__closure__
                       if getattr(c.cell_contents, '__name__', None) == 'HDDownloadThread')
    import threading
    for expected, action in (('success', lambda: 2),
                             ('cancelled', lambda: (_ for _ in ()).throw(InterruptedError('cancel'))),
                             ('failed', lambda: (_ for _ in ()).throw(ValueError('network')))):
        monkeypatch.setattr(imaging, 'export_iiif_hd_images', lambda *args, **kwargs: action())
        thread = thread_type({'id':'F','pages':[]}, ['c'], str(tmp_path), threading.Event())
        results = []
        loop = QEventLoop()
        thread.done.connect(lambda status, count, error: results.append((status, count, error)))
        thread.finished.connect(loop.quit)
        thread.start()
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        thread.wait()
        app.processEvents()
        assert results and results[0][0] == expected
        if expected == 'success':
            assert results[0][1] == 2 and results[0][2] == ''
        else:
            assert results[0][1] == 0 and results[0][2]


def test_gui_100_percent_progress_reports_success_not_cancelled(monkeypatch, tmp_path):
    """Qt integration: progress=maximum then worker success must show success toast."""
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    import pytest
    pytest.importorskip('PySide6')
    from PySide6.QtWidgets import QApplication
    from varians_synchro.core import create_witness, new_project
    from varians_synchro.guided_ui import make_guided_window
    import varians_synchro.imaging as imaging
    import time

    app = QApplication.instance() or QApplication([])
    window_type = make_guided_window(lambda: None)
    pages_class = next(c.cell_contents for c in window_type.manage_pages.__closure__
                       if getattr(c.cell_contents, '__name__', None) == 'PagesDialog')
    # Patch just the local Python wrappers, not global Qt GUI types.
    closure = {getattr(c.cell_contents, '__name__', None): c.cell_contents
               for c in pages_class.download_hd.__closure__}
    file_dialog = closure['QFileDialog']
    message_box = closure['QMessageBox']
    dest = tmp_path / 'HD'
    dest.mkdir()
    monkeypatch.setattr(file_dialog, 'getExistingDirectory',
                        staticmethod(lambda *a, **k: str(dest)))
    notices = []
    monkeypatch.setattr(message_box, 'information',
                        staticmethod(lambda *a, **k: notices.append(('information', a[2]))))
    monkeypatch.setattr(message_box, 'warning',
                        staticmethod(lambda *a, **k: notices.append(('warning', a[2]))))

    def successful_export(witness, selected, destination, *, cancelled, progress):
        progress(1, 1)  # Precisely the value that used to close QProgressDialog.
        return 1
    monkeypatch.setattr(imaging, 'export_iiif_hd_images', successful_export)
    project = new_project()
    witness = create_witness(project, 'F')
    witness['image_sources'].append({'id': 'iiif-source', 'kind': 'iiif',
        'reference': 'https://example.org/manifest',
        'manifest': {'canvases': [{'id': 'canvas-1', 'label': '14v',
            'image_service': 'https://example.org/iiif/14v',
            'iiif_image_version': 3}]}})
    dialog = pages_class(project, witness)
    dialog.pages.item(0).setSelected(True)
    dialog.download_hd()
    deadline = time.monotonic() + 3
    while not notices and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert len(notices) == 1
    assert notices[0][0] == 'information'
    assert '1' in notices[0][1]
    assert 'annul' not in notices[0][1].casefold()
    deadline = time.monotonic() + 3
    while getattr(dialog, '_hd_download_thread', None) is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert dialog._hd_download_thread is None
    dialog.close()
