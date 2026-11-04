"""Point d'entrée de l'interface de Varians-Synchro.

Les fenêtres sont réparties dans les modules ``ui_*`` :

- ``ui_main_window`` : fenêtre principale (``GuidedWindow``) ;
- ``ui_pair`` : synchronisation visuelle d'une paire de témoins ;
- ``ui_pages`` : images et associations ALTO/PAGE d'un témoin ;
- ``ui_batch_binding`` : association automatique par lot ;
- ``ui_resources`` : ajout et modification d'un témoin ;
- ``ui_tei_binding`` : liaison TEI ↔ lignes physiques ;
- ``ui_reading_order``, ``ui_scope`` : ordre de lecture, périmètre ;
- ``ui_widgets`` : widgets Qt qui traduisent leurs textes, ``_run_modal``.

Ce module ne charge PySide6 qu'à l'appel de ``make_guided_window`` : le
moteur et ses tests s'importent sans Qt.
"""
from __future__ import annotations


def make_guided_window():
    """La classe de la fenêtre principale (PySide6 est chargé ici)."""
    from .ui_main_window import GuidedWindow
    return GuidedWindow
