#!/usr/bin/env python3
"""Query and draw a map database.

    python dmap.py render dmg.sqlite 1
    python dmap.py render dmg.sqlite 1 --window 7 38 23 45
    python dmap.py stats   dmg.sqlite --level 1
    python dmap.py lowconf dmg.sqlite --level 1 --max-conf 3
    python dmap.py check   dmg.sqlite 1
    python dmap.py reach   dmg.sqlite 1 --from-room 1
    python dmap.py light   dmg.sqlite 1 12 8 --radius 3 --mark-seen
    python dmap.py walk    dmg.sqlite 1 12 8 E
"""
import argparse
import os
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


def load_edge_states(db, level):
    """{(x,y,orient): state} -- a door's CURRENT state (open, locked, spiked
    shut, ...), separate from `load()`'s structural `kind`. Its own query
    because most callers never need it; `line_of_sight` does."""
    con = sqlite3.connect(db)
    out = {(r[0], r[1], r[2]): r[3] for r in con.execute(
        "SELECT x,y,orient,state FROM edges WHERE level=?", (level,))}
    con.close()
    return out


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


def describe(db, level, cell, known=False):
    """What is at a square and every way out of it.

    *** WITH known=True, NOTHING THE PARTY HAS NOT SEEN IS DESCRIBED. ***

    THIS FLAG EXISTS BECAUSE THE SAME LEAK HAPPENED TWICE. On day 95 the DM read
    a route home off `path` through unwalked ground and the player said "we
    shouldn't know about the connection." A --known mode was promised then and
    never built. On day 99 it happened again, worse: the DM chained three `at`
    calls down an unexplored corridor -- (2,19) to (2,18) to (2,17) -- and told
    the player that the passage had no branches and that two orc bands were
    walking into each other in it. All true on the map. NONE OF IT SEEN.

    *** AND THE HEADER ALREADY WARNED HIM. *** Each of those squares printed
    "NOT SEEN by the party" and he read past it -- because the warning is on the
    QUERIED square while the leak is in the EXITS LIST, which reports the
    terrain and room label of neighbours nobody has ever looked at.

    So `known` masks the exits, not just the header. The edge KIND still shows
    (a door is a thing you can see from your own side of it); what is BEYOND it
    does not.
    """
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
    if known and not seen:
        return ['(%d,%d)  *** NOT SEEN BY THE PARTY. Nothing is known about it.'
                % (x, y),
                '  Re-run without --known for the DM view.']
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
            nseen = cstate.get(nxt, (None, None, 0))[2]
            if known and not nseen:
                # THE LEAK LIVED HERE. Reporting 'open corridor' or an area
                # name for a square nobody has looked at is handing over the
                # map, one adjacency at a time, and it reads as perception.
                desc = 'UNSEEN'
            else:
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


AVOID_TSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), 'campaign', 'avoid.tsv')


def avoid_set(level, path=None, allow=()):
    """{(x, y): why} the router must not send the party through. See avoid.tsv.

    *** A SHORTEST PATH IS NOT A ROUTE. *** This is the third attempt at a bug
    that was paid for twice and caught by hand both times -- exp.5 round 34
    routed the party past Kell's grave, exp.7 round 784 routed them under the
    magic mouths, and the second row states the gap outright: "party.py move has
    no --via and no forbidden-cell list."

    `allow` is the deliberate override. Walking into the mouths' alcove should
    be a DECLARED ACT, never a side effect of asking to go somewhere else.
    """
    out, allow = {}, {tuple(c) for c in allow}
    try:
        fh = open(path or AVOID_TSV, encoding='utf-8')
    except IOError:
        return out
    with fh:
        hdr = None
        for line in fh:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if hdr is None:
                hdr = parts
                continue
            r = dict(zip(hdr, parts))
            try:
                if int(r['level']) != int(level):
                    continue
                cell = (int(r['x']), int(r['y']))
            except (KeyError, ValueError):
                continue
            if cell not in allow:
                out[cell] = r.get('why', '')
    return out


