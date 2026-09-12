"""Light-source fuel: the burn model, and the ways it could quietly lie.

These test INVARIANTS, not the live campaign's fuel levels. `test_party.py`
learned that the hard way — a test pinned to a live value breaks the moment the
game moves, and the fix is always to edit the test, which trains everyone to
ignore it. So the live log is checked for being *well formed and replayable*,
never for a particular number of turns.

The four things that would make this tool worse than nothing, each with a test:

  * fuel burning while the lamp is out (the party sleeps and wakes up poorer)
  * fuel NOT burning while the lamp is hooded (the free-light exploit)
  * a torch that can be refilled (unlimited light through the back door)
  * a burn time hardcoded in Python, drifting away from PHB p. 102
"""
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import light                                                     # noqa: E402
import rules                                                     # noqa: E402

HEADER = ('when\texped\tround\tsource\tkind\twhat\twho\tfuel\tcertainty'
          '\tnote\n')
COLS = HEADER.strip('\n').split('\t')


def row(**kw):
    r = dict.fromkeys(COLS, '')
    r.update(kw)
    return r


def rows_to_file(tmp_path, rows, name='light.tsv'):
    p = tmp_path / name
    with open(str(p), 'w') as fh:
        fh.write(HEADER)
        for r in rows:
            fh.write('\t'.join(str(r.get(c, '')) for c in COLS) + '\n')
    return str(p)


@pytest.fixture
def cat():
    return light.catalogue()


# ------------------------------------------------------- the rules cache

def test_burn_times_come_from_the_markdown_and_not_from_python(tmp_path):
    """Point the parser at a FAKE table and the tool must follow it.

    This is the real test that nothing is hardcoded. If "24 turns" or "6 turns"
    lived in light.py, these numbers would not move.
    """
    d = tmp_path / 'rules'
    d.mkdir()
    open(str(d / 'exploration.md'), 'w').write(
        "## Light sources (invented for this test)\n"
        "\n"
        "| Source | Radius | Burning time |\n"
        "|---|---|---|\n"
        "| Torch | 40' | 99 turns |\n"
        "| Lantern (hooded) | 30' | 7 turns per pint of oil |\n"
        "\n"
        "*source: nowhere at all; this table is a fake.*\n")
    fake = light.catalogue(rules.load(directory=str(d)))
    assert fake['Torch']['burn_rounds'] == 990
    assert fake['Lantern (hooded)']['burn_rounds'] == 70

    # and the whole pipeline follows it, not just the parser
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='t', kind='new', what='Torch'),
        row(exped=4, round=0, source='t', kind='lit'),
    ])
    s = light.state(light.load(log), at_round=10, cat=fake)['t']
    assert s['fuel'] == 980


def test_the_live_table_still_says_what_the_PHB_says(cat):
    """PHB p. 102: torch 6 turns, hooded lantern 24 turns per pint.

    Not a duplicate of the table — a tripwire on it. If somebody edits
    rules/exploration.md and these move, that is a rules change and should be a
    deliberate one.
    """
    assert cat['Torch']['burn_turns'] == 6
    assert cat['Lantern (hooded)']['burn_turns'] == 24
    assert cat['Magic long sword']['infinite']


def test_refillability_is_read_off_the_books_own_wording(cat):
    """"24 turns PER PINT of oil" names a fuel; "6 turns (1 hour)" does not."""
    assert cat['Lantern (hooded)']['refillable']
    assert cat['Bullseye lanthorn']['refillable']
    assert not cat['Torch']['refillable']


def test_the_light_table_is_cited():
    assert rules.find(light.TABLE)['source'], \
        'the light-source table has no *source:* line'


def test_resolve_is_forgiving_of_shorthand_but_not_of_ambiguity(cat):
    assert light.resolve('lantern', cat) == 'Lantern (hooded)'
    assert light.resolve('torch', cat) == 'Torch'
    with pytest.raises(KeyError):
        light.resolve('magic', cat)          # three magic weapons
    with pytest.raises(KeyError):
        light.resolve('glowstick', cat)


