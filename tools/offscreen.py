#!/usr/bin/env python3
"""Offscreen agendas -- what the NPCs do while the party is somewhere else.

    python tools/offscreen.py status
    python tools/offscreen.py tick [--to DAY]
    python tools/offscreen.py news --who Wend
    python tools/offscreen.py deliver --who Wend [--day N]
    python tools/offscreen.py open --who wend --loop L043 --task "..." \\
        --table "d6|1-2=progress:...|3-6=hold:..." --cadence 7 --ceiling 8

**WHY THIS EXISTS.** `loops.tsv` records things that will one day close, but a
loop only moved when the PARTY asked about it. Wend's queue sat at OVERDUE 90
and OVERDUE 110 while the party was at the crag for two weeks, because the only
rolls that ever advanced her letters were the ones made when somebody happened
to say her name. An NPC who does nothing until asked is not a person, and the
player said so on day 135.

**THE SHAPE.** An *agenda* is one NPC task on a fixed cadence (weekly, by the
player's word) with its outcome table WRITTEN DOWN BEFORE the first roll, which
is the same discipline as "declared first" everywhere else here. A *tick* is one
turn of it: the campaign day has reached (opening day + n * cadence) and a die
is rolled, written to `campaign/rolls.tsv` by `dice.py` like every other roll,
and the outcome is appended to `campaign/offscreen.tsv`.

**HIDDEN UNTIL MET.** The player's ruling: *record the rolls, but do not show
me until, if or when it is relevant.* So `tick` prints only a COUNT. The results
are read with `news`, which is what to run when the party meets or writes to the
person, and `deliver` marks them told. `log.py day` runs `tick` on every new
campaign day, which is the guarantee that a day cannot open without the queue
catching up; `brief.py` says how many ticks are owed and how much news is
waiting, never what it is.

**IT IS APPEND-ONLY.** `agendas.tsv` and `offscreen.tsv` hold events; what is
active, how many ticks have run, when the next is due and what has been
delivered are all DERIVED, so there is no cell to go stale. Running `tick` twice
in a day does nothing the second time.

Table syntax: `d6|1-2=progress:text|3-4=hold:text|5-6=resolve:text`, where the
kind is `progress` (something moved), `hold` (nothing yet), `resolve` (done: the
agenda closes itself) or `due` (a fixed obligation). A table beginning `auto|`
has no die: `auto|due:text` fires every time it is due.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, read_tsv                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENDAS = os.path.join(ROOT, 'campaign', 'agendas.tsv')
TICKS = os.path.join(ROOT, 'campaign', 'offscreen.tsv')
DAYS = os.path.join(ROOT, 'campaign', 'days.tsv')
LOOPS = os.path.join(ROOT, 'campaign', 'loops.tsv')
PEOPLE = os.path.join(ROOT, 'campaign', 'people.tsv')

KINDS = ('progress', 'hold', 'resolve', 'due')
ACTIVE = ('open', 'resume')


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def current_day(path=None):
    days = [int(r['day']) for r in read_tsv(path or DAYS, missing_ok=True)
            if r.get('day', '').strip().isdigit()]
    return max(days) if days else None


def agendas(rows=None, path=None):
    """{id: merged row} for the latest state of each agenda, in file order."""
    rows = rows if rows is not None else read_tsv(path or AGENDAS,
                                                   missing_ok=True)
    out = {}
    for r in rows:
        aid = r.get('id', '').strip()
        if not aid:
            continue
        prev = out.get(aid, {})
        merged = dict(prev)
        for k, v in r.items():
            if v.strip() or k not in merged:
                merged[k] = v
        if 'opened' not in merged or r.get('action', '').strip() == 'open':
            merged['opened'] = r.get('day', '').strip()
        out[aid] = merged
    return out


def ticks(rows=None, path=None):
    """{agenda_id: [tick rows in order]} -- the `tick` rows only."""
    rows = rows if rows is not None else read_tsv(path or TICKS,
                                                   missing_ok=True)
    out = {}
    for r in rows:
        if r.get('action', '').strip() == 'tick':
            out.setdefault(r['agenda'].strip(), []).append(r)
    return out


def delivered(rows=None, path=None):
    """Set of (agenda, tick number) already told to the party."""
    rows = rows if rows is not None else read_tsv(path or TICKS,
                                                   missing_ok=True)
    return {(r['agenda'].strip(), r['tick'].strip()) for r in rows
            if r.get('action', '').strip() == 'deliver'}


def parse_table(text):
    """('d6', [(lo, hi, kind, news), ...]) or ('auto', [(1, 1, kind, news)])."""
    parts = [p.strip() for p in (text or '').split('|') if p.strip()]
    if not parts:
        raise ValueError('an agenda needs a table')
    head = parts[0].lower()
    out = []
    if head == 'auto':
        for seg in parts[1:]:
            kind, _, news = seg.partition(':')
            out.append((1, 1, kind.strip(), news.strip()))
        if len(out) != 1:
            raise ValueError('an auto table has exactly one outcome')
    else:
        if not re.fullmatch(r'd\d+', head):
            raise ValueError('a table starts with dN or auto, not %r' % head)
        for seg in parts[1:]:
            m = re.match(r'(\d+)(?:-(\d+))?=(\w+):(.*)$', seg)
            if not m:
                raise ValueError('cannot read outcome %r' % seg)
            lo = int(m.group(1))
            hi = int(m.group(2) or m.group(1))
            out.append((lo, hi, m.group(3).strip(), m.group(4).strip()))
        sides = int(head[1:])
        faces = [f for lo, hi, _, _ in out for f in range(lo, hi + 1)]
        if sorted(faces) != list(range(1, sides + 1)):
            raise ValueError('the table does not cover 1..%d exactly once '
                             'each' % sides)
    for _, _, kind, _ in out:
        if kind not in KINDS:
            raise ValueError('kind %r is not one of %s'
                             % (kind, ', '.join(KINDS)))
    return head, out


def outcome(table, roll):
    head, rows = parse_table(table)
    for lo, hi, kind, news in rows:
        if lo <= roll <= hi:
            return kind, news
    raise ValueError('roll %r falls outside the table' % roll)


def is_active(a):
    return a.get('action', '').strip() in ACTIVE


def next_due(agenda, agenda_ticks):
    """Day the next tick falls due, or None if the agenda is at its ceiling."""
    ceiling = int(agenda.get('ceiling') or 0)
    n = len(agenda_ticks)
    if ceiling and n >= ceiling:
        return None
    base = int(agenda_ticks[-1]['day']) if agenda_ticks \
        else int(agenda['opened'])
    return base + int(agenda.get('cadence') or 7)


def owed(upto=None, ag=None, tk=None):
    """[(agenda id, day due)] for every tick that has come due but not run."""
    upto = upto if upto is not None else current_day()
    ag = ag if ag is not None else agendas()
    tk = tk if tk is not None else ticks()
    out = []
    for aid, a in ag.items():
        if not is_active(a):
            continue
        mine = list(tk.get(aid, []))
        while True:
            d = next_due(a, mine)
            if d is None or d > upto:
                break
            out.append((aid, d))
            mine.append({'day': str(d)})
    return out


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def _roll_default(notation, reason):
    import dice
    return int(dice.roll(notation, reason=reason))


def tick(upto=None, roller=None, agenda_path=None, tick_path=None):
    """Roll every tick that has come due. Returns the number rolled.

    Prints nothing about WHAT came up: that is `news`, read when the party
    meets the person. Idempotent -- a second call the same day finds nothing
    owed.
    """
    roller = roller or _roll_default
    agenda_path = agenda_path or AGENDAS
    tick_path = tick_path or TICKS
    upto = upto if upto is not None else current_day()
    rolled = 0
    while True:
        ag = agendas(path=agenda_path)
        tk = ticks(path=tick_path)
        due = owed(upto, ag, tk)
        if not due:
            return rolled
        # one tick at a time so a `resolve` closes its agenda before the next
        aid, day = sorted(due, key=lambda x: (x[1], x[0]))[0]
        a = ag[aid]
        n = len(tk.get(aid, [])) + 1
        head, _ = parse_table(a['table'])
        if head == 'auto':
            r = 1
        else:
            r = roller(head, 'OFFSCREEN %s tick %d, day %d: %s (%s). DECLARED '
                             'FIRST, in agendas.tsv: %s'
                       % (aid, n, day, a.get('task', '')[:70],
                          a.get('who', ''), a['table'][:400]))
        kind, news = outcome(a['table'], r)
        append(tick_path, dict(day=day, agenda=aid, tick=n, action='tick',
                               roll=r if head != 'auto' else '', kind=kind,
                               news=news))
        rolled += 1
        if kind == 'resolve':
            append(agenda_path, dict(day=day, id=aid, action='close',
                                     note='resolved by its own tick %d' % n))


def deliver(who=None, agenda_ids=None, day=None, tick_path=None,
            agenda_path=None):
    """Mark waiting news told. Returns the number of ticks delivered."""
    tick_path = tick_path or TICKS
    day = day if day is not None else current_day()
    n = 0
    for r in waiting(who, tick_path=tick_path, agenda_path=agenda_path,
                     agenda_ids=agenda_ids):
        append(tick_path, dict(day=r['day'], agenda=r['agenda'],
                               tick=r['tick'], action='deliver',
                               delivered_day=day))
        n += 1
    return n


def waiting(who=None, tick_path=None, agenda_path=None, agenda_ids=None):
    """Undelivered tick rows, optionally for one person or set of agendas."""
    ag = agendas(path=agenda_path)
    rows = read_tsv(tick_path or TICKS, missing_ok=True)
    told = delivered(rows)
    out = []
    for r in rows:
        if r.get('action', '').strip() != 'tick':
            continue
        if (r['agenda'].strip(), r['tick'].strip()) in told:
            continue
        a = ag.get(r['agenda'].strip(), {})
        if who and a.get('who', '').strip().lower() != who.strip().lower():
            continue
        if agenda_ids and r['agenda'].strip() not in agenda_ids:
            continue
        out.append(r)
    return out


def news_text(names, tick_path=None, agenda_path=None):
    """The undelivered news for each name, as text for a briefing."""
    ag = agendas(path=agenda_path)
    lines = []
    for name in [n.strip() for n in names.split(',') if n.strip()]:
        for r in waiting(name, tick_path=tick_path, agenda_path=agenda_path):
            a = ag.get(r['agenda'], {})
            lines.append('  %s  %s tick %s (day %s) [%s] %s   -- %s'
                         % (r['agenda'], a.get('loop', ''), r['tick'],
                            r['day'], r['kind'], r['news'],
                            a.get('task', '')[:60]))
    return '\n'.join(lines) if lines else '  no offscreen news waiting'


def owed_count(upto=None):
    return len(owed(upto))


def news_summary():
    """{who: number of undelivered ticks} -- counts only, never content."""
    ag = agendas()
    out = {}
    for r in waiting():
        who = ag.get(r['agenda'], {}).get('who', '?')
        out[who] = out.get(who, 0) + 1
    return out


# --------------------------------------------------------------------------
# checks and the CLI
# --------------------------------------------------------------------------

def check():
    problems = []
    loop_ids = {r.get('loop', '').strip() for r in
                read_tsv(LOOPS, missing_ok=True)}
    people = {r['id'].strip().lower() for r in
              read_tsv(PEOPLE, missing_ok=True)}
    for aid, a in agendas().items():
        if not is_active(a):
            continue
        if a.get('loop') and a['loop'].strip() not in loop_ids:
            problems.append(('FAIL', '%s: loop %s is not in loops.tsv'
                             % (aid, a['loop'])))
        if a.get('who', '').strip().lower() not in people:
            problems.append(('FAIL', '%s: %r is not a people.tsv id'
                             % (aid, a.get('who'))))
        try:
            parse_table(a['table'])
        except ValueError as e:
            problems.append(('FAIL', '%s: %s' % (aid, e)))
    return problems


def status():
    ag = agendas()
    tk = ticks()
    told = delivered()
    lines = ['agenda  who      loop   state   ticks  next   waiting  task']
    day = current_day()
    for aid, a in ag.items():
        mine = tk.get(aid, [])
        nd = next_due(a, mine)
        w = sum(1 for r in mine if (aid, r['tick'].strip()) not in told)
        lines.append('%-7s %-8s %-6s %-7s %-6s %-6s %-8s %s'
                     % (aid, a.get('who', ''), a.get('loop', ''),
                        'active' if is_active(a) else a.get('action', ''),
                        '%d/%s' % (len(mine), a.get('ceiling') or '-'),
                        nd if nd is not None else '-', w,
                        a.get('task', '')[:60]))
    lines.append('')
    lines.append('day %s: %d tick(s) owed' % (day, owed_count(day)))
    return '\n'.join(lines)


def _next_id(path=None):
    ids = [int(re.sub(r'\D', '', r['id']) or 0)
           for r in read_tsv(path or AGENDAS, missing_ok=True)]
    return 'A%03d' % (max(ids + [0]) + 1)


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('status', help='every agenda, its next tick, what waits')
    t = sub.add_parser('tick', help='roll every tick that has come due')
    t.add_argument('--to', type=int)
    n = sub.add_parser('news', help='the undelivered news (read when met)')
    n.add_argument('--who')
    d = sub.add_parser('deliver', help='mark news told')
    d.add_argument('--who', required=True)
    d.add_argument('--day', type=int)
    o = sub.add_parser('open', help='start an agenda')
    o.add_argument('--who', required=True)
    o.add_argument('--loop', default='')
    o.add_argument('--task', required=True)
    o.add_argument('--table', required=True)
    o.add_argument('--cadence', type=int, default=7)
    o.add_argument('--ceiling', type=int, default=8)
    o.add_argument('--day', type=int)
    for verb in ('pause', 'resume', 'close'):
        c = sub.add_parser(verb)
        c.add_argument('agenda')
        c.add_argument('--why', default='')
    sub.add_parser('check', help='validate every agenda')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.cmd in (None, 'status'):
        print(status())
    elif a.cmd == 'tick':
        n = tick(a.to)
        print('%d offscreen tick(s) rolled and held: hidden until met' % n)
    elif a.cmd == 'news':
        if a.who:
            print(news_text(a.who))
        else:
            for who, c in sorted(news_summary().items()):
                print('%-10s %d waiting' % (who, c))
    elif a.cmd == 'deliver':
        print('%d tick(s) delivered' % deliver(a.who, day=a.day))
    elif a.cmd == 'open':
        parse_table(a.table)
        aid = _next_id()
        day = a.day if a.day is not None else current_day()
        print(append(AGENDAS, dict(
            day=day, id=aid, action='open', who=a.who.strip().lower(),
            loop=a.loop, cadence=a.cadence, ceiling=a.ceiling, task=a.task,
            table=a.table)))
    elif a.cmd in ('pause', 'resume', 'close'):
        print(append(AGENDAS, dict(day=current_day(), id=a.agenda,
                                   action=a.cmd, note=a.why)))
    elif a.cmd == 'check':
        bad = check()
        for sev, msg in bad:
            print('%-5s %s' % (sev, msg))
        if bad:
            return 1
        print('offscreen OK: every active agenda has a loop, a person and '
              'a table that covers the die')
    return 0


if __name__ == '__main__':
    sys.exit(main())
