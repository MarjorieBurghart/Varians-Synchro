"""Build a directly openable Varians project.xml bundle from Synchro resources.

Target syntax: Varians's documented teiManuscriptProject format with one TEI
edition. This is a physical mapping export; it does NOT assert that line links
have been reconciled with TEI <lb/> unless the editor independently confirms it.
The caller must run a final integration test against their installed Varians.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .varians_export import make_varians_alignments, verify_export_payloads
from .core import validate_project
from .hd_registry import local_copy_plan, varians_offline_index


def _varians_safe_id(witness_id):
    """Mirror Varians 0.8.x iiif_local.store_dir witness sanitization."""
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', witness_id).strip('._') or 'witness'


def _source_path(value):
    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f'Ressource absente : {path}')
    return path.resolve()


def _relative_or_absolute(path, output):
    """External source paths are preserved, never copied or silently rewritten."""
    return str(path)



def _cache_varians_manifest(source: dict, stage: Path, wid: str) -> bool:
    """Cache known IIIF canvases in Varians's existing manifest-cache format.

    Synchro stores a flattened presentation manifest, not necessarily its
    original JSON. Rebuild only the safe, known v3 presentation fields. This
    avoids a mandatory remote request when opening a portable local project.
    """
    metadata = source.get('manifest') or {}
    canvases = metadata.get('canvases') or []
    if not canvases:
        return False
    items = []
    for n, canvas in enumerate(canvases, 1):
        uri = str(canvas.get('id') or f'urn:varians:canvas:{wid}:{n}')
        label = str(canvas.get('label') or f'Page {n}')
        data = {'id': uri, 'type': 'Canvas', 'label': {'none': [label]},
                'items': []}
        for dim in ('width', 'height'):
            if canvas.get(dim) is not None:
                data[dim] = int(canvas[dim])
        service = canvas.get('image_service')
        image_url = canvas.get('image_url')
        if service or image_url:
            body = {'type': 'Image'}
            if image_url:
                body['id'] = image_url
            if service:
                body['service'] = [{'id': service,
                    'type': 'ImageService3' if canvas.get('iiif_image_version') == 3
                            else 'ImageService2'}]
            data['items'] = [{'id': uri + '/annotations', 'type': 'AnnotationPage',
                'items': [{'id': uri + '/annotation/painting', 'type': 'Annotation',
                           'motivation': 'painting', 'body': body}]}]
        items.append(data)
    raw = {'@context': 'http://iiif.io/api/presentation/3/context.json',
           'type': 'Manifest', 'id': str(source.get('reference') or ''),
           'label': {'none': [str(metadata.get('label') or wid)]}, 'items': items}
    cache = stage / 'iiif' / (_varians_safe_id(wid) + '.manifest.json')
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({'_format': 'varians-iiif-manifest-cache',
        'source': str(source.get('reference') or ''), 'manifest': raw},
        ensure_ascii=False, indent=2), encoding='utf-8')
    return True

TEI_NS = 'http://www.tei-c.org/ns/1.0'
XML_NS = 'http://www.w3.org/XML/1998/namespace'
TEI_ALL_RNG = 'https://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng'


def blank_tei_edition(title, witnesses):
    """La TEI vide que crée Varians pour une « transcription vierge »
    (``project_management.minimal_tei_text``, schéma « auto », langue fr) :
    titre, liste des témoins (cibles de ``@wit``), un ``<p/>`` vide, et les
    deux ``xml-model`` vers TEI All. Varians peut ensuite y préparer les
    ``<pb/>`` et ``<lb/>`` du pivot (« Paramètres du projet »). Identique
    octet pour octet à celle de Varians : tests/test_varians_blank_edition.py."""
    def q(name):
        return f'{{{TEI_NS}}}{name}'
    root = ET.Element(q('TEI'))
    file_desc = ET.SubElement(ET.SubElement(root, q('teiHeader')), q('fileDesc'))
    ET.SubElement(ET.SubElement(file_desc, q('titleStmt')), q('title')).text = \
        (title or 'Nouvelle édition').strip()
    publication = ET.SubElement(file_desc, q('publicationStmt'))
    source_desc = ET.SubElement(file_desc, q('sourceDesc'))
    ET.SubElement(publication, q('p')).text = 'Édition en préparation.'
    list_wit = ET.SubElement(source_desc, q('listWit'))
    for witness in witnesses:
        ET.SubElement(list_wit, q('witness'), {f'{{{XML_NS}}}id': witness['id']}).text = \
            str(witness.get('label') or witness['id']).strip()
    ET.SubElement(ET.SubElement(ET.SubElement(root, q('text')), q('body')), q('p'))
    ET.indent(root, space='  ')
    xml = ET.tostring(root, encoding='unicode', short_empty_elements=False,
                      default_namespace=TEI_NS)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<?xml-model href="{TEI_ALL_RNG}" type="application/xml" '
            'schematypens="http://relaxng.org/ns/structure/1.0"?>\n'
            f'<?xml-model href="{TEI_ALL_RNG}" type="application/xml" '
            'schematypens="http://purl.oclc.org/dsdl/schematron"?>\n' + xml + '\n')


def export_varians_project(project, pivot_id, destination, *, include_uncertain=False):
    """Stage a project.xml, the pivot TEI copy, alignment JSONs and resources.

    Without a TEI edition of the pivot, the project gets the blank edition
    Varians creates for a new transcription (``blank_tei_edition``).

    External images/ALTO remain linked by their original paths. One IIIF
    Manifest per witness is supported by Varians's project configuration.
    No existing/nonempty destination is overwritten, and failure leaves it
    unchanged. A separate README documents the schema and portability limits.
    """
    validate_project(project)
    dest = Path(destination).expanduser().absolute()
    if dest.is_symlink() or (dest.exists() and (not dest.is_dir() or any(dest.iterdir()))):
        raise FileExistsError('Choisissez un dossier vide pour le projet Varians')
    witnesses = project.get('witnesses') or []
    ids = [w['id'] for w in witnesses]
    if pivot_id not in ids:
        raise ValueError('Le pivot choisi ne fait pas partie du projet')
    for wid in ids:
        if wid in ('', '.', '..') or any(c in wid for c in '/\\.'):
            raise ValueError('Sigle de témoin incompatible avec le nom de fichier : ' + str(wid))
    safe_ids = [_varians_safe_id(wid) for wid in ids]
    if len(set(safe_ids)) != len(safe_ids):
        raise ValueError('Deux sigles deviennent identiques dans le cache IIIF local Varians')
    tei = [r for r in project.get('text_resources', [])
           if r.get('kind') == 'tei' and r.get('witness_id') == pivot_id]
    if len(tei) > 1:
        raise ValueError('Le pivot doit posséder au plus une édition TEI pour cet export ; '
                         'sélectionnez une édition de référence.')
    tei_path = _source_path(tei[0]['path']) if tei else None
    if tei_path is not None:
        tree = ET.parse(tei_path)
        if tree.getroot().tag.rsplit('}', 1)[-1] not in {'TEI', 'teiCorpus'}:
            raise ValueError('L’édition du pivot ne présente pas une racine TEI')
    packages, diagnostics = make_varians_alignments(project, pivot_id,
                                                     include_uncertain=include_uncertain)
    verify_export_payloads(packages, pivot_id)
    # Preflight ALL inputs before changing the filesystem.
    for w in witnesses:
        source_types = {src['kind'] for src in w.get('image_sources', [])}
        if len(source_types) > 1:
            raise ValueError(f"{w['id']} : images IIIF et images locales mélangées. "
                             'Le format de projet Varians visé demande une source homogène.')
        manifests = [s for s in w.get('image_sources', []) if s['kind'] == 'iiif']
        if len(manifests) > 1:
            raise ValueError(f"{w['id']} : plusieurs Manifests IIIF ; "
                             'le format Varians visé n’en accepte qu’un par témoin.')
        for page in w.get('pages', []):
            if page.get('image_kind') == 'local':
                _source_path(page.get('image_path'))
        for xml in w.get('alto_sources', []):
            _source_path(xml['path'])
    # A downloaded set becomes a local working copy ONLY if ALL segmented IIIF
    # images of that witness are present, current and checksum-verified. No
    # partial witness falls back to a silently incomplete offline configuration.
    hd_plans = {w['id']: local_copy_plan(w) for w in witnesses
                if any(p.get('image_kind') == 'iiif' for p in w.get('pages', []))}
    title = str(project.get('name') or 'Édition Varians')
    root = ET.Element('teiManuscriptProject', version='1')
    ET.SubElement(root, 'title').text = title
    ET.SubElement(root, 'edition', file='xml/edition.xml')
    ET.SubElement(root, 'schema', type='relaxng', source='xml-model')
    ET.SubElement(root, 'interface', language='fr', translationsDir='i18n', fallbackLanguage='en')
    ET.SubElement(root, 'rendering', css='rendering/tei.css',
                  customElements='rendering/custom-elements.xml', xsltMode='builtin')
    ET.SubElement(root, 'webViewer', outputDir='web_output', filename='viewer.html')
    json_pages = {wid: {str(page['id']) for page in data.get('pages', [])}
                  for wid, data in packages.items()}
    witness_list = ET.SubElement(root, 'witnesses', base=pivot_id)
    for w in witnesses:
        wid = w['id']
        child = ET.SubElement(witness_list, 'witness', id=wid,
                              label=str(w.get('label') or wid), alignment=f'alignments/{wid}.json')
        if wid == pivot_id:
            child.set('role', 'base')
        images = w.get('image_sources', [])
        if not images:
            ET.SubElement(child, 'images', type='none')
        elif images[0]['kind'] == 'iiif':
            source = images[0]
            ref = source.get('reference')
            if not ref:
                raise ValueError(f'{wid} : URL du Manifest absente')
            attrs = {'type': 'iiif', 'manifest': str(ref), 'selectionMode': 'selected'}
            if hd_plans[wid]['eligible']:
                attrs.update({'localCopy': 'true', 'downloadScope': 'ocr',
                              'webLocalCopy': 'false'})
            im = ET.SubElement(child, 'images', **attrs)
            for page in w.get('pages', []):
                if page.get('image_kind') != 'iiif':
                    continue
                ET.SubElement(im, 'canvas', ref=str(page['id']))
                bind = page.get('alto_binding') or {}
                xml = next((x for x in w.get('alto_sources', [])
                            if x['id'] == bind.get('source_id')), None)
                if xml:
                    ET.SubElement(im, 'ocrLink', file=_relative_or_absolute(
                        _source_path(xml['path']), dest), canvas=str(page['id']))
                # Only pages of the alignment JSON can be linked: Varians
                # refuses a link to a page it does not know (an unsegmented
                # Canvas, such as a flyleaf, is selected but has no page).
                if str(page['id']) in json_pages[wid]:
                    ET.SubElement(im, 'pageLink', page=str(page['id']), canvas=str(page['id']))
        else:
            im = ET.SubElement(child, 'images', type='files')
            for page in w.get('pages', []):
                if page.get('image_kind') != 'local':
                    continue
                ET.SubElement(im, 'image', file=_relative_or_absolute(
                    _source_path(page['image_path']), dest),
                    label=str(page.get('label') or page['id']))
        # No <alto type="files">: the alignment JSON already carries each
        # line's geometry and text, in Synchro's reading order and without
        # the lines out of scope. Declared ALTO/PAGE files would be laid over
        # it when Varians opens the project, bringing those lines back and
        # the XML order with them: the pivot's <lb/> would then be shifted.

    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.varians-project-', dir=str(dest.parent)))
    published = False
    try:
        # Export the local IIIF working-copy format that Varians 0.8.x reads:
        # iiif/local/<witness>/index.json and content-addressed JPEG files.
        # Images remain keyed by original Canvas/IIIF URL, NOT by file order.
        copied = {}
        for w in witnesses:
            wid = w['id']
            plan = hd_plans.get(wid)
            if not plan or not plan['eligible']:
                continue
            index_entries = varians_offline_index(w, plan)
            target = stage / 'iiif' / 'local' / _varians_safe_id(wid)
            target.mkdir(parents=True, exist_ok=True)
            entries = {}
            for key, entry in index_entries.items():
                src = Path(entry['_copy_from'])
                # Recheck just before packaging to catch changed files.
                from .hd_registry import _sha256
                recorded = next((p for p in plan['available'].values()
                                 if p['path'] == str(src)), None)
                if recorded is None or not src.is_file() or _sha256(src) != recorded['sha256']:
                    raise ValueError(f'{wid} : copie IIIF HD modifiée pendant l’export')
                shutil.copy2(src, target / entry['file'])
                entries[key] = {'file': entry['file'], 'source': entry['source']}
            (target / 'index.json').write_text(json.dumps({
                'format': 'varians-iiif-local-1', 'images': entries},
                ensure_ascii=False, indent=2), encoding='utf-8')
            copied[wid] = len(entries)
            remote = next((r for r in w.get('image_sources', [])
                           if r.get('kind') == 'iiif'), None)
            if remote:
                _cache_varians_manifest(remote, stage, wid)
        (stage / 'xml').mkdir()
        if tei_path is not None:
            shutil.copy2(tei_path, stage / 'xml' / 'edition.xml')
        else:
            (stage / 'xml' / 'edition.xml').write_text(
                blank_tei_edition(title, witnesses), encoding='utf-8', newline='\n')
        (stage / 'alignments').mkdir()
        for wid, data in packages.items():
            (stage / 'alignments' / f'{wid}.json').write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        (stage / 'rendering').mkdir()
        (stage / 'rendering' / 'tei.css').write_text(
            'body { font-family: Georgia, serif; max-width: 76ch; margin: 2em auto; }\n',
            encoding='utf-8')
        (stage / 'rendering' / 'custom-elements.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?><customElements/>\n', encoding='utf-8')
        (stage / 'i18n').mkdir()
        (stage / 'web_output').mkdir()
        ET.indent(root, space='  ')
        ET.ElementTree(root).write(stage / 'project.xml', encoding='utf-8',
                                   xml_declaration=True)
        (stage / 'RAPPORT_EXPORT_VARIANS.txt').write_text(
            'Projet généré par Varians-Synchro.\n'
            'Format du fichier project.xml : teiManuscriptProject (vérifié avec Varians 0.9.4.0).\n'
            'Vérifiez la compatibilité avec votre version courante de Varians.\n'
            'Les images locales restent à leur emplacement original. Les lignes (géométrie,\n'
            'texte HTR, ordre de lecture) sont dans les JSON d\u2019alignement ; les fichiers\n'
            'ALTO/PAGE ne sont pas déclarés dans project.xml (Varians les superposerait au JSON).\n'
            'Les identifiants exportés sont des références physiques ; la présence de la TEI\n'
            'ne prouve pas à elle seule que ses <lb/> sont reconnus par Varians.\n'
            + ('' if tei_path is not None else
               'Édition : TEI vide, comme une « transcription vierge » de Varians (aucune\n'
               'édition TEI n\u2019était associée au témoin pivot). Pour y préparer les <pb/>\n'
               'et les <lb/> du pivot : dans Varians, Fichier → Paramètres du projet…, cocher\n'
               '« Préparer les <pb/> du témoin pivot dans la TEI vide » (et « Générer aussi\n'
               'les <lb/> depuis ALTO, PAGE ou la synchronisation »).\n')
            + ('Copies IIIF HD locales vérifiées et incluses (témoin : nombre) : ' + str(copied) + '\n'
               if copied else 'Aucune copie IIIF HD locale incluse : couverture incomplète ou absente.\n')
            + '\n'.join(f'{wid} : copies HD refusées, Canvas segmentés manquants : '
                          + ', '.join(plan['missing'])
                          for wid, plan in hd_plans.items() if not plan['eligible'] and plan['missing']) + '\n'
            + ('Inclut les propositions de travail non validées.\n' if include_uncertain
               else 'Seules les correspondances validées sont exportées.\n'),
            encoding='utf-8')
        # Check what was actually serialized.
        if ET.parse(stage / 'project.xml').getroot().find('witnesses') is None:
            raise AssertionError('Configuration Varians incomplète')
        parsed = {wid: json.loads((stage / 'alignments' / f'{wid}.json').read_text(
            encoding='utf-8')) for wid in packages}
        verify_export_payloads(parsed, pivot_id)
        if dest.exists():
            if any(dest.iterdir()):
                raise FileExistsError('Le dossier cible a été rempli durant la préparation')
            dest.rmdir()
        try:
            os.replace(stage, dest)
            published = True
        except OSError:
            dest.mkdir(exist_ok=True)
            raise
    finally:
        if not published:
            shutil.rmtree(stage, ignore_errors=True)
    return {'project_file': str(dest / 'project.xml'),
            'witnesses': len(witnesses), 'base': pivot_id,
            'tei': str(tei_path) if tei_path is not None else None,
            'edition': 'copied' if tei_path is not None else 'blank',
            'alignment_diagnostics': diagnostics,
            'local_hd_copies': copied, 'hd_plans': {wid:{k:plan[k] for k in ('eligible','required','missing','problems')} for wid,plan in hd_plans.items()}}
