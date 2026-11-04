"""Witness-centered project resources, with non-destructive staged import.

The physical-line alignment model is deliberately not touched.  Source files
are only inspected, never rewritten.  GUI dialogs collect selections first;
``apply_witness_draft`` commits them as one coherent project change.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from .core import (create_witness, add_image_source, add_line_source,
                   inspect_manifest, validate_project)
from .imaging import create_pages
from .page_order import _natural


def _local_key(path: str) -> str:
    return str(Path(path).expanduser().resolve()).casefold()


def _manifest_key(value: str) -> str:
    parts = urlsplit(value.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ''))


def _xml_kind(path: str) -> str:
    with open(path, 'rb') as stream:
        for _, element in ET.iterparse(stream, events=('start',)):
            return element.tag.rsplit('}', 1)[-1]
    raise ValueError(f'XML vide : {path}')


def store_tei_reference(project: dict, witness_id: str, path: str) -> dict:
    """Register a TEI resource, WITHOUT claiming lb alignment or apparatus extraction.

    Explicit TEI line mapping is a V0.8.2–0.8.3 feature. Older snapshots with
    extracted ``lines`` are preserved untouched when editing a witness.
    """
    path = str(Path(path).expanduser().resolve())
    if _xml_kind(path).lower() not in ('tei', 'teicorpus'):
        raise ValueError(f'Il ne s’agit pas d’une édition TEI : {Path(path).name}')
    for item in project['text_resources']:
        if item.get('kind') == 'tei' and item.get('witness_id') == witness_id and _local_key(item['path']) == _local_key(path):
            return item
    from .tei_binding import extract_witness_tei
    analysis = extract_witness_tei(path, witness_id)
    entry = {'kind': 'tei', 'path': path, 'witness_id': witness_id,
             'status': 'tei_unaligned', 'lines': [],
             'tei_line_count': len(analysis['lines']),
             'tei_diagnostics': analysis['diagnostics'],
             'source_sha256': analysis['source_sha256']}
    import uuid
    entry['id'] = str(uuid.uuid4())
    project['text_resources'].append(entry)
    return entry


def set_project_pivot(project: dict, witness_id: str | None) -> None:
    if witness_id is not None and witness_id not in {w['id'] for w in project['witnesses']}:
        raise ValueError('Témoin pivot introuvable')
    project['pivot_witness_id'] = witness_id


def unavailable_manifests(witness: dict) -> list[str]:
    """Adresses des Manifests IIIF du témoin qui n'ont pas répondu."""
    return [source['reference'] for source in witness.get('image_sources', [])
            if source['kind'] == 'iiif' and source.get('status') == 'unavailable']


def resource_summary(project: dict, witness_id: str) -> dict:
    w = next(w for w in project['witnesses'] if w['id'] == witness_id)
    total = len(w.get('pages', []))
    mapped = sum(bool(page.get('alto_binding')) for page in w.get('pages', []))
    return {'images': sum(s['kind'] == 'local' for s in w['image_sources']),
            'manifests': sum(s['kind'] == 'iiif' for s in w['image_sources']),
            'xml': len(w['alto_sources']),
            'tei': sum(r.get('kind') == 'tei' and r.get('witness_id') == witness_id
                       for r in project.get('text_resources', [])),
            'pages': total, 'mapped': mapped,
            'pivot': project.get('pivot_witness_id') == witness_id}


def apply_witness_draft(project: dict, *, identifier: str, label: str = '',
                        images=(), manifests=(), xml_files=(), tei_files=(),
                        is_pivot=False, manifest_loader=None) -> dict:
    """Stage and validate all resources, then atomically replace project content.

    Existing page UIDs, manual order, XML bindings, link sessions, TEI documents,
    and previous source records survive. A failed XML import changes nothing.
    A manifest fetch failure is recorded as unavailable instead of aborting the
    entire witness; giving its address again retries it (``unavailable_manifests``).
    """
    identifier = identifier.strip()
    if not identifier:
        raise ValueError('Le sigle du témoin est obligatoire')
    staged = copy.deepcopy(project)
    w = next((x for x in staged['witnesses'] if x['id'] == identifier), None)
    if w is None:
        w = create_witness(staged, identifier, label.strip() or identifier)
    elif label.strip():
        w['label'] = label.strip()

    old_page_ids = {p['id'] for p in w.get('pages', [])}
    image_inventory_changed = False
    existing_img = {_local_key(s['reference']) for s in w['image_sources'] if s['kind'] == 'local'}
    # The physical page IDs must remain unchanged for all existing images.
    for p in sorted(set(str(x) for x in images), key=lambda x: _natural(Path(x).name)):
        if not Path(p).is_file():
            raise FileNotFoundError(p)
        if _local_key(p) not in existing_img:
            add_image_source(w, 'local', str(Path(p).resolve()))
            existing_img.add(_local_key(p))
            image_inventory_changed = True

    # A manifest given again is queried again only if it had not answered.
    known_manifests = {_manifest_key(s['reference']): s for s in w['image_sources'] if s['kind'] == 'iiif'}
    for url in dict.fromkeys(str(x).strip() for x in manifests if str(x).strip()):
        entry = known_manifests.get(_manifest_key(url))
        if entry is not None and entry.get('status') != 'unavailable':
            continue
        if entry is None:
            entry = add_image_source(w, 'iiif', url)
            known_manifests[_manifest_key(url)] = entry
        try:
            entry['manifest'] = (manifest_loader or inspect_manifest)(entry['reference'])
            entry['status'] = 'inspected'
            entry.pop('error', None)
        except Exception as exc:
            entry['status'] = 'unavailable'
            entry['error'] = str(exc)
        image_inventory_changed = True

    existing_xml = {_local_key(src['path']) for src in w['alto_sources']}
    for path in sorted(set(str(x) for x in xml_files), key=lambda x: _natural(Path(x).name)):
        if _local_key(path) not in existing_xml:
            add_line_source(w, path)
            existing_xml.add(_local_key(path))

    for path in tei_files:
        store_tei_reference(staged, identifier, str(path))
    if image_inventory_changed:
        create_pages(w)
        vanished = old_page_ids - {p['id'] for p in w['pages']}
        if vanished:
            raise ValueError('Une mise à jour des images supprimerait des pages déjà enregistrées ; import annulé.')
    if is_pivot or staged.get('pivot_witness_id') is None:
        set_project_pivot(staged, identifier)
    validate_project(staged)
    # In-place update preserves the project identity shared by open views.
    project.clear()
    project.update(staged)
    return next(x for x in project['witnesses'] if x['id'] == identifier)
