"""XML locale contracts are identical to Varians; no Qt required."""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from varians_synchro import i18n


def test_xml_catalogs_have_matching_keys_and_same_schema():
    root = Path(__file__).resolve().parents[1] / 'i18n'
    fr = ET.parse(root / 'fr.xml').getroot()
    en = ET.parse(root / 'en.xml').getroot()
    assert (fr.tag, fr.attrib) == ('translations', {'lang': 'fr', 'label': 'Français'})
    assert (en.tag, en.attrib) == ('translations', {'lang': 'en', 'label': 'English'})
    a = {x.attrib['key']: x.text for x in fr}
    b = {x.attrib['key']: x.text for x in en}
    assert len(a) >= 250 and set(a) == set(b)
    assert a['alignment.action.link_lines'] == 'Associer les lignes'
    assert b['alignment.action.link_lines'] == 'Link selected lines'
    assert a['project.mode.tei'] == 'Transcription TEI avec <lb/>'
    assert b['project.mode.tei'] == 'TEI transcription with <lb/>'


def test_symbolic_keys_and_legacy_strings_from_xml_not_python():
    try:
        i18n.set_language('en')
        assert i18n.tr('alignment.action.link_lines') == 'Link selected lines'
        assert i18n.tr('Associer les lignes') == 'Link selected lines'
        assert i18n.tr('textus medievalis') == 'textus medievalis'
        assert i18n.tr('project.mode.tei') == 'TEI transcription with <lb/>'
        assert i18n.language_labels()['fr'] == 'Français'
        assert i18n.language_labels()['en'] == 'English'
    finally:
        i18n.set_language('fr')


def test_xml_translation_edit_can_be_reloaded_without_restarting_python(tmp_path):
    for lang in ('fr','en'):
        shutil.copy2(i18n.CATALOG_DIR / (lang+'.xml'), tmp_path / (lang+'.xml'))
    english = tmp_path / 'en.xml'
    tree = ET.parse(english)
    for element in tree.getroot():
        if element.attrib['key'] == 'alignment.action.link_lines':
            element.text = 'Join the selected lines'
    tree.write(english,encoding='utf-8',xml_declaration=True)
    try:
        i18n.reload_catalogs(tmp_path)
        i18n.set_language('en')
        assert i18n.tr('alignment.action.link_lines') == 'Join the selected lines'
        assert i18n.tr('Associer les lignes') == 'Join the selected lines'
    finally:
        i18n.reload_catalogs()
        i18n.set_language('fr')


def test_invalid_missing_translation_is_rejected_without_losing_current_catalog(tmp_path):
    for lang in ('fr','en'):
        shutil.copy2(i18n.CATALOG_DIR / (lang+'.xml'), tmp_path / (lang+'.xml'))
    tree = ET.parse(tmp_path / 'en.xml')
    node = next(x for x in tree.getroot() if x.attrib['key'] == 'alignment.action.link_lines')
    tree.getroot().remove(node)
    tree.write(tmp_path / 'en.xml',encoding='utf-8',xml_declaration=True)
    original = i18n.tr('alignment.action.link_lines')
    with pytest.raises(ValueError,match='Translation keys differ'):
        i18n.reload_catalogs(tmp_path)
    assert i18n.tr('alignment.action.link_lines') == original


def test_additional_xml_language_is_discovered_automatically(tmp_path):
    for lang in ('fr','en'):
        shutil.copy2(i18n.CATALOG_DIR / (lang+'.xml'), tmp_path / (lang+'.xml'))
    tree = ET.parse(tmp_path / 'en.xml')
    root = tree.getroot()
    root.attrib.update(lang='de', label='Deutsch')
    tree.write(tmp_path / 'de.xml',encoding='utf-8',xml_declaration=True)
    try:
        i18n.reload_catalogs(tmp_path)
        assert i18n.available_languages() == ('de','en','fr')
        assert i18n.language_labels()['de'] == 'Deutsch'
        i18n.set_language('de')
        assert i18n.tr('alignment.action.link_lines') == 'Link selected lines'
    finally:
        i18n.reload_catalogs()
        i18n.set_language('fr')


def test_cross_platform_unix_launcher_and_no_platform_specific_logic():
    package = Path(__file__).resolve().parents[1]
    shell = (package / 'start_unix.sh').read_text(encoding='utf-8')
    assert shell.startswith('#!/bin/sh')
    assert 'python3' in shell and 'run.py' in shell
    source = (package / 'run.py').read_text(encoding='utf-8')
    assert 'from varians_synchro.gui import main' in source
    assert 'sys.platform == "win32"' not in source
