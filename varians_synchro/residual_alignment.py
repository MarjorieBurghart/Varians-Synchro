"""Conservative second-pass suggestions for orphan physical manuscript lines.

The *existing* partner link is expanded only after a separate preview/commit.
This is not a transcription or a claim that texts match: a neighbouring line
may carry an omission or addition. Never auto-extend a human/validated link.
PAGE and ALTO share the physical_lines interface; neither source is modified.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite
from statistics import median
from .physical_alignment import (_witness, physical_lines, pair_indices,
                                 is_revisable_automatic, _now)


def _box(line):
    try:
        b = line['bbox']
        x, y, w, h = (float(b[k]) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
        if min(w, h) <= 0 or not all(isfinite(v) for v in (x,y,w,h)):
            return None
        return (x, y, w, h)
    except (ValueError, TypeError, KeyError, OverflowError):
        return None


def _cy(b):
    return b[1] + b[3]/2


def _overlap(a, b):
    overlap = min(a[0]+a[2], b[0]+b[2]) - max(a[0], b[0])
    return max(0., overlap) / min(a[2], b[2])


def _same_column(a, b):
    return _overlap(a, b) >= .17


def _local_pitch(line, same_page):
    bbox = _box(line)
    if bbox is None:
        return None
    ys = sorted(_cy(b) for other in same_page
                if (b := _box(other)) is not None and _same_column(bbox, b))
    distances = [v-u for u,v in zip(ys, ys[1:]) if 1e-6 < v-u]
    if not distances:
        return max(bbox[3]*1.35, 1.)
    # Ignore horizontal rows belonging to another column (already filtered),
    # and very large gaps in sparse pages, if a local median is available.
    return max(1., median(distances))


def _linked_info(session, index_a, index_b, ignored_a, ignored_b, stale=frozenset()):
    """Only clean, physical correspondence groups can serve as neighbours.
    A stale group (its lines changed) is never one: extending it was refused
    at saving time, which refused the whole selection."""
    info=[]
    for link in session.get('links', []):
        ra=link.get('reference_ids', []); rb=link.get('target_ids', [])
        if link.get('kind') != 'correspondence' or not ra or not rb or link.get('id') in stale:
            continue
        if set(ra) & ignored_a or set(rb) & ignored_b:
            continue
        al=[index_a.get(uid) for uid in ra]; bl=[index_b.get(uid) for uid in rb]
        if None in al or None in bl or any(_box(x) is None for x in al+bl):
            continue
        if len({l['page_id'] for l in al})!=1 or len({l['page_id'] for l in bl})!=1:
            continue
        # Mark a link spanning two columns as unsuitable for local extensions.
        if any(not _same_column(_box(al[0]),_box(x)) for x in al[1:]):
            continue
        if any(not _same_column(_box(bl[0]),_box(x)) for x in bl[1:]):
            continue
        info.append({'link': link, 'a':al, 'b':bl})
    return info


def _nearest_group(orphan, side, groups, page_lines, max_distance=3.6):
    """Return the nearest same-column link + gap in local line pitches.

    If two equally near groups point to incompatible target pages/columns,
    refuse to infer the correspondence automatically.
    """
    box=_box(orphan)
    if box is None:
        return None, 'geometry'
    candidates=[]
    for g in groups:
        members = g[side]
        if members[0]['page_id'] != orphan['page_id']:
            continue
        choices=[_box(line) for line in members]
        choices=[b for b in choices if _same_column(box,b)]
        if not choices:
            continue
        closest=min(abs(_cy(box)-_cy(b)) for b in choices)
        pitch=_local_pitch(orphan,page_lines)
        if not pitch:
            continue
        steps=closest/pitch
        if steps<=max_distance:
            candidates.append((steps,g))
    if not candidates:
        return None, 'no-neighbour'
    candidates.sort(key=lambda item:item[0])
    if len(candidates)>1 and candidates[1][0]-candidates[0][0]<.18:
        # At near-equal distances, interpolation cannot tell which line
        # extends into this orphan: a manual anchor would resolve it.
        return None, 'ambiguous'
    return candidates[0], None


def suggest_residual_extensions(project, session, *, max_distance=3.6,
                                max_added_per_group=4):
    """Preview orphan-to-existing-group extensions, without mutating anything.

    A suggested line has no matching free line in the other witness. A strict
    same-folio, same-column neighbourhood and distance test is used instead of
    treating HTR or vertical proximity as proof of textual equivalence.
    Protected groups are reported but not offered for automatic modification.
    """
    wa=_witness(project,session['reference_witness_id'])
    wb=_witness(project,session['target_witness_id'])
    ignored_a=set(wa.get('ignored_line_ids',[]))
    ignored_b=set(wb.get('ignored_line_ids',[]))
    a={ln['id']:ln for ln in physical_lines(wa) if ln['id'] not in ignored_a}
    b={ln['id']:ln for ln in physical_lines(wb) if ln['id'] not in ignored_b}
    from .physical_alignment import stale_link_ids
    groups=_linked_info(session,a,b,ignored_a,ignored_b,stale_link_ids(project,session))
    used_a={uid for link in session.get('links',[]) for uid in link.get('reference_ids',[])}
    used_b={uid for link in session.get('links',[]) for uid in link.get('target_ids',[])}
    page_a={p:[v for v in a.values() if v['page_id']==p] for p in {v['page_id'] for v in a.values()}}
    page_b={p:[v for v in b.values() if v['page_id']==p] for p in {v['page_id'] for v in b.values()}}
    grouped={}
    diagnostics={'no_neighbour':0,'ambiguous':0,'protected':0,'unreliable':0,
                 'both_sides_open':0,'capped':0}
    for side, source, other, linked, other_linked, pages in (
        ('a',a,b,used_a,used_b,page_a), ('b',b,a,used_b,used_a,page_b)):
        opposing = 'b' if side=='a' else 'a'
        for orphan in source.values():
            if orphan['id'] in linked:
                continue
            choice, reason=_nearest_group(orphan,side,groups,
                                          pages[orphan['page_id']],max_distance)
            if choice is None:
                diagnostics['ambiguous' if reason=='ambiguous' else 'no_neighbour']+=1
                continue
            steps, g=choice
            link=g['link']
            # A free line on the partner page close to the candidate counterpart
            # is a plausible 1:1 alternative: leave it for standard interpolation.
            other_members=g[opposing]
            src_members=[_cy(_box(m)) for m in g[side]]
            source_y=_cy(_box(orphan))
            target_members=[_cy(_box(m)) for m in other_members]
            # A free target line on the OPPOSITE side of the link cannot
            # correspond to this orphan without contradicting reading order.
            # Use direction relative to the group's outermost line, not its
            # midpoint (important for existing 1:n correspondences).
            direction=(1 if source_y>max(src_members)+1e-6
                       else -1 if source_y<min(src_members)-1e-6 else 0)
            if direction==0:
                diagnostics['unreliable']+=1
                continue
            edge=max(target_members) if direction>0 else min(target_members)
            if any(free['page_id']==other_members[0]['page_id'] and
                   _box(free) is not None and
                   any(_same_column(_box(free),_box(m)) for m in other_members) and
                   0 < direction*(_cy(_box(free))-edge) <=
                   2.1*(_local_pitch(free, [v for v in other.values()
                                           if v['page_id']==free['page_id']]) or 1.)
                   for free in other.values() if free['id'] not in other_linked):
                diagnostics['both_sides_open']+=1
                continue
            if not is_revisable_automatic(link):
                diagnostics['protected']+=1
                continue
            entry=grouped.setdefault(link['id'],{
                'link_id':link['id'], 'reference_add_ids':[], 'target_add_ids':[],
                'origin':'interpolated-residual', 'state':'uncertain',
                'kind':'correspondence', 'distances':[],
                'expected_reference_ids':list(link['reference_ids']),
                'expected_target_ids':list(link['target_ids']),
                'expected_state':link.get('state'),
                'expected_origin':link.get('origin'),
                'expected_fingerprints':dict(link.get('fingerprints',{}))})
            key='reference_add_ids' if side=='a' else 'target_add_ids'
            entry[key].append(orphan['id'])
            entry['distances'].append(steps)
    suggestions=[]
    for candidate in grouped.values():
        count=len(candidate['reference_add_ids'])+len(candidate['target_add_ids'])
        if count>max_added_per_group:
            # No partial silent assignment when >4 missing lines cluster
            # around one link: propose at most the closest ones, and record it.
            diagnostics['capped']+=count-max_added_per_group
            # All additions are in order of traversal, use distances for cutoff.
            score_ids=list(zip(candidate['reference_add_ids'] + candidate['target_add_ids'],
                               ['reference_add_ids']*len(candidate['reference_add_ids'])+
                               ['target_add_ids']*len(candidate['target_add_ids']),
                               candidate['distances']))
            allowed=sorted(score_ids,key=lambda x:x[2])[:max_added_per_group]
            candidate['reference_add_ids']=[uid for uid,side,_ in allowed if side=='reference_add_ids']
            candidate['target_add_ids']=[uid for uid,side,_ in allowed if side=='target_add_ids']
            candidate['distances']=[d for _,_,d in allowed]
        candidate['expected_added_fingerprints']={uid:(a.get(uid) or b[uid])['fingerprint']
            for uid in candidate['reference_add_ids']+candidate['target_add_ids']}
        candidate['confidence']=round(max(.12,min(.48,.49-.085*max(candidate['distances']))),3)
        candidate['evidence']={'method':'orphan-neighbour-geometry-v1',
                               'maximum_distance_in_lines':round(max(candidate['distances']),3),
                               'htr_used':False}
        suggestions.append(candidate)
    suggestions.sort(key=lambda p:(p['confidence'],p['link_id']),reverse=True)
    return {'proposals':suggestions,'diagnostics':diagnostics,
            'unlinked_reference':sum(uid not in used_a for uid in a),
            'unlinked_target':sum(uid not in used_b for uid in b)}


def apply_residual_extensions(project, session, proposals):
    """Atomically add accepted orphan lines to tentative machine links only.

    The preview must be explicitly accepted by the user in the GUI. Each
    candidate contains a snapshot of the original link membership/status, so
    stale previews and conflicts abort without any partial project mutation.
    """
    if not proposals:
        return {'extended':0, 'lines_added':0}
    staged=deepcopy(session.get('links',[]))
    links={item['id']:item for item in staged}
    ia,ib=pair_indices(project,session)
    wa=_witness(project,session['reference_witness_id'])
    wb=_witness(project,session['target_witness_id'])
    ignored_a=set(wa.get('ignored_line_ids', [])); ignored_b=set(wb.get('ignored_line_ids', []))
    occupied_a={uid for link in staged for uid in link.get('reference_ids',[])}
    occupied_b={uid for link in staged for uid in link.get('target_ids',[])}
    pending_a=set();pending_b=set()
    extended=0;line_count=0
    for proposal in proposals:
        link=links.get(proposal.get('link_id'))
        if link is None or not is_revisable_automatic(link):
            raise ValueError('Le groupe a changé ou il est désormais protégé ; relancez la prévisualisation.')
        if (link.get('reference_ids')!=proposal.get('expected_reference_ids') or
            link.get('target_ids')!=proposal.get('expected_target_ids') or
            link.get('state')!=proposal.get('expected_state') or
            link.get('origin')!=proposal.get('expected_origin') or
            link.get('fingerprints',{})!=proposal.get('expected_fingerprints')):
            raise ValueError('La proposition est périmée : relancez le calcul.')
        aa=list(proposal.get('reference_add_ids',[])); bb=list(proposal.get('target_add_ids',[]))
        if not (aa or bb) or len(aa)!=len(set(aa)) or len(bb)!=len(set(bb)):
            raise ValueError('Proposition de lignes résiduelles invalide.')
        if (set(aa)&(occupied_a|pending_a|ignored_a) or
            set(bb)&(occupied_b|pending_b|ignored_b) or
            set(aa)-ia.keys() or set(bb)-ib.keys()):
            raise ValueError('La proposition contient une ligne indisponible ou déjà associée.')
        if any(link.get('fingerprints',{}).get(uid)!=(ia.get(uid) or ib[uid])['fingerprint']
               for uid in link['reference_ids']+link['target_ids']):
            raise ValueError('La source du groupe a changé depuis son alignement ; vérifiez les fichiers de segmentation.')
        if any(proposal.get('expected_added_fingerprints',{}).get(uid) != (ia.get(uid) or ib[uid])['fingerprint']
               for uid in aa+bb if uid in ia or uid in ib):
            raise ValueError('Les lignes ont changé depuis la prévisualisation ; relancez le calcul.')
        pending_a.update(aa);pending_b.update(bb)
        new_a=list(link['reference_ids'])+aa
        new_b=list(link['target_ids'])+bb
        order_a={uid:i for i,uid in enumerate(ia)}
        order_b={uid:i for i,uid in enumerate(ib)}
        new_a.sort(key=order_a.__getitem__)
        new_b.sort(key=order_b.__getitem__)
        old_origin=link.get('origin','unknown')
        evidence=deepcopy(link.get('evidence'))
        if not isinstance(evidence,dict):
            evidence={'prior_evidence':evidence} if evidence is not None else {}
        changes=list(evidence.get('residual_extensions',[]))
        changes.append({'date':_now(), 'reference_added':aa, 'target_added':bb,
                        'previous_origin':old_origin,
                        'method':'orphan-neighbour-geometry-v1'})
        evidence['residual_extensions']=changes
        link.update(reference_ids=new_a,target_ids=new_b,
                    fingerprints={uid:(ia.get(uid) or ib[uid])['fingerprint']
                                  for uid in new_a+new_b},
                    state='uncertain',origin='interpolated-residual',
                    evidence=evidence, modified=_now())
        link.pop('reviewed_at',None)
        link.pop('confidence',None)  # previous confidence cannot certify extended group
        extended+=1;line_count+=len(aa)+len(bb)
    session['links']=staged
    return {'extended':extended, 'lines_added':line_count}
