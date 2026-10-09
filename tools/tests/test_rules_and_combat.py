"""The rules cache, the modifier stack, and the numbers already got wrong once.

Several of these assert values that were stated incorrectly during play and are
recorded in CHECKLIST.md's "got wrong from memory" table. They are here so the
same mistake cannot come back through the code path.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import combat                                                   # noqa: E402
import dice                                                     # noqa: E402
import rules                                                    # noqa: E402


class Seq(object):
    """A deterministic stand-in for `random`, returning a fixed sequence."""

    def __init__(self, *values):
        self.values = list(values)

    def randint(self, a, b):
        v = self.values.pop(0)
        assert a <= v <= b, 'seeded %d outside %d..%d' % (v, a, b)
        return v


# ------------------------------------------------------------ the cache

def test_every_combat_table_is_cited():
    """A table without a source line is a rule nobody can check."""
    for key, t in rules.load(['combat.md', 'abilities.md']).items():
        if 'Morale' in key or 'Missile rate' in key:
            continue          # cited in the prose above them, not a source line
        assert t['source'], '%s has no *source:* line' % key


def test_monster_matrix_values_that_were_got_wrong():
    t = rules.find('To-hit, monsters')
    # CHECKLIST: "a 1 HD monster needs 16 to hit AC 3, where a level-1 fighter
    # would need 17". Both halves.
    assert rules.lookup(t, '3', '1') == '16'
    # CHECKLIST: "to-hit, 2 HD vs AC 3 -> 13, not 9 (1eonline was wrong)".
    assert rules.lookup(t, '3', '2-3+') == '13'


def test_character_matrix_differs_from_monster_matrix():
    c = rules.find('To-hit, characters')
    assert rules.lookup(c, '3', 'Fighter') == '17'
    m = rules.find('To-hit, monsters')
    assert rules.lookup(m, '3', '1') == '16'


def test_thief_and_magic_user_are_worse_than_fighter_at_level_one():
    c = rules.find('To-hit, characters')
    for ac in ('10', '5', '0'):
        f = int(rules.lookup(c, ac, 'Fighter'))
        th = int(rules.lookup(c, ac, 'Thief'))
        assert th >= f


def test_find_refuses_an_ambiguous_fragment():
    with pytest.raises(KeyError):
        rules.find('To-hit')            # matches both matrices


# ------------------------------------------------------- hit dice bands

@pytest.mark.parametrize('hd,band', [
    ('1', '1'), ('1+1', '1+'), ('2', '2-3+'), ('3+3', '2-3+'),
    ('4', '4-5+'), ('8', '8-9+'), ('16', '16+'), ('20', '16+'),
])
def test_hd_band(hd, band):
    assert combat.hd_band(hd) == band


def test_a_plus_above_three_is_another_hit_die():
    """DMG p.75: "Any plus above +3 equals another hit die, i.e. 6+6 equals 7"."""
    assert combat.hd_band('3+4') == combat.hd_band('4')
    assert combat.hd_band('6+6') == combat.hd_band('7')


# ---------------------------------------------------- the modifier stack

def _char(**kw):
    base = dict(name='X', **{'class': 'Fighter'})
    base.update(melee_hit='0', melee_dmg='0', missile_hit='0',
                proficient='long sword', bonus_weapons='-')
    base.update(kw)
    return base


def test_non_proficiency_penalty_is_the_class_value():
    """CHECKLIST: thief -3, cleric -3, fighter -2, magic-user -5."""
    for cls, pen in (('Thief', -3), ('Cleric', -3), ('Fighter', -2),
                     ('Magic-User', -5)):
        assert combat.proficiency_penalty(cls) == pen


def test_non_proficient_weapon_takes_the_penalty():
    c = _char(**{'class': 'Thief', 'proficient': 'long sword,short bow'})
    mods = combat.attack_modifiers(c, 'spear')
    assert sum(m.value for m in mods) == -3


def test_the_spear_question_the_player_actually_asked():
    """Tristle, thief 1, non-proficient spear, vs AC 7 -> needs 17."""
    c = _char(**{'class': 'Thief', 'proficient': 'long sword,short bow'})
    base, _ = combat.target_number('Thief', 7)
    mods = combat.attack_modifiers(c, 'spear')
    assert base - sum(m.value for m in mods) == 17


def test_strength_bonus_does_not_apply_to_a_bow():
    """rules/abilities.md: the STR adjustments are melee-and-hurled only."""
    assert combat.takes_strength('long sword')
    assert combat.takes_strength('dart')          # hurled -- it does apply
    assert not combat.takes_strength('short bow')
    assert not combat.takes_strength('sling')


def test_dexterity_adjustment_applies_to_missiles_not_melee():
    c = _char(missile_hit='3', melee_hit='0',
              proficient='long sword,short bow')
    ranged = combat.attack_modifiers(c, 'short bow')
    melee = combat.attack_modifiers(c, 'long sword')
    assert sum(m.value for m in ranged) == 3
    assert sum(m.value for m in melee) == 0


def test_racial_bonus_stacks_with_dexterity():
    """Tristle: +1 elf with the bow AND +3 from DEX 18. They are separate."""
    c = _char(**{'class': 'Thief', 'missile_hit': '3',
                 'proficient': 'long sword,short bow',
                 'bonus_weapons': 'long sword,short bow'})
    assert sum(m.value for m in combat.attack_modifiers(c, 'short bow')) == 4


# -------------------------------------------------------------- damage

def test_weapon_damage_handles_the_phb_inverted_names():
    assert combat.weapon_damage('long sword') == '1-8'
    assert combat.weapon_damage('long sword', 'L') == '1-12'
    assert combat.weapon_damage("footman's flail") == '2-7'


def test_unknown_weapon_raises_rather_than_guessing():
    with pytest.raises(KeyError):
        combat.weapon_damage('vorpal chainsaw')


# ---------------------------------------------------------------- dice

def test_range_notation_picks_the_right_dice():
    """1e "3-18" is 3d6, not a flat pick from 3 to 18."""
    r = dice.range_roll('3-18', log=False, rng=Seq(6, 6, 6))
    assert r.total == 18
    r = dice.range_roll('2-7', log=False, rng=Seq(1))
    assert r.total == 2                     # 1d6+1
    r = dice.range_roll('1-6', log=False, rng=Seq(4))
    assert r.total == 4


def test_range_notation_is_never_uniform_over_the_range():
    lo = dice.range_roll('3-18', log=False, rng=Seq(1, 1, 1))
    assert lo.total == 3
    assert len(lo.dice) == 3


def test_notation_rejects_nonsense():
    with pytest.raises(ValueError):
        dice.roll('d', log=False)
    with pytest.raises(ValueError):
        dice.roll('sword', log=False)


# ------------------------------------------------------- saves, morale

def test_natural_one_always_fails_a_save():
    """DMG p.79: "A roll of 1 is always failure"."""
    c = dict(name='Y', **{'class': 'Cleric'})
    lines, made = combat.saving_throw('Y', c, 'Paralyze', adjust=+10,
                                      rng=Seq(1))
    assert not made
    assert any('natural 1' in ln for ln in lines)


def test_save_uses_the_right_class_row():
    c = dict(name='F', **{'class': 'Magic-User'})
    lines, made = combat.saving_throw('F', c, 'Spell', rng=Seq(12))
    assert made                     # magic-user 1-5 saves vs spell on 12


def test_morale_plus_is_the_hit_dice_plus_not_rolled_hp():
    """DMG p.67: "+1%/hit point above any hit dice" is the "+n" in 3+2."""
    lines, held, _ = combat.morale('3+2', rng=Seq(62))
    assert held                          # score is exactly 62
    assert any('62' in ln for ln in lines)
    lines, held, _ = combat.morale('3+2', rng=Seq(63))
    assert not held


def test_a_one_hit_die_creature_scores_fifty():
    lines, held, _ = combat.morale('1', rng=Seq(50))
    assert held
    lines, held, result = combat.morale('1', rng=Seq(51))
    assert not held
    assert result == 'Fall back, fighting'


def test_morale_failure_bands():
    # "Disengage - retreat" carries a plain hyphen because rules.clean()
    # normalises every dash variant; the markdown prints an em dash.
    for rolled, expect in ((51, 'Fall back, fighting'),
                           (66, 'Disengage - retreat'),
                           (81, 'Flee in panic'),
                           (100, 'Flee in panic')):
        _, held, result = combat.morale('1', rng=Seq(rolled))
        assert not held
        assert result == expect, '%d gave %r' % (rolled, result)


def test_surrender_needs_a_situational_modifier():
    """A 1 HD creature scores 50%, so a bare d100 tops out at a 50% margin.

    Surrender (51%+) is therefore unreachable without a trigger from the table
    in rules/combat.md -- a leader slain is +30%, half the band down is +15%.
    That is a property of the system, not a gap in the tool.
    """
    _, held, result = combat.morale('1', rng=Seq(100))
    assert result == 'Flee in panic'
    _, held, result = combat.morale('1', modifier=30, why='leader slain',
                                    rng=Seq(100))
    assert not held and result == 'Surrender'


# ------------------------------------------------------------ initiative

def test_initiative_high_wins_and_ties_are_simultaneous():
    lines, scores = initiative_lines = combat.initiative(rng=Seq(5, 2))
    assert 'party act first' in '\n'.join(lines)
    lines, _ = combat.initiative(rng=Seq(3, 3))
    assert 'simultaneous' in '\n'.join(lines)


def test_surprise_range_is_explicit_not_assumed():
    """Troglodyte chameleon skin surprises on 1-4 (MM). A 3 was once rolled,
    announced as "party alert" against the default 1-2, and had to be corrected
    mid-encounter."""
    _, s = combat.surprise(surprised_on=2, rng=Seq(3))
    assert not s
    _, s = combat.surprise(surprised_on=4, why='troglodyte chameleon skin',
                           rng=Seq(3))
    assert s


def test_dexterity_adjustment_shifts_surprise():
    """PHB p.11: the Reaction/Attacking adjustment covers surprise as well."""
    _, s = combat.surprise(surprised_on=2, adjust=0, rng=Seq(2))
    assert s
    _, s = combat.surprise(surprised_on=2, adjust=3, rng=Seq(2))
    assert not s


# ------------------------------------ both sides at once (day 163)
#
# Tristle rolled 2 (within his own 1-2), three gnolls rolled 1 (within
# theirs) -- both sides independently cleared their own threshold, the
# exact tied-range case where DMG p.62's printed table and its own worked
# example disagree. The DM picked the worked-example reading (higher
# roller inactive) without flagging it; the player caught it and restated
# the day-118 ruling: the TABLE governs, so the LOWER roll is surprised and
# owes the segments. These tests pin that down in code so it cannot be
# re-litigated from memory under pressure a third time.

def test_neither_side_surprised_owes_nothing():
    _, r = combat.resolve_surprise('Tristle', 'gnolls', rng=Seq(5, 6))
    assert not r['a']['surprised'] and not r['b']['surprised']
    assert r['a']['segments'] == 0 and r['b']['segments'] == 0


def test_one_side_surprised_owes_its_OWN_roll():
    """The long-cached, unambiguous case: untouched by the tied-range fix."""
    _, r = combat.resolve_surprise('Tristle', 'gnolls', rng=Seq(2, 5))
    assert r['a']['surprised'] and not r['b']['surprised']
    assert r['a']['segments'] == 2 and r['b']['segments'] == 0


def test_the_actual_day_163_roll_the_LOWER_side_owes_the_difference():
    """Tristle=2, gnolls=1. Both clear 1-2. TABLE reading: the lower roll
    (gnolls, 1) is surprised and owes 2-1=1 segment; Tristle (2) owes
    nothing -- the opposite of what got narrated live at the table."""
    _, r = combat.resolve_surprise('Tristle', 'gnolls', rng=Seq(2, 1))
    assert r['a']['surprised'] and r['b']['surprised']
    assert r['a']['segments'] == 0, 'the higher roll must not be charged'
    assert r['b']['segments'] == 1


def test_the_difference_can_land_on_either_side():
    _, r = combat.resolve_surprise('Tristle', 'gnolls', rng=Seq(1, 2))
    assert r['a']['segments'] == 1 and r['b']['segments'] == 0


def test_both_surprised_EQUALLY_cancels():
    """DMG p.61: 'it is possible for both parties to be surprised EQUALLY --
    with surprise thus having no effect.'"""
    _, r = combat.resolve_surprise('Tristle', 'gnolls', rng=Seq(1, 1))
    assert r['a']['surprised'] and r['b']['surprised']
    assert r['a']['segments'] == 0 and r['b']['segments'] == 0


