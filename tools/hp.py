#!/usr/bin/env python3
"""Current hit points, computed from campaign/hp_log.tsv.

    python tools/hp.py                       # everyone
    python tools/hp.py --who Dave
    python tools/hp.py --log                 # every wound and heal in order
    python tools/hp.py damage Dave 8 --reason "berserker, round 1" --exped 3
    python tools/hp.py heal Dave 3 --reason "cure light wounds"
    python tools/hp.py anchor Dave 9 --reason "start of expedition 4"

Never quote hp from `party_roster.md`. Its CURRENT STATE block is written by
hand and has been two expeditions stale twice; on the second occasion it led
the DM to tell the player their iron spikes were unavailable.

**Negative hit points are not clamped.** In 1e a character taken to 0 is
unconscious and dies at -10, and a single blow can carry them optionally as low
as -3 (DMG p.82). Reporting a wounded character as "0" would erase exactly the
number the next ruling turns on.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, read_tsv, today                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, 'campaign', 'characters.tsv')
LOG = os.path.join(ROOT, 'campaign', 'hp_log.tsv')


def characters(path=None):
    out = {}
    for r in read_tsv(path or CHARS):
        out[r['name']] = r
    return out


def stabilised(chars=None, rows=None):
    """Who has had their bleeding STOPPED by aid, and is still stable.

    DMG p.82 is explicit that the 1-point-a-round slide to -10 "ceases
    immediately on any round a friendly creature administers aid" -- binding
    wounds, a draught, anything. Before this existed, hp.py derived "bleeding"
    from the NUMBER ALONE, so a character who had been bandaged went on being
    reported as bleeding to death by every briefing until somebody remembered
    otherwise. Ista bandaged Torsat at -1 on day 79 and the tool said he was
    still going down a point a round.

    Any FURTHER damage re-opens it: you can only stabilise a man once per
    wounding.
    """
    chars = chars if chars is not None else characters()
    rows = rows if rows is not None else read_tsv(LOG, missing_ok=True)
    stable = set()
    for r in rows:
        who = r.get('who', '').strip()
        if who not in chars:
            continue
        kind = r.get('kind')
        if kind == 'stabilise':
            stable.add(who)
        elif kind in ('damage', 'anchor'):
            stable.discard(who)
    return stable


def current(chars=None, rows=None):
    """{name: (hp, hp_max)}. Anchors supersede everything above them."""
    chars = chars if chars is not None else characters()
    rows = rows if rows is not None else read_tsv(LOG, missing_ok=True)
    hp = {}
    for n, c in chars.items():
        try:
            hp[n] = int(c.get('hp_max') or 0)
        except ValueError:
            hp[n] = 0
    maxhp = dict(hp)
    for r in rows:
        who = r.get('who', '').strip()
        if who not in hp:
            continue
        try:
            delta = int(r.get('delta') or 0)
        except ValueError:
            continue
        if r.get('kind') == 'anchor':
            hp[who] = delta
        else:
            # The cap is hp_max; there is no floor, deliberately.
            hp[who] = min(maxhp[who], hp[who] + delta)
    return {n: (hp[n], maxhp[n]) for n in hp}


def condition(hp, stable=False):
    """The 1e reading of a hit point total, so it is never guessed in play."""
    if hp <= -10:
        return 'DEAD'
    if hp <= 0:
        if stable:
            return ('unconscious, BLEEDING STOPPED -- and still comatose 1-6 '
                    'turns then OUT A WEEK, cure or no cure (DMG p.82)')
        return 'unconscious and bleeding 1 hp/round (DMG p.82)'
    return ''


def report(chars=None, rows=None):
    hp = current(chars, rows)
    chars = chars if chars is not None else characters()
    stable = stabilised(chars, rows)
    out = ['%-9s %-11s %7s  %s' % ('', 'class', 'hp', 'condition')]
    for n in sorted(hp, key=lambda k: -hp[k][0]):
        cur, mx = hp[n]
        out.append('%-9s %-11s %3d /%3d  %s'
                   % (n, chars[n].get('class', ''), cur, mx,
                      condition(cur, n in stable)))
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='hp.py', description='Current hit points, computed from the log.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--who', help='report one character')
    p.add_argument('--log', action='store_true', help='show every row in order')
    sub = p.add_subparsers(dest='cmd')
    for kind, helptext in (('damage', 'record a wound'),
                           ('heal', 'record a cure or bandaging'),
                           ('rest', 'record natural healing'),
                           ('anchor', 'set hp outright')):
        s = sub.add_parser(kind, help=helptext)
        s.add_argument('who')
        s.add_argument('amount', type=int,
                       help='a positive number; damage subtracts it')
        s.add_argument('--reason', default='')
        s.add_argument('--exped', default='')
        s.add_argument('--turn', default='')
    st = sub.add_parser('stabilise', help='aid given -- the bleeding STOPS '
                                         '(DMG p.82). Restores no hit points')
    st.add_argument('who')
    st.add_argument('--reason', default='')
    st.add_argument('--exped', default='')
    st.add_argument('--turn', default='')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    chars = characters()
    if a.cmd:
        if a.who not in chars:
            print('no character %r; known: %s' % (a.who, ', '.join(sorted(chars))))
            return 1
        # `stabilise` carries no amount: aid stops the bleeding and restores
        # nothing (DMG p.82). Giving it a delta would make it look like healing.
        delta = 0 if a.cmd == 'stabilise' else (
            -abs(a.amount) if a.cmd == 'damage' else abs(a.amount))
        append(a.log_file, dict(when=today(), exped=a.exped, turn=a.turn,
                                who=a.who, kind=a.cmd, delta=delta,
                                reason=a.reason))
        rows = read_tsv(a.log_file, missing_ok=True)
        hp, mx = current(chars, rows)[a.who]
        stable = a.who in stabilised(chars, rows)
        print('%s %s %s-> %d/%d  %s'
              % (a.who, a.cmd,
                 '' if a.cmd == 'stabilise' else '%d ' % abs(a.amount),
                 hp, mx, condition(hp, stable)))
        return 0

    rows = read_tsv(a.log_file, missing_ok=True)
    if a.log:
        for r in rows:
            print('exp %-3s turn %-4s %-9s %-7s %+4s  %s'
                  % (r.get('exped', ''), r.get('turn', ''), r.get('who', ''),
                     r.get('kind', ''), r.get('delta', ''), r.get('reason', '')))
        print()
    if a.who:
        hp, mx = current(chars, rows).get(a.who, (0, 0))
        print('%s %d/%d %s' % (a.who, hp, mx, condition(hp)))
        return 0
    print(report(chars, rows))
    return 0


if __name__ == '__main__':
    sys.exit(main())
