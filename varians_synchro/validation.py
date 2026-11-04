"""Read-only V0.7.4 preflight for documentary streams and physical pairs.

The audit NEVER repairs historical links, guesses an omission, or modifies data.
Warnings may reflect unavailable external resources on a different workstation.
Hard errors mark contradictions that must not be silently treated as reliable.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from .physical_alignment import physical_lines, STATES, KINDS
from .reading_stream import reading_stream, anchor_intervals, ReadingOrderError
from .varians_export import inspect_varians_export, _pair_for_base
from .core import validate_project


def _item(severity, code, *, witness=None, pair=None, link_id=None, detail=None):
    item = {'severity': severity, 'code': code}
    if witness is not None: item['witness'] = witness
    if pair is not None: item['pair'] = pair
    if link_id is not None: item['link_id'] = link_id
    if detail is not None: item['detail'] = detail
    return item


def _read_otherwise(source):
    """True for an unchanged PAGE file whose lines this version reads
    otherwise than its import did (nested reading order or regions, read
    wrongly before): the project keeps its lines, but associating the file
    again would give other ranks, so groups touching them would go stale."""
    if source.get('kind') != 'page' or not source.get('source_sha256'):
        return False
    import hashlib
    from .page_xml import inspect_page_xml
    path = Path(source['path'])
    try:
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['source_sha256']:
            return False             # another file: its new lines are expected
        fresh = inspect_page_xml(path)['pages']
    except (OSError, ValueError, SyntaxError):
        return False
    def lines(pages):
        return [[(line.get('alto_id'), line.get('text')) for line in page.get('lines', [])] for page in pages]
    return lines(fresh) != lines(source.get('pages', []))


def audit_project(project, base_witness_id=None, *, check_paths=False):
    """Return a JSON-serializable preflight, without changing ``project``.

    Three-witness projects remain pair-local: no invented A<->F mapping via Mu.
    Invalid or obsolete physical references are ERRORs; external file absence
    is a WARNING (projects may be transferred to another machine).
    """
    messages, summary = [], {'witnesses': {}, 'pairs': {}, 'tei': {}}
    try:
        validate_project(project)
    except (ValueError, TypeError, KeyError) as exc:
        messages.append(_item('error', 'invalid_project', detail=str(exc)))
        return {'ok': False, 'errors': 1, 'warnings': 0, 'messages': messages,
                'summary': summary, 'base': base_witness_id}
    witnesses = {w['id']: w for w in project.get('witnesses', [])}
    known = {}
    for wid, w in witnesses.items():
        try:
            physical = physical_lines(w)
            active = reading_stream(w)
        except (ValueError, KeyError, TypeError, ReadingOrderError) as exc:
            messages.append(_item('error', 'invalid_reading_stream', witness=wid, detail=str(exc)))
            known[wid] = set()
            continue
        physical_ids = {row['id'] for row in physical}
        active_ids = {row['id'] for row in active}
        ignored = set(w.get('ignored_line_ids', []))
        dangling = ignored - physical_ids
        if dangling:
            messages.append(_item('warning', 'obsolete_ignored_lines', witness=wid,
                                  detail=len(dangling)))
        if check_paths:
            for source in w.get('alto_sources', []):
                if not Path(source.get('path') or '').is_file():
                    messages.append(_item('warning', 'xml_source_unavailable', witness=wid,
                                          detail=source.get('path')))
                elif _read_otherwise(source):
                    messages.append(_item('warning', 'xml_source_read_otherwise', witness=wid,
                                          detail=Path(source['path']).name))
            for page in w.get('pages', []):
                if page.get('image_kind') == 'local' and not Path(page.get('image_path') or '').is_file():
                    messages.append(_item('warning', 'local_image_unavailable', witness=wid,
                                          detail=page.get('label', page.get('id'))))
        mapped = len({row['page_id'] for row in physical})
        summary['witnesses'][wid] = {'physical_lines': len(physical), 'active_lines': len(active),
            'ignored_lines': len(physical_ids & ignored), 'mapped_pages': mapped,
            'pages': len(w.get('pages', []))}
        known[wid] = active_ids
    # TEI ↔ physical is a separate editorial layer. A stale linkage never
    # rewrites witness-to-witness groups or adds fictitious export base_keys.
    from .tei_binding import tei_binding_status
    for source in project.get('text_resources', []):
        if source.get('kind') != 'tei':
            continue
        wid, rid = source.get('witness_id'), source.get('id')
        if wid not in witnesses or not rid:
            messages.append(_item('warning', 'tei_unattached_or_unknown_witness',
                                  witness=wid, detail=source.get('path')))
            continue
        status = tei_binding_status(project, wid, rid)
        summary['tei'][rid] = {'witness_id':wid, 'status':status['status'],
                                'bound_lines':status['count']}
        if status['status'] == 'stale':
            messages.append(_item('warning', 'tei_binding_stale', witness=wid,
                                  detail=status.get('reason', '')))
    seen_pairs = set()
    for session in project.get('pair_sessions', []):
        a, b = session.get('reference_witness_id'), session.get('target_witness_id')
        pair = ' ↔ '.join(str(x) for x in (a, b))
        pair_id = tuple(sorted([str(a), str(b)]))
        if not a or not b or a == b or a not in witnesses or b not in witnesses:
            messages.append(_item('error', 'unknown_or_identical_pair', pair=pair))
            continue
        if pair_id in seen_pairs:
            messages.append(_item('error', 'duplicate_pair_session', pair=pair))
        seen_pairs.add(pair_id)
        occupied = {'reference': {}, 'target': {}}
        counters = Counter()
        link_ids = set()
        for link in session.get('links', []):
            lid = link.get('id')
            counters['links'] += 1
            if not lid or lid in link_ids:
                messages.append(_item('error', 'duplicate_or_missing_link_id', pair=pair, link_id=lid))
            link_ids.add(lid)
            ref = link.get('reference_ids') or []
            tgt = link.get('target_ids') or []
            kind = link.get('kind')
            if link.get('state') not in STATES or kind not in KINDS:
                messages.append(_item('error', 'invalid_link_state_or_kind', pair=pair, link_id=lid))
            if (kind == 'correspondence' and (not ref or not tgt) or
                kind == 'absence' and (bool(ref) == bool(tgt))):
                messages.append(_item('error', 'invalid_group_sides', pair=pair, link_id=lid))
            for side, ids, wid in [('reference', ref, a), ('target', tgt, b)]:
                if len(ids) != len(set(ids)):
                    messages.append(_item('error', 'duplicate_line_inside_group', pair=pair, link_id=lid,
                                          detail=side))
                for uid in set(ids):
                    if uid not in known.get(wid, set()):
                        messages.append(_item('error', 'stale_or_ignored_line', pair=pair,
                                              link_id=lid, detail=side))
                    if uid in occupied[side]:
                        messages.append(_item('error', 'line_in_multiple_groups', pair=pair,
                                              link_id=lid, detail=side))
                    occupied[side][uid] = lid
            if kind == 'correspondence':
                counters['correspondences'] += 1
                if link.get('state') == 'validated': counters['validated'] += 1
            elif kind == 'absence' and link.get('state') == 'validated':
                counters['confirmed_absences'] += 1
        counters['linked_reference_lines'] = len(occupied['reference'])
        counters['linked_target_lines'] = len(occupied['target'])
        if a in witnesses and b in witnesses and known.get(a) and known.get(b):
            try:
                intervals = anchor_intervals(project, session)
                for warning in intervals['warnings']:
                    messages.append(_item('warning', 'anchor_' + warning['reason'],
                                          pair=pair, link_id=warning.get('link_id')))
                counters['anchored_intervals'] = len(intervals['intervals'])
            except (ValueError, TypeError, KeyError, ReadingOrderError) as exc:
                messages.append(_item('error', 'cannot_analyze_anchors', pair=pair, detail=str(exc)))
        summary['pairs'][pair] = dict(counters)
    if base_witness_id is not None:
        if base_witness_id not in witnesses:
            messages.append(_item('error', 'unknown_export_base', witness=base_witness_id))
        elif known.get(base_witness_id):
            try:
                export = inspect_varians_export(project, base_witness_id)
                summary['export'] = export['witnesses']
                for wid, stats in export['witnesses'].items():
                    if stats['working_linked_lines'] == 0:
                        messages.append(_item('warning', 'secondary_no_base_keys', witness=wid,
                                              detail=stats['reason']))
                    elif stats['validated_linked_lines'] == 0:
                        messages.append(_item('warning', 'secondary_only_uncertain', witness=wid))
            except (ValueError, TypeError, KeyError) as exc:
                messages.append(_item('error', 'export_preflight_failed', detail=str(exc)))
    return {'ok': not any(m['severity'] == 'error' for m in messages),
            'errors': sum(m['severity'] == 'error' for m in messages),
            'warnings': sum(m['severity'] == 'warning' for m in messages),
            'messages': messages, 'summary': summary, 'base': base_witness_id}
