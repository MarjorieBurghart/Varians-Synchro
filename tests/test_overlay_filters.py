"""Core overlay semantics: independent of Qt and safe on CI servers."""
import pytest
from varians_synchro.overlay_filters import (
    style_for_link, overlay_visible, FILTER_ALL, FILTER_UNLINKED,
    FILTER_AUTOMATIC_REVIEW,
)


def test_style_classification_and_geometry_origin():
    assert style_for_link({'origin': 'manual', 'state': 'validated', 'kind': 'correspondence'}) == 'manual_validated'
    assert style_for_link({'origin': 'manual', 'state': 'uncertain', 'kind': 'correspondence'}) == 'manual_uncertain'
    assert style_for_link({'origin': 'interpolated-geometry', 'state': 'uncertain', 'kind': 'correspondence'}) == 'automatic_uncertain'
    assert style_for_link({'origin': 'automatic-htr-htr', 'state': 'proposed', 'kind': 'correspondence'}) == 'automatic_uncertain'
    assert style_for_link({'origin': 'automatic-htr-htr', 'state': 'validated', 'kind': 'correspondence'}) == 'automatic_validated'
    assert style_for_link({'origin': 'manual', 'state': 'validated', 'kind': 'absence'}) == 'absence'
    assert style_for_link({'state': 'validated', 'kind': 'correspondence'}) == 'manual_validated'  # legacy


@pytest.mark.parametrize('style', [
    'default', 'manual_validated', 'manual_uncertain',
    'automatic_uncertain', 'automatic_validated', 'absence',
])
def test_all_filter_includes_every_line(style):
    assert overlay_visible(style, FILTER_ALL)


@pytest.mark.parametrize('style,unlinked,auto_review', [
    ('default', True, False),
    ('manual_validated', False, False),
    ('manual_uncertain', False, False),
    ('automatic_validated', False, False),
    ('automatic_uncertain', False, True),
    ('absence', False, False),
])
def test_filters_are_precise_and_not_confused_with_link_status(style, unlinked, auto_review):
    assert overlay_visible(style, FILTER_UNLINKED) is unlinked
    assert overlay_visible(style, FILTER_AUTOMATIC_REVIEW) is auto_review


def test_selected_lines_remain_visible_without_altering_state():
    for mode in (FILTER_ALL, FILTER_UNLINKED, FILTER_AUTOMATIC_REVIEW):
        assert overlay_visible('manual_validated', mode, selected=True)
        assert overlay_visible('default', mode, selected=True)
    assert not overlay_visible('manual_validated', FILTER_UNLINKED)


def test_invalid_filter_rejected():
    with pytest.raises(ValueError):
        overlay_visible('default', 'not-a-filter')
