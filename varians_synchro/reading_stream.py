"""V0.7: continuous documentary reading streams and human anchor intervals.

This layer never infers textual equivalence. It only orders physical lines and
extracts *every active line* strictly between user-confirmed homologous anchors.
No ALTO/PAGE, saved line UID, fingerprint, or existing pair link is rewritten.

Overrides are stored in the documentary witness's page dictionaries:
``reading_order`` (all pages), ``reading_region_order`` (region identifiers),
``reading_line_order`` (the line UIDs of one page). The last takes precedence.
"""
from __future__ import annotations

from .page_order import ordered_pages
from .physical_alignment import physical_lines


class ReadingOrderError(ValueError):
    """Ambiguous or obsolete documentary reading-order override."""


def _unique_order(items, expected, what):
    if not isinstance(items, list) or len(items) != len(expected) or set(items) != set(expected):
        raise ReadingOrderError(f'Ordre de lecture {what} incomplet, dupliqué ou périmé.')


def set_page_order(witness, page_ids):
    """Atomically assign whole-witness page order, without changing page IDs."""
    pages = witness.get('pages', [])
    _unique_order(page_ids, [page['id'] for page in pages], 'des pages')
    mapping = {page_id: index for index, page_id in enumerate(page_ids)}
    for page in pages:
        page['reading_order'] = mapping[page['id']]


def _region(line):
    return str(line.get('region_id') or '__unclassified__')


def set_region_order(witness, page_id, region_ids):
    """Reorder regions on one page; keep line IDs and their XML-local order."""
    page = next((p for p in witness.get('pages', []) if p['id'] == page_id), None)
    if page is None:
        raise ReadingOrderError('Page inconnue.')
    page_lines = [line for line in physical_lines(witness) if line['page_id'] == page_id]
    expected = list(dict.fromkeys(_region(line) for line in page_lines))
    _unique_order(region_ids, expected, 'des régions')
    page['reading_region_order'] = list(region_ids)
    # Explicit fine-grained line order otherwise masks this region operation.
    page.pop('reading_line_order', None)


def set_line_order(witness, page_id, line_ids):
    """Explicitly reorder all lines on one page; preserve stable UIDs."""
    page = next((p for p in witness.get('pages', []) if p['id'] == page_id), None)
    if page is None:
        raise ReadingOrderError('Page inconnue.')
    expected = [line['id'] for line in physical_lines(witness) if line['page_id'] == page_id]
    _unique_order(line_ids, expected, 'des lignes')
    page['reading_line_order'] = list(line_ids)


def reset_page_line_order(witness, page_id):
    page = next((p for p in witness.get('pages', []) if p['id'] == page_id), None)
    if page is None:
        raise ReadingOrderError('Page inconnue.')
    page.pop('reading_line_order', None)


def page_regions(witness, page_id):
    """Return available region IDs in their current stream order."""
    return list(dict.fromkeys(_region(line) for line in reading_stream(witness, include_ignored=True)
                              if line['page_id'] == page_id))


def reading_stream(witness, *, include_ignored=False):
    """Return one continuous, deterministic line stream across pages/columns.

    XML segmentation order is the default; explicit PAGE region order is already
    applied by its reader. Optional per-page overrides are the only source of
    reordering and are checked for completeness, including ignored lines.
    Legacy .vsynch files work without migration or changes to stable line IDs.
    """
    pages = ordered_pages(witness)
    all_lines = physical_lines(witness)
    grouped = {}
    for line in all_lines:
        grouped.setdefault(line['page_id'], []).append(line)
    ignored = set(witness.get('ignored_line_ids', []))
    result = []
    for page in pages:
        lines = list(grouped.get(page['id'], []))
        if not lines:
            continue
        override = page.get('reading_line_order')
        if override is not None:
            _unique_order(override, [line['id'] for line in lines], 'des lignes')
            order = {uid: idx for idx, uid in enumerate(override)}
            lines.sort(key=lambda line: order[line['id']])
        else:
            regions = list(dict.fromkeys(_region(line) for line in lines))
            region_order = page.get('reading_region_order')
            if region_order is not None:
                _unique_order(region_order, regions, 'des régions')
                orders = {rid: idx for idx, rid in enumerate(region_order)}
                # Sort is stable: within-region physical order is untouched.
                lines.sort(key=lambda line: orders[_region(line)])
        for line in lines:
            if not include_ignored and line['id'] in ignored:
                continue
            item = dict(line)
            item['region_id'] = _region(line)
            item['ignored'] = line['id'] in ignored
            item['stream_index'] = len(result)
            result.append(item)
    return result


