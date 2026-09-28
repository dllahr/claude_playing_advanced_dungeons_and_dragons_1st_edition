"""Ray-cast line of sight, and the light-radius reveal built on it.

Built day 139, at the player's word, after a session with at least five
separate geometry mistakes that all traced back to the same cause: eyeballing
grid distance instead of asking the map whether a wall was actually in the
way. The player's own framing is the algorithm -- cast the exact ray from
cell centre to cell centre and see what it crosses -- rather than the
walk-graph BFS first proposed, because a walk-graph gets both directions of
the error a torch would not: it can under-light an open room (routes the
"wrong" way round furniture that isn't there) and it can leak light around a
corner a real torch would not clear (a bent walk-path within radius is not
a straight one).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dmap                                                       # noqa: E402


def solid_field(x0, x1, y0, y1):
    """Every cell in the box marked solid -- the backdrop callers carve
    open cells and edges out of."""
    return {(x, y): ('solid', None, None, None)
            for x in range(x0, x1) for y in range(y0, y1)}


def open_room(x0, x1, y0, y1, pad=1):
    """An open rectangle from (x0,y0) to (x1-1,y1-1), solid border, every
    interior edge marked open."""
    cells = solid_field(x0 - pad, x1 + pad, y0 - pad, y1 + pad)
    edges = {}
    for x in range(x0, x1):
        for y in range(y0, y1):
            cells[(x, y)] = ('open', None, None, None)
    for x in range(x0, x1):
        for y in range(y0, y1):
            edges[(x, y, 'H')] = 'open'
            edges[(x, y, 'V')] = 'open'
    return cells, edges


# ------------------------------------------------------- the open case

def test_sees_straight_across_an_open_room():
    cells, edges = open_room(0, 5, 0, 5)
    ok, why = dmap.line_of_sight(cells, edges, 0, 0, 4, 0)
    assert ok, why


def test_sees_diagonally_across_an_open_room():
    """THE case the naive 'any corner graze is blocked' rule got wrong: a
    45-degree ray across open ground grazes a lattice corner at every step
    (draw y=x), and calling that blocked would make the tool useless for
    the single most common shape of room."""
    cells, edges = open_room(0, 5, 0, 5)
    ok, why = dmap.line_of_sight(cells, edges, 0, 0, 3, 3)
    assert ok, why


def test_same_cell_is_always_lit():
    cells, edges = open_room(0, 3, 0, 3)
    ok, why = dmap.line_of_sight(cells, edges, 1, 1, 1, 1)
    assert ok, why


# ------------------------------------------------------- walls actually stop it

def test_a_wall_edge_blocks_the_ray_and_names_itself():
    cells, edges = open_room(0, 5, 0, 5)
    for y in range(0, 5):
        edges[(1, y, 'V')] = 'wall'
    ok, why = dmap.line_of_sight(cells, edges, 0, 0, 3, 0)
    assert not ok
    assert why == "edge (1, 0, 'V') (wall)"


def test_a_ray_parallel_to_the_wall_is_unaffected():
    cells, edges = open_room(0, 5, 0, 5)
    for y in range(0, 5):
        edges[(1, y, 'V')] = 'wall'
    ok, _why = dmap.line_of_sight(cells, edges, 0, 0, 0, 4)
    assert ok


def test_does_not_see_around_a_corner():
    """An L-shaped 1-wide corridor: (0,0)-(1,0)-(2,0)-(2,1)-(2,2). The
    straight-line diagonal from one end to the other cuts through solid
    rock the corridor bends around -- exactly the case a walk-graph BFS
    would get wrong (short walk-distance, no real sightline)."""
    path = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    cells = solid_field(-1, 5, -1, 5)
    edges = {}
    for c in path:
        cells[c] = ('open', None, None, None)
    for a, b in zip(path, path[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx == 1:
            edges[(a[0], a[1], 'V')] = 'open'
        if dy == 1:
            edges[(a[0], a[1], 'H')] = 'open'
    ok, _why = dmap.line_of_sight(cells, edges, 0, 0, 2, 2)
    assert not ok
    ok, _why = dmap.line_of_sight(cells, edges, 0, 0, 2, 0)
    assert ok, 'straight down the first leg should still be clear'


def test_a_secret_door_blocks_light_even_though_it_is_walkable_once_found():
    """The distinction `find_path` does not need to make: a secret door
    still LOOKS like solid wall until it is found and opened, whatever
    `find_path` may already know about it once the party has."""
    cells, edges = open_room(0, 3, 0, 3)
    edges[(1, 1, 'V')] = 'secret'
    ok, why = dmap.line_of_sight(cells, edges, 1, 1, 2, 1)
    assert not ok
    assert 'secret' in why


def test_an_ordinary_door_blocks_light_when_shut_and_passes_it_open():
    cells, edges = open_room(0, 3, 0, 3)
    edges[(1, 1, 'V')] = 'door'
    ok, _why = dmap.line_of_sight(cells, edges, 1, 1, 2, 1)
    assert not ok, 'a door with no logged state defaults to shut'
    ok, _why = dmap.line_of_sight(cells, edges, 1, 1, 2, 1,
                                   edge_states={(1, 1, 'V'): 'open'})
    assert ok


def test_an_archway_never_blocks_regardless_of_state():
    cells, edges = open_room(0, 3, 0, 3)
    edges[(1, 1, 'V')] = 'archway'
    ok, _why = dmap.line_of_sight(cells, edges, 1, 1, 2, 1)
    assert ok


def test_an_unmapped_edge_defaults_to_blocking():
    """Missing data is the same conservative default as a shut door --
    'unknown' must not read as 'clear'."""
    cells, edges = open_room(0, 3, 0, 3)
    del edges[(1, 1, 'V')]
    ok, why = dmap.line_of_sight(cells, edges, 1, 1, 2, 1)
    assert not ok
    assert 'unknown' in why


def test_a_solid_cell_blocks_even_with_no_wall_edge_recorded():
    """A safety net for inconsistent extraction data (and the 45-degree
    diagonal-wall squares): if the terrain itself says solid, the ray does
    not pass, whatever the boundary edges happen to say."""
    cells, edges = open_room(0, 3, 0, 3)
    cells[(2, 0)] = ('solid', None, None, None)
    ok, why = dmap.line_of_sight(cells, edges, 0, 0, 2, 0)
    assert not ok
    assert 'solid cell' in why


# ------------------------------------------------------- the corner-graze rule itself

def test_a_diagonal_squeeze_between_two_solid_corners_is_blocked():
    """Two open cells touching only at a point, with solid cells on the
    OTHER diagonal -- the classic 'can't cut through a checkerboard
    corner' case, and correctly conservative regardless of the open-room
    exemption above."""
    cells = {(0, 0): ('open', None, None, None),
             (1, 1): ('open', None, None, None),
             (1, 0): ('solid', None, None, None),
             (0, 1): ('solid', None, None, None)}
    ok, why = dmap.line_of_sight(cells, {}, 0, 0, 1, 1)
    assert not ok
    assert 'corner graze' in why


def test_a_fully_open_corner_does_not_block_a_longer_diagonal():
    """The corner-passable exemption checks the SPECIFIC corner grazed, not
    just the two endpoints -- a longer ray grazing several corners in an
    open room must clear all of them."""
    cells, edges = open_room(0, 6, 0, 6)
    ok, why = dmap.line_of_sight(cells, edges, 0, 0, 5, 5)
    assert ok, why


# ------------------------------------------------------- light_reach

def make_db(tmp_path, cells, edges, level=2):
    import sqlite3
    schema = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'schema.sql')
    db = str(tmp_path / 'los.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    con.execute('INSERT INTO levels (level,name) VALUES (?,?)', (level, 'test'))
    for (x, y), v in cells.items():
        con.execute('INSERT INTO cells (level,x,y,terrain,confidence)'
                    ' VALUES (?,?,?,?,10)', (level, x, y, v[0]))
    for (x, y, o), kind in edges.items():
        con.execute('INSERT INTO edges (level,x,y,orient,kind,confidence)'
                    ' VALUES (?,?,?,?,?,10)', (level, x, y, o, kind))
    con.commit(); con.close()
    return db


def test_light_reach_stays_within_radius_and_finds_no_more(tmp_path):
    cells, edges = open_room(-5, 6, -5, 6)
    db = make_db(tmp_path, cells, edges)
    lit = dmap.light_reach(db, 2, 0, 0, radius=3)
    assert (0, 0) in lit and lit[(0, 0)] == 'origin'
    assert (3, 0) in lit           # 30 ft, exactly at the edge
    assert (4, 0) not in lit       # 40 ft, past the lantern
    assert (2, 2) in lit           # inside the disk, off both ring axes
    assert all(cx * cx + cy * cy <= 9 for (cx, cy) in lit)


def test_light_reach_does_not_cross_a_wall(tmp_path):
    cells, edges = open_room(-5, 6, -5, 6)
    for y in range(-5, 6):
        edges[(1, y, 'V')] = 'wall'
    db = make_db(tmp_path, cells, edges)
    lit = dmap.light_reach(db, 2, 0, 0, radius=3)
    assert (2, 0) not in lit, 'on the far side of a wall within radius'
    assert (1, 0) in lit, 'up against this side of the same wall'
