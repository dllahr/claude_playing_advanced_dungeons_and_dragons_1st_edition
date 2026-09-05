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

def test_treasure_types_come_from_the_bestiary():
    """The hand-typed table this replaced was wrong for two of six creatures."""
    ind, lair, raw = treasure.monster_types('orc')
    assert ind == 'L'
    # The old table said the orc lair was "D". The MM says C, O, Q (x10), S.
    assert 'D' not in lair
    for letter in ('C', 'O', 'Q', 'S'):
        assert letter in lair


def test_kobold_lair_no_longer_claims_type_d():
    ind, lair, raw = treasure.monster_types('kobold')
    assert ind == 'J'
    assert 'D' not in lair
    assert 'O' in lair and 'Q' in lair


def test_a_lair_only_creature_carries_nothing_individually():
    ind, lair, _ = treasure.monster_types('troglodyte')
    assert ind is None
    assert lair == 'A'


def test_unknown_creature_raises_with_the_options_listed():
    with pytest.raises(KeyError) as e:
        bestiary.stats('gelatinous accountant')
    assert 'troglodyte' in str(e.value)
