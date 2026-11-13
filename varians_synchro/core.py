"""Varians-Synchro: persistent inventory of documentary resources.

No TEI, ALTO or remote source is ever modified by the application.
Version 0.1 deliberately does not assert that page/image matches are verified.
"""
from __future__ import annotations
import json
import hashlib
import os
import shutil
import stat
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath, PureWindowsPath
from datetime import datetime, timezone
from .errors import Localized, localized

VERSION = '0.8.6.1'
SCHEMA = 'varians-synchro-project'


def new_project(name='Projet sans titre'):
    return {'format': SCHEMA, 'version': 1, 'name': name, 'created': datetime.now(timezone.utc).isoformat(),
            'witnesses': [], 'text_resources': [], 'notes': '', 'alignment_sessions': [],
            'pair_sessions': [], 'workflow_preference': 'alto_only', 'pivot_witness_id': None}


def default_mode(directory=False):
    """Droits qu'aurait un fichier (ou dossier) créé normalement, selon le
    masque de l'utilisateur. Un fichier temporaire est créé en 0600 (dossier
    en 0700) : publié tel quel, une équipe sur un partage ne pouvait pas
    lire le projet ou l'export."""
    mask = os.umask(0)
    os.umask(mask)
    return (0o777 if directory else 0o666) & ~mask


def _staged_file(destination: Path, payload: bytes | None = None) -> Path:
    """Create a private stage in the destination directory (same filesystem)."""
    fd, name = tempfile.mkstemp(prefix=f'.{destination.name}.', suffix='.tmp',
                                dir=destination.parent)
    tmp = Path(name)
    try:
        if payload is not None:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        else:
            os.close(fd)
        return tmp
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        tmp.unlink(missing_ok=True)
        raise


def save_project(project, path):
    """Save atomically with a recoverable previous version (``.vsynch.bak``).

    Existing data are never replaced until BOTH the new serialized project
    and the recovery copy of the previous version have been written.  The
    backup is deliberately not made on the first save.  It contains the
    precise bytes of the *previous* saved version, not a re-serialized model.
    An I/O failure leaves the existing .vsynch untouched.
    """
    path = Path(path)
    validate_project(project)
    payload = (json.dumps(_with_relative_paths(project, path.parent), ensure_ascii=False, indent=2)
               + '\n').encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = None
    backup_stage = None
    try:
        stage = _staged_file(path, payload)
        if path.exists():
            # Never follow a symlink to an unrelated project when saving.
            if not path.is_file() or path.is_symlink():
                raise ValueError('La destination du projet doit être un fichier ordinaire.')
            old_mode = stat.S_IMODE(path.stat().st_mode)
            os.chmod(stage, old_mode)
            backup = path.with_name(path.name + '.bak')
            if backup.is_symlink():
                raise ValueError('Copie de sécurité invalide (lien symbolique).')
            backup_stage = _staged_file(backup)
            with path.open('rb') as src, backup_stage.open('wb') as dst:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
            os.replace(backup_stage, backup)
            backup_stage = None
        else:
            os.chmod(stage, default_mode())
        os.replace(stage, path)
        stage = None
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
        if backup_stage is not None:
            backup_stage.unlink(missing_ok=True)


def _is_relative_file_path(value):
    """Vrai pour un chemin de fichier relatif ; faux pour une URL ou un chemin
    absolu, POSIX ou Windows (y compris celui d'un autre système)."""
    if not isinstance(value, str) or not value or '://' in value or value.startswith('file:'):
        return False
    return not (value.startswith(('/', '\\')) or PurePosixPath(value).is_absolute()
                or PureWindowsPath(value).drive)


def _map_file_paths(project, change):
    """Applique ``change`` à chaque chemin de fichier du projet : images
    locales, fichiers ALTO/PAGE, images des pages, dossiers HD, TEI."""
    for witness in project.get('witnesses', []):
        for source in witness.get('image_sources', []):
            if source.get('kind') == 'local':
                source['reference'] = change(source.get('reference'))
        for source in witness.get('alto_sources', []):
            if 'path' in source:
                source['path'] = change(source['path'])
        for page in witness.get('pages', []):
            if page.get('image_path'):
                page['image_path'] = change(page['image_path'])
        for batch in witness.get('hd_downloads', []):
            batch['directory'] = change(batch['directory'])
    for resource in project.get('text_resources', []):
        if 'path' in resource:
            resource['path'] = change(resource['path'])


