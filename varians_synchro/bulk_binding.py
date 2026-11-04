"""Conservative batch page↔ALTO/PAGE proposals and atomic confirmation.

Strong matches use explicit XML imageFilename / unique filename stems. The
ordinal fallback is ALWAYS labeled as provisional and requires user approval.
No matching operation modifies page order, line IDs or source data.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .page_order import ordered_pages, _natural
from .errors import Localized, localized


def _stem(value):
    return Path(str(value or '').replace('\\', '/')).stem.casefold().strip()


def _strong(value):
    return re.sub(r'[^\w\d]', '', _stem(value), flags=re.UNICODE)


def _page_candidates(page):
    labels = [page.get('label', '')]
    if page.get('image_kind') == 'local':
        labels.append(page.get('image_path', ''))
    else:
        canvas = page.get('canvas') or {}
        labels += [canvas.get('label'), canvas.get('id'), canvas.get('image_url')]
    return {_strong(x) for x in labels if x and _strong(x)}


def _xml_candidates(source, index, xml_page):
    names = [xml_page.get('image_filename'), xml_page.get('alto_page_id')]
    if len(source.get('pages', [])) == 1:
        names.append(source.get('path'))
    return {_strong(x) for x in names if x and _strong(x)}


def binding_fingerprint(witness):
    def current_file_state(path):
        try:
            stat = Path(path).stat()
            return (stat.st_size, stat.st_mtime_ns)
        except OSError:
            return None

    snapshot = {
        'pages': [(p['id'], p.get('reading_order'), p.get('alto_binding'))
                  for p in ordered_pages(witness)],
        'sources': [(s['id'], s.get('source_sha256'), s['path'],
                     current_file_state(s['path']), len(s.get('pages', [])))
                    for s in witness.get('alto_sources', [])]
    }
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def propose_bindings(witness):
    """Return an editable preview, never mutate witness or existing bindings.

    Ordinal fallback is allowed only for a homogeneous local-image batch with
    equal numbers of still-unmatched image and XML pages; never for IIIF subsets.
    """
    pages = [p for p in ordered_pages(witness) if not p.get('alto_binding')]
    all_xml = [(s, i, xp) for s in witness.get('alto_sources', [])
               for i, xp in enumerate(s.get('pages', []))]
    occupied = {(p['alto_binding']['source_id'], p['alto_binding']['page_index'])
                for p in witness.get('pages', []) if p.get('alto_binding')}
    available = [(s, i, xp) for s, i, xp in all_xml if (s['id'], i) not in occupied]
    candidates = {}
    ambiguous_names = False
    # An explicit PAGE @imageFilename is more reliable than the XML filename.
    # Do not use a coincidental XML basename to contradict that metadata.
    for p in pages:
        keys = _page_candidates(p)
        explicit = [(s['id'], i) for s, i, xp in available
                    if xp.get('image_filename') and _strong(xp['image_filename']) in keys]
        if explicit:
            matches = explicit
        else:
            matches = []
            for s, i, xp in available:
                if xp.get('image_filename'):
                    continue  # explicit but incompatible filename: not a strong match
                if keys & _xml_candidates(s, i, xp):
                    matches.append((s['id'], i))
        if len(matches) == 1:
            candidates[p['id']] = matches[0]
        elif len(matches) > 1:
            ambiguous_names = True
    counts = {}
    for target in candidates.values():
        counts[target] = counts.get(target, 0) + 1
    if any(count > 1 for count in counts.values()):
        ambiguous_names = True
    chosen = {pid: target for pid, target in candidates.items() if counts[target] == 1}
    used = set(chosen.values())
    rows = []
    for p in pages:
        target = chosen.get(p['id'])
        if target:
            rows.append({'page_id': p['id'], 'target': list(target), 'method': 'name',
                         'warning': '', 'image': p.get('image_path') or p.get('label') or p['id']})
    remainder_pages = [p for p in pages if p['id'] not in chosen]
    remainder_xml = [(s, i, xp) for s, i, xp in available if (s['id'], i) not in used]
    # Secondary ordinal matching only after *all* remaining files form a 1:1
    # local set, with no duplicated strong-name possibilities left.
    ordinal_ok = (not ambiguous_names and bool(remainder_pages)
                  and len(remainder_pages) == len(remainder_xml)
                  and all(p.get('image_kind') == 'local' for p in remainder_pages))
    if ordinal_ok:
        ordered_xml = sorted(remainder_xml,
                             key=lambda item: (_natural(Path(item[0]['path']).name), item[1]))
        for p, (s, i, _) in zip(remainder_pages, ordered_xml):
            rows.append({'page_id': p['id'], 'target': [s['id'], i], 'method': 'ordinal',
                         'warning': Localized('error.binding.by_order'),
                         'image': p.get('image_path') or p.get('label') or p['id']})
    else:
        for p in remainder_pages:
            rows.append({'page_id': p['id'], 'target': None, 'method': 'unresolved',
                         'warning': Localized('error.binding.no_unique_match'),
                         'image': p.get('image_path') or p.get('label') or p['id']})
    by_page = {x['page_id']: x for x in rows}
    return {'fingerprint': binding_fingerprint(witness),
            'rows': [by_page[p['id']] for p in pages],
            'available': [{'source_id': s['id'], 'page_index': i,
                           'name': f"{Path(s['path']).name} — page {i + 1}",
                           'lines': xp.get('line_count', len(xp.get('lines', [])))}
                          for s, i, xp in available],
            'unmatched_xml': len(remainder_xml) if not ordinal_ok else 0,
            'needs_review': sum(r['method'] == 'ordinal' for r in rows)}


def binding_selection_conflicts(plan, selections, witness=None):
    """Identify duplicate XML assignments *before* mutating any page.

    Returns all conflicting targets with their XML descriptions and page labels;
    this can be used both by the GUI and the headless validation layer.
    A missing/None selection does not count as an assignment.
    """
    pages_by_id = {p['id']: p for p in (witness or {}).get('pages', [])}
    row_by_id = {r['page_id']: r for r in plan.get('rows', [])}
    sources = {(s['source_id'], s['page_index']): s
               for s in plan.get('available', [])}
    selected = {}
    for page_id, target in selections.items():
        if target is None or page_id not in row_by_id:
            continue
        key = tuple(target)
        selected.setdefault(key, []).append(page_id)
    conflicts = []
    for key, page_ids in selected.items():
        if len(page_ids) < 2:
            continue
        source = sources.get(key) or {}
        pages = []
        for page_id in page_ids:
            page = pages_by_id.get(page_id) or {}
            row = row_by_id[page_id]
            pages.append({'page_id': page_id,
                          'label': str(page.get('label') or row.get('image') or page_id)})
        conflicts.append({'target': list(key),
                          'xml': source.get('name', f'{key[0]} — page {key[1]+1}'),
                          'pages': pages})
    return conflicts


def apply_binding_choices(witness, plan, selections):
    """All-or-nothing application of explicitly chosen preview rows.

    ``selections`` maps image page IDs to (source_id, page_index), or None.
    Existing manually associated pages, or sources occupied by them, may
    NEVER be modified through a batch plan.
    """
    if binding_fingerprint(witness) != plan['fingerprint']:
        raise ValueError('Les ressources ont changé depuis la prévisualisation. Recalculer les propositions.')
    permitted = {(x['source_id'], x['page_index']) for x in plan['available']}
    image_ids = {x['page_id'] for x in plan['rows']}
    by_id = {p['id']: p for p in witness.get('pages', [])}
    selected = []
    for page_id, target in selections.items():
        if page_id not in image_ids or page_id not in by_id or by_id[page_id].get('alto_binding'):
            raise ValueError('Page indisponible ou déjà associée')
        if target is None:
            continue
        target = tuple(target)
        if target not in permitted:
            raise ValueError('Source XML indisponible ou déjà utilisée')
        selected.append((page_id, target))
    conflicts = binding_selection_conflicts(plan, selections, witness)
    if conflicts:
        details = '; '.join(
            f"{conflict['xml']} → {', '.join(p['label'] for p in conflict['pages'])}"
            for conflict in conflicts)
        raise localized(ValueError, 'error.binding.xml_page_twice', details=details)
    # Everything has been checked: modifying the page dictionaries is safe.
    # A page bound to another XML loses the reading order made for its old lines.
    from .reading_stream import rebind_page
    for pid, (source_id, index) in selected:
        rebind_page(witness, pid, source_id, index)
    return {'associated': len(selected), 'skipped': len(selections) - len(selected)}
