"""The packed-load manifest -- who carries what, and what it does to movement.

*** THIS FILE EXISTS BECAUSE THE PLAYER ASKED WHAT THE DATA STRUCTURE WAS AND
*** THE ANSWER WAS "THERE ISN'T ONE."

Day 102. Per-person kit lived in inventory_log's free-text `holder` column --
one string per row, holding "WORN: Dave, Torsat, Yrtone, Blartho" and "ONE EACH:
Dave, Torsat, Tristle, Frython, Hask, Ista -- 2 spare". Thirty-three distinct
hand-typed strings. The per-person table the DM presented had been assembled BY
HAND out of that prose and offered as though computed.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import carry                                                     # noqa: E402


def _log(*rows):
    return [dict(zip(('when', 'day', 'who', 'asset', 'verb', 'qty', 'unit',
                      'note'), r)) for r in rows]


# ------------------------------------------- the structure the holder lacked

def test_two_people_carrying_the_same_asset_do_not_share_a_cell():
    """THE WHOLE POINT. inventory_log physically could not say this.

    Its cell key was (condition, unit) with the holder carried along as a value
    each row overwrote, so "Dave has one and Torsat has one" collapsed into one
    cell and the last holder won.
    """
    st = carry.state(_log(
        ('d', '102', 'Dave', 'long_sword', 'anchor', '1', 'each', ''),
        ('d', '102', 'Torsat', 'long_sword', 'anchor', '1', 'each', '')))
    assert st['Dave'][('long_sword', 'each')] == 1
    assert st['Torsat'][('long_sword', 'each')] == 1


def test_quantities_sum_per_person():
    st = carry.state(_log(
        ('d', '102', 'Ista', 'dart', 'anchor', '15', 'each', ''),
        ('d', '103', 'Ista', 'dart', 'move', '-3', 'each', 'three thrown')))
    assert st['Ista'][('dart', 'each')] == 12


def test_an_anchor_sets_outright_and_does_not_add():
    st = carry.state(_log(
        ('d', '102', 'Dave', 'dagger', 'anchor', '5', 'each', ''),
        ('d', '103', 'Dave', 'dagger', 'anchor', '1', 'each', 'set straight')))
    assert st['Dave'][('dagger', 'each')] == 1


# ------------------------------------------------- the vocabulary is CLOSED

def test_the_who_vocabulary_is_closed_and_free_text_is_refused():
    """A free-typed holder is how this went wrong in the first place."""
    problems = carry.check(_log(
        ('d', '102', 'WORN: Dave, Torsat', 'banded_mail', 'anchor', '2',
         'each', '')))
    assert any('VOCABULARY IS CLOSED' in m for _s, m in problems), problems


def test_every_character_and_party_are_in_the_vocabulary():
    v = carry.who_vocabulary()
    for n in ('Dave', 'Tristle', 'Dellie', 'Brand'):
        assert n in v
    assert carry.SHARED in v
    assert 'spread' not in v, ('"spread" was inventory_log\'s word for '
                               '"somewhere among our possessions", which on '
                               'day 101 included a lean-to 22 miles away')


def test_carriage_may_not_exceed_ownership():
    problems = carry.check(_log(
        ('d', '102', 'Dave', 'long_sword', 'anchor', '99', 'each', '')))
    assert any('may not exceed ownership' in m for _s, m in problems), problems


def test_an_owned_thing_with_nowhere_logged_fails_check():
    """TIGHTENED DAY 103: located == owned, not located <= owned.

    Dave's one long sword is real (characters.tsv/carry.tsv agree the party
    owns one), so an EMPTY manifest is missing it -- the exact shape of the
    headboard and the diary, which had an inventory_log row and no location
    anywhere for seventy days.
    """
    problems = carry.check(_log())
    assert any('located must equal owned' in m and 'long_sword' in m
               for _s, m in problems), problems


def test_places_and_non_pc_people_are_in_the_vocabulary():
    """EXTENDED DAY 103: carry.tsv is now the single "where is everything" log."""
    v = carry.who_vocabulary()
    for n in ('wethersby', 'wend_barn', 'basecamp', 'toller', 'dill'):
        assert n in v, '%r should resolve -- it is an id in people.tsv or ' \
                        'places.tsv' % n
    # a PC's identity-row id (lowercase) is NOT a second entry for that person
    # -- Dave is `Dave` here, from characters.tsv, not also `dave`
    assert 'dave' not in v


def test_the_live_manifest_reconciles():
    assert [m for s, m in carry.check() if s == 'FAIL'] == []


# ------------------------------- the Strength allowance, off the book's table

@pytest.mark.parametrize('score,want', [
    ('18/26', 1000), ('18', 750), ('17', 500), ('16', 350),
    ('14', 200), ('15', 200), ('13', 100), ('12', 100),
    ('11', 0), ('10', 0), ('9', 0), ('8', 0),
    ('7', -150), ('5', -250), ('3', -350),
])
def test_strength_allowance_is_read_from_the_book_table(score, want):
    """*** THREE THINGS BROKE THE FIRST PARSER AND ALL THREE ARE IN THE TABLE.

    A blank SPACER column between two column-pairs, so the right-hand pair is
    cells 3 and 4; a U+2212 MINUS and EN-DASHES, which `[+-]` matches neither
    of; and two values that are the WORD "normal".

    The first version returned +0 for STR 18/26 AND for STR 3 alike -- which
    would have let Dave carry exactly what Dellie carries.
    """
    assert carry._allowance_lookup(score) == want


def test_every_character_has_a_strength_the_tool_can_read():
    """It was scattered across party_roster.md and rolls.tsv for 102 days."""
    for name, r in carry.characters().items():
        s = (r.get('str') or '').strip()
        assert s, '%s has no str in characters.tsv -- encumbrance needs it' % name
        carry._allowance_lookup(s)          # must not raise


# ------------------------------------------------ the bands, and the sharing

def test_the_allowance_is_added_to_every_band_not_just_the_first():
    """PHB: "Strength penalties or bonuses will modify these guidelines"."""
    assert carry.band_for(1000, 0)[0] == 'very heavy'
    assert carry.band_for(1000, 1000)[0] == 'normal'
    assert carry.band_for(1349, 1000)[1] == '12"'


def test_a_strength_PENALTY_shrinks_the_bands():
    """DEX 4 is Dellie's problem; a STR 3 would be this one."""
    assert carry.band_for(300, 0)[0] == 'normal'
    assert carry.band_for(300, -350)[0] != 'normal'


