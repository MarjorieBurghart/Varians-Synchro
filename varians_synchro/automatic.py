"""Conservative, offline, deterministic TEI/HTR line alignment proposals.

No generative AI or source modification. Only unassigned intervals are eligible.
The sequence matcher detects shared textual spans, projects matched character
intervals to physical lines, and NEVER labels interpolation as verified.
"""
from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime, timezone
import re
import unicodedata
import uuid
from .alignment import base_key, get_base_lines, target_lines, _indices
from .errors import Localized, localized


def normalize(text, uv=True, ij=True):
    s = unicodedata.normalize('NFKD', text or '').casefold()
    s = ''.join(c for c in s if not unicodedata.combining(c))
    if uv: s = s.replace('v','u')
    if ij: s = s.replace('j','i')
    return re.sub(r'[^a-z0-9]+', '', s)


def _concatenate(lines, text_fn):
    """Return normalized stream + character-to-line indices."""
    chunks=[]; indices=[]
    for i, line in enumerate(lines):
        chunk=normalize(text_fn(line))
        chunks.append(chunk)
        indices.extend([i]*len(chunk))
    return ''.join(chunks), indices


def _free_spans(base, targets, session):
    """Split work into intervals between validated links and existing manual links."""
    used_b=set();used_t=set()
    for link in session.get('links',[]):
        used_b.update(link['base_keys']);used_t.update(link['target_refs'])
    return used_b,used_t


