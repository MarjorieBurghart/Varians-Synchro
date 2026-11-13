"""Manual physical-line alignments, independent of editorial XML (v0.3).

Sessions store rich links; the legacy Varians JSON is an export projection.
The application NEVER edits source TEI/ALTO files.
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from .imaging import mapped_alto_page

FORMAT = 'tei-manuscript-alignment'


def base_key(line):
    """Use the established Varians page_id::line integer contract."""
    return f"{line['page_id']}::{int(line['ordinal'])}"


def get_base_lines(project, resource_id):
    r = next((r for r in project['text_resources'] if r['id'] == resource_id), None)
    if r is None or r['kind'] != 'tei':
        raise ValueError('La référence doit être une ressource TEI importée')
    lines = r['lines']
    keys = [base_key(ln) for ln in lines]
    if len(keys) != len(set(keys)):
        raise ValueError('Lignes TEI non uniques (page + numéro)')
    return lines


def target_lines(witness):
    result = []
    seen = set()
    for page in witness.get('pages', []):
        source = mapped_alto_page(witness, page)
        if source is None: continue
        for index, line in enumerate(source.get('lines', []), 1):
            from .physical_alignment import line_uid
            if line_uid(witness['id'], page['id'], index) in witness.get('ignored_line_ids', []):
                continue
            ref = f"{page['id']}::{index}"
            if ref in seen: raise ValueError('Référence ALTO en double')
            seen.add(ref)
            result.append({'ref': ref, 'page_id': page['id'], 'page_label': page.get('label',''),
                           'line': index, 'text': line.get('text', ''), 'alto_id': line.get('alto_id'),
                           'bbox': line.get('bbox', {}), 'page': page})
    return result


def create_session(project, base_resource_id, target_witness_id):
    get_base_lines(project, base_resource_id)          # vérifie la référence (TEI importée, lignes uniques)
    witness = next((w for w in project['witnesses'] if w['id'] == target_witness_id), None)
    if witness is None: raise ValueError('Témoin cible inconnu')
    if not target_lines(witness): raise ValueError('Associez au moins un ALTO aux pages de ce témoin')
    base_res = next(r for r in project['text_resources'] if r['id'] == base_resource_id)
    if base_res.get('witness_id') == target_witness_id:
        raise ValueError('Le témoin secondaire doit être distinct de la base')
    for session in project.setdefault('alignment_sessions', []):
        if session['base_resource_id'] == base_resource_id and session['target_witness_id'] == target_witness_id:
            return session
    s = {'id': str(uuid.uuid4()), 'base_resource_id': base_resource_id,
         'target_witness_id': target_witness_id, 'base_witness_id': base_res.get('witness_id'),
         'links': [], 'created': datetime.now(timezone.utc).isoformat()}
    project['alignment_sessions'].append(s)
    return s


def _indices(project, session):
    bk = {base_key(l) for l in get_base_lines(project, session['base_resource_id'])}
    w = next(w for w in project['witnesses'] if w['id'] == session['target_witness_id'])
    tk = {l['ref'] for l in target_lines(w)}
    return bk, tk


def add_link(project, session, base_keys, target_refs, state='validated', kind='correspondence'):
    """Keep links disjoint: an explicit reassignment must first remove old links.

    Empty side is reserved for confirmed absence; not for unresolved lines.
    """
    bases = list(dict.fromkeys(base_keys)); targets = list(dict.fromkeys(target_refs))
    if not bases and not targets: raise ValueError('Sélection vide')
    if kind == 'correspondence' and (not bases or not targets):
        raise ValueError('Une correspondance exige des lignes des deux côtés')
    if kind == 'absence' and bool(bases) == bool(targets):
        raise ValueError('Une absence a exactement un côté vide')
    if kind not in ('correspondence', 'absence') or state not in ('proposed','validated','uncertain'):
        raise ValueError('Type ou statut invalide')
    known_b, known_t = _indices(project, session)
    if set(bases) - known_b or set(targets) - known_t:
        raise ValueError('Ligne inconnue dans le projet')
    for link in session['links']:
        if set(bases).intersection(link['base_keys']) or set(targets).intersection(link['target_refs']):
            raise ValueError('Ligne déjà associée : dissociez-la avant de recommencer')
    link = {'id': str(uuid.uuid4()), 'base_keys': bases, 'target_refs': targets,
            'kind': kind, 'state': state, 'origin': 'manual',
            'modified': datetime.now(timezone.utc).isoformat()}
    session['links'].append(link)
    return link


def remove_link(session, link_id):
    original = len(session['links'])
    session['links'] = [l for l in session['links'] if l['id'] != link_id]
    if len(session['links']) == original: raise ValueError('Association introuvable')


def export_varians(project, session, filename, include_proposed=True):
    """Export only physical target lines and base_keys; no invented TEI bbox.

    A base-side absence is retained in .vsynch but cannot be expressed in v1
    secondary-line JSON. The export returns a warning count.
    """
    known_b, known_t = _indices(project, session)
    w = next(w for w in project['witnesses'] if w['id'] == session['target_witness_id'])
    mapping = {}
    skipped = 0
    for link in session['links']:
        if link['state'] != 'validated' and not include_proposed:
            skipped += 1; continue
        if set(link['base_keys']) - known_b or set(link['target_refs']) - known_t:
            raise ValueError('Liens périmés : des sources ont été modifiées')
        for ref in link['target_refs']:
            if ref in mapping: raise ValueError('Ligne cible dupliquée dans les associations')
            mapping[ref] = link['base_keys']
    pages = []
    for page in w.get('pages', []):
        alto = mapped_alto_page(w, page)
        if alto is None: continue
        lines = []
        for n, line in enumerate(alto.get('lines', []), 1):
            ref = f"{page['id']}::{n}"
            bb = line.get('bbox') or {}
            def numeric(v):
                try: return float(v) if v is not None else None
                except (ValueError, TypeError): return None
            lines.append({'line': n, 'order': n, 'alto_id': line.get('alto_id'),
                          'alto': line.get('text',''),
                          'bbox': {'hpos':numeric(bb.get('HPOS')),'vpos':numeric(bb.get('VPOS')),
                                   'width':numeric(bb.get('WIDTH')),'height':numeric(bb.get('HEIGHT'))},
                          'base_keys': mapping.get(ref, [])})
        obj = {'id': page['id'], 'alto_width': numeric(alto.get('width')),
               'alto_height': numeric(alto.get('height')), 'lines': lines}
        if page['image_kind']=='iiif':
            c=page['canvas']
            obj['iiif']={'canvas_id':page['id'],'service':c.get('image_service'),
                         'image':c.get('image_url'),'width':c.get('width'),
                         'height':c.get('height'),'iiif_version':c.get('iiif_image_version'),
                         'label':page.get('label')}
        else:
            obj['local_image'] = page.get('image_path')
        pages.append(obj)
    output = {'meta': {'format': FORMAT,'format_version':1,'witness':w['id'],
                       'base_witness':session.get('base_witness_id'), 'role':'secondary'}, 'pages':pages}
    dest=Path(filename);dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_suffix(dest.suffix+'.tmp')
    try:
        temp.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(dest)
    finally:
        temp.unlink(missing_ok=True)
    return {'pages':len(pages),'lines':sum(len(p['lines']) for p in pages),
            'mapped_lines':len(mapping),'skipped_links':skipped,
            'base_absences_not_exported':sum(l['kind']=='absence' and bool(l['base_keys']) for l in session['links'])}