def _resolve_relative_paths(project, base):
    """Chemins relatifs du projet lus par rapport au dossier ``base`` du
    fichier .vsynch (séparateurs « / » ou « \\ »). Les chemins absolus et les
    URL ne changent pas. En mémoire, tous les chemins sont donc absolus.
    Les liens symboliques ne sont pas suivis : ouvrir puis enregistrer un
    projet garde ses chemins relatifs."""
    def absolute(value):
        if not _is_relative_file_path(value):
            return value
        return os.path.normpath(os.path.join(str(base), PureWindowsPath(value).as_posix()))
    _map_file_paths(project, absolute)


def _is_network_path(value):
    return isinstance(value, str) and value.startswith(('\\\\', '//'))


def suspicious_paths(path):
    """Chemins du projet ``path``, tels qu'écrits dans le fichier, qui sortent
    de son dossier par « .. » ou désignent un partage réseau. Varians-Synchro
    n'en écrit jamais de tels relatifs : un projet reçu qui en contient en
    ferait lire les fichiers à l'ouverture (et copier la TEI à l'export)."""
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    folder = os.path.normpath(str(path.absolute().parent))
    found = []

    def check(value):
        if _is_network_path(value):
            found.append(value)
        elif _is_relative_file_path(value):
            target = os.path.normpath(os.path.join(folder, PureWindowsPath(value).as_posix()))
            if os.path.commonpath([folder, target]) != folder:
                found.append(value)
        return value
    _map_file_paths(data, check)
    return list(dict.fromkeys(found))


REFUSED_FOLDER = '.vsynch-chemin-refuse'


def _refuse_paths(project, refused, folder):
    """Remplace les chemins ``refused`` par un chemin inexistant (le fichier
    est alors introuvable pour tout le logiciel) et garde l'original dans
    ``_refused_paths``, rendu à l'enregistrement."""
    refused = set(refused)
    originals = {}

    def block(value):
        if isinstance(value, str) and value in refused:
            stand_in = str(Path(folder) / REFUSED_FOLDER / f'{len(originals) + 1}-{PureWindowsPath(value).name}')
            originals[stand_in] = value
            return stand_in
        return value
    _map_file_paths(project, block)
    if originals:
        project['_refused_paths'] = originals


def _with_relative_paths(project, folder):
    """Copie du projet à enregistrer dans ``folder`` : un fichier situé dans ce
    dossier ou en dessous y est désigné par un chemin relatif à séparateurs
    « / », pour que le projet voyage avec ses fichiers ; un fichier ailleurs
    (autre dossier, autre disque) garde son chemin absolu."""
    bases = [Path(folder).absolute(), Path(folder).resolve()]
    refused = project.get('_refused_paths') or {}

    def relative(value):
        if isinstance(value, str) and value in refused:
            return refused[value]           # chemin refusé à l'ouverture : rendu tel quel
        if not isinstance(value, str) or _is_relative_file_path(value) or not Path(value).is_absolute():
            return value
        for candidate in (Path(value), Path(value).resolve()):
            for base in bases:
                try:
                    inside = candidate.relative_to(base)
                except ValueError:
                    continue
                if not inside.parts or (os.sep == '/' and '\\' in inside.as_posix()):
                    return value    # « \\ » d'un nom de fichier relu comme séparateur
                return inside.as_posix()
        return value
    copy = json.loads(json.dumps(project))
    copy.pop('_refused_paths', None)
    _map_file_paths(copy, relative)
    return copy


