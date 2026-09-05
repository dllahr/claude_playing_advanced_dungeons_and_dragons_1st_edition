"""Border trimming, and the render settings the database must carry.

Both come from B1. The frame matters because 33 of its 56 unreachable squares
were hillside and a compass rose rather than dungeon. The render settings
matter because a tool that reopens the page with its own defaults gets a
different grid, and then assigns everything it finds to the wrong edge.
"""
import os
import sqlite3

import pytest

import extract as E
import markers as M

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'schema.sql')


def framed(nx, ny, depth, interior='open'):
    """A map with a solid frame `depth`+1 cells thick and a clear interior."""
    t = {}
    for x in range(nx):
        for y in range(ny):
            edge = (x <= depth or y <= depth
                    or x >= nx - 1 - depth or y >= ny - 1 - depth)
            t[(x, y)] = 'solid' if edge else interior
    return t


@pytest.mark.parametrize('depth', [0, 1, 2])
def test_frame_depth_is_measured(depth):
    t = framed(20, 16, depth)
    assert E.frame_depth(t, 20, 16) == depth


def test_no_frame_is_reported_as_none():
    t = {(x, y): 'open' for x in range(12) for y in range(12)}
    assert E.frame_depth(t, 12, 12) == -1
    assert E.outside_cells(t, 12, 12) == set()


def test_a_pierced_side_still_finds_the_frame():
    """B1's south ring is hillside at 0.05 solid with the real frame behind it."""
    t = framed(20, 16, 1)
    for x in range(20):
        t[(x, 0)] = 'mixed'          # the ragged hill edge
    assert E.frame_depth(t, 20, 16) == 1


def test_scenery_in_the_frame_is_marked_outside():
    t = framed(20, 16, 1)
    for x in range(20):
        t[(x, 0)] = 'mixed'
    out = E.outside_cells(t, 20, 16)
    assert (5, 0) in out and (0, 5) in out
    assert (10, 8) not in out, 'the interior is untouched'


def test_an_entrance_through_the_frame_stays_walkable():
    """A frame square reading as clear floor is the way in, not scenery."""
    t = framed(20, 16, 1)
    for x in range(20):
        t[(x, 0)] = 'mixed'
    t[(9, 0)] = 'open'
    t[(9, 1)] = 'open'
    out = E.outside_cells(t, 20, 16)
    assert (9, 0) not in out and (9, 1) not in out
    assert (8, 0) in out


def test_render_settings_round_trip(tmp_path):
    """build.py must record what markers.py and highlight.py have to reproduce."""
    import build
    db = str(tmp_path / 'r.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name,pdf,page,dpi,channel,deskew_deg)"
                " VALUES (1,'t','/some/map.pdf',3,300,'r',-0.37)")
    con.commit(); con.close()
    cfg = M.render_settings(db, 1)
    assert cfg == dict(pdf='/some/map.pdf', page=3, dpi=300,
                       channel='r', deskew=-0.37)


def test_render_settings_absent_returns_none(tmp_path):
    con = sqlite3.connect(str(tmp_path / 'n.sqlite'))
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'t')")
    con.commit(); con.close()
    assert M.render_settings(str(tmp_path / 'n.sqlite'), 1) is None


def test_the_dmg_build_records_its_settings(dmg_db):
    cfg = M.render_settings(dmg_db, 1)
    assert cfg is not None
    assert cfg['channel'] == 'mean'
    assert cfg['dpi'] == 200
    assert abs(cfg['deskew']) < 0.06, 'the DMG sheet is square; nothing applied'
