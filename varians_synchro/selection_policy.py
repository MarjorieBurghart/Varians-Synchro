"""Pure cross-folio line selection rules shared by manuscript and text clicks.

Selection is transient visual UI state, never written to .vsynch or used by the
matching algorithm itself. All UIDs belong to one witness; the caller supplies
the already validated documentary reading order, including ignored lines.
"""
from __future__ import annotations


def update_line_selection(selected, clicked, ordered_ids, *, anchor=None,
                          ctrl=False, shift=False):
    """Return ``(selected_uids, anchor_uid)`` after a deliberate click.

    Simple click replaces *all* witness selection, including other folios.
    Ctrl+click toggles exactly one physical line; Shift+click selects an
    inclusive reading-order interval from the last unmodified/Ctrl click.
    Ctrl+Shift unions that interval with the selection already present.
    """
    selected = set(selected)
    if not shift:
        if ctrl:
            if clicked in selected:
                selected.remove(clicked)
            else:
                selected.add(clicked)
        else:
            selected = {clicked}
        # Keep a stable UID rather than a page-local row number.
        return selected, clicked
    positions = {uid: i for i, uid in enumerate(ordered_ids)}
    if anchor not in positions or clicked not in positions:
        # The previous anchor may have disappeared after source changes.
        return ({clicked} if not ctrl else selected | {clicked}), clicked
    first, last = sorted((positions[anchor], positions[clicked]))
    interval = set(ordered_ids[first:last + 1])
    if ctrl:
        selected.update(interval)
    else:
        selected = interval
    return selected, anchor
