"""V0.8.5.5: localization completeness and substitution safety.

This tests structural coverage, NOT professional linguistic correctness.
"""
import json
import string
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from varians_synchro import i18n

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('fr', 'en', 'de', 'cs', 'it', 'ru', 'ja')
NEW = ('de', 'cs', 'it', 'ru', 'ja')


def load(lang):
    return {e.attrib['key']: e.text for e in ET.parse(ROOT / 'i18n' / (lang+'.xml')).getroot()}


def params(value):
    return {field for _, field, _, _ in string.Formatter().parse(value) if field is not None}


class CompleteCatalogV0855(unittest.TestCase):
    def tearDown(self):
        i18n.set_language('fr')

    def test_seven_catalogs_complete_identical_keys_and_parameters(self):
        catalogs = {lang: load(lang) for lang in LANGS}
        keys = set(catalogs['fr'])
        # Nombre de clés tenu dans docs/i18n_coverage.json (mis à jour avec les catalogues).
        coverage = json.loads((ROOT/'docs/i18n_coverage.json').read_text(encoding='utf-8'))
        self.assertEqual(len(keys), coverage['fr']['catalog_entries'])
        for lang, values in catalogs.items():
            self.assertEqual(set(values), keys, lang)
            for k in keys:
                self.assertTrue(values[k] and values[k].strip(), (lang, k))
                self.assertEqual(params(values[k]), params(catalogs['fr'][k]), (lang,k))
                self.assertEqual(params(values[k]), params(catalogs['en'][k]), (lang,k))
                values[k].format(**{p:'TEST' for p in params(values[k])})
        self.assertEqual(set(i18n.available_languages()), set(LANGS))

    def test_previous_fallbacks_have_new_translations(self):
        completed = [line for line in (ROOT/'docs/i18n_completed_v0855.txt').read_text(encoding='utf-8').splitlines()
                     if line and not line.startswith('#')]
        self.assertEqual(len(completed), 244)
        self.assertEqual(len(set(completed)), 244)
        eng = load('en')
        for lang in NEW:
            values = load(lang)
            for key in completed:
                self.assertIn(key, values)
                # These proper names / technical terms may correctly be identical in two languages.
                if (lang, key) not in {('de','ui.etat'),('de','ui.details'),('ja','pages.image.iiif')}:
                    self.assertNotEqual(values[key], eng[key], (lang, key))
            self.assertFalse((ROOT/'i18n'/('FALLBACK_'+lang+'.txt')).exists())

    def test_structural_markup_and_technical_tokens_not_translated(self):
        en = load('en')
        for lang in LANGS:
            values = load(lang)
            for key in ('ui.h3.ressources.du.projet.h3', 'ui.h3.verifier.les.images.et.les.alto',
                        'ui.h3.synchroniser.les.temoins.h3', 'ui.h3.avancement.et.verifications.h3'):
                self.assertTrue(values[key].startswith('<h3>'),(lang,key))
                self.assertTrue(values[key].endswith('</h3>'),(lang,key))
            for key in ('project.mode.tei','tei.binding.help','export.varians.warning'):
                self.assertIn('<lb/>', values[key],(lang,key))
            for key in ('export.varians.audit_warning','export.varians.success'):
                self.assertIn('base_keys',values[key],(lang,key))
            for key in ('export.varians.warning','export.varians.audit_confirmation'):
                if lang != 'fr':  # Existing FR catalog describes the sets in French.
                    self.assertIn('working',values[key],(lang,key))
                    self.assertIn('validated',values[key],(lang,key))

    def test_coverage_json_consistent(self):
        coverage=json.loads((ROOT/'docs/i18n_coverage.json').read_text(encoding='utf-8'))
        self.assertEqual(set(coverage),set(LANGS))
        for lang in LANGS:
            self.assertEqual(coverage[lang]['catalog_entries'],len(load('fr')))
            self.assertEqual(coverage[lang]['english_fallbacks'],0)
            self.assertEqual(coverage[lang]['fallback_key_file'],None)

    def test_live_translation_and_substitution(self):
        for lang in NEW:
            i18n.set_language(lang)
            self.assertNotEqual(i18n.tr('alignment.action.fill_anchors'),load('en')['alignment.action.fill_anchors'])
            self.assertIn('37',i18n.tr('audit.result',errors=37,warnings=5))
            self.assertIn('example.png', i18n.tr('pages.order.tooltip', image='example.png',page_id='p001'))
            self.assertEqual(i18n.tr('folio f. 72r'), 'folio f. 72r')


if __name__ == '__main__':
    unittest.main()
