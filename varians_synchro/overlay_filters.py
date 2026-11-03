"""Pure, UI-independent semantics for ALTO line-overlay filtering.

The source of truth is always the physical-pair alignment session.  Filtering
changes visibility of image frames only; it never mutates links or selected IDs.
In particular, interpolated geometric links are AUTOMATIC proposals, despite
not having an origin string beginning with ``automatic``.
"""
from __future__ import annotations

FILTER_ALL = 'all'
FILTER_UNLINKED = 'unlinked'
FILTER_AUTOMATIC_REVIEW = 'automatic_review'
FILTERS = frozenset((FILTER_ALL, FILTER_UNLINKED, FILTER_AUTOMATIC_REVIEW))

AUTOMATIC_ORIGINS = frozenset((
    'interpolated-geometry',
    'automatic-htr-htr',
))


def style_for_link(link: dict) -> str:
    """Return the semantic overlay style for a saved relationship.

    A manual link is green, a machine-suggested link is blue, and confirmed
    absences are red.  A proposed/uncertain link uses a dashed line; validated
    links use a solid one.  No assumption of HTR accuracy is made.
    """
    if link.get('kind') == 'absence':
        return 'absence'
    origin = str(link.get('origin') or 'manual').lower()
    automatic = (origin in AUTOMATIC_ORIGINS
                 or origin.startswith('automatic')
                 or origin.startswith('interpolated-'))
    validated = link.get('state') == 'validated'
    if automatic:
        return 'automatic_validated' if validated else 'automatic_uncertain'
    return 'manual_validated' if validated else 'manual_uncertain'


def overlay_visible(style: str, filter_name: str = FILTER_ALL, *, selected: bool = False, counterpart: bool = False) -> bool:
    """Whether to display a line box under a given filter.

    Always keep active selections and temporary counterpart highlights visible
    so that the researcher can inspect a link even with restrictive filters.
    ``counterpart`` is display-only and never becomes a selected line.
      ``default`` means there is no correspondence in the current
    pair, not necessarily in every other pair of the project.
    """
    if filter_name not in FILTERS:
        raise ValueError(f'Unknown overlay filter: {filter_name}')
    if selected or counterpart:
        return True
    if filter_name == FILTER_ALL:
        return True
    if filter_name == FILTER_UNLINKED:
        return style == 'default'
    return style == 'automatic_uncertain'
