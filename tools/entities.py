#!/usr/bin/env python3
"""People, places, and the scenes that join them. Every name must RESOLVE.

    python tools/entities.py people                  # the roster
    python tools/entities.py places
    python tools/entities.py who Wend                # one person, and their scenes
    python tools/entities.py scenes --day 77
    python tools/entities.py check                   # every name resolves?

WHY `interactions.tsv` EXISTS. Social events lived only in prose -- three
thousand lines of it -- which is why "narrating from my own summary instead of
from the log" is the largest error class in this campaign. Every one of these
was a query that could not be run:

    how Kell died  ..  Sim's two years  ..  Cuddy toward Yrtone  ..  Ista's
    grievance  ..  the barrel "never moved"  ..  "the plan was the 51st"  ..
    Meg and Tibb as two families  ..  "you nearly forgot Wend"

WHY IDENTITY AND CONDITION ARE SEPARATE. `people.tsv` holds only what is stable
-- id, name, aliases, kind, first day. Anything that CHANGES is an event with a
date and goes to `interactions.tsv` (kind=fact), `loops.tsv` or
`availability.tsv`. *"Cuddy is frail"* is not a property of Cuddy; it became
true on day 76 and was rolled for. **Filing that sort of thing as a property is
exactly how `npcs.md` came to say of Ancel "Unanswered. He will not sit in the
square forever" -- true for two days, answered on day 34, and still quoted as
live on DAY 77.**

AND WHY ALIASES ARE A COLUMN. *Wetherby* and *Wethersby* are both in this
repository, some of them typed by the player. *"Rell's brother"* and *Gyll* are
one man whose name nobody in the hundred used for two years. A fuzzy match is a
guess, and a guess cannot be a constraint; an alias table can.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEOPLE = os.path.join(ROOT, 'campaign', 'people.tsv')
PLACES = os.path.join(ROOT, 'campaign', 'places.tsv')
SCENES = os.path.join(ROOT, 'campaign', 'interactions.tsv')

KINDS = ('pc', 'henchman', 'npc', 'hireling', 'offstage', 'dead')
SCENE_KINDS = ('first_contact', 'counsel', 'negotiation', 'promise', 'payment',
               'grievance', 'teaching', 'report', 'conflict', 'fact')


def _table(path):
    return {r['id']: r for r in read_tsv(path, missing_ok=True) if r.get('id')}


def people():
    return _table(PEOPLE)


def places():
    return _table(PLACES)


def scenes(path=None):
    return read_tsv(path or SCENES, missing_ok=True)


def index(table):
    """{lowercased id, name or alias: id}. The only legal way to resolve a name."""
    out = {}
    for pid, r in table.items():
        out[pid.lower()] = pid
        out[r.get('name', '').strip().lower()] = pid
        for a in (r.get('aliases') or '').split(';'):
            if a.strip():
                out[a.strip().lower()] = pid
    out.pop('', None)
    return out


def resolve(name, table=None):
    return index(table if table is not None else people()).get(
        name.strip().lower())


def split_people(cell):
    return [p.strip() for p in (cell or '').split(',') if p.strip()]


def who(name):
    """One person, and every scene they were in, in order."""
    pl = people()
    pid = resolve(name, pl)
    if pid is None:
        near = sorted({v for k, v in index(pl).items()
                       if name.lower() in k or k in name.lower()})
        return 'no person %r.%s' % (
            name, ('\nDid you mean: %s' % ', '.join(near)) if near else '')
    r = pl[pid]
    out = ['%s  (%s)' % (r['name'], r.get('kind', '')),
           '  first appears day %s' % r.get('first_day', '?')]
    if r.get('aliases'):
        out.append('  also called: %s' % r['aliases'].replace(';', ', '))
    if (r.get('place') or '').strip() not in ('', '-'):
        out.append('  usually at: %s' % r['place'])
    if r.get('notes'):
        out.append('  %s' % r['notes'])
    mine = [s for s in scenes() if pid in
            [resolve(n, pl) for n in split_people(s.get('people'))]]
    out.append('')
    out.append('%d scene(s):' % len(mine))
    for s in mine:
        out.append('  day %-4s %-14s %-13s %s'
                   % (s.get('day'), s.get('kind'),
                      ('reaction ' + s['reaction']) if s.get('reaction') else '',
                      s.get('summary', '')[:78]))
        out.append('           %s' % s.get('evidence', ''))
    out.append('')
    out.append('These are the SCENES. For wounds, rolls, money and gear see '
               '`tools/recall.py %s`.' % r['name'])
    return '\n'.join(out)


def check():
    """[(severity, message)]. The validator the prose never had."""
    pl, pc, out = people(), places(), []
    pidx, cidx = index(pl), index(pc)

    for pid, r in sorted(pl.items()):
        if r.get('kind') not in KINDS:
            out.append(('FAIL', 'person %r has kind %r, not in %s'
                        % (pid, r.get('kind'), list(KINDS))))
        where = (r.get('place') or '').strip()
        if where and where != '-' and where.lower() not in cidx:
            out.append(('FAIL', 'person %r lives at %r, which is not in '
                                'campaign/places.tsv' % (pid, where)))

    for pid, r in sorted(pc.items()):
        parent = (r.get('parent') or '').strip()
        if parent and parent.lower() not in cidx:
            out.append(('FAIL', 'place %r has parent %r, which does not exist'
                        % (pid, parent)))

    for i, s in enumerate(scenes(), 1):
        where = 'scene %s:%s' % (s.get('day'), s.get('seq'))
        for n in split_people(s.get('people')):
            if n.lower() not in pidx:
                # Both directions: "Wendel" must suggest "wend" as readily as
                # "Wen" does. A refusal that cannot name the near miss is an
                # obstacle rather than a gate.
                low = n.lower()
                near = sorted({v for k, v in pidx.items()
                               if low in k or k in low})
                out.append(('FAIL', '%s names %r, which is not in '
                                    'campaign/people.tsv.%s'
                            % (where, n,
                               (' Did you mean %s?' % ', '.join(near))
                               if near else '')))
        p = (s.get('place') or '').strip()
        if p and p != '-' and p.lower() not in cidx:
            out.append(('FAIL', '%s is at %r, which is not in '
                                'campaign/places.tsv' % (where, p)))
        if s.get('kind') not in SCENE_KINDS:
            out.append(('FAIL', '%s has kind %r, not in %s'
                        % (where, s.get('kind'), list(SCENE_KINDS))))
        if not (s.get('evidence') or '').strip():
            out.append(('WARN', '%s cites no evidence' % where))

    seen = set()
    for s in scenes():
        key = (s.get('day'), s.get('seq'))
        if key in seen:
            out.append(('FAIL', 'two scenes share day:seq %s:%s -- other files '
                                'point at that pair and it must be unique'
                        % key))
        seen.add(key)
    return out


def build_parser():
    p = argparse.ArgumentParser(
        prog='entities.py', description='People, places and the scenes.')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('people')
    sub.add_parser('places')
    w = sub.add_parser('who', help='one person, and every scene they were in')
    w.add_argument('name')
    s = sub.add_parser('scenes')
    s.add_argument('--day', type=int)
    s.add_argument('--kind')
    sub.add_parser('check', help='every name must resolve')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)

    if a.cmd == 'check':
        problems = check()
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            pl, sc = people(), scenes()
            print('entities OK: %d people, %d places, %d scenes, and every '
                  'name in every scene resolves.' % (len(pl), len(places()),
                                                     len(sc)))
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'who':
        print(who(a.name))
        return 0

    if a.cmd in ('people', 'places'):
        t = people() if a.cmd == 'people' else places()
        for pid, r in sorted(t.items(), key=lambda kv: (kv[1].get('kind', ''),
                                                        kv[0])):
            print('%-14s %-24s %-10s %s'
                  % (pid, r.get('name', '')[:24], r.get('kind', ''),
                     (r.get('notes', '') or '')[:60]))
        return 0

    for s in scenes():
        if a.day is not None and s.get('day') != str(a.day):
            continue
        if a.kind and s.get('kind') != a.kind:
            continue
        print('day %-4s %-3s %-12s %-14s %s'
              % (s.get('day'), s.get('seq'), s.get('place', ''),
                 s.get('kind', ''), s.get('summary', '')[:72]))
        print('             %s' % s.get('people', ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