def test_a_non_default_threshold_is_honoured_per_side():
    """Troglodyte chameleon skin again, but now on one side of a two-sided
    call: surprised on 1-4, not 1-2."""
    _, r = combat.resolve_surprise('party', 'troglodyte', b_surprised_on=4,
                                    rng=Seq(5, 3))
    assert not r['a']['surprised']
    assert r['b']['surprised'] and r['b']['segments'] == 3


def test_dexterity_adjustment_can_rescue_a_side_from_surprise():
    _, r = combat.resolve_surprise('Tristle', 'gnolls', a_adjust=3,
                                    rng=Seq(2, 1))
    assert not r['a']['surprised'], 'DEX +3 should push 2 out of the 1-2 range'
    assert r['b']['surprised'] and r['b']['segments'] == 1, (
        'B is the only one left surprised, so it owes its OWN roll (1), '
        'not a difference')


def test_attack_spec_carries_an_optional_modifier():
    assert combat.parse_attack('Dave:long sword') == ('Dave', 'long sword', ())
    who, weapon, extra = combat.parse_attack('Dave:long sword:+2:rear attack')
    assert (who, weapon) == ('Dave', 'long sword')
    assert extra[0][0] == 2 and 'rear' in extra[0][1]


def test_rear_attack_bonus_is_the_dmg_value():
    """DMG p.70: rear attacks are +2, and a flank attack is worth nothing
    against a defender with no shield."""
    # rules.clean() strips bold markers and normalises every dash variant, so
    # the row key is 'Rear' and the em dash comes back as a plain hyphen.
    t = rules.find('Flank and rear')
    assert rules.lookup(t, 'Rear', 'To hit') == '+2'
    assert rules.lookup(t, 'Flank', 'To hit') == '-'
    assert rules.lookup(t, 'Flank', "Defender's shield") == 'negated'


