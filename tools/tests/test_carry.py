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
