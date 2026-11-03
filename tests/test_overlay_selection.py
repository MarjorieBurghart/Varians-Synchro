from varians_synchro.overlay_selection import choose_line_at


def test_picks_closer_line_centre_not_last_drawn():
    rects = [
        (3, 30, 90, 300, 38),
        (4, 30, 111, 300, 40),
    ]
    # Both rectangles overlap between y=111 and y=128.
    assert choose_line_at((150, 113), rects) == 3
    assert choose_line_at((150, 125), rects) == 4
    assert choose_line_at((150, 300), rects) is None


def test_column_disambiguation_same_y():
    # Overwide TextLine rectangles overlap into the neighbouring column.
    rects = [(1, 0, 10, 350, 20), (2, 240, 10, 350, 20)]
    assert choose_line_at((255, 20), rects) == 1
    assert choose_line_at((330, 20), rects) == 2


def test_fallback_and_malformed_rectangles():
    assert choose_line_at((10, 10), [(0, 0, 0, 0, 20)], fallback=7) == 7
    assert choose_line_at((10, 10), [(0, 0, 0, float('nan'), 20)], fallback=7) == 7


def test_ignores_unrelated_rectangles_and_keeps_fallback():
    assert choose_line_at((200, 200), [(0, 0, 0, 100, 100)], fallback=0) == 0
