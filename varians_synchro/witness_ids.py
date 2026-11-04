"""Sigle d'un témoin et identifiant XML que Varians en tire.

Varians-Synchro garde le sigle saisi comme identifiant du témoin (il entre
dans l'identifiant de chaque ligne et ne change donc jamais). Varians, lui,
a besoin d'un ``xml:id`` (NCName) : quand le sigle n'en est pas un, il en
tire un par :func:`witness_id_for_siglum` et garde le sigle pour
l'affichage (``siglum`` dans project.xml, ``<idno type="siglum">`` dans la
TEI). Cette règle est celle de Varians (module ``witness_ids``, V0.9.2.8.2),
reprise à l'identique : les exports nomment les témoins et leurs fichiers
comme Varians les nommerait (« BnF lat. 123 » → « BnF_lat._123 »).

Module sans Qt."""
from __future__ import annotations

# Caractères de début d'un nom XML (NameStartChar, XML 1.0 5e éd.), « : » exclu.
_START_RANGES = (
    (0x41, 0x5A), (0x5F, 0x5F), (0x61, 0x7A), (0xC0, 0xD6), (0xD8, 0xF6), (0xF8, 0x2FF),
    (0x370, 0x37D), (0x37F, 0x1FFF), (0x200C, 0x200D), (0x2070, 0x218F), (0x2C00, 0x2FEF),
    (0x3001, 0xD7FF), (0xF900, 0xFDCF), (0xFDF0, 0xFFFD), (0x10000, 0xEFFFF),
)
# Caractères permis ensuite (NameChar), en plus des précédents.
_NAME_RANGES = ((0x2D, 0x2E), (0x30, 0x39), (0xB7, 0xB7), (0x300, 0x36F), (0x203F, 0x2040))

# Noms de périphériques que Windows refuse comme noms de fichiers, même
# suivis d'une extension (« CON.json »).
WINDOWS_RESERVED = frozenset({'CON', 'PRN', 'AUX', 'NUL', *(f'COM{n}' for n in range(1, 10)),
                              *(f'LPT{n}' for n in range(1, 10))})


def _in(ranges, ch):
    code = ord(ch)
    return any(low <= code <= high for low, high in ranges)


def _start_char(ch):
    return _in(_START_RANGES, ch)


def _name_char(ch):
    return _start_char(ch) or _in(_NAME_RANGES, ch)


def is_xml_id(value: str) -> bool:
    """``value`` peut-il servir d'``xml:id`` (NCName) ?"""
    return bool(value) and _start_char(value[0]) and all(_name_char(ch) for ch in value[1:])


def witness_id_for_siglum(siglum: str) -> str:
    """Identifiant XML tiré du sigle : le sigle lui-même s'il est valide ;
    sinon chaque caractère interdit devient « _ », et un « _ » est ajouté
    devant si le sigle ne commence pas par une lettre ou « _ ».
    « 1760 » → « _1760 », « T 2 » → « T_2 » ; sigle vide → ""."""
    siglum = (siglum or "").strip()
    if not siglum:
        return ""
    value = "".join(ch if _name_char(ch) else "_" for ch in siglum)
    return value if _start_char(value[0]) else "_" + value


def file_key(siglum: str) -> str:
    """Ce qui distingue deux témoins dans les noms de fichiers des exports :
    leur identifiant XML, sans tenir compte de la casse (Windows et macOS
    ne distinguent pas « a.json » de « A.json »)."""
    return witness_id_for_siglum(siglum).casefold()


def is_reserved_on_windows(siglum: str) -> bool:
    """L'identifiant du sigle, nom de fichier refusé par Windows ?"""
    return witness_id_for_siglum(siglum).split('.')[0].upper() in WINDOWS_RESERVED
