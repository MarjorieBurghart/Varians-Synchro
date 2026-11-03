"""Unambiguous picking of visual ALTO lines when their bounding boxes overlap.

Pure geometry: no Qt dependency; remains usable in tests and on every Python
platform. The imported ALTO rectangles are never changed. At a click point
inside several boxes, prefer the nearest vertical centreline (and then the
closest horizontal centre), rather than the arbitrary graphics-item z-order.
"""
from __future__ import annotations

from math import isfinite


def choose_line_at(point, rectangles, *, fallback=None):
    """Return the (ordinal, bbox) index nearest the click within eligible boxes.

    `point` is (x, y); `rectangles` is an iterable of
    (ordinal, x, y, width, height) records for *visible* line overlays.
    Degenerate/non-finite boxes are ignored. If nothing contains the point,
    `fallback` (ordinarily the Qt item which received the click) is returned.

    Distance to the vertical midpoint is the main criterion because adjacent
    manuscript TextLine bounding boxes tend to overlap vertically, especially
    when the facsimile is displayed at reduced scale.
    """
    px, py = point
    candidates = []
    for ordinal, x, y, width, height in rectangles:
        if not all(isfinite(float(n)) for n in (x, y, width, height)):
            continue
        if width <= 0 or height <= 0:
            continue
        if not (x <= px <= x + width and y <= py <= y + height):
            continue
        vertical = abs(py - (y + height * 0.5)) / height
        horizontal = abs(px - (x + width * 0.5)) / width
        # Vertical distance dominates; horizontal distance resolves two-column
        # overlap or a short rubric lying inside a wider line rectangle.
        candidates.append((vertical, horizontal, width * height, ordinal))
    return min(candidates)[-1] if candidates else fallback


def choose_line_geometry(point, geometry, *, fallback=None):
    """Prefer actual ALTO polygons to overlapping bounding rectangles.

    Each record is ``(ordinal, x, y, width, height, polygon_or_none)`` in
    scene coordinates. Rectangle hit testing is only a fallback for lines
    whose ALTO source has *no* polygon. A sloping polygon's bounding rectangle
    cannot intercept clicks that belong to a neighbouring text line.
    """
    from .alto_geometry import polygon_contains
    polygon_hits = []
    rectangle_candidates = []
    px, py = point
    for ordinal, x, y, width, height, polygon in geometry:
        if polygon:
            if polygon_contains(point, polygon):
                centre = sum(v for _, v in polygon) / len(polygon)
                polygon_hits.append((abs(py - centre), ordinal))
        else:
            rectangle_candidates.append((ordinal, x, y, width, height))
    if polygon_hits:
        return min(polygon_hits)[-1]
    return choose_line_at(point, rectangle_candidates, fallback=fallback)
