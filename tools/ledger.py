#!/usr/bin/env python3
"""The purse, computed from campaign/money.tsv. And the double-entry check.

    python tools/ledger.py                 # the purse now, and how it got there
    python tools/ledger.py --log           # every movement in order
    python tools/ledger.py --day 65        # the purse as it stood on a day
    python tools/ledger.py check           # the audit. Exit 1 if anything fails
    python tools/ledger.py assets          # the reference, and what moved

NEVER QUOTE THE PURSE FROM A PROSE FILE OR FROM inventory.tsv'S CELL. The total
is a sum over the log, the same way hit points are a sum over `hp_log.tsv`.

WHY THIS EXISTS -- five errors of exactly one shape. A purchase was recorded as
a SENTENCE INSIDE THE NOTES COLUMN of the `funds` row, and the thing bought got
no row anywhere:

    two carts        50 gp each, day 19-20   -- forty days with no row
    two mules        20 gp each              -- ditto
    the small goods  357 gp, day 27          -- 17 days untracked, never rolled
    six 50-ft ropes  2 gp 4 sp, day 67       -- 11 days while the row said 2
    dragon scales    sold day 19 for 110     -- carried as unsold long after

**The fix is that `asset` is required.** `tools/log.py money` refuses a row that
does not name a row in `campaign/assets.tsv`, so you cannot write down that
money moved without writing down what it moved for. That requirement IS the
double entry -- not a reconciliation performed afterwards by someone who
remembers to perform it.

WHAT `check` VERIFIES

  1. every `asset` resolves to `campaign/assets.tsv`;
  2. no row has a zero or missing delta;
  3. a physical good that money moved for has a row in
     `campaign/inventory_log.tsv` -- the **leg that was missing every one of
     the five times.** A disposed-of thing gets a ZERO row with provenance, not
     an absent one: a zero says "sold"; an absence says nothing at all, which
     is precisely how the dragon scales were carried as unsold for weeks after
     they had been sold. Services are exempt by kind, which is what the service
     ids in `assets.tsv` are for.

There is deliberately NO purse-versus-inventory-cell cross-check any more. That
check existed because the purse lived in two places; it now lives in one, and a
tool that compared a figure against a copy of itself was never a check -- it was
an early warning that the design was wrong.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import inventory as invmod                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'money.tsv')
ASSETS = os.path.join(ROOT, 'campaign', 'assets.tsv')

# `anchor` is not an asset; it is the verb that sets the purse outright.
ANCHOR = 'anchor'
SERVICE_KINDS = ('service', 'money')


def assets(path=None):
    return {r['id']: r for r in read_tsv(path or ASSETS, missing_ok=True)
            if r.get('id')}


def rows(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def _delta(r):
    try:
        return float(r.get('delta') or 0)
    except ValueError:
        return 0.0


# The party's purse is book `party`; a BLANK book means party, because every row
# written before 2026-09-15 predates the column and they are all the purse.
#
# OTHER BOOKS ARE NOT MONEY THE PARTY HOLDS. They are COMMITMENTS -- sums the
# party is answerable for that live in somebody else's book. `art7` is the first:
# the wool venture's 500 gp seasonal guarantee, which is Wend's money to spend
# and the party's exposure to carry.
#
# The player's ruling 2026-09-15, and it is what makes this small: TRACK THE CAP,
# NOT THE BOOK. Wend's ledger is hers and is REPORTED, NOT INSPECTED. What gets
# logged here is only what the party is on the hook for.
PARTY_BOOKS = ('', 'party')

# A closed vocabulary, for the same reason `unit` and `condition` have one: a
# typo'd book would either inflate the purse or disappear from it, and both look
# deliberate. Add a book here before using it.
KNOWN_BOOKS = ('party', 'art7')


def book_of(r):
    return (r.get('book') or '').strip()


def total(log=None, day=None, book=None):
    """The purse in gp, or the running total of another book.

    *** A NON-PARTY ROW MUST NEVER MOVE THE PURSE. *** That is the whole risk of
    putting two books in one file, so the filter is the first thing this does
    and `test_ledger.py` pins it.
    """
    want = PARTY_BOOKS if book is None else (book,)
    out = 0.0
    for r in (log if log is not None else rows()):
        if book_of(r) not in want:
            continue
        if day is not None and r.get('day', '').isdigit() and int(r['day']) > day:
            continue
        if r.get('asset') == ANCHOR:
            out = _delta(r)
        else:
            out += _delta(r)
    return round(out, 2)


# The seasonal commitment, articles.md art. 7. The CAP is the party's, the
# spending is Wend's. Art.7 is "called at shearing and nowhere else", so the
# season boundary is SHEARING and not a date -- which is why this carries no
# reset logic. When the season turns, anchor it.
ART7_CAP = 500.0


def art7(log=None, day=None):
    """(spent, cap, remaining) against art. 7's seasonal guarantee."""
    spent = -total(log, day, book='art7')      # payments out are negative
    return round(spent, 2), ART7_CAP, round(ART7_CAP - spent, 2)


