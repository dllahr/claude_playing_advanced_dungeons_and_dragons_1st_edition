#!/usr/bin/env python3
"""Query and draw a map database.

    python dmap.py render dmg.sqlite 1
    python dmap.py render dmg.sqlite 1 --window 7 38 23 45
    python dmap.py stats   dmg.sqlite --level 1
    python dmap.py lowconf dmg.sqlite --level 1 --max-conf 3
    python dmap.py check   dmg.sqlite 1
    python dmap.py reach   dmg.sqlite 1 --from-room 1
"""
import argparse
import sqlite3
import sys

CELL = {'open': ' ', 'solid': '#', 'mixed': ':', 'unknown': '?'}
HEDGE = {'wall': '---', 'open': '   ', 'door': '-D-', 'secret': '-S-',
         'concealed': '-C-', 'one_way': '-1-', 'false_door': '-F-',
         'archway': '-=-', 'portcullis': '-P-', 'trap_door': '-X-',
         'unknown': '-?-'}
VEDGE = {'wall': '|', 'open': ' ', 'door': 'D', 'secret': 'S',
         'concealed': 'C', 'one_way': '1', 'false_door': 'F',
         'archway': '=', 'portcullis': 'P', 'trap_door': 'X', 'stairs': '%',
         'unknown': '?'}
PASSABLE = ('open', 'door', 'secret', 'concealed', 'archway', 'one_way',
            'portcullis', 'trap_door', 'stairs')
WALKABLE = ('open', 'mixed')


def load(db, level):
    con = sqlite3.connect(db)
    cells = {(r[0], r[1]): (r[2], r[3], r[4], r[5]) for r in con.execute(
        "SELECT x,y,terrain,room,feature,passage FROM cells WHERE level=?", (level,))}
    edges = {(r[0], r[1], r[2]): r[3] for r in con.execute(
        "SELECT x,y,orient,kind FROM edges WHERE level=?", (level,))}
    con.close()
    return cells, edges


def render(db, level, bounds=None):
    cells, edges = load(db, level)
    if not cells:
        return '(no cells for level %s)' % level
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]
    x0, y0, x1, y1 = bounds if bounds else (min(xs), min(ys), max(xs), max(ys))
    out = ['      ' + ''.join('%-4d' % x for x in range(x0, x1 + 1))]
    for y in range(y1, y0 - 1, -1):
        line = '      '
        for x in range(x0, x1 + 1):
            line += '+' + HEDGE.get(edges.get((x, y, 'H'), 'unknown'), '-?-')
        out.append(line + '+')
        line = '%4d  ' % y
        line += VEDGE.get(edges.get((x0 - 1, y, 'V'), 'unknown'), '?')
        for x in range(x0, x1 + 1):
            terrain, room, feature, _ = cells.get((x, y), ('unknown', None, None, None))
            body = room[:3].center(3) if room else CELL.get(terrain, '?') * 3
            if feature and not room:
                body = feature[:3].center(3)
            line += body + VEDGE.get(edges.get((x, y, 'V'), 'unknown'), '?')
        out.append(line)
    line = '      '
    for x in range(x0, x1 + 1):
        line += '+' + HEDGE.get(edges.get((x, y0 - 1, 'H'), 'unknown'), '-?-')
    out.append(line + '+')
    out += ['', "  cells: ' '=open  #=solid  :=mixed  ?=unknown",
            '  edges: -/|=wall  blank=open  D=door  S=secret  C=concealed',
            '         X=trap door  ==archway  1=one-way  F=false  ?=unknown']
    return '\n'.join(out)


