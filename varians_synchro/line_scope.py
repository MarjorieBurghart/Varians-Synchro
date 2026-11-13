"""Project-wide witness ALTO scope: lines excluded from the edited work.

Ignored != unaligned != confirmed textual absence.  Only project witness
records contain ignored_line_ids; no ALTO file, source image or pair-level
setting is altered.  Existing projects need no migration.
"""
from __future__ import annotations
import copy
from .physical_alignment import physical_lines, _witness, detach_pair_lines
from .errors import localized


def ignored_ids(witness):
    return set(witness.get('ignored_line_ids', []))


def _same_line_key(line):
    return line.get('alto_id'), (line.get('text') or '').strip()


def carried_ignored_lines(witness, page_id, before, after):
    """Ignored lines of page ``page_id`` once its XML lines ``before`` are
    replaced by ``after`` (lists of XML lines; empty when the page has, or
    gets, no file). A line is known by its page and rank only: without this,
    the mark stayed on the rank and fell on whatever line took it.

    An ignored line found again in ``after`` with the same ALTO identifier
    and text keeps its mark, at its new rank; the other marks of the page are
    released. Returns (new ignored_line_ids, number of marks released)."""
    from .physical_alignment import line_uid
    ignored = list(witness.get('ignored_line_ids') or [])
    span = max(len(before), len(after))
    ranks = {line_uid(witness['id'], page_id, rank): rank for rank in range(1, span + 1)}
    on_page = [uid for uid in ignored if uid in ranks]
    if not on_page:
        return ignored, 0
    free = {}
    for rank, line in enumerate(after, 1):
        free.setdefault(_same_line_key(line), []).append(rank)
    kept = []
    for uid in on_page:
        rank = ranks[uid]
        candidates = free.get(_same_line_key(before[rank - 1])) if rank <= len(before) else None
        if candidates:
            kept.append(line_uid(witness['id'], page_id, candidates.pop(0)))
    others = [uid for uid in ignored if uid not in ranks]
    return sorted(set(others) | set(kept)), len(on_page) - len(kept)


def carry_ignored_lines(witness, page_id, before, after):
    """Apply :func:`carried_ignored_lines`; return the number of marks
    released."""
    ignored, released = carried_ignored_lines(witness, page_id, before, after)
    if ignored != list(witness.get('ignored_line_ids') or []):
        witness['ignored_line_ids'] = ignored
    return released


def linked_scope_conflicts(project, changes):
    """Count session groups affected by newly excluded physical line IDs."""
    counts = {}
    for session in project.get('pair_sessions', []):
        hit = 0
        for link in session.get('links', []):
            if (set(link.get('reference_ids', [])) & set(changes.get(session['reference_witness_id'], []))
                    or set(link.get('target_ids', [])) & set(changes.get(session['target_witness_id'], []))):
                hit += 1
        if hit:
            counts[session['id']] = hit
    return counts


def update_ignored_lines(project, changes, *, ignored=True, unlink_existing=False):
    """Apply multiple witness-scope edits atomically, across ALL pair sessions.

    `changes` maps witness IDs to ALTO physical line UIDs.  Ignoring linked
    lines requires explicit `unlink_existing=True` (the UI asks confirmation).
    Partial n:m links retain their unselected members; empty groups disappear
    without becoming fabricated absences.  All edits are staged before commit.
    """
    prepared = {}
    for wid, ids in changes.items():
        witness = _witness(project, wid)
        if witness is None:
            raise localized(ValueError, 'error.scope.unknown_witness', witness=wid)
        valid = {line['id'] for line in physical_lines(witness)}
        selected = set(ids)
        if selected - valid:
            raise localized(ValueError, 'error.scope.unknown_line', witness=wid)
        old = ignored_ids(witness)
        prepared[wid] = (old | selected) if ignored else (old - selected)
    if not prepared:
        return {'changed': 0, 'affected_groups': 0, 'deleted_groups': 0}
    effective = {wid: prepared[wid] - ignored_ids(_witness(project, wid))
                 for wid in prepared} if ignored else {}
    # Old TEI sessions are not part of the new ALTO-to-ALTO pair format.
    # If a physical line is referenced there, refuse rather than silently
    # leave an excluded line actively linked or delete editorial evidence.
    if ignored and project.get('alignment_sessions'):
        old_refs = {}
        for wid, line_ids in effective.items():
            if line_ids:
                old_refs[wid] = {f"{ln['page_id']}::{ln['ordinal']}"
                                 for ln in physical_lines(_witness(project, wid))
                                 if ln['id'] in line_ids}
        for legacy in project['alignment_sessions']:
            for link in legacy.get('links', []):
                if ((set(link.get('target_refs', [])) & old_refs.get(legacy.get('target_witness_id'), set()))
                    or (set(link.get('base_keys', [])) & old_refs.get(legacy.get('base_witness_id'), set()))):
                    raise ValueError('Cette ligne est liée à une ancienne session TEI : dissociez-la dans l’outil TEI avant de l’ignorer.')
    conflicts = linked_scope_conflicts(project, effective) if ignored else {}
    if conflicts and not unlink_existing:
        raise ValueError('Certaines lignes ont déjà des associations : confirmation de dissociation nécessaire.')
    # Only clone impacted session links. A project may contain hundreds of
    # pages and large ALTO line inventories; copying every witness is costly.
    staged = dict(project)
    staged['pair_sessions'] = [copy.deepcopy(s) if s['id'] in conflicts else s
                               for s in project.get('pair_sessions', [])]
    affected = deleted = 0
    if conflicts:
        for session in staged['pair_sessions']:
            if session['id'] not in conflicts:
                continue
            result = detach_pair_lines(
                staged, session,
                effective.get(session['reference_witness_id'], ()),
                effective.get(session['target_witness_id'], ()))
            affected += result['affected_groups']
            deleted += result['deleted_groups']
    changed = 0
    for witness in project['witnesses']:
        if witness['id'] in prepared:
            changed += len(ignored_ids(witness) ^ prepared[witness['id']])
    # Commit only after every affected pair has been successfully staged.
    for witness in project['witnesses']:
        if witness['id'] in prepared:
            witness['ignored_line_ids'] = sorted(prepared[witness['id']])
    staged_sessions = {s['id']: s for s in staged.get('pair_sessions', [])}
    for session in project.get('pair_sessions', []):
        if session['id'] in conflicts:
            session['links'] = staged_sessions[session['id']]['links']
    return {'changed': changed, 'affected_groups': affected, 'deleted_groups': deleted}
