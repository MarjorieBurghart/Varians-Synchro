"""IIIF/local page registry, ALTO-to-page mapping, export for external HTR.

Images and ALTO are immutable external inputs. An export is a temporary working copy.
"""
from __future__ import annotations
import copy
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from .errors import Localized, localized
from .witness_ids import witness_id_for_siglum

MAX_MANIFEST_BYTES = 20_000_000
MAX_IMAGE_BYTES = 80_000_000


def _http_bytes(url, max_bytes=MAX_IMAGE_BYTES, timeout=30):
    if urlparse(url).scheme != 'https' and urlparse(url).scheme != 'http':
        raise ValueError('URL HTTP(S) attendue')
    with urlopen(Request(url, headers={'User-Agent':'Varians-Synchro/0.2 (research software)'}), timeout=timeout) as res:
        data = res.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('Ressource trop volumineuse')
        return data


def _label(value):
    if isinstance(value, str): return value
    if isinstance(value, list): return ', '.join(map(_label, value))
    if isinstance(value, dict):
        if '@value' in value: return str(value['@value'])
        for key in ('fr','en','none'):
            if key in value: return _label(value[key])
        return _label(next(iter(value.values()),''))
    return str(value or '')


def _first(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k): return d[k]
    return None


def parse_manifest(data, url=''):
    """Flatten IIIF Presentation v2/v3 Canvas and extract image image-service URLs."""
    if 'sequences' in data:
        version = 2
        canvases = [c for s in data.get('sequences',[]) for c in s.get('canvases',[])]
    elif 'items' in data:
        version = 3
        canvases = [c for c in data.get('items',[]) if c.get('type')=='Canvas']
    else: raise ValueError('Manifest Presentation IIIF 2/3 non reconnu')
    pages=[]
    for n,c in enumerate(canvases):
        resource={}; service={}
        if version==2:
            imgs=c.get('images',[])
            if imgs:
                resource=imgs[0].get('resource') or {}
                service=resource.get('service') or {}
        else:
            for ap in c.get('items',[]):
                for ann in ap.get('items',[]):
                    if ann.get('motivation') not in (None,'painting'): continue
                    b=ann.get('body') or {}
                    if isinstance(b,list): b=next((x for x in b if isinstance(x,dict)),{})
                    resource=b
                    service=b.get('service') or {}
                    if resource: break
                if resource: break
        if isinstance(service,list): service=next((x for x in service if isinstance(x,dict)),{})
        sid=_first(service,'id','@id')
        direct=_first(resource,'id','@id')
        pages.append({'id':_first(c,'id','@id') or f'canvas-{n+1}',
                      'label':_label(c.get('label')) or f'Page {n+1}',
                      'index':n,'width':c.get('width'),'height':c.get('height'),
                      'image_service':sid, 'image_url':direct,
                      'iiif_image_version':3 if str(_first(service,'type','profile') or '').find('ImageService3')!=-1 else 2})
    return {'url':url,'iiif_version':version,'label':_label(data.get('label')),
            'canvas_count':len(pages),'canvases':pages}


def fetch_manifest(url):
    return parse_manifest(json.loads(_http_bytes(url,MAX_MANIFEST_BYTES).decode('utf-8-sig')),url)


def create_pages(witness):
    """Build a unique page inventory from sources; preexisting mappings survive refresh."""
    prior={p['id']:p for p in witness.get('pages',[])}
    pages=[]; seen=set()
    for src in witness.get('image_sources',[]):
        if src['kind']=='iiif':
            for c in (src.get('manifest') or {}).get('canvases',[]):
                pid=c['id']
                if pid in seen:continue
                seen.add(pid)
                item={'id':pid,'label':c.get('label',''),'image_kind':'iiif',
                      'image_source_id':src['id'],'canvas':c,
                      'alto_binding':None}
                item['alto_binding']=prior.get(pid,{}).get('alto_binding')
                for field in ('reading_order', 'reading_region_order', 'reading_line_order'):
                    if field in prior.get(pid, {}):
                        item[field] = prior[pid][field]
                pages.append(item)
        elif src['kind']=='local':
            pid=src['id']
            if pid in seen:continue
            seen.add(pid)
            item={'id':pid,'label':Path(src['reference']).stem,'image_kind':'local',
                  'image_source_id':src['id'],'image_path':src['reference'],
                  'alto_binding':prior.get(pid,{}).get('alto_binding')}
            for field in ('reading_order', 'reading_region_order', 'reading_line_order'):
                if field in prior.get(pid, {}):
                    item[field] = prior[pid][field]
            pages.append(item)
    # A page added after a user-defined order must not silently revert the
    # existing pages to filename/Canvas order. Append new pages to the reading
    # sequence; the user may then place them precisely in the page manager.
    existing_order = bool(prior) and all(
        isinstance(page.get('reading_order'), int) for page in prior.values())
    if existing_order:
        next_index = max(page['reading_order'] for page in prior.values()) + 1
        for page in pages:
            if 'reading_order' not in page:
                page['reading_order'] = next_index
                next_index += 1
    from .page_order import ordered_pages
    witness['pages']=ordered_pages(witness, pages)
    return witness['pages']


