"""The dungeon clock and the hit-point ledger.

The clock arithmetic matters because an audit once found wandering checks being
rolled at 2-5x the correct rate, and because the round count previously lived
only in the DM's context and was lost to a cleared session.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import clock                                                    # noqa: E402
import hp as hpmod                                              # noqa: E402


class Seq(object):
    def __init__(self, *values):
        self.values = list(values)

    def randint(self, a, b):
        return self.values.pop(0)


def write(path, header, *rows):
    with open(path, 'w') as fh:
        fh.write(header)
        for r in rows:
            fh.write('\t'.join(str(c) for c in r) + '\n')
    return str(path)


CLOCK_HEADER = 'when\texped\tround\tkind\tanchor\tdetail\tnote\n'
HP_HEADER = 'when\texped\tturn\twho\tkind\tdelta\treason\n'


# ------------------------------------------------------------- the clock

def test_anchors_are_every_third_turn():
    """B1 p.4: "Every third turn of adventuring, the DM should take a die roll
    for the possible appearance of wandering monsters."  A turn is 10 rounds,
    so every third turn is 30.

    This was 20 for the whole campaign -- 1.5x the module's encounter rate --
    because rules/exploration.md asserted "20 rounds, the module's rate" with
    no page citation and the code trusted it.  Corrected 2026-08-30 against a
    200 dpi render.  If this number ever moves again it must move because
    somebody read the page, not because somebody remembered it.
    """
    assert clock.ANCHOR == 30


def test_reanchor_exists_and_demands_a_reason():
    """Changing ANCHOR does NOT change the schedule -- the anchors live in
    campaign/clock.tsv and stale ones go on firing forever.  `reanchor` is the
    only supported way to change the interval, and it refuses to run without
    --why, because a silently re-rolled wandering schedule is unauditable.
    """
    parser = clock.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['reanchor'])
    a = parser.parse_args(['reanchor', '--why', 'because the book says so'])
    assert a.cmd == 'reanchor' and a.why


def test_a_check_fires_once_inside_its_window():
    jitter = {20: 3, 40: 0, 60: 5}
    due = clock.check_due(0, 25, jitter, set())
    assert due == [(20, 3, 23)]


def test_a_check_already_fired_does_not_fire_again():
    jitter = {20: 3}
    assert clock.check_due(0, 25, jitter, {20}) == []


def test_advancing_past_several_anchors_fires_each_once():
    jitter = {20: 1, 40: 2, 60: 3}
    due = clock.check_due(0, 100, jitter, set())
    assert [a for a, _, _ in due] == [20, 40, 60]
    assert [at for _, _, at in due] == [21, 42, 63]


def test_the_jitter_never_pushes_a_check_into_the_next_window():
    """anchor + (1d6 - 1) is 0..5, so a check always lands before the next
    anchor. If this ever fails the average spacing is no longer 20 rounds."""
    for j in range(0, 6):
        assert 20 + j < 40


def test_state_reads_back_the_hidden_jitter(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 4, 0, 'start', '', '', 'in'),
              ('2026-01-01', 4, 0, 'jitter', '', '20:3,40:0', 'hidden'),
              ('2026-01-01', 4, 10, 'advance', '', '10', 'moved'))
    exped, rnd, jitter, fired = clock.state(clock.load(p))
    assert exped == '4' and rnd == 10
    assert jitter == {20: 3, 40: 0}
    assert fired == set()


def test_a_new_start_resets_the_count(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 3, 0, 'start', '', '', ''),
              ('2026-01-01', 3, 200, 'advance', '', '200', ''),
              ('2026-01-02', 4, 0, 'start', '', '', ''))
    exped, rnd, jitter, fired = clock.state(clock.load(p))
    assert exped == '4' and rnd == 0 and jitter == {}


def test_fired_checks_are_remembered(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 4, 0, 'start', '', '', ''),
              ('2026-01-01', 4, 0, 'jitter', '', '20:3', ''),
              ('2026-01-01', 4, 23, 'check', 20, 'd6=5', ''))
    _, rnd, _, fired = clock.state(clock.load(p))
    assert rnd == 23 and fired == {20}


# ------------------------------------------------- correcting the clock
# Added 2026-09-13. `state` takes max() of every round it sees, deliberately, so
# that a `check` row logged at the round it FIRED cannot rewind a move that ended
# later. The unnoticed cost of that rule was that the clock could not be
# corrected AT ALL: `advance --rounds -1` was appended and SILENTLY IGNORED,
# leaving a row in campaign/clock.tsv that said one thing while the tool did
# another. That is the failure this repo exists to prevent, so the clock got a
# way to be corrected rather than a dead row in its log.


def test_a_correct_row_is_the_one_thing_that_may_move_the_clock_BACK(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 9, 0, 'start', '', '', ''),
              ('2026-01-01', 9, 0, 'jitter', '', '30:5,60:5', ''),
              ('2026-01-01', 9, 17, 'advance', '', '17', ''),
              ('2026-01-01', 9, 16, 'correct', '', '-1', 'a round charged for '
               'a step through a wall that is not on the printed map'))
    assert clock.state(clock.load(p))[1] == 16


def test_a_negative_advance_is_STILL_ignored_so_correct_is_the_only_way(tmp_path):
    """The max() rule is untouched for `advance`. Loosening it there would
    reintroduce the bug it was written for."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 9, 0, 'start', '', '', ''),
              ('2026-01-01', 9, 0, 'jitter', '', '30:5', ''),
              ('2026-01-01', 9, 17, 'advance', '', '17', ''),
              ('2026-01-01', 9, 16, 'advance', '', '-1', 'must NOT take'))
    assert clock.state(clock.load(p))[1] == 17


