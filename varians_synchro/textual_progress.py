"""V0.7.1: linear, multi-folio text-quantity alignment between human anchors.

The two streams are *declared homologous by the editor*: this module never
tries to prove equivalence through geometry or OCR.  Weight-based cuts are
only *tentative* estimates of manuscript line segmentation.

No source, existing link, line UID, or TEI is changed by previewing. Protected
links (manual / validated / absence) form immutable obstacles. Automatic groups
may be recalculated after explicit confirmation with the existing atomic writer.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from math import hypot, isfinite
from statistics import median
import unicodedata

from .physical_alignment import is_revisable_automatic, stale_link_ids
from .reading_stream import reading_stream, anchor_intervals


def _chars(text):
    """Quantitative HTR: not sequence similarity, merely useful glyph count."""
    return sum(1 for char in str(text or '') if unicodedata.category(char)[:1] in ('L', 'N'))


def _length(line):
    baseline = line.get('baseline')
    if isinstance(baseline, list) and len(baseline) >= 2:
        try:
            pts = [(float(point[0]), float(point[1])) for point in baseline]
            dist = sum(hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(pts, pts[1:]))
            if isfinite(dist) and dist > 1:
                return dist
        except (IndexError, TypeError, ValueError, OverflowError):
            pass
    box = line.get('bbox') or {}
    try:
        value = float(box.get('WIDTH', 0))
        if isfinite(value) and value > 1:
            return value
    except (TypeError, ValueError, OverflowError):
        pass
    return None


def _weights(lines):
    """Per-witness weights with HTR, geometric and uniform per-line fallback.

    Use *characters*, not words or the recognized text itself, with outlier
    guards. In a region having mixed recognized/unrecognized lines, calibrate
    geometric fallback using chars per pixel of recognized lines. If a region
    has no recognized samples, use the witness-wide ratio; if *nothing* was
    recognized, normalize widths against a region's typical line length.
    """
    if not lines:
        return [], []
    geometric = [_length(line) for line in lines]
    htr = []
    for line, geom in zip(lines, geometric):
        text = line.get('text', '') or ''
        count = _chars(text)
        # A line of garbage with tens of thousands of OCR glyphs cannot dominate
        # the entire passage. Do not reject otherwise poor OCR spellings.
        htr.append(count if 3 <= count <= 600 and len(text) <= 1200 else None)
    by_region = defaultdict(list)
    for index, line in enumerate(lines):
        by_region[(line['page_id'], str(line.get('region_id') or ''))].append(index)
    # Use reliable bounded samples to derive a regional scale; a sparse HTR
    # region falls back to a witness-wide scale, not a foreign manuscript's.
    valid_ratios = [htr[i]/geometric[i] for i in range(len(lines))
                    if htr[i] is not None and geometric[i] is not None]
    global_ratio = median(valid_ratios) if valid_ratios else None
    medians = {}
    ratios = {}
    for region, indices in by_region.items():
        widths = [geometric[i] for i in indices if geometric[i] is not None]
        medians[region] = median(widths) if widths else None
        samples = [htr[i]/geometric[i] for i in indices
                   if htr[i] is not None and geometric[i] is not None]
        ratios[region] = median(samples) if len(samples) >= 2 else global_ratio
    # If no HTR anywhere, geometrical weights relative to each region's normal
    # line width avoid arbitrary pixel resolution differences across pages.
    # (The absolute average size will cancel under per-interval normalization.)
    weights = []
    methods = []
    for i, line in enumerate(lines):
        region = (line['page_id'], str(line.get('region_id') or ''))
        width = geometric[i]
        count = htr[i]
        if count is not None:
            value, method = float(count), 'htr'
        elif width is not None:
            if ratios[region] is not None:
                value = width * ratios[region]
            else:
                value = width / (medians[region] or width)
            method = 'geometry'
        else:
            value, method = (median(weights) if weights else 1.0), 'uniform'
        weights.append(max(0.01, value))
        methods.append(method)
    return weights, methods


def _cumulative(weights):
    total = sum(weights)
    values = [0.0]
    for weight in weights:
        values.append(values[-1] + weight/total)
    values[-1] = 1.0
    return values


def _partition(a, b):
    """Simple deterministic boundary matching: O((n+m) log max(n,m)).

    The shorter sequence drives the cut positions; each of its lines is linked
    to 1 or more consecutive lines in the longer sequence. There are no ratio
    limits and no hard group-size cutoff. Every input UID appears exactly once.
    Human n:m anchors remain first-class, and editors can manually regroup.
    """
    if not a or not b:
        return []
    if len(a) <= len(b):
        primary, secondary, swapped = a, b, False
    else:
        primary, secondary, swapped = b, a, True
    w1, methods1 = _weights(primary)
    w2, methods2 = _weights(secondary)
    c1 = _cumulative(w1)
    c2 = _cumulative(w2)
    boundaries = [0]
    previous = 0
    for i in range(1, len(primary)):
        # Reserve at least one secondary line for each remaining primary line.
        lower = previous + 1
        upper = len(secondary) - (len(primary) - i)
        k = bisect_left(c2, c1[i], lo=lower, hi=upper+1)
        choices = [max(lower, min(upper, k)), max(lower, min(upper, k-1))]
        boundary = min(choices, key=lambda j: (abs(c2[j] - c1[i]), j))
        boundaries.append(boundary)
        previous = boundary
    boundaries.append(len(secondary))
    result = []
    for i, (first, last) in enumerate(zip(boundaries, boundaries[1:])):
        p = primary[i:i+1]
        s = secondary[first:last]
        if swapped:
            aa, bb = s, p
            meth_a, meth_b = methods2[first:last], methods1[i:i+1]
        else:
            aa, bb = p, s
            meth_a, meth_b = methods1[i:i+1], methods2[first:last]
        result.append({'reference_ids': [x['id'] for x in aa],
                       'target_ids': [x['id'] for x in bb],
                       'method_reference': _method(meth_a),
                       'method_target': _method(meth_b),
                       'boundary_delta': round(abs(c1[i+1]-c2[last]), 6)})
    return result


def _method(methods):
    if 'htr' in methods:
        return 'htr' if all(x == 'htr' for x in methods) else 'mixed'
    if 'geometry' in methods:
        return 'geometry' if all(x == 'geometry' for x in methods) else 'mixed'
    return 'uniform'


def _segments(project, session):
    """Split validated intervals at all fixed manual or validated groups.

    Refuse intervals with stale/crossing/partial obstacles, rather than making
    unsafe assignments. Ignore only automatically revisable proposals; those
    can be replaced *after* user confirmation. Explicit absences are reserved
    by UID (never inferred). This stage is read-only.
    """
    witnesses = {w['id']: w for w in project.get('witnesses', [])}
    a = reading_stream(witnesses[session['reference_witness_id']])
    b = reading_stream(witnesses[session['target_witness_id']])
    ai = {line['id']: i for i, line in enumerate(a)}
    bi = {line['id']: i for i, line in enumerate(b)}
    base = anchor_intervals(project, session)
    warnings = [dict(w) for w in base['warnings']]
    # anchor_intervals already excludes each locally crossed validated pair.
    # Keep other valid intervals available: one erroneous human anchor must not
    # prevent recalculation of dozens of unrelated manuscript passages.
    protected = [link for link in session.get('links', []) if not is_revisable_automatic(link)]
    stale = stale_link_ids(project, session)
    parts = []
    for interval in base['intervals']:
        first_a = [ai[uid] for uid in interval['reference_ids']]
        first_b = [bi[uid] for uid in interval['target_ids']]
        if not first_a and not first_b:
            continue
        # We know the edge anchor indexes because every interval has valid ends.
        left_anchor = next(x for x in base['anchors'] if x['id'] == interval['start_link_id'])
        right_anchor = next(x for x in base['anchors'] if x['id'] == interval['end_link_id'])
        low_a, high_a = left_anchor['ref_end']+1, right_anchor['ref_start']
        low_b, high_b = left_anchor['target_end']+1, right_anchor['target_start']
        mid = []
        excluded_a, excluded_b = set(), set()
        unsafe = False
        for link in protected:
            if link['id'] in (left_anchor['id'], right_anchor['id']):
                continue
            ids_a, ids_b = link.get('reference_ids', []), link.get('target_ids', [])
            touches_a = any(uid in ai and low_a <= ai[uid] < high_a for uid in ids_a)
            touches_b = any(uid in bi and low_b <= bi[uid] < high_b for uid in ids_b)
            if not touches_a and not touches_b:
                continue
            if (link['id'] in stale or any(uid not in ai for uid in ids_a)
                    or any(uid not in bi for uid in ids_b)):
                unsafe = True
                warnings.append({'reason': 'stale_protected_link', 'link_id': link['id']})
                continue
            indexes_a = sorted(ai[uid] for uid in ids_a)
            indexes_b = sorted(bi[uid] for uid in ids_b)
            if not all(low_a <= idx < high_a for idx in indexes_a) or not all(low_b <= idx < high_b for idx in indexes_b):
                unsafe = True
                warnings.append({'reason': 'crossing_protected_link', 'link_id': link['id']})
                continue
            if link.get('kind') == 'absence':
                excluded_a.update(indexes_a); excluded_b.update(indexes_b)
                continue
            if (link.get('kind') != 'correspondence' or not indexes_a or not indexes_b
                or indexes_a != list(range(indexes_a[0],indexes_a[-1]+1))
                or indexes_b != list(range(indexes_b[0],indexes_b[-1]+1))):
                unsafe = True
                warnings.append({'reason': 'invalid_protected_group', 'link_id': link['id']})
                continue
            mid.append((indexes_a[0], indexes_a[-1], indexes_b[0], indexes_b[-1], link['id']))
        mid.sort()
        prev_a, prev_b = low_a-1, low_b-1
        for sa, ea, sb, eb, _ in mid:
            if sa <= prev_a or sb <= prev_b:
                unsafe = True
                warnings.append({'reason': 'crossing_protected_link', 'start_link_id': interval['start_link_id']})
            prev_a, prev_b = max(prev_a, ea), max(prev_b, eb)
        if unsafe:
            continue
        anchors = [(low_a-1, low_b-1, interval['start_link_id'])]
        anchors.extend((ea, eb, uid) for sa, ea, sb, eb, uid in mid)
        # Construct consecutive segments using both START and END of groups.
        segment_starts = [(low_a, low_b, interval['start_link_id'])]
        for sa, ea, sb, eb, uid in mid:
            begin_a, begin_b, beginning = segment_starts[-1]
            parts.append((begin_a, sa, begin_b, sb, beginning, uid, excluded_a, excluded_b,
                          interval['start_link_id'], interval['end_link_id']))
            segment_starts.append((ea+1, eb+1, uid))
        begin_a, begin_b, beginning = segment_starts[-1]
        parts.append((begin_a, high_a, begin_b, high_b, beginning,
                      interval['end_link_id'], excluded_a, excluded_b,
                      interval['start_link_id'], interval['end_link_id']))
    segments = []
    for lo_a, hi_a, lo_b, hi_b, start, end, excluded_a, excluded_b, anchor_start, anchor_end in parts:
        sa = [line for i, line in enumerate(a[lo_a:hi_a], lo_a) if i not in excluded_a]
        sb = [line for i, line in enumerate(b[lo_b:hi_b], lo_b) if i not in excluded_b]
        # The segment's bounds may be a protected group inside the interval
        # (a corrected automatic group); its validated anchors are kept too.
        segments.append({'reference': sa, 'target': sb, 'start_link_id': start,
                         'end_link_id': end, 'anchor_start': anchor_start, 'anchor_end': anchor_end})
    return a, b, segments, warnings


def suggest_textual_progress(project, session):
    """Preview complete tentative matching; never infer absences or mutate.

    The editor supplies two validated homologous anchors; manual groups inside
    remain protected. All proposals are one-to-many and jointly cover each
    nonempty eligible segment. All links remain 'uncertain' after acceptance.
    """
    a, b, segments, warnings = _segments(project, session)
    # Expose active lines outside the user's homologous anchors: these are
    # not valid candidates for interpolation and should not silently vanish.
    # Existing links (including confirmed absences) already account for their
    # members; diagnose only truly unlinked peripheral lines.
    if len([l for l in session.get('links', [])
            if l.get('state') == 'validated' and l.get('kind') == 'correspondence']) < 2:
        warnings.append({'reason': 'need_two_anchors'})
    else:
        positions_a = {line['id']:i for i, line in enumerate(a)}
        positions_b = {line['id']:i for i, line in enumerate(b)}
        anchors = []
        for link in session.get('links', []):
            if link.get('state') != 'validated' or link.get('kind') != 'correspondence':
                continue
            aa = [positions_a[uid] for uid in link['reference_ids'] if uid in positions_a]
            bb = [positions_b[uid] for uid in link['target_ids'] if uid in positions_b]
            if len(aa) == len(link['reference_ids']) and len(bb) == len(link['target_ids']) and aa and bb:
                anchors.append((min(aa), max(aa), min(bb), max(bb)))
        if len(anchors) >= 2:
            linked_a = {uid for link in session.get('links', []) for uid in link.get('reference_ids', [])}
            linked_b = {uid for link in session.get('links', []) for uid in link.get('target_ids', [])}
            for side, pa, pb, limit_a, limit_b in (
                    ('start', 0, 0, min(t[0] for t in anchors), min(t[2] for t in anchors)),
                    ('end', max(t[1] for t in anchors)+1, max(t[3] for t in anchors)+1,
                     len(a), len(b))):
                left = sum(line['id'] not in linked_a for line in a[pa:limit_a])
                right = sum(line['id'] not in linked_b for line in b[pb:limit_b])
                if left or right:
                    warnings.append({'reason': 'outside_anchors_' + side,
                                     'reference_count': left, 'target_count': right})
    proposals = []
    used_a, used_b = set(), set()
    treated = 0
    for segment in segments:
        aa, bb = segment['reference'], segment['target']
        if not aa and not bb:
            continue
        if not aa or not bb:
            warnings.append({'reason': 'one_sided_gap', 'start_link_id': segment['start_link_id'],
                             'end_link_id': segment['end_link_id'],
                             'reference_count': len(aa), 'target_count': len(bb)})
            continue
        treated += 1
        for proposal in _partition(aa, bb):
            if set(proposal['reference_ids']) & used_a or set(proposal['target_ids']) & used_b:
                raise AssertionError('Overlapping tentative textual-progress groups')
            used_a.update(proposal['reference_ids'])
            used_b.update(proposal['target_ids'])
            proposals.append({
                'reference_ids': proposal['reference_ids'],
                'target_ids': proposal['target_ids'],
                'kind': 'correspondence', 'state': 'uncertain',
                'origin': 'automatic-textual-progress-v071',
                'confidence': None,
                'evidence': {'algorithm': 'cumulative-text-quantity-v1',
                             'reference_method': proposal['method_reference'],
                             'target_method': proposal['method_target'],
                             'boundary_delta': proposal['boundary_delta'],
                             'interval_start': segment['start_link_id'],
                             'interval_end': segment['end_link_id'],
                             'anchor_start': segment['anchor_start'],
                             'anchor_end': segment['anchor_end']},
            })
    return {'proposals': proposals, 'warnings': warnings,
            'eligible_intervals': len(segments), 'calculated_intervals': treated,
            'reference_covered': len(used_a), 'target_covered': len(used_b),
            'reference_total': len(a), 'target_total': len(b)}
