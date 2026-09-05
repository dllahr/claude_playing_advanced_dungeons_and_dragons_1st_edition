"""Unit tests for the rock/ink split and the shape primitives.

These cover the four discriminators the extractor rests on: connectivity
(rock vs printed annotation), stroke thickness (ruling vs drawn wall),
enclosed white (door vs wall), and hole shape / band count (door vs stairs).
"""
import numpy as np
import pytest

import extract as E
import synth as S


def test_rock_mask_keeps_the_rock_and_drops_the_numeral(simple):
    m, grey, truth = simple
    rock, ink = E.rock_mask(grey)
    # the numeral planted at (6,6) must land in ink, not rock
    lx, ly = 6, 6
    grid = E.fit_grid(grey, E.find_field(grey))
    j = grid.ny - 1 - ly
    xa, xb, ya, yb = (int(v) for v in grid.box(lx, j, inset=0.15))
    assert ink[ya:yb, xa:xb].sum() > 100, 'numeral should be in the ink layer'
    assert rock[ya:yb, xa:xb].mean() < 0.15, 'numeral must not read as rock'


def test_rock_mask_ink_is_a_small_fraction(simple):
    _, grey, _ = simple
    rock, ink = E.rock_mask(grey)
    assert 0 < ink.mean() < 0.05
    assert rock.mean() > 0.3
    assert not (rock & ink).any(), 'rock and ink must be disjoint'


def test_rock_mask_min_area_controls_the_split():
    """Raising min_area moves more of the drawing out of rock into ink."""
    m = S.SynthMap(nx=6, ny=6).open_rect(1, 1, 4, 4)
    grey = m.render()
    small, _ = E.rock_mask(grey, min_area=100)
    big, _ = E.rock_mask(grey, min_area=10 ** 7)
    assert small.sum() > big.sum()
    assert big.sum() == 0


def test_holes_finds_an_enclosed_rectangle():
    p = np.zeros((30, 30), bool)
    p[5:25, 5:25] = True
    p[9:21, 9:21] = False          # a 12x12 hole
    area, aspect, slots, centroid = E._holes(p)
    assert area == pytest.approx(144, rel=0.1)
    assert aspect == pytest.approx(1.0, abs=0.2)
    assert slots == 0


def test_holes_flags_thin_slots_as_slots_not_doors():
    """Stair treads enclose white too, but long and thin."""
    p = np.ones((40, 40), bool)
    for k in range(4):
        p[6 + k * 8: 10 + k * 8, 4:36] = False   # 4 x 32 slots
    area, aspect, slots, centroid = E._holes(p)
    assert slots >= 3
    assert aspect > 3.0


def test_holes_returns_zero_when_nothing_enclosed():
    assert E._holes(np.zeros((20, 20), bool)) == (0, 0.0, 0, None)
    assert E._holes(np.ones((20, 20), bool)) == (0, 0.0, 0, None)


def test_hatch_counts_alternating_bands():
    p = np.zeros((40, 40), bool)
    for k in range(5):
        p[4 + k * 7: 7 + k * 7, :] = True
    assert E._hatch(p) >= 9          # 5 bars => 10 transitions


def test_hatch_is_zero_on_uniform_fields():
    assert E._hatch(np.zeros((30, 30), bool)) == 0
    assert E._hatch(np.ones((30, 30), bool)) == 0


def test_hatch_low_for_a_single_diagonal():
    p = np.zeros((40, 40), bool)
    for i in range(40):
        p[i, max(0, i - 6):min(40, i + 6)] = True
    assert E._hatch(p) <= 4


def test_edge_thickness_separates_ruling_from_wall(simple):
    """The core measurement: a printed ruling is thin, a drawn bar is not."""
    m, grey, truth = simple
    rock, _ = E.rock_mask(grey)
    grid = E.fit_grid(grey, E.find_field(grey))
    stats = {(e['x'], e['y'], e['orient']): e for e in E.edge_stats(rock, grid)}
    wall = stats[(7, 6, 'V')]        # planted wall bar
    plain = stats[(2, 6, 'V')]       # ordinary ruling between two open cells
    assert wall['thick'] > plain['thick'] + 3
    assert plain['thick'] < E.classify_edge.__defaults__[0]   # below t_thick
    assert wall['thick'] >= E.classify_edge.__defaults__[0]
