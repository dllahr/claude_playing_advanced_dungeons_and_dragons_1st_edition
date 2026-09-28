"""`dmap.py walk` -- advance until there is something to stop for.

Built day 139 alongside `light`, to replace guessing a destination and
retrying against `party.py move`'s REFUSED errors, which is how tonight's
"advance until something changes" declarations kept eating three attempts
each. The stop conditions are the player's own list: a junction (a real
choice, so it stops and hands back rather than picking), a dead end, an
area-label change, or a feature already visible to the party -- and
deliberately NOT merely stepping onto ground nobody has walked before, since
a long plain corridor should not stop every ten feet.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dmap                                                       # noqa: E402


def make_db(tmp_path, cells, edges, rooms=(), secrets_seen=()):
    """`cells`: {(x,y): terrain} or {(x,y): (terrain, room, feature)}.
    `edges`: {(x,y,orient): kind}. `secrets_seen`: [(x,y,orient)] already
    found by the party."""
    schema = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'schema.sql')
    db = str(tmp_path / 'walk.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    con.execute('INSERT INTO levels (level,name) VALUES (1,?)', ('test',))
    for (x, y), v in cells.items():
        terrain, room, feature = v if isinstance(v, tuple) else (v, None, None)
        con.execute('INSERT INTO cells (level,x,y,terrain,room,feature,'
                    'confidence) VALUES (1,?,?,?,?,?,10)',
                    (x, y, terrain, room, feature))
    seen = set(secrets_seen)
    for (x, y, o), kind in edges.items():
        con.execute('INSERT INTO edges (level,x,y,orient,kind,seen,'
                    'confidence) VALUES (1,?,?,?,?,?,10)',
                    (x, y, o, kind, 1 if (x, y, o) in seen else 0))
    for number, name, ax, ay in rooms:
        con.execute('INSERT INTO rooms (level,number,name,anchor_x,anchor_y)'
                    ' VALUES (1,?,?,?,?)', (number, name, ax, ay))
    con.commit(); con.close()
    return db


def corridor(tmp_path, n, room_at=None):
    """A straight open corridor (0,0)..(n,0). `room_at` optionally maps
    x -> room number for some cells, everything else unlabeled."""
    room_at = room_at or {}
    cells = {(x, 0): ('open', room_at.get(x), None) for x in range(n + 1)}
    edges = {(x, 0, 'V'): 'open' for x in range(n)}
    return cells, edges


# ------------------------------------------------------- the plain case

def test_walks_a_featureless_corridor_to_its_dead_end(tmp_path):
    cells, edges = corridor(tmp_path, 5)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'][-1] == (5, 0)
    assert len(r['path']) == 6, 'every square walked, start included'


def test_does_not_stop_merely_for_new_ground(tmp_path):
    """The explicit non-requirement: a long plain corridor walks straight
    through to its real stop, not one square at a time."""
    cells, edges = corridor(tmp_path, 20)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E', max_squares=100)
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'][-1] == (20, 0)


def test_no_way_that_direction_is_a_dead_end_of_one(tmp_path):
    cells, edges = corridor(tmp_path, 3)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'N')
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'] == [(0, 0)]


# ------------------------------------------------------------- junctions

def test_a_three_way_junction_stops_and_names_both_new_directions(tmp_path):
    # a corridor east, with a branch north partway along
    cells, edges = corridor(tmp_path, 4)
    cells[(2, 1)] = ('open', None, None)
    edges[(2, 0, 'H')] = 'open'
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_JUNCTION
    assert r['path'][-1] == (2, 0)
    dirs = sorted(d for d, _ in r['options'])
    assert dirs == ['E', 'N']


def test_a_junction_does_not_count_the_way_just_walked(tmp_path):
    """Two exits at a cell, one of them being where the party came from,
    is a plain corridor continuing, not a junction."""
    cells, edges = corridor(tmp_path, 4)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END, (
        'every interior cell has a W exit back the way it came; that must '
        'not itself register as a second option')


# ------------------------------------------------------------ area boundaries

def test_stops_on_entering_a_labelled_room(tmp_path):
    cells, edges = corridor(tmp_path, 4, room_at={3: '12', 4: '12'})
    db = make_db(tmp_path, cells, edges, rooms=[('12', 'Library', 3, 0)])
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_AREA
    assert r['path'][-1] == (3, 0)


def test_stops_on_leaving_a_labelled_room_too(tmp_path):
    cells, edges = corridor(tmp_path, 4, room_at={0: '12', 1: '12'})
    db = make_db(tmp_path, cells, edges, rooms=[('12', 'Library', 0, 0)])
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_AREA
    assert r['path'][-1] == (2, 0), 'stops the instant it leaves room 12'


# ------------------------------------------------------------------- features

def test_stops_at_a_cell_feature(tmp_path):
    cells, edges = corridor(tmp_path, 4)
    cells[(3, 0)] = ('open', None, 'stairs')
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_FEATURE
    assert 'stairs' in r['why']
    assert r['path'][-1] == (3, 0)


def test_stops_at_a_found_secret_door_but_not_an_unfound_one(tmp_path):
    cells, edges = corridor(tmp_path, 4)
    edges[(3, 0, 'H')] = 'secret'
    db = make_db(tmp_path, cells, edges)  # not marked seen
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END, (
        'an unfound secret door is invisible to the party, same as it is '
        'to a passing glance -- it must not leak a stop')

    db2 = make_db(tmp_path, cells, edges, secrets_seen=[(3, 0, 'H')])
    r2 = dmap.walk_until(db2, 1, (0, 0), 'E')
    assert r2['stop'] == dmap.STOP_FEATURE
    assert 'secret' in r2['why']
    assert r2['path'][-1] == (3, 0)


# ------------------------------------------------------------------------ cap

def test_the_safety_cap_fires_before_a_pathological_walk_runs_forever(tmp_path):
    cells, edges = corridor(tmp_path, 50)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E', max_squares=10)
    assert r['stop'] == dmap.STOP_CAPPED
    assert len(r['path']) == 11
