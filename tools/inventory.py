#!/usr/bin/env python3
"""What the party owns, computed from campaign/inventory_log.tsv.

    python tools/inventory.py                     # everything, by category
    python tools/inventory.py --asset rope_50ft   # one line, with conditions
    python tools/inventory.py --held-by Ista
    python tools/inventory.py carried             # spikes: owned minus emplaced
    python tools/inventory.py check               # the audit. Exit 1 on FAIL

NEVER QUOTE A QUANTITY FROM A PROSE FILE OR FROM THE OLD `qty` CELL.

WHY THIS EXISTS. `campaign/inventory.tsv` was the ONE campaign file still edited
IN PLACE -- materialised state with no watermark, which is the only category of
thing in this repo that can rot -- and it is the file that rotted five times:
the two carts (forty days with no row at all), the two mules, the small goods
(357 gp, seventeen days untracked), six ropes (eleven days while the row said
2), the dragon scales (carried as unsold long after they were sold).

*** AND THE `unit` COLUMN, WHICH IS THE PLAYER'S DESIGN AND THE REAL FIX ***

The old `qty` cell was prose pretending to be a number, and every tool that read
it took the first integer it could find:

    "~2.5 IRON + 8 STANDARD"   read as 2    <- TWO THINGS IN ONE CELL
    "1,072 gp 1 sp"            read as 1
    "~100 lb, ~97 gp"          read as 100  <- a WEIGHT read as a COUNT
    "18 sealed (+1 broached)"  read as 18   <- the broached flask invisible
    "8 (7 sound, 1 damaged)"   read as 8    <- and the damaged rope is the one
                                               that nearly dropped Blartho

Three of those were simply wrong. **One row per (asset, condition), and the unit
is what forces the split** -- you cannot write "2.5 person-weeks of iron and 8
of standard" into a single signed quantity.

WHAT THIS FILE DELIBERATELY DOES NOT OWN

  * **Light and fuel** are `campaign/light.tsv`'s. Lanterns, oil, torches and
    candles were counted in two places and drifted apart TWICE. Two sources for
    one fact is the defect this project exists to remove.
  * **Where a thing is in the dungeon** is `campaign/world_changes.tsv`'s. This
    file records what the party OWNS; `world.py deployed` records what is
    emplaced. **Spikes carried = owned - emplaced, derived, never stored.**
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import ledger as ledgermod                                       # noqa: E402
import world as worldmod                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'inventory_log.tsv')

# A closed vocabulary, so a typo is a test failure and not a second silent unit.
# `each` is the default and covers most things. Add to this list deliberately.
UNITS = ('each', 'person-week', 'set', 'quiver', 'bundle', 'pair', 'flask',
         'gallon', 'lb', 'gp-weight', 'tod', 'sheet', 'gp')

# *** `gp` IS A UNIT OF QUANTITY HERE, NOT A PRICE, AND IT IS FOR DEBTS. ***
# Added day 93, when the player asked whether Fenn's 90 gp was recorded anywhere
# and the answer was NO. A debt owed TO the party is a thing the party OWNS
# whose quantity happens to be denominated in money -- 90 gp of `loan_fenn` --
# and there was no unit that could say so, so two receivables (Fenn's 90 and
# Dill's 1.1) existed only in prose. Fenn's was worse: the money left the purse
# on day 27, INSIDE the day-39 anchor, so no money.tsv row records it either,
# and its last written mention was a loop that got CLOSED on day 92.
#
# DO NOT use `gp` for the purse. That is ledger.py's, computed from money.tsv,
# and a second copy here is exactly the drift this whole scheme exists to stop.
# `gp-weight` remains what it always was: the WEIGHT of carried coin.

# Conditions describe the state of a thing WHILE HELD. Disposal is a negative
# qty with a note, not a condition -- "sold" is an event, not a state.
CONDITIONS = ('', 'sound', 'damaged', 'worn', 'issued', 'sealed', 'broached',
              'empty', 'full', 'unidentified', 'cached')

VERBS = ('anchor', 'move')

# Assets whose count is owned by another log. Naming them here rather than
# relying on nobody adding a row is the difference between a rule and a hope.
FOREIGN = {
    'oil_flask': 'campaign/light.tsv -- tools/light.py oilstate. That log knows '
                 'which flasks have been BROACHED, so sealed is derived there '
                 'and counting it here would recreate the drift that light.py '
                 'warned about twice',
    'coin': 'campaign/money.tsv -- tools/ledger.py',
}


def rows(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def state(log=None):
    """{asset: {key: [qty, unit, holder, note]}}. Anchors set; moves add.

    *** THE KEY IS (CONDITION, UNIT), NOT CONDITION ALONE, AND THAT COST 48
    ARROWS. ***

    This keyed on condition only, carrying the unit along as a value that each
    row overwrote. So two rows for one asset in the same condition but DIFFERENT
    UNITS landed in the same cell, and the later anchor destroyed the earlier:

        day 77  anchor 48 each     cell = [48, 'each']
        day 77  anchor  1 quiver   cell = [ 1, 'quiver']   <- ate the 48
        day 81  move  +36 each     cell = [37, 'each']

    From day 77 to day 81 the tool reported the party's arrows as "1 quiver" and
    the forty-eight were invisible -- including in brief.py, which is the file
    the DM reads first every session. Caught 2026-09-14 when the player said
    "we have 3 quivers, we bought 1 each at the start of the game" and the total
    came out 37.

    CLAUDE.md and this module's own docstring both promised "one row per (asset,
    condition), with an explicit unit". The unit column was added and nothing was
    keyed on it -- the unit-column principle half-applied, which is worse than
    not applying it, because the figure looks authoritative.

    A key is rendered as "condition" when the unit is the only distinction, so
    the report reads the same as before for every asset held in one unit.
    """
    log = log if log is not None else rows()
    out = {}
    for r in log:
        a = (r.get('asset') or '').strip()
        if not a:
            continue
        cond = (r.get('condition') or '').strip()
        unit = (r.get('unit') or 'each').strip()
        cell = out.setdefault(a, {}).setdefault((cond, unit),
                                                [0.0, unit, '', ''])
        if (r.get('verb') or '').strip() == 'anchor':
            cell[0] = _num(r.get('qty'))
        else:
            cell[0] += _num(r.get('qty'))
        if r.get('holder', '').strip():
            cell[2] = r['holder'].strip()
        if r.get('note', '').strip():
            cell[3] = r['note'].strip()
    return out


def conditions(st_for_asset):
    """{condition: cell} for callers that only care about the condition.

    Kept so ledger.py and light.py, which ask "is there a row for this asset",
    do not have to learn about the compound key.
    """
    out = {}
    for (cond, _unit), cell in st_for_asset.items():
        out.setdefault(cond, cell)
    return out


def qty(asset, log=None):
    """Total across every condition. Mixed units are refused, not summed."""
    st = state(log).get(asset, {})
    units = {v[1] for v in st.values() if v[0]}
    if len(units) > 1:
        raise ValueError('%s is held in more than one unit (%s); ask per '
                         'condition instead of for a total'
                         % (asset, ', '.join(sorted(units))))
    return sum(v[0] for v in st.values())


def carried_spikes(log=None):
    """owned - emplaced. DERIVED, so the two can never drift apart."""
    emplaced, _ = worldmod.deployed(worldmod.load())
    return qty('iron_spike', log) - emplaced.get('iron spike', 0)


def _fmt(v):
    return ('%d' % v) if float(v) == int(v) else ('%g' % v)


def report(log=None, asset=None, held_by=None):
    st = state(log)
    ass = ledgermod.assets()
    lines, last_kind = [], None
    for a in sorted(st, key=lambda k: (ass.get(k, {}).get('kind', 'zz'), k)):
        if asset and a != asset:
            continue
        kind = ass.get(a, {}).get('kind', '?')
        for (cond, _u), (n, unit, holder, note) in sorted(st[a].items()):
            if held_by and held_by.lower() not in holder.lower():
                continue
            if not n and not asset:
                continue
            if kind != last_kind and not asset:
                lines.append('')
                lines.append('-- %s' % kind)
                last_kind = kind
            lines.append('  %-16s %8s %-12s %-12s %-16s %s'
                         % (a, _fmt(n), unit, cond or '-', holder or '-',
                            note[:44]))
    return '\n'.join(lines).lstrip('\n') or 'nothing held'


def gp_weight(asset, qty, ass=None):
    """(gp-weight, note) for `qty` of `asset`, or (None, why) if unknown.

    assets.tsv carries weight in TWO columns on purpose -- a number and its
    unit -- because DMG Appendix O counts encumbrance in GP WEIGHT, ten to the
    pound, while every merchant and cart in the fiction talks in POUNDS. A bare
    number would be a unit kept in somebody's head.
    """
    ass = ass or ledgermod.assets()
    a = ass.get(asset) or {}
    w = (a.get('weight') or '').strip()
    if not w:
        return None, 'no weight in assets.tsv'
    try:
        w = float(w)
    except ValueError:
        return None, 'weight %r is not a number' % w
    unit = (a.get('weight_unit') or '').strip().lower()
    if unit.startswith('lb'):
        return w * qty * 10.0, ''
    return w * qty, ''


def weigh(log=None, held_by=None):
    """Every held thing, with its weight, grouped and totalled.

    *** THIS IS WHAT L052 HAS BEEN BLOCKED ON SINCE DAY 95. *** The loop says
    the party's real load has never been computed and that the first attempt put
    them over the 6-inch band -- and its caveat is that `inventory_log` tracks
    what the party OWNS AND HAS WITH IT, not WHAT WAS PACKED FOR A TRIP.

    This does not solve that. It gives the arithmetic the loop needs and reports
    the gap honestly: totals by HOLDER, so the reader can see what is actually
    in hand versus what is in a barn twenty-two miles away, and an explicit list
    of every held thing whose weight nobody has ever recorded.
    """
    st = state(log)
    ass = ledgermod.assets()
    by_holder, unknown = {}, []
    for a in sorted(st):
        for (cond, _u), (n, unit, holder, _note) in sorted(st[a].items()):
            if not n:
                continue
            if held_by and held_by.lower() not in (holder or '').lower():
                continue
            gp, why = gp_weight(a, n, ass)
            key = (holder or '-').strip() or '-'
            by_holder.setdefault(key, []).append((a, n, unit, cond, gp, why))
            if gp is None:
                unknown.append((a, n, unit, key, why))

    out, grand = [], 0.0
    for holder in sorted(by_holder, key=lambda h: -sum(
            r[4] or 0 for r in by_holder[h])):
        rows_ = by_holder[holder]
        sub = sum(r[4] or 0 for r in rows_)
        grand += sub
        out.append('')
        out.append('== %s' % holder)
        for a, n, unit, cond, gp, why in sorted(
                rows_, key=lambda r: -(r[4] or 0)):
            out.append('   %-18s %8s %-12s %-9s %10s %8s  %s'
                       % (a, _fmt(n), unit, cond or '-',
                          ('%.0f' % gp) if gp is not None else '?',
                          ('%.1f' % (gp / 10.0)) if gp is not None else '?',
                          why))
        out.append('   %-18s %41s %8.1f lb' % ('', '%.0f gp-wt' % sub, sub / 10))
    out.append('')
    out.append('GRAND TOTAL %s gp-weight = %.1f lb'
               % ('{:,.0f}'.format(grand), grand / 10))
    if unknown:
        out.append('')
        out.append('NO WEIGHT RECORDED (%d held things) -- these are NOT in the '
                   'totals above:' % len(unknown))
        for a, n, unit, holder, why in unknown:
            out.append('   %-18s %8s %-12s %-24s %s'
                       % (a, _fmt(n), unit, holder[:24], why))
    out.append('')
    out.append('   columns: asset  qty  unit  condition  gp-weight  lb')
    return '\n'.join(out).lstrip('\n')


def check(log=None):
    """[(severity, message)]. Empty means the inventory hangs together."""
    log = log if log is not None else rows()
    ass = ledgermod.assets()
    out = []
    for i, r in enumerate(log, 1):
        a = (r.get('asset') or '').strip()
        where = 'row %d (%s)' % (i, a or '?')
        if a not in ass:
            out.append(('FAIL', '%s names an asset that is not in '
                                'campaign/assets.tsv' % where))
        if a in FOREIGN:
            out.append(('FAIL', '%s is counted by %s. TWO SOURCES FOR ONE FACT '
                                'is exactly what drifted twice on the oil '
                                'count -- remove this row.'
                        % (where, FOREIGN[a])))
        u = (r.get('unit') or '').strip()
        if u and u not in UNITS:
            out.append(('FAIL', '%s uses unit %r, which is not in the closed '
                                'vocabulary %s' % (where, u, list(UNITS))))
        c = (r.get('condition') or '').strip()
        if c not in CONDITIONS:
            out.append(('WARN', '%s uses condition %r, not in %s. "sold" and '
                                '"consumed" are EVENTS -- log a negative qty '
                                'with a note instead'
                        % (where, c, list(CONDITIONS))))
        v = (r.get('verb') or '').strip()
        if v not in VERBS:
            out.append(('FAIL', '%s has verb %r; expected one of %s'
                        % (where, v, list(VERBS))))
    for a, conds in state(log).items():
        for cond, (n, _u, _h, _n2) in conds.items():
            if n < 0:
                out.append(('FAIL', 'asset %r condition %r computes to %s -- '
                                    'a negative holding is not a thing'
                            % (a, cond or '-', _fmt(n))))
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog='inventory.py',
        description='What the party owns, computed from the log.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--asset', help='one asset, broken out by condition')
    p.add_argument('--held-by', help='filter by holder')
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('weigh', help='every held thing, with weights, grouped by holder and totalled')
    sub.add_parser('carried', help='spikes: owned minus emplaced')
    sub.add_parser('check', help='units, assets, verbs and negatives')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)

    if a.cmd == 'check':
        problems = check(log)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            print('inventory OK: every asset resolves, every unit is in the '
                  'vocabulary, nothing is double-counted, nothing is negative.')
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'weigh':
        print(weigh(log, held_by=a.held_by))
        return 0

    if a.cmd == 'carried':
        emplaced, _ = worldmod.deployed(worldmod.load())
        owned = qty('iron_spike', log)
        print('iron spikes: %s owned, %s emplaced in the dungeon, %s CARRIED'
              % (_fmt(owned), emplaced.get('iron spike', 0),
                 _fmt(carried_spikes(log))))
        print('  (carried is DERIVED. It is not stored anywhere, so it cannot '
              'drift from the emplacement log the way the oil count did.)')
        return 0

    print(report(log, asset=a.asset, held_by=a.held_by))
    return 0


if __name__ == '__main__':
    sys.exit(main())
