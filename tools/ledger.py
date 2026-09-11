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
  3. a physical good that money moved for has a row in `inventory.tsv` -- the
     **leg that was missing every one of the five times.** Services are exempt
     by kind, which is what the service ids in `assets.tsv` are for;
  4. the computed purse agrees with the cell in `inventory.tsv`. That cell is
     MATERIALISED STATE and is the only thing here that can rot, so it is
     checked rather than trusted -- the same mechanism by which `light.py`
     caught the oil count drifting twice.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'money.tsv')
ASSETS = os.path.join(ROOT, 'campaign', 'assets.tsv')
INVENTORY = os.path.join(ROOT, 'campaign', 'inventory.tsv')

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


def total(log=None, day=None):
    """The purse in gp. Anchors supersede everything above them."""
    out = 0.0
    for r in (log if log is not None else rows()):
        if day is not None and r.get('day', '').isdigit() and int(r['day']) > day:
            continue
        if r.get('asset') == ANCHOR:
            out = _delta(r)
        else:
            out += _delta(r)
    return round(out, 2)


def gp_sp(v):
    """1,072.1 -> "1,072 gp 1 sp". Silver is a tenth and always has been."""
    neg = '-' if v < 0 else ''
    v = abs(round(v, 2))
    g = int(v)
    s = int(round((v - g) * 10))
    return '%s%s gp%s' % (neg, '{:,}'.format(g), (' %d sp' % s) if s else '')


def inventory_cell():
    """The purse as inventory.tsv states it -- materialised state, checkable."""
    for r in read_tsv(INVENTORY, missing_ok=True):
        if r.get('category') == 'funds' and r.get('item', '').strip() == 'gold pieces':
            q = r.get('qty', '').replace(',', '')
            g = re.search(r'(\d+)\s*gp', q)
            s = re.search(r'(\d+)\s*sp', q)
            if g:
                return int(g.group(1)) + (int(s.group(1)) / 10.0 if s else 0.0)
    return None


def inventory_items():
    """{item name lowercased: qty cell} -- the other leg of the double entry."""
    return {r.get('item', '').strip().lower(): r.get('qty', '')
            for r in read_tsv(INVENTORY, missing_ok=True)}


def check(log=None, ass=None):
    """[(severity, message)]. Empty means the ledger hangs together."""
    log = log if log is not None else rows()
    ass = ass if ass is not None else assets()
    inv = inventory_items()
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
    for a in sorted({(r.get('asset') or '').strip() for r in log}):
        if a in ('', ANCHOR) or a not in ass:
            continue
        if ass[a].get('kind') in SERVICE_KINDS:
            continue
        name = ass[a].get('name', '').lower()
        stem = re.split(r'[,(\-]', name)[0].strip()
        if not any(stem and stem in k for k in inv):
            out.append(('WARN', 'asset %r (%s) has money against it but no '
                                'inventory row matching %r. THIS IS THE LEG '
                                'THAT WAS MISSING ALL FIVE TIMES.'
                        % (a, ass[a].get('kind'), stem)))

    cell, computed = inventory_cell(), total(log)
    if cell is None:
        out.append(('WARN', 'inventory.tsv states no purse to check against'))
    elif abs(cell - computed) > 0.001:
        out.append(('FAIL', 'THE PURSE DISAGREES. money.tsv computes %s; '
                            'inventory.tsv states %s. The LOG wins -- correct '
                            'the cell, or append the movement that is missing.'
                    % (gp_sp(computed), gp_sp(cell))))
    return out


def report(log=None):
    log = log if log is not None else rows()
    lines = ['THE PURSE: %s' % gp_sp(total(log)),
             '  (computed from %d rows in campaign/money.tsv -- never stored)'
             % len(log), '']
    ins = sum(_delta(r) for r in log
              if _delta(r) > 0 and r.get('asset') != ANCHOR)
    outs = sum(_delta(r) for r in log
               if _delta(r) < 0 and r.get('asset') != ANCHOR)
    anch = [r for r in log if r.get('asset') == ANCHOR]
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
    sub.add_parser('assets', help='the asset reference')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)

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