def test_a_launcher_resolves_damage_as_its_ammunition():
    """The PHB damage table has "Arrow", not "short bow". Firing a bow raised a
    KeyError in the middle of a volley."""
    assert combat.weapon_damage('short bow') == combat.weapon_damage('arrow')
    assert combat.weapon_damage('short bow') == '1-6'
    assert combat.weapon_damage('sling') == '2-5'
    assert combat.weapon_damage('sling stone') == '1-4'


def test_proficiency_still_keys_off_the_launcher_not_the_ammunition():
    """A character is proficient in the bow, never in arrows."""
    c = _char(**{'class': 'Thief', 'proficient': 'short bow', 'missile_hit': '3'})
    assert sum(m.value for m in combat.attack_modifiers(c, 'short bow')) == 3
    assert sum(m.value for m in combat.attack_modifiers(c, 'arrow')) == 0


@pytest.mark.parametrize('hd', ['1/2', '1/4', '1-4 hit points',
                                '1-2 hit points', '½'])
def test_fractional_hit_dice_fall_in_the_lowest_dmg_band(hd):
    """Regression: the three commonest wandering monsters on B1 level 1 could
    not attack AT ALL.

    Kobolds and giant rats are 1/2 hit dice in the MM and giant centipedes 1/4,
    and the bestiary files spell it the module's way -- "1-4 hit points". None
    of those forms parsed, so `combat.py monster --creature giant-rat` raised
    ValueError in the middle of an encounter instead of rolling a bite. Found
    live at round 1204 with two rats already in contact. They all belong in the
    DMG p.75 "up to 1-1" column.
    """
    assert combat.hd_band(hd) == 'up to 1-1'