# ------------------------------------------------------- the burn model

def test_fuel_burns_only_while_lit(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=50, source='lamp', kind='out'),
    ])
    rows = light.load(log)
    # 50 rounds lit, then 430 rounds dark: only the first 50 are charged.
    s = light.state(rows, at_round=480, cat=cat)['lamp']
    assert s['fuel'] == 240 - 50
    assert not s['burning']


def test_sleeping_with_the_lamp_out_costs_nothing(tmp_path, cat):
    """`clock.py rest --hours 8` advances 480 rounds. That must be free."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
    ])
    rows = light.load(log)
    before = light.state(rows, at_round=0, cat=cat)['lamp']['fuel']
    after = light.state(rows, at_round=480, cat=cat)['lamp']['fuel']
    assert before == after == 240


def test_a_hooded_lantern_KEEPS_BURNING(tmp_path, cat):
    """rules/exploration.md: "Hooding does not stop the burn."

    The conservative reading, and the one the file states outright. If hooding
    were free the party would hood the lamp through every rest and light would
    stop being a resource at all.
    """
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=10, source='lamp', kind='hooded'),
    ])
    s = light.state(light.load(log), at_round=100, cat=cat)['lamp']
    assert s['burning'], 'a hooded lantern is shuttered, not extinguished'
    assert s['hooded']
    assert s['fuel'] == 240 - 100, 'hooding must not pause the fuel clock'


def test_hooding_an_unlit_lantern_does_not_light_it(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='hooded'),
    ])
    s = light.state(light.load(log), at_round=100, cat=cat)['lamp']
    assert not s['burning']
    assert s['fuel'] == 240


def test_a_torch_gutters_at_its_burn_time_and_the_round_is_reported(
        tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=100, source='t', kind='new', what='Torch'),
        row(exped=4, round=100, source='t', kind='lit'),
    ])
    s = light.state(light.load(log), at_round=500, cat=cat)['t']
    assert s['guttered_at'] == 160          # 100 + 6 turns
    assert not s['burning']
    assert s['fuel'] == 0


def test_a_magic_sword_never_burns_down(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='sword', kind='new',
            what='Magic long sword'),
        row(exped=4, round=0, source='sword', kind='lit'),
    ])
    s = light.state(light.load(log), at_round=99999, cat=cat)['sword']
    assert s['burning'] and s['infinite']
    assert s['guttered_at'] is None


# ------------------------------------------------------- refills

def test_a_refill_resets_the_fuel(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=200, source='lamp', kind='refill', who='Frython'),
    ])
    s = light.state(light.load(log), at_round=200, cat=cat)['lamp']
    assert s['fuel'] == 240
    assert s['fills'] == 1
    assert s['who'] == 'Frython'
    # and it starts burning down again immediately, because it is still lit
    s2 = light.state(light.load(log), at_round=210, cat=cat)['lamp']
    assert s2['fuel'] == 230


def test_a_refill_after_it_guttered_puts_it_back_in_service(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=300, source='lamp', kind='refill'),
        row(exped=4, round=300, source='lamp', kind='lit'),
    ])
    s = light.state(light.load(log), at_round=300, cat=cat)['lamp']
    assert s['guttered_at'] is None and s['burning'] and s['fuel'] == 240


def test_A_TORCH_CANNOT_BE_REFILLED(tmp_path, cat):
    """The rules table prices a torch at "6 turns (1 hour)" and names no fuel."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='t', kind='new', what='Torch'),
        row(exped=4, round=0, source='t', kind='lit'),
        row(exped=4, round=10, source='t', kind='refill'),
    ])
    with pytest.raises(ValueError) as e:
        light.state(light.load(log), at_round=20, cat=cat)
    assert 'consumed item' in str(e.value)


