"""Money cannot move for nothing, and a glued row cannot hide a whole event.

**This file guards class B: "the money moved and the thing got no row."** Five
purchases in this campaign were recorded only as a sentence inside the notes
column of the `funds` row, and the thing bought got no row anywhere:

    two carts        50 gp each, day 19-20   -- forty days with no row
    two mules        20 gp each              -- ditto
    the small goods  357 gp, day 27          -- 17 days untracked, never rolled
    six 50-ft ropes  2 gp 4 sp, day 67       -- 11 days while the row said 2
    dragon scales    sold day 19 for 110     -- carried as unsold long after

The fix is that `asset` is required and `tools/log.py` refuses without it. That
requirement IS the double entry -- not a reconciliation performed later by
somebody who remembers to perform it.

AND THE OVER-WIDE ROW TEST, which earned its keep before it was even written.
`tsvlog.read_tsv` pads SHORT rows on purpose, so a line that lost a MIDDLE field
is read silently with every later value shifted one column left. Checking field
counts across every campaign log turned up two rows that were **two events glued
together by a missing newline**, and in both cases the second event was
invisible to every tool that had ever read the file:

    clock.tsv        round 959, "Yrtone casts cure light wounds on Dave"
    world_changes    the square (20,8) marked SEEN

Both had been there since 2026-08-28. `world.py replay` went from 404 applied
changes to 405 once the line was split.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import ledger                                                     # noqa: E402
import log as logmod                                              # noqa: E402
import inventory as inv                                           # noqa: E402
from tsvlog import read_tsv                                       # noqa: E402

MONEY = os.path.join(ROOT, 'campaign', 'money.tsv')


def money_rows():
    return read_tsv(MONEY)


# ------------------------------------------------------------- the purse

def test_the_purse_is_computed_not_stored():
    """*** THIS USED TO ASSERT 1072.1 AND BROKE THE FIRST TIME THE PARTY
    BOUGHT ANYTHING. *** A test that pins today's gold is a stored total
    wearing a test's clothes -- the exact thing ledger.py exists to abolish.
    What must hold is the INVARIANT: the purse is the sum of the log.
    """
    # ONLY THE PARTY'S OWN BOOK -- money.tsv gained a `book` column on
    # 2026-09-15 and non-party rows are commitments, not the purse. This
    # recomputation used to sum every row and went red the moment the wool
    # venture's 288 gp was logged against art.7, which is exactly the drift
    # the filter exists to prevent.
    rows = [r for r in money_rows()
            if ledger.book_of(r) in ledger.PARTY_BOOKS]
    anchor = [r for r in rows if r['asset'] == ledger.ANCHOR][-1]
    after = rows[rows.index(anchor) + 1:]
    expect = float(anchor['delta']) + sum(float(r['delta'] or 0)
                                          for r in after)
    assert abs(ledger.total() - expect) < 0.001
    assert ledger.total() > 0, 'the party is not in debt'


def test_there_is_no_second_copy_of_the_purse_left_to_check_against():
    """This test used to assert the computed purse matched inventory.tsv's cell.

    **Both the cell and the check are gone, and that is the improvement.** The
    purse lived in two places, so a cross-check was needed; it now lives in one,
    and a tool that compares a figure against a copy of itself was never a check
    -- it was an early warning that the design was wrong. Same reasoning retired
    light.py's oil disagreement warning in the same commit.
    """
    assert not hasattr(ledger, 'inventory_cell')
    # and no figure is pinned here either, for the same reason
    assert ledger.total() == ledger.total(ledger.rows())


def test_an_anchor_supersedes_everything_above_it():
    log = [dict(day='1', delta='10', asset='coin', reason=''),
           dict(day='2', delta='500', asset=ledger.ANCHOR, reason=''),
           dict(day='3', delta='-5', asset='coin', reason='')]
    assert ledger.total(log) == 495


def test_the_purse_can_be_asked_for_a_past_day():
    """day 65 is the day the party passed a thousand gold for the first time."""
    # PAST days are safe to pin: they cannot change without rewriting the
    # log, which is the one thing CLAUDE.md forbids outright.
    assert ledger.total(day=65) == 1084.5
    assert ledger.total(day=52) == 570.6
    assert ledger.total() >= ledger.total(day=65) - 200


def test_gp_sp_formatting_is_the_campaigns_own():
    assert ledger.gp_sp(1072.1) == '1,072 gp 1 sp'
    assert ledger.gp_sp(25) == '25 gp'
    assert ledger.gp_sp(-2.4) == '-2 gp 4 sp'


# ------------------------------------------------------------- the check

def test_the_live_ledger_passes_its_own_audit():
    assert [m for s, m in ledger.check() if s == 'FAIL'] == []


def test_check_catches_a_row_with_no_asset():
    """THE RULE. This is the shape of all five historical errors."""
    log = [dict(day='1', delta='-50', asset='', reason='two carts')]
    fails = [m for s, m in ledger.check(log) if s == 'FAIL']
    assert any('NO ASSET' in m for m in fails)


def test_check_catches_an_asset_id_that_does_not_exist():
    """A typo'd id is worse than a missing row: it reconciles to nothing and
    looks deliberate."""
    log = [dict(day='1', delta='-50', asset='cartz', reason='')]
    fails = [m for s, m in ledger.check(log) if s == 'FAIL']
    assert any('cartz' in m for m in fails)


def test_check_warns_when_a_good_has_money_but_no_inventory_row():
    """THE LEG THAT WAS MISSING ALL FIVE TIMES.

    A disposed-of thing gets a ZERO row with provenance, not an absent one: a
    zero says "sold", an absence says nothing at all -- which is exactly how the
    dragon scales were carried as unsold for weeks after they had been sold.
    """
    log = [dict(day='1', delta='110', asset='dragon_scales', reason='')]
    warns = [m for s, m in ledger.check(log, ) if s == 'WARN']
    assert not warns, 'dragon_scales has a zero row, so this must be quiet'
    log = [dict(day='1', delta='-50', asset='tapestry', reason='')]
    # tapestry IS held, so also quiet. Use an asset with no inventory row:
    log = [dict(day='1', delta='-50', asset='salvage_misc', reason='')]
    warns = [m for s, m in ledger.check(log) if s == 'WARN']
    assert any('salvage_misc' in m for m in warns)


def test_services_are_exempt_from_needing_an_inventory_row():
    """Wages, lodging, a licence and a loan buy nothing you can put on a cart.

    Without the service ids the double-entry rule would be UNSATISFIABLE on its
    first real use, and a rule that cannot be obeyed is a rule that gets
    quietly broken -- which is how rules die.
    """
    ass = ledger.assets()
    for sid in ('service', 'wages', 'lodging', 'licence', 'loan', 'kit'):
        assert sid in ass, 'service id %r has gone from assets.tsv' % sid
        assert ass[sid]['kind'] == 'service'
    log = [dict(day='1', delta='-25', asset='licence', reason='')]
    assert not [m for s, m in ledger.check(log) if 'inventory row' in m]


def test_every_asset_named_in_money_exists():
    ass = ledger.assets()
    unknown = sorted({r['asset'] for r in money_rows()
                      if r['asset'] not in ass and r['asset'] != ledger.ANCHOR})
    assert not unknown, 'money.tsv names unknown assets: %s' % unknown


def test_the_day_39_anchor_survives():
    """The reconstruction rests on it, and its note carries the finding that
    the prose blob stops reconciling around day 34."""
    anchors = [r for r in money_rows() if r['asset'] == ledger.ANCHOR]
    assert len(anchors) == 1
    assert anchors[0]['day'] == '39'
    assert float(anchors[0]['delta']) == 595.6


# ------------------------------------------------------------- the gate

def test_log_refuses_an_unknown_asset_and_suggests_the_right_one(tmp_path):
    scratch = tmp_path / 'money.tsv'
    scratch.write_text(open(MONEY).read())
    before = scratch.read_text()
    assert logmod.main(['--log-file', str(scratch), 'money', '--delta', '-12',
                        '--asset', 'rope', '--reason', 'x']) == 1
    assert scratch.read_text() == before, 'it wrote anyway'


def test_log_refuses_a_zero_delta(tmp_path):
    scratch = tmp_path / 'money.tsv'
    scratch.write_text(open(MONEY).read())
    assert logmod.main(['--log-file', str(scratch), 'money', '--delta', '0',
                        '--asset', 'coin', '--reason', 'x']) == 1


def test_log_refuses_a_day_that_runs_backwards(tmp_path):
    scratch = tmp_path / 'days.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign', 'days.tsv')).read())
    before = scratch.read_text()
    assert logmod.main(['--log-file', str(scratch), 'day', '--day', '70']) == 1
    assert scratch.read_text() == before


def test_log_refuses_an_unknown_character(tmp_path):
    scratch = tmp_path / 'availability.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign',
                                         'availability.tsv')).read())
    assert logmod.main(['--log-file', str(scratch), 'available',
                        '--who', 'Halm', '--status', 'present']) == 1


def test_log_writes_at_full_width(tmp_path):
    """A row missing a MIDDLE field is read silently with everything shifted.

    It happened twice within an hour of money.tsv being written by hand: two
    rows lost their `interaction` field and their reason was read as an
    interaction id. log.py always writes every column.
    """
    scratch = tmp_path / 'money.tsv'
    scratch.write_text(open(MONEY).read())
    assert logmod.main(['--log-file', str(scratch), 'money', '--delta', '-12',
                        '--asset', 'rations_iron', '--qty', '3',
                        '--reason', 'iron rations']) == 0
    last = [ln for ln in scratch.read_text().splitlines()
            if ln.strip() and not ln.startswith('#')][-1]
    # ten since 2026-09-15: ... reason BOOK. The count is asserted rather than
    # derived on purpose -- a silently WIDENING row is the same defect as a
    # silently narrow one, and this catches both.
    assert len(last.split('\t')) == 10
    header = [ln for ln in open(MONEY, encoding='utf-8')
              if ln.startswith('when\t')][0].rstrip('\n').split('\t')
    assert len(header) == 10 and header[-1] == 'book', header
    assert read_tsv(str(scratch))[-1]['reason'] == 'iron rations'


# ------------------------------------------------- glued rows, everywhere

def test_no_campaign_log_has_an_over_wide_row():
    """An over-wide row is TWO EVENTS GLUED BY A MISSING NEWLINE, and the
    second one is invisible to every tool that reads the file.

    This found two of them on its first run, both dating from 2026-08-28:
    clock.tsv had lost round 959 (Yrtone casting cure light wounds on Dave) and
    world_changes.tsv had lost the square (20,8) being marked SEEN -- so the map
    believed the party had never looked at a square they walked through.
    """
    bad = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'campaign', '*.tsv'))):
        width = None
        for n, ln in enumerate(open(path, encoding='utf-8'), 1):
            ln = ln.rstrip('\n')
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            f = ln.split('\t')
            if width is None:
                width = len(f)
                continue
            if len(f) > width:
                bad.append('%s:%d has %d fields, header has %d'
                           % (os.path.relpath(path, ROOT), n, len(f), width))
    assert not bad, (
        'over-wide row(s) -- almost certainly two events glued by a missing '
        'newline, and the second event is invisible to every tool:\n  %s'
        % '\n  '.join(bad))


def test_the_two_recovered_events_are_still_separate_rows():
    """Named explicitly so a future merge cannot silently re-glue them."""
    clock = read_tsv(os.path.join(ROOT, 'campaign', 'clock.tsv'))
    assert any(r.get('round') == '959' for r in clock), (
        'clock round 959 has gone again -- it was lost inside a glued row '
        'from 2026-08-28 until 2026-09-11')
    world = read_tsv(os.path.join(ROOT, 'campaign', 'world_changes.tsv'))
    assert any(r.get('scope') == 'seen' and r.get('target') == '20,8'
               for r in world), (
        'the (20,8) seen row has gone again -- same glued row')


# --------------------------------------------- two books in one file
# Added 2026-09-15. The wool venture's purse was in NO log at all: the buying
# party went out on day 73 and came home having paid 288 gp, and nothing
# recorded it. The player's ruling settled the shape -- TRACK THE CAP, NOT THE
# BOOK. Wend's ledger is hers and is reported, not inspected; what the party
# logs is its own EXPOSURE against art.7's 500 gp seasonal guarantee.

def _mixed():
    return [
        dict(day='39', delta='595.6', unit='gp', asset=ledger.ANCHOR,
             reason='anchor', book=''),
        dict(day='80', delta='-12', unit='gp', asset='rations_std',
             reason='food', book='party'),
        dict(day='83', delta='-288', unit='gp', asset='wool', qty='36',
             reason='the wool buy', book='art7'),
    ]


def test_an_art7_row_does_NOT_move_the_purse():
    """The whole risk of putting two books in one file, in one assertion."""
    assert ledger.total(_mixed()) == 595.6 - 12


def test_the_art7_counter_totals_only_its_own_book():
    spent, cap, remaining = ledger.art7(_mixed())
    assert spent == 288
    assert cap == 500
    assert remaining == 212


def test_a_blank_book_is_the_PARTY_because_every_old_row_has_one():
    """The column was added on 2026-09-15 to a file with eighteen rows in it.
    Blank must mean party or the purse would have reset to zero."""
    assert '' in ledger.PARTY_BOOKS and 'party' in ledger.PARTY_BOOKS


def test_the_double_entry_check_does_not_demand_inventory_for_another_book():
    """A non-party book buys somebody else's stock for somebody else's barn.
    Demanding an inventory row for the wool would push a false entry into the
    party's own gear -- which is the opposite of what that check is for."""
    problems = [m for lvl, m in ledger.check(_mixed()) if 'wool' in m]
    assert not problems, problems