def anchor_intervals(project, session):
    """Extract intervals between *validated* 1:n/n:m correspondence groups.

    Traverses pages and columns; handles both anchors with multiple members.
    An anchor must be contiguous on both streams and anchors must be strictly
    monotone. Any missing/ignored/crossed anchor produces an explicit warning;
    it is NEVER discarded to invent a larger, unsafe interval.

    This J1 function is a READ-ONLY preview: no automatic links are generated.
    """
    witnesses = {w['id']: w for w in project.get('witnesses', [])}
    a = reading_stream(witnesses[session['reference_witness_id']])
    b = reading_stream(witnesses[session['target_witness_id']])
    ai = {line['id']: i for i, line in enumerate(a)}
    bi = {line['id']: i for i, line in enumerate(b)}
    anchors = []
    warnings = []
    for link in session.get('links', []):
        if link.get('state') != 'validated' or link.get('kind') != 'correspondence':
            continue
        aids = link.get('reference_ids', [])
        bids = link.get('target_ids', [])
        if not aids or not bids:
            warnings.append({'link_id': link.get('id'), 'reason': 'empty_anchor'})
            continue
        if any(uid not in ai for uid in aids) or any(uid not in bi for uid in bids):
            warnings.append({'link_id': link.get('id'), 'reason': 'stale_or_ignored_anchor'})
            continue
        ia = sorted(ai[uid] for uid in aids)
        ib = sorted(bi[uid] for uid in bids)
        if ia != list(range(ia[0], ia[-1] + 1)) or ib != list(range(ib[0], ib[-1] + 1)):
            warnings.append({'link_id': link.get('id'), 'reason': 'noncontiguous_anchor'})
            continue
        anchors.append({'id': link['id'], 'ref_start': ia[0], 'ref_end': ia[-1],
                        'target_start': ib[0], 'target_end': ib[-1],
                        'reference_ids': list(aids), 'target_ids': list(bids)})
    anchors.sort(key=lambda item: item['ref_start'])
    intervals = []
    # A crossed anchor contaminates both neighboring intervals. Without this
    # guard the next pair (crossed anchor -> C) might look locally monotone
    # and be recalculated despite contradicting the preceding fixed anchor.
    conflicting = set()
    for first, last in zip(anchors, anchors[1:]):
        if first['ref_end'] >= last['ref_start'] or first['target_end'] >= last['target_start']:
            warnings.append({'link_id': last['id'], 'reason': 'crossing_or_overlapping_anchors',
                             'previous_link_id': first['id']})
            conflicting.update((first['id'], last['id']))
    for first, last in zip(anchors, anchors[1:]):
        if first['id'] in conflicting or last['id'] in conflicting:
            continue
        ref_lines = a[first['ref_end'] + 1:last['ref_start']]
        target_lines = b[first['target_end'] + 1:last['target_start']]
        intervals.append({
            'start_link_id': first['id'], 'end_link_id': last['id'],
            'reference_ids': [line['id'] for line in ref_lines],
            'target_ids': [line['id'] for line in target_lines],
            'reference_count': len(ref_lines), 'target_count': len(target_lines),
            'reference_pages': list(dict.fromkeys(line['page_label'] for line in ref_lines)),
            'target_pages': list(dict.fromkeys(line['page_label'] for line in target_lines)),
            'needs_attention': not ref_lines or not target_lines,
        })
    return {'reference_count': len(a), 'target_count': len(b),
            'anchors': anchors, 'intervals': intervals, 'warnings': warnings}
