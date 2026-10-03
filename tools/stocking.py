#!/usr/bin/env python3
"""The stocked monster registry -- what is actually where, computed.

    python tools/stocking.py status [--level N] [--area N]
    python tools/stocking.py at LEVEL X Y
    python tools/stocking.py stock  --id troglodyte_41a --level 2 --area 41 \\
        --monster troglodyte --x 19 --y 4 --hp 10 --note "..."
    python tools/stocking.py hp     --id troglodyte_41a --hp 4 --note "..."
    python tools/stocking.py move   --id troglodyte_41a --x 19 --y 5 --note "..."
    python tools/stocking.py flee   --id troglodyte_41a --x 17 --y 3 \\
        --duration 32 --note "panicked west at the junction, d6=2"
    python tools/stocking.py die    --id troglodyte_41a --note "..."
    python tools/stocking.py simulate --id troglodyte_41a --feet-per-turn 120 \\
        --note "broke off when Torsat dropped its packmate"

**DM-ONLY, same standing as `modules/B1_DM_NOTES_DO_NOT_READ.md` and
`modules/private/b1_wandering.tsv`.** Tracked, published, never quoted to the
player, never read out of context -- what preserves the surprise is that
this tool's OUTPUT never gets pasted into a reply except through an actual
resolved encounter, exactly the discipline already kept for the DM notes.
Nothing here enforces that; it is the same trust arrangement the rest of the
module's secrets already run on.

**WHY THIS EXISTS.** B1's own stocking (`modules/B1_DM_NOTES_DO_NOT_READ.md`,
rolled once on day 1 and never re-rolled) lived only as prose -- a table of
what a room HOLDS, with nothing that tracked what happens to it after the
party meets it. A monster that fled a fight had nowhere to go on the map; the
orcs that ran west at (4,19) on level 1 and were "gone" when the party
followed forced a retcon (inventing a passage that was not there) rather
than a real answer to "where." This gives every stocked individual a
tracked, ray-cast-checkable position instead.

**APPEND-ONLY, same shape as every other campaign log.** `stock` places an
individual once, at the room's placement; `hp` records a wound (or a heal);
`move` repositions it with no time limit (a scripted, deliberate move);
`flee` repositions it WITH a limited window (see below); `die` removes it
from what `present`/`at` will ever return again. Current position, hp and
whether an individual still counts as "there" are all DERIVED by replay --
nothing is stored twice.

**THE FLEE WINDOW.** The player's ruling, day 139: a fled monster keeps
"living" off-screen for a short time, findable if the party goes there, then
"goes back into the pool of wandering monsters" -- narratively rejoining
whatever abstraction the level's own wandering table already represents, not
a mechanical change to that table's odds. `flee` records a `duration` in
ROUNDS; `present()` treats it as expired the instant the campaign DAY or the
EXPEDITION changes, or once that many rounds have passed within the same
expedition -- a short recovery window does not survive a change of day in
any way that matters, so exact round math is only needed for staying within
one expedition's clock.

**GENERAL-PURPOSE, not flee-specific.** `move`/`flee`/`hp` apply to any
stocked individual, not only ones running from the party -- a wounded
creature that limps off, a patrol repositioned by DM judgement, anything.

**`simulate` is the dice-driven mover, also general-purpose.** Give it an
individual and its own move rate (from `bestiary/`, the DM's to supply --
this does not look it up) and it walks the REAL map from wherever that
individual currently is: `dmap.random_walk` picks uniformly at random among
the walkable exits at every junction (excluding only the square just left,
same as a panicked animal not doubling straight back), for a dice-rolled
1d3 turns at that move rate, stopping early at a dead end. It then rolls the
linger window (5+1d4 turns) and records the whole thing as one `flee`
event -- built for exactly the case that forced a retcon once already, the
orcs that ran from (4,19) on level 1 and were simply "gone" when the party
followed, because there was nowhere real on the map for them to have gone.
Not limited to actual flight -- anything that needs a real, dice-decided
position can use it. Ambient, UNDISTURBED movement (a monster wandering its
home area on no particular schedule, with nothing having provoked it) is
deliberately NOT built here yet; an untouched individual stays exactly
where `stock` put it until some event -- a `simulate` among them -- moves it.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, read_tsv, today                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'modules', 'private', 'b1_stocking.tsv')
B1_DB = os.path.join(ROOT, 'mapdb', 'output', 'b1', 'b1.sqlite')
sys.path.insert(0, os.path.join(ROOT, 'mapdb'))  # for `import dmap`

VERBS = ('stock', 'hp', 'move', 'flee', 'die')


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def rows(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def state(rows_=None, path=None):
    """{monster_id: {level, area, monster, x, y, hp, alive, flee_at}} --
    every individual's CURRENT computed state, replaying events in file
    order. `flee_at` is (day, exped, round, duration) for the most recent
    `flee`, or None if it is not currently fled (a later `move`/`hp` clears
    it -- the individual has settled, not just paused mid-flight)."""
    rows_ = rows_ if rows_ is not None else rows(path)
    out = {}
    for r in rows_:
        mid = (r.get('monster_id') or '').strip()
        verb = (r.get('verb') or '').strip()
        if not mid or verb not in VERBS:
            continue
        cur = out.setdefault(mid, {
            'level': None, 'area': None, 'monster': None,
            'x': None, 'y': None, 'hp': None, 'alive': True, 'flee_at': None,
        })
        if verb == 'stock':
            cur['level'] = int(r['level'])
            cur['area'] = (r.get('area') or '').strip()
            cur['monster'] = (r.get('monster') or '').strip()
            cur['x'], cur['y'] = int(r['x']), int(r['y'])
            cur['hp'] = float(r['hp']) if r.get('hp') else None
            cur['alive'], cur['flee_at'] = True, None
        elif verb == 'hp':
            cur['hp'] = float(r['hp']) if r.get('hp') else cur['hp']
        elif verb == 'move':
            cur['x'], cur['y'] = int(r['x']), int(r['y'])
            cur['flee_at'] = None
        elif verb == 'flee':
            cur['x'], cur['y'] = int(r['x']), int(r['y'])
            try:
                exped = int(r.get('exped') or 0)
            except ValueError:
                exped = 0
            cur['flee_at'] = (int(r.get('day') or 0), exped,
                              int(r.get('round') or 0),
                              int(r.get('duration') or 0))
        elif verb == 'die':
            cur['alive'] = False
    return out


def _fled_expired(flee_at, now):
    """`now` is (day, exped, round). A flee window does not survive a
    change of day or expedition -- see the module docstring -- only exact
    round math within the SAME expedition matters."""
    if flee_at is None:
        return False
    fday, fexped, fround, duration = flee_at
    day, exped, rnd = now
    if day != fday or exped != fexped:
        return True
    return rnd - fround >= duration


def present(level, now=None, rows_=None, path=None):
    """{monster_id: state} -- everyone currently ALIVE and not an expired
    flee, on this level. `now` is (day, exped, round); omit it and every
    flee is treated as still active (useful for a DM-side listing where the
    clock does not matter, e.g. `status`)."""
    out = {}
    for mid, s in state(rows_, path).items():
        if s['level'] != level or not s['alive']:
            continue
        if now is not None and _fled_expired(s['flee_at'], now):
            continue
        out[mid] = s
    return out


def at(level, x, y, now=None, rows_=None, path=None):
    """[monster_id] present at exactly this cell right now."""
    return sorted(mid for mid, s in present(level, now, rows_, path).items()
                  if (s['x'], s['y']) == (x, y))


def scan_squares(db, level, squares, radius=3, now=None):
    """Walk `squares` IN ORDER (a move, or a single [cell] for a look-around)
    and report, for each one, what FIRST comes into range there -- stocked
    monsters, doors/secrets, and feature tags -- that was not already in
    range from an earlier square in the list.

    THE WHOLE POINT: a single `at`/`light` call on the destination of a
    multi-square move misses anything that came into range partway there
    (day 140 -- the same door-visibility bug, and the same bug again one
    stop later for a stocked sighting mid-move, not just at the endpoint).
    Call this with the full list of squares a move actually passes through,
    not just the last one, and stop the move at the first square that
    reports something.

    Returns a list of (square, kind, detail) tuples, in the order squares
    were walked -- kind is 'monster', 'door', 'secret' or 'feature'.
    """
    sys.path.insert(0, os.path.join(ROOT, 'mapdb'))
    import dmap
    cells, edges = dmap.load(db, level)
    seen_monsters = set()
    seen_edges = set()
    seen_features = set()
    findings = []
    for sq in squares:
        lit = dmap.light_reach(db, level, sq[0], sq[1], radius=radius)
        lit = set(lit.keys()) if isinstance(lit, dict) else set(lit)
        here = present(level, now)
        for mid, s in sorted(here.items()):
            if (s['x'], s['y']) in lit and mid not in seen_monsters:
                seen_monsters.add(mid)
                findings.append((sq, 'monster',
                                 '%s at (%s,%s)' % (mid, s['x'], s['y'])))
        for c in sorted(lit):
            feat = cells.get(c, ('?', None, None, None))[2]
            if feat and (c, feat) not in seen_features:
                seen_features.add((c, feat))
                findings.append((sq, 'feature', '%s at %s' % (feat, c)))
            for d, dx, dy, ef in dmap.DIRS:
                key = ef(*c)
                val = edges.get(key)
                if val in ('door', 'secret') and key not in seen_edges:
                    seen_edges.add(key)
                    findings.append((sq, val,
                                     '%s facing %s from %s' % (val, d, c)))
    return findings


def current_now(clock_log=None, days_log=None):
    """(day, exped, round) off the real clock and day logs -- what a CLI
    caller passes to `present`/`at`. Kept out of the pure functions above so
    they stay testable without a live campaign state."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import clock as clockmod
    import offscreen as offmod
    exped, rnd, _jitter, _fired = clockmod.state(
        clockmod.load(clock_log) if clock_log else None)
    day = offmod.current_day(days_log)
    return day, (int(exped) if exped is not None else None), rnd


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def record(monster_id, verb, level=None, area=None, monster=None,
           x=None, y=None, hp=None, duration=None, note='',
           day=None, exped=None, rnd=None, path=None):
    if verb not in VERBS:
        raise ValueError('verb must be one of %s, got %r' % (VERBS, verb))
    if verb == 'stock' and (level is None or x is None or y is None
                            or hp is None or not monster):
        raise ValueError('stock needs level, monster, x, y and hp')
    if verb in ('move', 'flee') and (x is None or y is None):
        raise ValueError('%s needs x and y' % verb)
    if verb == 'flee' and not duration:
        raise ValueError('flee needs a --duration (rounds the window lasts)')
    row = {'when': today(), 'day': day or '', 'level': level or '',
           'area': area or '', 'monster_id': monster_id, 'monster': monster or '',
           'verb': verb, 'x': x if x is not None else '',
           'y': y if y is not None else '', 'hp': hp if hp is not None else '',
           'exped': exped or '', 'round': rnd if rnd is not None else '',
           'duration': duration or '', 'note': note}
    return append(path or LOG, row)