def test_the_shared_kit_is_apportioned_and_not_ignored():
    """*** THE PART EVERY HAND-CALCULATION GOT WRONG. ***

    The rope, rations, sacks and torches are most of what the party lifts, and
    counting only personal kit flatters every single load.
    """
    gp, lines = carry.shared_total()
    assert gp > 0 and lines
    out = carry.report()
    assert 'TOTAL SHARED' in out and 'divided among' in out


def test_fewer_bearers_means_more_each():
    """Ten people sharing the rope carry less each than three do."""
    ten = carry.report()
    three = carry.report(bearers=['Dave', 'Yrtone', 'Tristle'])
    assert 'divided among 3 bearers' in three
    assert 'divided among 10 bearers' in ten


# ----------------------------------- the two standing views, added day 103
# Both of these were typed out by hand once and were stale ONE MESSAGE LATER,
# when the second lantern moved from Yrtone to Dave. That is why they are
# scripts.

def test_roster_itemises_every_person_and_names_the_unweighed():
    out = carry.roster()
    for name in ('Dave', 'Tristle', 'Frython', 'Brand'):
        assert name in out
    assert 'UNWEIGHED' in out, (
        'as long as any carried thing lacks a weight, the roster must SAY so '
        'beside it -- an honest gap beats a total that quietly omits things')
    assert 'gp-wt' in out and 'lb' in out


def test_roster_says_so_when_somebody_carries_nothing_of_their_own():
    """A live-state script, not a fixture -- it is UPDATED as play moves the
    manifest, not converted away from checking the real file (see the note
    above this section). Brand carried nothing of his own from day 95 until
    day 139, when he took up his own axe again plus three salvaged orc axes
    as ammunition; the roster now itemises them instead of saying so."""
    out = carry.roster()
    assert 'Brand' in out and 'nothing of his own' not in out.split('Brand')[1]
    assert 'hand_axe' in out


# ------------------------------------------------- where: the complement of roster

def test_where_lists_a_place_but_not_a_character_or_party():
    """Added day 139, after a hand-rolled one-off script got a basecamp total
    wrong by summing anchors additively instead of letting the last one win.
    `roster` already answers what a PERSON carries; `where` answers what a
    PLACE holds, which nothing had before."""
    out = carry.everywhere(_log(
        ('d', '139', 'basecamp', 'cart', 'anchor', '2', 'each', ''),
        ('d', '139', 'Dave', 'long_sword', 'anchor', '1', 'each', '')))
    assert 'basecamp:' in out
    assert 'cart' in out
    assert 'Dave' not in out
    assert 'party:' not in out


def test_where_respects_anchor_sets_outright_same_as_state():
    """The exact bug this subcommand exists to stop: a naive additive sum of
    two anchors gives 3; the real total, last-anchor-wins, is 1."""
    out = carry.everywhere(_log(
        ('d', '135', 'basecamp', 'cart', 'anchor', '2', 'each', ''),
        ('d', '139', 'basecamp', 'cart', 'anchor', '1', 'each', 'corrected')))
    assert '        2 each' not in out
    assert '        1 each' in out


def test_where_omits_a_holder_whose_balance_has_gone_to_zero():
    out = carry.everywhere(_log(
        ('d', '135', 'basecamp', 'torch', 'anchor', '3', 'each', ''),
        ('d', '139', 'basecamp', 'torch', 'move', '-3', 'each', 'used up')))
    assert 'basecamp' not in out


# ------------------------------------------------- fill the strongest first