def find_path(db, level, a, b, avoid=None):
    """Shortest walkable route, with the doors and stairs it crosses.

    `avoid` is {(x,y): why}; those squares are removed from the walkable set
    UNLESS they are an endpoint -- asking to go somewhere is always allowed, it
    is being sent THROUGH it unasked that this stops.
    """
    cells, edges = load(db, level)
    walk = {k for k, v in cells.items()
            if v[0] in WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    if avoid:
        walk -= ({c for c in avoid} - {a, b})
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


def path_report(db, level, a, b, rate_ft=90, avoid=None, through=()):
    avoid = avoid_set(level, allow=through) if avoid is None else avoid
    route, crossed = find_path(db, level, a, b, avoid)
    if not route:
        naive, _ = find_path(db, level, a, b)
        if naive and avoid:
            hit = [c for c in naive if c in avoid]
            return (['NO ROUTE from (%d,%d) to (%d,%d) that avoids everything '
                     'in campaign/avoid.tsv.' % (a + b)]
                    + ['  the only way through is %s -- %s'
                       % ('(%d,%d)' % c, avoid[c][:110]) for c in hit]
                    + ['  If the party is going anyway, SAY SO: '
                       '--through %d,%d' % hit[0]])
        return ['no route from (%d,%d) to (%d,%d)' % (a + b)]
    steps = len(route) - 1
    feet = steps * FEET_PER_SQUARE
    out = ['(%d,%d) -> (%d,%d):  %d squares, %d feet' % (a + b + (steps, feet)),
           '  %.1f turns at %d ft/turn (%.0f rounds)'
           % (feet / rate_ft, rate_ft, round(10 * feet / rate_ft))]
    if crossed:
        out.append('  crosses: %s' % ', '.join(
            '%s at (%d,%d,%s)' % (k, e[0], e[1], e[2]) for k, e in crossed))
    # *** SAY WHEN THE AVOID LIST CHANGED THE ANSWER. *** A router that silently
    # returns a different route is how somebody eventually deletes avoid.tsv for
    # being pointless. Both documented failures were SHORTER by the forbidden
    # way; the cost of going round is exactly the thing worth printing.
    if avoid:
        naive, _ = find_path(db, level, a, b)
        if naive and len(naive) != len(route):
            hit = [c for c in naive if c in avoid]
            out.append('  *** ROUTED AROUND %s, +%d ft ***'
                       % (', '.join('(%d,%d)' % c for c in hit),
                          (len(route) - len(naive)) * FEET_PER_SQUARE))
            for c in hit:
                out.append('      (%d,%d): %s' % (c + (avoid[c][:100],)))
        if through:
            out.append('  [--through given: %s is ALLOWED on this route]'
                       % ', '.join('(%d,%d)' % tuple(c) for c in through))
    return out


EDGE_ALWAYS_OPAQUE = {'wall', 'secret', 'concealed', 'false_door', 'unknown'}
EDGE_NEVER_OPAQUE = {'open', 'archway', 'stairs'}
EDGE_OPEN_STATES = {'open', 'leaf removed'}


def _edge_blocks_light(kind, state):
    """Does one edge stop a ray of light? Opacity, not walkability --

    a SECRET or CONCEALED door still looks like solid wall until it is found
    and opened, so it blocks light even though `find_path` may already treat
    it as walkable for a party that knows it is there. Conversely an ARCHWAY
    is open by construction and a `stairs` edge is a stairwell opening, not a
    wall, so neither is gated by state at all.

    A DOOR (or one-way / portcullis / trap-door) blocks unless its logged
    `state` says otherwise. No state on record defaults to blocking -- the
    conservative direction, same as `unknown` -- because a door nobody has
    opened is shut.
    """
    if kind in EDGE_NEVER_OPAQUE:
        return False
    if kind in EDGE_ALWAYS_OPAQUE:
        return True
    return (state or '').strip() not in EDGE_OPEN_STATES


def _corner_passable(cells, edges, edge_states, i, j):
    """Is the lattice point (i,j) -- where cells (i-1,j-1), (i,j-1),
    (i-1,j) and (i,j) all meet -- open on every side? Used only for a ray
    that grazes a corner exactly; see `line_of_sight`."""
    for c in ((i - 1, j - 1), (i, j - 1), (i - 1, j), (i, j)):
        if cells.get(c, ('solid',))[0] == 'solid':
            return False
    for edge in ((i - 1, j - 1, 'V'), (i - 1, j, 'V'),
                 (i - 1, j - 1, 'H'), (i, j - 1, 'H')):
        kind = edges.get(edge, 'unknown')
        if _edge_blocks_light(kind, (edge_states or {}).get(edge)):
            return False
    return True


def line_of_sight(cells, edges, ax, ay, bx, by, edge_states=None):
    """Does an unbroken line of sight run from the CENTRE of (ax,ay) to the
    CENTRE of (bx,by)? Ray-casting, not a walk-graph search: the ray is a
    continuous segment between the two cell centres (each at (n+0.5, n+0.5)
    in cell units, so 1 cell = 10 ft), and it is blocked the instant it
    crosses an opaque edge or passes through a solid cell -- never routed
    AROUND one the way a pathfinder would. Returns (bool, why); `why` names
    the blocking edge or cell when the answer is False, '' when the segment
    never leaves the source cell.

    Built on exact `fractions.Fraction` arithmetic, not floats: a ray that
    passes EXACTLY through a lattice corner (grazing where four cells meet)
    is a real, not-vanishingly-rare case at this grid's scale, and it has to
    compare as *exactly* equal, not almost. Graze a corner and this call it
    BLOCKED -- the conservative reading, matching the direction every other
    known error in this map already leans (mapdb/DIAGONAL_CONNECTIVITY.md:
    the live grid never claims two squares are FURTHER apart than they
    really are, only ever closer / more open -- so an ambiguous ray answers
    the way that under-, not over-, shows what a torch would).

    Does NOT special-case the 45-degree diagonal-wall squares
    (DIAGONAL_WALLS.md) beyond what their own `terrain`/`edges` rows already
    encode -- if that extraction is right, the wall and solid-terrain checks
    below already see it; this does not re-derive sub-cell geometry.

    `edge_states`, if given, is `load_edge_states()`'s {(x,y,orient): state}
    -- a door's CURRENT open/shut state, separate from `edges`'s structural
    kind. Omit it and every door-like edge is read as shut (the same
    conservative default `_edge_blocks_light` falls back to on its own).
    """
    from fractions import Fraction
    import math
    edge_states = edge_states or {}
    x0 = Fraction(ax) + Fraction(1, 2)
    y0 = Fraction(ay) + Fraction(1, 2)
    x1 = Fraction(bx) + Fraction(1, 2)
    y1 = Fraction(by) + Fraction(1, 2)
    if (ax, ay) == (bx, by):
        return True, ''
    dx, dy = x1 - x0, y1 - y0

    crossings = []  # (t, orient, i)
    if dx != 0:
        lo, hi = sorted((x0, x1))
        for i in range(math.floor(lo) + 1, math.ceil(hi)):
            crossings.append(((i - x0) / dx, 'V', i))
    if dy != 0:
        lo, hi = sorted((y0, y1))
        for j in range(math.floor(lo) + 1, math.ceil(hi)):
            crossings.append(((j - y0) / dy, 'H', j))
    crossings.sort(key=lambda c: c[0])

    def cell_at(t):
        px, py = x0 + t * dx, y0 + t * dy
        return (math.floor(px), math.floor(py))

    bounds = [Fraction(0)] + [c[0] for c in crossings] + [Fraction(1)]
    for i, (t, orient, k) in enumerate(crossings):
        # a corner graze: a V and an H crossing land at the identical t --
        # the ray passes exactly through the lattice point where 4 cells
        # meet. Block it UNLESS all 4 cells and the 4 edges between them are
        # open: a diagonal sightline across an open room grazes a corner at
        # every step (draw the line y=x and see), and calling every one of
        # those blocked would make this useless in the single most common
        # case. It is still the conservative side of any real ambiguity --
        # one solid cell or opaque edge at that corner blocks it.
        if i + 1 < len(crossings) and crossings[i + 1][0] == t:
            corner_i = k if orient == 'V' else math.floor(x0 + t * dx)
            corner_j = k if orient == 'H' else math.floor(y0 + t * dy)
            if not _corner_passable(cells, edges, edge_states,
                                     corner_i, corner_j):
                return False, 'corner graze at (%s, %s)' % (corner_i, corner_j)
        if orient == 'V':
            row = math.floor(y0 + t * dy)
            edge = (k - 1, row, 'V')
        else:
            col = math.floor(x0 + t * dx)
            edge = (col, k - 1, 'H')
        kind = edges.get(edge, 'unknown')
        if _edge_blocks_light(kind, edge_states.get(edge)):
            return False, 'edge %s (%s)' % (edge, kind)
        # the cell the ray occupies AFTER this crossing, up to the next one
        # (or the target) -- the midpoint needs no epsilon, it is exact
        far = cell_at((t + bounds[i + 2]) / 2)
        if cells.get(far, ('solid',))[0] == 'solid':
            return False, 'solid cell %s' % (far,)
    return True, ''


def light_reach(db, level, x, y, radius=3):
    """{(cx,cy): why} every cell within `radius` cells (default 3 = 30 ft)
    of (x,y) that an unbroken ray reaches -- see `line_of_sight`. `why` is a
    one-line reason: 'origin' for the source cell itself, 'los' for
    everything else. Cells outside the radius, or blocked, are simply
    absent; this never claims a negative.

    Checks the full disk, not just the three ring boundaries at r=1,2,3 --
    a cell at offset (1,1), for instance, sits on neither ring but is well
    within 30 ft and needs its own ray checked like any other.
    """
    cells, edges = load(db, level)
    if (x, y) not in cells:
        return {}
    edge_states = load_edge_states(db, level)
    out = {(x, y): 'origin'}
    r2 = radius * radius
    for cx in range(x - radius, x + radius + 1):
        for cy in range(y - radius, y + radius + 1):
            if (cx, cy) == (x, y) or (cx, cy) not in cells:
                continue
            # centre-to-centre distance, in cell units
            ddx, ddy = (cx - x), (cy - y)
            if ddx * ddx + ddy * ddy > r2:
                continue
            ok, _why = line_of_sight(cells, edges, x, y, cx, cy, edge_states)
            if ok:
                out[(cx, cy)] = 'los'
    return out


STOP_JUNCTION, STOP_DEAD_END, STOP_AREA, STOP_FEATURE, STOP_CAPPED = (
    'junction', 'dead_end', 'area_boundary', 'feature', 'capped')


def exits(cell, edges, came_from=None):
    """[(dir, neighbour)] -- every PASSABLE exit from `cell`, excluding the
    direction just arrived from. Does not check whether the neighbour cell
    itself exists in `cells` or is WALKABLE terrain; callers do that (see
    `walk_until` and `tools/stocking.py`'s flee simulator, both of which
    filter this against `cells` themselves). Public because both need it."""
    out = []
    for d, dx, dy, ef in DIRS:
        n = (cell[0] + dx, cell[1] + dy)
        if n == came_from:
            continue
        if edges.get(ef(*cell), 'unknown') in PASSABLE:
            out.append((d, n))
    return out


def walk_until(db, level, start, heading, max_squares=60):
    """Walk from `start` heading roughly `heading` ('N'/'S'/'E'/'W'), taking
    the only way forward through a plain corridor and stopping the moment
    there is something to stop FOR -- never routing the party through a
    decision point unasked.

    A STOP fires on: a JUNCTION (2+ ways on, once the way just walked is
    excluded -- a real choice, so this hands back to the player rather than
    picking for them); a DEAD END (0 ways on); an AREA BOUNDARY (the room
    label of the cell just entered differs from the one just left -- this
    includes leaving a numbered room into blank corridor and the reverse,
    not only room-to-room); or a FEATURE already visible to the party (the
    cell's own `feature` tag, or a secret/concealed edge at this cell that
    is already `seen`.  An UNFOUND secret is invisible to this the same way
    it is to the party). Simply crossing into ground the party has not
    walked before is deliberately NOT a stop condition on its own -- a long
    featureless corridor should not stop every ten feet just because it is
    new.

    Returns a dict: `path` (list of cells walked, `start` included), `stop`
    (one of the STOP_* constants above), `why` (what fired it, in enough
    detail to narrate), and for STOP_JUNCTION, `options` (the [(dir, cell)]
    choices on offer).

    *** LEVEL 2's ROOM LABELS ARE UNRELIABLE. *** mapdb/README.md already
    documents this: `cells.room` there is "nearest numbered area", not
    "inside room N", over one large, patchily-labelled open cavern. An
    AREA_BOUNDARY stop on level 2 may fire on a label flicker that means
    nothing in the fiction -- use judgement the way any confidence-scored
    call in this database asks for, same as a low-confidence wall call.
    This function does not try to filter that out; it reports what the
    label data says and leaves the reading to the DM.

    Does not know about monsters, wandering or placed -- see `light_reach`
    for what is visible from any cell this returns, and
    `tools/stocking.py`/`modules/private/b1_stocking.tsv` for what is
    actually there. Deliberately kept a pure geometry query, the same
    separation `clock.py` and `mapdb` already keep.
    """
    cells, edges = load(db, level)
    con = sqlite3.connect(db)
    found_secret = {(r[0], r[1], r[2]) for r in con.execute(
        "SELECT x,y,orient FROM edges WHERE level=? AND kind IN"
        " ('secret','concealed') AND seen=1", (level,))}
    con.close()
    if start not in cells or cells[start][0] not in WALKABLE:
        return {'path': [start], 'stop': STOP_DEAD_END,
                'why': '(%d,%d) is not walkable ground' % start}

    leg = next(((dx, dy, ef) for d, dx, dy, ef in DIRS if d == heading), None)
    if leg is None:
        return {'path': [start], 'stop': STOP_DEAD_END,
                'why': 'unknown heading %r' % heading}
    dx, dy, ef = leg
    first = (start[0] + dx, start[1] + dy)
    if first not in cells or cells[first][0] not in WALKABLE or \
            edges.get(ef(*start), 'unknown') not in PASSABLE:
        return {'path': [start], 'stop': STOP_DEAD_END,
                'why': 'no way %s from (%d,%d)' % (heading, *start)}

    def feature_at(cell):
        feat = cells[cell][2]
        if feat:
            return 'feature: %s' % feat
        for d, dx, dy, ef in DIRS:
            e = ef(*cell)
            if e in found_secret:
                return 'a known secret door (%s)' % (e,)
        return None

    path = [start, first]
    came_from = start
    cur = first
    room_here = cells[start][1]
    while True:
        if cells[cur][1] != room_here:
            return {'path': path, 'stop': STOP_AREA,
                    'why': 'area changes from %r to %r entering (%d,%d)'
                           % (room_here, cells[cur][1], *cur)}
        feat = feature_at(cur)
        if feat:
            return {'path': path, 'stop': STOP_FEATURE,
                    'why': '%s at (%d,%d)' % (feat, *cur)}
        options = [(d, n) for d, n in exits(cur, edges, came_from)
                   if n in cells and cells[n][0] in WALKABLE]
        if not options:
            return {'path': path, 'stop': STOP_DEAD_END,
                    'why': 'no way on from (%d,%d)' % cur}
        if len(options) > 1:
            return {'path': path, 'stop': STOP_JUNCTION,
                    'why': '%d ways on from (%d,%d)' % (len(options), *cur),
                    'options': options}
        if len(path) - 1 >= max_squares:
            return {'path': path, 'stop': STOP_CAPPED,
                    'why': 'still going after %d squares, nothing new yet'
                           % max_squares}
        came_from, cur = cur, options[0][1]
        room_here = cells[path[-1]][1]
        path.append(cur)


def walk_report(db, level, start, heading, max_squares=60):
    r = walk_until(db, level, start, heading, max_squares)
    feet = (len(r['path']) - 1) * FEET_PER_SQUARE
    out = ['heading %s from (%d,%d): %d square(s), %d ft, stopped at (%d,%d)'
           % (heading, start[0], start[1], len(r['path']) - 1, feet,
              *r['path'][-1]),
           '  %s -- %s' % (r['stop'], r['why'])]
    if r['stop'] == STOP_JUNCTION:
        out.append('  choices: ' + ', '.join('%s -> (%d,%d)' % (d, *n)
                                              for d, n in r['options']))
    return '\n'.join(out)


def light_report(db, level, x, y, radius=3, mark=False):
    """Human-readable: every square a light source at (x,y) actually
    reaches, grouped by whether the party has already seen it, with the
    new ones on top since those are what narration needs. `mark`, if set,
    calls `mark_seen` on the newly-lit squares before returning -- the
    direct fix for hand-picking a `seen --cells` list and getting it wrong,
    which is why this exists."""
    lit = light_reach(db, level, x, y, radius)
    con = sqlite3.connect(db)
    already = {(r[0], r[1]) for r in con.execute(
        'SELECT x,y FROM cells WHERE level=? AND seen=1', (level,))}
    con.close()
    new = sorted(c for c in lit if c not in already and c != (x, y))
    known = sorted(c for c in lit if c in already and c != (x, y))
    out = ['light from (%d,%d), radius %d (%d ft): %d square(s) lit'
           % (x, y, radius, radius * 10, len(lit))]
    if new:
        out.append('  newly lit: ' + ', '.join('(%d,%d)' % c for c in new))
    if known:
        out.append('  already seen: ' + ', '.join('(%d,%d)' % c for c in known))
    if mark and new:
        n = mark_seen(db, level, new)
        out.append('  marked %d square(s) seen' % n)
    return '\n'.join(out)


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
    at.add_argument('--known', action='store_true',
                    help='DESCRIBE ONLY WHAT THE PARTY HAS SEEN. Masks the '
                         'square if unseen, and masks what lies beyond any '
                         'exit into unseen ground. Use this before narrating')

    pa = common(sub.add_parser(
        'path', help='route between two squares, in squares, feet and turns',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    pa.add_argument('coords', type=int, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'))
    pa.add_argument('--rate', type=int, default=90,
                    help="feet per turn; 90 is 9in cautious mapping movement")
    pa.add_argument('--through', action='append', metavar='X,Y',
                    help='allow routing through a square listed in '
                         'campaign/avoid.tsv. Repeatable. Entering the magic '
                         "mouths' alcove should be a DECLARED ACT, never a "
                         'side effect of asking to go somewhere else')

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

    lt = common(sub.add_parser(
        'light', help='what a light source at a square actually reveals, '
                       'by ray-cast line of sight -- not grid distance',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    lt.add_argument('x', type=int)
    lt.add_argument('y', type=int)
    lt.add_argument('--radius', type=int, default=3,
                    help='cells (10 ft each); 3 = a hooded lantern\'s 30 ft')
    lt.add_argument('--mark-seen', action='store_true',
                    help="also mark the newly-lit squares seen -- the "
                         "computed replacement for hand-picking a `seen "
                         "--cells` list")

    wk = common(sub.add_parser(
        'walk', help='advance in a direction until there is something to '
                      'stop for -- a junction, dead end, area change or a '
                      'known feature',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter),
        level_required=True)
    wk.add_argument('x', type=int)
    wk.add_argument('y', type=int)
    wk.add_argument('heading', choices=['N', 'S', 'E', 'W'])
    wk.add_argument('--max-squares', type=int, default=60,
                    help='safety cap if nothing stops it first')
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
        print('\n'.join(describe(args.db, args.level, (args.x, args.y),
                                known=args.known)))
    elif args.cmd == 'path':
        c = args.coords
        through = []
        for t in (args.through or []):
            try:
                x, y = (int(v) for v in t.split(','))
            except ValueError:
                print('--through wants x,y -- got %r' % t, file=sys.stderr)
                return 2
            through.append((x, y))
        print('\n'.join(path_report(args.db, args.level,
                                    (c[0], c[1]), (c[2], c[3]), args.rate,
                                    through=through)))
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
    elif args.cmd == 'light':
        print(light_report(args.db, args.level, args.x, args.y,
                           args.radius, mark=args.mark_seen))
    elif args.cmd == 'walk':
        print(walk_report(args.db, args.level, (args.x, args.y),
                          args.heading, args.max_squares))
    return 0


if __name__ == '__main__':
    sys.exit(main())
