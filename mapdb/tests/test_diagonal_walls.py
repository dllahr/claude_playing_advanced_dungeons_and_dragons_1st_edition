"""45-degree walls: the rock is INSIDE the square, where no boundary can see it.

The test that matters is `test_a_diagonal_corridor_...does_not_fire`. A diagonal
wall and a diagonal corridor of the same width put rock in the SAME TWO CORNERS
of a square -- corner occupancy cannot tell them apart, and calling a corridor a
wall would seal a passage the party has to walk down. The fixtures here plant
one of each and assert the detector separates them.

The rest pins the two things the study measured and the one thing that is easy
to get wrong: the rock-fraction gate. Solid rock projects onto a diagonal
perfectly (its anti-diagonal is full, peak 1.00), so without the gate every
square of the rock mass is a "diagonal wall".
"""
import numpy as np
import pytest

import diagcheck
import extract as E
import synth as S


def patches(m):
    """{(x, y): rock patch} for a synthetic map, sampled as cell_stats does."""
    grey = m.render()
    rock, _ = E.rock_mask(grey)
    grid = E.fit_grid(grey, E.find_field(grey))
    H, W = rock.shape
    out = {}
    for x in range(m.nx):
        for y in range(m.ny):
            xa, xb, ya, yb = grid.box(x, grid.ny - 1 - y)
            out[(x, y)] = rock[max(0, int(round(ya))):min(H, int(round(yb))),
                               max(0, int(round(xa))):min(W, int(round(xb)))]
    return out


def wall_map(x0, y0, x1, y1, width=8):
    """A partition drawn across an open room -- floor on BOTH sides of it."""
    m = S.SynthMap(nx=16, ny=12).open_rect(2, 2, 9, 9)
    m.rulings()
    m.diagonal_wall(x0, y0, x1, y1, width=width)
    return m


def corridor_map(width):
    """The same line cut through solid rock: a passage, not a wall."""
    m = S.SynthMap(nx=16, ny=12)
    m.rulings()
    m.diagonal(3, 3, 8, 8, width=width)
    return m


# --- the wall ---------------------------------------------------------------

@pytest.mark.parametrize('ends,orient', [
    ((3, 3, 8, 8), 'SWNE'),
    ((3, 8, 8, 3), 'NWSE'),
])
def test_a_planted_diagonal_wall_is_detected_at_its_planted_orientation(ends, orient):
    m = wall_map(*ends)
    P = patches(m)
    assert m.truth()['diagonals'], 'the fixture should record what it drew'
    for cell, planted in m.truth()['diagonals'].items():
        assert planted == orient
        got, peak, _ = E.diagonal_stat(P[cell])
        assert peak >= E.DIAG_PEAK, '%s scored %.2f' % (cell, peak)
        assert got == orient, '%s read as %s' % (cell, got)


def test_an_ordinary_open_square_beside_the_wall_does_not_fire():
    P = patches(wall_map(3, 3, 8, 8))
    assert E.diagonal_stat(P[(5, 3)]) == (None, 0.0, 0.0)


def test_the_wall_leaves_the_square_a_third_rock_which_is_why_the_band_is_wide():
    """A normal-weight wall crossing a square covers about a third of it.

    B1's twelve partitions measure 0.27-0.42 against this fixture's 0.33, so the
    0.15-0.45 band is describing the same object, not a tuned threshold.
    """
    P = patches(wall_map(3, 3, 8, 8))
    for cell in [(4, 4), (5, 5), (6, 6), (7, 7)]:
        assert E.DIAG_LO <= P[cell].mean() <= E.DIAG_HI


# --- the corridor: the distinction corner occupancy gets wrong ---------------

@pytest.mark.parametrize('width,why', [
    (8, 'the same width as the wall'),
    (20, 'the same ROCK FRACTION as the wall -- corner for corner identical'),
])
def test_a_diagonal_corridor_does_not_fire(width, why):
    """A corridor is a way THROUGH. Calling it a wall seals a passage.

    Rock in the north-west and south-east corners of a square is EITHER a NW-SE
    wall OR the flanks of a SW-NE corridor, so corner occupancy fires on both
    (precision 0.69 on B1, its false positives all of this kind). The Radon peak
    separates them: a wall is one line the full width of the cell, while a
    corner wedge's hypotenuse only gets that long by filling the square.
    """
    P = patches(corridor_map(width))
    for cell in [(4, 4), (5, 5), (6, 6), (7, 7)]:
        orient, peak, _ = E.diagonal_stat(P[cell])
        assert peak < E.DIAG_PEAK, '%s (%s) scored %.2f' % (cell, why, peak)


def test_the_corridor_at_the_walls_rock_fraction_is_rejected_on_the_peak_alone():
    """Not by the gate -- it passes the gate. The 45-degree line is what differs."""
    P = patches(corridor_map(20))
    rk = P[(6, 6)]
    assert E.DIAG_LO <= rk.mean() <= E.DIAG_HI, 'must be inside the gate to count'
    assert E.diagonal_stat(rk)[1] < 0.75


# --- the rock-fraction gate -------------------------------------------------

def test_the_gate_rejects_solid_rock_although_it_projects_perfectly():
    """Solid rock's anti-diagonal is full, so the peak alone reads it as a wall."""
    solid = np.ones((30, 30), bool)
    assert E.diagonal_stat(solid, 0.0, 1.0)[1] == pytest.approx(1.0)
    assert E.diagonal_stat(solid) == (None, 0.0, 0.0)


def test_the_gate_rejects_an_empty_square():
    assert E.diagonal_stat(np.zeros((30, 30), bool)) == (None, 0.0, 0.0)


