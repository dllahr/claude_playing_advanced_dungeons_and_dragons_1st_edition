"""Party position, and the move that should have been impossible.

Round 1111 of expedition 4: the party was walked from (19,5) to (19,6) through
a wall. These tests exist so that specific mistake cannot recur.
"""
import os
import sqlite3
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(ROOT, 'mapdb'))

import party                                                    # noqa: E402

SCHEMA = os.path.join(ROOT, 'mapdb', 'schema.sql')
HEADER = ('when\tmap\tlevel\tx\ty\texped\tturn\tsquares\tfeet\trate\twhy'
          '\troute\n')


@pytest.fixture
def world(tmp_path):
    """A corridor: (0,0)-(0,2), a WALL above (0,2), and (0,3)-(0,4) beyond it,
    reachable only the long way round through x=1."""
    db = str(tmp_path / 'b1.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'test')")
    for x in (0, 1):
        for y in range(6):
            con.execute("INSERT INTO cells (level,x,y,terrain) "
                        "VALUES (1,?,?,'open')", (x, y))
    for x in (0, 1):
        for y in range(6):
            k = 'wall' if (x == 0 and y == 2) else 'open'
            con.execute("INSERT INTO edges (level,x,y,orient,kind) "
                        "VALUES (1,?,?,'H',?)", (x, y, k))
            con.execute("INSERT INTO edges (level,x,y,orient,kind) "
                        "VALUES (1,?,?,'V','open')", (x, y))
    con.commit(); con.close()
    log = str(tmp_path / 'party.tsv')
    open(log, 'w').write(HEADER)
    return db, log


def test_place_then_where(world):
    db, log = world
    party.place('0,0', 'test', path=log)
    x, y, level, _ = party.where(log)
    assert (x, y, level) == (0, 0, 1)


def test_move_records_the_route(world):
    db, log = world
    party.place('0,0', 'test', path=log)
    steps, crossed, feet = party.move('0,2', db=db, path=log)
    assert steps[0] == (0, 0) and steps[-1] == (0, 2)
    assert feet == 20


def test_a_one_square_move_through_a_wall_is_REFUSED(world):
    """THE round-1111 test. (0,2) to (0,3) looks like one square north. The
    wall between them means the only route is the long way round, and that
    must raise rather than quietly walking the party 8 squares."""
    db, log = world
    party.place('0,2', 'test', path=log)
    with pytest.raises(ValueError) as e:
        party.move('0,3', db=db, path=log)
    assert 'DETOUR' in str(e.value)
    assert 'NOT adjacent' in str(e.value)


def test_a_deliberate_detour_can_be_confirmed(world):
    """The long way round is a legal thing to want — it just has to be said."""
    db, log = world
    party.place('0,2', 'test', path=log)
    steps, _, _ = party.move('0,3', db=db, path=log, max_squares=20)
    assert steps[-1] == (0, 3)
    assert len(steps) - 1 > 2


def test_max_squares_refuses_a_longer_route_than_expected(world):
    db, log = world
    party.place('0,0', 'test', path=log)
    with pytest.raises(ValueError) as e:
        party.move('0,4', db=db, path=log, max_squares=4)
    assert 'not where you think' in str(e.value)


def test_an_unreachable_destination_raises(world):
    db, log = world
    party.place('0,0', 'test', path=log)
    with pytest.raises(ValueError) as e:
        party.move('99,99', db=db, path=log)
    assert 'not a square' in str(e.value)


def test_moving_before_being_placed_raises(tmp_path, world):
    db, _ = world
    log = str(tmp_path / 'empty.tsv')
    open(log, 'w').write(HEADER)
    with pytest.raises(ValueError) as e:
        party.move('0,1', db=db, path=log)
    assert 'never been placed' in str(e.value)


def test_the_live_log_has_the_party_somewhere_real():
    cur = party.where()
    assert cur is not None, 'the party has no recorded position'
    x, y, level, _ = cur
    import dmap
    cells, _ = dmap.load(party.DB, level)
    assert (x, y) in cells, 'the party is standing off the map'
