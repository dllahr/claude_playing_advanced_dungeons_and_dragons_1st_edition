#!/usr/bin/env python3
"""Roll AD&D 1e treasure types, so the Monster Manual appendix is read once.

    python tools/treasure.py K --individuals 2      # 2 berserkers
    python tools/treasure.py B                      # a lair hoard
    python tools/treasure.py --monster berserker --individuals 2
    python tools/treasure.py --list

Transcribed from the MONSTER MANUAL appendix, TREASURE TYPES, from a page
render rather than the OCR text layer -- the digits in these scans corrupt
silently and this table is nothing but digits.

Two things the table's layout hides and which are easy to get wrong:

  * The coin columns are **1,000's** of copper, silver, electrum and gold, and
    **100's** of platinum. A type A hoard rolling "1-6 :25%" for copper means
    1,000-6,000 copper pieces, on a 25% chance.
  * Types **J through N are per individual and are literal pieces** -- no
    multiplier. Type K is "3-18 pieces per individual", i.e. 3d6 silver each,
    with no percentage chance attached. These are what a wandering band is
    carrying; the lair types are what is back home.
"""
import argparse
import os
import random
import re
import sys

# (low, high, percent-chance) per column, or None. Chance None = always.
# columns: cp, sp, ep, gp, pp, gems, jewelry ; magic is free text.
LAIR = {
    'A': ((1, 6, 25), (1, 6, 30), (1, 6, 35), (1, 10, 40), (1, 4, 25),
          (4, 40, 60), (3, 30, 50), 'Any 3: 30%'),
    'B': ((1, 8, 50), (1, 6, 25), (1, 4, 25), (1, 3, 25), None,
          (1, 8, 30), (1, 4, 20), 'Sword, armor, or misc. weapon: 10%'),
    'C': ((1, 12, 20), (1, 6, 30), (1, 4, 10), None, None,
          (1, 6, 25), (1, 3, 20), 'Any 2: 10%'),
    'D': ((1, 8, 10), (1, 12, 15), (1, 8, 15), (1, 6, 50), None,
          (1, 10, 30), (1, 6, 25), 'Any 2 plus 1 potion: 15%'),
    'E': ((1, 10, 5), (1, 12, 25), (1, 6, 25), (1, 8, 25), None,
          (1, 12, 15), (1, 8, 10), 'Any 3 plus 1 scroll: 25%'),
    'F': (None, (1, 20, 10), (1, 12, 15), (1, 10, 40), (1, 8, 35),
          (3, 30, 20), (1, 10, 10),
          'Any 3 except swords or misc. weapons, plus 1 potion & 1 scroll: 30%'),
    'G': (None, None, None, (10, 40, 50), (1, 20, 50),
          (5, 20, 30), (1, 10, 25), 'Any 4 plus 1 scroll: 35%'),
    'H': ((5, 30, 25), (1, 100, 40), (10, 40, 40), (10, 60, 55), (5, 50, 25),
          (1, 100, 50), (10, 40, 50), 'Any 4 plus 1 potion & 1 scroll: 15%'),
    'I': (None, None, None, None, (3, 18, 30),
          (2, 20, 55), (1, 12, 50), 'Any 1: 15%'),
    'O': ((1, 4, 25), (1, 3, 20), None, None, None, None, None, None),
    'P': (None, (1, 6, 30), (1, 2, 25), None, None, None, None, None),
    'Q': (None, None, None, None, None, (1, 4, 50), None, None),
    'R': (None, None, None, (2, 8, 40), (10, 60, 50),
          (4, 32, 55), (1, 12, 45), None),
    'S': (None,) * 7 + ('2-8 potions: 40%',),
    'T': (None,) * 7 + ('1-4 scrolls: 50%',),
    'U': (None, None, None, None, None, (10, 80, 90), (5, 30, 80),
          '1 of each magic excluding potions & scrolls: 70%'),
    'V': (None,) * 7 + ('2 of each magic excluding potions & scrolls: 85%',),
    'W': (None, None, None, (5, 30, 60), (1, 8, 15),
          (10, 80, 60), (5, 40, 50), '1 map: 55%'),
    'X': (None,) * 7 + ('1 misc. magic plus 1 potion: 60%',),
    'Y': (None, None, None, (2, 12, 70), None, None, None, None),
    'Z': ((1, 3, 20), (1, 4, 25), (1, 4, 25), (1, 4, 30), (1, 6, 30),
          (10, 60, 55), (5, 30, 50), 'Any 3 magic: 50%'),
}

# J-N: literal pieces per individual, no percentage.
INDIVIDUAL = {
    'J': ('cp', 3, 24),
    'K': ('sp', 3, 18),
    'L': ('ep', 2, 12),
    'M': ('gp', 2, 8),
    'N': ('pp', 1, 6),
}

COLS = ('cp', 'sp', 'ep', 'gp', 'pp', 'gems', 'jewelry')
MULT = {'cp': 1000, 'sp': 1000, 'ep': 1000, 'gp': 1000, 'pp': 100,
        'gems': 1, 'jewelry': 1}

