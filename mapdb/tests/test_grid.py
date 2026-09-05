"""Unit tests for grid registration: does the fit recover what was planted?"""
import numpy as np
import pytest

import extract as E
import synth as S


def test_fit_axis_recovers_planted_pitch(simple):
    _, grey, truth = simple
    field = E.find_field(grey)
    gx, gy = E._gradients(grey, field)
    px, phx, _ = E.fit_axis(gx)
    py, phy, _ = E.fit_axis(gy)
    assert px == pytest.approx(truth['pitch'], abs=0.5)
    assert py == pytest.approx(truth['pitch'], abs=0.5)


def test_fit_phase_lands_on_a_grid_line(simple):
    _, grey, truth = simple
    field = E.find_field(grey)
    gx, _ = E._gradients(grey, field)
    ph, _ = E.fit_phase(gx, truth['pitch'])
    # the fitted phase must be an integer number of pitches from the true origin
    offset = (field[2] + ph - truth['margin']) % truth['pitch']
    assert min(offset, truth['pitch'] - offset) < 2.0


def test_find_field_brackets_the_drawn_area(simple):
    _, grey, truth = simple
    r0, r1, c0, c1 = E.find_field(grey)
    m, p = truth['margin'], truth['pitch']
    assert c0 == pytest.approx(m, abs=4)
    assert r0 == pytest.approx(m, abs=4)
    assert c1 == pytest.approx(m + truth['nx'] * p, abs=4)
    assert r1 == pytest.approx(m + truth['ny'] * p, abs=4)


def test_grid_covers_every_planted_cell(simple):
    _, grey, truth = simple
    grid = E.fit_grid(grey, E.find_field(grey))
    assert grid.px == pytest.approx(truth['pitch'], abs=0.6)
    assert grid.nx >= truth['nx'] - 1
    assert grid.ny >= truth['ny'] - 1


def test_gy_inverts_row_index():
    g = E.Grid(0, 40, 10, 0, 40, 8)
    assert g.gy(0) == 7          # top image row is the northernmost dungeon row
    assert g.gy(7) == 0
    assert [g.gy(j) for j in range(8)] == list(range(7, -1, -1))


def test_box_is_inset_within_the_cell():
    g = E.Grid(100.0, 40.0, 5, 200.0, 40.0, 5)
    xa, xb, ya, yb = g.box(0, 0, inset=0.1)
    assert xa == pytest.approx(104.0)
    assert xb == pytest.approx(136.0)
    assert ya == pytest.approx(204.0)
    assert yb == pytest.approx(236.0)


@pytest.mark.parametrize('angle', [-1.5, 0.0, 1.5])
def test_rotation_check_detects_skew(angle):
    m = S.simple_map()
    grey = m.render(rotate=angle)
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)
    rot = E.rotation_check(grey, field, grid.px)
    if angle == 0.0:
        assert abs(rot['angle_deg']) < 0.35
    else:
        # sign and rough magnitude; band fitting is coarse by construction
        assert abs(rot['angle_deg']) > 0.3
        assert rot['monotonic']
        assert np.sign(rot['angle_deg']) == np.sign(angle)


def test_rotation_check_unwraps_phase_across_the_pitch():
    """A phase that wraps past the pitch must not read as a huge jump."""
    m = S.simple_map()
    grey = m.render()
    field = E.find_field(grey)
    rot = E.rotation_check(grey, field, 40.0)
    assert abs(rot['drift']) < 40.0