def bind_alto(witness,page_id,alto_source_id,alto_page_index=0):
    page=next((p for p in witness.get('pages',[]) if p['id']==page_id),None)
    src=next((a for a in witness.get('alto_sources',[]) if a['id']==alto_source_id),None)
    if page is None or src is None:raise ValueError('Page ou source ALTO/PAGE introuvable')
    if not 0<=alto_page_index<len(src['pages']): raise ValueError('Index de page XML invalide')
    before=(mapped_alto_page(witness,page) or {}).get('lines',[])
    page['alto_binding']={'source_id':alto_source_id,'page_index':alto_page_index,'verified':False}
    # Ignored lines are known by page and rank: carry each mark to the same
    # line in the new file, or release it (never leave it on another line).
    from .line_scope import carry_ignored_lines
    return carry_ignored_lines(witness,page_id,before,src['pages'][alto_page_index].get('lines',[]))


def mapped_alto_page(witness,page):
    b=page.get('alto_binding')
    if b is None:return None
    src=next((a for a in witness['alto_sources'] if a['id']==b['source_id']),None)
    return src['pages'][b['page_index']] if src and b['page_index']<len(src['pages']) else None


def bind_line_source(witness, page_id, source_id, page_index=0):
    return bind_alto(witness, page_id, source_id, page_index)


def mapped_line_page(witness, page):
    return mapped_alto_page(witness, page)


def suggest_alto_bindings(witness):
    """Suggest ALTO/PAGE associations; never commit ambiguous matches automatically."""
    sources=[(a,i,p) for a in witness['alto_sources'] for i,p in enumerate(a['pages'])]
    result=[]
    def norm(s):return re.sub(r'[^a-z0-9]','',str(s or '').lower())
    for page in witness.get('pages',[]):
        label=norm(page.get('label'))
        candidates=[]
        for a,i,p in sources:
            stem=norm(Path(a['path']).stem)
            aid=norm(p.get('alto_page_id'))
            image_stem=norm(Path(str(p.get('image_filename') or '').replace('\\', '/')).stem)
            if label and (label==stem or label==aid or label==image_stem or (len(label)>=4 and label in stem)):
                candidates.append((a['id'],i))
        if len(candidates)==1:result.append({'page_id':page['id'],'alto_source_id':candidates[0][0],
                                             'alto_page_index':candidates[0][1]})
    return result


def suggest_line_bindings(witness):
    return suggest_alto_bindings(witness)


def image_request_url(page, max_width=2500):
    if page['image_kind']!='iiif':return None
    c=page['canvas']; sid=c.get('image_service')
    if sid:
        ver=c.get('iiif_image_version',2)
        return sid.rstrip('/') + ('/full/!' if ver==2 else '/full/') + str(max_width) + (',/0/default.jpg' if ver==2 else ',/0/default.jpg')
    return c.get('image_url')


def image_bytes(page, max_width=2500):
    if page['image_kind']=='local':
        path=Path(page['image_path'])
        if path.stat().st_size>MAX_IMAGE_BYTES:raise ValueError('Fichier image trop volumineux pour cet aperçu')
        return path.read_bytes()
    url=image_request_url(page,max_width)
    if not url:raise ValueError('Pas de service IIIF ni URL image dans le Canvas')
    return _http_bytes(url)


