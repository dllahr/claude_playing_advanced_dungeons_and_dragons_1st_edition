"""The stocked monster registry: computed position, hp, and the flee window.

Built day 139, the third piece of the geometry work (after `dmap.py light`
and `walk`) -- the one that finally lets a fled monster go somewhere REAL
instead of vanishing and forcing a retcon, which is what happened to the
orcs that ran west at (4,19) on level 1 and were "gone" when the party
followed.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stocking as stk                                            # noqa: E402


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