# --------------------------------------------------------------------------
# movement -- general-purpose, not flee-specific; walks ANY stocked
# individual across the real map with the dice deciding every junction
# --------------------------------------------------------------------------

def _default_roller():
    import dice as dicemod
    return lambda notation, reason: dicemod.roll(notation, reason=reason).total


def random_walk(cells, edges, start, feet_budget, roller):
    """A dice-driven walk from `start`: at every step, choose uniformly at
    random among the walkable, non-backtrack exits (excluding only the
    square just left, same as a panicked animal not doubling straight back
    on itself) and take it, until the feet budget runs out or a dead end is
    reached. A single-exit step is not rolled -- there is no real choice in
    it, same reasoning `dmap.walk_until` uses for the party.

    Returns (end_cell, path, feet_used, reason) -- `reason` is 'dead_end' or
    'budget'. `roller(notation, reason) -> int` is `dice.roll(...).total` by
    default, swappable for tests."""
    import dmap
    path = [start]
    came_from, cur, feet_used = None, start, 0
    while feet_used < feet_budget:
        options = [(d, n) for d, n in dmap.exits(cur, edges, came_from)
                  if n in cells and cells[n][0] in dmap.WALKABLE]
        if not options:
            return cur, path, feet_used, 'dead_end'
        if len(options) == 1:
            pick = options[0]
        else:
            i = roller('d%d' % len(options),
                      'panicked flight: %d-way choice at (%d,%d)'
                      % (len(options), *cur))
            pick = options[max(1, min(len(options), i)) - 1]
        came_from, cur = cur, pick[1]
        path.append(cur)
        feet_used += dmap.FEET_PER_SQUARE
    return cur, path, feet_used, 'budget'