def test_whole_hit_dice_still_band_as_before():
    """The fractional branch must not swallow ordinary hit dice."""
    assert combat.hd_band('1') == '1'
    assert combat.hd_band('2-1') == '1'
    assert combat.hd_band(2) == '2-3+', 'the DMG bands 2 and 3 HD together'


def test_a_monster_attack_with_NIL_damage_does_not_crash():
    """Regression, found mid-encounter with two centipedes on the table.

    Some attacks do no hit point damage at all and the Monster Manual says so
    in one word: "Nil". A giant centipede is the example — it bites, the bite
    does nothing, and the poison is the whole attack. Passing that string to
    the dice parser raised `cannot read dice notation 'Nil'` and the encounter
    stopped dead.

    The attack must still resolve: it can HIT, it deals 0, and the caller is
    told to go and resolve the special attack.
    """
    import random

    class Fixed(object):
        def randint(self, a, b):
            return 20                      # always a natural 20, always a hit

    for nil in ('Nil', 'nil', 'none', '-', ''):
        lines, hit, dmg = combat.monster_attack(
            hd='1/4', target_ac=9, damage=nil, name='giant centipede',
            rng=Fixed())
        assert hit is True, nil
        assert dmg == 0, nil
        assert any('NIL' in ln for ln in lines), nil


