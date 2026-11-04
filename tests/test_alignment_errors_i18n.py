"""Les messages d'erreur de l'alignement (physical_alignment.py) sont dans
les catalogues : l'interface les affiche avec ``tr`` (le texte français est
l'alias de sa clé), donc dans la langue choisie. « Associez des pages ALTO
aux deux témoins avant de synchroniser » s'affichait en français partout."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from varians_synchro.i18n import set_language, tr

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'varians_synchro' / 'physical_alignment.py').read_text(encoding='utf-8')
MESSAGES = sorted(set(re.findall(r"raise ValueError\('([^']*)'\)", SOURCE)))


def test_every_alignment_error_has_a_catalog_entry():
    french = {entry.text for entry in ET.parse(ROOT / 'i18n' / 'fr.xml').getroot()}
    assert len(MESSAGES) >= 20
    assert [m for m in MESSAGES if m not in french] == []


def test_the_message_is_shown_in_the_chosen_language():
    message = 'Associez des pages ALTO aux deux témoins avant de synchroniser'
    try:
        set_language('en')
        assert tr(message) == 'Link ALTO pages to both witnesses before aligning them'
        set_language('ja')
        assert tr(message) != message
    finally:
        set_language('fr')
    assert tr(message) == message
