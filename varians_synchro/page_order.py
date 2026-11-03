"""Documentary reading order for pages, independent of dialog import order.

IIIF Canvas order is authoritative. For local images, common folio labels
(e.g. f014v, 1r, 1v, 2r) or natural filename numbers are used. Mixed-source
witnesses retain their source-group order; a future page-order editor may
allow manual cross-group reordering. This module never renumbers page IDs.
"""
from __future__ import annotations
import re
from pathlib import Path

_FOLIO = re.compile(r'(?<![a-z0-9])(?:f(?:ol(?:io)?)?[-._\s]*)?(\d{1,5})\s*[-._\s]*([rv])(?![a-z])', re.I)
_NATURAL = re.compile(r'(\d+)')


def _natural(text):
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in _NATURAL.split(str(text)))


def folio_key(value):
    """Return sortable folio key or None; avoid treating arbitrary IDs as folios."""
    value = str(value or '')
    match = _FOLIO.search(value)
    if match:
        return int(match.group(1)), 0 if match.group(2).lower() == 'r' else 1
    # A standalone folio label may have spaces or a leading f (e.g. 'f. 12v').
    match = re.search(r'\bf\.?\s*(\d+)\s*([rv])\b', value, re.I)
    if match:
        return int(match.group(1)), 0 if match.group(2).lower() == 'r' else 1
    return None


def _local_key(page):
    label = str(page.get('label') or '')
    filename = Path(page.get('image_path') or '').stem
    folio = folio_key(label) or folio_key(filename)
    if folio:
        return (0, folio[0], folio[1], _natural(filename))
    return (1, _natural(filename or label))


def ordered_pages(witness, pages=None):
    """Return pages in reading order without modifying their identity.

    Existing projects (including those saved in reverse local import order)
    are sorted when read. A user-provided integer ``reading_order`` overrides
    inferred ordering when present on *every* page.
    """
    pages = list(witness.get('pages', []) if pages is None else pages)
    if not pages:
        return pages
    if all(isinstance(p.get('reading_order'), int) for p in pages):
        return sorted(pages, key=lambda p: p['reading_order'])
    kinds = {p.get('image_kind') for p in pages}
    source_indices = {src['id']: i for i, src in enumerate(witness.get('image_sources', []))}
    if kinds == {'local'}:
        return sorted(pages, key=lambda p: _local_key(p))
    def key(page):
        src_index = source_indices.get(page.get('image_source_id'), 10**8)
        if page.get('image_kind') == 'iiif':
            canvas = page.get('canvas') or {}
            return (src_index, 0, int(canvas.get('index') or 0), ())
        return (src_index, 1, 0, _local_key(page))
    return sorted(pages, key=key)
