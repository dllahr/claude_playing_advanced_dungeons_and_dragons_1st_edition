#!/usr/bin/env python3
"""Resolve AD&D 1e combat, in the open, from the verified rules cache.

    # a whole round of the party's attacks in one call
    python tools/combat.py round --target "berserker AC 7 HD 1" \
        --attack Dave:"long sword" Torsat:"long sword" Yrtone:"footman's flail"

    # one monster swinging back
    python tools/combat.py monster --hd 1 --target-ac 3 --damage 1-8 \
        --name berserker --attacks 2

    python tools/combat.py initiative
    python tools/combat.py surprise --who "Tristle scouting" --adjust 3
    python tools/combat.py save --who Frython --vs Spell
    python tools/combat.py morale --hd 3+2 --modifier 15 --why "half the band down"

Every table this reads comes from `rules/*.md` through `tools/rules.py`; none is
restated here. That is the point -- the number the dice are compared against and
the "DMG p. 75" citation beside it are the same object, so a rule cannot drift
out of agreement with its source.

WHAT THIS DOES NOT DECIDE
-------------------------
It does not choose targets, apply hit points to monsters, or narrate. Monster
hit points stay with the DM, because the campaign rule is to describe wounds
and never state them. It resolves dice and modifiers, prints its working, and
stops.

The three mistakes this exists to make impossible, all of which happened:
  * using a character's to-hit table for a monster (a 1 HD monster needs 16 to
    hit AC 3, not 17)
  * forgetting the non-proficiency penalty (a thief is -3, not -2 or -4)
  * applying a Strength damage bonus to bow fire, where it does not belong
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules                                                    # noqa: E402
from dice import roll, range_roll                               # noqa: E402
from hp import characters, current as current_hp                # noqa: E402
import bestiary                                                 # noqa: E402

# Weapons whose damage comes from the weapon, not the arm. The Strength hit and
# damage adjustments are melee-and-hurled; a bow stores its own energy. Darts
# and thrown spears ARE hurled and do take the bonus. See rules/abilities.md.
NO_STRENGTH = ('bow', 'crossbow', 'sling', 'quarrel', 'bolt', 'arrow')
# Weapons that use the Dexterity Reaction/Attacking adjustment instead.
MISSILE = NO_STRENGTH + ('dart', 'javelin')

CLASS_COLUMN = {'fighter': 'Fighter', 'cleric': 'Cleric', 'thief': 'Thief',
                'magic-user': 'Magic-User', 'magic user': 'Magic-User',
                'druid': 'Cleric', 'paladin': 'Fighter', 'ranger': 'Fighter',
                'assassin': 'Thief', 'monk': 'Cleric', 'illusionist': 'Magic-User'}

# Monster hit-dice bands, in the order they appear across the DMG p.75 matrix.
HD_BANDS = ('up to 1-1', '1-1', '1', '1+', '2-3+', '4-5+', '6-7+', '8-9+',
            '10-11+', '12-13+', '14-15+', '16+')


# ------------------------------------------------------------------ lookups

def _to_hit_tables():
    return rules.find('To-hit, characters'), rules.find('To-hit, monsters')


def is_missile(weapon):
    w = weapon.lower()
    return any(k in w for k in MISSILE)


def takes_strength(weapon):
    w = weapon.lower()
    return not any(k in w for k in NO_STRENGTH)


def hd_band(hd):
    """Which DMG p.75 column a monster's hit dice fall in.

    `hd` may be "1", "1+1", "3+4", "2-1", or a number. The DMG's own note:
    "Any plus above +3 equals another hit die, i.e. 6+6 equals 7 hit dice", so
    a 3+4 creature is read as 4 HD before the band is chosen.
    """
    s = str(hd).strip()

    # FRACTIONAL hit dice. The MM gives kobolds and giant rats 1/2 and giant
    # centipedes 1/4, and the bestiary files spell the same thing the module's
    # way -- "1-4 hit points", "1-2 hit points". None of it parsed, so every
    # attack by the three commonest wandering monsters on this level raised
    # instead of rolling. They all sit in the DMG's lowest column.
    frac = s.lower().replace(' ', '')
    if (re.match(r'^\d+/\d+$', frac) or frac in ('half', '\u00bd', '\u00bc')
            or re.match(r'^\d+-\d+hitpoints?$', frac)):
        return 'up to 1-1'

    m = re.match(r'^(\d+)\s*(?:([+-])\s*(\d+))?$', s)
    if not m:
        raise ValueError('cannot read hit dice %r' % hd)
    base = int(m.group(1))
    sign, plus = m.group(2), int(m.group(3) or 0)
    if sign == '-':
        return 'up to 1-1' if base <= 1 else HD_BANDS[HD_BANDS.index('1')]
    if plus > 3:                      # +4 or more is another whole hit die
        base += plus // 4
        plus = plus % 4
    if base <= 0:
        return 'up to 1-1'
    if base == 1:
        return '1+' if plus else '1'
    if base <= 3:
        return '2-3+'
    if base <= 5:
        return '4-5+'
    if base <= 7:
        return '6-7+'
    if base <= 9:
        return '8-9+'
    if base <= 11:
        return '10-11+'
    if base <= 13:
        return '12-13+'
    if base <= 15:
        return '14-15+'
    return '16+'


def proficiency_penalty(cls):
    t = rules.find('Weapon proficiency')
    d = rules.as_dict(t)
    key = cls.title().replace('Magic-User', 'Magic-User')
    for k in d:
        if k.lower() == cls.lower():
            key = k
            break
    return int(d[key]['Non-proficiency penalty'])


# ------------------------------------------------------------------- attack

class Modifier(object):
    """A single term in the to-hit stack, carrying where it came from."""

    def __init__(self, value, why, source):
        self.value, self.why, self.source = value, why, source

    def __str__(self):
        return '%+d  %-28s %s' % (self.value, self.why, self.source)


def attack_modifiers(char, weapon, ranged=None, extra=()):
    """Every to-hit modifier for one character with one weapon, with sources."""
    mods = []
    ranged = is_missile(weapon) if ranged is None else ranged
    if ranged:
        n = int(char.get('missile_hit') or 0)
        if n:
            mods.append(Modifier(n, 'DEX missile adjustment',
                                 'PHB p.11, DEXTERITY TABLE I'))
    else:
        n = int(char.get('melee_hit') or 0)
        if n:
            mods.append(Modifier(n, 'STR hit adjustment',
                                 'PHB Strength Table II'))
    prof = [w.strip().lower() for w in (char.get('proficient') or '').split(',')
            if w.strip() and w.strip() != '-']
    if weapon.lower() not in prof:
        pen = proficiency_penalty(char.get('class', ''))
        mods.append(Modifier(pen, 'NON-PROFICIENT',
                             'PHB p.37, %s' % char.get('class', '')))
    bonus = [w.strip().lower() for w in (char.get('bonus_weapons') or '').split(',')
             if w.strip() and w.strip() != '-']
    if weapon.lower() in bonus:
        mods.append(Modifier(1, 'racial weapon bonus', 'PHB race description'))
    for value, why, source in extra:
        mods.append(Modifier(value, why, source))
    return mods


def target_number(cls, ac):
    t, _ = _to_hit_tables()
    col = CLASS_COLUMN.get(cls.lower())
    if not col:
        raise ValueError('no to-hit column for class %r' % cls)
    return int(rules.lookup(t, str(ac), col)), t['source']


def monster_target_number(hd, ac):
    _, t = _to_hit_tables()
    band = hd_band(hd)
    return int(rules.lookup(t, str(ac), band)), band, t['source']


def resolve_attack(name, char, weapon, ac, extra=(), size='S/M', rng=None):
    """One swing. Returns (lines, hit, damage)."""
    import random as _r
    rng = rng or _r
    lines = []
    cls = char.get('class', '')
    base, src = target_number(cls, ac)
    mods = attack_modifiers(char, weapon, extra=extra)
    total_mod = sum(m.value for m in mods)
    need = base - total_mod
    d = roll('d20', reason='%s attacks with %s' % (name, weapon), rng=rng)
    nat = d.dice[0]
    lines.append('%s -- %s vs AC %s' % (name, weapon, ac))
    lines.append('    d20 = %d' % nat)
    lines.append('    %d  base to hit, %s %s' % (base, cls, 'level 1'))
    for m in mods:
        lines.append('    ' + str(m))
    lines.append('    needs %d%s' % (need, '' if not mods else
                                     '  (%d %+d)' % (base, total_mod)))
    # A natural 20 always hits and a natural 1 always misses; the matrices run
    # past 20 for deep armour classes precisely so that high AC still needs the
    # DM's ruling rather than an automatic hit, but 1e treats the extremes as
    # absolute in play and this campaign has done so throughout.
    if nat == 20:
        hit, why = True, ' -- NATURAL 20'
    elif nat == 1:
        hit, why = False, ' -- NATURAL 1'
    else:
        hit, why = nat >= need, ''
    lines.append('    rolled %d vs %d -> %s%s'
                 % (nat, need, 'HIT' if hit else 'MISS', why))
    dmg = 0
    if hit:
        spec = weapon_damage(weapon, size)
        dr = range_roll(spec, reason='%s damage, %s' % (name, weapon), rng=rng)
        dmg = dr.total
        line = '    damage %s' % dr
        if takes_strength(weapon):
            b = int(char.get('melee_dmg') or 0)
            if b:
                dmg += b
                line += '  %+d STR (PHB Strength Table II) = %d' % (b, dmg)
        else:
            b = int(char.get('melee_dmg') or 0)
            if b:
                line += ('  (STR damage bonus %+d does NOT apply to %s -- '
                         'rules/abilities.md)' % (b, weapon))
        lines.append(line)
    return lines, hit, dmg


# A launcher does no damage; its AMMUNITION does. The PHB damage table lists
# "Arrow" and "Sling bullet", never "short bow" or "sling", so firing one raised
# a KeyError mid-volley. Proficiency and the to-hit modifiers still key off the
# LAUNCHER -- a character is proficient in the bow, not in arrows.
AMMUNITION = {
    'short bow': 'Arrow', 'long bow': 'Arrow', 'composite bow': 'Arrow',
    'bow': 'Arrow',
    'sling': 'Sling bullet', 'sling stone': 'Sling stone',
    'sling bullet': 'Sling bullet',
    'light crossbow': 'Quarrel (bolt), light',
    'heavy crossbow': 'Quarrel (bolt), heavy',
}


def weapon_damage(weapon, size='S/M'):
    """The damage range for a weapon against a target size, from PHB p.37.

    Launchers resolve as their ammunition -- see AMMUNITION above.
    """
    t = rules.find('Weapon damage')
    d = rules.as_dict(t)
    ammo = AMMUNITION.get(weapon.strip().lower())
    if ammo:
        for k in d:
            if k.lower() == ammo.lower():
                col = 'vs L' if str(size).upper().startswith('L') else 'vs S or M'
                return d[k][col]
    col = 'vs L' if str(size).upper().startswith('L') else 'vs S or M'
    w = weapon.strip().lower()
    for k in d:
        if k.lower() == w:
            return d[k][col]
    # "long sword" is printed "Sword, long"; try the inverted form.
    parts = [p.strip() for p in w.split()]
    if len(parts) == 2:
        for k in d:
            if k.lower() == '%s, %s' % (parts[1], parts[0]):
                return d[k][col]
    raise KeyError('no weapon %r in the PHB damage table; known: %s'
                   % (weapon, ', '.join(sorted(d))[:400]))


# ------------------------------------------------------ monsters attacking

def monster_attack(name, hd, target_ac, damage, extra=(), rng=None):
    import random as _r
    rng = rng or _r
    need, band, src = monster_target_number(hd, target_ac)
    total_mod = sum(v for v, _, _ in extra)
    need -= total_mod
    d = roll('d20', reason='%s attacks AC %s' % (name, target_ac), rng=rng)
    nat = d.dice[0]
    lines = ['%s (%s HD, column %r) vs AC %s' % (name, hd, band, target_ac),
             '    d20 = %d' % nat,
             '    needs %d   %s' % (need, src or 'DMG p.75')]
    for v, why, source in extra:
        lines.append('    %+d  %-28s %s' % (v, why, source))
    hit = nat == 20 or (nat != 1 and nat >= need)
    lines.append('    rolled %d vs %d -> %s' % (nat, need, 'HIT' if hit else 'MISS'))
    dmg = 0
    if hit:
        # SOME ATTACKS DO NO HIT POINT DAMAGE AT ALL, and the bestiary says so
        # in the Monster Manual's own word: "Nil". A giant centipede is the
        # example -- `bestiary/giant-centipede.md`: "It bites, and the bite
        # carries poison... Never roll damage for a centipede bite. There is
        # none to roll." Rot grubs, some oozes and several paralysers are the
        # same shape of thing.
        #
        # Passing that straight to the dice parser raised
        # `cannot read dice notation 'Nil'` in the middle of a live encounter,
        # with two centipedes already on the table. The attack still HITS and
        # the special attack still applies -- the damage is what is absent.
        if str(damage).strip().lower() in ('nil', 'none', '-', '', '0'):
            lines.append('    damage NIL -- the hit lands and does no hit point '
                         'damage. Resolve the special attack (save, poison, '
                         'paralysis) from the bestiary entry.')
            return lines, hit, 0
        dr = range_roll(damage, reason='%s damage' % name, rng=rng)
        dmg = dr.total
        lines.append('    damage %s' % dr)
    return lines, hit, dmg


# --------------------------------------------- initiative, surprise, saves

def initiative(sides=6, names=('party', 'monsters'), rng=None):
    import random as _r
    rng = rng or _r
    out, scores = [], {}
    for n in names:
        r = roll('d%d' % sides, reason='initiative, %s' % n, rng=rng)
        scores[n] = r.total
        out.append('    %-10s d%d = %d' % (n, sides, r.total))
    best = max(scores.values())
    winners = [n for n, v in scores.items() if v == best]
    out.insert(0, 'initiative (d%d per side, HIGH wins)' % sides)
    if len(winners) > 1:
        out.append('    TIED at %d -- blows are simultaneous this round' % best)
    else:
        out.append('    %s act first' % winners[0])
    return out, scores


def surprise(sides=6, surprised_on=2, who='party', adjust=0, rng=None,
             why=''):
    """d6 per side; a roll of `surprised_on` or less is surprised.

    THE RANGE IS NOT ALWAYS 1-2. Several creatures widen it, and the default
    silently produced a wrong answer once already: troglodyte chameleon skin
    surprises on 1-4 (MM), a 3 was rolled and announced as "party alert", and
    the encounter had to be corrected mid-fight. Pass `--surprised-on 4` and
    say why; the reason is printed so the ruling is auditable.

    The Dexterity Reaction/Attacking adjustment applies to surprise as well as
    missiles -- the PHB says so in as many words -- so a high-DEX scout shifts
    the roll. `adjust` is added to the die.
    """
    import random as _r
    rng = rng or _r
    r = roll('d%d' % sides, reason='surprise check, %s' % who, rng=rng)
    val = r.total + adjust
    surprised = val <= surprised_on
    out = ['surprise, %s' % who,
           '    d%d = %d%s' % (sides, r.total,
                               '  %+d = %d' % (adjust, val) if adjust else ''),
           '    1-%d is surprised%s' % (surprised_on,
                                        '   (%s)' % why if why else ''),
           '    -> %s' % ('SURPRISED' if surprised else 'not surprised')]
    return out, surprised


SAVE_BANDS = {'Cleric': '1-3', 'Fighter': '1-2', 'Magic-User': '1-5',
              'Thief': '1-4'}


def saving_throw(name, char, category, adjust=0, why='', rng=None):
    import random as _r
    rng = rng or _r
    t = rules.find('Saving throws')
    cls = CLASS_COLUMN.get(char.get('class', '').lower(), char.get('class'))
    band = SAVE_BANDS.get(cls)
    row = None
    for r in t['rows']:
        if r[0] == cls and r[1] == band:
            row = dict(zip(t['columns'], r))
            break
    if row is None:
        raise KeyError('no saving throw row for %s %s' % (cls, band))
    col = None
    for c in t['columns'][2:]:
        if category.lower() in c.lower():
            col = c
            break
    if col is None:
        raise KeyError('no save category matching %r; columns: %s'
                       % (category, ', '.join(t['columns'][2:])))
    need = int(row[col])
    d = roll('d20', reason='%s save vs %s' % (name, col), rng=rng)
    nat = d.dice[0]
    lines = ['%s (%s %s) save vs %s' % (name, cls, band, col),
             '    d20 = %d' % nat,
             '    needs %d   %s' % (need, t['source'] or 'DMG p.79')]
    if adjust:
        lines.append('    %+d  %s' % (adjust, why or 'adjustment'))
    # The DMG is explicit: a roll of 1 is always a failure, whatever the bonus.
    made = nat != 1 and (nat + adjust) >= need
    lines.append('    rolled %d%s vs %d -> %s%s'
                 % (nat, ' %+d' % adjust if adjust else '', need,
                    'SAVED' if made else 'FAILED',
                    '  -- natural 1 always fails (DMG p.79)' if nat == 1 else ''))
    return lines, made


# ------------------------------------------------------------------ morale

def morale(hd=1, modifier=0, why='', rng=None):
    """DMG percentage morale, not Basic's 2d6.

    DMG p.67: "Each monster has a base morale of 50%, +5%/hit die above 1,
    +1%/hit point above any hit dice."

    The last clause means the PLUS in the hit-dice expression -- the "+2" of a
    3+2 HD creature -- not the hit points it happened to roll. Taking it as
    rolled hp would make a lucky goblin braver than a hobgoblin, and it is the
    reading this tool used until the DMG page was read.

    Roll d100 and add the situational modifier to the ROLL; exceeding the score
    is a failure, and the MARGIN of failure says what the creature does.
    """
    import random as _r
    rng = rng or _r
    m = re.match(r'^\s*(\d+)\s*(?:\+\s*(\d+))?', str(hd))
    base_hd = int(m.group(1)) if m else 1
    plus = int(m.group(2) or 0) if m else 0
    score = 50 + 5 * max(0, base_hd - 1) + plus
    lines = ['morale check   (DMG p.67, percentage system)',
             '    50%  base',
             '    %+d%%  %d hit dice' % (5 * max(0, base_hd - 1), base_hd)]
    if plus:
        lines.append('    %+d%%  the "+%d" hit points above its hit dice'
                     % (plus, plus))
    lines.append('    score %d%%' % score)
    r = roll('d100', reason='morale', rng=rng)
    adj = r.total + modifier
    if modifier:
        lines.append('    %+d%%  %s' % (modifier, why or 'situation'))
    lines.append('    d100 = %d%s' % (r.total,
                                      '  %+d = %d' % (modifier, adj) if modifier else ''))
    if adj <= score:
        lines.append('    %d vs %d -> MORALE HOLDS' % (adj, score))
        return lines, True, None
    margin = adj - score
    # The result band table is the SECOND table under the Morale heading, which
    # rules.py keys with a "(2)" suffix rather than silently overwriting the
    # first. The first is the trigger/modifier table.
    result = None
    for r2 in rules.find('Morale (DMG, verified) (2)')['rows']:
        lo, _, hi = r2[0].partition('-')
        lo = int(re.sub(r'\D', '', lo) or 0)
        hi = int(re.sub(r'\D', '', hi) or 999) if hi.strip() else 999
        if lo <= margin <= hi:
            result = r2[1]
            break
    lines.append('    %d vs %d -> MORALE BREAKS by %d%%: %s'
                 % (adj, score, margin, result or '(margin off the table)'))
    return lines, False, result


# --------------------------------------------------------------------- CLI

def parse_attack(spec):
    """"Dave:long sword" or "Dave:long sword:+2:rear attack, DMG p.70".

    The optional modifier and its reason exist so a one-off circumstance does
    not have to be hand-rolled outside the tool -- which is where the arithmetic
    errors come from. The reason is printed beside the number like every other
    modifier, so an ad-hoc ruling is as auditable as a table lookup.
    """
    parts = spec.split(':')
    who = parts[0].strip()
    weapon = parts[1].strip() if len(parts) > 1 else ''
    extra = ()
    if len(parts) > 2 and parts[2].strip():
        why = parts[3].strip() if len(parts) > 3 else 'situational'
        extra = ((int(parts[2].strip()), why, 'DM ruling this round'),)
    return who, weapon, extra


def parse_target(spec):
    """"berserker AC 7 HD 1" -> (name, ac, hd, size)."""
    ac = re.search(r'\bAC\s*(-?\d+)', spec, re.I)
    hd = re.search(r'\bHD\s*([\d+\-]+)', spec, re.I)
    size = 'L' if re.search(r'\bsize\s*L\b|\blarge\b', spec, re.I) else 'S/M'
    name = re.split(r'\bAC\b|\bHD\b', spec, flags=re.I)[0].strip() or 'target'
    if not ac:
        raise ValueError('target %r does not state an AC' % spec)
    return name, int(ac.group(1)), hd.group(1) if hd else '1', size


def build_parser():
    p = argparse.ArgumentParser(
        prog='combat.py',
        description='Resolve AD&D 1e combat from the verified rules cache.',
        epilog='Every table comes from rules/*.md via tools/rules.py; none is '
               'restated in code.')
    sub = p.add_subparsers(dest='cmd', required=True)

    r = sub.add_parser('round', help="resolve a round of the party's attacks")
    r.add_argument('--target', required=True,
                   help='e.g. "berserker AC 7 HD 1" (size L if larger than man-sized)')
    r.add_argument('--attack', nargs='+', required=True, metavar='WHO:WEAPON',
                   help='e.g. Dave:"long sword" Frython:dart. Add a one-off '
                        'modifier and its reason with two more colons: '
                        'Dave:"long sword":+2:"rear attack, DMG p.70"')
    r.add_argument('--initiative', action='store_true',
                   help='roll initiative for the round first')

    m = sub.add_parser('monster', help='a monster attacking a character')
    m.add_argument('--creature',
                   help='look hit dice and damage up in bestiary/ instead of '
                        'retyping them, e.g. --creature troglodyte')
    m.add_argument('--attack-index', type=int, default=1,
                   help='with --creature, which of its damage entries to use '
                        '(1-3/1-3/2-5 -> 1, 2 or 3)')
    m.add_argument('--name', default='monster')
    m.add_argument('--hd', default='1', help='hit dice, e.g. 1, 1+1, 3+4')
    m.add_argument('--target-ac', type=int, required=True)
    m.add_argument('--damage', default='1-8', help='1e range, e.g. 1-8, 2-7')
    m.add_argument('--attacks', type=int, default=1, help='attacks this round')

    i = sub.add_parser('initiative', help='d6 per side, high wins')
    i.add_argument('--sides', type=int, default=6)

    s = sub.add_parser('surprise', help='d6 per side, 1-2 surprised by default')
    s.add_argument('--who', default='party')
    s.add_argument('--surprised-on', type=int, default=2,
                   help='surprised on this or less. NOT always 2: troglodyte '
                        'chameleon skin makes it 4 (MM), and taking the default '
                        'got an encounter wrong once')
    s.add_argument('--why', default='', help='what widens or narrows the range')
    s.add_argument('--adjust', type=int, default=0,
                   help='DEX Reaction/Attacking adjustment, PHB p.11')

    sv = sub.add_parser('save', help='a saving throw')
    sv.add_argument('--who', required=True)
    sv.add_argument('--vs', required=True,
                    help='Paralyze / Petrify / Rod / Breath / Spell')
    sv.add_argument('--adjust', type=int, default=0)
    sv.add_argument('--why', default='')

    mo = sub.add_parser('morale', help='DMG percentage morale check')
    mo.add_argument('--hd', default='1',
                    help='hit dice as printed, e.g. 1, 3+2 -- the "+n" adds to '
                         'the morale score (DMG p.67)')
    mo.add_argument('--modifier', type=int, default=0,
                    help='from the trigger table in rules/combat.md')
    mo.add_argument('--why', default='')

    w = sub.add_parser('damage', help='look up a weapon damage range')
    w.add_argument('weapon')
    w.add_argument('--size', default='S/M')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    chars = characters()

    if a.cmd == 'round':
        name, ac, hd, size = parse_target(a.target)
        out, total = [], 0
        if a.initiative:
            lines, _ = initiative()
            out += lines + ['']
        hp = current_hp(chars)
        for spec in a.attack:
            who, weapon, extra = parse_attack(spec)
            if who not in chars:
                out.append('%s: no such character' % who)
                continue
            if hp[who][0] <= 0:
                out.append('%s is at %d hp and cannot attack (DMG p.82)'
                           % (who, hp[who][0]))
                continue
            lines, hit, dmg = resolve_attack(who, chars[who], weapon, ac,
                                             extra=extra, size=size)
            out += lines + ['']
            total += dmg
        out.append('total damage to %s this round: %d' % (name, total))
        out.append('(monster hit points stay with the DM -- describe wounds)')
        print('\n'.join(out))
        return 0

    if a.cmd == 'monster':
        if a.creature:
            # The stat block is data now, not three arguments retyped from a
            # page render every time the same creature turns up.
            d, src = bestiary.stats(a.creature)
            a.hd = d['Hit Dice']['Value']
            if a.name == 'monster':
                a.name = a.creature
            dmg = [x.strip() for x in
                   d['Damage']['Value'].split('or')[0].split('/')]
            a.damage = dmg[min(a.attack_index, len(dmg)) - 1]
            print('%s: AC %s, HD %s, damage %s   %s'
                  % (a.creature, d['Armor Class']['Value'], a.hd,
                     d['Damage']['Value'], src or ''))
            print()
        total = 0
        for i in range(max(1, a.attacks)):
            lines, hit, dmg = monster_attack(
                '%s attack %d' % (a.name, i + 1) if a.attacks > 1 else a.name,
                a.hd, a.target_ac, a.damage)
            print('\n'.join(lines))
            print()
            total += dmg
        print('total damage: %d' % total)
        return 0

    if a.cmd == 'initiative':
        lines, _ = initiative(a.sides)
        print('\n'.join(lines))
        return 0

    if a.cmd == 'surprise':
        lines, _ = surprise(who=a.who, adjust=a.adjust,
                            surprised_on=a.surprised_on, why=a.why)
        print('\n'.join(lines))
        return 0

    if a.cmd == 'save':
        if a.who not in chars:
            print('no character %r' % a.who)
            return 1
        lines, _ = saving_throw(a.who, chars[a.who], a.vs, a.adjust, a.why)
        print('\n'.join(lines))
        return 0

    if a.cmd == 'morale':
        lines, _, _ = morale(a.hd, a.modifier, a.why)
        print('\n'.join(lines))
        return 0

    if a.cmd == 'damage':
        print('%s vs %s: %s' % (a.weapon, a.size, weapon_damage(a.weapon, a.size)))
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