def test_a_monster_attack_with_real_damage_still_rolls_it():
    """The nil branch must not swallow ordinary attacks."""
    class Fixed(object):
        def randint(self, a, b):
            return b
    lines, hit, dmg = combat.monster_attack(
        hd='1', target_ac=9, damage='1-8', name='orc', rng=Fixed())
    assert hit is True and dmg == 8


def test_all_expands_inside_a_comma_list():
    """'all,Hask,Dellie' — a party award a half-share ally was also present for.

    'all' used to be an exact-match-only token. Written inside a list it split
    into a NAME, matched no character, and was silently dropped: the six PCs got
    nothing and the two half-share allies split the entire award between them.

    Caught in play 2026-09-01 when a 435 xp treasure row moved nobody's total
    except the two NPCs'. The failure mode is the dangerous one -- it produced a
    plausible-looking wrong answer rather than an error.
    """
    import xp as xpmod
    chars = {
        'A': dict(cls='Fighter', prime='STR', score='12', bonus=False,
                  treasure_weight=1.0, is_party=True, next_level=2000),
        'B': dict(cls='Cleric', prime='WIS', score='12', bonus=False,
                  treasure_weight=1.0, is_party=True, next_level=1500),
        'N': dict(cls='Thief', prime='DEX', score='12', bonus=False,
                  treasure_weight=0.5, is_party=False, next_level=1250),
    }
    # TREASURE still halves the henchman: 2 full + 1 half = 2.5 shares,
    # 100/2.5 = 40 a full share and 20 the half.
    log = [dict(kind='treasure', xp='100', earned_by='all,N', notes='')]
    tot, _ = xpmod.totals(chars=chars, log=log)
    assert tot['A'] == 40 and tot['B'] == 40, 'the PCs were dropped again'
    assert tot['N'] == 20

    # and bare 'all' must still mean the party and nobody else
    log = [dict(kind='treasure', xp='100', earned_by='all', notes='')]
    tot, _ = xpmod.totals(chars=chars, log=log)
    assert tot['A'] == 50 and tot['B'] == 50 and tot['N'] == 0


