"""One QApplication per process, with Spyder/IPython-friendly window lifetime.

This module deliberately has no Qt dependency so lifecycle logic is unit-testable
without a graphical display. `QApplication` and the main window are injected by
`gui.main()` after importing PySide6.
"""
from __future__ import annotations
import sys


def launch(qapplication, window_factory, argv=None, icon=None):
    """Display the main window and only own Qt's event loop when we own the app.

    Spyder/IPython Qt consoles generally own a QApplication and its event loop.
    In this situation, calling ``QApplication(...)`` or ``app.exec()`` again is
    incorrect. The window is held on the application object to prevent Python
    from garbage-collecting it when the Spyder ``%runfile`` call returns.

    Re-executing while the window is open focuses that window and preserves the
    current (possibly unsaved) project rather than creating a duplicate.

    ``icon`` returns the window icon; it is called once the application exists
    (a Qt icon cannot be built before). When we own the application, the icon
    is the application's, hence that of every window, parentless dialogs
    included; inside another program's Qt console, only our window takes it.
    """
    app = qapplication.instance()
    owns_app = app is None
    if owns_app:
        app = qapplication(sys.argv if argv is None else argv)

    previous = getattr(app, '_varians_synchro_window', None)
    if previous is not None:
        try:
            if previous.isVisible():
                if previous.isMinimized():
                    previous.showNormal()
                previous.raise_()
                previous.activateWindow()
                return 0
        except RuntimeError:
            # A destroyed Qt C++ object may outlive its Python reference.
            pass

    image = None if icon is None else icon()
    if image is not None and owns_app:
        app.setWindowIcon(image)
    window = window_factory()
    if image is not None:
        window.setWindowIcon(image)
    # A Python-side strong reference is required when main() returns in Spyder.
    app._varians_synchro_window = window
    window.show()

    if owns_app:
        return app.exec()
    return 0
