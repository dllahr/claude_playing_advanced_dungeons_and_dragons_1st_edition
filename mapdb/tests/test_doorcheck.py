"""The one-sided door test: a door goes through the wall, furniture does not.

The fixtures here are the two shapes the printed page actually draws, built
from scratch so the assertions do not depend on the scan:

    a DOOR      a rectangle centred on a heavy wall bar
    FURNITURE   the same rectangle, wholly to one side of the same bar
    A ROOM      the same rectangle on a 2 px graph-paper ruling, no wall at all

The third case is the one that mattered most in practice. Six of B1's furnished
rooms produced fabricated doors, and the ovals and beds inside them sit on
nothing but a ruling -- there is no wall there for a door to be a hole in.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import extract as E                                             # noqa: E402


class FakeGrid(object):
    def __init__(self, px=40.0, py=40.0, nx=8, ny=8, x0=0.0, y0=0.0):
        self.px, self.py, self.nx, self.ny = px, py, nx, ny
        self.x0, self.y0 = x0, y0


def page(wall_thick=10, glyph_offset=0, wall=True, size=400, bar_row=200):
    """A horizontal wall across the page with a door rectangle on it.

    `glyph_offset` slides the rectangle off the bar, in pixels: 0 is a door,
    ~15 is a piece of furniture drawn against the wall.
    """
    rock = np.zeros((size, size), bool)
    t = wall_thick if wall else 2          # 2 px = graph-paper ruling
    rock[bar_row - t // 2:bar_row + t // 2 + t % 2, :] = True
    # The glyph: a hollow rectangle outline 24 x 14, enclosing 18 x 8 of white.
    # Sized to the real thing -- B1's doors enclose 134-187 px at 200 dpi -- so
    # that it fits inside the 0.50-cell sample box the way a real one does. An
    # oversized fixture gets clipped by the box, the white stops being enclosed,
    # and the test measures nothing.
    cy = bar_row + glyph_offset
    cx = size // 2
    y0, y1 = cy - 7, cy + 7
    x0, x1 = cx - 12, cx + 12
    rock[y0:y1, x0:x1] = True
    rock[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = False       # its enclosed white
    return rock


def edge_at(rock, orient='H', size=400, bar_row=200):
    """Measure the boundary running along `bar_row` of a synthetic page."""
    grid = FakeGrid(px=40.0, py=40.0)
    H, W = rock.shape
    cx, cy = size // 2, bar_row
    return E._edge(rock, 3, 3, orient, cx, cy, grid, 0.30, 0.25, 0.50, H, W)


def test_a_door_glyph_centred_on_the_wall_bar_is_not_suspect():
    e = edge_at(page(glyph_offset=0))
    assert e['hole'] > 0, 'the rectangle should enclose white'
    assert e['wall'] >= 5.0, 'a 10 px bar is a wall'
    assert e['offset'] < 0.14
    assert E.door_suspect(e) is None


def test_furniture_beside_the_wall_is_flagged_one_sided():
    """The area 24 failure: a drawn bed against an intact wall."""
    e = edge_at(page(glyph_offset=12))
    why = E.door_suspect(e)
    assert why is not None
    assert 'one-sided' in why


def test_furniture_on_a_bare_ruling_is_flagged_no_wall():
    """The area 27 failure: a dais drawn in open floor, no wall anywhere."""
    e = edge_at(page(glyph_offset=0, wall=False))
    why = E.door_suspect(e)
    assert why is not None
    assert 'no wall' in why


def test_the_offset_grows_as_the_glyph_slides_off_the_bar():
    offs = [edge_at(page(glyph_offset=d))['offset'] for d in (0, 4, 8, 12)]
    assert all(b > a for a, b in zip(offs, offs[1:])), offs


def test_flank_measures_the_wall_beside_the_glyph_not_the_glyph():
    """`thick` samples inside the door box, which is why it never worked.

    The regression this pins: area 24's fabrications measured THICKER than the
    genuine door next to them, because the band being measured was the glyph.
    """
    rock = page(wall_thick=10, glyph_offset=0)
    grid = FakeGrid()
    H, W = rock.shape
    thick, pos = E._flank(rock, 200, 200, 'H', grid, 0.30, H, W)
    assert 8 <= thick <= 12, 'should report the 10 px bar, not the 22 px glyph'
    assert abs(pos - 200) < 3, 'and should locate it at the bar'


def test_a_glyph_with_no_enclosed_white_has_no_offset_to_measure():
    rock = np.zeros((400, 400), bool)
    rock[195:205, :] = True                    # a plain wall, no door
    e = edge_at(rock)
    assert e['hole'] == 0
    assert e['offset'] is None


def test_door_suspect_never_raises_on_an_edge_with_no_measurements():
    """classify_edge short-circuits tiny boundaries and returns a stub dict."""
    assert E.door_suspect(dict(x=0, y=0, orient='H')) is not None


@pytest.mark.parametrize('orient,bar', [('H', 200), ('V', 200)])
def test_the_test_works_in_both_orientations(orient, bar):
    rock = page(glyph_offset=0)
    if orient == 'V':
        rock = rock.T
    e = edge_at(rock, orient=orient)
    assert E.door_suspect(e) is None