def export_iiif_htr_zip(witness, page_ids, output_path, max_width=2500, *,
                        cancelled=None, progress=None):
    """Download only selected IIIF pages, with Canvas metadata to enable reimport.

    ``progress(done, total)`` is called after each page; ``cancelled()``,
    checked before each page, stops the export (InterruptedError) without
    leaving an archive. Both let the interface run it outside its thread."""
    pages={p['id']:p for p in witness['pages']}
    if not page_ids:raise ValueError('Sélectionnez au moins une page')
    items=[]
    dest=Path(output_path);dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_suffix(dest.suffix+'.tmp')
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for num,pid in enumerate(page_ids,1):
                if cancelled is not None and cancelled():
                    raise InterruptedError('Export annulé')
                p=pages[pid]
                if p['image_kind']!='iiif':raise ValueError('Export IIIF : sélection contenant une image locale')
                # The siglum is free text: name the images by the XML
                # identifier derived from it, a safe file name (no « / »).
                fname=f'{witness_id_for_siglum(witness["id"])}_{num:04d}.jpg'
                body=image_bytes(p,max_width)
                if not body.startswith(b'\xff\xd8'):
                    raise localized(ValueError, 'error.imaging.export_not_jpeg', page=p['label'])
                z.writestr(fname,body)
                items.append({'file':fname,'canvas_id':p['id'],'label':p['label'],
                              'image_request_url':image_request_url(p,max_width),
                              'canvas_dimensions':{'width':p['canvas'].get('width'),'height':p['canvas'].get('height')}})
                if progress is not None:
                    progress(num, len(page_ids))
            z.writestr('pages.json',json.dumps({'format':'varians-synchro-htr-export',
                        'witness':witness['id'],'pages':items},ensure_ascii=False,indent=2))
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return len(items)


def import_htr_results(witness, mapping_json_path, alto_directory, inspect_func=None):
    """Reattach exported image names to ALTO or PAGE files (matching basename).

    Missing or ambiguous files are reported, never guessed. Explicit preexisting
    bindings are preserved. The HTR provider may use arbitrary ALTO IDs.
    """
    from .core import add_alto_source
    mapping_path=Path(mapping_json_path)
    mapping=json.loads(mapping_path.read_text(encoding='utf-8'))
    if mapping.get('format')!='varians-synchro-htr-export':
        raise ValueError('Le fichier pages.json ne provient pas de Varians-Synchro')
    if mapping.get('witness')!=witness['id']:
        raise ValueError('Témoin incompatible avec pages.json')
    folder=Path(alto_directory)
    paths=list(folder.glob('*.xml'))
    sourcefn=inspect_func or add_alto_source
    imported=[];missing=[];ambiguous=[]
    # All or nothing: the lot is read on a copy of the witness, published
    # only once every file has been read (a truncated file left the witness
    # half modified, an XML of several pages an orphan source).
    final=witness
    witness=copy.deepcopy(witness)
    bypage={p['id']:p for p in witness.get('pages',[])}
    for item in mapping.get('pages',[]):
        canvas=item['canvas_id']; page=bypage.get(canvas)
        if page is None:
            missing.append({'canvas':canvas,'reason':'Canvas absent du projet'});continue
        if page.get('alto_binding'):
            ambiguous.append({'canvas':canvas,'reason':'Page déjà associée à un ALTO'});continue
        stem=Path(item['file']).stem.casefold()
        matches=[p for p in paths if p.stem.casefold()==stem]
        if not matches:
            missing.append({'canvas':canvas,'expected':stem+'.xml'});continue
        if len(matches)>1:
            ambiguous.append({'canvas':canvas,'reason':'Plusieurs fichiers XML candidats'});continue
        src=sourcefn(witness,matches[0])
        if len(src['pages'])!=1:
            witness['alto_sources']=[s for s in witness['alto_sources'] if s is not src]
            ambiguous.append({'canvas':canvas,'reason':'XML comportant plusieurs pages'});continue
        bind_alto(witness,canvas,src['id'],0)
        imported.append(canvas)
    final.clear()
    final.update(witness)
    return {'imported':imported,'missing':missing,'skipped':ambiguous}


