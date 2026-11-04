"""Alignment between physical ALTO lines without TEI or TXT.

These sessions have no editorial base: `reference_witness_id` is a reversible
technical display/comparison choice, not an assertion about the edition.
Original ALTO and images are never edited. Legacy TEI sessions remain separate.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from .imaging import mapped_alto_page
from .page_order import ordered_pages
from .errors import Localized, localized

STATES = {'proposed', 'uncertain', 'validated'}
KINDS = {'correspondence', 'absence'}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def line_uid(witness_id, page_id, ordinal):
    """Stable as long as documentary witness/page identity and line ordinal hold."""
    raw = json.dumps([witness_id, page_id, int(ordinal)], ensure_ascii=False)
    return 'urn:vsynch:line:' + str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def physical_lines(witness):
    """Inventory only ALTO pages explicitly bound to documentary pages."""
    result = []
    seen = set()
    for page in ordered_pages(witness):
        data = mapped_alto_page(witness, page)
        if data is None:
            continue
        for ordinal, item in enumerate(data.get('lines', []), 1):
            uid = line_uid(witness['id'], page['id'], ordinal)
            if uid in seen:
                raise ValueError('Identifiants de lignes ALTO dupliqués')
            seen.add(uid)
            result.append({
                'id': uid,
                'witness_id': witness['id'],
                'page_id': page['id'],
                'page_label': page.get('label', ''),
                'ordinal': ordinal,
                'alto_id': item.get('alto_id'),
                'text': item.get('text', ''),
                'bbox': item.get('bbox', {}),
                # Additive reading/geometry metadata. Deliberately omitted from
                # fingerprint so V0.6.x correspondence integrity is unchanged.
                'region_id': item.get('region_id'),
                'region_order': item.get('region_order'),
                'polygon': item.get('polygon'),
                'baseline': item.get('baseline'),
                'fingerprint': _hash([item.get('alto_id'), item.get('bbox'), item.get('text')]),
            })
    return result


def _witness(project, identifier):
    return next((w for w in project.get('witnesses', []) if w['id'] == identifier), None)


def create_pair_session(project, reference_witness_id, target_witness_id):
    if reference_witness_id == target_witness_id:
        raise ValueError('Choisissez deux témoins distincts')
    ref = _witness(project, reference_witness_id)
    target = _witness(project, target_witness_id)
    if ref is None or target is None:
        raise ValueError('Témoin inconnu')
    if not physical_lines(ref) or not physical_lines(target):
        raise ValueError('Associez des pages ALTO aux deux témoins avant de synchroniser')
    # Pair direction is presentation only; never create a second contradictory session
    for s in project.setdefault('pair_sessions', []):
        if {s['reference_witness_id'], s['target_witness_id']} == {reference_witness_id, target_witness_id}:
            return s
    session = {
        'id': str(uuid.uuid4()), 'reference_witness_id': reference_witness_id,
        'target_witness_id': target_witness_id, 'kind': 'physical-pair',
        'links': [], 'created': _now(),
        'review_settings': {'mode': 'rigorous', 'threshold': .65},
    }
    project['pair_sessions'].append(session)
    return session


def pair_indices(project, session):
    ref = _witness(project, session['reference_witness_id'])
    target = _witness(project, session['target_witness_id'])
    if ref is None or target is None:
        raise ValueError('Un témoin de la session est absent du projet')
    return ({x['id']: x for x in physical_lines(ref)},
            {x['id']: x for x in physical_lines(target)})


def link_is_stale(link, known):
    """True when a line of ``link`` has vanished, or has changed since the
    link recorded it (its fingerprint differs): after a new segmentation of
    its page, the line at that rank is another line. ``known`` maps line
    UIDs to current physical lines. Links without recorded fingerprints
    (very old projects) are not judged, as in the export."""
    fingerprints = link.get('fingerprints') or {}
    for uid in list(link.get('reference_ids', [])) + list(link.get('target_ids', [])):
        line = known.get(uid)
        if line is None:
            return True
        if fingerprints.get(uid) is not None and fingerprints[uid] != line['fingerprint']:
            return True
    return False


def stale_link_ids(project, session):
    """IDs of the session's stale links (``link_is_stale``). They are never
    deleted: the engines leave them out of anchors and calculations, the
    export leaves them out, and the user revalidates or unlinks them."""
    known_a, known_b = pair_indices(project, session)
    known = {**known_a, **known_b}
    return {link['id'] for link in session.get('links', []) if link_is_stale(link, known)}


def _revalidation_check(project, session, link_id, known_a, known_b):
    link = next((item for item in session.get('links', []) if item['id'] == link_id), None)
    if link is None:
        raise ValueError('Association introuvable')
    members = list(link.get('reference_ids', [])) + list(link.get('target_ids', []))
    if any(uid not in known_a and uid not in known_b for uid in members):
        raise ValueError('Une ligne de ce groupe n’existe plus : dissociez-la au lieu de revalider.')
    ignored = (set(_witness(project, session['reference_witness_id']).get('ignored_line_ids', []))
               | set(_witness(project, session['target_witness_id']).get('ignored_line_ids', [])))
    if set(members) & ignored:
        raise ValueError('Réintégrez les lignes ignorées avant de les associer.')
    return link, members


def revalidate_pair_links(project, session, link_ids):
    """Human confirmation that stale links still join the right lines: their
    fingerprints are recorded again from the current lines, and they become
    validated. All or nothing: refused if a line of one of them no longer
    exists or is out of scope (that link must be unlinked). The previous
    state and fingerprints are kept in ``evidence.manual_corrections``.
    Returns the number of links revalidated."""
    known_a, known_b = pair_indices(project, session)
    checked = [_revalidation_check(project, session, link_id, known_a, known_b)
               for link_id in dict.fromkeys(link_ids)]
    for link, members in checked:
        evidence = link.get('evidence')
        evidence = dict(evidence) if isinstance(evidence, dict) else (
            {} if evidence is None else {'prior_evidence': evidence})
        corrections = list(evidence.get('manual_corrections', []))
        corrections.append({'at': _now(), 'action': 'revalidate',
                            'previous': {'state': link.get('state'),
                                         'fingerprints': dict(link.get('fingerprints') or {})}})
        evidence['manual_corrections'] = corrections
        link.update(fingerprints={uid: (known_a.get(uid) or known_b[uid])['fingerprint']
                                  for uid in members},
                    state='validated', evidence=evidence, modified=_now())
        link['reviewed_at'] = link['modified']
    return len(checked)


def revalidate_pair_link(project, session, link_id):
    """``revalidate_pair_links`` for one link; returns it."""
    revalidate_pair_links(project, session, [link_id])
    return next(item for item in session['links'] if item['id'] == link_id)


def page_links_impact(project, witness_id, page_id, source_id=None, page_index=0):
    """What a new segmentation of a page (another XML) would affect, to say
    it beforehand: links citing its current lines, in every pair session
    (``links``, ``validated``, ``by_state``), whether the page has a
    corrected reading order (``reading_order``), which would be dropped,
    and, given the new file (``source_id``, ``page_index``), how many of its
    ignored lines are not found in it and would be released
    (``ignored_lost``)."""
    witness = _witness(project, witness_id)
    if witness is None:
        raise ValueError('Témoin inconnu')
    page = next((p for p in witness.get('pages', []) if p['id'] == page_id), None)
    if page is None:
        raise ValueError('Page inconnue')
    uids = {line['id'] for line in physical_lines(witness) if line['page_id'] == page_id}
    by_state = {}
    for session in project.get('pair_sessions', []):
        for link in session.get('links', []):
            if uids & (set(link.get('reference_ids', [])) | set(link.get('target_ids', []))):
                state = link.get('state', 'uncertain')
                by_state[state] = by_state.get(state, 0) + 1
    ignored_lost = 0
    source = next((s for s in witness.get('alto_sources', []) if s['id'] == source_id), None)
    if source is not None and 0 <= page_index < len(source.get('pages', [])):
        from .line_scope import carried_ignored_lines
        before = (mapped_alto_page(witness, page) or {}).get('lines', [])
        ignored_lost = carried_ignored_lines(witness, page_id, before,
                                             source['pages'][page_index].get('lines', []))[1]
    return {'links': sum(by_state.values()), 'validated': by_state.get('validated', 0),
            'by_state': by_state,
            'reading_order': bool(page.get('reading_line_order') or page.get('reading_region_order')),
            'ignored_lost': ignored_lost}


def _link_context(project, session):
    """What ``add_pair_link`` checks a new group against: the lines of both
    witnesses, their ignored lines and the lines already linked. Computed
    once for a whole batch of proposals (it was recomputed for every group:
    minutes for a manuscript of a few thousand lines)."""
    known_a, known_b = pair_indices(project, session)
    return {'known_a': known_a, 'known_b': known_b,
            'scope_a': set(_witness(project, session['reference_witness_id']).get('ignored_line_ids', [])),
            'scope_b': set(_witness(project, session['target_witness_id']).get('ignored_line_ids', [])),
            'linked_a': {uid for link in session['links'] for uid in link['reference_ids']},
            'linked_b': {uid for link in session['links'] for uid in link['target_ids']}}


def add_pair_link(project, session, reference_ids, target_ids, *,
                  state='validated', kind='correspondence', origin='manual', confidence=None, evidence=None,
                  _context=None):
    first = list(dict.fromkeys(reference_ids))
    second = list(dict.fromkeys(target_ids))
    if state not in STATES or kind not in KINDS:
        raise ValueError('Statut ou nature de correspondance invalide')
    if kind == 'correspondence' and (not first or not second):
        raise ValueError('Une correspondance exige des lignes des deux témoins')
    if kind == 'absence' and (bool(first) == bool(second)):
        raise ValueError('Une absence exige exactement un côté sans ligne')
    context = _context if _context is not None else _link_context(project, session)
    known_a, known_b = context['known_a'], context['known_b']
    if (set(first) - set(known_a)) or (set(second) - set(known_b)):
        raise ValueError('Au moins une ligne n’existe pas dans les pages ALTO associées')
    if set(first) & context['scope_a'] or set(second) & context['scope_b']:
        raise ValueError('Réintégrez les lignes ignorées avant de les associer.')
    if set(first) & context['linked_a'] or set(second) & context['linked_b']:
        raise ValueError('Une ligne est déjà associée : dissociez-la avant de recommencer')
    link = {
        'id': str(uuid.uuid4()), 'reference_ids': first, 'target_ids': second,
        'fingerprints': {key: (known_a.get(key) or known_b.get(key))['fingerprint']
                         for key in first + second},
        'kind': kind, 'state': state, 'origin': origin, 'modified': _now(),
    }
    if confidence is not None:
        if not 0 <= float(confidence) <= 1:
            raise ValueError('Confiance hors limites')
        link['confidence'] = float(confidence)
    if evidence is not None:
        link['evidence'] = evidence
    session['links'].append(link)
    context['linked_a'].update(first)
    context['linked_b'].update(second)
    return link



def extend_pair_link(project, session, reference_ids, target_ids):
    """Extend ONE existing correspondence with as-yet-unlinked lines.

    The caller selects at least one line of the existing link plus new lines
    from either witness. Existing link identity is kept for review/navigation;
    other groups and confirmed absences are never silently merged or removed.
    Manual correction makes an uncertain automatic suggestion human-protected,
    but does not accidentally validate the entire machine-generated group.
    The update is atomic; failed validation leaves the session untouched.
    """
    first = list(dict.fromkeys(reference_ids))
    second = list(dict.fromkeys(target_ids))
    if not first or not second:
        raise ValueError('Sélectionnez des lignes dans les deux témoins, dont une déjà liée.')
    known_a, known_b = pair_indices(project, session)
    if set(first) - known_a.keys() or set(second) - known_b.keys():
        raise ValueError('Une ligne sélectionnée est absente des ALTO associés.')
    if (set(first) & set(_witness(project, session['reference_witness_id']).get('ignored_line_ids', []))
            or set(second) & set(_witness(project, session['target_witness_id']).get('ignored_line_ids', []))):
        raise ValueError('Réintégrez les lignes ignorées avant de les associer.')

    matching = [link for link in session.get('links', [])
                if set(first) & set(link['reference_ids']) or set(second) & set(link['target_ids'])]
    if not matching:
        return {'action': 'created', 'link': add_pair_link(project, session, first, second)}
    if len(matching) != 1:
        raise ValueError('La sélection touche plusieurs groupes existants. Dissociez les lignes concernées avant de les réassocier.')
    link = matching[0]
    if link.get('kind') != 'correspondence':
        raise ValueError('La ligne est marquée comme absente. Retirez d’abord cette absence confirmée.')
    if link_is_stale(link, {**known_a, **known_b}):
        # Recomputing its fingerprints here would erase the trace of the change.
        raise ValueError('Ce groupe est périmé : ses lignes ont changé depuis son '
                         'enregistrement. Revalidez-le ou dissociez-le d’abord.')
    add_a = [uid for uid in first if uid not in link['reference_ids']]
    add_b = [uid for uid in second if uid not in link['target_ids']]
    if not add_a and not add_b:
        return {'action': 'unchanged', 'link': link}

    # Group members remain in reading/document order for later use/export.
    order_a = {uid: i for i, uid in enumerate(known_a)}
    order_b = {uid: i for i, uid in enumerate(known_b)}
    updated_a = sorted(set(link['reference_ids']) | set(first), key=order_a.__getitem__)
    updated_b = sorted(set(link['target_ids']) | set(second), key=order_b.__getitem__)
    previous = {'origin': link.get('origin', 'manual'),
                'state': link.get('state', 'uncertain')}
    existing_evidence = link.get('evidence')
    if isinstance(existing_evidence, dict):
        evidence = dict(existing_evidence)
    elif existing_evidence is None:
        evidence = {}
    else:
        evidence = {'prior_evidence': existing_evidence}
    corrections = list(evidence.get('manual_corrections', []))
    corrections.append({'at': _now(), 'action': 'extend',
                        'reference_added': add_a, 'target_added': add_b,
                        'previous': previous})
    evidence['manual_corrections'] = corrections

    link.update(reference_ids=updated_a, target_ids=updated_b,
                fingerprints={uid: (known_a.get(uid) or known_b[uid])['fingerprint']
                              for uid in updated_a + updated_b},
                origin='manual-correction', evidence=evidence, modified=_now())
    # Preserve validation status; a correction must never turn uncertain
    # machine work into a certified correspondence.
    link.pop('confidence', None)  # geometric score no longer covers edited group
    if link.get('state') == 'validated':
        link['reviewed_at'] = link['modified']
    else:
        link.pop('reviewed_at', None)
    return {'action': 'extended', 'link': link, 'added_reference': len(add_a),
            'added_target': len(add_b)}


def detach_pair_lines(project, session, reference_ids=(), target_ids=()):
    """Unlink selected physical lines, keeping a valid remainder of each group.

    E.g. 1↔3 minus one target line becomes 1↔2, not an empty group or
    deletion of the unrelated two-line correspondence. If either side of a
    correspondence becomes empty, the whole group disappears; that is NOT
    recorded as evidence of textual absence. All edits are staged atomically.
    """
    first = set(reference_ids)
    second = set(target_ids)
    if not first and not second:
        raise ValueError('Sélectionnez les lignes à dissocier sur les images.')
    known_a, known_b = pair_indices(project, session)
    if first - known_a.keys() or second - known_b.keys():
        raise ValueError('Une ligne sélectionnée est absente des ALTO associés.')
    import copy
    staged = copy.deepcopy(session.get('links', []))
    affected = 0
    deleted = 0
    removed_lines = 0
    unchanged = []
    for link in staged:
        remove_a = first & set(link['reference_ids'])
        remove_b = second & set(link['target_ids'])
        if not remove_a and not remove_b:
            unchanged.append(link)
            continue
        affected += 1
        removed_lines += len(remove_a) + len(remove_b)
        next_a = [uid for uid in link['reference_ids'] if uid not in remove_a]
        next_b = [uid for uid in link['target_ids'] if uid not in remove_b]
        if ((link.get('kind') == 'correspondence' and (not next_a or not next_b))
                or (link.get('kind') == 'absence' and not (next_a or next_b))):
            deleted += 1
            continue
        ev = link.get('evidence')
        evidence = dict(ev) if isinstance(ev, dict) else ({'prior_evidence': ev} if ev is not None else {})
        corrections = list(evidence.get('manual_corrections', []))
        corrections.append({'at': _now(), 'action': 'detach-lines',
                            'reference_removed': sorted(remove_a),
                            'target_removed': sorted(remove_b),
                            'previous': {'origin': link.get('origin', 'manual'),
                                         'state': link.get('state', 'uncertain')}})
        evidence['manual_corrections'] = corrections
        link.update(reference_ids=next_a, target_ids=next_b,
                    fingerprints={uid: link.get('fingerprints', {}).get(uid)
                                  for uid in next_a + next_b},
                    origin='manual-correction', evidence=evidence, modified=_now())
        link.pop('confidence', None)
        if link.get('state') == 'validated':
            link['reviewed_at'] = link['modified']
        else:
            link.pop('reviewed_at', None)
        unchanged.append(link)
    if affected:
        session['links'] = unchanged
    return {'affected_groups': affected, 'deleted_groups': deleted,
            'removed_lines': removed_lines}


def is_revisable_automatic(link):
    """Only *unvalidated* machine proposals may be replaced by recalculation.

    A manually created link is an editorial decision, even when marked
    uncertain. An explicit validation similarly prevents recalculation.
    """
    origin = str(link.get('origin', 'manual'))
    return (link.get('kind') == 'correspondence'
            and link.get('state') != 'validated'
            and (origin.startswith('automatic-') or origin.startswith('interpolated-')))


def replace_revisable_pair_proposals(project, session, proposals):
    """Safely recompute tentative alignment without destroying human work.

    Existing automatic/uncertain groups can be removed *only when every line
    they cover on BOTH sides is covered by selected replacements*. A candidate
    touching a protected manual/validated link, or an unreplaced link, is
    skipped. The complete commit is staged and atomic at session granularity.
    Returns the added, replaced and skipped group counts.
    """
    import copy

    selected = list(proposals)
    before = session.get('links', [])
    protected = [link for link in before if not is_revisable_automatic(link)]
    revisable = [link for link in before if is_revisable_automatic(link)]

    def lines(links):
        # Lines of a set of groups, per witness: a group overlaps the set
        # when it shares a line with it (sets, not pairwise comparisons).
        return ({uid for link in links for uid in link.get('reference_ids', [])},
                {uid for link in links for uid in link.get('target_ids', [])})

    def touches(link, sides):
        return bool(set(link.get('reference_ids', [])) & sides[0]
                    or set(link.get('target_ids', [])) & sides[1])

    # Ignore malformed/unrelated candidates. Reject conflicts against any
    # protected link before deciding which machine suggestions are removable.
    protected_lines = lines(protected)
    accepted = []
    used = (set(), set())
    for p in selected:
        if (p.get('kind', 'correspondence') != 'correspondence'
                or not p.get('reference_ids') or not p.get('target_ids')
                or touches(p, protected_lines) or touches(p, used)):
            continue
        accepted.append(p)
        used[0].update(p['reference_ids'])
        used[1].update(p['target_ids'])

    # Partial manual selection must never drop lines belonging to an old
    # machine group which the new selection has not actually replaced.
    while True:
        covered_a, covered_b = lines(accepted)
        removable = [link for link in revisable
                     if (set(link['reference_ids']) <= covered_a
                         and set(link['target_ids']) <= covered_b
                         and touches(link, (covered_a, covered_b)))]
        remove_ids = {link['id'] for link in removable}
        remaining = lines([link for link in revisable if link['id'] not in remove_ids])
        safe = [p for p in accepted if not touches(p, remaining)]
        if len(safe) == len(accepted):
            break
        accepted = safe

    if not accepted:
        return {'added': 0, 'replaced': 0, 'skipped': len(selected)}

    staged = copy.deepcopy(session)
    staged['links'] = [link for link in staged.get('links', []) if link['id'] not in remove_ids]
    result = apply_pair_proposals(project, staged, accepted)
    # Invariant: either the entire recalculation succeeds or nothing changes.
    if result['added'] != len(accepted):
        raise ValueError('Recalcul interrompu : conflits entre les nouvelles correspondances.')
    session['links'] = staged['links']
    return {'added': result['added'], 'replaced': len(removable),
            'skipped': len(selected) - len(accepted)}


def remove_pair_link(session, link_id):
    initial = len(session.get('links', []))
    session['links'] = [link for link in session['links'] if link['id'] != link_id]
    if len(session['links']) == initial:
        raise ValueError('Association introuvable')


def set_pair_link_states(session, link_ids, state):
    if state not in STATES:
        raise ValueError('Statut invalide')
    desired = set(link_ids)
    matching = [l for l in session['links'] if l['id'] in desired]
    if len(matching) != len(desired):
        raise ValueError('Association introuvable : rien n’a été modifié')
    for link in matching:
        link['state'] = state
        link['modified'] = _now()
        if state == 'validated':
            link['reviewed_at'] = link['modified']
        else:
            link.pop('reviewed_at', None)
    return len(matching)


def pair_progress(project, session):
    a, b = pair_indices(project, session)
    linked_a, linked_b, validated_a, validated_b = set(), set(), set(), set()
    by_state = {state: 0 for state in sorted(STATES)}
    stale = 0
    for link in session['links']:
        ai = set(link['reference_ids']); bi = set(link['target_ids'])
        linked_a.update(ai); linked_b.update(bi)
        if link['state'] == 'validated':
            validated_a.update(ai); validated_b.update(bi)
        by_state[link['state']] += 1
        for key in ai | bi:
            line = a.get(key) or b.get(key)
            if line is None or (link.get('fingerprints', {}).get(key) is not None
                               and link['fingerprints'][key] != line['fingerprint']):
                stale += 1
    ignored_a = set(_witness(project, session['reference_witness_id']).get('ignored_line_ids', [])) & a.keys()
    ignored_b = set(_witness(project, session['target_witness_id']).get('ignored_line_ids', [])) & b.keys()
    active_a, active_b = a.keys() - ignored_a, b.keys() - ignored_b
    return {
        'reference_total': len(active_a), 'target_total': len(active_b),
        'reference_ignored': len(ignored_a), 'target_ignored': len(ignored_b),
        'reference_alto_total': len(a), 'target_alto_total': len(b),
        'reference_covered': len(linked_a & active_a), 'target_covered': len(linked_b & active_b),
        'reference_validated': len(validated_a & active_a), 'target_validated': len(validated_b & active_b),
        'reference_unresolved': len(active_a - linked_a), 'target_unresolved': len(active_b - linked_b),
        'links': len(session['links']), 'by_state': by_state,
        'stale_references': stale,
    }


def verify_pair_sessions(project):
    """Return warnings without modifying existing links after source changes."""
    alerts = []
    for session in project.get('pair_sessions', []):
        try:
            status = pair_progress(project, session)
            if status['stale_references']:
                alerts.append(Localized('error.pairs.stale_lines', reference=session['reference_witness_id'],
                                        target=session['target_witness_id'], count=status['stale_references']))
        except (ValueError, KeyError) as exc:
            alerts.append(Localized('error.pairs.session_error', session=session.get('id'), error=exc))
    return alerts


def suggest_htr_pair_alignment(project, session, min_support=.38):
    """Use the existing deterministic sequence matcher on TWO ALTO HTR streams.

    Its synthetic TEI-like reference exists only in memory. There is no TEI
    requirement, no editorial base, and no persisted artificial transcription.
    Existing manual/validated links become protected anchors.
    """
    from .automatic import propose_alignment
    from .alignment import base_key, target_lines
    ref_w = _witness(project, session['reference_witness_id'])
    target_w = _witness(project, session['target_witness_id'])
    ref_lines = [x for x in physical_lines(ref_w) if x['id'] not in ref_w.get('ignored_line_ids', [])]
    target_physical = [x for x in physical_lines(target_w) if x['id'] not in target_w.get('ignored_line_ids', [])]
    ref_legacy = [{'page_id': x['page_id'], 'ordinal': x['ordinal'], 'text': x['text']}
                  for x in ref_lines]
    key_a = {base_key(l): x['id'] for l, x in zip(ref_legacy, ref_lines)}
    key_b = {f"{x['page_id']}::{x['ordinal']}": x['id'] for x in target_physical}
    if len(key_a) != len(ref_lines) or len(key_b) != len(target_physical):
        return {'proposals': [], 'warnings': ['Clés physiques ambiguës : alignement suspendu.'],
                'unmatched_reference': len(ref_lines), 'unmatched_target': len(target_physical)}
    reverse_a = {v: k for k, v in key_a.items()}
    reverse_b = {v: k for k, v in key_b.items()}
    resource_id = '__physical_pair_reference__'
    # Avoid edits and do not leak fake resources into the persistent project.
    simulated = dict(project)
    simulated['text_resources'] = [{'id': resource_id, 'kind': 'tei', 'lines': ref_legacy}]
    protected = []
    for link in session['links']:
        protected.append({
            'base_keys': [reverse_a.get(k) for k in link['reference_ids'] if k in reverse_a],
            'target_refs': [reverse_b.get(k) for k in link['target_ids'] if k in reverse_b],
        })
    synthetic_session = {'base_resource_id': resource_id,
                         'target_witness_id': target_w['id'], 'links': protected}
    result = propose_alignment(simulated, synthetic_session, min_support=min_support,
                               max_window_lines=30)
    candidates=[]
    coarse_count = 0
    for link in result['proposals']:
        if not all(k in key_a for k in link['base_keys']) or not all(k in key_b for k in link['target_refs']):
            continue
        # Identical concatenated passages do not imply accurate line-level links.
        coarse = len(link['base_keys']) > 1 and len(link['target_refs']) > 1
        if coarse: coarse_count += 1
        candidates.append({
            'reference_ids': [key_a[k] for k in link['base_keys']],
            'target_ids': [key_b[k] for k in link['target_refs']],
            'state': 'uncertain' if coarse else link['state'],
            'confidence': link['confidence'], 'coarse': coarse,
            'origin': 'automatic-htr-htr', 'kind': 'correspondence',
        })
    warnings = list(result['warnings'])
    if coarse_count:
        warnings.append(Localized('error.htr.coarse_groups', count=coarse_count))
    return {'proposals': candidates, 'warnings': warnings,
            'unmatched_reference': result['unmatched_base'],
            'unmatched_target': result['unmatched_target']}


def apply_pair_proposals(project, session, proposals, include_uncertain=True):
    """Commit only non-conflicting candidates; never overwrite existing edits."""
    inserted=0;skipped=0
    context = _link_context(project, session)
    for proposal in proposals:
        if proposal.get('state') == 'uncertain' and not include_uncertain:
            skipped += 1;continue
        try:
            add_pair_link(project, session, proposal['reference_ids'], proposal['target_ids'],
                          state=proposal['state'], kind='correspondence',
                          origin=proposal.get('origin', 'automatic-htr-htr'),
                          confidence=proposal.get('confidence'), evidence=proposal.get('evidence'),
                          _context=context)
            inserted += 1
        except ValueError:
            skipped += 1
    return {'added': inserted, 'skipped': skipped}
