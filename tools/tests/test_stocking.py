"""The stocked monster registry: computed position, hp, and the flee window.

Built day 139, the third piece of the geometry work (after `dmap.py light`
and `walk`) -- the one that finally lets a fled monster go somewhere REAL
instead of vanishing and forcing a retcon, which is what happened to the
orcs that ran west at (4,19) on level 1 and were "gone" when the party
followed.
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stocking as stk                                            # noqa: E402

MAPDB = os.path.join(stk.ROOT, 'mapdb')
sys.path.insert(0, MAPDB)
import dmap                                                        # noqa: E402


def make_db(tmp_path, cells, edges, level=2):
    """`cells`: {(x,y): terrain}. `edges`: {(x,y,orient): kind}."""
    schema = os.path.join(MAPDB, 'schema.sql')
    db = str(tmp_path / 'stocking_map.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    con.execute('INSERT INTO levels (level,name) VALUES (?,?)', (level, 'test'))
    for (x, y), terrain in cells.items():
        con.execute('INSERT INTO cells (level,x,y,terrain,confidence)'
                    ' VALUES (?,?,?,?,10)', (level, x, y, terrain))
    for (x, y, o), kind in edges.items():
        con.execute('INSERT INTO edges (level,x,y,orient,kind,confidence)'
                    ' VALUES (?,?,?,?,?,10)', (level, x, y, o, kind))
    con.commit(); con.close()
    return db


def corridor(n):
    """A straight open corridor (0,0)..(n,0)."""
    cells = {(x, 0): 'open' for x in range(n + 1)}
    edges = {(x, 0, 'V'): 'open' for x in range(n)}
    return cells, edges


def scripted_roller(*picks):
    """A roller that returns each of `picks` in turn, ignoring notation --
    for tests that need a KNOWN sequence of choices rather than real dice."""
    it = iter(picks)
    return lambda notation, reason: next(it)


@pytest.fixture
def log(tmp_path):
    p = tmp_path / 'b1_stocking.tsv'
    p.write_text(
        '# test fixture\n'
        'when\tday\tlevel\tarea\tmonster_id\tmonster\tverb\tx\ty\thp\texped\t'
        'round\tduration\tnote\n')
    return str(p)


def stock(log, mid, level=2, area='41', monster='troglodyte',
         x=19, y=4, hp=10, day=1):
    stk.record(mid, 'stock', level=level, area=area, monster=monster,
              x=x, y=y, hp=hp, day=day, path=log)


# ----------------------------------------------------------------- state()

def test_a_stocked_individual_is_present_at_its_placement(log):
    stock(log, 'troglodyte_41a')
    st = stk.state(path=log)
    assert st['troglodyte_41a'] == {
        'level': 2, 'area': '41', 'monster': 'troglodyte',
        'x': 19, 'y': 4, 'hp': 10.0, 'alive': True, 'flee_at': None}


def test_hp_updates_without_moving_it(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'hp', hp=3, day=1, path=log)
    st = stk.state(path=log)['troglodyte_41a']
    assert st['hp'] == 3.0
    assert (st['x'], st['y']) == (19, 4)


def test_die_stops_it_being_alive(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'die', day=1, path=log)
    assert stk.state(path=log)['troglodyte_41a']['alive'] is False


def test_a_plain_move_has_no_expiry(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'move', x=20, y=5, day=1, path=log)
    st = stk.state(path=log)['troglodyte_41a']
    assert (st['x'], st['y']) == (20, 5)
    assert st['flee_at'] is None


# --------------------------------------------------------------- present()/at()

def test_present_excludes_the_dead(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'die', day=1, path=log)
    assert stk.present(2, path=log) == {}


def test_present_filters_by_level(log):
    stock(log, 'troglodyte_41a', level=2)
    stock(log, 'orc_1a', level=1, area='1', monster='orc', x=15, y=8, hp=5)
    assert list(stk.present(1, path=log)) == ['orc_1a']
    assert list(stk.present(2, path=log)) == ['troglodyte_41a']


def test_at_finds_who_is_at_an_exact_cell(log):
    stock(log, 'troglodyte_41a', x=19, y=4)
    stock(log, 'troglodyte_41b', x=19, y=4, hp=4)
    stock(log, 'black_widow_spider_42a', area='42', monster='black_widow_spider',
         x=15, y=8, hp=13)
    assert stk.at(2, 19, 4, path=log) == ['troglodyte_41a', 'troglodyte_41b']
    assert stk.at(2, 15, 8, path=log) == ['black_widow_spider_42a']
    assert stk.at(2, 0, 0, path=log) == []


# ----------------------------------------------------------- the flee window

def test_a_fled_individual_is_findable_at_its_new_cell(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=30,
              day=5, exped=9, rnd=100, path=log)
    now = (5, 9, 110)  # 10 rounds later, same day and expedition
    assert stk.at(2, 17, 3, now=now, path=log) == ['troglodyte_41a']


def test_a_flee_window_expires_after_its_duration_within_the_same_expedition(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=30,
              day=5, exped=9, rnd=100, path=log)
    still_in = (5, 9, 129)
    just_out = (5, 9, 130)
    assert stk.at(2, 17, 3, now=still_in, path=log) == ['troglodyte_41a']
    assert stk.at(2, 17, 3, now=just_out, path=log) == []


def test_a_flee_window_does_not_survive_a_new_day_regardless_of_round_math(log):
    """The player's own reasoning: a short recovery window does not survive
    a change of day in any way that matters, so exact round comparison is
    only meaningful within the SAME expedition."""
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=9999,
              day=5, exped=9, rnd=100, path=log)
    assert stk.at(2, 17, 3, now=(6, 9, 105), path=log) == []


def test_a_flee_window_does_not_survive_a_new_expedition_either(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=9999,
              day=5, exped=9, rnd=100, path=log)
    assert stk.at(2, 17, 3, now=(5, 10, 105), path=log) == []


def test_a_later_move_clears_the_flee_window_it_has_settled(log):
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=30,
              day=5, exped=9, rnd=100, path=log)
    stk.record('troglodyte_41a', 'move', x=17, y=3, day=5, exped=9, rnd=105,
              path=log)
    # even long after the original window would have expired, it is a
    # settled position now, not a fading flee
    assert stk.at(2, 17, 3, now=(5, 9, 9999), path=log) == ['troglodyte_41a']


def test_present_with_no_clock_ignores_flee_expiry(log):
    """A DM-side status listing that does not care about the live clock --
    `status` uses this, `at` from the table does not."""
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'flee', x=17, y=3, duration=1,
              day=1, exped=1, rnd=1, path=log)
    assert 'troglodyte_41a' in stk.present(2, now=None, path=log)


# -------------------------------------------------------------- write guards

def test_stock_requires_its_fields(log):
    with pytest.raises(ValueError):
        stk.record('x', 'stock', path=log)


def test_flee_requires_a_duration(log):
    stock(log, 'troglodyte_41a')
    with pytest.raises(ValueError):
        stk.record('troglodyte_41a', 'flee', x=1, y=1, path=log)


def test_an_unknown_verb_is_refused(log):
    with pytest.raises(ValueError):
        stk.record('x', 'wander', path=log)


# ---------------------------------------------------------------- random_walk

def test_random_walk_stops_at_a_dead_end_within_budget(tmp_path):
    cells, edges = corridor(3)
    db = make_db(tmp_path, cells, edges)
    c, e = dmap.load(db, 2)
    end, _path, feet, reason = stk.random_walk(
        c, e, (0, 0), feet_budget=999, roller=lambda n, r: 1)
    assert reason == 'dead_end'
    assert end == (3, 0)
    assert feet == 30


def test_random_walk_stops_when_the_budget_runs_out(tmp_path):
    cells, edges = corridor(20)
    db = make_db(tmp_path, cells, edges)
    c, e = dmap.load(db, 2)
    end, path, feet, reason = stk.random_walk(
        c, e, (0, 0), feet_budget=50, roller=lambda n, r: 1)
    assert reason == 'budget'
    assert feet == 50
    assert end == (5, 0)


def test_random_walk_does_not_roll_a_single_exit_step(tmp_path):
    """No real choice, no die -- same reasoning `dmap.walk_until` uses."""
    cells, edges = corridor(3)
    db = make_db(tmp_path, cells, edges)
    c, e = dmap.load(db, 2)

    def refuse(notation, reason):
        raise AssertionError('should not have rolled: %s' % reason)

    end, _path, _feet, reason = stk.random_walk(c, e, (0, 0), 999, refuse)
    assert reason == 'dead_end' and end == (3, 0)


def test_random_walk_uses_the_roller_at_a_real_junction(tmp_path):
    cells, edges = corridor(4)
    cells[(2, 1)] = 'open'
    edges[(2, 0, 'H')] = 'open'
    db = make_db(tmp_path, cells, edges)
    c, e = dmap.load(db, 2)
    # two single-exit steps reach (2,0) unrolled; only THAT junction rolls.
    # options there are N->(2,1) and E->(3,0), in DIRS' own order (N, E)
    end, _path, _feet, _reason = stk.random_walk(
        c, e, (0, 0), feet_budget=30, roller=scripted_roller(1))
    assert end == (2, 1), 'picking option 1 of 2 (N) at the junction'


# -------------------------------------------------------------- simulate_flee

def test_simulate_flee_moves_it_and_records_a_flee_event(tmp_path, log):
    cells, edges = corridor(10)
    db = make_db(tmp_path, cells, edges)
    stock(log, 'troglodyte_41a', x=0, y=0)
    out = stk.simulate_flee(
        'troglodyte_41a', feet_per_turn=120, db=db, day=5, exped=9, rnd=100,
        roller=scripted_roller(2, 3), path=log)  # duration d3=2 turns, jitter d4=3
    st = stk.state(path=log)['troglodyte_41a']
    assert st['flee_at'] is not None
    assert 'flees' in out

    # 2 turns * 120 ft/turn = 240 ft = 24 squares along a 10-square corridor
    # -> stops at the dead end, x=10
    assert (st['x'], st['y']) == (10, 0)

    # linger = (5 + 3) * 10 = 80 rounds
    now_in = (5, 9, 100 + 79)
    now_out = (5, 9, 100 + 80)
    assert stk.at(2, 10, 0, now=now_in, path=log) == ['troglodyte_41a']
    assert stk.at(2, 10, 0, now=now_out, path=log) == []


def test_simulate_flee_refuses_an_unknown_or_dead_individual(tmp_path, log):
    with pytest.raises(ValueError):
        stk.simulate_flee('nobody', 90, db=make_db(tmp_path, *corridor(3)),
                          path=log)
    stock(log, 'troglodyte_41a')
    stk.record('troglodyte_41a', 'die', day=1, path=log)
    with pytest.raises(ValueError):
        stk.simulate_flee('troglodyte_41a', 90,
                          db=make_db(tmp_path, *corridor(3)), path=log)


# --------------------------------------------- check_against_encounters() --
#
# Day 162: area 8's seven giant rats and area 32's two giant centipedes
# were both fully fought and paid in encounters.tsv, with this file's own
# die rows never appended -- they sat `present` indefinitely because
# nothing ever cross-checked the two logs against each other. These tests
# guard the fix.

@pytest.fixture
def encounters(tmp_path):
    p = tmp_path / 'encounters.tsv'
    p.write_text(
        '# test fixture\n'
        'exped\tkind\tencounter\txp\tearned_by\tsource\tnotes\n'
        '7\tmonster\tgiant rats (2), area 9 doorway\t21\tall\tx\ty\n'
        '7\tmonster\tgiant rats (5) slain sleeping, area 8\t44\tall\tx\ty\n'
        '31\tmonster\tthree of five kobolds, area 51 near (31,27)\t27\tall\tx'
        '\tthe 2hp and 1hp survivors fled, not credited\n')
    return str(p)


def test_check_flags_a_group_fully_fought_but_never_marked_dead(log, encounters):
    """area 8's exact shape: all seven still `present`, but encounters.tsv
    already has the kill rows."""
    for mid, hp in (('giant_rat_8a', 4), ('giant_rat_8b', 3),
                   ('giant_rat_8c', 3), ('giant_rat_8d', 2),
                   ('giant_rat_8e', 2), ('giant_rat_8f', 1),
                   ('giant_rat_8g', 1)):
        stock(log, mid, level=1, area='8', monster='giant_rat', x=14, y=23,
             hp=hp, day=46)
    flags = stk.check_against_encounters(path=log, encounters_path=encounters)
    assert len(flags) == 1
    lvl, area, monster, ids, exped, text = flags[0]
    assert (lvl, area, monster) == (1, '8', 'giant_rat')
    assert ids == sorted('giant_rat_8%s' % c for c in 'abcdefg')


def test_check_is_silent_once_the_die_rows_exist(log, encounters):
    for mid, hp in (('giant_rat_8a', 4), ('giant_rat_8b', 3)):
        stock(log, mid, level=1, area='8', monster='giant_rat', x=14, y=23,
             hp=hp, day=46)
        stk.record(mid, 'die', day=46, path=log)
    assert stk.check_against_encounters(path=log, encounters_path=encounters) == []


def test_check_does_not_flag_an_individual_already_tracked_as_fled(log, encounters):
    """kobold_51d/e: encounters.tsv's own text says they fled, not died.
    Sitting `present` after a FLEE event is a judged outcome, not an
    oversight, and must not be flagged just because the room and monster
    are mentioned in an unrelated kill row."""
    stock(log, 'kobold_51a', level=2, area='51', monster='kobold',
         x=31, y=27, hp=4, day=140)
    stk.record('kobold_51a', 'die', day=140, path=log)
    stock(log, 'kobold_51d', level=2, area='51', monster='kobold',
         x=31, y=27, hp=2, day=140)
    stk.record('kobold_51d', 'flee', x=32, y=30, duration=30, day=140,
              path=log)
    flags = stk.check_against_encounters(level=2, path=log,
                                         encounters_path=encounters)
    assert flags == []


# --------------------------------------------------------------- the real file

def test_the_live_file_parses_and_every_stocked_individual_has_a_home():
    """Not a spoiler check -- just that the backfilled real B1_stocking.tsv
    is well-formed and every row this module cares about has the fields
    `stock` requires."""
    st = stk.state()
    areas = {(s['level'], s['area']) for s in st.values()}
    assert len(areas) == 19, 'the 19 areas the master stocking table names'
    for mid, s in st.items():
        assert s['level'] in (1, 2), mid
        assert s['x'] is not None and s['y'] is not None, mid
        assert s['hp'] is not None, mid