def simulate_flee(monster_id, feet_per_turn, db=None, day=None, exped=None,
                  rnd=None, roller=None, note='', path=None,
                  duration_die='d3', linger_base_turns=5,
                  linger_jitter_die='d4'):
    """Simulate one stocked, live individual bolting from wherever it
    currently is: a dice-rolled number of turns (default 1d3) of panicked,
    dice-driven movement at its OWN move rate (`feet_per_turn` -- the DM's
    to supply, from its bestiary entry; not looked up here), stopping early
    at a dead end. Then a dice-rolled LINGER window (default 5 + 1d4 turns)
    during which it is genuinely findable at the cell it stopped at, before
    the `flee` event's own expiry logic (see `_fled_expired`) retires it.

    Built for exactly the case that forced a retcon once already: orcs that
    ran from (4,19) on level 1 and were simply "gone" when the party
    followed, because there was nowhere real on the map for them to have
    gone. This walks the real graph, so wherever it ends up is a real,
    reachable square.

    Records a `flee` event and returns a human-readable report. Raises if
    the individual is unknown or already dead."""
    import dmap
    roller = roller or _default_roller()
    cur = state(path=path).get(monster_id)
    if cur is None or not cur['alive']:
        raise ValueError('%s is not a known, live, stocked individual'
                         % monster_id)
    cells, edges = dmap.load(db or B1_DB, cur['level'])
    turns = roller(duration_die, '%s panics: how many turns it flees'
                                 % monster_id)
    end, walked, feet_used, reason = random_walk(
        cells, edges, (cur['x'], cur['y']), turns * feet_per_turn, roller)
    jitter = roller(linger_jitter_die,
                    '%s: linger window jitter' % monster_id)
    linger_rounds = (linger_base_turns + jitter) * 10
    full_note = ('%s. ' % note if note else '') + (
        'fled %d turn(s) (%d ft) at %d ft/turn, stopped by %s at (%d,%d); '
        '%d-round linger window (5+%d turns); path %s'
        % (turns, feet_used, feet_per_turn, reason, end[0], end[1],
           linger_rounds, jitter, walked))
    record(monster_id, 'flee', x=end[0], y=end[1], duration=linger_rounds,
          day=day, exped=exped, rnd=rnd, note=full_note, path=path)
    return ('%s flees %d turn(s) (%d ft), stops (%s) at (%d,%d). Findable '
           'there for %d more round(s) of this expedition, this day.'
           % (monster_id, turns, feet_used, reason, end[0], end[1],
              linger_rounds))


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def status_report(level=None, area=None, rows_=None, path=None):
    st = state(rows_, path)
    out = []
    for mid in sorted(st):
        s = st[mid]
        if level is not None and s['level'] != level:
            continue
        if area is not None and s['area'] != str(area):
            continue
        tag = 'DEAD' if not s['alive'] else (
            'FLED (expires-aware only via --now)' if s['flee_at'] else 'present')
        out.append('%-20s L%s area %-4s %-16s (%s,%s) hp %s  %s'
                   % (mid, s['level'], s['area'], s['monster'] or '?',
                      s['x'], s['y'], s['hp'], tag))
    return '\n'.join(out) if out else '(nothing recorded)'