def test_pack_fills_the_strongest_first():
    rows, _left, _shared = carry.pack()
    assert rows[0][0] == 'Dave', rows[0]
    takes = [r[5] for r in rows]
    assert takes[0] == max(takes), 'Dave has the +1,000 and should take most'


def test_pack_breaks_ties_on_RAW_strength_not_just_allowance():
    """*** WITHOUT THE SECOND SORT KEY THIS WAS WRONG. ***

    Hask and Dellie at STR 11 were ordered BEHIND Frython at STR 8, because all
    three share a +0 allowance. The rule is "start with the strongest, then the
    subsequently lower strength members".
    """
    order = [r[0] for r in carry.pack()[0]]
    assert order.index('Hask') < order.index('Frython')
    assert order.index('Dellie') < order.index('Tristle')
    assert order.index('Tristle') < order.index('Frython')


def test_nobody_is_filled_past_the_target_band():
    chars = carry.characters()
    for name, _s, alw, _own, _room, _take, tot in carry.pack()[0]:
        band, _move = carry.band_for(tot, alw)
        assert band in ('normal', 'heavy'), (name, tot, alw, band)


def test_pack_conserves_the_shared_weight():
    """Placed plus left over must equal what there was. It is a division."""
    rows, left, shared = carry.pack()
    assert abs(sum(r[5] for r in rows) + left - shared) < 1e-6


def test_a_harder_target_leaves_weight_behind():
    """Filling everybody only to 12" cannot absorb 348 lb, and must say so."""
    _rows, left, _shared = carry.pack(target='normal')
    assert left > 0
    assert 'CANNOT BE CARRIED' in carry.pack_report(target='normal')


def test_the_easy_target_absorbs_it_all_and_says_the_party_rate():
    """Day 118: orc salvage (six hand axes, a short bow, a spear, two
    polearms, two light crossbows) plus the area 11 supply room's nails,
    mortar and hardware box added ~150 lb of shared kit. 'heavy' (9") no
    longer absorbs all of it -- 'very heavy' (6") is now the target that
    does, which is exactly what the player computed at the table before
    this was logged."""
    out = carry.pack_report(target='very heavy')
    assert 'IT ALL FITS' in out
    assert 'THE PARTY MOVES AT 6"' in out


def test_fewer_bearers_can_make_it_stop_fitting():
    """Three people cannot carry what ten can, and the tool must not pretend.
    (A synthetic kit, not the live one: the live load changes every day and a
    pack horse took most of it on day 120.)"""
    log = _log(('d', '1', 'party', 'rope_50ft', 'anchor', '200', 'each', ''))
    _r, left, _s = carry.pack(log=log, bearers=['Dave', 'Frython', 'Brand'])
    assert left > 0


def test_a_bearer_over_the_band_on_his_own_kit_is_not_within_it():
    """Day 120: `pack --target normal` said EVERY MEMBER IS WITHIN normal (12")
    while Blartho's OWN kit, 745 gp-wt, sat above his normal ceiling of 550.
    A bearer already over the band by himself leaves weight that cannot be
    carried at that band, even with no shared kit at all."""
    log = _log(('d', '1', 'Blartho', 'banded_mail', 'anchor', '2', 'each', ''))
    _r, left, _s = carry.pack(log=log, bearers=['Blartho'], target='normal')
    assert left > 0


# ------------------------------------------- standing exemptions (day 119)

def test_standing_exempt_latest_row_per_name_wins(tmp_path):
    """Tristle is exempt from the shared kit by the player's standing
    instruction of day 119. The file is append-only; `resume` undoes it."""
    f = tmp_path / 'carry_exempt.tsv'
    f.write_text('# c\ndate\tday\twho\taction\tnote\n'
                 '2026-09-24\t119\tTristle\texempt\tx\n'
                 '2026-09-24\t119\tDave\texempt\tx\n'
                 '2026-09-25\t120\tDave\tresume\tx\n')
    assert carry.standing_exempt(str(f)) == {'Tristle'}


def test_a_missing_exempt_file_means_nobody_is_exempt(tmp_path):
    assert carry.standing_exempt(str(tmp_path / 'nope.tsv')) == set()


def test_the_live_exemption_keeps_tristle_at_twelve_inches():
    """`person Tristle` used to charge him a share even when he was not among
    the bearers. With the standing exemption his own kit alone sets his rate."""
    import subprocess
    out = subprocess.run([sys.executable, os.path.join(TOOLS, 'carry.py'),
                          'person', 'Tristle'], capture_output=True,
                         text=True).stdout
    assert '0 share of the common kit' in out
    assert 'movement 12"' in out


def test_the_party_rate_survives_the_exemption():
    """The exemption must not push so much onto the other nine that the party
    loses more than a band against what everybody sharing would give. (The live
    load changes every expedition, so this compares the two, it does not pin a
    band.)"""
    import party
    b = carry.default_bearers()
    assert b is not None and 'Tristle' not in b
    with_ex = party._band_inches(bearers=b)
    everyone = party._band_inches(bearers=b + ['Tristle'])
    assert with_ex >= everyone - 3
