#!/usr/bin/env python3
"""Open loops -- the things that will one day close, computed from the log.

    python tools/loops.py                          # everything open, by due day
    python tools/loops.py --subject wend           # just Wend's
    python tools/loops.py --due 83                 # open and due by day 83
    python tools/loops.py --touching "Wend, Osk"   # <- THE ONE THAT MATTERS
    python tools/loops.py history L002
    python tools/loops.py open --subject bern --what "..." --day 77 --evidence ...
    python tools/loops.py close L018 --day 79 --evidence 79:2 --note "..."

WHY THIS EXISTS -- four errors of exactly one shape. A forward-looking note was
written, the thing happened, and nobody went back to close it:

  * `articles.md` art. 11 warned that the Wace receipt would reach Wend before
    she had seen the letter. True on day 55, fired on day 65, and the DM quoted
    it as live on DAY 77.
  * `npcs.md` said of Ancel *"Unanswered. He will not sit in the square
    forever."* Answered on day 34, quoted as live on day 77 -- FORTY-THREE DAYS.
  * `CHECKLIST` section 11 was headed "day 39" while play stood at 77, while
    warning in its own second paragraph that snapshots rot.
  * "Rowe stays until his foot heals", long after he had gone south with Halm.

**A warning is the one kind of prose that never LOOKS stale.** A stale total
looks like a number and can be checked against a tool. A stale warning looks
exactly like a live one, so it gets quoted for ever.

TWO DESIGN DECISIONS, both the player's, and both load-bearing:

  1. **This file is a LOG, not a table of loops with a `closed` cell.** One row
     per EVENT -- open, close, supersede, note -- and the open set is DERIVED,
     the same way `hp.py` derives hit points. A mutable `closed` column would be
     materialised state, which is the only category of thing in this repo that
     can rot. The first draft of the schema had exactly that bug.

  2. **`close` REQUIRES evidence, and this tool refuses without it.** A loop
     cannot be closed with a flag: closing means citing the thing that closed
     it. That is precisely the step skipped on art. 11 -- and if closing art. 11
     had required naming day 65, the DM would have had to *find* day 65, which
     was the whole of the omission.

AND THE POINT OF `--touching`: asking me to remember to check a list is asking
the same faculty that is already wrong. Being SHOWN the list is different. So
the intended use is not "read all the loops" -- it is **print the loops for
whoever the player just named**, every turn. That is a grep, not a judgment.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, read_tsv, today                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'loops.tsv')
DAYS = os.path.join(ROOT, 'campaign', 'days.tsv')

OPEN_VERBS = ('open', 'supersede')
VERBS = OPEN_VERBS + ('close', 'note')


def current_day(path=None):
    """max(day) over campaign/days.tsv. Derived, so it cannot drift."""
    days = [int(r['day']) for r in read_tsv(path or DAYS, missing_ok=True)
            if r.get('day', '').strip().isdigit()]
    return max(days) if days else None


def state(rows=None, path=None):
    """{loop_id: row} for the LATEST event of each loop, in log order.

    `note` rows deliberately do not change a loop's state -- they are for
    recording movement on something still open.
    """
    rows = rows if rows is not None else read_tsv(path or LOG, missing_ok=True)
    latest, order = {}, []
    for r in rows:
        lid = r.get('loop', '').strip()
        if not lid:
            continue
        if lid not in latest:
            order.append(lid)
        if r.get('verb', '').strip() == 'note' and lid in latest:
            continue
        prev = latest.get(lid, {})
        merged = dict(prev)
        # A `close` row need not restate the subject or the text.
        for k, v in r.items():
            if v.strip() or k not in merged:
                merged[k] = v
        latest[lid] = merged
    return latest, order


def open_loops(rows=None, path=None):
    latest, order = state(rows, path)
    return [latest[i] for i in order
            if latest[i].get('verb', '').strip() in OPEN_VERBS]


def _due_key(r, day):
    """Overdue first, then soonest, then undated. Undated is not 'never'."""
    e = r.get('expected_day', '').strip()
    if not e.isdigit():
        return (1, 0)
    return (0, int(e))


def report(rows=None, path=None, subject=None, due=None, touching=None,
           day=None):
    loops = open_loops(rows, path)
    day = day if day is not None else current_day()
    if subject:
        s = subject.lower()
        loops = [r for r in loops if s in r.get('subject', '').lower()]
    if touching:
        names = [n.strip().lower() for n in touching.split(',') if n.strip()]
        loops = [r for r in loops
                 if any(n in (r.get('subject', '') + ' ' + r.get('what', '')).lower()
                        for n in names)]
    if due is not None:
        loops = [r for r in loops
                 if r.get('expected_day', '').strip().isdigit()
                 and int(r['expected_day']) <= due]
    if not loops:
        return 'no open loops matching'
    loops.sort(key=lambda r: _due_key(r, day))
    out = []
    for r in loops:
        exp = r.get('expected_day', '').strip()
        if exp.isdigit() and day is not None and int(exp) < day:
            when = 'OVERDUE %s' % exp
        elif exp.isdigit():
            when = 'day %s' % exp
        else:
            when = '--'
        out.append('%-5s %-11s %-12s %s'
                   % (r.get('loop', ''), when, r.get('subject', ''),
                      r.get('what', '')))
    head = 'OPEN LOOPS (%d)' % len(loops)
    if day is not None:
        head += ', as of day %d' % day
    return head + '\n' + '\n'.join(out)


def next_id(rows=None, path=None):
    latest, _ = state(rows, path)
    n = 0
    for lid in latest:
        if lid.startswith('L') and lid[1:].isdigit():
            n = max(n, int(lid[1:]))
    return 'L%03d' % (n + 1)


def build_parser():
    p = argparse.ArgumentParser(
        prog='loops.py',
        description='Open loops, derived from the append-only log.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--subject', help='filter by subject')
    p.add_argument('--due', type=int, help='only those due by this campaign day')
    p.add_argument('--touching',
                   help='comma-separated names; print loops mentioning any of '
                        'them. RUN THIS EVERY TURN with whoever was just named')
    p.add_argument('--day', type=int, help='override the current campaign day')
    sub = p.add_subparsers(dest='cmd')

    o = sub.add_parser('open', help='open a new loop')
    o.add_argument('--subject', required=True)
    o.add_argument('--what', required=True)
    o.add_argument('--day', type=int, help='campaign day it was opened')
    o.add_argument('--expected-day', default='', help='when it should close')
    o.add_argument('--evidence', default='', help='where it was said')
    o.add_argument('--loop', help='force an id; normally auto-assigned')

    c = sub.add_parser('close', help='close a loop. EVIDENCE IS REQUIRED')
    c.add_argument('loop')
    c.add_argument('--evidence', required=True,
                   help='the thing that closed it -- day:seq, file:line, a row')
    c.add_argument('--day', type=int)
    c.add_argument('--note', default='')

    s = sub.add_parser('supersede', help='restate a loop, keeping it open')
    s.add_argument('loop')
    s.add_argument('--what', required=True)
    s.add_argument('--expected-day', default='')
    s.add_argument('--day', type=int)
    s.add_argument('--evidence', default='')

    n = sub.add_parser('note', help='record movement without closing')
    n.add_argument('loop')
    n.add_argument('--what', required=True)
    n.add_argument('--day', type=int)
    n.add_argument('--evidence', default='')

    h = sub.add_parser('history', help='every event for one loop')
    h.add_argument('loop')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    rows = read_tsv(a.log_file, missing_ok=True)
    latest, _ = state(rows)
    day = a.day if getattr(a, 'day', None) is not None else current_day()

    if a.cmd == 'history':
        hits = [r for r in rows if r.get('loop', '').strip() == a.loop]
        if not hits:
            print('no loop %r' % a.loop)
            return 1
        for r in hits:
            print('day %-4s %-10s %-11s %s  [%s]'
                  % (r.get('day', ''), r.get('verb', ''),
                     r.get('subject', ''), r.get('what', ''),
                     r.get('evidence', '')))
        return 0

    if a.cmd in ('close', 'supersede', 'note'):
        if a.loop not in latest:
            print('no loop %r. Open ones:' % a.loop)
            print(report(rows, day=day))
            return 1
        if a.cmd == 'close' and latest[a.loop]['verb'] == 'close':
            print('%s is ALREADY CLOSED (day %s, evidence %s).'
                  % (a.loop, latest[a.loop].get('day'),
                     latest[a.loop].get('evidence')))
            print('Closing it twice would hide which event actually closed it.')
            return 1
        row = dict(when=today(), day=day if day is not None else '',
                   loop=a.loop, verb=a.cmd,
                   subject=latest[a.loop].get('subject', ''),
                   evidence=getattr(a, 'evidence', ''),
                   expected_day=getattr(a, 'expected_day', ''),
                   what=getattr(a, 'what', '') or getattr(a, 'note', ''))
        append(a.log_file, row)
        print('%s %s' % (a.loop, a.cmd.upper()))
        print(report(rows=read_tsv(a.log_file), day=day))
        return 0

    if a.cmd == 'open':
        lid = a.loop or next_id(rows)
        if lid in latest:
            print('%s already exists; use supersede or pick another id' % lid)
            return 1
        append(a.log_file, dict(
            when=today(), day=day if day is not None else '', loop=lid,
            verb='open', subject=a.subject, expected_day=a.expected_day,
            evidence=a.evidence, what=a.what))
        print('%s OPENED' % lid)
        return 0

    print(report(rows, subject=a.subject, due=a.due, touching=a.touching,
                 day=day))
    return 0


if __name__ == '__main__':
    sys.exit(main())
