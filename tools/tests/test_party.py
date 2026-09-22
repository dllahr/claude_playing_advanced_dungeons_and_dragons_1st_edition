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


# ------------------------------------------------- secret doors on a route

@pytest.fixture
def world_with_secret(tmp_path):
    """(0,0)-(0,2) open corridor; a SECRET door on (0,1)'s east side."""
    db = str(tmp_path / 'b1.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'test')")
    for x in (0, 1):
        for y in range(3):
            con.execute("INSERT INTO cells (level,x,y,terrain) "
                        "VALUES (1,?,?,'open')", (x, y))
    for x in (0, 1):
        for y in range(3):
            con.execute("INSERT INTO edges (level,x,y,orient,kind) "
                        "VALUES (1,?,?,'H','open')", (x, y))
            con.execute("INSERT INTO edges (level,x,y,orient,kind) "
                        "VALUES (1,?,?,'V','open')", (x, y))
    con.execute("UPDATE edges SET kind='secret', notes='a big printed S' "
                "WHERE level=1 AND x=0 AND y=1 AND orient='V'")
    con.commit(); con.close()
    log = str(tmp_path / 'party.tsv')
    open(log, 'w').write(HEADER)
    return db, log


def test_secrets_near_finds_a_door_on_the_stepped_cells_own_side(world_with_secret):
    """(0,1,V) is stored under (0,1) itself -- the simple case."""
    near = party.secrets_near([(0, 0), (0, 1), (0, 2)], db=world_with_secret[0])
    assert [(x, y, o) for x, y, o, _n in near] == [(0, 1, 'V')]


def test_secrets_near_finds_a_door_on_the_neighbours_side(world_with_secret):
    """mapdb stores an edge ONCE -- (0,1,V) is also (1,1)'s WEST side, and a
    route that only steps through (1,1), never (0,1), must still find it.
    This is the case day 118's audit actually missed: the party crossed
    (4,41), and the door was stored as (3,41,V) under its OTHER neighbour.
    """
    near = party.secrets_near([(1, 0), (1, 1), (1, 2)], db=world_with_secret[0])
    assert [(x, y, o) for x, y, o, _n in near] == [(0, 1, 'V')]


def test_secrets_near_is_silent_when_nothing_is_near(world_with_secret):
    near = party.secrets_near([(0, 0)], db=world_with_secret[0])
    assert near == []


def test_move_prints_the_owed_check(world_with_secret, capsys):
    db, log = world_with_secret
    party.place('0,0', 'test', path=log)
    party.main(['--db', db, '--log-file', log, 'move', '--to', '1,1'])
    out = capsys.readouterr().out
    assert 'KNOWN SECRET DOOR' in out
    assert '0,1,V' in out