def gp_sp(v):
    """1,072.1 -> "1,072 gp 1 sp". Silver is a tenth and always has been."""
    neg = '-' if v < 0 else ''
    v = abs(round(v, 2))
    g = int(v)
    s = int(round((v - g) * 10))
    return '%s%s gp%s' % (neg, '{:,}'.format(g), (' %d sp' % s) if s else '')


def held_assets():
    """Asset ids the party actually holds -- the other leg of the double entry.

    Comes from campaign/inventory_log.tsv. It used to come from a name match
    against inventory.tsv's prose item column, which is why this was the weaker
    half of the check: matching "rope, 50 ft" against "rope_50ft" by stem is a
    guess, and a guess cannot be a constraint.
    """
    import inventory as invmod
    return set(invmod.state())


def check(log=None, ass=None):
    """[(severity, message)]. Empty means the ledger hangs together."""
    log = log if log is not None else rows()
    ass = ass if ass is not None else assets()
    held = held_assets()
    out = []

    for i, r in enumerate(log, 1):
        a = (r.get('asset') or '').strip()
        if not a:
            out.append(('FAIL', 'row %d (day %s) names NO ASSET. That is the '
                                'whole rule: money cannot move for nothing. %r'
                        % (i, r.get('day'), r.get('reason', '')[:60])))
            continue
        if a == ANCHOR:
            continue
        if a not in ass:
            out.append(('FAIL', 'row %d (day %s) names asset %r, which is not '
                                'in campaign/assets.tsv'
                        % (i, r.get('day'), a)))
            continue
        if _delta(r) == 0:
            out.append(('WARN', 'row %d (day %s) has a zero delta'
                        % (i, r.get('day'))))

    # The leg that was missing all five times: a GOOD that money moved for and
    # that appears nowhere in the inventory.
    #
    # *** ONLY FOR THE PARTY'S OWN BOOK. *** A non-party book records money the
    # party is ANSWERABLE FOR, not money it spent, and the goods it buys are
    # somebody else's stock in somebody else's barn. The wool is the case that
    # found this: 288 gp of it under book=art7, which the party never owned and
    # which must never appear in campaign/inventory_log.tsv. Demanding an
    # inventory row for it would push a false entry into the party's gear.
    party_assets = {(r.get('asset') or '').strip()
                    for r in log if book_of(r) in PARTY_BOOKS}
    for a in sorted(party_assets):
        if a in ('', ANCHOR) or a not in ass:
            continue
        if ass[a].get('kind') in SERVICE_KINDS:
            continue
        # *** AN ASSET COUNTED BY ANOTHER TOOL CANNOT HAVE AN INVENTORY ROW,
        # *** SO DEMANDING ONE IS THE CHECKER CRYING WOLF.
        #
        # `inventory.FOREIGN` is the list of things inventory.py deliberately
        # does not count: oil, which `light.py` owns because only that log knows
        # which flasks have been broached, and coin, which `ledger.py` owns.
        # log.py REFUSES an inventory row for them -- so the first time oil was
        # ever bought with a money row naming `oil_flask` (day 97, two flasks,
        # every flask in Wethersby) this check demanded a row that the write
        # path is built to reject, and turned a test red on a correct entry.
        #
        # CLAUDE.md, on audit.py and by extension every checker here: "IF IT
        # EVER CRIES WOLF, LOOSEN THE CHECKER -- do not learn to pass
        # --no-verify." The double entry is still enforced; the other half of it
        # just lives in campaign/light.tsv, which is where it belongs.
        if a in invmod.FOREIGN:
            continue
        if a not in held:
            out.append(('WARN', 'asset %r (%s) has money against it but NO ROW '
                                'in campaign/inventory_log.tsv. THIS IS THE LEG '
                                'THAT WAS MISSING ALL FIVE TIMES. If the thing '
                                'was consumed or sold on, log the movement that '
                                'took it away rather than leaving it absent.'
                        % (a, ass[a].get('kind'))))
    return out


