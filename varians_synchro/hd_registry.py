"""Durable, source-bound IIIF HD downloads linked to manuscript Canvas IDs.

No network requests. The registry stores where successful downloads live; it
never turns an image into a new manuscript page or replaces an IIIF source.
The original ``images.json`` remains the authoritative download receipt.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .imaging import iiif_hd_url
from .errors import Localized, localized

REGISTRY_FORMAT = 'varians-synchro-iiif-hd'


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


def inspect_hd_folder(witness: dict, directory, *, tolerate_bad_images=False) -> dict:
    """Validate a complete images.json receipt without mutating the witness.

    Bind each image to its existing Canvas and full-resolution IIIF URL, not
    file order or label. Detect missing, changed or non-JPEG files. No implicit
    disk traversal outside the chosen folder is allowed.
    """
    folder = Path(directory).expanduser().resolve(strict=True)
    if not folder.is_dir():
        raise ValueError('Dossier HD invalide')
    receipt = folder / 'images.json'
    manifest = json.loads(receipt.read_text(encoding='utf-8'))
    if manifest.get('format') != REGISTRY_FORMAT or manifest.get('witness') != witness.get('id'):
        raise ValueError('images.json ne correspond pas au témoin sélectionné')
    declared = manifest.get('pages')
    if not isinstance(declared, list) or not declared:
        raise ValueError('images.json ne décrit aucune image HD')
    current = {p['id']: p for p in witness.get('pages', []) if p.get('image_kind') == 'iiif'}
    seen_ids, seen_files, entries, problems = set(), set(), [], []
    for item in declared:
        try:
            if not isinstance(item, dict):
                raise ValueError('Entrée HD invalide')
            canvas = item.get('canvas_id')
            name = item.get('file')
            if canvas not in current or canvas in seen_ids:
                raise localized(ValueError, 'error.hd.canvas_unknown', canvas=canvas)
            if not isinstance(name, str) or name in ('', '.', '..') or Path(name).name != name or '/' in name or '\\' in name:
                raise ValueError('Nom de fichier HD dangereux ou invalide')
            if name in seen_files or not name.lower().endswith('.jpg'):
                raise ValueError('Fichier HD réutilisé ou extension non JPEG')
            source = iiif_hd_url(current[canvas])
            if item.get('iiif_image_url') != source:
                raise localized(ValueError, 'error.hd.source_changed', canvas=canvas)
            file = folder / name
            if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(folder):
                raise localized(FileNotFoundError, 'error.hd.copy_missing', name=name)
            size = file.stat().st_size
            with file.open('rb') as stream:
                signature = stream.read(3)
            if size < 3 or signature != b'\xff\xd8\xff':
                raise localized(ValueError, 'error.hd.not_jpeg', name=name)
            if item.get('size_bytes') != size:
                raise localized(ValueError, 'error.hd.size_changed', name=name)
            entries.append({'canvas_id': canvas, 'file': name, 'iiif_image_url': source,
                            'size_bytes': size, 'sha256': _sha256(file)})
            seen_ids.add(canvas)
            seen_files.add(name)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if not tolerate_bad_images:
                raise
            problems.append(str(exc))
            continue
    return {'directory': str(folder), 'pages': entries, 'problems': problems}


def register_hd_snapshot(witness: dict, batch: dict) -> dict:
    """Record a batch already validated by the background worker."""
    existing = witness.setdefault('hd_downloads', [])
    existing[:] = [b for b in existing if b.get('directory') != batch['directory']]
    existing.append(batch)
    return batch


def register_hd_folder(witness: dict, directory) -> dict:
    """Remember one *published* download batch; safe to call again."""
    batch = inspect_hd_folder(witness, directory)
    return register_hd_snapshot(witness, batch)


def local_copy_plan(witness: dict) -> dict:
    """Read-only preflight. ALL ALTO/PAGE-bound IIIF canvases are mandatory.

    Missing copies, changed IIIF sources or modified JPG bytes disable the
    ENTIRE witness's offline-copy export. Other witnesses remain independent.
    A witness without a physical segmentation is ineligible by definition.
    """
    pages = {p['id']: p for p in witness.get('pages', []) if p.get('image_kind') == 'iiif'}
    required = {p['id'] for p in pages.values() if p.get('alto_binding')}
    verified = {}
    problems = []
    for batch in witness.get('hd_downloads', []):
        folder = Path(str(batch.get('directory') or '')).expanduser()
        if not folder.is_absolute() or not folder.is_dir() or folder.is_symlink():
            problems.append('Dossier HD manquant ou non sûr : ' + str(folder))
            continue
        try:
            fresh = inspect_hd_folder(witness, folder, tolerate_bad_images=True)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            problems.append(str(folder) + ' : ' + str(exc))
            continue
        problems.extend(fresh.get('problems', []))
        # Ensure the persisted record agrees with the receipt and downloaded
        # file fingerprints. Trust neither the receipt alone nor a stale path.
        prior = {x.get('canvas_id'): x for x in batch.get('pages', [])}
        for entry in fresh['pages']:
            saved = prior.get(entry['canvas_id'])
            if not saved or saved != entry:
                problems.append('Fichier HD modifié après association : ' + entry['file'])
                continue
            verified[entry['canvas_id']] = {**entry, 'path': str(folder / entry['file'])}
    missing = sorted(required - set(verified))
    eligible = bool(required) and not missing
    return {'eligible': eligible, 'required': sorted(required), 'missing': missing,
            'available': verified if eligible else {}, 'verified_count': len(verified),
            'problems': problems}


def varians_remote_key(page: dict) -> str:
    """Compute the key used by Varians's ``iiif_local.remote_key`` cache.

    The original image source URL and Canvas URI are retained; the local path
    is only an alternate image body.
    """
    c = page.get('canvas') or {}
    image = {'canvas': c.get('id'), 'service': c.get('image_service'),
             'image': c.get('image_url'), 'iiif_version': c.get('iiif_image_version', 2),
             'width': c.get('width'), 'height': c.get('height')}
    return hashlib.sha256(json.dumps(image, sort_keys=True,
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def varians_offline_index(witness: dict, plan: dict) -> dict:
    """Build Varians 0.8.x ``varians-iiif-local-1`` index entries."""
    pages = {p['id']: p for p in witness.get('pages', []) if p.get('image_kind') == 'iiif'}
    result = {}
    for canvas, entry in plan['available'].items():
        if canvas not in pages:
            continue
        key = varians_remote_key(pages[canvas])
        name = hashlib.md5(key.encode('ascii')).hexdigest() + '.jpg'
        result[key] = {'file': name, 'source': entry['iiif_image_url'],
                       '_copy_from': entry['path']}
    return result
