#!/usr/bin/env python3
"""Total the party's experience from the encounter log.

    python tools/xp.py                    # current totals
    python tools/xp.py --by-expedition    # what each trip was worth
    python tools/xp.py --log              # every award, in order

Running totals are NOT stored anywhere. They are computed from
`campaign/encounters.tsv` every time, because a stored total is a number that
silently goes stale -- which is exactly what happened to the roster's XP line,
last correct on day 2 of expedition 1 and quoted as authoritative for weeks
afterwards.

The prime-requisite bonus is applied per character, not to the pot: PHB p.9
(fighters, STR 16+), p.10 (magic-users, INT 16+) and p.11 (clerics WIS 16+,
thieves DEX 16+) each grant "+10% of earned experience" to that character.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, 'campaign', 'characters.tsv')
LOG = os.path.join(ROOT, 'campaign', 'encounters.tsv')


# DMG p.85 halves experience for henchmen -- but read where the sentence sits.
# It is inside "Division of Experience Points", which opens "Experience points
# (x.p.) for SLAIN MONSTERS, however, is strictly your prerogative", and its
# worked example is monster xp: "the x.p. for monsters killed total 4,300 ...
# halved for henchman characters."  The next heading, EXPERIENCE VALUE OF
# TREASURE TAKEN, is a separate section and never mentions henchmen at all.
#
# So the two kinds of award are halved by DIFFERENT mechanisms:
#
#   monster   -- an explicit halving rule, and p.85 hands the DM the decision
#                in those words.  RULED 2026-09-05, day 39: once Hask, Dellie
#                and Ista became classed characters they draw a FULL share of
#                monster xp.  They stand in the same corridor and take the same
#                bite.
#   treasure  -- NO halving rule exists.  Treasure xp is 1 gp = 1 xp on coin
#                actually gained, so half a share of the coin yields half the
#                xp on its own.  Halving the award as well would be halving it
#                twice.  The `share` column therefore now means SHARE OF THE
#                TREASURE, and applies to treasure rows only.
#
# The switch is PROSPECTIVE, held that way by the day-39 anchor in
# encounters.tsv.  Without it, flipping these weights would have recomputed
# every past award: the pot divisor on a nine-body fight goes 7 -> 8, which
# would have quietly taken xp AWAY from the six PCs for a ruling that was
# meant to give some to the three.
TREASURE_WEIGHT = {'full': 1.0, 'half': 0.5, '': 1.0, '-': 1.0}


def characters():
    out = {}
    for r in read_tsv(CHARS):
        share = (r.get('share') or 'full').strip().lower()
        w = TREASURE_WEIGHT.get(share)
        if w is None:
            raise ValueError('characters.tsv: %s has share=%r; expected full or '
                             'half' % (r['name'], r.get('share')))
        out[r['name']] = dict(cls=r['class'], prime=r['prime'], score=r['score'],
                              bonus=r['bonus'].lower() == 'yes',
                              treasure_weight=w,
                              # 'all' means THE PARTY -- the six full-share PCs.
                              # It is a roster fact, not a weight, and must stay
                              # separate now that monster weight is 1.0 for
                              # everyone.  Deriving it from the weight again
                              # would silently sweep the three henchmen into
                              # every 'all' award they were not present for.
                              is_party=(share == 'full'),
                              # A 0-LEVEL NORMAL MAN HAS NO THRESHOLD TO
                              # REACH. rules/zero-level.md: 1e has no
                              # 0-level-to-1st progression at all -- 1st
                              # level BEGINS at 0 xp and the gate is
                              # capacity, not points. So `-` is the
                              # honest value and None is the honest
                              # parse; int('-') crashed the whole tool
                              # and the pre-commit hook the hour Brand
                              # was given a stat line.
                              next_level=_threshold(r['next_level']))
    return out


def _threshold(v):
    """XP needed for next level, or None for a character who has no next level."""
    v = (v or '').strip()
    return int(v) if v and v != '-' else None


def totals(chars=None, log=None):
    """(totals, per-award detail). Anchors reset a character outright.

    Shares accumulate as exact fractions and the +10% is applied ONCE to the
    running base, not to each award. Applying it per kill and truncating loses
    the bonus entirely on small awards -- a share of 8 becomes 8.8 becomes 8 --
    and the PHB grants it on "earned experience", not per corpse. Over a
    campaign of many small fights the difference is most of the bonus.
    """
    chars = chars or characters()
    log = log if log is not None else read_tsv(LOG)
    anchor = {n: 0 for n in chars}
    base = {n: 0.0 for n in chars}
    detail = []
    for row in log:
        xp = int(row['xp'] or 0)
        if row['kind'] == 'anchor':
            for chunk in row['notes'].split('\u2014')[0].split('/'):
                parts = chunk.strip().split()
                if len(parts) >= 2 and parts[0] in anchor:
                    try:
                        anchor[parts[0]] = int(parts[1])
                        base[parts[0]] = 0.0       # anchors supersede
                    except ValueError:
                        pass
            detail.append((row, dict(anchor), 'anchor'))
            continue
        # 'all' means the PARTY -- every full-share character -- and nothing
        # else.  Half-share NPCs must be NAMED, because they are not at every
        # fight and because making 'all' include them would silently re-divide
        # a hundred past awards the moment somebody new joins.  That happened
        # once: adding Hask and Dellie took Dave from 567 to 520 by giving them
        # a cut of a carrion crawler they never saw.
        # 'all' expands to every FULL-SHARE character and may appear INSIDE a
        # comma list -- "all,Hask,Dellie" is the common case, a party award that
        # a half-share ally was also present for.
        #
        # It used to be an exact-match-only token, so "all,Hask,Dellie" split
        # into ['all','Hask','Dellie'], 'all' matched no character, and was
        # dropped by the filter below.  The six PCs silently got NOTHING and the
        # two allies split the whole award.  Caught 2026-09-01 when a 435 xp
        # treasure row moved nobody's total but theirs.
        who = []
        for w in row['earned_by'].split(','):
            w = w.strip()
            if w == 'all':
                who.extend(n for n, c in chars.items() if c['is_party'])
            elif w:
                who.append(w)
        seen = set()
        who = [n for n in who if not (n in seen or seen.add(n))]
        who = [w for w in who if w in chars]
        if not who:
            continue
        # A share is xp / (sum of weights), not xp / (head count) -- a
        # henchman drawing half does NOT halve everyone else's award, it
        # counts as half a claimant on the pot.  DMG p.85.
        #
        # MONSTER rows weight everyone at 1.0; only TREASURE rows consult the
        # share column.  See the TREASURE_WEIGHT comment above for why.
        wt = ({n: 1.0 for n in who} if row['kind'] == 'monster'
              else {n: chars[n]['treasure_weight'] for n in who})
        pot = sum(wt[n] for n in who)
        unit = xp / pot
        got = {n: unit * wt[n] for n in who}
        for n in who:
            base[n] += got[n]
        halves = [n for n in who if wt[n] != 1.0]
        detail.append((row, got,
                       'share %.2f of %.1f%s' % (unit, pot,
                        ' (half: %s)' % ', '.join(halves) if halves else '')))
    tot = {}
    for n, c in chars.items():
        earned = base[n] * (1.1 if c['bonus'] else 1.0)
        tot[n] = anchor[n] + int(earned)
    return tot, detail


def build_parser():
    p = argparse.ArgumentParser(
        prog='xp.py', description='Total party experience from the encounter log.')
    p.add_argument('--log', action='store_true', help='show every award in order')
    p.add_argument('--by-expedition', action='store_true',
                   help='subtotal each expedition')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    chars = characters()
    rows = read_tsv(LOG)
    tot, detail = totals(chars, rows)

    if a.log:
        for row, got, how in detail:
            print('exp %-4s %-9s %-42s %6s  %s'
                  % (row['exped'], row['kind'], row['encounter'][:42],
                     row['xp'], how))
            if row['kind'] != 'anchor':
                print('        ' + '  '.join('%s +%.2f' % (k, v)
                                             for k, v in sorted(got.items())))
        print()

    if a.by_expedition:
        seen = {}
        for row in rows:
            if row['kind'] == 'anchor':
                continue
            seen.setdefault(row['exped'], {'monster': 0, 'treasure': 0})
            seen[row['exped']][row['kind']] += int(row['xp'] or 0)
        print('%-6s %9s %9s %9s' % ('exped', 'monster', 'treasure', 'total'))
        for e, v in sorted(seen.items()):
            print('%-6s %9d %9d %9d' % (e, v['monster'], v['treasure'],
                                        v['monster'] + v['treasure']))
        print()

    print('%-9s %-11s %-7s %8s %8s %8s' %
          ('', 'class', 'bonus', 'XP', 'next lvl', 'to go'))
    for n, c in sorted(chars.items(), key=lambda kv: -tot[kv[0]]):
        # A 0-level man has NO next level to print. 1e gives no 0-to-1st
        # progression: 1st level begins at 0 xp and the gate is capacity, not
        # points (rules/zero-level.md). Printing a threshold of 0 would read as
        # "already there", and printing anything else would invent a rule.
        nxt = c['next_level']
        print('%-9s %-11s %-7s %8d %8s %8s'
              % (n, c['cls'], '+10%' if c['bonus'] else '-', tot[n],
                 nxt if nxt is not None else 'n/a',
                 max(0, nxt - tot[n]) if nxt is not None else '-'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
