"""V0.7.3: safe, explicit, pair-local confirmed textual absences.

No inference of omission from geometry or HTR. A selected passage in ONE
witness is asserted to lack a counterpart in the other witness of this pair.
Existing *uncertain automatic* groups can be partially peeled away; manual
or validated groups are never silently rewritten. Preview and commit are
separate, checked, all-or-nothing operations.
"""
from __future__ import annotations

import copy
import hashlib
import json

from .physical_alignment import (pair_indices, add_pair_link,
                                 is_revisable_automatic, _witness, _now)
from .reading_stream import reading_stream


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def _selection(project, session, side, line_ids):
    if side not in ('reference', 'target'):
        raise ValueError('Sélectionnez un témoin de la paire.')
    ids = list(dict.fromkeys(line_ids))
    if not ids or len(ids) != len(line_ids):
        raise ValueError('Sélection vide ou identifiants en double.')
    wid = session['reference_witness_id' if side == 'reference' else 'target_witness_id']
    witness = _witness(project, wid)
    known_a, known_b = pair_indices(project, session)
    known = known_a if side == 'reference' else known_b
    if set(ids) - known.keys():
        raise ValueError('Des lignes n’existent plus dans les sources ALTO/PAGE.')
    if set(ids) & set(witness.get('ignored_line_ids', [])):
        raise ValueError('Une ligne ignorée ne peut pas devenir une absence : réintégrez-la au périmètre.')
    # Reading stream is authoritative, including multi-folio groups.
    stream = reading_stream(witness, include_ignored=False)
    positions = {line['id']: i for i, line in enumerate(stream)}
    if set(ids) - positions.keys():
        raise ValueError('Une ligne est absente du flux de lecture actif.')
    return witness, sorted(ids, key=positions.__getitem__), positions, known_a, known_b


def _runs(ids, positions):
    """Separate distinct omissions; contiguous lines may cross folios."""
    output = []
    for uid in ids:
        if not output or positions[uid] != positions[output[-1][-1]] + 1:
            output.append([uid])
        else:
            output[-1].append(uid)
    return output


def preview_confirmed_absence(project, session, side, line_ids):
    """Read-only preflight; protected decisions fail with no mutation."""
    witness, ids, positions, known_a, known_b = _selection(project, session, side, line_ids)
    selected = set(ids)
    affected = [link for link in session.get('links', [])
                if selected & set(link['reference_ids' if side == 'reference' else 'target_ids'])]
    protected = [link for link in affected if not is_revisable_automatic(link)]
    if protected:
        raise ValueError(
            'La sélection touche une association manuelle, validée ou une absence existante. '
            'Dissociez explicitement cette décision avant de confirmer une absence.')
    # Check the old automatic suggestions are still attached to unchanged
    # ALTO/PAGE lines. The user should not silently rewrite stale evidence.
    for link in affected:
        for uid in link.get('reference_ids', []) + link.get('target_ids', []):
            current = known_a.get(uid) or known_b.get(uid)
            if not current or link.get('fingerprints', {}).get(uid) != current['fingerprint']:
                raise ValueError('Source ALTO/PAGE modifiée : contrôlez les groupes avant de déclarer une absence.')
    runs = _runs(ids, positions)
    watched = {uid: (known_a.get(uid) or known_b.get(uid))['fingerprint']
               for link in affected for uid in link['reference_ids'] + link['target_ids']}
    watched.update({uid: (known_a.get(uid) or known_b.get(uid))['fingerprint'] for uid in ids})
    return {
        'side': side, 'witness': witness['id'],
        'missing_in': session['target_witness_id' if side == 'reference' else 'reference_witness_id'],
        'selected_ids': ids, 'runs': runs,
        'automatic_groups_affected': len(affected),
        'new_absence_groups': len(runs),
        'fingerprints': watched,
        'session_digest': _digest(session.get('links', [])),
        'ignored_digest': _digest([
            sorted(_witness(project, session['reference_witness_id']).get('ignored_line_ids', [])),
            sorted(_witness(project, session['target_witness_id']).get('ignored_line_ids', []))]),
    }


def confirm_absence(project, session, preview):
    """Apply exactly the inspected choice, or fail without altering session.

    No automatic absence is ever inferred. This is an explicitly confirmed
    editorial assertion by the user, never an automatic suggestion.
    """
    side = preview['side']
    fresh = preview_confirmed_absence(project, session, side, preview['selected_ids'])
    if any(fresh[k] != preview[k] for k in ('side', 'witness', 'missing_in',
            'selected_ids', 'runs', 'automatic_groups_affected',
            'fingerprints', 'session_digest', 'ignored_digest')):
        raise ValueError('La prévisualisation est périmée : recommencez la vérification.')
    staged = copy.deepcopy(session)
    selected = set(preview['selected_ids'])
    remaining = []
    for link in staged.get('links', []):
        field = 'reference_ids' if side == 'reference' else 'target_ids'
        overlap = selected.intersection(link[field])
        if not overlap:
            remaining.append(link)
            continue
        # Already verified to be an unvalidated automatic proposal. Do NOT
        # mark the remainder "manual-correction": it must stay recalculable.
        link[field] = [uid for uid in link[field] if uid not in selected]
        if not link['reference_ids'] or not link['target_ids']:
            continue   # counterpart is free, never inferred absent
        ev = link.get('evidence')
        evidence = dict(ev) if isinstance(ev, dict) else {}
        evidence.setdefault('confirmed_absence_edits', []).append({
            'at': _now(), 'removed_from': side,
            'line_ids': sorted(overlap), 'missing_in': preview['missing_in'],
            'remaining_requires_review': True,
        })
        link['evidence'] = evidence
        link['fingerprints'] = {uid: fp for uid, fp in link['fingerprints'].items()
                                if uid in (link['reference_ids'] + link['target_ids'])}
        link['modified'] = _now()
        link.pop('confidence', None)
        remaining.append(link)
    staged['links'] = remaining
    created = []
    for group in preview['runs']:
        first, second = (group, []) if side == 'reference' else ([], group)
        link = add_pair_link(project, staged, first, second, state='validated',
            kind='absence', origin='manual-confirmed-absence', evidence={
                'exception': 'no-textual-counterpart',
                'missing_in': preview['missing_in'],
                'source_witness': preview['witness'],
                'explicit_user_confirmation': True,
            })
        created.append(link['id'])
    session['links'] = staged['links']
    return {'groups_created': len(created), 'line_count': len(preview['selected_ids']),
            'automatic_groups_changed': preview['automatic_groups_affected'],
            'link_ids': created, 'missing_in': preview['missing_in']}


def pair_exception_summary(project, session):
    """Counts for a specific pair, independent of the editorial pivot witness."""
    a, b = pair_indices(project, session)
    result = {'reference_absent_lines': 0, 'target_absent_lines': 0,
              'confirmed_groups': 0, 'stale_absences': 0}
    for link in session.get('links', []):
        if link.get('kind') != 'absence':
            continue
        result['confirmed_groups'] += 1
        result['reference_absent_lines'] += len(link.get('reference_ids', []))
        result['target_absent_lines'] += len(link.get('target_ids', []))
        for uid in link.get('reference_ids', []) + link.get('target_ids', []):
            current = a.get(uid) or b.get(uid)
            if (not current or link.get('fingerprints', {}).get(uid) != current['fingerprint']):
                result['stale_absences'] += 1
    return result