def test_the_purse_BREAKDOWN_reconciles_with_its_own_headline():
    """It stopped the moment a second book existed. `total()` filtered by book
    and the in/out summary beneath it did not, so the report printed a purse of
    1,036.4 over a sum that came to 748.4 -- the 288 gp of somebody else's wool.
    A breakdown that does not add up to the number above it is worse than none.
    """
    import re
    out = ledger.report()
    purse = float(re.search(r'THE PURSE: ([\d,]+) gp (\d+) sp', out).group(1)
                  .replace(',', '')) + float(
        re.search(r'THE PURSE: ([\d,]+) gp (\d+) sp', out).group(2)) / 10
    anch = float(re.search(r'anchored at ([\d,]+) gp', out)
                 .group(1).replace(',', ''))
    ins = float(re.search(r'in ([\d,]+) gp', out).group(1).replace(',', ''))
    outs = float(re.search(r'out -([\d,]+) gp', out).group(1).replace(',', ''))
    assert abs((anch + ins - outs) - purse) < 1.0, (anch, ins, outs, purse)


# ------------------------------------------- a relocation is not a quantity

def test_inventory_still_refuses_a_zero_qty_with_NO_holder(tmp_path):
    """The original guard stands: a row that says nothing is still refused."""
    scratch = tmp_path / 'inventory_log.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign',
                                         'inventory_log.tsv')).read())
    before = scratch.read_text()
    assert logmod.main(['--log-file', str(scratch), 'inventory',
                        '--asset', 'shovel', '--qty', '0', '--unit', 'each',
                        '--note', 'x']) == 1
    assert scratch.read_text() == before, 'it wrote anyway'


