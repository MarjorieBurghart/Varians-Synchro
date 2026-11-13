import unittest
from varians_synchro.i18n import set_language,tr,EN


class InternationalizationTests(unittest.TestCase):
    def tearDown(self):
        set_language('fr')

    def test_default_french_english_and_neutral_manuscript_data(self):
        set_language('fr')
        self.assertEqual(tr('Associer les lignes'),'Associer les lignes')
        set_language('en')
        self.assertEqual(tr('Associer les lignes'),'Link selected lines')
        self.assertEqual(tr('textus Iohannes manuscrit'), 'textus Iohannes manuscrit')
        self.assertEqual(tr('viewer.alto.toggle'),'Line outlines')
        self.assertEqual(tr('Images et ALTO uniquement'),'Images and ALTO only')

    def test_seven_languages_supported(self):
        from varians_synchro.i18n import available_languages
        self.assertEqual(set(available_languages()), {'fr','en','de','cs','it','ru','ja'})
        for language in available_languages():
            set_language(language)
            self.assertTrue(tr('navigation.project'))
        with self.assertRaises(ValueError): set_language('xx')

    def test_catalog_has_no_empty_translations(self):
        self.assertTrue(all(k.strip() and v.strip() for k,v in EN.items()))

if __name__=='__main__':unittest.main()


def test_visual_htr_panel_controls_translated():
    set_language('en')
    try:
        assert tr('Texte HTR') == 'HTR text'
        assert tr('Effacer sélection') == 'Clear selection'
        assert tr('Effacer les lignes sélectionnées sur les images') == 'Clear selected lines on the images'
    finally:
        set_language('fr')
