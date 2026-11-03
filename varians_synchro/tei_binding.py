"""Safe, witness-specific TEI extraction and explicit TEI↔physical line bindings.

TEI is read only. Bindings are *not* witness-to-witness correspondence links.
No '<lb/>' without the exact target @edRef is silently assigned.
Unresolved apparatus readings block bulk linking, never fabricate witness text.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from .reading_stream import reading_stream

XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
EXCLUDED = {'teiHeader', 'facsimile', 'note', 'fw', 'figure', 'standOff'}
CHOICE_PREFERENCE = ('reg', 'corr', 'expan', 'orig', 'sic', 'abbr')


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _refs(value):
    return {token.lstrip('#') for token in (value or '').split() if token.strip('#')}


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stamp(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def extract_witness_tei(path, witness_id):
    """Return only explicitly attributed lb lines and the chosen witness readings.

    `unresolved` contains editorial questions that prevent automatic binding.
    Header, notes, unselected apparat readings and unrelated witness lb are not
    mistaken for the witness's text.  A `<choice>` selects one reading only.
    """
    if not witness_id or not isinstance(witness_id, str):
        raise ValueError('Un sigle de témoin est indispensable pour lire une TEI.')
    path = Path(path)
    root = ET.parse(path).getroot()
    if _local(root.tag) not in ('TEI', 'teiCorpus'):
        raise ValueError('Le document n’est pas une édition TEI.')
    bodies = [el for el in root.iter() if _local(el.tag) == 'text']
    # A corpus with multiple independently encoded editions must not concatenate
    # unrelated texts into one physical witness sequence.
    if len(bodies) != 1:
        raise ValueError('La liaison automatique requiert un unique élément <text> TEI.')
    current_page = {'n': None, 'facs': None, 'xml_id': None}
    line = None
    lines = []
    diagnostics = []
    unqualified = 0
    ignored_other_lb = 0
    identifiers = set()

    def issue(code, message):
        diagnostics.append({'code': code, 'message': message})

    def emit_text(value):
        nonlocal line
        if line is not None and value:
            line['text'] += value

    def walk(element):
        nonlocal current_page, line, unqualified, ignored_other_lb
        tag = _local(element.tag)
        if tag in EXCLUDED:
            return
        if tag == 'app':
            readings = [child for child in element if _local(child.tag) in ('lem', 'rdg')]
            matching = [child for child in readings if witness_id in _refs(child.get('wit'))]
            # Explicit witnesses in variant branches take precedence.  A lone
            # unqualified reading is unambiguous; multiple branches without
            # matching @wit must not be mixed or guessed.
            candidates = matching if matching else (readings if len(readings) == 1 else [])
            if len(candidates) == 1:
                walk(candidates[0])
            else:
                issue('apparatus_unresolved',
                      f'Apparat sans lecture unique pour {witness_id} (xml:id={element.get(XML_ID) or "?"}).')
            # Apparat's own tail belongs to the parent context.
            return
        if tag == 'choice':
            choices = [child for child in element if _local(child.tag) in CHOICE_PREFERENCE]
            for name in CHOICE_PREFERENCE:
                selected = next((child for child in choices if _local(child.tag) == name), None)
                if selected is not None:
                    walk(selected)
                    return
            issue('choice_unresolved', 'Élément <choice> sans branche exploitable.')
            return
        if tag in ('lem', 'rdg') and element.get('wit') and witness_id not in _refs(element.get('wit')):
            return
        if tag == 'pb':
            ref = element.get('edRef')
            if not ref or witness_id in _refs(ref):
                current_page = {'n': element.get('n'), 'facs': element.get('facs'),
                                'xml_id': element.get(XML_ID)}
        if tag == 'lb':
            ref = element.get('edRef')
            if ref and witness_id in _refs(ref):
                identifier = element.get(XML_ID)
                if identifier:
                    if identifier in identifiers:
                        issue('duplicate_lb_id', f'Identifiant TEI dupliqué : {identifier}')
                    identifiers.add(identifier)
                line = {'tei_key': identifier or f'lb-{len(lines)+1:06d}',
                        'lb_id': identifier, 'ordinal': len(lines)+1, 'edRef': ref,
                        'page_label': current_page['n'],
                        'page_id': (current_page['facs'] or current_page['xml_id'] or 'unpaged').lstrip('#'),
                        'text': ''}
                lines.append(line)
            elif not ref:
                unqualified += 1
            else:
                ignored_other_lb += 1
        if element.text:
            emit_text(element.text)
        for child in element:
            walk(child)
            if child.tail:
                emit_text(child.tail)

    walk(bodies[0])
    for item in lines:
        item['text'] = re.sub(r'\s+', ' ', item['text']).strip()
    if unqualified:
        issue('unattributed_lb', f'{unqualified} <lb/> sans @edRef : exclus du témoin {witness_id}.')
    if not lines:
        issue('no_target_lb', f'Aucun <lb edRef="#{witness_id}"/> trouvé.')
    return {'path': str(path.resolve()), 'source_sha256': _digest(path),
            'witness_id': witness_id, 'lines': lines, 'diagnostics': diagnostics,
            'ignored_other_witness_lb': ignored_other_lb,
            'blocking': any(x['code'] in ('apparatus_unresolved', 'choice_unresolved',
                                          'duplicate_lb_id', 'no_target_lb') for x in diagnostics)}


def _resource(project, witness_id, resource_id):
    if witness_id not in {w['id'] for w in project.get('witnesses', [])}:
        raise ValueError('Témoin inconnu.')
    matches = [r for r in project.get('text_resources', []) if r.get('kind') == 'tei'
               and r.get('witness_id') == witness_id and r.get('id') == resource_id]
    if len(matches) != 1:
        raise ValueError('Édition TEI absente de ce témoin.')
    return matches[0]


def preview_tei_binding(project, witness_id, resource_id):
    """Compute a read-only positional proposal AFTER explicit scope definition.

    Equal numbers of active physical lines and TEI @edRef lb are required.
    This is a preview, not editorial certification.  The signature protects
    against changed XML, page order, ignored lines or source segmentation.
    """
    resource = _resource(project, witness_id, resource_id)
    witness = next(w for w in project['witnesses'] if w['id'] == witness_id)
    extracted = extract_witness_tei(resource['path'], witness_id)
    stream = reading_stream(witness, include_ignored=False)
    physical = [{'id': l['id'], 'page_id': l['page_id'], 'page_label': l['page_label'],
                 'ordinal': l['ordinal'], 'fingerprint': l['fingerprint']}
                for l in stream]
    diagnostics = list(extracted['diagnostics'])
    if resource.get('source_sha256') and resource['source_sha256'] != extracted['source_sha256']:
        diagnostics.append({'code':'tei_source_changed',
                            'message':'Le fichier TEI a changé depuis son import : réimportez-le avant de lier.'})
    if len(physical) != len(extracted['lines']):
        diagnostics.append({'code':'line_count_mismatch',
                            'message':f'{len(extracted["lines"])} <lb/> TEI pour {len(physical)} lignes physiques actives.'})
    if not physical:
        diagnostics.append({'code':'no_physical_lines', 'message':'Aucune ligne ALTO/PAGE active.'})
    pairs = [{'tei_key': t['tei_key'], 'tei_ordinal': t['ordinal'], 'tei_text': t['text'],
              'physical_line_id': p['id'], 'physical_fingerprint': p['fingerprint'],
              'page_id': p['page_id'], 'page_label': p['page_label'], 'physical_ordinal': p['ordinal']}
             for t,p in zip(extracted['lines'], physical)]
    blocker_codes = {'tei_source_changed', 'line_count_mismatch', 'no_physical_lines'}
    eligible = not extracted['blocking'] and not any(x['code'] in blocker_codes for x in diagnostics)
    signature = _stamp({'tei_hash': extracted['source_sha256'], 'physical':physical,
                        'ignored_line_ids': sorted(witness.get('ignored_line_ids', [])),
                        'tei_resource_id':resource_id, 'witness_id':witness_id,
                        'source_hash_at_import':resource.get('source_sha256')})
    return {'witness_id':witness_id, 'resource_id':resource_id,
            'tei_count':len(extracted['lines']), 'physical_count':len(physical),
            'tei_lines':extracted['lines'], 'pairs':pairs, 'diagnostics': diagnostics,
            'eligible':eligible, 'signature':signature,
            'source_sha256':extracted['source_sha256']}


def apply_tei_binding(project, witness_id, resource_id, preview, *, replace=False):
    """Atomically commit a fresh, eligible preview without altering pair links."""
    resource = _resource(project, witness_id, resource_id)
    fresh = preview_tei_binding(project, witness_id, resource_id)
    if fresh['signature'] != preview.get('signature'):
        raise ValueError('La prévisualisation TEI est périmée : actualisez-la.')
    if not fresh['eligible']:
        raise ValueError('La liaison TEI ne peut pas être validée : corrigez les diagnostics.')
    if resource.get('tei_binding') and not replace:
        raise ValueError('Une liaison TEI existe déjà. Demandez explicitement son remplacement.')
    resource['tei_binding'] = {'witness_id': witness_id,
                               'source_sha256':fresh['source_sha256'],
                               'signature':fresh['signature'],
                               'pairs': fresh['pairs']}
    resource['lines'] = fresh['tei_lines']
    resource['status'] = 'tei_aligned'
    resource.pop('warning', None)
    return {'count':len(fresh['pairs']), 'resource_id':resource_id}


def refresh_tei_source(project, witness_id, resource_id, *, replace_binding=False):
    """Explicitly re-inspect a revised TEI source; preserve prior mapping history.

    Reading/parsing is completed BEFORE any project change. Replacing a binding
    requires an explicit user confirmation at the call site.
    """
    resource = _resource(project, witness_id, resource_id)
    new = extract_witness_tei(resource['path'], witness_id)
    if resource.get('tei_binding') and not replace_binding:
        raise ValueError('Une liaison existante doit être explicitement invalidée.')
    if resource.get('tei_binding'):
        resource.setdefault('tei_binding_history', []).append(resource['tei_binding'])
        resource.pop('tei_binding', None)
    resource['source_sha256'] = new['source_sha256']
    resource['tei_line_count'] = len(new['lines'])
    resource['tei_diagnostics'] = new['diagnostics']
    resource['lines'] = []
    resource['status'] = 'tei_unaligned'
    return {'count':len(new['lines']), 'diagnostics':new['diagnostics']}


def tei_binding_status(project, witness_id, resource_id):
    """Detect stale TEI/physical linkage; never silently relink new lines."""
    resource = _resource(project, witness_id, resource_id)
    binding = resource.get('tei_binding')
    if not binding:
        return {'status':'unbound', 'count':0}
    try:
        now = preview_tei_binding(project, witness_id, resource_id)
    except (OSError, ValueError, ET.ParseError) as exc:
        return {'status':'stale', 'reason':str(exc), 'count':len(binding.get('pairs', []))}
    if now['signature'] != binding.get('signature') or not now['eligible']:
        return {'status':'stale', 'reason':'La TEI, le périmètre ou l’ordre physique ont changé.',
                'count':len(binding.get('pairs', []))}
    return {'status':'valid', 'count':len(binding['pairs'])}


def linked_tei_texts(project, witness_id):
    """Textual lookup for a *current, validated* TEI↔physical binding only.

    Returns line_uid→text; no HTR guess, no implicit stale mapping and no
    project mutation. Conflicting multiple TEI editions are not merged.
    """
    candidates = [r for r in project.get('text_resources', [])
                  if r.get('kind') == 'tei' and r.get('witness_id') == witness_id
                  and r.get('tei_binding')]
    valid = [r for r in candidates
             if tei_binding_status(project, witness_id, r['id'])['status'] == 'valid']
    if len(valid) != 1:
        return {}
    source = valid[0]
    by_key = {line['tei_key']: line.get('text', '') for line in source.get('lines', [])}
    pairs = source['tei_binding']['pairs']
    if len(by_key) != len(pairs) or any(p['tei_key'] not in by_key for p in pairs):
        return {}
    return {pair['physical_line_id']: by_key[pair['tei_key']] for pair in pairs}
