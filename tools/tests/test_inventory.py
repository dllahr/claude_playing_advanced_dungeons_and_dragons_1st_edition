"""A quantity must carry its unit, and one fact must have one home.

**The `unit` column is the player's design and it is the whole point of this
file.** The retired `inventory.tsv` had a single `qty` cell that was prose
pretending to be a number, and every tool that read it took the first integer it
could find:

    "~2.5 IRON + 8 STANDARD"   read as 2    <- TWO THINGS IN ONE CELL
    "1,072 gp 1 sp"            read as 1
    "~100 lb, ~97 gp"          read as 100  <- a WEIGHT read as a COUNT
    "18 sealed (+1 broached)"  read as 18   <- the broached flask invisible
    "8 (7 sound, 1 damaged)"   read as 8    <- and the damaged rope is the one
                                               that nearly dropped Blartho

Three of those were simply wrong. **One row per (asset, condition), and the unit
is what forces the split** — you cannot write "2.5 person-weeks of iron and 8 of
standard" into a single signed quantity.

AND THE SECOND HALF: ONE FACT, ONE HOME. Oil flasks were counted in both
`inventory.tsv` and `light.tsv` and drifted apart TWICE. Iron spikes were
counted as "carried" by hand while `world_changes.tsv` separately tracked what
was emplaced. Both are now derived from a single source, so there is nothing
left to disagree.
"""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import inventory                                                  # noqa: E402
import ledger                                                     # noqa: E402


# ------------------------------------------------------------- the unit

def test_the_rations_split_that_used_to_read_as_two():
    """THE WORKED EXAMPLE. "~2.5 IRON + 8 STANDARD" was two things in one cell.

    Iron rations keep a month; standard ones do not. They are different assets
    with different prices and different purposes, and the old cell gave every
    tool the number 2 for the pair of them.
    """
    st = inventory.state()
    # THE UNITS are the invariant. The QUANTITIES move every time the party
    # buys food, and pinning them made this fail on the first purchase after
    # it was written -- a stored total wearing a test's clothes.
    assert st['rations_iron'][('', 'person-week')][1] == 'person-week'
    assert st['rations_std'][('', 'person-week')][1] == 'person-week'
    assert 'rations_iron' in st and 'rations_std' in st, (
        'iron and standard are DIFFERENT ASSETS. The retired cell held both '
        'as "~2.5 IRON + 8 STANDARD" and every tool read it as the number 2')
    # *** AND THE LINE THAT USED TO BE HERE PINNED THE QUANTITIES ANYWAY. ***
    # It asserted both were > 0, four lines under a comment saying not to do
    # that, and it went red on day 95 when the party CACHED ALL 2.5 PERSON-
    # WEEKS OF IRON RATIONS in a smithy fire pit -- correct play, not a
    # regression. A test that forbids the party from spending a thing is not
    # protecting anything.
    #
    # The invariant is that they are TWO SEPARATE ROWS with their own units and
    # their own quantities, so that no tool can ever read the pair as one
    # number again. A quantity of zero satisfies that perfectly: it says "we
    # have no iron rations", which is a fact, and the retired cell could not
    # have said it.
    assert st['rations_iron'] is not st['rations_std']
    for aid in ('rations_iron', 'rations_std'):
        assert st[aid][('', 'person-week')][0] >= 0, (
            '%s computes negative -- that is a real error' % aid)


