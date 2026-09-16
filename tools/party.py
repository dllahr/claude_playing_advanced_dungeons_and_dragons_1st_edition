#!/usr/bin/env python3
"""Where the party is, and the only legal way to move it.

    python tools/party.py where
    python tools/party.py move --to 20,7 --why "north to the three-way"
    python tools/party.py move --to 20,7 --rate known
    python tools/party.py place --at 16,1 --why "entered the dungeon"
    python tools/party.py trail --last 10

Why this exists
---------------
The party's position used to live only in the DM's prose, which meant nothing
could check a move. On expedition 4, round 1111, the party was walked from
(19,5) to (19,6) -- straight through a wall that the query output had printed
on screen a moment earlier -- and given a corridor opening that does not exist.
The player caught it by reading the printed map.

`mapdb/dmap.py path` physically cannot route through a wall. It reproduced the
correct route first try. The tool that cannot make the mistake existed; it just
was not in the loop.

So position is now DATA, in `campaign/party.tsv`, and `move` is the only thing
that changes it. A move to an unreachable square RAISES rather than narrating.
This converts "remember to check the map" into "cannot be got wrong".

`place` exists for the start of an expedition and for teleports and falls --
anything that legitimately puts the party somewhere without walking. It is
deliberately a separate verb so that skipping the check is always explicit.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mapdb'))
from tsvlog import append, read_tsv, today                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# *** EDGES THE PATHFINDER MAY NOT USE -- DERIVED, NOT WRITTEN HERE. ***
#
# `move` physically cannot cross a WALL, which has held for three expeditions.
# It had no notion of a route the campaign has RULED OUT -- and on day 79 it
# proved it: asked for the four-way at (16,19), it went back through the secret
# slab and straight up x=16 from y=13 to y=19, the corridor under the magic
# mouths, which is the one stretch of level 1 this party does not walk.
#
# *** THE LIST USED TO BE A HARDCODED DICT RIGHT HERE, AND THAT WAS A SECOND
# *** COPY OF A RULE. On day 95 the player asked whether there was a tool for
# the mouth-avoiding route. There was half of one: party.py knew six edges and
# REFUSED them, `dmap path` knew nothing and happily printed the forbidden
# route, and NEITHER knew about (17,21), Kell's grave, which is the OTHER
# square a route was hand-corrected away from (exp.5, round 34).
#
# So the squares now live in campaign/avoid.tsv, ONE copy, read by both. Edges
# are derived from them: any edge leading INTO an avoided square is forbidden,
# which is the same six edges the dict used to spell out, plus the ones round
# Kell that it never had.
def _avoid_cells(map_name, level):
    """{(x, y): why} from campaign/avoid.tsv. Cached per (map, level)."""
    key = (map_name, int(level))
    if key not in _AVOID_CACHE:
        import dmap
        # avoid.tsv is not per-map today; B1 is the only live dungeon and the
        # DMG sample has no party in it. If a second map ever gets a row, give
        # the file a `map` column rather than a second file.
        _AVOID_CACHE[key] = dmap.avoid_set(level) if map_name == 'b1' else {}
    return _AVOID_CACHE[key]


_AVOID_CACHE = {}


def forbidden(map_name, level, x, y, orient):
    """Why this EDGE is ruled out, or None. Derived from the avoided squares.

    An edge is forbidden when it leads into an avoided square from outside it.
    (16,13,H) separates (16,13) from (16,14); the old dict listed six such
    edges up the mouth corridor and this reproduces them from one square.
    """
    cells = _avoid_cells(map_name, level)
    if not cells:
        return None
    x, y = int(x), int(y)
    other = (x + 1, y) if orient == 'V' else (x, y + 1)
    # AN EDGE IS FORBIDDEN IF EITHER SQUARE IT SEPARATES IS AVOIDED. That is
    # the whole rule, and it is only this simple because avoid.tsv lists the
    # mouth corridor AS A RUN -- (16,14) through (16,18) -- rather than as the
    # one square the mouths sit in. The old hardcoded dict spelled out the six
    # resulting edges by hand; this derives them, and derives Kell's too.
    for c in ((x, y), other):
        if c in cells:
            return cells[c]
    return None


def edge_between(a, b):
    """The (x, y, orient) separating two adjacent squares."""
    (ax, ay), (bx, by) = a, b
    if ay == by:
        return (min(ax, bx), ay, 'V')
    return (ax, min(ay, by), 'H')


def forbidden_on(steps, map_name, level):
    """[(edge, why)] for every ruled-out edge the route would cross."""
    out = []
    for a, b in zip(steps, steps[1:]):
        x, y, o = edge_between(a, b)
        why = forbidden(map_name, level, x, y, o)
        if why:
            out.append(((x, y, o), why))
    return out
LOG = os.path.join(ROOT, 'campaign', 'party.tsv')
DB = os.path.join(ROOT, 'mapdb', 'output', 'b1', 'b1.sqlite')

# Feet per turn for dmap's --rate, by how the party is moving.
# rules/exploration.md, PHB p.102: exploring is the rate per TURN, a known route
# is five times faster, fleeing and combat ten times.
RATES = {'explore': 90, 'known': 450, 'flee': 900}


def parse_cell(text):
    f = [c.strip() for c in str(text).split(',')]
    if len(f) != 2:
        raise ValueError('cell must be "x,y", got %r' % text)
    return int(f[0]), int(f[1])


def history(path=None, map_name=None):
    rows = read_tsv(path or LOG, missing_ok=True)
    if map_name:
        rows = [r for r in rows
                if (r.get('map') or '').lower() == map_name.lower()]
    return rows


def where(path=None, map_name='b1'):
    """(x, y, level, the row it came from) or None if never placed."""
    rows = history(path, map_name)
    if not rows:
        return None
    last = rows[-1]
    return (int(last['x']), int(last['y']), int(last['level'] or 1), last)


def route(db, level, a, b, avoid=None):
    """The walkable path from a to b, or None. Never crosses a wall.

    *** IT ALSO NOW ROUTES AROUND campaign/avoid.tsv RATHER THAN REFUSING. ***
    Refusing was the day-79 fix and it was only half of one: it stopped the
    party being walked under the magic mouths, but it left the caller to name
    waypoints and walk the legs by hand, which is precisely what the exp.7
    round-784 row was complaining about when it said "a named route must be
    walked leg by leg with --max-squares". Asking for a destination should
    produce THE ROUTE THE PARTY ACTUALLY USES.
    """
    import dmap
    return dmap.find_path(db, level, a, b, avoid)


def move(to, why='', rate='explore', db=None, path=None, map_name='b1',
         exped='', turn='', max_squares=None, anyway=False):
    """Move the party. Raises ValueError if the route does not exist.

    This is the whole point of the module: an illegal move is an exception,
    not a sentence of narration.
    """
    db = db or DB
    cur = where(path, map_name)
    if cur is None:
        raise ValueError('the party has never been placed; use `place` first')
    x, y, level, _ = cur
    dest = parse_cell(to)
    if dest == (x, y):
        raise ValueError('the party is already at %d,%d' % dest)
    cells, _ = _load(db, level)
    if dest not in cells:
        raise ValueError('(%d,%d) is not a square on level %d of %s'
                         % (dest[0], dest[1], level, os.path.basename(db)))
    import dmap
    avoid = {} if anyway else dmap.avoid_set(level)
    steps, crossed = route(db, level, (x, y), dest, avoid)
    detoured = []
    if steps and avoid:
        naive, _ = route(db, level, (x, y), dest)
        if naive and len(naive) != len(steps):
            detoured = [c for c in naive if c in avoid]
    if not steps and avoid:
        naive, _ = route(db, level, (x, y), dest)
        if naive:
            hit = [c for c in naive if c in avoid]
            raise ValueError(
                'NO ROUTE from (%d,%d) to (%d,%d) that avoids what the '
                'campaign has ruled out.\n'
                '    The only way through is %s\n      %s\n'
                '    If the party has genuinely decided to go that way, '
                'pass --anyway. It is a DECLARED ACT, not a default.'
                % (x, y, dest[0], dest[1],
                   ', '.join('(%d,%d)' % c for c in hit),
                   avoid[hit[0]][:160]))
    if not steps:
        raise ValueError(
            'NO WALKABLE ROUTE from (%d,%d) to (%d,%d) on level %d.\n'
            '    The party cannot get there. Check the map before narrating:\n'
            '        python mapdb/dmap.py at %s %d %d\n'
            '    If they should be able to, the MAP is wrong -- fix it in the '
            'corrections file, do not move them anyway.'
            % (x, y, dest[0], dest[1], level, db, dest[0], dest[1]))
    # A route far longer than the straight line means the destination is NOT
    # where the caller thinks it is. This is the check that actually catches
    # the round-1111 error: (19,5) to (19,6) looks like one square north, and
    # the map routes it 28 squares the long way round. Refusing impossible
    # destinations was never enough -- the bad move was possible, just not the
    # way it was imagined.
    # *** A ROUTE THE CAMPAIGN HAS RULED OUT. ***
    #
    # The pathfinder finds the SHORTEST legal path, and "legal" meant "does not
    # cross a wall". On day 79, asked for the four-way at (16,19), it went back
    # through the secret slab and straight up the corridor under the magic
    # mouths -- the one stretch of level 1 this party does not walk. The rule
    # lived in CHECKLIST.md, in prose, where no tool could read it.
    #
    # It REFUSES rather than rerouting, on purpose: the caller should name the
    # way they mean, exactly as the player did.
    bad = forbidden_on(steps, map_name, level)
    if bad and not anyway:
        raise ValueError(
            'THAT ROUTE IS RULED OUT. The shortest path from (%d,%d) to '
            '(%d,%d) crosses:\n%s\n'
            '    Name the waypoints and walk it in legs, or pass --anyway if '
            'the party has genuinely decided to use it.'
            % (x, y, dest[0], dest[1],
               '\n'.join('        (%d,%d,%s)  %s' % (e[0], e[1], e[2], w)
                          for e, w in bad)))

    straight = abs(dest[0] - x) + abs(dest[1] - y)
    walked = len(steps) - 1
    # max(2, ...) not max(3, ...): a one-square straight line that costs three
    # squares of walking IS the failure being hunted. The floor of 2 still
    # allows an ordinary step round a corner without complaint.
    detour = walked > max(2, straight * 2)
    if detour and max_squares is None:
        raise ValueError(
            'DETOUR: (%d,%d) to (%d,%d) is %d square(s) apart in a straight '
            'line but the only route is %d squares, %d feet.\n'
            '    The destination is NOT adjacent the way it looks -- there is '
            'something between them.\n'
            '    Route: %s\n'
            '    If the long way round is what you meant, pass --max-squares %d '
            'to confirm it.'
            % (x, y, dest[0], dest[1], straight, walked, walked * 10,
               ' '.join('%d,%d' % s for s in steps), walked))
    if max_squares is not None and walked > max_squares:
        raise ValueError(
            'route is %d squares, longer than the %d you expected. '
            'The destination is not where you think.\n    Route: %s'
            % (walked, max_squares, ' '.join('%d,%d' % s for s in steps)))
    feet = walked * 10
    append(path or LOG, dict(
        when=today(), map=map_name, level=level, x=dest[0], y=dest[1],
        exped=exped, turn=turn, squares=len(steps) - 1, feet=feet,
        rate=rate, why=why,
        route=' '.join('%d,%d' % s for s in steps)))
    return steps, crossed, feet


def _load(db, level):
    import dmap
    return dmap.load(db, level)


def place(at, why='', level=1, path=None, map_name='b1', exped='', turn=''):
    """Put the party somewhere without walking there.

    For the start of an expedition, a teleport, or a fall. Separate from `move`
    on purpose: skipping the reachability check should always be a deliberate,
    visible act.
    """
    dest = parse_cell(at)
    append(path or LOG, dict(
        when=today(), map=map_name, level=level, x=dest[0], y=dest[1],
        exped=exped, turn=turn, squares='', feet='', rate='PLACED', why=why,
        route=''))
    return dest


def build_parser():
    p = argparse.ArgumentParser(
        prog='party.py',
        description='Where the party is. Moves are validated against the map.',
        epilog='An illegal move raises. That is the point.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--db', default=DB)
    p.add_argument('--map', default='b1')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('where', help='current square, and what is around it')

    mv = sub.add_parser('move', help='move the party along a real route')
    mv.add_argument('--to', required=True, metavar='X,Y')
    mv.add_argument('--rate', default='explore', choices=sorted(RATES),
                    help='explore = mapping; known = a route already walked; '
                         'flee = fleeing or in combat')
    mv.add_argument('--why', default='')
    mv.add_argument('--max-squares', type=int, default=None,
                    help='how many squares you EXPECT the route to be. A '
                         'longer one is refused. Also confirms a deliberate '
                         'detour, which is otherwise refused automatically.')
    mv.add_argument('--exped', default='')
    mv.add_argument('--turn', default='')

    pl = sub.add_parser('place', help='put the party somewhere WITHOUT walking')
    pl.add_argument('--at', required=True, metavar='X,Y')
    pl.add_argument('--level', type=int, default=1)
    pl.add_argument('--why', required=True,
                    help='say why the check is being skipped')
    pl.add_argument('--exped', default='')
    pl.add_argument('--turn', default='')

    tr = sub.add_parser('trail', help='where the party has been')
    tr.add_argument('--last', type=int, default=10)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)

    if a.cmd == 'where':
        cur = where(a.log_file, a.map)
        if cur is None:
            print('the party has not been placed on map %r' % a.map)
            return 1
        x, y, level, row = cur
        print('party at (%d,%d) on %s level %d' % (x, y, a.map, level))
        if row.get('why'):
            print('  last move: %s' % row['why'])
        import dmap
        print()
        print('\n'.join(dmap.describe(a.db, level, (x, y))))
        return 0

    if a.cmd == 'move':
        try:
            steps, crossed, feet = move(a.to, a.why, a.rate, a.db,
                                        a.log_file, a.map, a.exped, a.turn,
                                        a.max_squares)
        except ValueError as e:
            print('REFUSED: %s' % e)
            return 1
        print('party -> (%d,%d)   %d squares, %d feet'
              % (steps[-1][0], steps[-1][1], len(steps) - 1, feet))
        rate = RATES[a.rate]
        rounds = max(1, int(round(feet / rate * 10)))
        print('  %s rate, %d ft/turn -> about %d round(s)'
              % (a.rate, rate, rounds))
        if crossed:
            # dmap returns (kind, (x, y, orient)) tuples, not strings.
            print('  crosses: %s' % ', '.join(
                '%s at (%d,%d,%s)' % (k, e[0], e[1], e[2]) for k, e in crossed))
        print('  route: %s' % ' '.join('%d,%d' % s for s in steps))
        return 0

    if a.cmd == 'place':
        dest = place(a.at, a.why, a.level, a.log_file, a.map, a.exped, a.turn)
        print('party PLACED at (%d,%d) without a reachability check: %s'
              % (dest[0], dest[1], a.why))
        return 0

    if a.cmd == 'trail':
        for r in history(a.log_file, a.map)[-a.last:]:
            print('%-11s exp%-3s turn %-5s (%3s,%3s) %-8s %s'
                  % (r.get('when', ''), r.get('exped', ''), r.get('turn', ''),
                     r.get('x', ''), r.get('y', ''), r.get('rate', ''),
                     r.get('why', '')))
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
