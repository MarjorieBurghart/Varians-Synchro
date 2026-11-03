"""V0.7.2 — rapid, non-destructive human review of physical correspondences.

This module never auto-validates machine suggestions. Display sorting and
filtering have no effect on .vsynch storage order or Varians JSON export.
"""
from __future__ import annotations

from .physical_alignment import pair_indices, set_pair_link_states, stale_link_ids
from .reading_stream import reading_stream

FILTER_ALL = 'all'
FILTER_PENDING = 'pending'
FILTER_VALIDATED = 'validated'
FILTER_ABSENCES = 'absences'
# Links whose lines changed after a new segmentation: to revalidate or unlink.
FILTER_STALE = 'stale'
FILTERS = {FILTER_ALL, FILTER_PENDING, FILTER_VALIDATED, FILTER_ABSENCES, FILTER_STALE}


def ordered_links(project, session, filter_mode=FILTER_ALL):
    """Order by *reading stream*, across folios; keep underlying links unchanged."""
    if filter_mode not in FILTERS:
        raise ValueError('Unknown review filter')
    witnesses = {w['id']: w for w in project['witnesses']}
    left = reading_stream(witnesses[session['reference_witness_id']], include_ignored=True)
    right = reading_stream(witnesses[session['target_witness_id']], include_ignored=True)
    ai = {line['id']: i for i, line in enumerate(left)}
    bi = {line['id']: i for i, line in enumerate(right)}
    stale = stale_link_ids(project, session) if filter_mode == FILTER_STALE else set()

    def visible(link):
        if filter_mode == FILTER_STALE:
            return link['id'] in stale
        if filter_mode == FILTER_PENDING:
            return link['state'] != 'validated' and link['kind'] == 'correspondence'
        if filter_mode == FILTER_VALIDATED:
            return link['state'] == 'validated' and link['kind'] == 'correspondence'
        if filter_mode == FILTER_ABSENCES:
            return link['kind'] == 'absence'
        return True

    def sort_key(link):
        left_positions = [ai[x] for x in link.get('reference_ids', []) if x in ai]
        right_positions = [bi[x] for x in link.get('target_ids', []) if x in bi]
        # Missing/stale UIDs should remain inspectable, not crash sorting.
        return (min(left_positions, default=len(ai) + 1),
                min(right_positions, default=len(bi) + 1),
                str(link['id']))

    return sorted((link for link in session.get('links', []) if visible(link)), key=sort_key)


def review_counts(session):
    links = session.get('links', [])
    return {'pending': sum(l['state'] != 'validated' and l['kind'] == 'correspondence' for l in links),
            'validated': sum(l['state'] == 'validated' and l['kind'] == 'correspondence' for l in links),
            'absences': sum(l['kind'] == 'absence' for l in links)}


def pending_ids(project, session):
    return [link['id'] for link in ordered_links(project, session, FILTER_PENDING)]


def following_anchor_interval(project, session, first_anchor_id):
    """Return the *next* validated homologous pair, if its order is unambiguous.

    A crossing or duplicate anchor is not an eligible local recalculation.
    Only an explicit validated anchor can create a fresh segment boundary.
    """
    links = [l for l in session.get('links', [])
             if l.get('state') == 'validated' and l.get('kind') == 'correspondence']
    from .reading_stream import anchor_intervals
    pairs = anchor_intervals(project, session)['intervals']
    candidates = [i for i in pairs if i['start_link_id'] == first_anchor_id]
    if len(candidates) == 1:
        return first_anchor_id, candidates[0]['end_link_id']
    return None


def verify_before_review(project, session, ids):
    """Check every selected ID and its fingerprints before any batch validation.

    Fail atomically if ALTO/PAGE changed since the proposal was generated.
    Validated manual anchors are not revalidated as a side effect.
    """
    wanted = set(ids)
    links = {link['id']: link for link in session.get('links', [])}
    if len(wanted) != len(ids) or not wanted or wanted - links.keys():
        raise ValueError('Review selection is empty, duplicated or no longer exists')
    a, b = pair_indices(project, session)
    for uid in wanted:
        link = links[uid]
        if link.get('kind') != 'correspondence':
            raise ValueError('An absence cannot be validated as a correspondence')
        for line_id in link.get('reference_ids', []) + link.get('target_ids', []):
            current = a.get(line_id) or b.get(line_id)
            if current is None or link.get('fingerprints', {}).get(line_id) != current['fingerprint']:
                raise ValueError('An ALTO/PAGE line has changed: review its association before validation')
    return links


def validate_checked(project, session, ids):
    """Explicit validation of the inspected set, no implicit automatic acceptance."""
    verify_before_review(project, session, ids)
    return set_pair_link_states(session, ids, 'validated')


def suggestions_for_interval(result, start_id, end_id):
    """Select only suggestions *entirely* bounded by a known pair of anchors."""
    return [p for p in result['proposals']
            if p.get('evidence', {}).get('interval_start') == start_id
            and p.get('evidence', {}).get('interval_end') == end_id]