def test_the_damaged_rope_is_visible_on_its_own_row():
    """"8 (7 sound, 1 damaged)" read as 8 and hid which rope not to trust.

    *** THE INVARIANT IS THE SEPARATION, NOT THE COUNT. *** This test pinned
    `sound == 7` and went red on day 95 the moment the party picked a coil of
    rope off the area 13 rack -- which is the party playing the game correctly,
    not a regression. That is the SIXTH time a test in this suite has failed by
    asserting today's game state instead of the property it was written to
    protect; see the docstring in test_party_forbidden.py for the same lesson
    about the party's position.

    What must never come back is a single merged number that hides which coil
    you should not abseil on.
    """
    st = inventory.state()['rope_50ft']
    sound = st[('sound', 'each')][0]
    damaged = st[('damaged', 'each')][0]
    assert damaged >= 1, 'the damaged coil has vanished from the log'
    assert sound >= 1
    assert inventory.qty('rope_50ft') == sound + damaged, (
        'the total must be the sum of the condition rows, not a stored figure')
    assert len([k for k in st if k[0] in ('sound', 'damaged')]) == 2, (
        'sound and damaged rope have been merged into one row -- that is the '
        'bug this test exists for')
    assert 'NOT TO BE TRUSTED' in st[('damaged', 'each')][3]


def test_a_total_across_mixed_units_is_refused_not_summed():
    """Adding person-weeks to flasks is the error the unit column prevents.

    Refusing is the point. A tool that returned 10.5 here would be confidently
    wrong, which is worse than useless.
    """
    log = [dict(asset='x', verb='anchor', qty='2', unit='person-week',
                condition='a', holder='', note=''),
           dict(asset='x', verb='anchor', qty='3', unit='flask',
                condition='b', holder='', note='')]
    with pytest.raises(ValueError, match='more than one unit'):
        inventory.qty('x', log)


def test_every_unit_is_in_the_closed_vocabulary():
    """A typo'd unit would be a second silent unit, which is how this started."""
    bad = [(r.get('asset'), r.get('unit')) for r in inventory.rows()
           if (r.get('unit') or '').strip()
           and r['unit'].strip() not in inventory.UNITS]
    assert not bad, 'units outside the vocabulary: %s' % bad


# ------------------------------------------------- one fact, one home

def test_spikes_carried_is_derived_not_stored():
    """CARRIED = OWNED - EMPLACED, whatever today's numbers happen to be.

    The old file stored "13" by hand beside a world_changes log that separately
    tracked 9 emplaced. Two numbers for one fact is how the spike ledger came to
    show a phantom negative and needed two correcting rows, the first of which
    over-corrected to 7.

    *** THIS TEST USED TO ASSERT `carried_spikes() == 13` AND WENT RED THE
    MOMENT THE PARTY SPIKED A DOOR. *** On day 79 they wedged both secret doors
    of the 8/9 pocket, carried fell to 9, and a test about DERIVATION failed for
    a reason that was simply play happening. That is the third time this shape
    has appeared -- the purse, the party's position, the encounter fixture -- so
    it now asserts the relationship instead of the reading.
    """
    import world
    owned = inventory.qty('iron_spike')
    carried = inventory.carried_spikes()
    placed, _ = world.deployed(world.load())
    emplaced = placed.get('iron spike', 0)
    assert owned > 0
    assert carried == owned - emplaced, (owned, emplaced, carried)
    assert 0 <= carried <= owned, (carried, owned)
    assert emplaced >= 0, 'a NEGATIVE emplacement is the phantom this log had'


def test_oil_is_not_counted_here_at_all():
    """It is light.tsv's, because that log knows which flasks are broached."""
    assert 'oil_flask' in inventory.FOREIGN
    assert not any(r.get('asset') == 'oil_flask' for r in inventory.rows())
    fails = [m for s, m in inventory.check() if s == 'FAIL']
    assert fails == []


def test_check_refuses_a_row_for_a_foreign_asset():
    log = [dict(asset='oil_flask', verb='anchor', qty='18', unit='flask',
                condition='sealed', holder='', note='')]
    fails = [m for s, m in inventory.check(log) if s == 'FAIL']
    assert any('TWO SOURCES FOR ONE FACT' in m for m in fails)


def test_check_refuses_an_unknown_asset_and_an_unknown_unit():
    log = [dict(asset='banana', verb='anchor', qty='1', unit='bushel',
                condition='', holder='', note='')]
    fails = [m for s, m in inventory.check(log) if s == 'FAIL']
    assert any('assets.tsv' in m for m in fails)
    assert any('vocabulary' in m for m in fails)


