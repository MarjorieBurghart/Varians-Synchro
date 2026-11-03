"""Regression for witness-wide clicks, Ctrl toggle and Shift spans."""
from varians_synchro.selection_policy import update_line_selection as update


ORDER = tuple(f'w::f{folio}::l{i}' for folio in range(2) for i in range(1, 5))


def test_plain_click_replaces_selection_even_on_another_folio():
    initial = {ORDER[0], ORDER[3], ORDER[5]}
    selected, anchor = update(initial, ORDER[6], ORDER, anchor=ORDER[3])
    assert selected == {ORDER[6]}
    assert anchor == ORDER[6]


def test_ctrl_click_toggles_only_one_line_and_updates_anchor():
    selected, anchor = update(set(), ORDER[0], ORDER)
    selected, anchor = update(selected, ORDER[4], ORDER, anchor=anchor, ctrl=True)
    assert selected == {ORDER[0], ORDER[4]}
    selected, anchor = update(selected, ORDER[0], ORDER, anchor=anchor, ctrl=True)
    assert selected == {ORDER[4]}
    assert anchor == ORDER[0]


def test_shift_selects_inclusive_range_across_folios():
    selected, anchor = update({ORDER[1], ORDER[7]}, ORDER[2], ORDER)
    selected, anchor = update(selected, ORDER[5], ORDER, anchor=anchor, shift=True)
    assert selected == set(ORDER[2:6])
    assert anchor == ORDER[2]


def test_ctrl_shift_unions_range_with_existing_individual_selection():
    selected, anchor = update({ORDER[0], ORDER[2]}, ORDER[6], ORDER,
                              anchor=ORDER[2], ctrl=True, shift=True)
    assert selected == {ORDER[0], *ORDER[2:7]}
    assert anchor == ORDER[2]


def test_shift_in_reverse_direction_and_missing_anchor_is_safe():
    selected, anchor = update({}, ORDER[7], ORDER, anchor=ORDER[4], shift=True)
    assert selected == set(ORDER[4:8])
    selected, anchor = update({ORDER[0]}, ORDER[3], ORDER, anchor='obsolete', shift=True)
    assert selected == {ORDER[3]}
    assert anchor == ORDER[3]


def test_witness_selections_remain_independent():
    mu, a = update(set(), ORDER[0], ORDER)
    f_order = tuple(x.replace('w::', 'f::') for x in ORDER)
    fr, b = update(set(), f_order[1], f_order)
    mu, a = update(mu, ORDER[2], ORDER, anchor=a)
    assert mu == {ORDER[2]}
    assert fr == {f_order[1]}