def test_monster_xp_is_a_full_share_but_treasure_xp_is_not():
    """The two kinds of award are weighted differently, and on purpose.

    DMG p.85's halving sentence lives inside "Division of Experience Points",
    whose opening line is about SLAIN MONSTERS and whose worked example is
    monster xp. The next heading, EXPERIENCE VALUE OF TREASURE TAKEN, never
    mentions henchmen -- treasure xp is 1 gp = 1 xp on coin actually gained, so
    a half share of the coin already yields half the xp and halving the award
    too would halve it twice.

    Ruled day 39 (2026-09-05): Hask, Dellie and Ista became classed characters
    and now draw a FULL share of monster xp, a HALF share of treasure.
    """
    import xp as xpmod
    chars = {
        'A': dict(cls='Fighter', prime='STR', score='12', bonus=False,
                  treasure_weight=1.0, is_party=True, next_level=2000),
        'N': dict(cls='Cleric', prime='WIS', score='12', bonus=False,
                  treasure_weight=0.5, is_party=False, next_level=1500),
    }
    # monster: 1 + 1 = 2 shares, 60/2 = 30 each.
    tot, _ = xpmod.totals(chars=chars,
                          log=[dict(kind='monster', xp='60',
                                    earned_by='all,N', notes='')])
    assert tot['A'] == 30 and tot['N'] == 30, 'monster xp must not halve'

    # treasure: 1 + 0.5 = 1.5 shares, 60/1.5 = 40 full and 20 half.
    tot, _ = xpmod.totals(chars=chars,
                          log=[dict(kind='treasure', xp='60',
                                    earned_by='all,N', notes='')])
    assert tot['A'] == 40 and tot['N'] == 20, 'treasure xp must stay halved'


# ------------------------------------------- 0-level humans, added day 99
# Brand stood in the marching order for a full day of play with no stat line at
# all. The first time the player said "everyone with missile weapons",
# combat.py raised ValueError: no to-hit column for class 'Normal Man'.

def test_a_normal_man_hits_off_the_zero_level_column():
    """PHB p.105: normal men are always level 0. DMG p.74 matrix I.B column 0."""
    for ac, want in ((2, 19), (5, 16), (6, 15), (10, 11)):
        base, src = combat.target_number('Normal Man', ac)
        assert base == want, (ac, base, want)
        assert 'DMG' in src


def test_the_zero_level_column_is_not_a_second_copy_in_combat_md():
    """No rules table is written twice -- it is READ from zero-level.md.

    If someone ever pastes a 0-level column into combat.md's character matrix,
    there are two numbers to keep in step and one of them will rot.
    """
    t = rules.find('To hit — 0-level HUMANS use the CHARACTER matrix, column 0')
    assert '0 level' in t['columns']
    chars = rules.find('To-hit, characters')
    assert '0 level' not in chars['columns']
    assert '0' not in chars['columns']


def test_a_normal_man_is_not_given_a_fighters_table():
    """A 0-level man is a full point worse than a 1st-level fighter."""
    for ac in (2, 5, 6, 10):
        assert (combat.target_number('Normal Man', ac)[0]
                == combat.target_number('Fighter', ac)[0] + 1)


def test_a_normal_man_takes_the_fighters_non_proficiency_penalty():
    """He has no class and so no slots; stated rather than left to crash."""
    assert (combat.proficiency_penalty('Normal Man')
            == combat.proficiency_penalty('Fighter'))


def test_hand_axe_resolves_by_the_name_the_party_uses():
    """Day 119: Brand's thrown hand axe raised KeyError after the d20 was rolled
    and logged, because the PHB table prints 'Axe, hand or throwing'."""
    import combat
    spec = combat.weapon_damage('hand axe')
    assert spec == combat.weapon_damage('Axe, hand or throwing')
