"""The hand-made label tables, and what detection is measured against.

These files are the source of record for where each area is labelled, so the
parser has to be exact: a dropped sub-location is how "2B" went missing from
the DMG key, and a flattened multi-cell entry is how a straddling label ends up
half-shielded and fabricates a wall.
"""
import os

import pytest

import label_file as LF

ARCHIVE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       '..', 'dlwork', 'archive')
DMG = os.path.join(ARCHIVE, '2026-08-24_dmg_lv1_number_locations.txt')
B1 = os.path.join(ARCHIVE, '2026-08-24_b1_lv1_number_locations.txt')


def test_plain_number_parses():
    assert LF.normalise('12') == ['12']


def test_sub_location_is_qualified_by_its_area():
    """Areas 1 and 2 each have an A and a B; a flat namespace loses one of each."""
    assert LF.normalise('B (for 2)') == ['2B']
    assert LF.normalise('A (for 1)') == ['1A']


def test_number_letter_yields_both_keys():
    """The sheet prints "1A": it is the area label and its sub-location at once."""
    assert LF.normalise('1A') == ['1', '1A']


@pytest.mark.skipif(not os.path.exists(DMG), reason='ground truth not present')
def test_dmg_table_has_every_area_and_no_letter_collisions():
    r = LF.load(DMG)
    for n in range(1, 40):
        assert str(n) in r, 'area %d missing' % n
    assert r['1B'] != r['2B'], 'the two Bs must not collapse together'
    assert len(r['39']) == 4, 'area 39 straddles four squares'
    assert (18, 0) not in r['39'], 'the old anchor was two squares out'


@pytest.mark.skipif(not os.path.exists(B1), reason='ground truth not present')
def test_b1_table_keeps_repeats_and_straddles():
    r = LF.load(B1)
    for n in range(1, 38):
        assert str(n) in r, 'area %d missing' % n
    assert len(r['1']) == 6, 'area 1 is printed six times'
    assert len(r['35']) == 5
    assert len(r['12']) == 2, 'a straddling label occupies two squares'
    assert len(LF.all_cells(r)) == 58


@pytest.mark.skipif(not os.path.exists(B1), reason='ground truth not present')
def test_anchors_pick_one_cell_each():
    r = LF.load(B1)
    a = LF.anchors(r)
    assert len(a) == len(r)
    assert all(isinstance(v, tuple) and len(v) == 2 for v in a.values())
    assert a['12'] == r['12'][0]


def test_duplicate_coordinates_are_not_repeated(tmp_path):
    p = tmp_path / 't.txt'
    p.write_text('number\tlocations\n7\t(1,2) (1,2) (3,4)\n')
    assert LF.load(str(p))['7'] == [(1, 2), (3, 4)]


def test_notes_column_is_not_scanned_for_coordinates(tmp_path):
    """A note may mention another square without that being a label position."""
    p = tmp_path / 't.txt'
    p.write_text('number\tlocations\tnotes\n7\t(1,2)\tnear (9,9) but not on it\n')
    assert LF.load(str(p))['7'] == [(1, 2)]


def test_blank_and_comment_lines_are_skipped(tmp_path):
    p = tmp_path / 't.txt'
    p.write_text('number\tlocations\n\n# a comment\n7\t(1,2)\n')
    assert LF.load(str(p)) == {'7': [(1, 2)]}


def test_digit_height_learns_the_modal_height():
    import eval_labels as EV
    boxes = [[0, 0, 10, 19, 100]] * 8 + [[0, 0, 10, 30, 100]] * 2
    assert EV.digit_height(boxes) == 19


def test_digit_height_is_none_when_there_is_nothing_to_learn():
    import eval_labels as EV
    assert EV.digit_height([]) is None
