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
    assert st['rations_iron'][''][1] == 'person-week'
    assert st['rations_std'][''][1] == 'person-week'
    assert 'rations_iron' in st and 'rations_std' in st, (
        'iron and standard are DIFFERENT ASSETS. The retired cell held both '
        'as "~2.5 IRON + 8 STANDARD" and every tool read it as the number 2')
    assert st['rations_iron'][''][0] > 0 and st['rations_std'][''][0] > 0


def test_the_damaged_rope_is_visible_on_its_own_row():
    """"8 (7 sound, 1 damaged)" read as 8 and hid which rope not to trust."""
    st = inventory.state()['rope_50ft']
    assert st['sound'][0] == 7
    assert st['damaged'][0] == 1
    assert inventory.qty('rope_50ft') == 8
    assert 'NOT TO BE TRUSTED' in st['damaged'][3]


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
