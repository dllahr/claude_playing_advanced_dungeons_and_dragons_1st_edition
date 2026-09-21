#!/usr/bin/env python3
"""WHO IS CARRYING WHAT, and what it does to their movement rate.

    python tools/carry.py                 # the whole manifest, per person
    python tools/carry.py person Dave     # one person's load and band
    python tools/carry.py check           # reconcile against what is OWNED

*** WHY THIS IS A SEPARATE LOG FROM inventory_log.tsv. ***

The player asked, on day 102, what data structure recorded per-person kit. There
wasn't one. It was the free-text `holder` column, one string per row, holding
things like "WORN: Dave, Torsat, Yrtone, Blartho" and "ONE EACH: Dave, Torsat,
Tristle, Frython, Hask, Ista -- 2 spare". Thirty-three distinct hand-typed
strings were in use, `--held-by Dave` was a substring match that returned the
group total, and the tidy per-person table the DM had presented was assembled BY
HAND out of that prose.

Adding `holder` to inventory's cell key was tried first. It fragmented the
ownership history -- inconsistent historical strings split every asset's running
total, and iron_spike computed to -13 for one string and +13 for another.

L052 had named both options on day 95: "Either inventory_log grows a notion of a
packed load, or the outfitting step starts producing a manifest." This is the
manifest, and the split is right on its merits: OWNERSHIP AND CARRIAGE ARE
DIFFERENT QUESTIONS. The party owns a kettle it is not carrying and carries
Ista's own hand axe it does not own.

WHAT THIS COMPUTES THAT NOTHING COULD BEFORE
--------------------------------------------
Per-person load in gp weight, against that person's own encumbrance bands --
because PHB p.101's bands are modified by the STRENGTH TABLE II allowance, which
differs by eleven hundred gp weight across this party. Dave carries 1,000 more
than Tristle before either notices.

*** AND IT APPORTIONS THE SHARED KIT, WHICH IS THE PART EVERY HAND-CALCULATION
GOT WRONG. *** `party` rows are real weight carried by real people; ignoring
them flatters every load, and the rope, rations, sacks and torches are most of
what the party is actually lifting.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import inventory as invmod                                       # noqa: E402
import rules as rulesmod                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'carry.tsv')
CHARS = os.path.join(ROOT, 'campaign', 'characters.tsv')

SHARED = 'party'


def characters():
    return {r['name']: r for r in read_tsv(CHARS)}


def rows(path=None):
    return read_tsv(path or LOG)


def who_vocabulary():
    """The closed set. A free-typed holder is how this went wrong."""
    return set(characters()) | {SHARED}


def state(log=None):
    """{who: {(asset, unit): qty}}. Anchors set outright; moves add."""
    out = {}
    for r in (log if log is not None else rows()):
        who = (r.get('who') or '').strip()
        asset = (r.get('asset') or '').strip()
        if not who or not asset:
            continue
        unit = (r.get('unit') or 'each').strip()
        try:
            q = float(r.get('qty') or 0)
        except ValueError:
            continue
        cell = out.setdefault(who, {})
        if (r.get('verb') or '').strip() == 'anchor':
            cell[(asset, unit)] = q
        else:
            cell[(asset, unit)] = cell.get((asset, unit), 0.0) + q
    return out


# --------------------------------------------------------------------------
# encumbrance
# --------------------------------------------------------------------------

def _table(heading):
    return rulesmod.find(heading)


def _allowance_table():
    """{STR spec: gp-weight allowance}, parsed from rules/exploration.md.

    *** THREE THINGS IN THIS TABLE BREAK A NAIVE PARSER AND ALL THREE DID. ***

    1. It is printed as TWO COLUMN-PAIRS WITH A BLANK SPACER between them,
       exactly as the PHB sets it -- "| 3 | -350 | | 14-15 | +200 |" -- so the
       right-hand pair is cells 3 and 4, not 2 and 3. Pairing by stride of two
       read the spacer as a key and returned +0 for every high Strength.
    2. THE MINUS SIGN IS U+2212, not an ASCII hyphen, and the ranges use an
       EN-DASH. A `[+-]` character class matches neither, so every penalty
       parsed as zero -- including STR 3's -350.
    3. Two values are the WORD "normal", one of them as "normal (no penalty)".

    The first version of this function returned +0 for STR 18/26 and for STR 3
    alike, which would have let Dave carry what Dellie carries.
    """
    import re
    txt = open(os.path.join(ROOT, 'rules', 'exploration.md'),
               encoding='utf-8').read()
    m = re.search(r'\| STR \| Weight allowance \|.*?\n\n', txt, re.S)
    if not m:
        raise ValueError('the Strength allowance table is not in '
                         'rules/exploration.md under its expected heading')
    table = {}
    for line in m.group(0).splitlines():
        if line.strip().startswith('|---'):
            continue
        cells = [c.strip().strip('*').strip()
                 for c in line.strip().strip('|').split('|')]
        cells = [c for c in cells if c]              # drop the spacer
        for i in range(0, len(cells) - 1, 2):
            key, val = cells[i], cells[i + 1]
            if not re.match(r'^\d', key):
                continue
            key = key.replace(' ', '').replace('\u2013', '-').replace('\u2014', '-')
            if 'normal' in val.lower():
                table[key] = 0
                continue
            mv = re.search(r'([+\u2212-])\s*([\d,]+)', val)
            if mv:
                sign = -1 if mv.group(1) in ('-', '\u2212') else 1
                table[key] = sign * int(mv.group(2).replace(',', ''))
    if not table:
        raise ValueError('parsed no rows out of the Strength allowance table')
    return table


def _allowance_lookup(score):
    return _match_band(str(score).strip(), _allowance_table())


def _match_band(score, table):
    import re
    if score in table:
        return table[score]
    # exceptional strength: "18/26" falls in the 18/01-50 band
    if '/' in score:
        base, pct = score.split('/', 1)
        try:
            pct = int(pct)
        except ValueError:
            pct = 0
        for key, val in table.items():
            mm = re.match(r'^18/(\d+)[-–](\d+)$', key)
            if mm and int(mm.group(1)) <= pct <= int(mm.group(2)):
                return val
        return table.get('18', 0)
    try:
        n = int(score)
    except ValueError:
        return 0
    for key, val in table.items():
        mm = re.match(r'^(\d+)[-–](\d+)$', key)
        if mm and int(mm.group(1)) <= n <= int(mm.group(2)):
            return val
    return table.get(score, 0)


# PHB pp.101-102 bands, in gp weight, BEFORE the Strength allowance is added.
BANDS = (('normal', 350, '12"'),
         ('heavy', 700, '9"'),
         ('very heavy', 1050, '6"'),
         ('encumbered', None, '3"-4"'))


def band_for(gp, allowance):
    """(band name, movement) for a load, with the allowance added to each band."""
    for name, ceiling, move in BANDS:
        if ceiling is None or gp <= ceiling + allowance:
            return name, move
    return BANDS[-1][0], BANDS[-1][2]


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def person_load(name, log=None, share=None):
    """(gp carried, [(asset, qty, unit, gp, why)], shared gp apportioned)."""
    st = state(log)
    ass = invmod.ledgermod.assets()
    lines, tot = [], 0.0
    for (asset, unit), qty in sorted(st.get(name, {}).items()):
        if not qty:
            continue
        gp, why = invmod.gp_weight(asset, qty, ass)
        if gp:
            tot += gp
        lines.append((asset, qty, unit, gp, why))
    return tot, lines, (share or 0.0)


def shared_total(log=None):
    """(gp, [(asset, qty, unit, gp, why)]) for the `party` rows."""
    st = state(log)
    ass = invmod.ledgermod.assets()
    lines, tot = [], 0.0
    for (asset, unit), qty in sorted(st.get(SHARED, {}).items()):
        if not qty:
            continue
        gp, why = invmod.gp_weight(asset, qty, ass)
        if gp:
            tot += gp
        lines.append((asset, qty, unit, gp, why))
    return tot, lines


def report(log=None, bearers=None):
    """The whole manifest, per person, with bands.

    `bearers` is who is actually on the trip, and it matters: the shared kit is
    divided among THEM, not among everybody on the roster. Ten people sharing
    the rope carry less each than seven do.
    """
    chars = characters()
    st = state(log)
    people = [n for n in chars if n in st or n in (bearers or [])]
    bearers = bearers or people
    shared_gp, shared_lines = shared_total(log)
    per_head = shared_gp / len(bearers) if bearers else 0.0

    out = []
    out.append('SHARED KIT -- carried by somebody, bearer not tracked')
    for asset, qty, unit, gp, why in sorted(shared_lines,
                                            key=lambda r: -(r[3] or 0)):
        out.append('   %-18s %8s %-12s %8s %7s  %s'
                   % (asset, invmod._fmt(qty), unit,
                      ('%.0f' % gp) if gp is not None else '?',
                      ('%.1f' % (gp / 10)) if gp is not None else '?', why))
    out.append('   %-18s %38s %7.1f lb' % ('TOTAL SHARED',
                                           '%.0f gp-wt' % shared_gp,
                                           shared_gp / 10))
    out.append('   divided among %d bearers = %.0f gp-wt (%.1f lb) each'
               % (len(bearers), per_head, per_head / 10))
    out.append('')
    out.append('%-9s %8s %8s %9s %9s %-11s %s'
               % ('', 'own', '+share', 'TOTAL', 'allowance', 'band', 'move'))
    grand = 0.0
    for name in sorted(people, key=lambda n: -person_load(n, log)[0]):
        own, lines, _ = person_load(name, log)
        share = per_head if name in bearers else 0.0
        total = own + share
        grand += own
        alw = _allowance_lookup(chars[name].get('str', '') or '0')
        bname, move = band_for(total, alw)
        out.append('%-9s %8.0f %8.0f %9.0f %+9d %-11s %s'
                   % (name, own, share, total, alw, bname, move))
    out.append('')
    out.append('   personal kit %.0f gp-wt + shared %.0f = %.0f gp-wt, %.0f lb'
               % (grand, shared_gp, grand + shared_gp,
                  (grand + shared_gp) / 10))
    out.append('   columns are GP WEIGHT, ten to the pound (DMG Appendix O)')
    return '\n'.join(out)


def check(log=None):
    """[(severity, message)]. Reconcile the manifest against what is OWNED."""
    log = log if log is not None else rows()
    st = state(log)
    vocab = who_vocabulary()
    owned = invmod.state()
    ass = invmod.ledgermod.assets()
    out = []

    for r in log:
        who = (r.get('who') or '').strip()
        if who and who not in vocab:
            out.append(('FAIL', 'who=%r is not a character or %r. THE '
                        'VOCABULARY IS CLOSED -- a free-typed holder is how '
                        'this went wrong in the first place.' % (who, SHARED)))
        a = (r.get('asset') or '').strip()
        if a and a not in ass:
            out.append(('FAIL', 'asset %r is not in campaign/assets.tsv' % a))
        v = (r.get('verb') or '').strip()
        if v not in ('anchor', 'move'):
            out.append(('FAIL', 'verb %r is not anchor or move' % v))

    for who, cells in st.items():
        for (a, unit), q in cells.items():
            if q < 0:
                out.append(('FAIL', '%s carries %g %s -- a negative is not a '
                            'thing' % (who, q, a)))

    carried = {}
    for who, cells in st.items():
        for (a, unit), q in cells.items():
            carried[a] = carried.get(a, 0.0) + q
    for a, q in sorted(carried.items()):
        have = sum(c[0] for c in owned.get(a, {}).values())
        if q > have + 1e-9:
            out.append(('FAIL', 'the manifest carries %g %s but the party owns '
                        '%g -- carriage may not exceed ownership' % (q, a, have)))

    return out


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog='carry.py',
        description='Who is carrying what, and what it does to their movement.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--bearers', help='comma-separated; who is actually on the '
                   'trip. The shared kit is divided among THEM, not the roster')
    sub = p.add_subparsers(dest='cmd')
    q = sub.add_parser('person', help='one person\'s load and band')
    q.add_argument('name')
    sub.add_parser('check', help='reconcile against what is OWNED')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)
    bearers = [b.strip() for b in a.bearers.split(',')] if a.bearers else None

    if a.cmd == 'check':
        problems = check(log)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            print('carry OK: every bearer is in the vocabulary, every asset '
                  'resolves, nothing is negative, and nothing is carried in '
                  'greater quantity than the party owns.')
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'person':
        chars = characters()
        if a.name not in chars:
            print('%r is not in campaign/characters.tsv. Known: %s'
                  % (a.name, ', '.join(sorted(chars))))
            return 1
        shared_gp, _ = shared_total(log)
        people = bearers or [n for n in chars if n in state(log)]
        share = shared_gp / len(people) if people else 0.0
        own, lines, _ = person_load(a.name, log, share)
        alw = _allowance_lookup(chars[a.name].get('str', '') or '0')
        print('%s -- STR %s, allowance %+d gp-weight'
              % (a.name, chars[a.name].get('str', '?'), alw))
        for asset, qty, unit, gp, why in sorted(lines,
                                                key=lambda r: -(r[3] or 0)):
            print('   %-18s %8s %-12s %8s %7s  %s'
                  % (asset, invmod._fmt(qty), unit,
                     ('%.0f' % gp) if gp is not None else '?',
                     ('%.1f' % (gp / 10)) if gp is not None else '?', why))
        total = own + share
        print('   own %.0f gp-wt + %.0f share of the common kit = %.0f gp-wt '
              '(%.1f lb)' % (own, share, total, total / 10))
        bname, move = band_for(total, alw)
        print('   band: %s -- movement %s' % (bname, move))
        return 0

    print(report(log, bearers))
    return 0


if __name__ == '__main__':
    sys.exit(main())