def test_the_cli_refuses_a_torch_refill_BEFORE_writing_the_row(tmp_path, cat):
    """An append-only log can only be corrected by another row, so a bad row
    has to be refused at the table, not discovered by a later report."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='t', kind='new', what='Torch'),
    ])
    before = open(log).read()
    code = light.main(['--log-file', log, '--at-round', '10',
                       'refill', 't', '--round', '10'])
    assert code == 1
    assert open(log).read() == before, 'the refused row was written anyway'


# ------------------------------------------------------- anchors & unknowns

def test_an_anchor_supersedes_everything_above_it(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=500, source='lamp', kind='anchor', fuel='9'),
    ])
    s = light.state(light.load(log), at_round=500, cat=cat)['lamp']
    assert s['fuel'] == 90 and s['known']


def test_unknown_fuel_stays_unknown_and_is_never_quietly_full_or_empty(
        tmp_path, cat):
    """"Prefer 'I don't know' to a reconstructed number" — CHECKLIST.md §9."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='anchor',
            what='Lantern (hooded)', fuel='?', certainty='uncertain'),
        row(exped=4, round=0, source='lamp', kind='lit'),
    ])
    s = light.state(light.load(log), at_round=300, cat=cat)['lamp']
    assert s['fuel'] is None
    assert not s['known'] and not s['certain']
    assert s['guttered_at'] is None, 'an unknown level must not gutter on cue'
    assert s['burned'] == 300, 'but the burn still accrues, so it can be ruled'
    word, fuel, gutter, warn = light.describe(s, 300)
    assert fuel == '?' and gutter == 'UNKNOWN' and 'UNKNOWN' in warn


def test_an_anchor_with_no_figure_is_unknown_rather_than_full(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='anchor',
            what='Lantern (hooded)'),
    ])
    s = light.state(light.load(log), at_round=0, cat=cat)['lamp']
    assert s['fuel'] is None and not s['known']


def test_a_known_anchor_retires_the_uncertainty(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='anchor',
            what='Lantern (hooded)', fuel='?', certainty='uncertain'),
        row(exped=4, round=50, source='lamp', kind='anchor', fuel='12',
            certainty='known'),
    ])
    s = light.state(light.load(log), at_round=50, cat=cat)['lamp']
    assert s['certain'] and s['fuel'] == 120


# ------------------------------------------------------- replay order

def test_replay_is_ORDER_INDEPENDENT_in_the_file(tmp_path, cat):
    """Ordered by exped/round, exactly like world_changes.tsv.

    The log is append-only, so a refill remembered a session later lands at the
    bottom of the file. Under file order that would put the oil in before it
    was burnt. world.py hit precisely this with a backfilled door-spiking.
    """
    events = [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=4, round=0, source='lamp', kind='lit'),
        row(exped=4, round=100, source='lamp', kind='hooded'),
        row(exped=4, round=200, source='lamp', kind='refill'),
        row(exped=4, round=260, source='lamp', kind='out'),
    ]
    canonical = light.state(light.load(rows_to_file(tmp_path, events)),
                            at_round=400, cat=cat)['lamp']
    rng = random.Random(1729)
    for i in range(8):
        shuffled = events[:]
        rng.shuffle(shuffled)
        got = light.state(
            light.load(rows_to_file(tmp_path, shuffled, 'shuffled.tsv')),
            at_round=400, cat=cat)['lamp']
        assert got['fuel'] == canonical['fuel']
        assert got['burning'] == canonical['burning']
        assert got['guttered_at'] == canonical['guttered_at']
    assert canonical['fuel'] == 240 - 60      # only rounds 200-260 since refill


