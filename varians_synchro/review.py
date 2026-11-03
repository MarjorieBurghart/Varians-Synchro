"""Review policy and batch operations for line alignment sessions (v0.5).

Confidence is a heuristic matching score, NEVER a scholarly verification.
All operations preserve immutable link identity and never modify source files.
"""
from __future__ import annotations
from datetime import datetime, timezone
from .alignment import get_base_lines, target_lines, base_key

STATES = {'proposed', 'uncertain', 'validated'}


def configure_session(session, mode='rigorous', threshold=.65):
    if mode not in ('rapid', 'rigorous'):
        raise ValueError('Mode invalide')
    if not isinstance(threshold, (float, int)) or not 0 <= threshold <= 1:
        raise ValueError('Seuil de confiance hors limites')
    session['review_settings'] = {'mode': mode, 'threshold': float(threshold)}
    return session['review_settings']


def prepare_proposals(proposals, mode='rigorous', threshold=.65):
    """Return copy of candidate set, with mode-dependent filtering.

    Rapid keeps even uncertain TEXTUAL candidates. It never fabricates a
    correspondence for a line where no text match exists; that would require
    a separate, explicitly marked geometric estimate engine.
    """
    if mode not in ('rapid', 'rigorous') or not 0 <= threshold <= 1:
        raise ValueError('Paramètres de révision invalides')
    results=[]
    for prop in proposals:
        c=float(prop.get('confidence', 0))
        if mode == 'rigorous' and c < threshold:
            continue
        clone=dict(prop)
        clone['base_keys']=list(prop['base_keys'])
        clone['target_refs']=list(prop['target_refs'])
        clone['state']='proposed' if c >= threshold else 'uncertain'
        results.append(clone)
    return results


def bulk_set_state(session, link_ids, state):
    """Atomic batch review. Unknown IDs cause an error without any change."""
    if state not in STATES:
        raise ValueError('Statut invalide')
    wanted=set(link_ids)
    if not wanted:
        return 0
    selected=[ln for ln in session.get('links',[]) if ln['id'] in wanted]
    if len(selected) != len(wanted):
        raise ValueError('Au moins une association sélectionnée est introuvable')
    now=datetime.now(timezone.utc).isoformat()
    for link in selected:
        link['state']=state
        link['modified']=now
        if state=='validated':
            link['reviewed_at']=now
        else:
            link.pop('reviewed_at',None)
    return len(selected)


def session_progress(project, session):
    """Coverage counts are by physical lines, not by number of link groups."""
    base=get_base_lines(project,session['base_resource_id'])
    witness=next(w for w in project['witnesses'] if w['id']==session['target_witness_id'])
    target=target_lines(witness)
    known_b={base_key(x) for x in base}
    known_t={x['ref'] for x in target}
    b_assigned=set();t_assigned=set();b_valid=set();t_valid=set()
    by_state={k:0 for k in STATES}
    by_kind={'correspondence':0,'absence':0}
    for ln in session.get('links',[]):
        b=set(ln['base_keys']);t=set(ln['target_refs'])
        if b-known_b or t-known_t:
            raise ValueError('Association périmée : lignes absentes des sources')
        b_assigned.update(b);t_assigned.update(t)
        if ln['state']=='validated':
            b_valid.update(b);t_valid.update(t)
        by_state[ln['state']]+=1
        by_kind[ln['kind']]+=1
    return {'base_total':len(known_b),'target_total':len(known_t),
            'base_covered':len(b_assigned),'target_covered':len(t_assigned),
            'base_validated':len(b_valid),'target_validated':len(t_valid),
            'base_unresolved':len(known_b-b_assigned),
            'target_unresolved':len(known_t-t_assigned),
            'links':len(session.get('links',[])),
            'by_state':by_state,'by_kind':by_kind}


def project_progress(project):
    return [{'id':s['id'],'base_witness_id':s.get('base_witness_id'),
             'target_witness_id':s['target_witness_id'],
             **session_progress(project,s)} for s in project.get('alignment_sessions',[])]