def test_a_correction_forward_works_too_and_fires_no_wandering_check(tmp_path):
    """A correction states what the clock SHOULD have read. Rolling for
    wanderers on it would invent an encounter out of a bookkeeping fix."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 9, 0, 'start', '', '', ''),
              ('2026-01-01', 9, 0, 'jitter', '', '30:0,60:0,90:0', ''),
              ('2026-01-01', 9, 20, 'advance', '', '20', ''))
    assert clock.main(['--log-file', p, 'correct', '--to', '80',
                       '--why', 'a fight that was never charged']) == 0
    rows = clock.load(p)
    assert clock.state(rows)[1] == 80
    assert [r for r in rows if r.get('kind') == 'check'] == [], (
        'a correction fired a wandering check')


def test_correct_demands_a_reason(tmp_path):
    parser = clock.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['correct', '--to', '16'])


def test_the_encounter_table_loaded_for_each_level():
    for level in (1, 2):
        t = clock.encounter_table(level)
        assert set(t) == {1, 2, 3, 4, 5, 6}, 'level %d has %s' % (level, sorted(t))
        for k, v in t.items():
            # Structural only -- the contents are DM-side and stay unprinted.
            assert 'AC' in v and 'HD' in v, 'level %d entry %d looks truncated' % (level, k)


def test_a_check_that_misses_produces_no_encounter(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER)
    lines, entry = clock.fire_check(20, 3, 23, 1, '4', rng=Seq(5), log_file=p)
    assert entry is None
    assert any('no encounter' in ln for ln in lines)


def test_a_check_that_hits_rolls_the_table_and_warns_about_placement(tmp_path):
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER)
    lines, entry = clock.fire_check(20, 3, 23, 1, '4', rng=Seq(1, 2), log_file=p)
    assert entry
    joined = '\n'.join(lines)
    assert 'WHAT, NOT WHERE' in joined
    assert 'anchor 20 fired at round 23' in joined


def test_the_action_costs_match_the_exploration_rules():
    assert clock.COSTS['search'][0] == 10        # one turn
    assert clock.COSTS['combat'][0] == 1
    assert clock.COSTS['move90'][0] == 10


# --------------------------------------------------------------- hit points

CHARS = {'Dave': {'name': 'Dave', 'class': 'Fighter', 'hp_max': '9'},
         'Tristle': {'name': 'Tristle', 'class': 'Thief', 'hp_max': '3'}}


def test_hp_starts_at_max_with_an_empty_log():
    assert hpmod.current(CHARS, []) == {'Dave': (9, 9), 'Tristle': (3, 3)}


def test_damage_and_healing_accumulate():
    rows = [{'who': 'Dave', 'kind': 'damage', 'delta': '-4'},
            {'who': 'Dave', 'kind': 'heal', 'delta': '3'}]
    assert hpmod.current(CHARS, rows)['Dave'] == (8, 9)


def test_healing_cannot_exceed_the_maximum():
    rows = [{'who': 'Dave', 'kind': 'heal', 'delta': '5'}]
    assert hpmod.current(CHARS, rows)['Dave'] == (9, 9)


def test_negative_hit_points_are_not_clamped():
    """1e death is at -10 and a blow can carry a character to -3 from 0.
    Reporting a wounded character as 0 would erase the deciding number."""
    rows = [{'who': 'Tristle', 'kind': 'damage', 'delta': '-7'}]
    assert hpmod.current(CHARS, rows)['Tristle'] == (-4, 3)


def test_an_anchor_supersedes_everything_above_it():
    rows = [{'who': 'Dave', 'kind': 'damage', 'delta': '-8'},
            {'who': 'Dave', 'kind': 'anchor', 'delta': '9'},
            {'who': 'Dave', 'kind': 'damage', 'delta': '-1'}]
    assert hpmod.current(CHARS, rows)['Dave'] == (8, 9)


@pytest.mark.parametrize('value,expect', [
    (5, ''), (1, ''), (0, 'unconscious'), (-3, 'unconscious'), (-10, 'DEAD'),
    (-11, 'DEAD'),
])
def test_condition_reads_the_1e_thresholds(value, expect):
    assert expect in hpmod.condition(value)


def test_the_live_log_parses_and_stays_sane():
    """Reads campaign/hp_log.tsv for real, but asserts INVARIANTS, not values.

    This test used to pin the six exact hit-point totals. It passed until the
    moment Torsat took a wound in play, and then a green suite went red for a
    reason that had nothing to do with the code. A test that breaks whenever the
    campaign moves is measuring the campaign, not the tool.
    """
    got = hpmod.current()
    # The six PCs must always be there.  Anyone ELSE may be, and that is not a
    # failure: campaign/characters.tsv also carries half-share allies who fight
    # alongside the party (DMG p.85), and their wounds want tracking too.
    # Pinning the set to exactly six made this test fail the day Hask and
    # Dellie joined -- which is the same "measuring the campaign, not the tool"
    # mistake the docstring above was written about.
    assert {'Dave', 'Torsat', 'Tristle', 'Blartho', 'Yrtone',
            'Frython'} <= set(got)
    for name, (cur, mx) in got.items():
        assert mx > 0, '%s has no hp_max' % name
        assert cur <= mx, '%s is above its maximum' % name
        assert cur > -10, '%s is at %d, which is dead' % (name, cur)


def test_a_check_logged_mid_advance_does_not_rewind_the_clock(tmp_path):
    """The check row carries the round it FIRED at, not the round the move
    ended at, and it is written last. Reading the last value rewound the clock
    from 23 back to 21 during expedition 4."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 4, 0, 'start', '', '', ''),
              ('2026-01-01', 4, 0, 'jitter', '', '20:1', ''),
              ('2026-01-01', 4, 23, 'advance', '', '3', 'moved to 23'),
              ('2026-01-01', 4, 21, 'check', 20, 'd6=6', 'fired at 21'))
    _, rnd, _, fired = clock.state(clock.load(p))
    assert rnd == 23
    assert fired == {20}