def test_a_backfilled_earlier_expedition_does_not_supersede_a_later_one(
        tmp_path, cat):
    """The anchor is expedition 4; the row written afterwards is expedition 3
    and must sort BEFORE it, not overwrite it."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=10, source='lamp', kind='anchor',
            what='Lantern (hooded)', fuel='5'),
        row(exped=3, round=900, source='lamp', kind='anchor', fuel='20'),
    ])
    s = light.state(light.load(log), at_round=10, cat=cat)['lamp']
    assert s['fuel'] == 50


# ------------------------------------------------------- the party total

def test_reserves_are_priced_off_the_rules_table(tmp_path, cat):
    """*** THE FLASK COUNT NOW COMES FROM THE OIL POOL, NOT AN INVENTORY CELL.

    It used to come from campaign/inventory.tsv, so the same fact lived in two
    files and they drifted apart TWICE -- caught both times only by a
    disagreement warning. light.tsv knows which flasks have been broached, so
    `sealed` is derived there and there is nothing left to disagree with. ***
    """
    inv_state = {
        'torch': {'': [2, 'each', 'spread', '']},
        'candle': {'': [6, 'each', 'spread', '']},
        'dagger': {'': [1, 'each', 'Frython', '']},
    }
    pool = dict(known=True, sealed=3, broached=0.0, opened=0, drawn=0.0,
                short=0.0, untracked=0.0)
    priced, unpriced = light.reserves(cat, inv_state=inv_state, pool=pool)
    by_item = {p['item']: p for p in priced}
    assert by_item['oil flask']['rounds'] == 3 * 240
    assert by_item['torch']['rounds'] == 2 * 60
    # A candle has no burn time in the cache. It is reported as unpriced rather
    # than counted as zero, because "we did not look it up" and "it gives no
    # light" are very different answers.
    assert [i for i, _ in unpriced] == ['candle']


def test_the_total_is_a_FLOOR_when_any_source_is_unknown(tmp_path, cat, monkeypatch):
    monkeypatch.setattr(light, 'reserves', lambda *a, **k: (
        [dict(item='oil flask', qty=2, what='Lantern (hooded)',
              each_rounds=240, rounds=2 * 240, text='')], []))
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='known', kind='new', what='Torch'),
        row(exped=4, round=0, source='dunno', kind='anchor',
            what='Lantern (hooded)', fuel='?', certainty='uncertain'),
    ])
    src = light.state(light.load(log), at_round=0, cat=cat)
    t = light.total(src, 0, cat)
    assert t['in_sources'] == 60             # the torch only
    assert t['reserves'] == 2 * 240
    assert t['unknown'] == ['dunno']
    assert 'FLOOR' in light.remaining_report(src, 0, cat)


def test_a_lost_source_stops_counting(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='t', kind='new', what='Torch'),
        row(exped=4, round=0, source='t', kind='lit'),
        row(exped=4, round=10, source='t', kind='lost',
            note='dropped down the shaft'),
    ])
    src = light.state(light.load(log), at_round=200, cat=cat)
    assert src['t']['gone'] and not src['t']['burning']
    assert light.total(src, 200, cat)['in_sources'] == 0


def test_a_low_source_warns_before_it_gutters(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='t', kind='new', what='Torch'),
        row(exped=4, round=0, source='t', kind='lit'),
    ])
    src = light.state(light.load(log), at_round=20, cat=cat)
    text = light.report(src, 20)
    assert 'LOW' in text and 'round 60' in text
    # ... and not while there is plenty left
    assert 'LOW' not in light.report(
        light.state(light.load(rows_to_file(tmp_path, [
            row(exped=4, round=0, source='l', kind='new',
                what='Lantern (hooded)'),
            row(exped=4, round=0, source='l', kind='lit')])),
            at_round=20, cat=cat), 20)


# ------------------------------------------------------- the live log

def test_the_live_log_replays_without_raising():
    """Invariant, not a value. What the party's fuel IS changes every session;
    that the log is well formed must not."""
    src = light.state(light.load(), at_round=10 ** 6)
    assert src, 'campaign/light.tsv has no light sources in it'


def test_every_row_of_the_live_log_is_well_formed():
    cat = light.catalogue()
    rows = light.load()
    whats = light.what_of(rows, cat)          # raises on a contradictory `what`
    for r in rows:
        sid = (r.get('source') or '').strip()
        assert sid, 'a row with no source: %r' % r
        kind = (r.get('kind') or '').strip().lower()
        assert kind in light.KINDS, \
            'unknown kind %r on %s' % (r.get('kind'), sid)
        # `oil` and `draw` are about the party's SUPPLY, not about a light
        # source: they have no burn time and price off nothing, so they are the
        # one case with no `what`. Everything else must name its rules-table
        # line or there is no way to know how fast it burns.
        if kind not in ('oil', 'draw'):
            assert sid in whats, \
                'no row for %s names which rules-table line prices it' % sid
        fuel = (r.get('fuel') or '').strip()
        if fuel and fuel != '?':
            float(fuel)


def test_one_source_cannot_be_two_different_things(tmp_path, cat):
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='x', kind='new', what='Torch'),
        row(exped=4, round=5, source='x', kind='lit',
            what='Lantern (hooded)'),
    ])
    with pytest.raises(ValueError) as e:
        light.state(light.load(log), at_round=10, cat=cat)
    assert 'one light source, one line' in str(e.value)


def test_the_row_that_names_what_need_not_sort_first(tmp_path, cat):
    """The order-independence bug this actually had: a bare `out` backfilled
    for an earlier expedition sorted ahead of the `new` row and the replay
    raised, because it looked up `what` on whichever row came first."""
    log = rows_to_file(tmp_path, [
        row(exped=4, round=0, source='lamp', kind='new',
            what='Lantern (hooded)'),
        row(exped=3, round=900, source='lamp', kind='out'),
    ])
    s = light.state(light.load(log), at_round=0, cat=cat)['lamp']
    assert s['what'] == 'Lantern (hooded)'


def test_the_live_seed_is_flagged_uncertain_rather_than_invented():
    """The party's real fuel level was never written down. The seed says so.

    If somebody later replaces the `?` with a made-up number and forgets to
    rule it properly, this fails — which is the point. Retire it by logging a
    `known` anchor with a real DM ruling, and then delete this test.
    """
    src = light.state(light.load(), at_round=10 ** 6)
    lanterns = [s for s in src.values() if s['what'] == 'Lantern (hooded)']
    assert lanterns, 'the party carries two hooded lanterns'
    if any(s['fuel'] is None for s in lanterns):
        assert all(not s['certain'] for s in lanterns if s['fuel'] is None), \
            'a lantern with unknown fuel must be flagged uncertain'


def test_num_accepts_numbers_as_well_as_strings():
    """Regression: `light.py anchor ... --fuel 23` crashed the first time a real
    figure was logged.

    Log fields arrive as STRINGS when replayed out of the TSV but as ints or
    floats when they come straight off argparse. `_num` assumed a string and
    raised `'int' object has no attribute 'strip'` — so the tool worked for the
    whole seeded history and broke the moment anyone tried to retire the
    uncertainty it was built to flag.
    """
    assert light._num(23) == 23.0
    assert light._num(23.5) == 23.5
    assert light._num('23') == 23.0
    assert light._num('  23  ') == 23.0
    assert light._num('') is None
    assert light._num(None) is None
    assert light._num('?') is None
    assert light._num('?', 'x') == 'x'
    assert light._num(0) == 0.0, 'zero fuel is a real value, not a missing one'


def test_a_new_expedition_restarts_the_fuel_clock(tmp_path):
    """THE SECOND TIME THIS TOOL PRODUCED INFINITE LIGHT.

    `clock.py` restarts its round counter at 0 for every expedition. `state()`
    ended with `_burn_to(s, max(at_round, s['at']))` -- a "never rewind" guard
    written to stop a row logged ahead of the clock from un-burning oil. But
    across an expedition boundary the new round is not a rewind, it is a
    different clock: max(164, 2263) is 2263, the lamp had already burned to it,
    and expedition 5 ran 164 rounds charging NOTHING.

    Caught in play 2026-08-31 when a lantern filled to 24 turns at round 0 still
    read 24.0 turns at round 164.
    """
    p = rows_to_file(tmp_path, [
        row(exped=4, round=0,    source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=4, round=0,    source='lamp', kind='lit'),
        row(exped=4, round=2000, source='lamp', kind='out'),
        row(exped=5, round=0,    source='lamp', kind='refill', fuel=24),
        row(exped=5, round=0,    source='lamp', kind='lit'),
    ])
    s = light.state(path=p, at_round=100)['lamp']
    assert s['burning']
    # 100 rounds of expedition 5 is ten turns, so 14 remain -- NOT 24.
    assert light.turns(s['fuel']) == pytest.approx(14.0), (
        'expedition 5 burned no oil: the fuel clock is still on expedition 4')


def test_the_never_rewind_guard_still_holds_inside_one_expedition(tmp_path):
    """The boundary fix must not reopen the hole it was guarding.

    Within a single expedition a row logged ahead of the clock is still a row
    about the future and must not un-burn oil already spent.
    """
    p = rows_to_file(tmp_path, [
        row(exped=5, round=0,   source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=5, round=0,   source='lamp', kind='lit'),
        row(exped=5, round=150, source='lamp', kind='hooded'),
    ])
    s = light.state(path=p, at_round=50)['lamp']
    assert light.turns(s['fuel']) == pytest.approx(9.0), (
        'a row at round 150 should have burned the lamp to 150, not back to 50')


# --------------------------------------------------------------- the oil pool
#
# Before this existed, `refill` set the reservoir to full and charged a whole
# flask no matter what was left in the lamp. The turns still in the lamp were
# thrown away twice over: once out of the reservoir, and once off the flask
# count. The player caught it at expedition 6 round 197 with 4.4 turns in the
# lamp -- "that means there are 4.4 turns remaining in the flask, not 0."

def test_topping_up_a_part_full_lamp_leaves_the_rest_in_the_flask(tmp_path):
    """The bug this whole mechanism exists to kill."""
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil',  kind='oil', fuel=10),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=6, round=0, source='lamp', kind='lit'),
        # 196 rounds = 19.6 turns burned, so 4.4 turns are left in the lamp.
        row(exped=6, round=196, source='lamp', kind='refill'),
    ])
    pool = light.oil_state(path=p, at_round=196)
    assert light.turns(pool['broached']) == pytest.approx(4.4), (
        'the lamp could only take 19.6 turns, so 4.4 stay IN THE FLASK')
    assert pool['opened'] == 1
    assert pool['sealed'] == 9, 'exactly one flask should have been broached'
    s = light.state(path=p, at_round=196)['lamp']
    assert light.turns(s['fuel']) == pytest.approx(24.0)


def test_a_part_used_flask_is_finished_before_another_is_opened(tmp_path):
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil',  kind='oil', fuel=2),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=6, round=0, source='lamp', kind='lit'),
        row(exped=6, round=100, source='lamp', kind='refill'),   # draws 10 turns
        row(exped=6, round=340, source='lamp', kind='refill'),   # draws 24 turns
    ])
    pool = light.oil_state(path=p, at_round=340)
    # `new --fuel 24` ASSERTS a level and draws nothing, so both flasks are
    # still sealed. The first refill broaches one and takes 10 of its 24. The
    # second needs 24: it must FINISH that flask's remaining 14 before opening
    # the second, and then takes 10 more from it, leaving 14.
    assert pool['opened'] == 2
    assert pool['sealed'] == 0
    assert light.turns(pool['broached']) == pytest.approx(14.0)
    assert pool['short'] == 0, 'two flasks were enough; nothing should be short'


def test_an_explicit_figure_on_a_refill_still_costs_oil(tmp_path):
    """The back door: `refill --fuel 24` must not be free light."""
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil',  kind='oil', fuel=5),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=0),
        row(exped=6, round=0, source='lamp', kind='refill', fuel=24),
    ])
    pool = light.oil_state(path=p, at_round=0)
    assert pool['opened'] == 1 and pool['sealed'] == 4
    assert light.turns(pool['drawn']) == pytest.approx(24.0)


def test_an_untracked_pool_is_reported_untracked_not_empty(tmp_path):
    """Same rule as an `anchor` with no fuel: unknown, never generous."""
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=6, round=0, source='lamp', kind='lit'),
        row(exped=6, round=100, source='lamp', kind='refill'),
    ])
    pool = light.oil_state(path=p, at_round=100)
    assert not pool['known']
    assert pool['sealed'] == 0 and pool['opened'] == 0
    assert pool['untracked'] > 0, 'the draw happened but is not debited'
    assert 'NOT TRACKED' in light.oil_report(pool)


def test_running_out_of_oil_fills_the_lamp_SHORT_not_full(tmp_path):
    """A lamp cannot be filled with oil the party does not have."""
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil',  kind='oil', fuel=1),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=24),
        row(exped=6, round=0, source='lamp', kind='lit'),
        row(exped=6, round=240, source='lamp', kind='refill'),   # spends flask 1
        # A REFILL DOES NOT RELIGHT A GUTTERED LAMP -- without this `lit` the
        # lamp burns nothing from 240 to 480 and the second refill draws zero.
        row(exped=6, round=240, source='lamp', kind='lit'),
        row(exped=6, round=480, source='lamp', kind='refill'),   # nothing left
    ])
    pool = light.oil_state(path=p, at_round=480)
    s = light.state(path=p, at_round=480)['lamp']
    assert light.turns(pool['short']) == pytest.approx(24.0)
    assert light.turns(s['fuel']) == pytest.approx(0.0), (
        'the lamp must not refill itself out of an empty pack')
    assert 'RAN DRY' in light.oil_report(pool)


def test_the_flask_count_comes_from_the_pool_and_nowhere_else(tmp_path,
                                                              monkeypatch):
    """There is no second count left to disagree with, and that is the fix.

    This test used to assert that the pool BEAT a stale inventory cell and that
    `oil_report` said so. Both halves are gone: the cell is gone, the
    disagreement warning is gone, and `reserves()` reads the flask count
    straight out of the pool. A warning that two sources disagree was never a
    check -- it was an early sign that the design was wrong.
    """
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil',  kind='oil', fuel=3),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=24),
    ])
    monkeypatch.setattr('inventory.state', lambda *a, **k: {})
    src, pool = light._replay(path=p, at_round=0)
    t = light.total(src, 0, pool=pool)
    # 3 sealed flasks, straight from the pool.
    assert light.turns(t['reserves']) == pytest.approx(72.0)
    assert 'DISAGREES' not in light.oil_report(pool)


def test_oil_used_on_something_other_than_a_lamp_comes_out_of_the_pool(tmp_path):
    """Oiling hinges costs oil, and it costs the BROACHED flask first.

    The expedition-4 precedent for oiling a door is "roughly 2 turns' worth off
    a broached flask, NOT a whole flask" -- before `draw` existed there was
    nowhere to put that number except prose.
    """
    p = rows_to_file(tmp_path, [
        row(exped=6, round=0, source='oil', kind='oil', fuel=3),
        row(exped=6, round=0, source='lamp', kind='new', what='lantern', fuel=0),
        row(exped=6, round=0, source='lamp', kind='refill', fuel=20),   # broaches one
        row(exped=6, round=10, source='oil', kind='draw', fuel=2),      # hinges
    ])
    pool = light.oil_state(path=p, at_round=10)
    assert pool['opened'] == 1
    assert pool['sealed'] == 2
    # 24 in the broached flask, 20 into the lamp, 2 onto the hinges -> 2 left.
    assert light.turns(pool['broached']) == pytest.approx(2.0)
