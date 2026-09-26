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

    # *** THE EXAMPLE ASSET IS DERIVED, NOT NAMED. *** This test used to hardcode
    # `salvage_misc` as "an asset with no inventory row", and on day 100 it got
    # one -- the 117 gp lot Hask sold needed a leg at the id the money named.
    # A test that hardcodes today's gap breaks the moment the gap is filled,
    # which is the third time this campaign has pinned game state in a test.
    logged = {r['asset'] for r in read_tsv(
        os.path.join(ROOT, 'campaign', 'inventory_log.tsv'))}
    ass = ledger.assets()
    candidates = [a for a, v in ass.items()
                  if v['kind'] not in ('service', 'money', 'debt')
                  and a not in logged and a not in inv.FOREIGN]
    assert candidates, ('every goods asset now has an inventory row, which is '
                        'the ideal -- but then this check has nothing to prove '
                        'and should be retired rather than fudged')
    orphan = sorted(candidates)[0]
    log = [dict(day='1', delta='-50', asset=orphan, reason='')]
    warns = [m for s, m in ledger.check(log) if s == 'WARN']
    assert any(orphan in m for m in warns), (orphan, warns)


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

    THE SILVER IS PART OF THE FIGURE. This test used to read only the gp of
    the anchor, the in and the out -- throwing away three silver components --
    and then allow 1.0 gp of slack to cover the damage. Three dropped tenths can
    reach 2.7 gp, so it was guaranteed to fail on a true ledger sooner or later,
    and on day 99 it did: anchor 595 gp 6 sp, in 733 gp 8 sp, out 304 gp 2 sp
    reconciles EXACTLY to 1,025 gp 2 sp, and the truncated version was out by
    1.2.

    A tolerance that exists to absorb a parsing bug hides the thing the test is
    for. Read the whole number and require it to be exact.
    """
    import re

    def gp(pattern):
        # *** THE SILVER IS OPTIONAL. *** gp_sp() prints "1,046 gp" with no
        # silver at all when a figure lands on a whole gold, and the first
        # version of this test REQUIRED the sp group -- so it went red on day
        # 101 the moment the purse came out even. A test that only passes on
        # untidy numbers is worse than no test.
        m = re.search(pattern, out)
        assert m, 'report did not contain %r' % pattern
        return (float(m.group(1).replace(',', ''))
                + float(m.group(2) or 0) / 10)

    out = ledger.report()
    SP = r'(?: (\d+) sp)?'
    purse = gp(r'THE PURSE: ([\d,]+) gp' + SP)
    anch = gp(r'anchored at ([\d,]+) gp' + SP)
    ins = gp(r'in ([\d,]+) gp' + SP)
    outs = gp(r'out -([\d,]+) gp' + SP)
    # *** EACH PRINTED FIGURE IS ROUNDED TO THE SILVER, so four of them cannot
    # sum exactly. *** Day 101: the true purse was 1,046.05 and gp_sp printed
    # "1,046 gp"; the breakdown summed to 1,046.1 and a 0.001 tolerance called
    # that a failure. The looser bound here is DISPLAY ROUNDING and nothing
    # else -- four figures, each at most half a silver out.
    assert abs((anch + ins - outs) - purse) < 0.25, (anch, ins, outs, purse)
    # And the part that CAN be exact, is: the headline must be the computed
    # purse, not a number that merely looks close to it.
    # The headline is printed to the SILVER, a tenth of a gold piece in this
    # campaign's decimal, and the printer TRUNCATES, so it can sit nearly a whole
    # tenth under the exact figure. Day 135: 2,253.455 printed as 2,253 gp 4 sp,
    # 0.055 out, and the old 0.05 bound called that a failure. It is display
    # rounding and nothing else; the exact total is compared elsewhere.
    assert abs(purse - ledger.total()) < 0.1, (purse, ledger.total())


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


def test_the_salvage_is_IN_ONE_NAMED_PLACE_and_not_in_nine_backpacks():
    """The invariant is in the NAME: one stated place, not nine backpacks.

    *** THIS TEST USED TO ASSERT "basecamp" AND WENT RED ON DAY 102, when the
    party carted the whole 413 lb to Wethersby. *** Its own docstring had
    predicted that -- "if the party fetches it, this test changes with the
    fiction" -- but predicting a break is not the same as surviving one, and
    this is the third time in this campaign a test has pinned a piece of game
    state that play then moved past.

    So it now asserts what the day-96 relocation actually exists to say, which
    no journey invalidates: every piece of the crag salvage has a holder that
    NAMES A PLACE, and they all name the SAME one. The failure it guards
    against is the salvage quietly reverting to "spread" -- i.e. being carried
    by nine people who are not carrying it.
    """
    st = inv.state()
    VAGUE = ('spread', 'one each', '-', '')
    places = {}
    for asset in ('chain_heavy', 'shovel', 'chisel', 'vise_iron',
                  'smith_tools', 'toolbox_mason', 'bellows_hand'):
        for cell in st[asset].values():
            if not cell[0]:
                continue        # a zero cell records an absence, not a place
            holder = (cell[2] or '').strip()
            assert holder.lower() not in VAGUE, (
                '%s holder is %r -- the crag salvage must name a PLACE. That '
                'is the whole point of the day-96 relocation: it is NOT in '
                'nine backpacks.' % (asset, holder))
            places.setdefault(holder.lower().split('--')[0].strip(),
                              []).append(asset)
    # *** ZERO PLACES IS A VALID ANSWER: IT MEANS SOLD. *** On day 100 Hask sold
    # the entire lot to Mund at the market, so the party owns none of it and
    # there is nothing to locate. The invariant only bites while they HOLD it.
    assert len(places) <= 1, (
        'the crag salvage is in %d different places and it travels as one '
        'stack: %r' % (len(places), places))


def test_check_does_not_demand_an_inventory_row_for_an_asset_ANOTHER_TOOL_OWNS():
    """*** THE CHECKER CRIED WOLF ON THE FIRST CORRECT OIL PURCHASE. ***

    `inventory.FOREIGN` lists what inventory.py deliberately does not count:
    oil, because only `light.tsv` knows which flasks have been broached, and
    coin, because `money.tsv` owns it. **log.py REFUSES an inventory row for
    them.** So on day 97, the first time any money row named `oil_flask` -- two
    flasks, which was every flask in Wethersby -- check() demanded the one row
    the write path is built to reject, and turned a green suite red on a
    perfectly correct entry.

    CLAUDE.md: "IF IT EVER CRIES WOLF, LOOSEN THE CHECKER -- do not learn to
    pass --no-verify." The double entry still holds; its other leg is in
    campaign/light.tsv, which is where it belongs.
    """
    import inventory as inv2
    assert 'oil_flask' in inv2.FOREIGN, 'the premise of the exemption is gone'
    # the real files, because the real files are what regressed
    assert [m for s, m in ledger.check() if 'oil_flask' in m] == []


def test_a_FOREIGN_asset_is_still_required_to_NAME_itself_in_money():
    """Loosening the row check must not loosen the rule that money names a thing.

    The exemption is narrow: it forgives a missing INVENTORY row, not a missing
    asset. A money row with no asset is still a FAIL and that is the rule the
    five lost purchases actually broke.
    """
    bad = [dict(asset='', delta='-2', day='97', reason='oil')]
    sev = [s for s, _ in ledger.check(log=bad)]
    assert 'FAIL' in sev
