"""Geometry-first manuscript column matching between confirmed 1:1 anchors.

This module never assumes a transcription is correct.  A physical ALTO column
can be aligned between its first and last confirmed lines even when the ALTO
reading-order list is interleaved with other columns, text lines are ragged,
or OCR order contains small vertical inversions. The output is *suggestions*,
not validated textual equivalence; no source or confirmed link is modified.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from math import inf, isfinite
from statistics import median

from .automatic import normalize
from .i18n import tr
from .physical_alignment import physical_lines, _witness, is_revisable_automatic, stale_link_ids


def _bbox(line):
    try:
        b = line['bbox']
        x = float(b['HPOS']); y = float(b['VPOS'])
        w = float(b['WIDTH']); h = float(b['HEIGHT'])
        if not all(map(isfinite, (x, y, w, h))) or w <= 0 or h <= 0:
            return None
        return x, y, w, h
    except (KeyError, ValueError, TypeError, OverflowError):
        return None


def _center_y(b):
    return b[1] + b[3] * 0.5


def _overlap_ratio(a, b):
    """Horizontal overlap relative to the shorter of two line boxes."""
    overlap = min(a[0]+a[2], b[0]+b[2]) - max(a[0], b[0])
    return max(0., overlap) / min(a[2], b[2])


def _column_interval(lines, first_id, last_id):
    """Extract a column by image geometry, NOT by ALTO element order.

    Returns (inner_lines, normalized_midpoint_positions), or None if the two
    anchors cannot reliably delimit a column. This extraction tolerates
    indentation, irregular line lengths and small ALTO reading-order errors.
    A non-overlapping neighbouring column is not admitted, even if ALTO lines
    from that column were interleaved in document order.
    """
    index = {line['id']: line for line in lines}
    first, last = index.get(first_id), index.get(last_id)
    if first is None or last is None or first['page_id'] != last['page_id']:
        return None
    b0, b1 = _bbox(first), _bbox(last)
    if b0 is None or b1 is None:
        return None
    y0, y1 = _center_y(b0), _center_y(b1)
    if y1 <= y0 + 0.000001:
        return None

    between = []
    for line in lines:
        if line['page_id'] != first['page_id']:
            continue
        b = _bbox(line)
        if b is not None and y0 - 0.000001 <= _center_y(b) <= y1 + 0.000001:
            between.append((line, b))
    if len(between) < 2:
        return None

    # Use the wider anchor as a stable horizontal reference when possible.
    # If the two anchor boxes do not overlap (e.g. two short last lines with
    # different indentations), seek a *typical-width* text line bridging them.
    # Reject an anomalously wide line spanning two actual columns.
    widths = [box[2] for _, box in between]
    typical_width = median(widths)
    if _overlap_ratio(b0, b1) >= .08:
        band = b0 if b0[2] >= b1[2] else b1
    else:
        bridges = [box for _, box in between
                   if _overlap_ratio(box, b0) >= .10
                   and _overlap_ratio(box, b1) >= .10
                   and box[2] <= 1.85 * typical_width]
        if not bridges:
            return None
        band = min(bridges, key=lambda box: (abs(box[2] - typical_width), box[2]))

    # Ensure BOTH bounding lines belong to the same horizontal column band.
    if _overlap_ratio(band, b0) < .08 or _overlap_ratio(band, b1) < .08:
        return None

    inner = []
    for line, box in between:
        if line['id'] in (first_id, last_id):
            continue
        # A broad ornament, marginal heading or spurious full-page TextLine
        # should not swallow an adjacent column. We prefer incomplete, clearly
        # labelled proposals over a spurious 'complete' column.
        if box[2] > 1.95 * max(typical_width, band[2]):
            continue
        if _overlap_ratio(box, band) < .16:
            continue
        inner.append((line, box))

    # ALTO reading order is often unreliable when columns are detected badly;
    # the only safe geometric assumption inside two anchors is the vertical
    # order of the physical line boxes. Original stable line IDs are retained.
    inner.sort(key=lambda entry: (_center_y(entry[1]), entry[1][0], entry[0]['id']))
    span = y1 - y0
    positions = [max(0., min(1., (_center_y(box) - y0) / span)) for _,box in inner]
    return [line for line,_ in inner], positions


def _htr_similarity(a, b, aa=None, bb=None, matcher=None):
    """Similarity of the HTR texts of two groups of lines, or None below
    0.60. ``aa`` and ``bb``: their normalised texts, when already known;
    ``matcher``: a SequenceMatcher already holding ``bb[:400]`` as its
    second sequence (its analysis is then reused)."""
    if aa is None:
        aa = normalize(' '.join(x.get('text','') for x in a))
    if bb is None:
        bb = normalize(' '.join(x.get('text','') for x in b))
    if min(len(aa), len(bb)) < 12 or min(len(set(aa)), len(set(bb))) < 6:
        return None
    if matcher is None:
        matcher = SequenceMatcher(None, aa[:400], bb[:400], autojunk=False)
    else:
        matcher.set_seq1(aa[:400])
    # Both quick ratios are upper bounds of ratio(): below the threshold,
    # the full comparison cannot reach it (same result, much cheaper).
    if matcher.real_quick_ratio() < 0.60 or matcher.quick_ratio() < 0.60:
        return None
    ratio = matcher.ratio()
    return ratio if ratio >= 0.60 else None


def _partition(a, b, positions_a, positions_b):
    """Bounded monotone DP. Every candidate line is covered exactly once.

    Groups up to 3 on either side handle line-break differences without
    treating visual alignment as proof of a scribal omission. Geometry is
    dominant; HTR only breaks sufficiently nearby ties.
    """
    n, m = len(a), len(b)
    if not n or not m:
        return []
    moves = ((1,1),(1,2),(2,1),(1,3),(3,1),(2,2),(2,3),(3,2),(3,3))
    texts, matchers = {}, {}

    def text(side, lines, start, count):
        # Each run of lines is normalised once, not at every transition.
        key = (side, start, count)
        if key not in texts:
            texts[key] = normalize(' '.join(x.get('text','') for x in lines[start:start+count]))
        return texts[key]

    def matcher(start, count):
        # One comparison object per run of lines of ``b``: its analysis of
        # the text is reused for every run of ``a`` compared with it.
        key = (start, count)
        if key not in matchers:
            matchers[key] = SequenceMatcher(None, '', text('b', b, start, count)[:400], autojunk=False)
        return matchers[key]
    dp = [[inf]*(m+1) for _ in range(n+1)]
    back = {}
    dp[0][0] = 0.
    for i in range(n+1):
        for j in range(m+1):
            if dp[i][j] == inf:
                continue
            for na, nb in moves:
                if i+na > n or j+nb > m:
                    continue
                pa = positions_a[i:i+na]; pb = positions_b[j:j+nb]
                middle = abs(sum(pa)/na - sum(pb)/nb)
                span = abs((pa[-1] - pa[0]) - (pb[-1] - pb[0]))
                cost = 5.0*middle + 1.5*span + .13*(na+nb-2)
                if na > 1 and nb > 1:
                    cost += .22
                # Avoid an expensive and untrustworthy OCR comparison except
                # for already geometrically plausible candidates.
                similarity = (_htr_similarity(None, None, text('a', a, i, na), text('b', b, j, nb),
                                              matcher(j, nb))
                              if middle <= .06 else None)
                if similarity is not None:
                    cost -= .16*(similarity-.6)/.4
                value = dp[i][j]+cost
                if value < dp[i+na][j+nb]-1e-9:
                    dp[i+na][j+nb] = value
                    back[(i+na,j+nb)] = (i,j,na,nb,middle,similarity)
    if (n,m) not in back:
        return []
    out = []
    i,j = n,m
    while i or j:
        pi,pj,na,nb,delta,sim = back[(i,j)]
        out.append((pi,pj,na,nb,delta,sim))
        i,j = pi,pj
    out.reverse()
    return out


def _unlinked_segments(ainner, binner, session, *, regenerate_automatic=False):
    """Find rectangular unlinked gaps around existing 1:n/n:m link groups.

    Human links and validated suggestions are always protected barriers.
    In regeneration mode, unvalidated machine proposals are excluded from
    the barrier calculation: this permits reinterpolation of a whole column.
    Existing data remains intact until the user explicitly accepts a preview.
    If a protected group crosses a boundary, refuse the interval.
    """
    ia = {line['id']:n for n,line in enumerate(ainner)}
    ib = {line['id']:n for n,line in enumerate(binner)}
    barriers=[]
    seen_a=set(); seen_b=set()
    provisional_barriers=False
    for link in session.get('links',[]):
        if regenerate_automatic and is_revisable_automatic(link):
            continue
        ids_a=link.get('reference_ids', [])
        ids_b=link.get('target_ids', [])
        if not (set(ids_a) & ia.keys() or set(ids_b) & ib.keys()):
            continue
        if (link.get('kind')!='correspondence'
                or not ids_a or not ids_b
                or not set(ids_a).issubset(ia) or not set(ids_b).issubset(ib)):
            return None, False
        aa=sorted(ia[uid] for uid in ids_a)
        bb=sorted(ib[uid] for uid in ids_b)
        if (aa!=list(range(aa[0],aa[-1]+1))
                or bb!=list(range(bb[0],bb[-1]+1))):
            return None, False
        if seen_a.intersection(aa) or seen_b.intersection(bb):
            return None, False
        seen_a.update(aa); seen_b.update(bb)
        if link.get('state')!='validated':
            provisional_barriers=True
        barriers.append((aa[0],aa[-1],bb[0],bb[-1]))
    barriers.sort()
    segments=[]
    prev_a=prev_b=-1
    for start_a,end_a,start_b,end_b in barriers:
        if start_a<=prev_a or start_b<=prev_b:
            return None, provisional_barriers
        segments.append((prev_a+1,start_a,prev_b+1,start_b))
        prev_a=end_a; prev_b=end_b
    segments.append((prev_a+1,len(ainner),prev_b+1,len(binner)))
    return segments, provisional_barriers


def _anchor_row(line):
    b = _bbox(line)
    return _center_y(b) if b is not None else inf


def suggest_between_anchors(project, session, *, max_lines_per_side=220,
                            regenerate_automatic=False):
    """Suggest full-column geometry between verified 1↔1 anchor links.

    Unlike V0.6.6, detects columns from the page's box geometry instead of
    relying on the ALTO's raw reading-order slice. It therefore works when
    ALTO interleaves both columns or a handful of lines are out of sequence.
    Protected/manual/validated links are never touched.  With regeneration
    enabled, tentative automatic links do not prevent a new proposal from
    spanning the column. Saving replacements requires explicit user consent.
    All proposals remain 'uncertain' pending human verification.
    """
    ref_w = _witness(project, session['reference_witness_id'])
    target_w = _witness(project, session['target_witness_id'])
    ignored_a = set(ref_w.get('ignored_line_ids', []))
    ignored_b = set(target_w.get('ignored_line_ids', []))
    # Keep ignored lines out of *column detection* as well as the DP. Their
    # boxes must not bias geometry, width medians, or candidate line counts.
    a = [ln for ln in physical_lines(ref_w) if ln['id'] not in ignored_a]
    b = [ln for ln in physical_lines(target_w) if ln['id'] not in ignored_b]
    ia = {ln['id']:ln for ln in a}
    ib = {ln['id']:ln for ln in b}
    groups = {}
    warnings = []
    stale = stale_link_ids(project, session)  # lines changed: never an anchor
    for link in session.get('links', []):
        aa, bb = link.get('reference_ids', []), link.get('target_ids', [])
        if (link.get('state') == 'validated' and link.get('kind') == 'correspondence'
                and link['id'] not in stale
                and len(aa) == len(bb) == 1 and aa[0] in ia and bb[0] in ib):
            pair = (ia[aa[0]]['page_id'], ib[bb[0]]['page_id'])
            groups.setdefault(pair, []).append((aa[0], bb[0], link['id']))
    anchors = sum(map(len, groups.values()))
    if anchors < 2:
        return {'proposals': [], 'warnings': [
            tr('Il faut au moins deux associations validées 1↔1 (début et fin de colonne) dans chaque témoin.')],
            'intervals': 0, 'skipped_intervals': 0}

    proposals = []
    intervals = 0
    skipped = 0
    paired = set()
    for page_pair, anchors_on_pages in groups.items():
        anchors_on_pages.sort(key=lambda item: (_anchor_row(ia[item[0]]),
                                                _bbox(ia[item[0]])[0] if _bbox(ia[item[0]]) else inf))
        # For every anchor choose the next compatible anchor IN THE SAME
        # COLUMN, not the next item in ALTO/DOM order or in the other column.
        for start_idx, (ref_start, target_start, start_id) in enumerate(anchors_on_pages):
            candidate = None
            for ref_end, target_end, end_id in anchors_on_pages[start_idx+1:]:
                profile_a = _column_interval(a, ref_start, ref_end)
                if profile_a is None:
                    continue
                profile_b = _column_interval(b, target_start, target_end)
                if profile_b is None:
                    continue
                # The first compatible lower anchor is the segment boundary.
                candidate = (ref_end, target_end, end_id, profile_a, profile_b)
                break
            if candidate is None:
                continue
            ref_end, target_end, end_id, (ainner, positions_a), (binner, positions_b) = candidate
            positions_a = [pos for line, pos in zip(ainner, positions_a) if line['id'] not in ignored_a]
            ainner = [line for line in ainner if line['id'] not in ignored_a]
            positions_b = [pos for line, pos in zip(binner, positions_b) if line['id'] not in ignored_b]
            binner = [line for line in binner if line['id'] not in ignored_b]
            paired.update((start_id, end_id))
            if not ainner or not binner:
                if ainner or binner:
                    warnings.append(tr('Intervalle avec des lignes d’un seul côté : absence non présumée.'))
                continue
            if len(ainner) > max_lines_per_side or len(binner) > max_lines_per_side:
                skipped += 1
                warnings.append(tr('Intervalle trop étendu : ajoutez des ancrages intermédiaires.'))
                continue
            if len(ainner) > 3*len(binner) or len(binner) > 3*len(ainner):
                skipped += 1
                warnings.append(tr('Nombre de lignes trop différent entre les colonnes : vérifiez les ancrages et la segmentation ALTO.'))
                continue
            segments, provisional_barriers = _unlinked_segments(
                ainner, binner, session, regenerate_automatic=regenerate_automatic)
            if segments is None:
                skipped += 1
                warnings.append(tr('Liens existants non monotones ou traversant une limite : colonne non recalculée.'))
                continue
            if provisional_barriers:
                warnings.append(tr('Certaines zones sont délimitées par des liens encore incertains : contrôlez-les.'))
            intervals += 1
            for a0,a1,b0,b1 in segments:
                segment_a=ainner[a0:a1]; segment_b=binner[b0:b1]
                if not segment_a or not segment_b:
                    if segment_a or segment_b:
                        warnings.append(tr('Intervalle avec des lignes d’un seul côté : absence non présumée.'))
                    continue
                if len(segment_a)>3*len(segment_b) or len(segment_b)>3*len(segment_a):
                    warnings.append(tr('Nombre de lignes trop différent entre les colonnes : vérifiez les ancrages et la segmentation ALTO.'))
                    continue
                partition=_partition(segment_a,segment_b,positions_a[a0:a1],positions_b[b0:b1])
                if not partition:
                    warnings.append(tr('Impossible de proposer un alignement monotone pour cette colonne.'))
                    continue
                for i,j,na,nb,delta,sim in partition:
                    geo_score = round(max(.12, min(.60, .58-1.5*delta)), 3)
                    proposals.append({
                        'reference_ids':[line['id'] for line in segment_a[i:i+na]],
                        'target_ids':[line['id'] for line in segment_b[j:j+nb]],
                        'kind':'correspondence', 'state':'uncertain',
                        'origin':'interpolated-geometry', 'confidence':geo_score,
                        'evidence':{'anchors':[start_id,end_id], 'method':'column-geometry-v2',
                                    'htr_corrob':sim is not None, 'geometry_delta':round(delta,4)},
                    })

    revisable_count = sum(is_revisable_automatic(link) for link in session.get('links', []))
    if not intervals and not skipped:
        skipped = 1
    if anchors and not proposals:
        warnings.append(tr('Ancrages sans colonne commune exploitable : vérifiez les pages, les cadres ALTO et la position des ancrages.'))
    return {'proposals':proposals, 'warnings':list(dict.fromkeys(warnings)),
            'intervals':intervals, 'skipped_intervals':skipped,
            'revisable_links':revisable_count}
