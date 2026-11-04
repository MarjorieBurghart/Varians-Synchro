"""Fenêtres encore ouvertes à la fin des tests : libérées avant l'arrêt de Python.

À l'arrêt de l'interpréteur, PySide détruit les fenêtres que Python garde
encore (``PySide::destroyQCoreApplication``). Selon l'ordre de ce passage,
la destruction d'une fenêtre pouvait toucher un objet déjà libéré : la suite
réussissait, puis le processus s'arrêtait sur une erreur de segmentation
(``QObject::~QObject``), une fois sur huit environ — un échec de la CI.

Les tests libèrent les fenêtres qu'ils ouvrent ; ce filet libère, par le
mécanisme ordinaire de Qt (``deleteLater``), celles qui resteraient. Rien
n'est montré ni demandé : ``closeEvent`` n'est pas appelé.
"""
import gc
import sys


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