def stats(db, level=None):
    con = sqlite3.connect(db)
    where = ('WHERE level=%d' % level) if level else ''
    out = []
    for tbl, label in (('cells', 'cells'), ('edges', 'edges'),
                       ('connections', 'conns')):
        rows = list(con.execute(
            'SELECT confidence, COUNT(*) FROM %s %s GROUP BY confidence'
            ' ORDER BY confidence' % (tbl, where)))
        out.append('%-6s total=%d' % (label, sum(n for _, n in rows)))
        for conf, n in rows:
            out.append('        conf %2d : %5d  %s' % (conf, n, '#' * min(40, n // 2 + 1)))
    for tbl, col in (('cells', 'terrain'), ('cells', 'feature'), ('edges', 'kind')):
        out.append('')
        for v, n in con.execute(
                'SELECT %s, COUNT(*) FROM %s %s GROUP BY %s ORDER BY COUNT(*) DESC'
                % (col, tbl, where, col)):
            if v is not None:
                out.append('  %-6s %-12s %5d' % (tbl, v, n))
    con.close()
    return '\n'.join(out)


def lowconf(db, level=None, limit=40, max_conf=None):
    con = sqlite3.connect(db)
    q = 'SELECT what,level,x,y,orient,detail,confidence,notes FROM low_confidence'
    clauses = []
    if level:
        clauses.append('level=%d' % level)
    if max_conf is not None:
        clauses.append('confidence<=%d' % max_conf)
    if clauses:
        q += ' WHERE ' + ' AND '.join(clauses)
    q += ' LIMIT %d' % limit
    fmt = '%-5s %-3s %-4s %-4s %-3s %-14s %-4s %s'
    out = [fmt % ('what', 'lvl', 'x', 'y', 'or', 'detail', 'conf', 'notes')]
    for r in con.execute(q):
        out.append(fmt % tuple('' if v is None else v for v in r))
    con.close()
    return '\n'.join(out)


def check(db, level):
    """Contradictions: a passable boundary that leads into solid rock."""
    con = sqlite3.connect(db)
    problems = []
    for x, y, orient, kind in con.execute(
            'SELECT x,y,orient,kind FROM edges WHERE level=? AND kind IN (%s)'
            % ','.join('?' * len(PASSABLE)), (level,) + PASSABLE):
        bx, by = (x + 1, y) if orient == 'V' else (x, y + 1)
        for cx, cy in ((x, y), (bx, by)):
            row = con.execute('SELECT terrain FROM cells WHERE level=? AND x=? AND y=?',
                              (level, cx, cy)).fetchone()
            if row and row[0] == 'solid':
                problems.append('passable %s edge (%d,%d,%s) touches SOLID cell (%d,%d)'
                                % (kind, x, y, orient, cx, cy))
            elif not row:
                problems.append('passable %s edge (%d,%d,%s) touches UNRECORDED cell (%d,%d)'
                                % (kind, x, y, orient, cx, cy))
    nc = con.execute("SELECT COUNT(*) FROM cells WHERE level=? AND terrain='unknown'",
                     (level,)).fetchone()[0]
    ne = con.execute("SELECT COUNT(*) FROM edges WHERE level=? AND kind='unknown'",
                     (level,)).fetchone()[0]
    con.close()
    out = problems if problems else ['no contradictions found']
    out.append('unknown cells: %d   unknown edges: %d' % (nc, ne))
    return '\n'.join(out)


def reachable(db, level, start=None, from_room=None, diagonal=True):
    """Flood the walkable network and report what cannot be reached.

    Every non-solid square on a dungeon level should be reachable from the
    entrance -- through doors, secret doors, trap doors, whatever. A square
    that is not is either genuinely isolated (worth knowing) or, far more
    often, evidence of a wall the extractor invented or a door it missed.

    `diagonal` allows a corner step between two cells that BOTH carry a
    diagonal-passage feature. A half-width 45-degree corridor really does
    connect only at the corner: the squares that would bridge it orthogonally
    contain no floor at all, and marking them walkable would invent floor that
    is not on the page.
    """
    cells, edges = load(db, level)
    # water is not floor: a stream fills its passage and is not a way through
    walk = {k for k, v in cells.items()
            if v[0] in WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    diag = {k for k, v in cells.items() if v[3] in ('diagonal', 'diagonal_half')}

    if start is None:
        con = sqlite3.connect(db)
        row = con.execute('SELECT anchor_x,anchor_y FROM rooms'
                          ' WHERE level=? AND number=?',
                          (level, str(from_room))).fetchone()
        con.close()
        if not row or row[0] is None:
            return ['cannot start: no anchor for room %r' % from_room]
        start = (row[0], row[1])
    if start not in walk:
        return ['cannot start: cell %s is not walkable' % (start,)]

    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy, ex, ey, orient in ((1, 0, x, y, 'V'), (-1, 0, x - 1, y, 'V'),
                                       (0, 1, x, y, 'H'), (0, -1, x, y - 1, 'H')):
            nxt = (x + dx, y + dy)
            if nxt in seen or nxt not in walk:
                continue
            if edges.get((ex, ey, orient), 'unknown') in PASSABLE:
                seen.add(nxt); stack.append(nxt)
        if diagonal and (x, y) in diag:
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                nxt = (x + dx, y + dy)
                if nxt not in seen and nxt in diag:
                    seen.add(nxt); stack.append(nxt)

    missed = sorted(walk - seen, key=lambda c: (-c[1], c[0]))
    out = ['start %s   walkable %d   reached %d   UNREACHED %d'
           % (start, len(walk), len(seen), len(missed))]
    if missed:
        con = sqlite3.connect(db)
        rooms = {(r[0], r[1]): r[2] for r in con.execute(
            'SELECT anchor_x,anchor_y,number FROM rooms WHERE level=?', (level,))}
        con.close()
        for c in missed:
            tag = ('  <- room %s' % rooms[c]) if c in rooms else ''
            out.append('  unreached (%2d,%2d) %s%s' % (c[0], c[1], cells[c][0], tag))
    return out


def room_graph(db, level, start=None):
    """Node graph derived from the GRID: which areas connect through which door.

    B1's module text does not encode its topology -- only about three of its
    thirty-seven areas state where they lead, the rest being descriptions of
    contents -- so unlike the DMG the graph cannot be read from the prose and
    has to come from the map.

    Areas are grouped by flooding through OPEN boundaries only. Whatever a door
    or a staircase separates is, by construction, a different node, so the
    doors become the edges of the graph and each open region becomes a node
    (named for the area labels inside it, or "corridor" where there are none).
    """
    cells, edges = load(db, level)
    walk = {k for k, v in cells.items()
            if v[0] in WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    comp, cid = {}, 0
    for c0 in sorted(walk):
        if c0 in comp:
            continue
        comp[c0] = cid
        stack = [c0]
        while stack:
            x, y = stack.pop()
            for dx, dy, ex, ey, o in ((1, 0, x, y, 'V'), (-1, 0, x - 1, y, 'V'),
                                      (0, 1, x, y, 'H'), (0, -1, x, y - 1, 'H')):
                nxt = (x + dx, y + dy)
                if nxt in comp or nxt not in walk:
                    continue
                if edges.get((ex, ey, o), 'unknown') == 'open':
                    comp[nxt] = cid
                    stack.append(nxt)
        cid += 1

    con = sqlite3.connect(db)
    labels = list(con.execute(
        'SELECT number,x,y FROM room_labels WHERE level=?', (level,)))
    names = dict(con.execute(
        'SELECT number,name FROM rooms WHERE level=?', (level,)))
    con.close()
    members = {}
    for number, x, y in labels:
        if (x, y) in comp:
            members.setdefault(comp[(x, y)], set()).add(number)

    links = {}
    for (x, y, o), kind in edges.items():
        if kind not in PASSABLE or kind == 'open':
            continue
        a = (x, y)
        b = (x + 1, y) if o == 'V' else (x, y + 1)
        if a not in comp or b not in comp or comp[a] == comp[b]:
            continue
        key = (min(comp[a], comp[b]), max(comp[a], comp[b]))
        links.setdefault(key, []).append((kind, (x, y, o)))

    def label(n):
        m = sorted(members.get(n, ()), key=lambda s: (len(s), s))
        if not m:
            return 'corridor#%d' % n
        return '/'.join(('%s %s' % (k, names.get(k) or '')).strip() for k in m)

    return comp, members, links, label


def graph_report(db, level, min_size=1):
    comp, members, links, label = room_graph(db, level)
    sizes = {}
    for c, n in comp.items():
        sizes[n] = sizes.get(n, 0) + 1
    out = ['%d open regions, %d of them holding a labelled area, %d links'
           % (len(sizes), len(members), len(links))]
    named = sorted(members, key=lambda n: -sizes[n])
    out.append('')
    out.append('regions holding an area label:')
    for n in named:
        out.append('  %-4d %3d sq  %s' % (n, sizes[n], label(n)))
    out.append('')
    out.append('links (a door, staircase or secret door between two regions):')
    for (a, b), es in sorted(links.items(), key=lambda kv: -max(sizes[kv[0][0]], sizes[kv[0][1]])):
        kinds = {}
        for k, _ in es:
            kinds[k] = kinds.get(k, 0) + 1
        if sizes[a] < min_size and sizes[b] < min_size:
            continue
        out.append('  %-34s <-> %-34s  %s'
                   % (label(a)[:34], label(b)[:34],
                      ', '.join('%dx %s' % (v, k) for k, v in sorted(kinds.items()))))
    return '\n'.join(out)


DIRS = (('N', 0, 1, lambda x, y: (x, y, 'H')),
        ('S', 0, -1, lambda x, y: (x, y - 1, 'H')),
        ('E', 1, 0, lambda x, y: (x, y, 'V')),
        ('W', -1, 0, lambda x, y: (x - 1, y, 'V')))
FEET_PER_SQUARE = 10


def describe(db, level, cell):
    """What the DM needs at the table: where this is, and every way out.

    Replaces reading geometry off a crop mid-session, which is what produced
    every one of the six errors that started this work.

    This also reports `state` -- what the PARTY has done to a square or a
    boundary, replayed from campaign/world_changes.tsv by tools/world.py. It
    belongs here rather than in a second command precisely because this is the
    one query that gets run before describing anything; a door the party spiked
    open two expeditions ago is no use in a file nobody opens mid-session.
    """
    cells, edges = load(db, level)
    con = sqlite3.connect(db)
    names = dict(con.execute('SELECT number,name FROM rooms WHERE level=?', (level,)))
    rstate = {r[0]: (r[1], r[2]) for r in con.execute(
        'SELECT number,state,state_note FROM rooms'
        ' WHERE level=? AND state IS NOT NULL', (level,))}
    cstate = {(r[0], r[1]): (r[2], r[3], r[4]) for r in con.execute(
        'SELECT x,y,state,state_note,seen FROM cells WHERE level=?', (level,))}
    estate = {(r[0], r[1], r[2]): (r[3], r[4]) for r in con.execute(
        'SELECT x,y,orient,state,state_note FROM edges'
        ' WHERE level=? AND state IS NOT NULL', (level,))}
    con.close()
    x, y = cell
    here = cells.get(cell)
    if not here:
        return ['(%d,%d) is off the map' % cell]
    terrain, room, feature, passage = here
    where = 'area %s %s' % (room, names.get(room) or '') if room else 'corridor'
    st, snote, seen = cstate.get(cell, (None, None, 0))
    out = ['(%d,%d)  %s  %s%s%s' % (x, y, terrain, where.strip(),
                                    '  [%s]' % feature if feature else '',
                                    '' if seen else '   *** NOT SEEN by the party')]
    if st:
        out.append('  STATE: %s -- %s' % (st, snote or ''))
    if room:
        n = sum(1 for k, v in cells.items() if v[1] == room)
        out.append('  area %s covers %d squares' % (room, n))
        if room in rstate:
            out.append('  area STATE: %s -- %s'
                       % (rstate[room][0], rstate[room][1] or ''))
    out.append('  exits:')
    for name, dx, dy, ef in DIRS:
        nxt = (x + dx, y + dy)
        ekey = ef(x, y)
        kind = edges.get(ekey, 'unknown')
        beyond = cells.get(nxt)
        if kind == 'wall' and not beyond:
            continue
        if beyond:
            broom = beyond[1]
            desc = ('area %s %s' % (broom, names.get(broom) or '')).strip() \
                if broom else ('%s' % beyond[0])
        else:
            desc = 'off map'
        mark = '' if kind in PASSABLE else '   (blocked)'
        out.append('    %-2s %-8s -> (%2d,%2d) %-28s%s'
                   % (name, kind, nxt[0], nxt[1], desc, mark))
        if ekey in estate:
            out.append('       >> %s -- %s'
                       % (estate[ekey][0], estate[ekey][1] or ''))
    return out


def find_path(db, level, a, b):
    """Shortest walkable route, with the doors and stairs it crosses."""
    cells, edges = load(db, level)
    walk = {k for k, v in cells.items()
            if v[0] in WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    if a not in walk or b not in walk:
        return None, []
    prev = {a: None}
    q = [a]
    while q:
        nxt = []
        for (x, y) in q:
            if (x, y) == b:
                q = []
                break
            for _, dx, dy, ef in DIRS:
                n = (x + dx, y + dy)
                if n in prev or n not in walk:
                    continue
                if edges.get(ef(x, y), 'unknown') in PASSABLE:
                    prev[n] = (x, y)
                    nxt.append(n)
        q = nxt
        if b in prev:
            break
    if b not in prev:
        return None, []
    route = [b]
    while route[-1] != a:
        route.append(prev[route[-1]])
    route.reverse()
    crossed = []
    for p, n in zip(route, route[1:]):
        for _, dx, dy, ef in DIRS:
            if (p[0] + dx, p[1] + dy) == n:
                k = edges.get(ef(*p), 'unknown')
                if k != 'open':
                    crossed.append((k, ef(*p)))
    return route, crossed


def path_report(db, level, a, b, rate_ft=90):
    route, crossed = find_path(db, level, a, b)
    if not route:
        return ['no route from (%d,%d) to (%d,%d)' % (a + b)]
    steps = len(route) - 1
    feet = steps * FEET_PER_SQUARE
    out = ['(%d,%d) -> (%d,%d):  %d squares, %d feet' % (a + b + (steps, feet)),
           '  %.1f turns at %d ft/turn (%.0f rounds)'
           % (feet / rate_ft, rate_ft, round(10 * feet / rate_ft))]
    if crossed:
        out.append('  crosses: %s' % ', '.join(
            '%s at (%d,%d,%s)' % (k, e[0], e[1], e[2]) for k, e in crossed))
    return out


def mark_seen(db, level, cells_):
    """Record that the party has verified these squares and their boundaries."""
    con = sqlite3.connect(db)
    n = 0
    for (x, y) in cells_:
        n += con.execute('UPDATE cells SET seen=1 WHERE level=? AND x=? AND y=?',
                         (level, x, y)).rowcount
        for _, dx, dy, ef in DIRS:
            e = ef(x, y)
            con.execute('UPDATE edges SET seen=1 WHERE level=? AND x=? AND y=?'
                        ' AND orient=?', (level, e[0], e[1], e[2]))
    con.commit()
    con.close()
    return n


def build_parser():
    p = argparse.ArgumentParser(
        prog='dmap.py', description='Query and draw a dungeon map database.')
    sub = p.add_subparsers(dest='cmd', required=True, metavar='COMMAND')

    def common(sp, level_required=False):
        sp.add_argument('db', help='SQLite map database')
        if level_required:
            sp.add_argument('level', type=int, help='dungeon level number')
        else:
            sp.add_argument('--level', type=int, default=None,
                            help='restrict to one dungeon level')
        return sp

    r = common(sub.add_parser('render', help='draw the level as doubled-grid ASCII',
                              formatter_class=argparse.ArgumentDefaultsHelpFormatter),
               level_required=True)
    r.add_argument('--window', type=int, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'),
                   help='draw only this inclusive cell window (default: whole level)')

    common(sub.add_parser('stats', help='confidence histogram and class counts'))

    lc = common(sub.add_parser(
        'lowconf', help='least-trustworthy calls first',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter))
    lc.add_argument('--limit', type=int, default=40, help='rows to print')
    lc.add_argument('--max-conf', type=int, default=None,
                    help='only show items at or below this confidence (1-10)')

    common(sub.add_parser('check', help='find passable edges leading into rock'),
           level_required=True)

    at = common(sub.add_parser(
        'at', help='what is at a square, and every way out of it'),
        level_required=True)
    at.add_argument('x', type=int)
    at.add_argument('y', type=int)

    pa = common(sub.add_parser(
        'path', help='route between two squares, in squares, feet and turns',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    pa.add_argument('coords', type=int, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'))
    pa.add_argument('--rate', type=int, default=90,
                    help="feet per turn; 90 is 9in cautious mapping movement")

    sn = common(sub.add_parser(
        'seen', help='mark squares as verified by the party (DM-side only)'),
        level_required=True)
    sn.add_argument('--room', help='mark every square of this area')
    sn.add_argument('--cells', nargs='+', metavar='X,Y', help='mark these squares')

    gp = common(sub.add_parser(
        'graph', help='node graph of areas and the doors between them',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    gp.add_argument('--min-size', type=int, default=1,
                    help='hide links where both regions are smaller than this')

    rc = common(sub.add_parser(
        'reach', help='report squares unreachable from the entrance',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    g = rc.add_mutually_exclusive_group()
    g.add_argument('--from-room', default='1',
                   help='start from this room number, using its anchor cell')
    g.add_argument('--from-cell', type=int, nargs=2, metavar=('X', 'Y'),
                   help='start from an explicit cell instead')
    rc.add_argument('--no-diagonal', action='store_true',
                    help='forbid corner steps between diagonal-passage cells')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == 'render':
        print(render(args.db, args.level,
                     tuple(args.window) if args.window else None))
    elif args.cmd == 'stats':
        print(stats(args.db, args.level))
    elif args.cmd == 'lowconf':
        print(lowconf(args.db, args.level, args.limit, args.max_conf))
    elif args.cmd == 'check':
        print(check(args.db, args.level))
    elif args.cmd == 'at':
        print('\n'.join(describe(args.db, args.level, (args.x, args.y))))
    elif args.cmd == 'path':
        c = args.coords
        print('\n'.join(path_report(args.db, args.level,
                                    (c[0], c[1]), (c[2], c[3]), args.rate)))
    elif args.cmd == 'seen':
        target = []
        if args.room:
            con = sqlite3.connect(args.db)
            target = [(x, y) for x, y in con.execute(
                'SELECT x,y FROM cells WHERE level=? AND room=?',
                (args.level, args.room))]
            con.close()
        for c in (args.cells or []):
            x, y = c.split(',')
            target.append((int(x), int(y)))
        print('marked %d square(s) seen' % mark_seen(args.db, args.level, target))
    elif args.cmd == 'graph':
        print(graph_report(args.db, args.level, args.min_size))
    elif args.cmd == 'reach':
        print('\n'.join(reachable(
            args.db, args.level,
            start=tuple(args.from_cell) if args.from_cell else None,
            from_room=args.from_room, diagonal=not args.no_diagonal)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
