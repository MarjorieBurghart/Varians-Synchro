"""Read-only reciprocal navigation over a physical ALTO pair session.

This module never changes line selection or alignment data.  Links with
confirmed absences have no target lines, and can be reported to the researcher
without manufacturing a fictitious counterpart.  Direct links only: no
transitive inference and no assumption that HTR is reliable.
"""
from __future__ import annotations


def build_pair_navigation_index(session):
    """Return (reference_index, target_index) for direct line relationships.

    Each entry contains counterpart UIDs, the link's state, origin, and kind.
    All rows in 1-to-many and many-to-many links receive the whole opposite
    group.  The original data and UID order remain untouched.
    """
    ref_index, target_index = {}, {}
    for link in session.get('links', []):
        refs = list(dict.fromkeys(link.get('reference_ids', [])))
        targets = list(dict.fromkeys(link.get('target_ids', [])))
        kind = link.get('kind', 'correspondence')
        if kind not in ('correspondence', 'absence'):
            continue
        information = {
            'kind': kind,
            'state': link.get('state', 'uncertain'),
            'origin': link.get('origin', 'manual'),
            'link_id': link.get('id'),
        }
        for uid in refs:
            ref_index[uid] = {**information, 'counterpart_ids': targets if kind == 'correspondence' else []}
        for uid in targets:
            target_index[uid] = {**information, 'counterpart_ids': refs if kind == 'correspondence' else []}
    return ref_index, target_index


def combined_counterparts(index, selected_ids, *, clicked=None):
    """Collect the unique related lines for a witness-wide visual selection.

    Prioritise the most recent click for navigation, then preserve the order of
    the selected physical lines. This is a read-only *preview*: no links or
    other-witness selections are modified. A plain click's replacement of the
    selected set automatically discards older visual previews.
    """
    ids = list(selected_ids)
    candidates = ([clicked] if clicked in ids else []) + ids
    targets = []
    seen = set()
    absence = False
    for uid in candidates:
        info = index.get(uid)
        if not info:
            continue
        if info['kind'] == 'absence':
            absence = True
        elif info['kind'] == 'correspondence':
            for target in info.get('counterpart_ids', []):
                if target not in seen:
                    seen.add(target)
                    targets.append(target)
    return targets, absence
