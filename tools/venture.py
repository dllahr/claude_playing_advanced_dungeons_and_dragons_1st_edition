#!/usr/bin/env python3
"""The wool/cloth venture -- what it holds, what it owes, and who owns it.

    python tools/venture.py                # holdings and payables
    python tools/venture.py shares         # the cap table
    python tools/venture.py check          # closed vocab, negatives, totals

*** WHY THIS EXISTS. *** The player, day 103, after inventory.py's per-person
reckoning: "along with an inventory of the venture, let's track who owns the
shares of the venture." The share structure has sat in wool_venture.md's prose
since day 16 and was never queryable; the venture's own stock (wool bought on
its own money, book=art7 in money.tsv) had NO home in any log at all, because
inventory_log.tsv is explicitly the PARTY's, not the venture's.

*** SCOPE, THE PLAYER'S OWN WORDS. *** "(a) what it physically holds and
(b) the money position -- who is owed what. NOT (c) valuation... we can figure
that out when needed, and not frequently." So this module computes neither a
share price nor a venture net worth. `report()` is exactly (a) and (b);
nothing here answers "what is a share worth".

*** THE PARTY IS THE ONLY CAPITAL INVESTOR. *** Player, day 103: Wend and the
six holders each earned their shares (her judgement, their wool at the floor);
neither put in coin. So venture_shares.tsv carries no capital-weighting and
this module does not compute one -- see its own header for the full reasoning.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import ledger as ledgermod                                       # noqa: E402
import carry as carrymod                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'venture.tsv')
SHARES_LOG = os.path.join(ROOT, 'campaign', 'venture_shares.tsv')

HOLDERS_GROUP = 'holders_six'
POSITION_ASSETS = {
    'venture_capital': 'owed BY the venture TO the party -- capital outstanding',
    'venture_payable_holders': 'owed BY the venture TO the six holders',
}


def rows(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def share_rows(path=None):
    return read_tsv(path or SHARES_LOG, missing_ok=True)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def share_vocabulary():
    """A character name, a non-PC people.tsv id, or the `holders_six` bucket."""
    return set(carrymod.characters()) | set(carrymod.non_pc_people()) \
        | {HOLDERS_GROUP}


def shares(log=None):
    """{holder: shares}. Anchor sets outright; move adds (a transfer)."""
    out = {}
    for r in (log if log is not None else share_rows()):
        who = (r.get('who') or '').strip()
        if not who:
            continue
        q = _num(r.get('shares'))
        if (r.get('verb') or '').strip() == 'anchor':
            out[who] = q
        else:
            out[who] = out.get(who, 0.0) + q
    return out


def state(log=None):
    """{asset: {(unit, holder): qty}}. Anchor sets outright; move adds.

    Unlike inventory_log.tsv's state(), the key includes `holder`: a venture
    payable to `holders_six` and one to `party` are never the same debt, and
    there is no history of mixed holder strings here to fragment -- this file
    started clean on day 103.
    """
    log = log if log is not None else rows()
    out = {}
    for r in log:
        a = (r.get('asset') or '').strip()
        if not a:
            continue
        unit = (r.get('unit') or 'each').strip()
        holder = (r.get('holder') or '').strip()
        cell = out.setdefault(a, {}).setdefault((unit, holder), 0.0)
        q = _num(r.get('qty'))
        if (r.get('verb') or '').strip() == 'anchor':
            out[a][(unit, holder)] = q
        else:
            out[a][(unit, holder)] = cell + q
    return out


def holdings(log=None):
    """[(asset, unit, holder, qty)] for the physical goods -- (a)."""
    ass = ledgermod.assets()
    out = []
    for a, cells in state(log).items():
        if a in POSITION_ASSETS:
            continue
        for (unit, holder), q in cells.items():
            if q:
                out.append((a, unit, holder, q))
    return sorted(out)


def position(log=None):
    """[(asset, holder, gp, note)] for capital/payable rows -- (b)."""
    out = []
    for a in POSITION_ASSETS:
        for (unit, holder), q in state(log).get(a, {}).items():
            if q:
                out.append((a, holder, q))
    return sorted(out)


def report(log=None, slog=None):
    ass = ledgermod.assets()
    out = ['VENTURE HOLDINGS -- (a) what it physically holds', '']
    h = holdings(log)
    if not h:
        out.append('  nothing on record')
    for a, unit, holder, q in h:
        nm = (ass.get(a) or {}).get('name', a)
        out.append('  %-14s %8s %-6s  held by %-12s  %s'
                   % (a, ('%g' % q), unit, holder, nm))
    out.append('')
    out.append('MONEY POSITION -- (b) who is owed what')
    out.append('')
    p = position(log)
    if not p:
        out.append('  nothing on record')
    for a, holder, gp in p:
        direction = ('the venture owes the PARTY' if a == 'venture_capital'
                    else 'the venture owes %s' % holder)
        out.append('  %-24s %8.0f gp -- %s' % (a, gp, direction))
    out.append('')
    st = shares(slog if slog is not None else share_rows())
    total = sum(st.values())
    out.append('CAP TABLE -- %g shares total (see `venture.py shares` for '
               'the full table)' % total)
    return '\n'.join(out)


def shares_report(log=None):
    st = shares(log)
    total = sum(st.values()) or 1.0
    out = ['CAP TABLE -- a share is a claim on PROFIT, not on capital or '
           'stock (venture_shares.tsv header). Capital returns first.', '']
    for who, n in sorted(st.items(), key=lambda kv: -kv[1]):
        if not n:
            continue
        out.append('  %-12s %5g shares  (%.1f%%)' % (who, n, 100 * n / total))
    out.append('')
    out.append('  TOTAL %g shares' % total)
    return '\n'.join(out)


def check(log=None, slog=None):
    """[(severity, message)]. Closed vocab, no negatives, share total intact."""
    log = log if log is not None else rows()
    slog = slog if slog is not None else share_rows()
    ass = ledgermod.assets()
    vocab = carrymod.who_vocabulary()
    out = []

    for r in log:
        a = (r.get('asset') or '').strip()
        if a not in ass and a not in POSITION_ASSETS:
            out.append(('FAIL', 'asset %r is not in campaign/assets.tsv and '
                        'is not a recognised venture position id' % a))
        v = (r.get('verb') or '').strip()
        if v not in ('anchor', 'move'):
            out.append(('FAIL', 'verb %r is not anchor or move' % v))
        holder = (r.get('holder') or '').strip()
        if holder and holder not in vocab and holder != HOLDERS_GROUP:
            out.append(('FAIL', 'holder %r is not a character, a place/'
                        'person id, or %r' % (holder, HOLDERS_GROUP)))

    for a, cells in state(log).items():
        for (unit, holder), q in cells.items():
            if q < 0:
                out.append(('FAIL', '%s (%s, holder %s) computes to %g -- a '
                            'negative holding is not a thing'
                            % (a, unit, holder or '-', q)))

    svocab = share_vocabulary()
    for r in slog:
        who = (r.get('who') or '').strip()
        if who and who not in svocab:
            out.append(('FAIL', 'venture_shares.tsv: who=%r is not a '
                        'character, a non-PC people.tsv id, or %r'
                        % (who, HOLDERS_GROUP)))
    st = shares(slog)
    for who, n in st.items():
        if n < 0:
            out.append(('FAIL', 'venture_shares.tsv: %s holds %g shares -- '
                        'negative shares are not a thing' % (who, n)))

    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog='venture.py',
        description="What the venture holds and owes, and who owns it.")
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--shares-file', default=SHARES_LOG)
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('shares', help='the cap table')
    sub.add_parser('check', help='closed vocab, negatives, share total')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)
    slog = share_rows(a.shares_file)

    if a.cmd == 'shares':
        print(shares_report(slog))
        return 0

    if a.cmd == 'check':
        problems = check(log, slog)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            print('venture OK: every asset and holder resolves, nothing is '
                  'negative.')
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    print(report(log, slog))
    return 0


if __name__ == '__main__':
    sys.exit(main())
