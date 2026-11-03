"""ALTO physical-line polygon geometry (pure Python, no Qt dependency).

PERO and other HTR engines may describe a sloping text line using
<TextLine><Shape><Polygon POINTS="x,y ..."/></Shape></TextLine>.
The TextLine HPOS/VPOS/WIDTH/HEIGHT attributes are only an axis-aligned
*envelope*, which can overlap neighbouring lines even when the polygons don't.
This module never changes the source file or the persistent line identifiers.
For projects imported before polygons were stored, original ALTO files are
consulted on demand and cached; if missing, original bounding boxes remain.
"""
from __future__ import annotations

from functools import lru_cache
from math import isfinite
from pathlib import Path
import re
import xml.etree.ElementTree as ET

_NUMBER_RE = re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')


def parse_alto_points(value):
    """Return a valid polygon as ``[[x,y], ...]``, else an empty list.

    Accept both ALTO's common comma-paired and whitespace-paired formats.
    Never fabricate a shape from an invalid or incomplete POINTS attribute.
    """
    if not isinstance(value, str) or len(value) > 1_000_000:
        return []
    numbers = _NUMBER_RE.findall(value)
    if len(numbers) < 6 or len(numbers) % 2:
        return []
    coords = [float(n) for n in numbers]
    if not all(isfinite(n) and abs(n) < 1_000_000_000 for n in coords):
        return []
    points = [[coords[i], coords[i + 1]] for i in range(0, len(coords), 2)]
    if points[0] == points[-1]:
        points.pop()
    if len(points) < 3 or len(points) > 10_000:
        return []
    # Reject collinear/degenerate points (shoelace area).
    area2 = sum(a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1]))
    if abs(area2) < .001:
        return []
    return points


def _local_name(tag):
    return tag.rsplit('}', 1)[-1]


def textline_polygon(textline):
    """Read only the TextLine's own Shape/Polygon, never word/region shapes."""
    for child in textline:
        if _local_name(child.tag) != 'Shape':
            continue
        for polygon in child:
            if _local_name(polygon.tag) == 'Polygon':
                result = parse_alto_points(polygon.get('POINTS'))
                if result:
                    return result
    return []


def _source_geometry(path):
    root = ET.parse(path).getroot()
    if _local_name(root.tag) == 'PcGts':
        from .page_xml import inspect_page_xml
        pages = inspect_page_xml(path)['pages']
        return [[(line.get('alto_id'), line.get('polygon'),
                  tuple(line['bbox'][key] for key in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')))
                 for line in page['lines']] for page in pages]
    return [
        [(node.get('ID'), textline_polygon(node),
          tuple(node.get(x) for x in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')))
         for node in page.iter() if _local_name(node.tag) == 'TextLine']
        for page in root.iter() if _local_name(page.tag) == 'Page'
    ]


@lru_cache(maxsize=16)
def _cached_source_geometry(path, mtime_ns, size):
    return _source_geometry(path)


def page_line_polygons(witness, page, alto_page=None):
    """Return one polygon (or None) per saved ALTO line.

    Existing project snapshots without a ``polygon`` attribute are enriched
    *in memory only* from the original unchanged local source, if available.
    Index, ALTO ID and envelope coordinates are checked before associating a
    reread polygon with an existing persisted line.
    """
    if alto_page is None:
        from .imaging import mapped_alto_page
        alto_page = mapped_alto_page(witness, page)
    if not alto_page:
        return []
    lines = alto_page.get('lines', [])
    results = [line.get('polygon') or None for line in lines]
    if all(results) or not lines:
        return results
    binding = page.get('alto_binding') or {}
    source = next((s for s in witness.get('alto_sources', [])
                   if s.get('id') == binding.get('source_id')), None)
    if not source or not source.get('path'):
        return results
    try:
        path = Path(source['path'])
        stat = path.stat()
        # An old project may reference a file which has been replaced. Never
        # silently associate geometries from that different ALTO with its old IDs.
        if source.get('source_size') is not None and source['source_size'] != stat.st_size:
            return results
        if (source.get('source_mtime_ns') is not None and
                source['source_mtime_ns'] != stat.st_mtime_ns):
            import hashlib
            if (source.get('source_sha256') and
                    hashlib.sha256(path.read_bytes()).hexdigest() != source['source_sha256']):
                return results
        geometry = _cached_source_geometry(str(path), stat.st_mtime_ns, stat.st_size)
        entries = geometry[binding['page_index']]
        if len(entries) != len(lines):
            return results
        for i, (source_id, polygon, bbox) in enumerate(entries):
            line = lines[i]
            if not polygon or results[i]:
                continue
            if line.get('alto_id') and source_id != line['alto_id']:
                continue
            stored = line.get('bbox') or {}
            try:
                if any(abs(float(stored[k]) - float(v)) > 0.01
                       for k, v in zip(('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'), bbox)):
                    continue
            except (TypeError, ValueError, KeyError):
                continue
            results[i] = polygon
    except (OSError, ET.ParseError, KeyError, IndexError, TypeError, ValueError):
        pass
    return results


def polygon_contains(point, polygon):
    """Boundary-inclusive point-in-polygon test for sloping ALTO lines."""
    if not polygon or len(polygon) < 3:
        return False
    x, y = point
    inside = False
    prev_x, prev_y = polygon[-1]
    for next_x, next_y in polygon:
        # Include points on an edge to make narrow lines easy to select.
        cross = (x - prev_x) * (next_y - prev_y) - (y - prev_y) * (next_x - prev_x)
        if (abs(cross) < 1e-7 and
                min(prev_x, next_x) - 1e-7 <= x <= max(prev_x, next_x) + 1e-7 and
                min(prev_y, next_y) - 1e-7 <= y <= max(prev_y, next_y) + 1e-7):
            return True
        if (prev_y > y) != (next_y > y):
            crossing = prev_x + (y - prev_y) * (next_x - prev_x) / (next_y - prev_y)
            if x < crossing:
                inside = not inside
        prev_x, prev_y = next_x, next_y
    return inside
