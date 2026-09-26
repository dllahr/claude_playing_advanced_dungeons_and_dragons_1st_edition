#!/usr/bin/env python3
"""Running accounts with NPCs, computed from campaign/accounts.tsv.

    python tools/account.py            every account and its balance
    python tools/account.py holt       one account, with its rows

Positive = the NPC owes the party. The balance is a sum, never stored: the
tab at the Inn is the reason -- it comes off a debt one night at a time, and a
figure in a note would be wrong from the first night.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'accounts.tsv')


def rows(account=None, path=None):
    out = read_tsv(path or LOG, missing_ok=True)
    if account:
        out = [r for r in out if r['account'].strip().lower() ==
               account.strip().lower()]
    return out


def balance(account, path=None):
    return round(sum(float(r['delta']) for r in rows(account, path)), 3)


def balances(path=None):
    accts = []
    for r in read_tsv(path or LOG, missing_ok=True):
        a = r['account'].strip().lower()
        if a not in accts:
            accts.append(a)
    return {a: balance(a, path) for a in accts}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        rs = rows(argv[0])
        for r in rs:
            print('day %-4s %8s  %-6s %s' % (r['day'], r['delta'], r['kind'],
                                             r['note']))
        print('BALANCE %s: %.2f gp' % (argv[0], balance(argv[0])))
    else:
        for a, b in balances().items():
            print('%-10s %10.2f gp' % (a, b))
    return 0


if __name__ == '__main__':
    sys.exit(main())
