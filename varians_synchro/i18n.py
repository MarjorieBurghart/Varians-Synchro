"""Varians-Synchro localization: XML catalogs, same schema as Varians.

The files ``i18n/fr.xml`` and ``i18n/en.xml`` live beside ``run.py``.
All UI message values (including the French defaults) come from these files.
Application state, source texts, folio labels and manuscripts are NEVER translated.
"""
from __future__ import annotations

from pathlib import Path
import string
import xml.etree.ElementTree as ET

CATALOG_DIR = Path(__file__).resolve().parent.parent / 'i18n'
_LANGUAGE = 'fr'
_CATALOGS = {}
_LABELS = {}
_ALIASES = {}
EN = {}  # Backward-compatible read-only-style snapshot, populated from XML.


def _load_one(file: Path, language: str) -> tuple[dict[str, str], str]:
    root = ET.parse(file).getroot()
    if root.tag != 'translations' or root.get('lang') != language:
        raise ValueError(f'Invalid translation catalog: {file}')
    result = {}
    for entry in root:
        if entry.tag != 'string':
            raise ValueError(f'Unexpected XML element in {file}: {entry.tag}')
        key = entry.get('key')
        if not key or key in result:
            raise ValueError(f'Missing/duplicate translation key in {file}: {key}')
        value = entry.text if entry.text is not None else ''
        if not value.strip():
            raise ValueError(f'Empty translation for {key} in {file}')
        result[key] = value
    return result, (root.get('label') or language)


def _parameters(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def reload_catalogs(directory: str | Path | None = None) -> None:
    """Reload XML from disk (e.g. after a translator edits a file).

    Parse and validate both languages before replacing active catalogs.
    """
    global _CATALOGS, _LABELS, _ALIASES, EN
    directory = Path(directory) if directory is not None else CATALOG_DIR
    files = sorted(directory.glob('*.xml'))
    if not files or not {'fr', 'en'}.issubset({f.stem for f in files}):
        raise ValueError(f'French and English XML catalogs required in {directory}')
    parsed = {f.stem: _load_one(f, f.stem) for f in files}
    new = {lang: pair[0] for lang, pair in parsed.items()}
    labels = {lang: pair[1] for lang, pair in parsed.items()}
    expected = set(new['fr'])
    for lang, values in new.items():
        if set(values) != expected:
            raise ValueError('Translation keys differ in ' + lang + ': ' +
                             ', '.join(sorted(set(values) ^ expected)[:12]))
        for key, french in new['fr'].items():
            if _parameters(french) != _parameters(values[key]):
                raise ValueError(f'Translation placeholders differ for {key} ({lang})')
    aliases = {v: k for k,v in new['fr'].items()}
    _CATALOGS = new
    _LABELS = labels
    _ALIASES = aliases
    EN = {french: new['en'][key] for key, french in new['fr'].items()}


def available_languages() -> tuple[str, ...]:
    return tuple(_CATALOGS)


def language_labels() -> dict[str, str]:
    """Human-facing language names from XML, for the UI selector."""
    return dict(_LABELS)


def set_language(language: str) -> None:
    global _LANGUAGE
    if language not in _CATALOGS:
        raise ValueError(f'Unsupported language: {language}')
    _LANGUAGE = language


def get_language() -> str:
    return _LANGUAGE


def tr(key_or_legacy_text: str, **values) -> str:
    """Translate a symbolic key (preferred) or an old literal UI phrase.

    Unknown texts are returned unchanged: a manuscript/folio identifier or
    an error should never be silently translated by approximate matching.
    """
    key = (key_or_legacy_text if key_or_legacy_text in _CATALOGS['fr']
           else _ALIASES.get(key_or_legacy_text))
    value = (_CATALOGS[_LANGUAGE].get(key, _CATALOGS['fr'].get(key, key_or_legacy_text))
             if key else key_or_legacy_text)
    return value.format(**values) if values else value


def is_catalog_text(text) -> bool:
    """``text`` is a key of the catalogs, or the French value of one (never
    a text received from a file, a server or a project)."""
    return isinstance(text, str) and (text in _CATALOGS['fr'] or text in _ALIASES)


def french(key: str, **values) -> str:
    """Le texte français de *key*, quelle que soit la langue de l'interface :
    celui des messages d'erreur et des journaux (voir ``errors.py``)."""
    value = _CATALOGS['fr'].get(key, key)
    return value.format(**values) if values else value


def translate_template(key_or_legacy_text: str, **values) -> str:
    return tr(key_or_legacy_text, **values)


reload_catalogs()