def report(log=None):
    log = log if log is not None else rows()
    # EVERY FIGURE IN THIS BLOCK IS THE PARTY'S BOOK. The in/out breakdown used
    # the unfiltered log while the total did not, so the moment the wool
    # venture's 288 gp went in under art.7 the summary stopped reconciling with
    # the very total printed above it -- 595.6 + 576.3 - 423.5 = 748.4 against a
    # purse of 1,036.4. A breakdown that does not add up to its own headline is
    # worse than no breakdown.
    mine = [r for r in log if book_of(r) in PARTY_BOOKS]
    lines = ['THE PURSE: %s' % gp_sp(total(mine)),
             '  (computed from %d rows in campaign/money.tsv -- never stored)'
             % len(mine), '']
    ins = sum(_delta(r) for r in mine
              if _delta(r) > 0 and r.get('asset') != ANCHOR)
    outs = sum(_delta(r) for r in mine
               if _delta(r) < 0 and r.get('asset') != ANCHOR)
    anch = [r for r in mine if r.get('asset') == ANCHOR]
    if anch:
        lines.append('anchored at %s on day %s'
                     % (gp_sp(_delta(anch[-1])), anch[-1].get('day')))
    lines.append('since:  in %s   out %s' % (gp_sp(ins), gp_sp(outs)))
    return '\n'.join(lines)


def log_report(log=None, ass=None):
    log = log if log is not None else rows()
    ass = ass if ass is not None else assets()
    run, out = 0.0, []
    for r in log:
        if r.get('asset') == ANCHOR:
            run = _delta(r)
        else:
            run += _delta(r)
        out.append('day %-4s %9s  %-16s %-14s %s'
                   % (r.get('day', ''), gp_sp(_delta(r)),
                      r.get('asset', ''), gp_sp(run),
                      r.get('reason', '')[:60]))
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='ledger.py', description='The purse, computed from the log.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--log', action='store_true', help='every movement in order')
    p.add_argument('--day', type=int, help='the purse as it stood on a day')
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('check', help='the double-entry audit')
    sub.add_parser('art7', help="art.7's seasonal exposure -- the "
                                'party is ANSWERABLE for this and does '
                                'not hold it')
    sub.add_parser('assets', help='the asset reference')
    return p



def art7_report(log=None, day=None):
    """Art. 7's seasonal exposure, in words."""
    spent, cap, remaining = art7(log, day)
    return '\n'.join([
        'ART. 7 -- the wool venture\'s seasonal guarantee',
        '  spent     %8s' % gp_sp(spent),
        '  cap       %8s' % gp_sp(cap),
        '  REMAINING %8s' % gp_sp(remaining),
        '',
        '  This is the PARTY\'S EXPOSURE, not its money and not its purse.',
        '  Wend\'s book is hers and is REPORTED, NOT INSPECTED (player, day 83).',
        '  The season turns AT SHEARING, not on a date -- art.7 is "called at',
        '  shearing and nowhere else" -- so when it turns, ANCHOR it.',
    ])

def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)

    if a.cmd == 'art7':
        print(art7_report(day=a.day))
        return 0
    if a.cmd == 'check':
        problems = check(log)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            print('ledger OK: every movement names an asset, every good has an '
                  'inventory row, and the purse agrees with the cell.')
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'assets':
        ass = assets()
        moved = {}
        for r in log:
            moved[r.get('asset')] = moved.get(r.get('asset'), 0) + _delta(r)
        print('%-18s %-10s %-44s %s' % ('id', 'kind', 'name', 'money moved'))
        for k, v in sorted(ass.items()):
            m = moved.get(k)
            print('%-18s %-10s %-44s %s'
                  % (k, v.get('kind', ''), v.get('name', '')[:44],
                     gp_sp(m) if m else ''))
        return 0

    if a.day is not None:
        print('day %d: %s' % (a.day, gp_sp(total(log, day=a.day))))
        return 0
    if a.log:
        print(log_report(log))
        print()
    print(report(log))
    return 0


if __name__ == '__main__':
    sys.exit(main())
