"""Replay of campaign/world_changes.tsv onto a map database.

The bugs these guard against both happened while the tool was being written:

  * filtering the log on `level` alone replayed all of Quasqueton's changes
    onto the DMG sample dungeon -- both are level 1 -- and reported 73
    successful updates while doing it
  * a schema CHECK constraint on the state column would have rejected a state
    nobody anticipated, mid-session
"""
import os
import sqlite3
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import world                                                    # noqa: E402

SCHEMA = os.path.join(ROOT, 'mapdb', 'schema.sql')

HEADER = ('when\tmap\texped\tturn\tlevel\tscope\ttarget\tchange\titem\tqty'
          '\twho\tnote\n')


def write_log(tmp_path, *rows):
    p = tmp_path / 'log.tsv'
    body = HEADER
    for r in rows:
        body += '\t'.join(str(c) for c in r) + '\n'
    p.write_text(body)
    return str(p)


def make_db(tmp_path, name='b1.sqlite'):
    """A two-cell, one-edge, one-room level 1 with the real schema."""
    p = str(tmp_path / name)
    con = sqlite3.connect(p)
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'test')")
    for x in (0, 1):
        con.execute("INSERT INTO cells (level,x,y,terrain,room)"
                    " VALUES (1,?,0,'open','7')", (x,))
    con.execute("INSERT INTO edges (level,x,y,orient,kind)"
                " VALUES (1,0,0,'V','secret')")
    con.execute("INSERT INTO rooms (level,number) VALUES (1,'7')")
    con.commit()
    con.close()
    return p


def read(db, sql, args=()):
    con = sqlite3.connect(db)
    out = con.execute(sql, args).fetchall()
    con.close()
    return out


# ------------------------------------------------------------- targets

@pytest.mark.parametrize('scope,target,want', [
    ('edge', '17,13,V', (17, 13, 'V')),
    ('edge', '17,13,h', (17, 13, 'H')),
    ('cell', '3,4', (3, 4)),
    ('area', '25', '25'),
    ('seen', 'area:9', ('area', '9')),
    ('seen', '3,4', ('cell', (3, 4))),
])
def test_parse_target(scope, target, want):
    assert world.parse_target(scope, target) == want


@pytest.mark.parametrize('scope,target', [
    ('edge', '17,13'), ('edge', '17,13,Q'), ('cell', '1,2,3'),
])
def test_bad_targets_raise(scope, target):
    with pytest.raises(ValueError):
        world.parse_target(scope, target)


# -------------------------------------------------------- supersession

def test_a_later_row_supersedes_an_earlier_one(tmp_path):
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 3, 10, 1, 'edge', '0,0,V', 'spiked_open',
         'iron spike', 2, 'Tristle', 'wedged it'),
        ('2026-01-02', 'b1', 4, 20, 1, 'edge', '0,0,V', 'spiked_shut',
         '', '', 'Dave', 'shut it again'))
    rows = world.load(log, 'b1', 1)
    st = world.current(rows)
    assert st['edge'][(0, 0, 'V')][0] == 'spiked_shut'


def test_a_backfilled_older_row_does_not_supersede_a_newer_one(tmp_path):
    """The log is append-only, so history written later lands at the bottom.

    Exactly this happened: the expedition-1 spiking of the pair-2 door was
    logged after the expedition-3 row that reopened it, and under file order
    the older action won and left the door shut.
    """
    log = write_log(
        tmp_path,
        ('2026-08-25', 'b1', 3, '', 1, 'edge', '0,0,V', 'spiked_open',
         'iron spike', 2, 'Tristle', 'reopened from behind'),
        ('2026-08-16', 'b1', 1, '', 1, 'edge', '0,0,V', 'spiked_shut',
         '', '', 'party', 'backfilled a week later'))
    st = world.current(world.load(log, 'b1', 1))
    assert st['edge'][(0, 0, 'V')][0] == 'spiked_open'


def test_turn_orders_rows_inside_one_expedition(tmp_path):
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 4, 90, 1, 'edge', '0,0,V', 'spiked_shut',
         '', '', 'D', 'later'),
        ('2026-01-01', 'b1', 4, 10, 1, 'edge', '0,0,V', 'spiked_open',
         '', '', 'T', 'earlier'))
    st = world.current(world.load(log, 'b1', 1))
    assert st['edge'][(0, 0, 'V')][0] == 'spiked_shut'


