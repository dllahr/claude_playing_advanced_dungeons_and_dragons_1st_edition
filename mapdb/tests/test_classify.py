"""Unit tests for the classification truth tables.

Thresholds are behaviour, not implementation detail: t_solid in particular was
wrong at 0.25 (it swallowed the quarter-open squares of a full-width diagonal
corridor and broke the passage into disconnected pieces), so it gets asserted
explicitly here.
"""
import pytest

import extract as E


def cell(open_frac, **kw):
    d = dict(open_frac=open_frac, rock_frac=1 - open_frac, ink_frac=0.0,
             edges_touched=0, rock_sides='', slots=0, ncomp=1,
             biggest=1.0, eta=0.9, i=0, j=0, x=0, y=0)
    d.update(kw)
    return d


@pytest.mark.parametrize('frac,expect', [
    (0.00, 'solid'), (0.03, 'solid'), (0.05, 'solid'),
    (0.08, 'mixed'), (0.25, 'mixed'), (0.50, 'mixed'), (0.74, 'mixed'),
    (0.75, 'open'), (0.99, 'open'), (1.00, 'open'),
])
def test_classify_thresholds(frac, expect):
    assert E.classify(cell(frac), t_solid=0.05, t_open=0.75) == expect


def test_quarter_open_square_is_not_solid():
    """A full-width 45-degree corridor leaves ~25% of a square open.

    Calling that solid severs the passage; the real DMG map had three such
    squares at open=0.25 and the corridor came out in disconnected pieces.
    """
    assert E.classify(cell(0.25), t_solid=0.05) == 'mixed'


def test_cell_confidence_is_high_only_at_the_extremes():
    assert E.cell_confidence(cell(0.0), 'solid') == 10
    assert E.cell_confidence(cell(0.02), 'solid') == 10
    assert E.cell_confidence(cell(0.04), 'solid') == 8
    assert E.cell_confidence(cell(1.0), 'open') == 10
    assert E.cell_confidence(cell(0.8), 'open') == 8
    assert E.cell_confidence(cell(0.5), 'mixed') == 3


def edge(thick=0.0, hole=0, aspect=1.0, slots=0, x=0, y=0, orient='V', gap=0.0):
    return dict(x=x, y=y, orient=orient, thick=thick, cover=0.0, gap=gap,
                hole=hole, hole_aspect=aspect, slots=slots)


OPEN_GRID = {(0, 0): 'open', (1, 0): 'open', (0, 1): 'open'}


def test_two_open_cells_with_a_thin_ruling_are_connected():
    kind, conf = E.classify_edge(edge(thick=2.0), OPEN_GRID, 4, 4)
    assert kind == 'open' and conf >= 8


def test_thick_bar_between_open_cells_is_a_wall():
    kind, conf = E.classify_edge(edge(thick=9.0), OPEN_GRID, 4, 4)
    assert kind == 'wall' and conf >= 8


def test_enclosed_hole_makes_it_a_door():
    kind, conf = E.classify_edge(edge(thick=6.0, hole=120, aspect=1.8),
                                 OPEN_GRID, 4, 4)
    assert kind == 'door' and conf >= 8


def test_long_thin_hole_is_a_stair_tread_not_a_door():
    """The staircase between areas 4 and 5 produced four phantom doors."""
    kind, _ = E.classify_edge(edge(thick=7.0, hole=130, aspect=6.4, slots=3),
                              OPEN_GRID, 4, 4)
    assert kind == 'stairs'


def test_tiny_hole_is_not_a_door():
    kind, _ = E.classify_edge(edge(thick=6.0, hole=25, aspect=1.2), OPEN_GRID, 4, 4)
    assert kind == 'wall'


def test_boundary_against_rock_is_a_wall():
    terrain = {(0, 0): 'open', (1, 0): 'solid'}
    kind, conf = E.classify_edge(edge(thick=0.0), terrain, 4, 4)
    assert kind == 'wall' and conf >= 9


def test_rock_to_rock_boundary_is_certain():
    terrain = {(0, 0): 'solid', (1, 0): 'solid'}
    kind, conf = E.classify_edge(edge(), terrain, 4, 4)
    assert kind == 'wall' and conf == 10


def test_edge_touching_a_mixed_cell_is_low_confidence():
    terrain = {(0, 0): 'open', (1, 0): 'mixed'}
    kind, conf = E.classify_edge(edge(thick=1.0), terrain, 4, 4)
    assert conf <= 5, 'a partial square is exactly where a human should look'


def test_off_map_boundary_is_a_wall_not_unknown():
    """The sheet edge bounds the map; it used to flood lowconf with noise."""
    terrain = {(3, 0): 'solid'}
    kind, conf = E.classify_edge(edge(x=3, y=0), terrain, 4, 4)
    assert kind == 'wall' and conf == 10


def test_is_door_rejects_wrong_shape_and_accepts_right_shape():
    assert E.is_door(edge(hole=120, aspect=1.8))
    assert not E.is_door(edge(hole=120, aspect=6.0))     # stair tread
    assert not E.is_door(edge(hole=20, aspect=1.0))      # too small
    assert not E.is_door(edge(hole=120, aspect=1.5, slots=3))   # a ladder


