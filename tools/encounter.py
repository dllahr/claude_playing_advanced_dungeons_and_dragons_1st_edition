#!/usr/bin/env python3
"""The live fight, computed from campaign/encounter.tsv.

    python tools/encounter.py                     # the fight as it stands
    python tools/encounter.py --round 3
    python tools/encounter.py start --detail "y=21 corridor, one troglodyte" \
        --exped 9 --day 79
    python tools/encounter.py declare Dave "attacks the trog with his long sword"
    python tools/encounter.py hold Blartho --detail "ready to close or cast"
    python tools/encounter.py damage trog1 6 --detail "Torsat, 16 for 8"
    python tools/encounter.py next                # advance a round
    python tools/encounter.py end --detail "the troglodyte is dead"

WHY THIS EXISTS. A fight runs ten messages, and across them the DM was holding
the round number, the initiative order, who was engaged, WHO HAD HELD AN ACTION,
each monster's remaining hit points and who was surprised -- all of it in his own
narration, re-read every turn out of his own previous messages. That is the
"narrate from my own summary" failure operating in the highest-stakes context in
the game, and the worst single error of the campaign happened in exactly it:

    DAY 70, round 285. THE DM RESOLVED THE PARTY'S ROUND WITHOUT ASKING --
    decided who engaged, decided Yrtone swapped weapons, decided nobody fired or
    cast or withdrew. Four attack rolls were VOIDED. "Please stop right now."

*** THE GATE. *** `combat.py round` refuses to roll for a character with no
`declare` row in the current round. The CHECKLIST rule -- THE DM DOES NOT DECLARE
THE PARTY'S ACTIONS, EVER, ASK -- stops being a sentence and becomes a required
argument.

It is a SPEED BUMP AND NOT A WALL: the DM could type a declaration the player
never made. So could he log a move `party.py` never routed. That tool has held
for two expeditions anyway, because the friction lands at the exact instant of
the error, and that is the whole mechanism.

MONSTER HIT POINTS LIVE HERE AND NOWHERE ELSE, and `--hidden` keeps them out of
any report the player might read. Character damage stays in `hp_log.tsv`; this
file is the monsters' side and the round's bookkeeping.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, header_of, read_tsv, today             # noqa: E402
import loops as loopmod                                           # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'encounter.tsv')

VERBS = ('start', 'surprise', 'initiative', 'declare', 'attack', 'damage',
         'hold', 'move', 'morale', 'flee', 'dead', 'end')
SIDES = ('party', 'monsters', '')


def rows(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def current(log=None):
    """The fight as it stands, or None if none is in progress.

    Everything here is recomputed from the log on every call. Nothing about a
    live fight is stored, so nothing about a live fight can be remembered wrong.
    """
    log = log if log is not None else rows()
    started = None
    for r in log:
        v = (r.get('verb') or '').strip()
        if v == 'start':
            started = []
        if started is not None:
            started.append(r)
        if v == 'end':
            started = None
    if not started:
        return None

    rnd = max((_int(r.get('round')) for r in started), default=0)
    declared, held, damage, gone = {}, set(), {}, set()
    for r in started:
        v = (r.get('verb') or '').strip()
        actor = (r.get('actor') or '').strip()
        if v == 'declare' and _int(r.get('round')) == rnd:
            declared[actor] = r.get('detail', '')
        if v == 'hold' and _int(r.get('round')) == rnd:
            held.add(actor)
            declared[actor] = 'HELD: ' + r.get('detail', '')
        if v == 'damage':
            tgt = (r.get('target') or actor).strip()
            damage[tgt] = damage.get(tgt, 0) + _int(r.get('qty'))
        if v in ('dead', 'flee'):
            gone.add(actor)
    return dict(rows=started, round=rnd, declared=declared, held=held,
                damage=damage, gone=gone,
                exped=next((r.get('exped') for r in started if r.get('exped')),
                           ''),
                day=next((r.get('day') for r in started if r.get('day')), ''),
                detail=started[0].get('detail', ''))


def undeclared(names, log=None):
    """Which of `names` have NOT said what they are doing this round."""
    st = current(log)
    if st is None:
        return list(names)
    return [n for n in names if n not in st['declared']]


def report(log=None, hidden=False):
    st = current(log)
    if st is None:
        return 'no fight in progress'
    out = ['FIGHT -- expedition %s, day %s, ROUND %s'
           % (st['exped'], st['day'], st['round']), '  %s' % st['detail'], '']
    if st['declared']:
        out.append('declared this round:')
        for who in sorted(st['declared']):
            out.append('  %-10s %s' % (who, st['declared'][who]))
    else:
        out.append('*** NOTHING DECLARED THIS ROUND. ASK. ***')
    if st['gone']:
        out.append('')
        out.append('out of the fight: %s' % ', '.join(sorted(st['gone'])))
    if hidden and st['damage']:
        out.append('')
        out.append('DM ONLY -- damage dealt to monsters:')
        for tgt, n in sorted(st['damage'].items()):
            out.append('  %-10s %d' % (tgt, n))
    return '\n'.join(out)


def write(path, row):
    """Append at the file's full width, so no field can shift left."""
    return append(path, {c: row.get(c, '') for c in header_of(path)})


