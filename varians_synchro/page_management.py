"""Human page ordering; never change page identity or ALTO/PAGE associations.

Only ``reading_order`` is written. The image and its XML binding stay together,
including when a page is moved across a folio or an image-source boundary.
"""
from __future__ import annotations

from .page_order import ordered_pages
from .reading_stream import set_page_order


def page_ids_in_reading_order(witness):
    return [page['id'] for page in ordered_pages(witness)]


def commit_page_order(witness, page_ids):
    """Validate full permutation before any mutation, then commit atomically."""
    page_ids = list(page_ids)
    set_page_order(witness, page_ids)
    return page_ids_in_reading_order(witness)


def invert_page_order(witness):
    return commit_page_order(witness, list(reversed(page_ids_in_reading_order(witness))))


def move_page_by_id(witness, page_id, direction):
    ids = page_ids_in_reading_order(witness)
    try:
        position = ids.index(page_id)
    except ValueError as exc:
        raise ValueError('Page absente du témoin') from exc
    target = position + int(direction)
    if not 0 <= target < len(ids):
        return ids
    ids[position], ids[target] = ids[target], ids[position]
    return commit_page_order(witness, ids)
