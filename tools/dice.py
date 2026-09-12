#!/usr/bin/env python3
"""Dice, rolled in the open and written down.

    python tools/dice.py 3d6+2 --reason "hp for a new henchman"
    python tools/dice.py d20 --times 6

Two campaign rules shape this module.

**Roll in the open.** Every roll is printed with its notation, the individual
dice, and the modifier, so the player can check the arithmetic. The only roll
this campaign conceals is the wandering-check jitter, and even that is reported
once it fires -- `tools/clock.py` handles it and marks it `hidden`.

**Nothing is reconstructed from memory.** Every roll is appended to
`campaign/rolls.tsv`. The one time the record of a fight had to be rebuilt it
came out of a 60 MB conversation transcript; a 40-line TSV is better.

1e range notation is not modern dice notation. "3-18" in the Monster Manual
means 3d6, and "2-7" means 1d6+1 -- the low end is the number of dice or the
offset, never a uniform pick from the range. `range_roll` implements that
reading; see its docstring for how the two cases are told apart.
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, today                                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLLS = os.path.join(ROOT, 'campaign', 'rolls.tsv')

# *** AN ESCAPE HATCH FOR TOOL-TESTING, BECAUSE THE HOLE WAS ONLY HALF SHUT. ***
#
# `roll()` logs by DEFAULT, which is right for play: CLAUDE.md treats
# campaign/rolls.tsv as the evidence and a roll that never got written down is a
# roll that can be argued about later. But it means anything that drives
# combat.py or clock.py writes into the campaign's own audit trail.
#
# pytest was doing exactly that -- 31 rows a run, 125 runs, ~3,875 rows in a
# 7,247-row file -- and `tools/tests/conftest.py` closed it FOR PYTEST ONLY.
# Driving combat.py by hand from a shell to check the new declaration gate put
# three more real d20s into the live log within a minute of the gate being
# written, which is the same hole through the other door.
#
# Set DND_ROLL_LOG to redirect. The logging branch still runs and is still
# tested; it just writes somewhere that is not the campaign.
ROLLS = os.environ.get('DND_ROLL_LOG') or ROLLS

_NOTATION = re.compile(r'^\s*(\d*)\s*d\s*(\d+)\s*([+-]\s*\d+)?\s*$', re.I)
_RANGE = re.compile(r'^\s*(\d+)\s*-\s*(\d+)\s*$')


class Roll(object):
    """A roll and everything needed to audit it."""

    def __init__(self, notation, dice, modifier=0, reason='', hidden=False):
        self.notation = notation
        self.dice = list(dice)
        self.modifier = modifier
        self.reason = reason
        self.hidden = hidden

    @property
    def total(self):
        return sum(self.dice) + self.modifier

    def __int__(self):
        return self.total

    def __str__(self):
        body = '+'.join(str(d) for d in self.dice)
        if self.modifier:
            body += ' %+d' % self.modifier
        if len(self.dice) == 1 and not self.modifier:
            return '%s = %d' % (self.notation, self.total)
        return '%s = %s = %d' % (self.notation, body, self.total)


def roll(notation, reason='', hidden=False, log=True, rng=random):
    """Roll standard notation: d20, 3d6, 2d4+1, d100."""
    m = _NOTATION.match(notation)
    if not m:
        raise ValueError('cannot read dice notation %r' % notation)
    n = int(m.group(1) or 1)
    sides = int(m.group(2))
    mod = int((m.group(3) or '0').replace(' ', ''))
    if n < 1 or sides < 1:
        raise ValueError('%r asks for %d dice of %d sides' % (notation, n, sides))
    r = Roll(notation, [rng.randint(1, sides) for _ in range(n)], mod,
             reason, hidden)
    if log:
        record(r)
    return r


def range_roll(spec, reason='', hidden=False, log=True, rng=random):
    """Roll 1e range notation such as "3-18", "2-7", "1-6".

    The books write damage and quantities as a range, and the range implies the
    dice. Two cases, and telling them apart matters because they have different
    distributions:

      * `lo` divides `hi` evenly and hi/lo is a real die size -- "3-18" is 3d6,
        "10-40" is 10d4, "2-8" is 2d4.
      * otherwise the range is one die plus an offset -- "2-7" is 1d6+1,
        "3-12" would be ambiguous but resolves as 3d4 by the first rule.

    Rolling uniformly across the range would be wrong in both cases: 3d6 is not
    flat, and the difference shows up over a campaign of small hits.
    """
    m = _RANGE.match(spec)
    if not m:
        return roll(spec, reason, hidden, log, rng)
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo > hi:
        raise ValueError('range %r runs backwards' % spec)
    if lo == hi:
        r = Roll(spec, [lo], 0, reason, hidden)
        if log:
            record(r)
        return r
    if lo and hi % lo == 0 and (hi // lo) in (2, 3, 4, 6, 8, 10, 12, 20, 100):
        n, sides, mod = lo, hi // lo, 0
    else:
        n, sides, mod = 1, hi - lo + 1, lo - 1
    r = Roll('%s (%dd%d%s)' % (spec, n, sides, '%+d' % mod if mod else ''),
             [rng.randint(1, sides) for _ in range(n)], mod, reason, hidden)
    if log:
        record(r)
    return r


def record(r, path=None, exped='', turn=''):
    """Append to campaign/rolls.tsv. Silently skipped if the file is absent."""
    path = path or ROLLS
    if not os.path.exists(path):
        return
    try:
        append(path, dict(when=today(), exped=exped, turn=turn,
                          notation=r.notation,
                          dice=','.join(str(d) for d in r.dice),
                          modifier=r.modifier, total=r.total,
                          hidden='yes' if r.hidden else '',
                          reason=r.reason))
    except (ValueError, OSError):
        pass                      # a broken audit log must never stop the game


def build_parser():
    p = argparse.ArgumentParser(
        prog='dice.py', description='Roll dice and write them down.')
    p.add_argument('notation', help='d20, 3d6+2, d100, or a 1e range like 3-18')
    p.add_argument('--times', type=int, default=1, help='roll it this many times')
    p.add_argument('--reason', default='', help='what the roll is for')
    p.add_argument('--no-log', action='store_true',
                   help='do not append to campaign/rolls.tsv')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    for _ in range(max(1, a.times)):
        print(range_roll(a.notation, a.reason, log=not a.no_log))
    return 0


if __name__ == '__main__':
    sys.exit(main())
