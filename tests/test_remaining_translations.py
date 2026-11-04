"""Derniers textes non traduits (red team D7, D8).

- Les boutons standard de Qt (« &Yes », « &No », « OK », « Cancel »)
  restaient en anglais, même en français : aucun traducteur Qt n'était
  installé. PySide6 livre les traductions de Qt pour six des sept langues
  (le tchèque compris) ; elles suivent la langue choisie.
- Les diagnostics de la liaison TEI et les avertissements de l'association
  par lots étaient écrits en français dans le code ; « [ligne modifiée] »
  avait sa clé mais n'était pas traduit.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest

from varians_synchro.errors import localized_text
from varians_synchro.i18n import get_language, set_language, tr


@pytest.fixture
def german():
    previous = get_language()
    set_language('de')
    yield
    set_language(previous)


def test_qt_standard_buttons_follow_the_language(german):
    pytest.importorskip('PySide6')
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from varians_synchro.ui_widgets import install_qt_translation
    try:
        install_qt_translation('de')
        assert QCoreApplication.translate('QPlatformTheme', '&Yes') == '&Ja'
        install_qt_translation('fr')
        assert QCoreApplication.translate('QPlatformTheme', '&Yes') == '&Oui'
    finally:
        install_qt_translation('en')
    assert QCoreApplication.translate('QPlatformTheme', '&Yes') == '&Yes'


def test_tei_binding_diagnostics_are_translated(tmp_path, german):
    from varians_synchro.tei_binding import extract_witness_tei
    tei = tmp_path / 'e.xml'
    tei.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p><lb/>a <lb edRef="#B"/>b'
                   '<choice/></p></body></text></TEI>', encoding='utf-8')
    diagnostics = extract_witness_tei(tei, 'A')['diagnostics']
    shown = [localized_text(d['message']) for d in diagnostics]
    assert tr('error.tei.no_target_lb', witness='A') in shown
    assert tr('error.tei.unattributed_lb', count=1, witness='A') in shown
    assert all(text != d['message'] for text, d in zip(shown, diagnostics))      # en allemand


def test_batch_binding_warnings_are_translated(german):
    from varians_synchro.bulk_binding import propose_bindings
    from varians_synchro.core import create_witness, new_project
    witness = create_witness(new_project('Essai'), 'A')
    witness['pages'] = [{'id': 'p1', 'label': '1r', 'image_kind': 'iiif', 'alto_binding': None}]
    witness['alto_sources'] = [{'id': 's', 'path': '/absent/x.xml', 'pages': [{'lines': []}, {'lines': []}]}]
    rows = propose_bindings(witness)['rows']
    assert localized_text(rows[0]['warning']) == tr('error.binding.no_unique_match')
