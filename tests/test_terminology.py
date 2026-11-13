"""Varians-Synchro emploie les termes de Varians, dans chaque langue : les
deux logiciels se suivent (le guide cite les libellés de l'un et de
l'autre). Écarts corrigés : en japonais, 基準伝本 (pivot) et 略号 (sigle),
au lieu de ピボット伝本 et シグラム ; en allemand, « Zeuge » au lieu de
« Textzeuge »."""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import help_labels  # noqa: E402

AVOIDED = {
    'ja': re.compile('基準伝本|略号'),
    'de': re.compile(r'(?<![A-Za-zÄÖÜäöüß])Zeuge|(?:Referenz|Vergleichs)zeug'),
}


@pytest.mark.parametrize('lang', sorted(AVOIDED))
def test_the_terms_of_varians_are_used(lang):
    for path in (ROOT / 'i18n' / f'{lang}.xml', ROOT / 'help' / f'{lang}.html'):
        found = AVOIDED[lang].findall(path.read_text(encoding='utf-8'))
        assert found == [], f'{path.name}: {sorted(set(found))}'


def test_the_siglum_is_named_as_in_varians():
    source = help_labels.varians_source()
    if source is None:
        if os.environ.get('VARIANS_REQUIRED'):
            pytest.fail('code source de Varians introuvable (VARIANS_SOURCE)')
        pytest.skip('code source de Varians introuvable')
    for lang in ('fr', 'en', 'de', 'cs', 'it', 'ru', 'ja'):
        varians = help_labels.varians_catalog(lang, source)['project.witness.id']
        assert help_labels.synchro_label('resources.witness.sigil', lang) == help_labels.screen_text(varians), lang
