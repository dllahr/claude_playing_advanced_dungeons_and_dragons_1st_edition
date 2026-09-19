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
# A letter, optionally a "J-N" range, optionally a "(x5)" multiplier. The
# multiplier is consumed as part of the letter's match so that the capital X the
# MM prints in "Q ( X 5)" is never mistaken for treasure type X.
_TYPE_RE = re.compile(
    r'\b([A-Z])\b(?:\s*-\s*\b([A-Z])\b)?(?:\s*\(\s*[xX]\s*(\d+)\s*\))?')


def parse_types(raw):
    """(individual, lair) as [(letter, multiplier)], from a raw MM type line.

    **Classified by the LETTER, not by the prose around it.** A-I and O-Z are
    lair hoards, J-N are what an individual carries, and the two sets are
    disjoint -- so the letter decides with no ambiguity at all.

    That matters because the Monster Manual writes the same fact three different
    ways and a parser keyed on the words gets two of them wrong:

      * ``L individually; C, O, Q (x10), S in lair``   -- orc, letter first
      * ``Individuals L, M; D, Q (x5), S in lair``     -- gnoll, word first,
        **and two letters**
      * ``J-N, Q``                                     -- crab spider, a RANGE
        and no qualifying word anywhere

    The old regex matched only the first form. On the gnoll it found nothing and
    printed *"no individual treasure"* for a creature that carries two types,
    and it filed the crab spider's whole J-N range as a lair hoard -- which
    `roll_lair` would then have refused, since no J-N letter is a lair type.
    A silently plausible wrong answer, which is the worst kind.

    Multipliers were dropped outright: ``Q (x10)`` rolled once.
    """
    if not raw or raw.strip().lower() in ('nil', '-', ''):
        return [], []
    ind, lair = [], []
    for m in _TYPE_RE.finditer(raw):
        first, last, mult = m.group(1), m.group(2), m.group(3)
        mult = int(mult) if mult else 1
        span = ([chr(c) for c in range(ord(first), ord(last) + 1)]
                if last else [first])
        for letter in span:
            (ind if letter in INDIVIDUAL else lair).append((letter, mult))
    return ind, lair


def monster_types(name):
    """(individual, lair, raw) from bestiary/ -- see parse_types for the pairs."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bestiary
    raw = bestiary.field(name, 'Treasure Type')
    ind, lair = parse_types(raw)
    return ind, lair, raw


def fmt_types(pairs):
    """"L, M" or "Q x5" for display."""
    return ', '.join('%s x%d' % (L, m) if m > 1 else L for L, m in pairs) or '-'


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
            print('%-12s individual %-8s lair %-18s  MM: %r'
                  % (k, fmt_types(ind), fmt_types(lair), raw))
        return 0

    letter, n = a.type, a.individuals
    if a.monster:
        try:
            ind, lair, raw = monster_types(a.monster)
        except KeyError as e:
            print('%s' % e)
            return 1
        print('%s: MM treasure type %r' % (a.monster, raw))
        pairs = lair if a.lair else ind
        if not pairs:
            print('  no %s treasure' % ('lair' if a.lair else 'individual'))
            return 0
        # A creature may carry or hoard SEVERAL types -- the gnoll carries both
        # L and M -- so every letter is rolled and the coins summed.
        print('  %s lists %d type(s): %s -- rolling each'
              % ('lair' if a.lair else 'individuals', len(pairs),
                 fmt_types(pairs)))
        total = {}
        for L, mult in pairs:
            for i in range(mult):
                if a.lair:
                    got, notes = roll_lair(L)
                else:
                    got, notes = roll_individual(L, max(1, n))
                print('  --- type %s%s ---'
                      % (L, ' (%d of %d)' % (i + 1, mult) if mult > 1 else ''))
                for line in notes:
                    print('    ' + line)
                for k, v in got.items():
                    total[k] = total.get(k, 0) + v
        print('  ===')
        print('  TOTAL: %s'
              % (', '.join('%d %s' % (v, k) for k, v in total.items())
                 or 'nothing'))
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