def test_check_refuses_a_negative_holding():
    log = [dict(asset='dagger', verb='anchor', qty='1', unit='each',
                condition='', holder='', note=''),
           dict(asset='dagger', verb='move', qty='-3', unit='each',
                condition='', holder='', note='')]
    fails = [m for s, m in inventory.check(log) if s == 'FAIL']
    assert any('negative holding' in m for m in fails)


def test_an_anchor_sets_and_a_move_adds():
    log = [dict(asset='dagger', verb='anchor', qty='5', unit='each',
                condition='', holder='', note=''),
           dict(asset='dagger', verb='move', qty='-2', unit='each',
                condition='', holder='', note=''),
           dict(asset='dagger', verb='anchor', qty='8', unit='each',
                condition='', holder='', note='')]
    assert inventory.qty('dagger', log) == 8


# --------------------------------------------------- the retired file

def test_the_old_inventory_is_retired_and_not_read_by_anything():
    """It is in deprecated/ so old citations do not point at nothing."""
    assert not os.path.exists(os.path.join(ROOT, 'campaign', 'inventory.tsv'))
    old = os.path.join(ROOT, 'deprecated', 'inventory.tsv')
    assert os.path.exists(old), 'retiring it must not ORPHAN the citations'
    assert 'RETIRED' in open(old, encoding='utf-8').read(400)


def test_no_tool_still_reads_the_retired_file():
    """A PATH to it, not a MENTION of it.

    Several tools explain in their docstrings why the old file is gone, and that
    prose is the fix rather than the fault -- the same distinction `world.py`
    already draws when it skips a note that points AT the world log. What must
    not survive is a constant that opens it.
    """
    offenders = []
    for fn in sorted(os.listdir(TOOLS)):
        if not fn.endswith('.py'):
            continue
        text = open(os.path.join(TOOLS, fn), encoding='utf-8').read()
        if re.search(r"""['"]campaign['"]\s*,\s*['"]inventory\.tsv['"]""", text):
            offenders.append(fn)
    assert not offenders, (
        '%s still points at the retired campaign/inventory.tsv. Reading a '
        'deprecated file is how a citation becomes a fact again.' % offenders)


def test_disposed_things_have_a_zero_row_not_an_absent_one():
    """A zero says "sold". An absence says nothing at all.

    That difference is exactly how the dragon scales were carried as unsold for
    weeks after they had been sold for 110 gp on day 19.
    """
    st = inventory.state()
    for asset in ('dragon_scales', 'small_goods', 'lab_glass', 'realgar',
                  'ale_barrel_sd', 'dye'):
        assert asset in st, '%s has no row at all -- that is the defect' % asset
        assert sum(v[0] for v in st[asset].values()) == 0
    assert [m for s, m in ledger.check() if s == 'WARN'] == []


# ----------------------------- the unit belongs in the KEY, not just the cell
# Added 2026-09-14. `state()` keyed on CONDITION ALONE and carried the unit as a
# value each row overwrote, so two rows for one asset in the same condition but
# different units shared a cell and the later ANCHOR DESTROYED THE EARLIER:
#
#     day 77  anchor 48 each     -> [48, 'each']
#     day 77  anchor  1 quiver   -> [ 1, 'quiver']   ate the 48
#     day 81  move  +36 each     -> [37, 'each']
#
# The party's forty-eight arrows were invisible for four campaign days, brief.py
# included -- the file the DM reads first every session. Caught by the player
# saying "we have 3 quivers, we bought 1 each at the start of the game" when the
# total came out 37.
#
# CLAUDE.md and the module docstring both promised "one row per (asset,
# condition), with an explicit unit". THE UNIT COLUMN WAS ADDED AND NOTHING WAS
# KEYED ON IT -- the unit-column principle half-applied, which is worse than not
# applying it, because the wrong figure looks authoritative.