def build_parser():
    p = argparse.ArgumentParser(prog='stocking.py',
                                description='The stocked monster registry.')
    sub = p.add_subparsers(dest='cmd', required=True)

    st = sub.add_parser('status', help="everyone's current computed state")
    st.add_argument('--level', type=int)
    st.add_argument('--area')

    at_p = sub.add_parser('at', help='who is at exactly this cell now')
    at_p.add_argument('level', type=int)
    at_p.add_argument('x', type=int)
    at_p.add_argument('y', type=int)
    at_p.add_argument('--ignore-clock', action='store_true',
                      help='do not expire flee windows against the real clock')

    sc = sub.add_parser('scan', help='walk a planned move square by square '
                         'and report the FIRST square from which anything '
                         '(a stocked monster, a door, a feature) comes into '
                         'range -- use this for every multi-square move and '
                         'every look-around, not `at`/`light` on just the '
                         'destination')
    sc.add_argument('--db', required=True)
    sc.add_argument('level', type=int)
    sc.add_argument('--path', nargs='+', required=True, metavar='X,Y',
                    help='every square the move actually passes through, '
                         'in order, starting with the first one after the '
                         'current position (a single X,Y for a look-around)')
    sc.add_argument('--radius', type=int, default=3,
                    help='cells (10 ft each); 3 = lamp, 6 = infravision')
    sc.add_argument('--ignore-clock', action='store_true')

    def common_write(name, help_):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument('--id', dest='monster_id', required=True)
        sp.add_argument('--note', default='')
        sp.add_argument('--day', type=int)
        return sp

    sk = common_write('stock', 'place an individual for the first time')
    sk.add_argument('--level', type=int, required=True)
    sk.add_argument('--area', required=True)
    sk.add_argument('--monster', required=True)
    sk.add_argument('--x', type=int, required=True)
    sk.add_argument('--y', type=int, required=True)
    sk.add_argument('--hp', type=float, required=True)

    hp = common_write('hp', 'record a wound or a heal')
    hp.add_argument('--hp', type=float, required=True)

    mv = common_write('move', 'reposition, no time limit')
    mv.add_argument('--x', type=int, required=True)
    mv.add_argument('--y', type=int, required=True)

    fl = common_write('flee', 'reposition with a limited findable window')
    fl.add_argument('--x', type=int, required=True)
    fl.add_argument('--y', type=int, required=True)
    fl.add_argument('--duration', type=int, required=True,
                    help='rounds the flee window lasts')

    common_write('die', 'remove from what present()/at() will ever return')

    sm = sub.add_parser('simulate', help='dice-driven flight from wherever '
                        'this individual currently is, walking the real map')
    sm.add_argument('--id', dest='monster_id', required=True)
    sm.add_argument('--feet-per-turn', type=int, required=True,
                    help="the creature's own MV, from its bestiary entry")
    sm.add_argument('--note', default='')
    sm.add_argument('--day', type=int)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.cmd == 'status':
        print(status_report(a.level, a.area))
        return 0
    if a.cmd == 'at':
        now = None if a.ignore_clock else current_now()
        found = at(a.level, a.x, a.y, now)
        print(', '.join(found) if found else '(nobody there)')
        return 0
    if a.cmd == 'scan':
        now = None if a.ignore_clock else current_now()
        squares = [tuple(int(v) for v in sq.split(',')) for sq in a.path]
        findings = scan_squares(a.db, a.level, squares, a.radius, now)
        if not findings:
            print('nothing new the whole way -- clean')
            return 0
        for sq, kind, detail in findings:
            print('%-10s %-8s %s' % (str(sq), kind.upper(), detail))
        return 0
    if a.cmd == 'simulate':
        day, exped, rnd = current_now()
        if a.day:
            day = a.day
        print(simulate_flee(a.monster_id, a.feet_per_turn, day=day,
                            exped=exped, rnd=rnd, note=a.note))
        return 0
    day, exped, rnd = (None, None, None)
    if a.cmd in ('stock', 'move', 'flee'):
        day, exped, rnd = current_now()
        if a.day:
            day = a.day
    kwargs = dict(vars(a))
    kwargs.pop('cmd')
    verb = a.cmd
    record(monster_id=kwargs.pop('monster_id'), verb=verb,
          level=kwargs.pop('level', None), area=kwargs.pop('area', None),
          monster=kwargs.pop('monster', None), x=kwargs.pop('x', None),
          y=kwargs.pop('y', None), hp=kwargs.pop('hp', None),
          duration=kwargs.pop('duration', None), note=kwargs.pop('note', ''),
          day=day, exped=exped, rnd=rnd)
    print('%s recorded for %s' % (verb, a.monster_id))
    return 0


if __name__ == '__main__':
    sys.exit(main())
