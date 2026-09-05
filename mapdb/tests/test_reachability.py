"""Integration tests for the connectivity check.

Every non-solid square on a level should be reachable from the entrance. A
square that is not is either genuinely isolated or -- far more often --
evidence of a wall the extractor invented or a door it missed.
"""
import os
import sqlite3

import pytest

import dmap


def make_db(tmp_path, cells, edges, rooms=(), schema=None):
    """Build a minimal level. `cells` maps (x,y) -> terrain or (terrain, passage)."""
    schema = schema or os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'schema.sql')
    db = str(tmp_path / 'test.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'test')")
    for (x, y), v in cells.items():
        terrain, passage = (v, None) if isinstance(v, str) else v
        con.execute('INSERT INTO cells (level,x,y,terrain,passage,confidence)'
                    ' VALUES (1,?,?,?,?,10)', (x, y, terrain, passage))
    for (x, y, o), kind in edges.items():
        con.execute('INSERT INTO edges (level,x,y,orient,kind,confidence)'
                    ' VALUES (1,?,?,?,?,10)', (x, y, o, kind))
    for number, x, y in rooms:
        con.execute('INSERT INTO rooms (level,number,anchor_x,anchor_y)'
                    ' VALUES (1,?,?,?)', (number, x, y))
    con.commit(); con.close()
    return db


def straight_corridor(tmp_path, kinds):
    """Cells (0,0)..(n,0) all open, with the given kinds on the V edges."""
    cells = {(x, 0): 'open' for x in range(len(kinds) + 1)}
    edges = {(x, 0, 'V'): k for x, k in enumerate(kinds)}
    return make_db(tmp_path, cells, edges, rooms=[('1', 0, 0)])


def test_open_corridor_is_fully_reachable(tmp_path):
    db = straight_corridor(tmp_path, ['open'] * 4)
    out = dmap.reachable(db, 1, from_room='1')
    assert 'UNREACHED 0' in out[0]


@pytest.mark.parametrize('kind', ['door', 'secret', 'concealed', 'archway',
                                  'trap_door', 'one_way', 'portcullis'])
def test_every_passable_kind_is_traversable(tmp_path, kind):
    db = straight_corridor(tmp_path, ['open', kind, 'open'])
    out = dmap.reachable(db, 1, from_room='1')
    assert 'UNREACHED 0' in out[0], '%s should be passable' % kind


def test_a_wall_severs_the_corridor(tmp_path):
    db = straight_corridor(tmp_path, ['open', 'wall', 'open'])
    out = dmap.reachable(db, 1, from_room='1')
    assert 'UNREACHED 2' in out[0]


def test_unknown_edge_does_not_conduct(tmp_path):
    db = straight_corridor(tmp_path, ['open', 'unknown', 'open'])
    out = dmap.reachable(db, 1, from_room='1')
    assert 'UNREACHED 2' in out[0]


def test_mixed_squares_are_walkable(tmp_path):
    """A partly-filled square is still floor; a diagonal corridor depends on it."""
    cells = {(0, 0): 'open', (1, 0): 'mixed', (2, 0): 'open'}
    edges = {(0, 0, 'V'): 'open', (1, 0, 'V'): 'open'}
    db = make_db(tmp_path, cells, edges, rooms=[('1', 0, 0)])
    assert 'UNREACHED 0' in dmap.reachable(db, 1, from_room='1')[0]


def test_full_width_diagonal_needs_no_special_handling(tmp_path):
    """The clipped squares make the chain orthogonally contiguous."""
    chain = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
    cells = {c: 'mixed' for c in chain}
    edges = {(0, 0, 'V'): 'open', (1, 0, 'H'): 'open',
             (1, 1, 'V'): 'open', (2, 1, 'H'): 'open'}
    db = make_db(tmp_path, cells, edges, rooms=[('1', 0, 0)])
    assert 'UNREACHED 0' in dmap.reachable(db, 1, from_room='1')[0]


def test_half_width_diagonal_connects_only_at_the_corner(tmp_path):
    """The bridging squares hold no floor, so the corner step is the passage.

    Without the diagonal flag the chain must break; with it, it must not.
    """
    chain = [(0, 0), (1, 1), (2, 2)]
    cells = {c: ('mixed', 'diagonal') for c in chain}
    db = make_db(tmp_path, cells, {}, rooms=[('1', 0, 0)])
    assert 'UNREACHED 0' in dmap.reachable(db, 1, from_room='1')[0]
    assert 'UNREACHED 2' in dmap.reachable(db, 1, from_room='1',
                                           diagonal=False)[0]


def test_corner_step_requires_the_flag_on_both_cells(tmp_path):
    cells = {(0, 0): ('mixed', 'diagonal'), (1, 1): 'mixed'}
    db = make_db(tmp_path, cells, {}, rooms=[('1', 0, 0)])
    assert 'UNREACHED 1' in dmap.reachable(db, 1, from_room='1')[0]


def test_start_from_explicit_cell(tmp_path):
    db = straight_corridor(tmp_path, ['open', 'open'])
    assert 'UNREACHED 0' in dmap.reachable(db, 1, start=(2, 0))[0]


def test_missing_room_anchor_reports_cleanly(tmp_path):
    db = straight_corridor(tmp_path, ['open'])
    out = dmap.reachable(db, 1, from_room='99')
    assert 'cannot start' in out[0]


def test_start_on_solid_reports_cleanly(tmp_path):
    cells = {(0, 0): 'solid', (1, 0): 'open'}
    db = make_db(tmp_path, cells, {}, rooms=[('1', 0, 0)])
    assert 'not walkable' in dmap.reachable(db, 1, from_room='1')[0]


def test_unreached_cells_are_named_with_their_room(tmp_path):
    cells = {(0, 0): 'open', (1, 0): 'open', (2, 0): 'open'}
    edges = {(0, 0, 'V'): 'open', (1, 0, 'V'): 'wall'}
    db = make_db(tmp_path, cells, edges, rooms=[('1', 0, 0), ('7', 2, 0)])
    out = '\n'.join(dmap.reachable(db, 1, from_room='1'))
    assert 'room 7' in out