# --- boundaries between partly-filled squares -------------------------------

MIXED_PAIR = {(0, 0): 'mixed', (1, 0): 'mixed'}


def test_a_gap_in_the_boundary_makes_it_passable():
    """Rock must SPAN a boundary to close it.

    Two half-filled squares meeting along a boundary the rock only partly
    covers are still connected. Judging by median thickness alone severed
    seven passages on the DMG sheet that plainly connect on the page.
    """
    kind, _ = E.classify_edge(edge(thick=9.0, gap=0.5), MIXED_PAIR, 4, 4)
    assert kind == 'open'


def test_a_fully_spanned_boundary_is_still_a_wall():
    kind, _ = E.classify_edge(edge(thick=9.0, gap=0.0), MIXED_PAIR, 4, 4)
    assert kind == 'wall'


def test_gap_does_not_override_a_door():
    kind, _ = E.classify_edge(edge(thick=7.0, gap=0.5, hole=120, aspect=1.8),
                              MIXED_PAIR, 4, 4)
    assert kind == 'door'


def test_gap_is_ignored_when_a_neighbour_is_solid_rock():
    terrain = {(0, 0): 'mixed', (1, 0): 'solid'}
    kind, _ = E.classify_edge(edge(gap=1.0), terrain, 4, 4)
    assert kind == 'wall'


# --- diagonal passages ------------------------------------------------------

def sided(sides, klass='mixed'):
    return cell(0.4, rock_sides=sides), klass


@pytest.mark.parametrize('sides', ['NW', 'NE', 'SW', 'SE'])
def test_rock_on_two_adjacent_sides_is_a_diagonal(sides):
    """Rock in one corner means the floor runs corner to corner."""
    assert E.passage_kind(*sided(sides)) == 'diagonal'


@pytest.mark.parametrize('sides', ['NS', 'WE'])
def test_rock_on_opposite_sides_is_a_pinch_not_a_diagonal(sides):
    assert E.passage_kind(*sided(sides)) is None


@pytest.mark.parametrize('sides', ['', 'N', 'NSW', 'NSWE'])
def test_other_side_patterns_are_not_diagonals(sides):
    """NSWE in particular is the stream: a thread reaching every border."""
    assert E.passage_kind(*sided(sides)) is None


def test_only_partly_filled_squares_can_be_diagonals():
    assert E.passage_kind(cell(1.0, rock_sides='NW'), 'open') is None
    assert E.passage_kind(cell(0.0, rock_sides='NW'), 'solid') is None


def test_side_order_does_not_matter():
    assert E.passage_kind(*sided('WN')) == 'diagonal'


# --- label shielding --------------------------------------------------------

def test_label_boxes_cover_the_cell_interior_only():
    """The shield must not reach the boundary, where the rulings live."""
    grid = E.Grid(0.0, 40.0, 10, 0.0, 40.0, 10)
    boxes = E.label_boxes([(2, 9)], grid, inset=0.15)   # top-left cell
    (x0, y0, x1, y1), = boxes
    assert (x0, x1) == (86, 114)      # 80..120 inset by 6px each side
    assert (y0, y1) == (6, 34)


def test_label_boxes_skip_anchors_off_the_grid():
    grid = E.Grid(0.0, 40.0, 5, 0.0, 40.0, 5)
    assert E.label_boxes([(99, 99)], grid) == []


# --- stairs are a way through, not a barrier ---------------------------------

def test_stair_treads_are_passable_not_a_wall():
    """Stairs defeat both other tests and used to fall through to 'wall'.

    A ladder of treads reads as thick to the thickness test and as a stack of
    doors to the hole test, so both reject it. Calling the result a wall severs
    the passage the staircase belongs to -- on B1 it sealed the entrance
    corridor off from the other 1200 squares of the level.
    """
    kind, _ = E.classify_edge(edge(thick=9.0, hole=130, aspect=6.4, slots=3),
                              OPEN_GRID, 4, 4)
    assert kind == 'stairs'
    assert 'stairs' in __import__('dmap').PASSABLE


def test_is_stairs_needs_treads_and_a_long_thin_hole():
    assert E.is_stairs(edge(hole=130, aspect=6.4, slots=3))
    assert not E.is_stairs(edge(hole=130, aspect=1.5, slots=3))   # compact: a door
    assert not E.is_stairs(edge(hole=10, aspect=6.4, slots=3))    # too small
    assert not E.is_stairs(edge(hole=130, aspect=6.4, slots=0))   # no treads


def test_a_door_still_wins_over_stairs():
    kind, _ = E.classify_edge(edge(thick=7.0, hole=130, aspect=1.8, slots=0),
                              OPEN_GRID, 4, 4)
    assert kind == 'door'


def test_stairs_against_solid_rock_is_still_a_wall():
    terrain = {(0, 0): 'open', (1, 0): 'solid'}
    kind, _ = E.classify_edge(edge(hole=130, aspect=6.4, slots=3), terrain, 4, 4)
    assert kind == 'wall'
