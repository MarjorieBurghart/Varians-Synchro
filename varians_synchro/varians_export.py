"""Export physical-line sessions to the Varians alignment JSON schema.

Opening the exported project in Varians 0.9.4.6 is checked by
tests/test_varians_094_compat.py (the real Varians code reads it). Lines are
written in the witness's reading order (reading_stream).

One explicit technical reference witness is used for these export files. This
DOES NOT magically create an editorial TEI line mapping. The TEI XML <lb/>
line IDs must still be reconciled with the physical reference's page::ordinal
keys before manuscript-to-edition synchronization is guaranteed.

No network, Qt, or local source-image files are required for the export.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import hashlib
import re
import uuid
import tempfile
import os
import shutil

from .imaging import mapped_alto_page
from .page_order import ordered_pages
from .physical_alignment import physical_lines, line_uid
from .reading_stream import reading_stream
from .errors import Localized, localized


def _get_witness(project, wid):
    return next((w for w in project.get('witnesses', []) if w['id'] == wid), None)


def _image_block(page):
    kind = page.get('image_kind')
    if kind == 'local':
        # Preserve the user's original filepath as data. Paths must be relocated
        # when opening the export on a different workstation.
        return {'type': 'file', 'path': str(page.get('image_path') or ''),
                'label': str(page.get('label') or page['id'])}
    if kind == 'iiif':
        cv = page.get('canvas') or {}
        return {'type': 'iiif', 'label': str(page.get('label') or cv.get('label') or page['id']),
                'width': cv.get('width'), 'height': cv.get('height'),
                'service': cv.get('image_service'), 'image': cv.get('image_url'),
                'canvas': cv.get('id') or page.get('id'),
                'iiif_version': cv.get('iiif_image_version') or 2}
    return {'type': 'none'}


def _build_witness_cache(witness, *, base_id, base=False):
    pages, uid_to_line = [], {}
    order = 0
    ignored = set(witness.get('ignored_line_ids', []))
    # Lines follow the witness's reading order (reading_stream: page order,
    # then region and line overrides), as the TEI binding does. Varians reads
    # the pivot's lines in the order of this JSON (the nth <lb/> is the nth
    # line), and the other witnesses' lines by ``order``. Physical ``line``
    # numbers are kept: base_keys still address the same lines.
    stream = {}
    for item in reading_stream(witness, include_ignored=True):
        stream.setdefault(item['page_id'], []).append(item['id'])
    for page in ordered_pages(witness):
        source = mapped_alto_page(witness, page)
        if source is None:
            continue  # No false line geometry on unbound IIIF canvases.
        rows = []
        by_uid = {line_uid(witness['id'], page['id'], ordinal): (ordinal, src)
                  for ordinal, src in enumerate(source.get('lines', []), 1)}
        for uid in stream.get(page['id'], list(by_uid)):
            ordinal, src = by_uid[uid]
            order += 1
            box = src.get('bbox') or {}
            row = {
                'line': ordinal, 'order': order,
                'bbox': {k: float(box.get(upper, 0) or 0)
                         for k, upper in [('hpos', 'HPOS'), ('vpos', 'VPOS'),
                                          ('width', 'WIDTH'), ('height', 'HEIGHT')]},
                'alto_id': src.get('alto_id'), 'alto': src.get('text') or '',
            }
            if src.get('polygon') and len(src['polygon']) >= 3:
                row['polygon'] = src['polygon']
            if uid in ignored:
                # These are NOT part of the edited work.  Varians counts every
                # base JSON line as a required TEI <lb/>, including lines with
                # `vsynch_ignored`: exporting them created phantom <lb/> tags.
                # Preserve original page identifiers and physical `line` numbers
                # for all retained rows: secondary base_keys must not shift.
                continue
            # Deliberately NO synthetic corrected/transcribed TEI reading.
            rows.append(row)
            uid_to_line[uid] = (page['id'], row)
        pages.append({'id': page['id'], 'label': page.get('label') or page['id'],
                      'alto_width': source.get('width'), 'alto_height': source.get('height'),
                      'image': _image_block(page), 'lines': rows})
    obj = {'meta': {'format': 'tei-manuscript-alignment', 'format_version': 1,
                    'witness': witness['id'], 'base_witness': base_id,
                    'role': 'base' if base else 'secondary',
                    'source': 'Varians-Synchro', 'reference_basis': 'physical-lines-in-study-scope',
                    'editorial_tei_alignment': 'NOT_ESTABLISHED'},
           'pages': pages}
    return obj, uid_to_line


def _line_fingerprint(record):
    raw = [record.get('alto_id'), record.get('bbox'), record.get('text')]
    encoded = json.dumps(raw, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _shared_pero_uuid(identifier):
    """Accept known PERO ``line_UUID`` and PAGE ``id_UUID`` identifier forms."""
    if not isinstance(identifier, str):
        return None
    match = re.fullmatch(r'(?:line|id)_([0-9A-Fa-f-]{36})', identifier)
    if not match:
        return None
    try:
        return uuid.UUID(match.group(1))
    except ValueError:
        return None


def _safe_same_segmentation_after_format_change(witness, uid, current, old_fingerprint):
    """Prove an old ALTO link still addresses the exact PAGE line.

    Strong evidence required: recover the old line's ORIGINAL fingerprint from
    embedded ALTO source metadata; same PERO UUID, same text, same geometry.
    Do not trust ordinal coincidence or text similarity alone.
    """
    new_uuid = _shared_pero_uuid(current.get('alto_id'))
    if new_uuid is None or not old_fingerprint:
        return False
    for source in witness.get('alto_sources', []):
        for page in source.get('pages', []):
            for old in page.get('lines', []):
                if _shared_pero_uuid(old.get('alto_id')) != new_uuid:
                    continue
                if _line_fingerprint(old) != old_fingerprint:
                    continue
                if old.get('text', '') != current.get('text', ''):
                    continue
                old_box, new_box = old.get('bbox') or {}, current.get('bbox') or {}
                try:
                    if any(abs(float(old_box[name])-float(new_box[name])) > 0.01
                           for name in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')):
                        continue
                except (ValueError, TypeError, KeyError):
                    continue
                return True
    return False


def _reference_health(witness, uid, known, lookup, fp):
    """Return `valid`, `per_uuid`, or `stale`; never silently remap a line."""
    if uid not in lookup or uid not in known or uid in set(witness.get('ignored_line_ids', [])):
        return 'stale'
    original = fp.get(uid)
    if not original or original == known[uid]['fingerprint']:
        return 'valid'
    if _safe_same_segmentation_after_format_change(witness, uid, known[uid], original):
        return 'per_uuid'
    return 'stale'


def witness_file_names(project):
    """{siglum: name of its files in the exports}: the XML identifier Varians
    derives from the siglum (``witness_ids``), which is also a safe file name.
    Refuses a project in which two witnesses would get the same file (case
    ignored) or a name Windows reserves; new projects refuse such sigla
    from the creation of the witness."""
    from .witness_ids import file_key, is_reserved_on_windows, witness_id_for_siglum
    names, seen = {}, {}
    for witness in project.get('witnesses', []):
        wid = witness.get('id')
        name = witness_id_for_siglum(wid) if isinstance(wid, str) else ''
        if not name or is_reserved_on_windows(wid) or file_key(wid) in seen:
            raise localized(ValueError, 'error.project_export.siglum_filename', witness=str(wid))
        seen[file_key(wid)] = wid
        names[wid] = name
    return names


def links_kept_by_uuid_continuity(project):
    """IDs of the correspondence groups the export keeps only through the
    PERO identifier continuity (an ALTO file replaced by the PAGE file of the
    same segmentation): they need the old file to prove it, and are lost
    from the export when it is removed."""
    known, lookups = {}, {}
    for witness in project.get('witnesses', []):
        lookups[witness['id']] = _build_witness_cache(witness, base_id=witness['id'])[1]
        known[witness['id']] = {row['id']: row for row in physical_lines(witness)}
    kept = set()
    for session in project.get('pair_sessions', []):
        sides = [(session.get('reference_witness_id'), 'reference_ids'),
                 (session.get('target_witness_id'), 'target_ids')]
        if any(wid not in known for wid, _ in sides):
            continue
        for link in session.get('links', []):
            if link.get('kind') != 'correspondence':
                continue
            fp = link.get('fingerprints') or {}
            health = [_reference_health(_get_witness(project, wid), uid, known[wid], lookups[wid], fp)
                      for wid, field in sides for uid in link.get(field, [])]
            if 'per_uuid' in health and 'stale' not in health:
                kept.add(link['id'])
    return kept


def _pair_for_base(project, base_id, target_id):
    candidates = [s for s in project.get('pair_sessions', [])
                  if {s.get('reference_witness_id'), s.get('target_witness_id')} == {base_id, target_id}]
    if len(candidates) > 1:
        raise localized(ValueError, 'error.export.ambiguous_sessions', reference=base_id, target=target_id)
    return candidates[0] if candidates else None


def make_varians_alignments(project, base_witness_id, *, include_uncertain=False):
    """Return {witness_id: Varians JSON}, diagnostics as a plain Python dict.

    Stale links are wholly withheld, as are links touching ignored lines.
    Only direct pair sessions with the requested base are exported. Never
    silently infer a transitive mapping via a third witness.
    """
    base = _get_witness(project, base_witness_id)
    if base is None:
        raise localized(ValueError, 'error.export.unknown_reference', witness=base_witness_id)
    caches = {}
    lookups = {}
    lines_by_uid = {}
    for witness in project.get('witnesses', []):
        data, lut = _build_witness_cache(witness, base_id=base_witness_id,
                                         base=witness['id'] == base_witness_id)
        caches[witness['id']] = data
        lookups[witness['id']] = lut
        lines_by_uid[witness['id']] = {row['id']: row for row in physical_lines(witness)}
    if not lookups[base_witness_id]:
        raise ValueError('Le témoin de base ne possède aucune ligne de segmentation liée à une image.')
    diagnostics = {'base': base_witness_id, 'include_uncertain': bool(include_uncertain),
                   'status': 'physical-reference-not-TEI', 'per_witness': {},
                   'warnings': ['Le référentiel des clés exportées est physique (page::ordinal), non une transcription TEI.'],
                   'needs_tei_line_mapping': True,
                   'ignored_lines_excluded_from_export': True}
    base_keys = {uid: f'{page_id}::{row["line"]}'
                 for uid, (page_id, row) in lookups[base_witness_id].items()}
    for witness in project.get('witnesses', []):
        wid = witness['id']
        if wid == base_witness_id:
            continue
        target = caches[wid]
        pair = _pair_for_base(project, base_witness_id, wid)
        info = Counter()
        if pair is None:
            diagnostics['warnings'].append(Localized('error.export.no_direct_session', witness=wid,
                                                     reference=base_witness_id))
        else:
            direct = pair['reference_witness_id'] == base_witness_id
            for link in pair.get('links', []):
                info['total_groups'] += 1
                if link.get('kind') != 'correspondence':
                    info['non_correspondence'] += 1
                    if link.get('kind') == 'absence' and link.get('state') == 'validated':
                        info['confirmed_absence_groups'] += 1
                        base_absent = (link.get('reference_ids', []) if direct
                                       else link.get('target_ids', []))
                        secondary_absent = (link.get('target_ids', []) if direct
                                            else link.get('reference_ids', []))
                        # These are real editorial exceptions, never base_keys.
                        info['base_side_absent_lines'] += len(base_absent)
                        info['secondary_side_absent_lines'] += len(secondary_absent)
                    continue
                if link.get('state') != 'validated' and not include_uncertain:
                    info['not_validated'] += 1
                    continue
                ref_ids = link.get('reference_ids', []) if direct else link.get('target_ids', [])
                target_ids = link.get('target_ids', []) if direct else link.get('reference_ids', [])
                if not ref_ids or not target_ids:
                    info['empty_group'] += 1
                    continue
                fp = link.get('fingerprints') or {}
                health = [_reference_health(base, uid, lines_by_uid[base_witness_id],
                                            lookups[base_witness_id], fp)
                          for uid in ref_ids]
                health += [_reference_health(witness, uid, lines_by_uid[wid],
                                             lookups[wid], fp)
                           for uid in target_ids]
                if 'stale' in health:
                    info['stale_or_ignored_group'] += 1
                    continue
                if 'per_uuid' in health:
                    info['uuid_verified_migrated_groups'] += 1
                    info['uuid_verified_migrated_references'] += health.count('per_uuid')
                keys = [base_keys[uid] for uid in ref_ids]
                # A single source group may map multiple physical lines 1<->n.
                if any('base_keys' in lookups[wid][uid][1] for uid in target_ids):
                    info['conflicting_group'] += 1
                    continue
                for uid in target_ids:
                    target_row = lookups[wid][uid][1]
                    target_row['base_keys'] = list(keys)
                    target_row['vsynch_state'] = link.get('state')
                    target_row['vsynch_origin'] = link.get('origin', '')
                    if isinstance(link.get('confidence'), (int, float)):
                        target_row['score'] = link['confidence']
                info['exported_groups'] += 1
                info['linked_target_lines'] += len(target_ids)
                info['linked_base_line_instances'] += len(ref_ids)
        diagnostics['per_witness'][wid] = dict(info)
    return caches, diagnostics




def inspect_varians_export(project, base_witness_id):
    """Read-only audit of the actual line mappings in BOTH export variants.

    Never infer a mapping from HTR or physical proximity here: if a secondary
    has zero base_keys, the cause must be diagnosed before it is used in Varians.
    The chosen *base* JSON intentionally has no base_keys of its own.
    """
    validated, valid_report = make_varians_alignments(project, base_witness_id,
                                                       include_uncertain=False)
    working, work_report = make_varians_alignments(project, base_witness_id,
                                                   include_uncertain=True)
    summary = {'base': base_witness_id, 'witnesses': {},
               'warnings': [], 'explanation': 'The base JSON has no base_keys by design.'}
    for wid in validated:
        if wid == base_witness_id:
            continue
        vc = sum(1 for page in validated[wid]['pages']
                 for line in page['lines'] if line.get('base_keys'))
        wc = sum(1 for page in working[wid]['pages']
                 for line in page['lines'] if line.get('base_keys'))
        total = sum(len(page['lines']) for page in working[wid]['pages'])
        stat = work_report['per_witness'].get(wid, {})
        reason = None
        if wc == 0:
            if _pair_for_base(project, base_witness_id, wid) is None:
                reason = 'no_direct_session'
            elif not stat.get('total_groups'):
                reason = 'no_saved_links'
            elif not stat.get('exported_groups') and stat.get('stale_or_ignored_group'):
                reason = 'stale_or_ignored'
            elif not stat.get('exported_groups') and stat.get('non_correspondence') == stat.get('total_groups'):
                reason = 'absence_only'
            else:
                reason = 'no_exportable_correspondence'
        elif vc == 0:
            reason = 'working_only'
        summary['witnesses'][wid] = {
            'total_lines': total, 'validated_linked_lines': vc,
            'working_linked_lines': wc, 'reason': reason,
            'working_diagnostics': stat,
            'validated_diagnostics': valid_report['per_witness'].get(wid, {}),
        }
        if reason:
            summary['warnings'].append({'witness': wid, 'reason': reason})
    return summary


def verify_export_payloads(payloads, base_witness_id):
    """Verify the in-memory Varians contract before writing a single file.

    Physical ``page::line`` keys must resolve to an active base line. The
    verified set is returned so the export report can document actual coverage.
    """
    if base_witness_id not in payloads:
        raise ValueError('Témoin pivot absent des fichiers JSON')
    base = payloads[base_witness_id]
    if base.get('meta', {}).get('role') != 'base':
        raise ValueError('Le témoin pivot ne porte pas le rôle attendu')
    keys = []
    for page in base['pages']:
        for line in page['lines']:
            if line.get('base_keys'):
                raise ValueError('Le témoin pivot contient des base_keys')
            keys.append(f"{page['id']}::{line['line']}")
    if len(keys) != len(set(keys)):
        raise ValueError('Clés physiques du témoin pivot non uniques')
    known = set(keys)
    rows = {}
    for wid, data in payloads.items():
        if data['meta']['base_witness'] != base_witness_id:
            raise localized(ValueError, 'error.export.inconsistent_pivot', witness=wid)
        seen = set()
        linked = 0
        for page in data['pages']:
            for line in page['lines']:
                item_key = (page['id'], line['line'])
                if item_key in seen:
                    raise localized(ValueError, 'error.export.repeated_line', witness=wid)
                seen.add(item_key)
                if wid != base_witness_id and line.get('base_keys'):
                    refs = line['base_keys']
                    if not isinstance(refs, list) or len(refs) != len(set(refs)) or not refs:
                        raise localized(ValueError, 'error.export.invalid_base_keys', witness=wid)
                    if set(refs) - known:
                        raise localized(ValueError, 'error.export.unknown_base_keys', witness=wid)
                    linked += 1
        rows[wid] = {'total_lines': len(seen), 'linked_lines': linked}
    return {'base_witness': base_witness_id, 'base_lines': len(known),
            'per_witness': rows, 'all_base_keys_resolve': True}


def export_varians_alignments(project, base_witness_id, destination):
    """Stage and validate BOTH export variants, then publish them together.

    If validation or a file write fails, the final destination is untouched.
    Existing non-empty directories are never overwritten. On Windows we move
    into place only after removing a verified EMPTY destination directory.
    """
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise FileExistsError('Destination non valide (fichier ou lien symbolique).')
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError('Choisissez un dossier vide pour éviter tout écrasement de synchronisations existantes.')
    names = witness_file_names(project)
    # ALL potentially failing domain calculations happen before disk mutation.
    packages, reports = {}, {}
    for folder, include_uncertain in [('validated', False), ('working', True)]:
        cache, report = make_varians_alignments(project, base_witness_id,
                                               include_uncertain=include_uncertain)
        report['integrity'] = verify_export_payloads(cache, base_witness_id)
        packages[folder] = cache
        reports[folder] = report
    reports['audit'] = inspect_varians_export(project, base_witness_id)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.varians-synchro-export-',
                                    dir=str(destination.parent)))
    from .core import default_mode
    os.chmod(staging, default_mode(directory=True))       # mkdtemp: 0700
    published = False
    try:
        for folder, cache in packages.items():
            sub = staging / folder
            sub.mkdir()
            for wid, data in cache.items():
                (sub / f'{names[wid]}.json').write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        (staging / 'rapport_export.json').write_text(
            json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
        # Check real serialized files, not merely the dictionary before writing.
        for folder in packages:
            parsed = {wid: json.loads((staging / folder / f'{names[wid]}.json').read_text(encoding='utf-8'))
                      for wid in packages[folder]}
            verify_export_payloads(parsed, base_witness_id)
        if destination.exists():
            if any(destination.iterdir()):
                raise FileExistsError('Le dossier de destination a été rempli pendant la préparation.')
            destination.rmdir()
        try:
            os.replace(staging, destination)
            published = True
        except OSError:
            # Restore an existing empty destination on rare filesystem errors.
            destination.mkdir(exist_ok=True)
            raise
    finally:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)
    return reports