def test_a_blank_turn_sorts_last_within_its_expedition(tmp_path):
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 4, '', 1, 'edge', '0,0,V', 'broken',
         '', '', 'D', 'no turn recorded, so end of the trip'),
        ('2026-01-01', 'b1', 4, 90, 1, 'edge', '0,0,V', 'spiked_open',
         '', '', 'T', 'turn 90'))
    st = world.current(world.load(log, 'b1', 1))
    assert st['edge'][(0, 0, 'V')][0] == 'broken'


def test_revert_clears_the_state(tmp_path):
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 3, 10, 1, 'edge', '0,0,V', 'spiked_open',
         'iron spike', 2, 'Tristle', ''),
        ('2026-01-02', 'b1', 4, 20, 1, 'edge', '0,0,V', 'revert',
         'iron spike', -2, 'Tristle', 'spikes pulled'))
    st = world.current(world.load(log, 'b1', 1))
    assert (0, 0, 'V') not in st['edge']
    net, _ = world.deployed(world.load(log, 'b1'))
    assert net == {}                    # the spikes came back


def test_deployed_nets_and_keeps_nonzero(tmp_path):
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 3, 10, 1, 'edge', '0,0,V', 'spiked_open',
         'iron spike', 2, 'Tristle', ''),
        ('2026-01-02', 'b1', 3, 12, 1, 'cell', '1,0', 'blocked',
         'iron spike', 1, 'Dave', ''))
    net, where = world.deployed(world.load(log, 'b1'))
    assert net == {'iron spike': 3}
    assert len(where['iron spike']) == 2


# ------------------------------------------------------------- replay

def test_replay_writes_state_to_the_right_row(tmp_path):
    db = make_db(tmp_path)
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V', 'spiked_open',
         'iron spike', 2, 'Tristle', 'two at the bottom'))
    n, problems = world.replay(db, 1, rows=world.load(log, 'b1', 1), quiet=True)
    assert not problems and n == 1
    got = read(db, "SELECT kind,state,state_note FROM edges WHERE orient='V'")
    # The KIND is what the map says and must not be overwritten by play state.
    assert got[0][0] == 'secret'
    assert got[0][1] == 'spiked_open'
    assert 'Tristle' in got[0][2] and 'exp.3' in got[0][2]


def test_replay_is_idempotent(tmp_path):
    db = make_db(tmp_path)
    log = write_log(
        tmp_path,
        ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V', 'spiked_open',
         '', '', 'Tristle', ''))
    rows = world.load(log, 'b1', 1)
    a = world.replay(db, 1, rows=rows, quiet=True)
    before = read(db, 'SELECT x,y,orient,state,state_note FROM edges')
    b = world.replay(db, 1, rows=rows, quiet=True)
    assert a == b
    assert before == read(db, 'SELECT x,y,orient,state,state_note FROM edges')


def test_replay_clears_a_state_whose_row_was_removed(tmp_path):
    db = make_db(tmp_path)
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V',
                     'spiked_open', '', '', 'T', ''))
    world.replay(db, 1, rows=world.load(log, 'b1', 1), quiet=True)
    empty = write_log(tmp_path / 'x') if False else write_log(tmp_path)
    world.replay(db, 1, rows=world.load(empty, 'b1', 1), quiet=True)
    assert read(db, 'SELECT state FROM edges')[0][0] is None


def test_seen_by_area_marks_every_square_of_the_area(tmp_path):
    db = make_db(tmp_path)
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 0, 1, 'seen', 'area:7', 'yes',
                     '', '', '', ''))
    world.replay(db, 1, rows=world.load(log, 'b1', 1), quiet=True)
    assert read(db, 'SELECT COUNT(*) FROM cells WHERE seen=1')[0][0] == 2


def test_the_map_column_keeps_one_dungeon_out_of_another(tmp_path):
    """Both maps have a level 1. Filtering on level alone applied B1's changes
    to the DMG sample dungeon and called it success."""
    dmg = make_db(tmp_path, 'dmg.sqlite')
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V',
                     'spiked_open', '', '', 'Tristle', ''))
    rows = world.load(log, world.map_of(dmg), 1)
    assert rows == []
    n, _ = world.replay(dmg, 1, rows=rows, quiet=True)
    assert n == 0
    assert read(dmg, 'SELECT state FROM edges')[0][0] is None