def test_an_orthogonal_wall_projects_onto_the_orthogonal_axis_not_a_diagonal():
    rk = np.zeros((30, 30), bool)
    rk[11:19, :] = True                       # a horizontal bar, 0.27 of the cell
    assert E.DIAG_LO <= rk.mean() <= E.DIAG_HI
    assert E.diagonal_stat(rk)[1] < 0.5


def test_diagonal_suspect_never_raises_on_a_cell_with_no_measurements():
    assert E.diagonal_suspect(dict(x=0, y=0)) is None


# --- the topological side split ---------------------------------------------

@pytest.mark.parametrize('ends,orient,classes', [
    ((3, 3, 8, 8), 'SWNE', ('NW', 'SE')),
    ((3, 8, 8, 3), 'NWSE', ('NE', 'SW')),
])
def test_the_wall_cuts_the_square_into_two_side_classes(ends, orient, classes):
    P = patches(wall_map(*ends))
    for cell in m_cells(ends):
        assert E.side_classes(P[cell]) == classes
        assert E.split_orient(E.side_classes(P[cell])) == orient


def m_cells(ends):
    x0, y0, x1, y1 = ends
    sx, sy = (1 if x1 >= x0 else -1), (1 if y1 >= y0 else -1)
    return [(x0 + k * sx, y0 + k * sy)
            for k in range(1, max(abs(x1 - x0), abs(y1 - y0)))]


def test_an_open_square_is_one_class_reaching_all_four_sides():
    P = patches(wall_map(3, 3, 8, 8))
    assert E.side_classes(P[(5, 3)]) == ('NSEW',)
    assert E.split_orient(E.side_classes(P[(5, 3)])) is None


def test_a_diagonal_corridor_is_one_component_touching_all_four_sides():
    """The reason this test succeeds where corner occupancy fails: the corridor's
    floor is connected, so its sides are mutually reachable and it is not a split."""
    P = patches(corridor_map(20))
    for cell in [(4, 4), (5, 5), (6, 6), (7, 7)]:
        assert E.side_classes(P[cell]) == ('NSEW',)
        assert E.split_orient(E.side_classes(P[cell])) is None


def test_a_furniture_sliver_against_a_wall_is_not_a_side_class():
    """Why side_classes drops components below min_area.

    B1's rooms are drawn full of furniture and a table against a wall shaves a
    sliver off the floor. Unfiltered, a fifth of the sheet reports three or four
    classes and the topology test's precision collapses from 0.85 to 0.07.
    """
    rk = patches(wall_map(3, 3, 8, 8))[(5, 5)].copy()
    rk[0:11, 3:6] = rk[10:13, 0:6] = True      # a cupboard against the west wall
    assert E.side_classes(rk, min_area=0.0) == ('NW', 'SE', 'W'), \
        'the sliver reaches a third of the west border'
    assert E.side_classes(rk) == ('NW', 'SE')
    assert E.split_orient(E.side_classes(rk)) == 'SWNE'


# --- wiring and the proposed corrections ------------------------------------

def test_cell_stats_carries_the_diagonal_measurement():
    m = wall_map(3, 3, 8, 8)
    grey = m.render()
    rock, ink = E.rock_mask(grey)
    grid = E.fit_grid(grey, E.find_field(grey))
    by = {(s['x'], s['y']): s for s in E.cell_stats(grey, rock, ink, grid)}
    for cell in m_cells((3, 3, 8, 8)):
        s = by[cell]
        assert s['diag_orient'] == 'SWNE'
        assert s['diag_peak'] >= E.DIAG_PEAK
        assert E.diagonal_suspect(s)
        assert E.split_orient(s['side_classes']) == 'SWNE'
    assert E.diagonal_suspect(by[(5, 3)]) is None


def test_the_staircase_corrections_seal_the_side_the_square_is_assigned_to():
    """Area 34's hand corrections, re-derived.

    (26,24) carries a SW-NE wall and the player assigned it to area 34, on the
    north-west side; `edge 26 23 H wall` and `edge 26 24 V wall` are the south
    and east boundaries of that square, and the first is line for line one of
    the five corrections in b1_corrections.tsv.
    """
    s = dict(x=26, y=24, diag_orient='SWNE', diag_peak=1.0)
    nw = [ln.split('\t')[:5] for ln in diagcheck.corrections(s, 'NW')]
    assert nw == [['edge', '26', '23', 'H', 'wall'],
                  ['edge', '26', '24', 'V', 'wall']]
    se = [ln.split('\t')[:5] for ln in diagcheck.corrections(s, 'SE')]
    assert se == [['edge', '26', '24', 'H', 'wall'],
                  ['edge', '25', '24', 'V', 'wall']]


def test_the_two_assignments_between_them_name_all_four_sides():
    """Whichever side owns the square, the wall is sealed against the other."""
    for orient, a, b in (('SWNE', 'NW', 'SE'), ('NWSE', 'NE', 'SW')):
        s = dict(x=5, y=5, diag_orient=orient, diag_peak=1.0)
        got = set()
        for side in (a, b):
            for ln in diagcheck.corrections(s, side):
                got.add(tuple(ln.split('\t')[1:4]))
        assert got == {('5', '4', 'H'), ('5', '5', 'H'),
                       ('4', '5', 'V'), ('5', '5', 'V')}


def test_diagcheck_writes_nothing_and_proposes_nothing_for_an_unknown_orientation():
    assert diagcheck.corrections(dict(x=1, y=1, diag_orient=None,
                                      diag_peak=0.0), 'NW') == []