# Treasure types come from bestiary/, which reads them off the Monster Manual
# page renders. They are NOT restated here: this table used to be a hand-typed
# second copy and it was wrong for two of the six creatures in it -- orc lair
# "D" (the MM says C, O, Q x10, S) and kobold lair "Q, D" (the MM says O, Q x5).
# Both errors survived because nothing ever compared them to the book.
_INDIVIDUAL_RE = re.compile(r'([A-Z])\s*(?:individually|individuals?)', re.I)
_LAIR_RE = re.compile(r'in lair', re.I)


def monster_types(name):
    """(individual letter or None, lair letters, the raw text) from bestiary/."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bestiary
    raw = bestiary.field(name, 'Treasure Type')
    ind, _, lair = raw.partition(';')
    if not lair:
        # "A" or "C" alone means a lair type with nothing carried individually.
        if _INDIVIDUAL_RE.search(ind):
            return _INDIVIDUAL_RE.search(ind).group(1).upper(), '', raw
        return None, ind.strip(), raw
    m = _INDIVIDUAL_RE.search(ind)
    return (m.group(1).upper() if m else None), lair.strip(), raw


def known_monsters():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bestiary
    return sorted(bestiary.creatures())


def dice(lo, hi):
    """Roll the 1e range notation: `lo` dice of `hi // lo` sides.

    3-18 is 3d6, 10-40 is 10d4, 1-100 is 1d100. Rolling uniformly across the
    range instead would give the wrong distribution -- 3d6 is not flat.
    """
    n = lo
    sides = hi // lo if lo else hi
    return sum(random.randint(1, sides) for _ in range(n)) if n else 0


def roll_individual(letter, n=1):
    """Coins carried by `n` members of a band. Types J-N only."""
    spec = INDIVIDUAL.get(letter.upper())
    if not spec:
        return {}, ['type %s is not an individual type' % letter]
    coin, lo, hi = spec
    per = [dice(lo, hi) for _ in range(n)]
    return {coin: sum(per)}, ['%s each: %s' % (coin, ', '.join(map(str, per)))]


def roll_lair(letter):
    """A hoard. Coin columns are thousands, platinum hundreds."""
    row = LAIR.get(letter.upper())
    if not row:
        return {}, ['type %s is not a lair type' % letter]
    out, notes = {}, []
    for col, spec in zip(COLS, row[:7]):
        if not spec:
            continue
        lo, hi, chance = spec
        r = random.randint(1, 100)
        if r > chance:
            notes.append('%-8s no (%d vs %d%%)' % (col, r, chance))
            continue
        amount = dice(lo, hi) * MULT[col]
        out[col] = out.get(col, 0) + amount
        notes.append('%-8s YES (%d vs %d%%) -> %d' % (col, r, chance, amount))
    magic = row[7]
    if magic:
        notes.append('magic:   %s  -- roll separately on the DMG tables' % magic)
    return out, notes


def build_parser():
    p = argparse.ArgumentParser(
        prog='treasure.py',
        description='Roll AD&D 1e treasure types (Monster Manual appendix).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('type', nargs='?', help='treasure type letter, A-Z')
    p.add_argument('--individuals', type=int, default=0,
                   help='number of creatures carrying an individual type (J-N)')
    p.add_argument('--monster', help='look the type up by creature name')
    p.add_argument('--lair', action='store_true',
                   help='with --monster, roll the lair hoard instead')
    p.add_argument('--list', action='store_true', help='list known monsters')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.list:
        for k in known_monsters():
            ind, lair, raw = monster_types(k)
            print('%-12s individual %-4s lair %-18s  MM: %r'
                  % (k, ind or '-', lair or '-', raw))
        return 0

    letter, n = a.type, a.individuals
    if a.monster:
        try:
            ind, lair, raw = monster_types(a.monster)
        except KeyError as e:
            print('%s' % e)
            return 1
        print('%s: MM treasure type %r' % (a.monster, raw))
        if a.lair:
            # A lair may list several types; roll each.
            letters = re.findall(r'\b([A-Z])\b', lair)
            if not letters:
                print('  no lair treasure')
                return 0
            if len(letters) > 1:
                print('  lair lists %d types: %s -- rolling each'
                      % (len(letters), ', '.join(letters)))
                for L in letters:
                    got, notes = roll_lair(L)
                    print('  --- type %s ---' % L)
                    for line in notes:
                        print('    ' + line)
                    print('    TOTAL: %s'
                          % (', '.join('%d %s' % (v, k) for k, v in got.items())
                             or 'nothing'))
                return 0
            letter = letters[0]
        else:
            letter = ind
        if not letter:
            print('  no %s treasure' % ('lair' if a.lair else 'individual'))
            return 0
    if not letter:
        build_parser().print_help()
        return 1

    if letter.upper() in INDIVIDUAL and not a.lair:
        got, notes = roll_individual(letter, max(1, n))
    else:
        got, notes = roll_lair(letter)
    print('treasure type %s%s' % (letter.upper(),
                                  ' x%d individuals' % n if n else ''))
    for line in notes:
        print('  ' + line)
    print('  ---')
    print('  TOTAL: %s' % (', '.join('%d %s' % (v, k) for k, v in got.items())
                           or 'nothing'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
