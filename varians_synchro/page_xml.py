"""PAGE-XML (PRImA / PAGE) parser for Varians-Synchro.

Produces the same physical-line inventory as ALTO, with true PAGE TextLine
Coords polygons and line-level TextEquiv/Unicode. No image/HTR processing or
transformation of the source file is performed. Namespace versions are
accepted by local element name, after checking the PAGE document structure.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from .alto_geometry import parse_alto_points


def _name(node):
    return node.tag.rsplit('}', 1)[-1]


def _direct(node, name):
    return [child for child in node if _name(child) == name]


def _line_text(line):
    """Prefer best indexed TextEquiv on a LINE, never inherited region text."""
    alternatives = []
    for position, te in enumerate(_direct(line, 'TextEquiv')):
        unicode_nodes = _direct(te, 'Unicode')
        if not unicode_nodes:
            continue
        value = ''.join(unicode_nodes[0].itertext()).strip()
        if not value:
            continue
        try:
            index = int(te.get('index', '0'))
        except ValueError:
            index = position
        alternatives.append((index, position, value))
    return min(alternatives)[2] if alternatives else ''


_GROUPS = ('OrderedGroup', 'UnorderedGroup', 'OrderedGroupIndexed', 'UnorderedGroupIndexed')
_REFS = ('RegionRef', 'RegionRefIndexed')


def _region_order(page):
    """Respect PAGE region reading order when explicitly supplied.

    Groups may be nested (``OrderedGroupIndexed`` inside an ``OrderedGroup``,
    as OCR-D or Aletheia write them): each group is read in turn, its members
    sorted by their own ``index`` (local to the group) when it is ordered,
    in document order otherwise. Flattening the groups and sorting on those
    local indexes mixed them up."""
    refs = []

    def walk(group):
        members = [child for child in group if _name(child) in _GROUPS + _REFS]
        if _name(group).startswith('Ordered'):
            def key(item):
                position, child = item
                try:
                    return (int(child.get('index')), position)
                except (TypeError, ValueError):
                    return (len(members) + position, position)
            members = [child for _, child in sorted(enumerate(members), key=key)]
        for child in members:
            if child.get('regionRef'):
                refs.append(child.get('regionRef'))
            if _name(child) in _GROUPS:
                walk(child)

    for reading_order in _direct(page, 'ReadingOrder'):
        for group in reading_order:
            if _name(group) in _GROUPS:
                walk(group)
        break
    order = {}
    for ident in refs:
        order.setdefault(ident, len(order))
    return order


def _own_lines(region):
    """TextLines of ``region`` itself, not those of the regions it contains
    (a nested TextRegion counted its lines twice)."""
    found = []

    def walk(node):
        for child in node:
            name = _name(child)
            if name == 'TextRegion':
                continue
            if name == 'TextLine':
                found.append(child)
            else:
                walk(child)
    walk(region)
    return found


def _baseline_points(value):
    """Read a PAGE polyline (two points suffice), unlike an area polygon."""
    if not isinstance(value, str) or len(value) > 1_000_000:
        return []
    points = []
    for token in value.split():
        parts = token.split(',')
        if len(parts) != 2:
            return []
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return []
        if not all(math.isfinite(v) and abs(v) < 1_000_000_000 for v in (x, y)):
            return []
        points.append([x, y])
    return points if 2 <= len(points) <= 10_000 else []


def _line_info(line, page_width, page_height):
    coords = _direct(line, 'Coords')
    polygon = parse_alto_points(coords[0].get('points', '')) if coords else []
    if not polygon:
        return None
    x0 = min(x for x, _ in polygon)
    y0 = min(y for _, y in polygon)
    x1 = max(x for x, _ in polygon)
    y1 = max(y for _, y in polygon)
    if x1 <= x0 or y1 <= y0:
        return None
    # Preserve the genuine PAGE geometry and also supply its ALTO-like envelope
    # to existing alignment algorithms (which must not alter that polygon).
    baseline_nodes = _direct(line, 'Baseline')
    baseline = _baseline_points(baseline_nodes[0].get('points', '')) if baseline_nodes else []
    return {
        'alto_id': line.get('id'),
        **({'baseline': baseline} if baseline else {}),
        'text': _line_text(line),
        'bbox': {'HPOS': x0, 'VPOS': y0, 'WIDTH': x1-x0, 'HEIGHT': y1-y0},
        'polygon': polygon,
    }


def inspect_page_xml(path):
    """Read PAGE-XML, preserving source file hashes and physical line order.

    Regions are ordered using PAGE ReadingOrder when present; within a region,
    XML TextLine order is preserved (not sorted by x/y, to avoid changing
    document identities on unpredictable sloping or marginal text).
    """
    p = Path(path)
    root = ET.parse(p).getroot()
    if _name(root) != 'PcGts':
        raise ValueError('Le fichier XML ne semble pas être un PAGE-XML (PcGts attendu)')
    pages = []
    for page_index, page in enumerate(node for node in root if _name(node) == 'Page'):
        width = page.get('imageWidth')
        height = page.get('imageHeight')
        if not width or not height or float(width) <= 0 or float(height) <= 0:
            raise ValueError('Dimensions PAGE-XML manquantes ou invalides')
        ro = _region_order(page)
        regions = [n for n in page.iter() if _name(n) == 'TextRegion']
        region_positions = {id(n): i for i, n in enumerate(regions)}
        regions.sort(key=lambda n: (0, ro[n.get('id')]) if n.get('id') in ro else (1, region_positions[id(n)]))
        lines = []
        missing = 0
        for region_index, region in enumerate(regions):
            for node in _own_lines(region):
                info = _line_info(node, width, height)
                if info is None:
                    missing += 1
                else:
                    info['region_id'] = region.get('id') or f'textregion_{region_index+1}'
                    info['region_order'] = region_index
                    lines.append(info)
        pages.append({
            'alto_page_id': page.get('imageFilename') or page.get('id') or p.stem,
            'image_filename': page.get('imageFilename') or '',
            'width': width, 'height': height,
            'line_count': len(lines),
            'htr_line_count': sum(bool(line['text']) for line in lines),
            'skipped_unsegmented_lines': missing,
            'lines': lines,
        })
    if not pages:
        raise ValueError('Aucune page PAGE-XML détectée')
    stat = p.stat()
    return {'kind': 'page', 'path': str(p.resolve()),
            'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'source_size': stat.st_size, 'source_mtime_ns': stat.st_mtime_ns,
            'pages': pages, 'page_count': len(pages),
            'line_count': sum(page['line_count'] for page in pages),
            'htr_line_count': sum(page['htr_line_count'] for page in pages)}