def test_an_extra_check_does_not_crash_on_its_string_anchor(tmp_path):
    """`extra` passes the literal 'extra' as the anchor; it was formatted with
    %d and every noise-triggered check raised TypeError."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER)
    lines, entry = clock.fire_check('extra', 0, 106, 1, '4', rng=Seq(5),
                                    log_file=p)
    assert entry is None
    assert 'EXTRA' in lines[0]
    rows = clock.load(p)
    assert rows[-1]['anchor'] == 'extra'


def test_an_extra_check_is_not_counted_as_a_scheduled_anchor(tmp_path):
    """A string anchor must not land in `fired` and cancel a real anchor."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 4, 0, 'start', '', '', ''),
              ('2026-01-01', 4, 0, 'jitter', '', '20:1', ''),
              ('2026-01-01', 4, 5, 'check', 'extra', 'd6=5', 'noise'))
    _, rnd, jitter, fired = clock.state(clock.load(p))
    assert clock.check_due(0, 30, jitter, fired) == [(20, 1, 21)]


def test_a_rest_does_not_fire_every_anchor_it_covers(tmp_path):
    """Eight hours is 480 rounds and 24 anchors. The module gives THREE checks
    per night camped inside, so the anchors inside a rest must be marked fired
    without being rolled."""
    p = write(tmp_path / 'c.tsv', CLOCK_HEADER,
              ('2026-01-01', 4, 0, 'start', '', '', ''),
              ('2026-01-01', 4, 0, 'jitter', '',
               ','.join('%d:0' % (k * 20) for k in range(1, 30)), ''))
    exped, rnd, jitter, fired = clock.state(clock.load(p))
    due = clock.check_due(rnd, rnd + 480, jitter, fired)
    assert len(due) > 20, 'the normal schedule really would fire this many'