def iiif_hd_url(page):
    """Return the native-size IIIF Image API JPEG URL for a Canvas.

    Intentionally refuse guessed direct-image endpoints: not all direct URLs
    supply native resolution, and harvesting other IIIF assets is outside scope.
    """
    if page.get('image_kind') != 'iiif':
        raise ValueError('Image IIIF attendue pour le téléchargement HD')
    canvas = page.get('canvas') or {}
    service = canvas.get('image_service')
    if not isinstance(service, str) or urlparse(service).scheme not in ('http', 'https'):
        raise localized(ValueError, 'error.imaging.no_image_service', page=str(page.get('label') or page.get('id')))
    version = canvas.get('iiif_image_version', 2)
    if version not in (2, 3):
        raise ValueError('Version Image API IIIF non reconnue')
    # Image API 2 supports the full size token; Image API 3 prefers max.
    size = 'full' if version == 2 else 'max'
    return service.rstrip('/') + '/full/' + size + '/0/default.jpg'


def export_iiif_hd_images(witness, page_ids, destination, *, cancelled=None,
                          progress=None, max_image_bytes=160_000_000):
    """Publish native-resolution downloads for only explicitly selected canvases.

    The destination must be empty, and is populated atomically via a temporary
    sibling directory. A cancelled/failed download never publishes partial data.
    No project model field is modified. Intended to run off the Qt GUI thread.
    """
    import os
    import shutil
    import tempfile

    pages = {p['id']: p for p in witness.get('pages', [])}
    if not page_ids or len(set(page_ids)) != len(page_ids):
        raise ValueError('Sélection IIIF vide ou contenant des doublons')
    selected = []
    for page_id in page_ids:
        page = pages.get(page_id)
        if page is None:
            raise ValueError('Canvas sélectionné absent du projet')
        selected.append((page, iiif_hd_url(page)))
    dest = Path(destination)
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        raise FileExistsError('Le dossier de destination doit être un répertoire réel')
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError('Veuillez choisir un dossier vide pour éviter tout écrasement')
    if cancelled is None:
        cancelled = lambda: False
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.varians-hd-', dir=str(parent)))
    published = False
    try:
        manifest = {'format': 'varians-synchro-iiif-hd', 'witness': witness['id'], 'pages': []}
        for index, (page, url) in enumerate(selected, 1):
            if cancelled():
                raise InterruptedError('Téléchargement annulé')
            safe_label = re.sub(r'[^A-Za-z0-9_-]+', '_', str(page.get('label') or '')).strip('_')[:65]
            filename = f'{witness["id"]}_{index:04d}' + (f'_{safe_label}' if safe_label else '') + '.jpg'
            filename = re.sub(r'[^A-Za-z0-9_.-]', '_', filename)
            final = staging / filename
            with urlopen(Request(url, headers={'User-Agent': 'Varians-Synchro/0.8.5.1'}),
                         timeout=35) as response, final.open('wb') as outfile:
                total = 0
                signature = b''
                while True:
                    if cancelled():
                        raise InterruptedError('Téléchargement annulé')
                    chunk = response.read(262_144)
                    if not chunk:
                        break
                    if not signature:
                        signature = chunk[:3]
                    total += len(chunk)
                    if total > max_image_bytes:
                        raise localized(ValueError, 'error.imaging.hd_too_large', page=str(page.get('label')))
                    outfile.write(chunk)
            if signature != b'\xff\xd8\xff':
                raise localized(ValueError, 'error.imaging.hd_not_jpeg', page=str(page.get('label')))
            manifest['pages'].append({'file': filename, 'canvas_id': page['id'],
                                      'label': page.get('label'), 'iiif_image_url': url,
                                      'size_bytes': total})
            if progress:
                progress(index, len(selected))
        if cancelled():
            raise InterruptedError('Téléchargement annulé')
        (staging / 'images.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                            encoding='utf-8')
        if dest.exists():
            if any(dest.iterdir()):
                raise FileExistsError('Le dossier cible a été rempli pendant le téléchargement')
            dest.rmdir()
        try:
            os.replace(staging, dest)
            published = True
        except OSError:
            dest.mkdir(exist_ok=True)
            raise
    finally:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)
    return len(selected)