def test_inventory_ALLOWS_a_zero_qty_WHEN_a_holder_is_given(tmp_path):
    """*** A THING CAN CHANGE PLACE WITHOUT CHANGING AMOUNT, AND UNTIL DAY 96
    THERE WAS NO WAY TO SAY SO. ***

    The party stacked 421 lb of salvage under the lean-to at Coll's basecamp and
    walked to Wethersby without it. They still own every ounce and none of it is
    with them. The old schema could only express that as a negative row and a
    positive row per asset -- twenty-two rows to record that nobody gained or
    spent anything, every one of them a chance to fat-finger a quantity that
    `ledger check` would then have to be argued with.

    inventory.py already resolved `holder` last-writer-wins while SUMMING qty,
    so the model always supported this; only the guard did not.
    """
    scratch = tmp_path / 'inventory_log.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign',
                                         'inventory_log.tsv')).read())
    n_before = len(scratch.read_text().splitlines())
    assert logmod.main(['--log-file', str(scratch), 'inventory',
                        '--asset', 'shovel', '--qty', '0', '--unit', 'each',
                        '--condition', 'sound', '--holder', "Coll's basecamp",
                        '--note', 'stacked under the lean-to']) == 0
    lines = scratch.read_text().splitlines()
    assert len(lines) == n_before + 1
    assert "Coll's basecamp" in lines[-1]
    assert '\t0.0\t' in lines[-1] or '\t0\t' in lines[-1], \
        'the quantity must still be recorded as zero -- it moved, it did not '\
        'multiply'


def test_the_salvage_is_AT_THE_BASECAMP_and_not_in_nine_backpacks():
    """Belt and braces on the thing the relocation exists to say.

    Not a pinned quantity -- it asserts the HOLDER, which is the fact day 96
    established and which no later purchase or sale can invalidate. If the party
    fetches it, this test changes with the fiction, which is correct.
    """
    st = inv.state()
    for asset in ('chain_heavy', 'shovel', 'chisel', 'vise_iron'):
        holders = {cell[2] for cell in st[asset].values()}
        assert any('basecamp' in h.lower() for h in holders), (
            '%s should be under the lean-to at Coll\'s basecamp; holder reads '
            '%r' % (asset, holders))