def build_parser():
    p = argparse.ArgumentParser(
        prog='encounter.py', description='The live fight, computed.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--round', type=int, help='report a particular round')
    p.add_argument('--hidden', action='store_true',
                   help='include monster hit points. DM ONLY')
    sub = p.add_subparsers(dest='cmd')

    s = sub.add_parser('start', help='a fight begins')
    s.add_argument('--detail', required=True, help='where, and what was met')
    s.add_argument('--exped', default='')
    s.add_argument('--day', type=int)

    d = sub.add_parser('declare', help='WHAT THE PLAYER SAID A CHARACTER DOES')
    d.add_argument('actor')
    d.add_argument('detail', help='in the player\'s own words where possible')

    h = sub.add_parser('hold', help='an action deliberately held')
    h.add_argument('actor')
    h.add_argument('--detail', default='')

    dm = sub.add_parser('damage', help='hit points off a MONSTER')
    dm.add_argument('target')
    dm.add_argument('qty', type=int)
    dm.add_argument('--detail', default='')

    for verb in ('surprise', 'initiative', 'move', 'morale', 'flee', 'dead'):
        v = sub.add_parser(verb)
        v.add_argument('actor', nargs='?', default='')
        v.add_argument('--detail', default='')
        v.add_argument('--side', default='')

    sub.add_parser('next', help='advance one round')
    e = sub.add_parser('end', help='the fight is over')
    e.add_argument('--detail', required=True, help='the outcome')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)
    st = current(log)

    if a.cmd is None:
        print(report(log, hidden=a.hidden))
        return 0

    if a.cmd == 'start':
        if st is not None:
            print('a fight is ALREADY in progress at round %d. End it first, '
                  'or the two will be read as one.' % st['round'])
            return 1
        write(a.log_file, dict(when=today(), day=a.day or loopmod.current_day(),
                               exped=a.exped, round=1, verb='start',
                               detail=a.detail))
        print(report(rows(a.log_file)))
        return 0

    if st is None:
        print('no fight in progress. `encounter.py start --detail "..."` first.')
        return 1

    rnd = st['round']
    if a.cmd == 'next':
        write(a.log_file, dict(when=today(), day=st['day'], exped=st['exped'],
                               round=rnd + 1, verb='initiative',
                               detail='round %d begins' % (rnd + 1)))
        print('round %d. NOTHING IS DECLARED. ASK BEFORE ROLLING ANYTHING.'
              % (rnd + 1))
        return 0

    if a.cmd == 'end':
        write(a.log_file, dict(when=today(), day=st['day'], exped=st['exped'],
                               round=rnd, verb='end', detail=a.detail))
        print('fight ended at round %d: %s' % (rnd, a.detail))
        return 0

    row = dict(when=today(), day=st['day'], exped=st['exped'], round=rnd,
               verb=a.cmd, actor=getattr(a, 'actor', ''),
               detail=getattr(a, 'detail', ''),
               side=getattr(a, 'side', ''))
    if a.cmd == 'declare':
        row['side'] = 'party'
    if a.cmd == 'damage':
        row.update(target=a.target, qty=a.qty, side='monsters')
    write(a.log_file, row)
    print(report(rows(a.log_file), hidden=a.hidden))
    return 0


if __name__ == '__main__':
    sys.exit(main())
