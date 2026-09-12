#!/usr/bin/env python3
"""The land above ground, on a grid. Computed from campaign/places.tsv.

    python tools/overland.py                      # the schematic
    python tools/overland.py --scale 3            # tighter
    python tools/overland.py how-far Draycot Marchford
    python tools/overland.py from Wethersby       # everywhere, by distance
    python tools/overland.py check                # does the grid still agree
                                                  # with the narrative? exit 1

WHY A GRID AND NOT A PICTURE. The distances lived in `calendar.md` prose and
were misquoted: the DM twice described the cart as *"a day behind at Fenn's"*
when Ede's gate is **eight miles** from Fenn's yard -- a couple of hours. A
drawing would have been just as easy to misread. Coordinates can be *checked*,
and `check` recomputes every travel time off them and FAILS if the map stops
agreeing with the fiction it was built from.

*** THE SCALE IS ATTESTED, NOT INVENTED. *** One day by cart = **18 miles**,
because the crag turning is *"one day's walk, call it fifteen to twenty miles
laden"* and one day from Wethersby. Everything else is scaled off that.

*** AND `fix` SAYS HOW EACH PLACE GOT WHERE IT IS. *** A map flattens the
difference between a fact and a guess more thoroughly than prose does -- once
something is drawn, it looks surveyed. So every place carries its provenance:

    attested   bearing AND distance are both in the record
    part       one of the two is; the other is a DM call
    call       NEITHER is. Placed to make the schematic work, and the
               schematic is the only authority for it
    region     an area, not a point

**A `call` is not canon.** If play establishes where Marrow's holding actually
lies, that answer wins and this file changes to match it.
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import entities as entmod                                        # noqa: E402

MILES_PER_DAY = 18          # attested: the crag turning, one day, 15-20 laden

# A DAY IS NOT A DISTANCE, and `places.tsv` carries `day_mode` beside every
# figure for the same reason every quantity in this campaign carries its unit.
# Draycot is "a long day's RIDE; the walk is two days" -- and checking that 1
# against cart speed was the first thing `check` caught, in this file's author.
PACE = {'cart': 18, 'ride': 30, 'walk': 14, '': 18}
TOLERANCE = 0.45            # a day's travel, either way, before `check` warns

# The roads, as sequences of place ids. Travel follows a road where one exists,
# which is why a straight-line distance is a FLOOR and never a quote.
ROADS = {
    'the north road': ['crag_turning', 'wethersby', 'marchford', 'ludbury'],
    'the Draycot road': ['wethersby', 'draycot'],
    'the Ludbury road east': ['ludbury', 'wraye'],
}

GLYPH = {'town': 'O', 'city': '@', 'hall': 'H', 'village': 'v',
         'holding': 'f', 'hamlet': '.', 'camp': 'c', 'landmark': '^',
         'dungeon': '*', 'region': ' ', 'hundred': ' '}


def points():
    """{id: (x, y, row)} for every place that has coordinates."""
    out = {}
    for pid, r in entmod.places().items():
        try:
            out[pid] = (float(r['x']), float(r['y']), r)
        except (KeyError, ValueError):
            continue
    return out


def miles(a, b, pts=None):
    pts = pts if pts is not None else points()
    (ax, ay, _), (bx, by, _) = pts[a], pts[b]
    return math.hypot(bx - ax, by - ay)


def days(m, mode='cart'):
    return m / PACE.get(mode, MILES_PER_DAY)


def bearing(a, b, pts=None):
    """Eight points of the compass, as anybody in the fiction would say it."""
    pts = pts if pts is not None else points()
    (ax, ay, _), (bx, by, _) = pts[a], pts[b]
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return 'the same place'
    ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    names = ('north', 'north-east', 'east', 'south-east',
             'south', 'south-west', 'west', 'north-west')
    return names[int((ang + 22.5) // 45) % 8]


def road_between(a, b):
    for name, stops in ROADS.items():
        if a in stops and b in stops:
            return name
    return None


def render(scale=2, pts=None):
    """A schematic, and a legend under it.

    Labels are NOT written onto the grid. The first attempt did and they
    collided -- Wettleford overwrote Marrow's, both overwrote WETHERSBY, and the
    origin of the whole map vanished under somebody's holding. A legend keyed by
    letter cannot do that, and it has room for the provenance besides.
    """
    pts = pts if pts is not None else points()
    real = {k: v for k, v in pts.items()
            if (v[2].get('kind') or '') not in ('region', 'hundred')}
    xs = [v[0] for v in real.values()]
    ys = [v[1] for v in real.values()]
    x0, x1 = min(xs) - scale * 2, max(xs) + scale * 2
    y0, y1 = min(ys) - scale * 2, max(ys) + scale * 2
    rowmiles = scale * 2                    # characters are ~twice as tall
    cols = int((x1 - x0) / scale) + 1
    rows = int((y1 - y0) / rowmiles) + 1
    grid = [[' '] * cols for _ in range(rows)]

    def cell(x, y):
        return (max(0, min(cols - 1, int(round((x - x0) / scale)))),
                max(0, min(rows - 1, rows - 1 - int(round((y - y0) / rowmiles)))))

    for stops in ROADS.values():
        for a, b in zip(stops, stops[1:]):
            if a not in pts or b not in pts:
                continue
            (ax, ay), (bx, by) = cell(*pts[a][:2]), cell(*pts[b][:2])
            steps = max(abs(bx - ax), abs(by - ay)) or 1
            for i in range(steps + 1):
                cx = ax + int(round((bx - ax) * i / steps))
                cy = ay + int(round((by - ay) * i / steps))
                if grid[cy][cx] == ' ':
                    grid[cy][cx] = ('|' if abs(bx - ax) < abs(by - ay)
                                    else ('-' if by == ay else '\\'))

    # North first, so a collision keeps the northern place and the legend says
    # which two shared a cell rather than silently losing one.
    keys, shared = {}, []
    for n, (pid, (x, y, r)) in enumerate(
            sorted(real.items(), key=lambda kv: (-kv[1][1], kv[1][0]))):
        letter = chr(ord('a') + n) if n < 26 else '+'
        keys[pid] = letter
        cx, cy = cell(x, y)
        if grid[cy][cx] not in ' -|\\':
            shared.append(pid)
        else:
            grid[cy][cx] = letter

    out = ['THE HUNDRED AND THE ROAD SOUTH -- computed from campaign/places.tsv',
           'N up, E right. %d miles a column, %d a row. Wethersby is the origin.'
           % (scale, rowmiles), '']
    out += ['   ' + ''.join(r).rstrip() for r in grid]
    out += ['', '%-4s %-22s %-9s %6s %6s  %-11s %s'
            % ('key', 'place', 'kind', 'x', 'y', 'bearing', 'from Wethersby')]
    for pid, (x, y, r) in sorted(real.items(), key=lambda kv: (-kv[1][1],
                                                              kv[1][0])):
        m = miles('wethersby', pid, pts)
        mode = (r.get('day_mode') or 'cart').strip() or 'cart'
        mark = '' if r.get('fix') == 'attested' else '  <- %s' % r.get('fix')
        out.append('%-4s %-22s %-9s %6.0f %6.0f  %-11s %3.0f mi, %.1f d by %s%s'
                   % (keys[pid], r['name'], r.get('kind', ''), x, y,
                      bearing('wethersby', pid, pts) if pid != 'wethersby'
                      else '--', m, m / PACE[mode], mode, mark))
    if shared:
        out.append('')
        out.append('sharing a cell at this scale: %s'
                   % ', '.join(real[p][2]['name'] for p in shared))
    out += ['',
            'ROADS: ' + ' | '.join('%s = %s' % (n, ' - '.join(
                pts[s][2]['name'] for s in stops if s in pts))
                for n, stops in ROADS.items()),
            '',
            '"<- call" means the record establishes NEITHER bearing nor '
            'distance and the position is a DM call. "<- part" means one of the '
            'two is attested. A call is not canon: if play fixes it, play wins.']
    return '\n'.join(out)


def check(pts=None):
    """[(severity, message)]. Does the grid still agree with the fiction?"""
    pts = pts if pts is not None else points()
    out = []
    if 'wethersby' not in pts:
        return [('FAIL', 'Wethersby has no coordinates and it is the origin')]

    for pid, (x, y, r) in sorted(pts.items()):
        stated = (r.get('days_from_wethersby') or '').strip()
        if not stated:
            continue
        try:
            want = float(stated)
        except ValueError:
            continue
        mode = (r.get('day_mode') or 'cart').strip() or 'cart'
        if mode not in PACE:
            out.append(('FAIL', '%s has day_mode %r; expected one of %s'
                        % (pid, mode, sorted(k for k in PACE if k))))
            continue
        m = miles('wethersby', pid, pts)
        got = m / PACE[mode]
        if abs(got - want) > TOLERANCE:
            out.append(('FAIL', '%s: the record says %g day(s) BY %s from '
                                'Wethersby, the grid gives %.2f (%.0f miles at '
                                '%d miles a day). THE NARRATIVE WINS -- move '
                                'the coordinates, or fix the mode.'
                        % (pid, want, mode.upper(), got, m, PACE[mode])))

    # Bearings the record states in words, checked against the grid.
    for pid, want in (('draycot', 'south-west'), ('marchford', 'south'),
                      ('ludbury', 'south'), ('crag_turning', 'north')):
        if pid in pts:
            got = bearing('wethersby', pid, pts)
            if got != want:
                out.append(('FAIL', '%s is %s of Wethersby on the grid; the '
                                    'record says %s' % (pid, got, want)))
    if 'wraye' in pts and 'ludbury' in pts:
        got = bearing('ludbury', 'wraye', pts)
        if got != 'east':
            out.append(('FAIL', 'Wraye is %s of Ludbury on the grid; the '
                                'record says three days EAST' % got))

    # The two distances the DM has already got wrong in play.
    if 'fenns' in pts and 'edes' in pts:
        m = miles('fenns', 'edes', pts)
        if abs(m - 8) > 2.5:
            out.append(('FAIL', "Fenn's to Ede's is %.1f miles on the grid. "
                                'The record says EIGHT, "a couple of hours, '
                                'not a day" -- and the DM said "a day" twice '
                                'before the player caught it.' % m))
    for pid in ('basecamp', 'cave_mouth'):
        if pid in pts and 'crag_turning' in pts:
            m = miles('crag_turning', pid, pts)
            if m > 6:
                out.append(('FAIL', '%s is %.1f miles off the road. Half an '
                                    'hour to the basecamp and half an hour '
                                    'again to the door, and A CART NEVER '
                                    'REACHES THE DOOR.' % (pid, m)))

    for pid, (x, y, r) in sorted(pts.items()):
        if (r.get('fix') or '') not in ('attested', 'part', 'call', 'region'):
            out.append(('FAIL', '%s has fix=%r; it must say how the position '
                                'was arrived at' % (pid, r.get('fix'))))
    return out


def from_report(origin, pts=None):
    pts = pts if pts is not None else points()
    oid = entmod.resolve(origin, entmod.places())
    if oid is None or oid not in pts:
        return 'no place %r with coordinates' % origin
    rows = sorted(((miles(oid, k, pts), k) for k in pts if k != oid))
    out = ['from %s:' % pts[oid][2]['name'], '']
    for m, k in rows:
        r = pts[k][2]
        road = road_between(oid, k)
        out.append('  %-22s %4.0f miles  %4.1f days  %-11s %s%s'
                   % (r['name'], m, days(m), bearing(oid, k, pts),
                      ('by %s' % road) if road else 'cross-country',
                      '' if r.get('fix') == 'attested' else '   [%s]'
                      % r.get('fix')))
    out.append('')
    out.append('Straight-line, so every figure is a FLOOR. Travel follows a '
               'road where one exists.')
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='overland.py', description='The land above ground, on a grid.')
    p.add_argument('--scale', type=int, default=4, help='miles per column')
    sub = p.add_subparsers(dest='cmd')
    h = sub.add_parser('how-far')
    h.add_argument('a')
    h.add_argument('b')
    f = sub.add_parser('from')
    f.add_argument('origin')
    sub.add_parser('check', help='does the grid still agree with the fiction?')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    pts = points()

    if a.cmd == 'check':
        problems = check(pts)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            att = sum(1 for v in pts.values() if v[2].get('fix') == 'attested')
            print('overland OK: %d places, %d of them ATTESTED in both bearing '
                  'and distance. Every stated travel time is reproduced by the '
                  'grid to within %.2f of a day.' % (len(pts), att, TOLERANCE))
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'how-far':
        pc = entmod.places()
        ai, bi = entmod.resolve(a.a, pc), entmod.resolve(a.b, pc)
        if ai not in pts or bi not in pts:
            print('need two places with coordinates')
            return 1
        m = miles(ai, bi, pts)
        road = road_between(ai, bi)
        print('%s to %s: %.0f miles, about %.1f day(s) by cart, %s'
              % (pts[ai][2]['name'], pts[bi][2]['name'], m, days(m),
                 bearing(ai, bi, pts)))
        print('  %s' % (('along %s' % road) if road else
                        'cross-country -- no road on record between them'))
        for i in (ai, bi):
            if pts[i][2].get('fix') != 'attested':
                print('  [%s is a %s, not something the record establishes]'
                      % (pts[i][2]['name'], pts[i][2].get('fix')))
        return 0

    if a.cmd == 'from':
        print(from_report(a.origin, pts))
        return 0

    print(render(a.scale, pts))
    return 0


if __name__ == '__main__':
    sys.exit(main())