def load_project(path, refused=()):
    """Lit le projet ``path``. Les chemins ``refused`` (voir
    :func:`suspicious_paths`) ne sont pas lus : leurs fichiers sont
    introuvables, mais le projet les garde à l'enregistrement."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    validate_project(data)
    if refused:
        _refuse_paths(data, refused, Path(path).absolute().parent)
    _resolve_relative_paths(data, Path(path).resolve().parent)
    # In-memory migration from the original 0.5 project schema. Never rewrite
    # the user's original file until explicit Save.
    data.setdefault('pair_sessions', [])
    data.setdefault('pivot_witness_id', None)
    if 'workflow_preference' not in data:
        kinds = {r.get('kind') for r in data.get('text_resources', [])}
        data['workflow_preference'] = ('tei' if 'tei' in kinds else
                                      'pivot' if 'pivot' in kinds else 'alto_only')
    return data


def validate_project(project):
    if project.get('format') != SCHEMA or project.get('version') != 1:
        raise ValueError('Format ou version de projet non pris en charge')
    ids = [w['id'] for w in project.get('witnesses', [])]
    if project.get('pivot_witness_id') is not None and project['pivot_witness_id'] not in ids:
        raise ValueError('Le témoin pivot ne figure pas dans le projet')
    if len(ids) != len(set(ids)):
        raise ValueError('Identifiants de témoins non uniques')
    for witness in project.get('witnesses', []):
        batches = witness.get('hd_downloads', [])
        if (not isinstance(batches, list) or
                any(not isinstance(batch, dict) or not isinstance(batch.get('directory'), str)
                    or not isinstance(batch.get('pages'), list) for batch in batches)):
            raise ValueError('Registre des téléchargements HD invalide')
        ignored = witness.get('ignored_line_ids', [])
        if not isinstance(ignored, list) or any(not isinstance(uid, str) for uid in ignored) or len(set(ignored)) != len(ignored):
            raise ValueError('Liste des lignes ignorées invalide')
    if not isinstance(project.get('pair_sessions', []), list):
        raise ValueError('Sessions physiques de format invalide')
    for r in project.get('text_resources', []):
        if r.get('kind') == 'tei' and r.get('tei_binding') is not None:
            mapping = r['tei_binding']
            if (not isinstance(mapping, dict) or mapping.get('witness_id') != r.get('witness_id')
                or not isinstance(mapping.get('pairs'), list)
                or any(not isinstance(row, dict) or not row.get('physical_line_id')
                       or not row.get('tei_key') for row in mapping.get('pairs', []))):
                raise ValueError('Liaison TEI ↔ lignes physiques mal formée')
    if project.get('workflow_preference', 'alto_only') not in ('alto_only', 'pivot', 'tei'):
        raise ValueError('Parcours documentaire inconnu')


def create_witness(project, identifier, label=''):
    """New witness of siglum ``identifier``. Any siglum is accepted, as in
    Varians; but two sigla which would give the same identifier or file
    name in the exports, or a name Windows reserves, are refused."""
    from .witness_ids import file_key, is_reserved_on_windows, witness_id_for_siglum
    identifier = identifier.strip()
    if not identifier or any(w['id'] == identifier for w in project['witnesses']):
        raise ValueError('Identifiant de témoin vide ou déjà utilisé')
    if not witness_id_for_siglum(identifier):
        raise ValueError('Identifiant de témoin vide ou déjà utilisé')
    other = next((w['id'] for w in project['witnesses'] if file_key(w['id']) == file_key(identifier)), None)
    if other is not None:
        raise localized(ValueError, 'error.witness.siglum_conflict', witness=identifier, other=other)
    if is_reserved_on_windows(identifier):
        raise localized(ValueError, 'error.witness.siglum_reserved', witness=identifier)
    w = {'id': identifier, 'label': label or identifier, 'image_sources': [], 'alto_sources': [], 'pages': [], 'ignored_line_ids': []}
    project['witnesses'].append(w)
    return w


def add_image_source(witness, kind, reference):
    if kind not in ('iiif', 'local'):
        raise ValueError('Type image inconnu')
    entry = {'id': str(uuid.uuid4()), 'kind': kind, 'reference': str(reference), 'status': 'not_inspected'}
    witness['image_sources'].append(entry)
    return entry


def add_alto_source(witness, path):
    """Import an ALTO or PAGE-XML line source (historical function name)."""
    entry = inspect_line_source(path)
    entry['id'] = str(uuid.uuid4())
    witness['alto_sources'].append(entry)
    return entry


def lname(tag):
    return tag.rsplit('}', 1)[-1]


def inspect_line_source(path):
    """Detect ALTO or PAGE-XML by its root element, not its filename."""
    with Path(path).open('rb') as stream:
        for _, elem in ET.iterparse(stream, events=('start',)):
            name = lname(elem.tag).lower()
            if name == 'alto':
                return inspect_alto(path)
            if name == 'pcgts':
                from .page_xml import inspect_page_xml
                return inspect_page_xml(path)
            raise ValueError('Format de transcription XML inconnu : ALTO ou PAGE-XML requis')
    raise ValueError('Fichier XML vide')


def add_line_source(witness, path):
    """Preferred name for importing either ALTO or PAGE (backwards compatible)."""
    return add_alto_source(witness, path)


def inspect_alto(path):
    p = Path(path)
    root = ET.parse(p).getroot()
    if lname(root.tag).lower() != 'alto':
        raise ValueError('Le fichier ne semble pas être un ALTO XML')
    pages = []
    for page in root.iter():
        if lname(page.tag) != 'Page':
            continue
        lines = []
        # TextBlock membership is metadata for adjustable reading order. The
        # original flat TextLine enumeration is kept to preserve old line UIDs.
        region_for_node = {}
        region_index_for_node = {}
        blocks = [n for n in page.iter() if lname(n.tag) == 'TextBlock']
        for block_index, block in enumerate(blocks):
            region_id = block.get('ID') or f'textblock_{block_index+1}'
            for member in block.iter():
                if lname(member.tag) == 'TextLine' and id(member) not in region_for_node:
                    region_for_node[id(member)] = region_id
                    region_index_for_node[id(member)] = block_index
        for node in page.iter():
            if lname(node.tag) != 'TextLine':
                continue
            strings = [n.attrib.get('CONTENT', '') for n in node.iter() if lname(n.tag) == 'String']
            from .alto_geometry import textline_polygon
            polygon = textline_polygon(node)
            lines.append({'alto_id': node.attrib.get('ID'), 'text': ' '.join(t for t in strings if t),
                          'bbox': {key: node.attrib.get(key) for key in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')},
                          'region_id': region_for_node.get(id(node), '__unclassified__'),
                          'region_order': region_index_for_node.get(id(node), len(blocks)),
                          **({'polygon': polygon} if polygon else {})})
        pages.append({'alto_page_id': page.attrib.get('ID'), 'width': page.attrib.get('WIDTH'),
                      'height': page.attrib.get('HEIGHT'), 'line_count': len(lines),
                      'htr_line_count': sum(bool(l['text'].strip()) for l in lines), 'lines': lines})
    stat = p.stat()
    return {'kind': 'alto', 'path': str(p.resolve()), 'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'source_size': stat.st_size, 'source_mtime_ns': stat.st_mtime_ns,
            'pages': pages, 'page_count': len(pages),
            'line_count': sum(p['line_count'] for p in pages), 'htr_line_count': sum(p['htr_line_count'] for p in pages)}


def import_tei(project, path, witness_id=None):
    """Import one witness's TEI lines without mixing apparatus readings.

    The source remains untouched.  This legacy API now uses the same safe
    extractor as the V0.8.2–V0.8.3 editorial binding workflow.
    """
    if not witness_id:
        raise ValueError('Précisez le sigle du témoin pour importer les lignes TEI.')
    from .tei_binding import extract_witness_tei
    extracted = extract_witness_tei(path, witness_id)
    resource = {'id': str(uuid.uuid4()), 'kind': 'tei', 'path': extracted['path'],
                'witness_id': witness_id, 'source_sha256': extracted['source_sha256'],
                'lines': extracted['lines'], 'status': 'tei_unaligned',
                'tei_diagnostics': extracted['diagnostics']}
    project['text_resources'].append(resource)
    return resource


# TXT/MD import was removed from the supported V0.8 interface.  Pre-existing
# text_resources of that type are intentionally preserved by load_project().


def inspect_manifest(url, timeout=15):
    """Presentation 2/3 manifest inspection, including image URLs for each Canvas."""
    from .imaging import fetch_manifest
    return fetch_manifest(url)


def diagnostic(project):
    rows = []
    for w in project['witnesses']:
        rows.append({'witness': w['id'], 'image_sources': len(w['image_sources']),
                     'alto_sources': len(w['alto_sources']), 'page_sources': sum(s.get('kind') == 'page' for s in w['alto_sources']), 'alto_lines': sum(a['line_count'] for a in w['alto_sources']),
                     'htr_lines': sum(a['htr_line_count'] for a in w['alto_sources'])})
    return rows


def check_alto_files(project):
    """Report missing/modified external ALTO or PAGE without replacing snapshots.

    Old projects lacking a source hash are intentionally not flagged as changed.
    """
    warnings = []
    for witness in project.get('witnesses', []):
        for src in witness.get('alto_sources', []):
            path = Path(src['path'])
            if not path.is_file():
                warnings.append(Localized('error.core.xml_missing', witness=witness['id'], path=str(path)))
                continue
            expected = src.get('source_sha256')
            if expected is None:
                continue
            st = path.stat()
            if (st.st_size == src.get('source_size') and
                    st.st_mtime_ns == src.get('source_mtime_ns')):
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                warnings.append(Localized('error.core.xml_modified', witness=witness['id'], name=path.name))
    return warnings