def test_map_of_reads_the_database_name():
    assert world.map_of('mapdb/output/b1/b1.sqlite') == 'b1'
    assert world.map_of('mapdb/output/dmg/dmg.sqlite') == 'dmg'
    assert world.map_of('/tmp/dmg_blind.sqlite') == 'dmg'


# ---------------------------------------------------------- validation

def test_an_unknown_state_warns_but_still_applies(tmp_path):
    """No CHECK constraint: a verb nobody anticipated must not stop the game."""
    db = make_db(tmp_path)
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V',
                     'glued_shut_by_a_grey_ooze', '', '', 'DM', ''))
    rows = world.load(log, 'b1', 1)
    warnings = world.validate(rows)
    assert any('not one of the documented values' in w for w in warnings)
    n, problems = world.replay(db, 1, rows=rows, quiet=True)
    assert n == 1 and not problems
    assert read(db, 'SELECT state FROM edges')[0][0] == 'glued_shut_by_a_grey_ooze'


def test_a_state_on_a_boundary_the_map_lacks_is_reported(tmp_path):
    db = make_db(tmp_path)
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 58, 1, 'edge', '99,99,V',
                     'spiked_open', '', '', 'T', ''))
    rows = world.load(log, 'b1', 1)
    n, problems = world.replay(db, 1, rows=rows, quiet=True)
    assert n == 0 and problems
    assert 'matched nothing' in problems[0]


def test_check_flags_a_wall_that_the_party_walked_through(tmp_path):
    """Reachability cannot see this; only the play record can."""
    db = make_db(tmp_path)
    con = sqlite3.connect(db)
    con.execute("UPDATE edges SET kind='wall'")
    con.commit()
    con.close()
    log = write_log(tmp_path,
                    ('2026-01-01', 'b1', 3, 58, 1, 'edge', '0,0,V',
                     'spiked_open', '', '', 'T', ''))
    out = world.check(db, 1, world.load(log, 'b1', 1))
    assert any('calls it a plain wall' in ln for ln in out)


# ------------------------------- once-per-object, because prose failed twice
# `rules/thief.md` has carried a box headed "THE LIMIT IS PER OBJECT, NOT A
# PER-LEVEL BUDGET" since 2026-09-06, written after the DM got it wrong. On day
# 81 he got it wrong AGAIN with the box in the file, telling the player that
# Tristle -- having just picked (20,31,H) -- had "no picks left" for the bay
# door and was spent "until 2nd level". PHB p.28: once per LOCK.
#
# So the attempts became a QUERY. A warning that has failed twice must stop
# being a sentence.

def _picks_rows():
    return [
        dict(when='2026-08-29', scope='edge', target='23,6,V', who='Tristle',
             change='unlocked',
             note='lock sprung on the first and only attempt, d100=24 vs 35'),
        dict(when='2026-09-06', scope='edge', target='29,31,H', who='Tristle',
             change='trap', note='STUMPED on the pit trap, d100=71 vs 25'),
        dict(when='2026-09-04', scope='edge', target='9,21,H', who='Tristle',
             change='locked',
             note='still LOCKED and Tristle has never attempted the lock'),
        dict(when='2026-09-09', scope='edge', target='25,10,H', who='party',
             change='unspiked', note='cloaks picked up on the way out'),
        dict(when='2026-09-04', scope='edge', target='24,29,H', who='Ista',
             change='oiled', note='hinges oiled with 2 turns of oil'),
    ]


def test_picks_reports_one_line_per_character_and_OBJECT():
    out = world.report_picks(_picks_rows())
    assert 'edge 23,6,V' in out and 'SPRUNG' in out
    assert 'edge 29,31,H' in out and 'STUMPED' in out
    assert 'edge 9,21,H' in out and 'UNTRIED' in out


def test_picks_does_NOT_match_cloaks_picked_up_or_oiled_hinges():
    """The first version matched a bare "pick" and reported both. A lookup
    nobody trusts is worse than no lookup: it sends you back to memory, which
    is the thing that got this wrong twice."""
    out = world.report_picks(_picks_rows())
    assert '25,10,H' not in out, 'matched "cloaks picked up"'
    assert '24,29,H' not in out, 'matched an oiling row'


def test_picks_says_out_loud_that_the_limit_is_per_object():
    out = world.report_picks(_picks_rows())
    assert 'PER OBJECT' in out
    assert 'NOT LISTED AT ALL is a fresh' in out, (
        'the report must state what an ABSENT pair means, or the reader infers '
        'a per-level budget from a short list -- which is the original error')
