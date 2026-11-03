"""Read-only visual review model for TEI↔physical-line proposals.

This module deliberately has no PySide6 dependency. It never changes project
sources, correspondence groups, TEI bindings, or the TEI XML. All coordinates
are expressed in the XML page coordinate system, then projected to the actual
image/IIIF Canvas dimensions for fetching and rendering.
"""
from __future__ import annotations

from math import ceil, floor, isfinite
from urllib.parse import urlparse

from .alto_geometry import page_line_polygons
from .imaging import mapped_alto_page, _http_bytes, image_bytes


def _positive(value):
    try:
        number = float(value)
        if 0 < number < 1_000_000_000 and isfinite(number):
            return number
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def review_pairs(preview):
    """Return begin/end and optional intermediate candidates without mutation."""
    pairs = preview.get('pairs') or []
    if not preview.get('eligible') or not pairs:
        return {'first': None, 'last': None, 'count': len(pairs)}
    return {'first': pairs[0], 'last': pairs[-1], 'count': len(pairs)}


def line_preview_descriptor(project, witness_id, pair, *, max_width=1300):
    """Locate a checked XML line on its image, with precise overlay polygon.

    The returned model describes the source rectangle *before* any IIIF resize.
    No document image is downloaded by this function.
    """
    witness = next((w for w in project.get('witnesses', []) if w.get('id') == witness_id), None)
    if witness is None:
        raise ValueError('Témoin introuvable.')
    page = next((p for p in witness.get('pages', []) if p.get('id') == pair.get('page_id')), None)
    if page is None:
        raise ValueError('Folio correspondant introuvable.')
    source = mapped_alto_page(witness, page)
    if source is None:
        raise ValueError('Fichier ALTO/PAGE indisponible pour ce folio.')
    index = int(pair.get('physical_ordinal', 0)) - 1
    lines = source.get('lines', [])
    if not 0 <= index < len(lines):
        raise ValueError('Ligne physique correspondante introuvable.')
    line = lines[index]
    from .physical_alignment import line_uid
    if line_uid(witness_id, page['id'], index + 1) != pair.get('physical_line_id'):
        raise ValueError('L’identifiant de la ligne physique a changé.')
    from .reading_stream import reading_stream
    active = next((p for p in reading_stream(witness) if p['id'] == pair.get('physical_line_id')), None)
    if active is None or active['fingerprint'] != pair.get('physical_fingerprint'):
        raise ValueError('Le périmètre ou la segmentation a changé : actualisez la liaison.')
    xml_width = _positive(source.get('width'))
    xml_height = _positive(source.get('height'))
    if not xml_width or not xml_height:
        raise ValueError('Dimensions ALTO/PAGE indisponibles : recadrage impossible.')
    bbox = line.get('bbox') or {}
    try:
        x, y, w, h = (float(bbox[k]) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
    except (ValueError, TypeError, KeyError):
        raise ValueError('Coordonnées de la ligne physique indisponibles.') from None
    if not all(isfinite(z) for z in (x, y, w, h)) or w <= 0 or h <= 0:
        raise ValueError('Rectangle de ligne invalide.')
    polygons = page_line_polygons(witness, page, source)
    polygon = (polygons[index] if index < len(polygons) else None) or [
        [x, y], [x+w, y], [x+w, y+h], [x, y+h]]
    # The preview includes neighbours; use the precise original polygon for overlay.
    points = [[float(px), float(py)] for px, py in polygon]
    xmin = min(px for px, _ in points)
    xmax = max(px for px, _ in points)
    ymin = min(py for _, py in points)
    ymax = max(py for _, py in points)
    if not all(isfinite(v) for v in (xmin, xmax, ymin, ymax)):
        raise ValueError('Polygone de ligne non valide.')
    pad_x = max(12, min(80, (xmax-xmin)*0.06))
    pad_y = max(18, (ymax-ymin)*1.35)
    left = max(0, xmin-pad_x)
    top = max(0, ymin-pad_y)
    right = min(xml_width, xmax+pad_x)
    bottom = min(xml_height, ymax+pad_y)
    if right <= left or bottom <= top:
        raise ValueError('Ligne hors des limites de la page.')
    kind = page.get('image_kind')
    canvas = page.get('canvas') or {}
    canvas_width = _positive(canvas.get('width')) if kind == 'iiif' else None
    canvas_height = _positive(canvas.get('height')) if kind == 'iiif' else None
    area = [left, top, right-left, bottom-top]
    output = {
        'witness_id': witness_id, 'page_id': page['id'],
        'page_label': page.get('label', ''), 'physical_ordinal': index + 1,
        'tei_ordinal': pair['tei_ordinal'], 'tei_text': pair.get('tei_text', ''),
        'physical_line_id': pair['physical_line_id'],
        'xml_size': [xml_width, xml_height], 'crop_xml': area,
        'polygon_xml': points, 'image_kind': kind,
        'max_width': max_width, 'page': page,
        'region_url': None, 'region_canvas': None,
    }
    if kind == 'iiif' and canvas.get('image_service') and canvas_width and canvas_height:
        # Canvas and ALTO/Page dimensions can be different due to OCR rescaling.
        scale_x, scale_y = canvas_width/xml_width, canvas_height/xml_height
        cx = max(0, floor(left*scale_x))
        cy = max(0, floor(top*scale_y))
        cx2 = min(ceil(canvas_width), ceil(right*scale_x))
        cy2 = min(ceil(canvas_height), ceil(bottom*scale_y))
        cw, ch = cx2-cx, cy2-cy
        if cw > 0 and ch > 0:
            base = str(canvas['image_service']).rstrip('/')
            if urlparse(base).scheme in ('https', 'http'):
                region = f'{cx},{cy},{cw},{ch}'
                size = f'!{int(max_width)},' if canvas.get('iiif_image_version', 2) == 2 else f'{int(max_width)},'
                output['region_url'] = f'{base}/{region}/{size}/0/default.jpg'
                output['region_canvas'] = [cx, cy, cw, ch]
                output['canvas_size'] = [canvas_width, canvas_height]
    return output


def fetch_preview_bytes(descriptor):
    """I/O intended for a worker thread, never the Qt UI thread."""
    if descriptor.get('region_url'):
        return _http_bytes(descriptor['region_url'], max_bytes=16_000_000, timeout=22)
    return image_bytes(descriptor['page'], max_width=1700)


def render_transform(descriptor, image_width, image_height):
    """Return crop rectangle and overlay in *returned image pixel* units.

    For region requests the bytes are already cropped and downscaled. For local
    images / direct image URLs, the crop is applied only after decoding.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError('Image décodée vide.')
    xw, yh = descriptor['xml_size']
    if descriptor.get('region_canvas'):
        rx, ry, rw, rh = descriptor['region_canvas']
        cw, ch = descriptor['canvas_size']
        sx = (cw/xw)*(image_width/rw)
        sy = (ch/yh)*(image_height/rh)
        polygon = [[px*sx-rx*image_width/rw, py*sy-ry*image_height/rh]
                   for px, py in descriptor['polygon_xml']]
        return {'crop': [0, 0, image_width, image_height], 'polygon': polygon}
    sx, sy = image_width/xw, image_height/yh
    x, y, w, h = descriptor['crop_xml']
    left = max(0, floor(x*sx))
    top = max(0, floor(y*sy))
    right = min(image_width, ceil((x+w)*sx))
    bottom = min(image_height, ceil((y+h)*sy))
    if right <= left or bottom <= top:
        raise ValueError('Le recadrage demandé est hors de l’image.')
    polygon = [[px*sx-left, py*sy-top] for px, py in descriptor['polygon_xml']]
    return {'crop': [left, top, right-left, bottom-top], 'polygon': polygon}