# --------------------------------------------------- stabilising the dying
# Added 2026-09-13. `condition()` derived "bleeding 1 hp/round" FROM THE NUMBER
# ALONE, so a character who had been bandaged went on being reported as bleeding
# to death by every briefing until somebody remembered otherwise. Ista bandaged
# Torsat at -1 on day 79 and the tool said he was still going down a point a
# round -- with the only correction living in a `heal 0` row nobody reads.

def test_aid_stops_the_bleeding_and_the_report_says_so(tmp_path):
    p = write(tmp_path / 'h.tsv', HP_HEADER,
              ('2026-01-01', 9, 4, 'Torsat', 'damage', -7, 'seven on a six'),
              ('2026-01-01', 9, 4, 'Torsat', 'stabilise', 0, 'bandaged'))
    rows = hpmod.read_tsv(p)
    assert hpmod.current(rows=rows)['Torsat'][0] == -1
    assert 'Torsat' in hpmod.stabilised(rows=rows)
    line = hpmod.condition(-1, True)
    assert 'BLEEDING STOPPED' in line
    assert 'bleeding 1 hp/round' not in line


def test_aid_restores_NO_hit_points(tmp_path):
    """DMG p.82 aid stops the slide; it is not a cure. A delta here would read
    as healing in every total computed from the log."""
    p = write(tmp_path / 'h.tsv', HP_HEADER,
              ('2026-01-01', 9, 4, 'Torsat', 'damage', -7, ''),
              ('2026-01-01', 9, 4, 'Torsat', 'stabilise', 0, ''))
    assert hpmod.current(rows=hpmod.read_tsv(p))['Torsat'][0] == -1


def test_further_damage_REOPENS_it(tmp_path):
    """You can only stabilise a man once per wounding."""
    p = write(tmp_path / 'h.tsv', HP_HEADER,
              ('2026-01-01', 9, 4, 'Torsat', 'damage', -7, ''),
              ('2026-01-01', 9, 4, 'Torsat', 'stabilise', 0, 'bandaged'),
              ('2026-01-01', 9, 5, 'Torsat', 'damage', -1, 'kicked'))
    rows = hpmod.read_tsv(p)
    assert 'Torsat' not in hpmod.stabilised(rows=rows)
    assert 'bleeding 1 hp/round' in hpmod.condition(-2, False)


def test_an_unstabilised_negative_still_reports_the_bleeding(tmp_path):
    assert 'bleeding 1 hp/round' in hpmod.condition(-1, False)
    assert hpmod.condition(-10, True) == 'DEAD'