def _two_unit_log():
    return [
        dict(asset='arrows', verb='anchor', qty='48', unit='each',
             condition='', holder='spread', note='counted'),
        dict(asset='arrows', verb='anchor', qty='1', unit='quiver',
             condition='', holder='spread', note='off the bandits, uncounted'),
        dict(asset='arrows', verb='move', qty='36', unit='each',
             condition='', holder='spread', note='area 37'),
    ]


def test_two_units_of_one_asset_do_not_share_a_cell():
    st = inventory.state(_two_unit_log())['arrows']
    assert st[('', 'each')][0] == 84, st
    assert st[('', 'quiver')][0] == 1, st


def test_an_anchor_in_ONE_unit_does_not_wipe_ANOTHER():
    """The whole bug in one assertion."""
    st = inventory.state(_two_unit_log())['arrows']
    assert st[('', 'each')][0] != 37, (
        'the quiver anchor ate the 48 arrows again')


def test_mixed_units_are_still_REFUSED_as_a_total():
    """qty() must go on raising rather than adding arrows to quivers."""
    import pytest as _p
    with _p.raises(ValueError):
        inventory.qty('arrows', _two_unit_log())


def test_the_report_still_prints_the_CONDITION_not_the_raw_key():
    """The key became a tuple; the column must not."""
    out = inventory.report(_two_unit_log(), asset='arrows')
    assert "('', 'each')" not in out, 'the compound key leaked into the report'
    assert '84' in out and 'quiver' in out


# --------------------------------------------------- debts are things OWNED
# Added day 93. The player asked whether Fenn's 90 gp was recorded anywhere and
# the answer was NO. TWO receivables existed only in prose -- Fenn's 90 and
# Dill's 1.1 -- because there was no unit for a quantity denominated in money.
#
# *** FENN'S WAS THE DANGEROUS ONE. *** The coin left the purse on day 27,
# INSIDE the day-39 anchor, so money.tsv has no row for it and never will; and
# its last written mention was loop L048, WHICH WAS CLOSED THE DAY BEFORE. A
# debt recorded only inside a closed loop is a debt nobody will ever find again.

def test_every_debt_asset_has_an_inventory_row():
    """A receivable with no quantity is a sentence, which is what these were."""
    ass = ledger.assets()
    debts = [k for k, v in ass.items() if v.get('kind') == 'debt']
    assert debts, 'no debt assets at all -- pick a new fixture'
    held = {r['asset'] for r in inventory.rows()}
    for d in debts:
        assert d in held, (
            '%s is an asset of kind `debt` with no row in inventory_log.tsv. '
            'A debt owed TO the party is a thing the party OWNS and its '
            'quantity must be derived, not narrated.' % d)


def test_a_debt_is_NOT_a_service_so_the_ledger_polices_its_repayment():
    """kind matters. ledger.SERVICE_KINDS are exempt from the "every good has
    an inventory row" leg -- the leg that was missing all five times a purchase
    got recorded as a sentence. Filing a debt as a service would exempt its
    repayment from exactly that check, so when Fenn pays, money.tsv takes +N
    naming loan_fenn and this log must take -N, and the ledger refuses one
    without the other."""
    for k, v in ledger.assets().items():
        if v.get('kind') == 'debt':
            assert v['kind'] not in ledger.SERVICE_KINDS, k


def test_gp_is_for_DEBTS_and_never_becomes_a_second_copy_of_the_purse():
    """THE PURSE IS ledger.py's, computed from money.tsv. A `gp` quantity in
    the inventory log for anything but a debt is a stored copy of a derived
    number, which is the one mistake this whole scheme exists to prevent."""
    ass = ledger.assets()
    for r in inventory.rows():
        if (r.get('unit') or '').strip() == 'gp':
            kind = ass.get(r['asset'], {}).get('kind')
            assert kind == 'debt', (
                '%s carries a `gp` quantity but is kind %r. `gp` is for debts '
                'only; the purse is computed by ledger.py and must not be '
                'mirrored here. (`gp-weight` is the WEIGHT of carried coin and '
                'is a different unit.)' % (r['asset'], kind))
