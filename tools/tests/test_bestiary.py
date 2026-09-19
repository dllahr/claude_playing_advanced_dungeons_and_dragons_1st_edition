"""The bestiary, and the errors that made it necessary."""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import bestiary                                                 # noqa: E402
import treasure                                                 # noqa: E402

ALL = sorted(bestiary.creatures())


def test_the_bestiary_is_not_empty():
    assert ALL


@pytest.mark.parametrize('name', ALL)
def test_every_creature_has_a_readable_stat_block(name):
    d, source = bestiary.stats(name)
    for field in ('Armor Class', 'Hit Dice', 'Move', 'Number of Attacks',
                  'Damage', 'Treasure Type', 'Alignment', 'Size'):
        assert field in d, '%s has no %r' % (name, field)
    assert source, '%s stat block has no *source:* line' % name
    assert 'Monster Manual' in source


@pytest.mark.parametrize('name', ALL)
def test_every_creature_declares_both_surprise_numbers(name):
    """The default of 2 is wrong often enough that it must be stated.

    Troglodyte chameleon skin surprises on 1-4 and taking the default got two
    separate encounters wrong.
    """
    for f in ('Surprised On', 'Surprises On'):
        v = bestiary.field(name, f)
        assert v.isdigit(), '%s: %s is %r, not a number' % (name, f, v)


def test_the_troglodyte_surprise_range_is_four():
    assert bestiary.field('troglodyte', 'Surprises On') == '4'
    assert bestiary.field('kobold', 'Surprises On') == '2'


def test_berserkers_never_check_morale():
    """MM p.67. Not in B1's stat block, and it decides how the fight ends."""
    assert 'never' in bestiary.field('berserker', 'Morale').lower()


def test_troglodyte_damage_is_the_mm_value_not_the_module_one():
    """B1 prints 1-4/1-4/1-4; the MM gives two claws and a bite."""
    assert bestiary.field('troglodyte', 'Damage').startswith('1-3/1-3/2-5')


# ------------------------------------------------- treasure, via the bestiary

def _letters(pairs):
    return [letter for letter, _mult in pairs]


def test_treasure_types_come_from_the_bestiary():
    """The hand-typed table this replaced was wrong for two of six creatures."""
    ind, lair, raw = treasure.monster_types('orc')
    assert _letters(ind) == ['L']
    # The old table said the orc lair was "D". The MM says C, O, Q (x10), S.
    assert 'D' not in _letters(lair)
    for letter in ('C', 'O', 'Q', 'S'):
        assert letter in _letters(lair)


def test_kobold_lair_no_longer_claims_type_d():
    ind, lair, raw = treasure.monster_types('kobold')
    assert _letters(ind) == ['J']
    assert 'D' not in _letters(lair)
    assert 'O' in _letters(lair) and 'Q' in _letters(lair)


def test_a_lair_only_creature_carries_nothing_individually():
    ind, lair, _ = treasure.monster_types('troglodyte')
    assert ind == []
    assert _letters(lair) == ['A']


# --------------------------------------------- the day-99 gnoll parse failure
#
# Every case below returned a WRONG answer before 2026-09-18, and none of them
# raised. The parser matched only "<letter> individually" and the Monster Manual
# writes the same fact three ways.

def test_a_creature_carrying_two_individual_types_reports_both():
    """The gnoll is 'Individuals L, M' -- word first, and TWO letters.

    This printed "no individual treasure" for four days, which is a confident
    wrong answer about a body the party was standing over.
    """
    ind, lair, raw = treasure.monster_types('gnoll')
    assert _letters(ind) == ['L', 'M'], raw
    assert _letters(lair) == ['D', 'Q', 'S'], raw


def test_a_letter_range_expands_and_lands_on_the_individual_side():
    """The crab spider is 'J-N, Q' with no qualifying word anywhere.

    J-N was filed as a LAIR hoard, and no J-N letter is a lair type, so
    roll_lair would have refused it.
    """
    ind, lair, raw = treasure.monster_types('crab spider')
    assert _letters(ind) == ['J', 'K', 'L', 'M', 'N'], raw
    assert _letters(lair) == ['Q'], raw


def test_the_multiplier_is_not_discarded():
    """'Q (x10)' means ten hoard rolls. It used to mean one."""
    _ind, lair = treasure.parse_types('C, O, Q (x10), S in lair')
    assert dict(lair)['Q'] == 10
    assert dict(lair)['C'] == 1


def test_the_capital_x_in_the_mm_multiplier_is_not_read_as_type_x():
    """The MM prints it as '( X 20)'. Type X is a real treasure type."""
    ind, lair = treasure.parse_types('Individuals M ( X 3); C, Q ( X 20) in lair')
    assert dict(ind) == {'M': 3}
    assert dict(lair) == {'C': 1, 'Q': 20}
    assert 'X' not in dict(lair)


def test_individual_and_lair_letter_sets_are_disjoint():
    """This is WHY classifying by letter is exact rather than a heuristic.

    If the two tables ever overlapped, parse_types would be guessing.
    """
    assert not (set(treasure.LAIR) & set(treasure.INDIVIDUAL))
    assert set(treasure.INDIVIDUAL) == set('JKLMN')


def test_nil_carries_nothing_either_way():
    assert treasure.parse_types('Nil') == ([], [])
    ind, lair, _ = treasure.monster_types('skeleton')
    assert (ind, lair) == ([], [])


def test_unknown_creature_raises_with_the_options_listed():
    with pytest.raises(KeyError) as e:
        bestiary.stats('gelatinous accountant')
    assert 'troglodyte' in str(e.value)
