"""Fenêtres encore ouvertes à la fin des tests : libérées avant l'arrêt de Python.

À l'arrêt de l'interpréteur, PySide détruit les fenêtres que Python garde
encore (``PySide::destroyQCoreApplication``). Selon l'ordre de ce passage,
la destruction d'une fenêtre pouvait toucher un objet déjà libéré : la suite
réussissait, puis le processus s'arrêtait sur une erreur de segmentation
(``QObject::~QObject``), une fois sur huit environ — un échec de la CI.

Les tests libèrent les fenêtres qu'ils ouvrent ; ce filet libère, par le
mécanisme ordinaire de Qt (``deleteLater``), celles qui resteraient. Rien
n'est montré ni demandé : ``closeEvent`` n'est pas appelé.

Le journal des erreurs d'un test (``error_log``, ouvert par ``gui.main``)
va dans un dossier temporaire, jamais dans celui de l'utilisateur, et il est
refermé après le test.
"""
import gc
import sys

import pytest


@pytest.fixture(autouse=True)
def _isolated_error_log(tmp_path_factory, monkeypatch):
    monkeypatch.setenv('VARIANS_SYNCHRO_LOG_DIR', str(tmp_path_factory.getbasetemp() / 'journal-des-erreurs'))
    yield
    error_log = sys.modules.get('varians_synchro.error_log')
    if error_log is not None:
        error_log.uninstall()


def pytest_sessionfinish(session, exitstatus):
    if 'PySide6.QtWidgets' not in sys.modules:
        return
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return
    for _ in range(3):
        widgets = QApplication.topLevelWidgets()
        if not widgets:
            break
        for widget in widgets:
            widget.hide()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        gc.collect()