def propose_alignment(project, session, min_match=7, min_support=0.38,
                      max_window_lines=250, allow_estimates=False, targets=None):
    """Return proposed links only, without mutating project.

    Anchors are shared character spans, grouped into line-to-line components.
    SequenceMatcher is executed only on bounded windows between existing
    anchors when possible. For large unanchored inputs, a window-based
    heuristic is used and low-confidence results remain uncertain.
    """
    if min_match < 2: raise ValueError('min_match doit être >= 2')
    if not 0 <= min_support <= 1: raise ValueError('min_support doit être entre 0 et 1')
    bases=get_base_lines(project, session['base_resource_id'])
    witness=next(w for w in project['witnesses'] if w['id']==session['target_witness_id'])
    # ``targets``: the target lines in reading order, when the caller has them.
    targets=target_lines(witness) if targets is None else targets
    occupied_b, occupied_t = _free_spans(bases,targets,session)
    # Existing links delimit safe intervals: never suggest crossing any occupied line.
    bkeys=[base_key(ln) for ln in bases]
    tkeys=[ln['ref'] for ln in targets]
    fixed=[]
    for link in session.get('links',[]):
        bidx=[bkeys.index(k) for k in link['base_keys'] if k in bkeys]
        tidx=[tkeys.index(k) for k in link['target_refs'] if k in tkeys]
        if bidx and tidx:
            fixed.append((min(bidx),max(bidx),min(tidx),max(tidx)))
    fixed.sort()
    # Non-monotone or overlapping manual anchors: leave computation conservative.
    monotonic=all(fixed[i][1]<fixed[i+1][0] and fixed[i][3]<fixed[i+1][2]
                  for i in range(len(fixed)-1))
    windows=[]
    if monotonic:
        previous_b=previous_t=-1
        for b0,b1,t0,t1 in fixed:
            windows.append((previous_b+1,b0,previous_t+1,t0))
            previous_b,previous_t=b1,t1
        windows.append((previous_b+1,len(bases),previous_t+1,len(targets)))
    else:
        # Avoid trying to infer order in a known transposition.
        return {'proposals':[], 'warnings':['Ancrages non monotones : calcul automatique suspendu ; sélectionner une zone manuellement.'],
                'unmatched_base':len(bases)-len(occupied_b),'unmatched_target':len(targets)-len(occupied_t)}
    proposals=[]; warnings=[]
    for bs,be,ts,te in windows:
        # Trim occupied lines, and split any large interval in proportional blocks.
        available_b=[i for i in range(bs,be) if bkeys[i] not in occupied_b]
        available_t=[i for i in range(ts,te) if tkeys[i] not in occupied_t]
        if not available_b or not available_t: continue
        if len(available_b)>max_window_lines or len(available_t)>max_window_lines:
            warnings.append(Localized('error.automatic.large_interval', reference=len(available_b), target=len(available_t)))
        n_chunks=max(1,(max(len(available_b),len(available_t))+max_window_lines-1)//max_window_lines)
        for part in range(n_chunks):
            bi=available_b[part*len(available_b)//n_chunks:(part+1)*len(available_b)//n_chunks]
            ti=available_t[part*len(available_t)//n_chunks:(part+1)*len(available_t)//n_chunks]
            if not bi or not ti:continue
            btexts=[bases[i] for i in bi];ttexts=[targets[i] for i in ti]
            bt,bmap=_concatenate(btexts,lambda x:x.get('text',''))
            tt,tmap=_concatenate(ttexts,lambda x:x.get('text',''))
            if not bt or not tt:
                warnings.append('Un intervalle ne contient pas de texte HTR exploitable.')
                continue
            sm=SequenceMatcher(None,bt,tt,autojunk=False)
            counts=defaultdict(int)
            for block in sm.get_matching_blocks():
                if block.size < min_match: continue
                # project contiguous matching substrings onto both line sets
                for offset in range(block.size):
                    counts[(bmap[block.a+offset],tmap[block.b+offset])]+=1
            if not counts:continue
            # Construct bipartite connected components: merges line splits 1:n / n:1.
            adj_b=defaultdict(set);adj_t=defaultdict(set)
            for (b,t),hits in counts.items():
                if hits>=min_match or hits>=min(5,max(2,len(normalize(btexts[b].get('text','')))//3)):
                    adj_b[b].add(t);adj_t[t].add(b)
            seen_b=set();seen_t=set()
            for start in sorted(adj_b):
                if start in seen_b:continue
                group_b=set();group_t=set();todo=[('b',start)]
                while todo:
                    side,idx=todo.pop()
                    if side=='b':
                        if idx in seen_b:continue
                        seen_b.add(idx);group_b.add(idx)
                        todo += [('t',j) for j in adj_b[idx] if j not in seen_t]
                    else:
                        if idx in seen_t:continue
                        seen_t.add(idx);group_t.add(idx)
                        todo += [('b',j) for j in adj_t[idx] if j not in seen_b]
                if not group_t:continue
                bsorted=sorted(group_b);tsorted=sorted(group_t)
                hit=sum(counts.get((b,t),0) for b in bsorted for t in tsorted)
                length_b=sum(len(normalize(btexts[k].get('text',''))) for k in bsorted)
                length_t=sum(len(normalize(ttexts[k].get('text',''))) for k in tsorted)
                confidence=round(min(1.0, 2*hit/max(1,length_b+length_t)),3)
                state='proposed' if confidence>=min_support else 'uncertain'
                proposals.append({'base_keys':[bkeys[bi[k]] for k in bsorted],
                    'target_refs':[tkeys[ti[k]] for k in tsorted],
                    'state':state,'confidence':confidence,'origin':'automatic',
                    'kind':'correspondence','evidence_characters':hit})
    # Suppress components that could overlap in rare fragmented matching.
    accepted=[];assigned_b=set();assigned_t=set()
    for p in sorted(proposals,key=lambda p:p['confidence'],reverse=True):
        if set(p['base_keys'])&assigned_b or set(p['target_refs'])&assigned_t:continue
        assigned_b.update(p['base_keys']);assigned_t.update(p['target_refs']);accepted.append(p)
    accepted.sort(key=lambda p:bkeys.index(p['base_keys'][0]))
    return {'proposals':accepted,'warnings':warnings,
            'unmatched_base':len(set(bkeys)-occupied_b-assigned_b),
            'unmatched_target':len(set(tkeys)-occupied_t-assigned_t)}


def apply_proposals(project, session, proposals, include_uncertain=False):
    """Atomically accept non-conflicting proposals, never overwrite existing links."""
    bk,tk=_indices(project,session)
    used_b=set();used_t=set()
    for link in session.get('links',[]):
        used_b.update(link['base_keys']);used_t.update(link['target_refs'])
    accepted=[];skipped=0
    for p in proposals:
        b=list(dict.fromkeys(p['base_keys']));t=list(dict.fromkeys(p['target_refs']))
        if p['state']=='uncertain' and not include_uncertain:
            skipped+=1;continue
        if not b or not t or (set(b)-bk) or (set(t)-tk) or set(b)&used_b or set(t)&used_t:
            skipped+=1;continue
        accepted.append({'id':str(uuid.uuid4()),'base_keys':b,'target_refs':t,
                         'kind':'correspondence','state':p['state'],
                         'origin':'automatic','confidence':float(p['confidence']),
                         'modified':datetime.now(timezone.utc).isoformat()})
        used_b.update(b);used_t.update(t)
    session.setdefault('links',[]).extend(accepted)
    return {'added':len(accepted),'skipped':skipped}
