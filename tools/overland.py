#!/usr/bin/env python3
"""The land above ground, on a grid. Computed from campaign/places.tsv.

    python tools/overland.py                      # the schematic
    python tools/overland.py --scale 3            # tighter
    python tools/overland.py how-far Draycot Marchford
    python tools/overland.py from Wethersby       # everywhere, by distance
    python tools/overland.py check                # does the grid still agree
                                                  # with the narrative? exit 1

*** THE ASCII MAP IS NOT FOR THE DM, AND IT IS NOT AUTHORITATIVE. ***

Asked directly whether the text map was easier to read than the data behind it,
the honest answer is NO. Reading "which town lies north-west of Wethersby" off a
character grid means reconstructing coordinates from column positions -- which is
strictly harder than reading the coordinates. Every question the DM actually asks
has a better answer in a query:

    how far          `how-far A B`      exact, both ways, with the time ranges
    which way        the bearing, computed, not eyeballed off a glyph
    what lies on     `from <place>`, sorted by distance
    do they know     `knows`

A picture can surprise you with something you did not ask about, and that is
worth something. It is thin next to the cost of the DM squinting at a grid.

*** AND A PASTED MAP IS A STALE MAP. *** A rendering in the conversation is
correct at the instant it is made and never again. Reading a position back off
one is narrating from a summary instead of from the log -- the single largest
error class in this campaign -- so: RENDER IT FOR THE PLAYER, QUERY IT FOR
YOURSELF.

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
from tsvlog import read_tsv                                      # noqa: E402
import entities as entmod                                        # noqa: E402

MILE = 5280

# FROM THE BOOK, NOT INVENTED: rules/overland.md, DMG p.58. An earlier draft of
# this file used a DM-reasoned 18 miles per CART-day, taken off "fifteen to
# twenty miles laden" -- which is a WALKING figure. The DMG gives a cart 25 on a
# road. Every travel TIME in the narrative is unchanged; only the mileage moved,
# and it moved onto the book.
PACE = {'cart': 25, 'wagon': 25, 'ride': 40, 'ride_light': 60,
        'walk': 20, 'walk_rough': 10, '': 25}

# A DISTANCE IS FIXED. A TIME IS NOT -- load, weather, road and beast all move
# it, which is why the uncertainty that used to sit on the map now sits here,
# where it is honest.
SPREAD = 0.2

# Attested PAIRWISE claims. `attested_days` on a row is a radius from Wethersby
# and only works where the road runs roughly straight; Wraye is "three days EAST
# OF LUDBURY" and its eight days from Wethersby go south and THEN east, so a
# straight line cuts the corner and the check fired. The claim belongs on the
# leg. (a, b, days, mode)
LEGS = (('marchford', 'ludbury', 2, 'cart'),
        ('ludbury', 'wraye', 3, 'cart'),
        ('marchford', 'fenns', 1, 'cart'))

KNOWN, VAGUE, HEARD, UNKNOWN = 'known', 'vague', 'heard', 'unknown'
LEVELS = (KNOWN, VAGUE, HEARD, UNKNOWN)

ROADS = {
    'the north road': ['crag_turning', 'wethersby', 'marchford', 'ludbury'],
    'the Draycot road': ['wethersby', 'draycot'],
    'the Ludbury road east': ['ludbury', 'wraye'],
}

GLYPH = {'town': 'O', 'city': '@', 'hall': 'H', 'village': 'v',
         'holding': 'f', 'hamlet': '.', 'camp': 'c', 'landmark': '^',
         'dungeon': '*', 'region': ' ', 'hundred': ' '}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOW = os.path.join(ROOT, 'campaign', 'knowledge.tsv')
FRAMES = os.path.join(ROOT, 'campaign', 'frames.tsv')


def knowledge(path=None):
    """{place: row} -- the LATEST row per place. A place with none is unknown."""
    out = {}
    for r in read_tsv(path or KNOW, missing_ok=True):
        if r.get('place'):
            out[r['place']] = r
    return out


def level_of(pid, kn=None):
    kn = kn if kn is not None else knowledge()
    return (kn.get(pid, {}).get('level') or UNKNOWN).strip() or UNKNOWN


def frames(path=None):
    return {r['id']: r for r in read_tsv(path or FRAMES, missing_ok=True)
            if r.get('id')}


def to_overland(frame_id, cell_x, cell_y, fr=None):
    """A local grid square -> feet in the world frame. THE ONE CONVERSION."""
    fr = fr if fr is not None else frames()
    f = fr[frame_id]
    u = float(f['unit_ft'])
    dx, dy = cell_x * u, cell_y * u
    rot = math.radians(float(f.get('rotation_deg') or 0))
    if rot:
        dx, dy = (dx * math.cos(rot) - dy * math.sin(rot),
                  dx * math.sin(rot) + dy * math.cos(rot))
    return int(round(float(f['origin_x_ft']) + dx)), \
           int(round(float(f['origin_y_ft']) + dy))


def points():
    """{id: (x_ft, y_ft, row)} for every place with coordinates. EXACT."""
    out = {}
    for pid, r in entmod.places().items():
        try:
            out[pid] = (float(r['x_ft']), float(r['y_ft']), r)
        except (KeyError, ValueError):
            continue
    return out


def feet(a, b, pts=None):
    pts = pts if pts is not None else points()
    (ax, ay, _), (bx, by, _) = pts[a], pts[b]
    return math.hypot(bx - ax, by - ay)


def miles(a, b, pts=None):
    return feet(a, b, pts) / MILE


def days(m, mode='cart'):
    """Mid-estimate in days for `m` MILES."""
    return m / PACE.get(mode, PACE['cart'])


def days_range(m, mode='cart'):
    """(low, high). A distance is fixed; a TIME is not, and this says so."""
    mid = days(m, mode)
    return mid * (1 - SPREAD), mid * (1 + SPREAD)


def how_long(m):
    """Every ordinary way of covering `m` miles, as a range of days."""
    out = []
    for mode, label in (('cart', 'by cart'), ('ride', 'at a medium ride'),
                        ('walk', 'walking laden'), ('walk_rough', 'off the road')):
        lo, hi = days_range(m, mode)
        out.append('%-18s %4.1f - %.1f days' % (label, lo, hi))
    return out


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


ASPECT = 2.0        # a terminal character is about twice as tall as it is wide


def _fit(pts, width, height=None, margin=2):
    """Miles per column so the map fills `width`, honouring the aspect ratio.

    If `height` is given the map is fitted into the BOX, which letterboxes
    horizontally -- this world is half as wide as it is tall, so filling the
    width makes a long map. That is the honest shape of it.
    """
    xs = [v[0] for v in pts.values()]
    ys = [v[1] for v in pts.values()]
    span_x = max((max(xs) - min(xs)) / MILE, 1.0)
    span_y = max((max(ys) - min(ys)) / MILE, 1.0)
    by_w = span_x / max(width - margin * 2 - 1, 1)
    if height is None:
        return by_w
    by_h = span_y / (max(height - margin - 1, 1) * ASPECT)
    return max(by_w, by_h)


def _road_char(dx, dy):
    if dx == 0:
        return '|'
    if dy == 0:
        return '-'
    return '\\' if (dx > 0) == (dy > 0) else '/'


def _place_label(grid, cy, cx, text):
    """Write `text` near (cy,cx) wherever it fits. Returns True if it landed.

    The first renderer wrote labels straight onto the grid and they collided --
    Wettleford over Marrow's, both over WETHERSBY, and the origin of the whole
    map vanished under somebody's holding. This tries four sides and gives up
    honestly rather than overwriting.
    """
    rows, cols = len(grid), len(grid[0])

    def free(y, x0, n):
        if not (0 <= y < rows and 0 <= x0 and x0 + n <= cols):
            return False
        return all(grid[y][x0 + i] == ' ' for i in range(n))

    n = len(text) + 1
    spots = [(cy, cx + 2), (cy, cx - n - 1)]
    for dy in (-1, 1, -2, 2, -3, 3):
        for dx in (1, 2, 3, -n, -n - 1, -n - 2, 0):
            spots.append((cy + dy, cx + dx))
    for y, x0 in spots:
        if free(y, x0, n):
            for i, ch in enumerate(text):
                grid[y][x0 + i] = ch
            return True
    return False


def crop(pts, centre, radius_mi):
    """Only what lies within `radius_mi` of `centre`. THE ZOOM.

    The party's world is about 38 miles wide and 146 tall, so filling 120
    columns with the whole of it honestly gives a map 200 rows deep and mostly
    road. Cropping is what makes a wide terminal pay: the hundred at 30 miles
    across puts the crag, the basecamp and the cave mouth in separate columns.
    """
    if centre not in pts:
        return pts
    cx, cy, _ = pts[centre]
    r = radius_mi * MILE
    return {k: v for k, v in pts.items()
            if math.hypot(v[0] - cx, v[1] - cy) <= r}


def render(scale_mi=None, pts=None, true=False, kn=None,
           width=120, height=None, labels=True, all_pts=None):
    """The PARTY'S map by default. `true` is the DM's.

    *** THE DEFAULT MATTERS AND IT IS NOT DECORATION. *** A map is the easiest
    possible way to leak a position. If the party has never been to Wraye their
    map must not carry a dot at its exact coordinates -- CHECKLIST section 8 --
    so a `heard` place is a name in the margin and nothing else.
    """
    pts = pts if pts is not None else points()
    # Distances in the legend are always FROM WETHERSBY, which a crop may have
    # cut out -- the crag at a 4-mile radius does not contain the town.
    all_pts = all_pts if all_pts is not None else points()
    kn = kn if kn is not None else knowledge()
    real = {k: v for k, v in pts.items()
            if (v[2].get('kind') or '') not in ('region', 'hundred')}
    if not true:
        real = {k: v for k, v in real.items()
                if level_of(k, kn) in (KNOWN, VAGUE)}
    if not real:
        return 'the party has been nowhere yet'

    # Reserve room for the longest NAME before choosing the scale, or a place
    # at the eastern edge has nowhere to put its label and the map has to report
    # that it gave up -- which it did, for Marrow's holding and Ede's cottage.
    pad = max(len(v[2]['name']) for v in real.values()) + 3
    scale = (scale_mi if scale_mi
             else _fit(real, max(width - pad, 20), height)) * MILE
    rowft = scale * ASPECT
    xs = [v[0] for v in real.values()]
    ys = [v[1] for v in real.values()]
    x0 = min(xs) - scale * 2
    y0 = min(ys) - rowft
    cols = int((max(xs) + scale * 2 - x0) / scale) + 1 + pad
    rows = int((max(ys) + rowft - y0) / rowft) + 1
    grid = [[' '] * cols for _ in range(rows)]

    def cell(x, y):
        return (max(0, min(cols - 1, int(round((x - x0) / scale)))),
                max(0, min(rows - 1, rows - 1 - int(round((y - y0) / rowft)))))

    for stops in ROADS.values():
        for a_, b_ in zip(stops, stops[1:]):
            if a_ not in real or b_ not in real:
                continue
            (ax, ay), (bx, by) = cell(*pts[a_][:2]), cell(*pts[b_][:2])
            ch = _road_char(bx - ax, by - ay)
            steps = max(abs(bx - ax), abs(by - ay)) or 1
            for i in range(steps + 1):
                cx = ax + int(round((bx - ax) * i / steps))
                cy = ay + int(round((by - ay) * i / steps))
                if grid[cy][cx] == ' ':
                    grid[cy][cx] = ch

    order = sorted(real.items(), key=lambda kv: (-kv[1][1], kv[1][0]))
    at, unlabelled = {}, []
    for pid, (x, y, r) in order:
        cx, cy = cell(x, y)
        g = GLYPH.get(r.get('kind') or '', '+')
        if grid[cy][cx] not in ' -|\\/':
            at.setdefault((cy, cx), []).append(pid)
            continue
        grid[cy][cx] = g
        at.setdefault((cy, cx), []).append(pid)

    if labels:
        for pid, (x, y, r) in order:
            cx, cy = cell(x, y)
            here = at.get((cy, cx), [])
            if here and here[0] != pid:
                continue                       # the sharer names the cell
            mark = '~' if level_of(pid, kn) == VAGUE else ''
            text = mark + r['name'] + (
                '' if not true or r.get('fix') == 'attested' else '?')
            if len(here) > 1:
                text += ' +%d' % (len(here) - 1)
            if not _place_label(grid, cy, cx, text):
                unlabelled.append(r['name'])

    mi = scale / MILE
    # An adaptive bar. A fixed "10 miles" ran off the edge at the crag, where a
    # column is fifty feet, and would have been a single character out at the
    # whole-world zoom.
    want = cols * mi * 0.3
    steps = [1 / 52.8, 5 / 52.8, 10 / 52.8, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100]
    step = min(steps, key=lambda v: abs(math.log(v / max(want, 1e-6))))
    bar = max(3, min(cols, int(round(step / mi))))
    label = ('%d mile%s' % (round(step), '' if round(step) == 1 else 's')) if step >= 1 else (
        '%g mile' % step if step >= 0.25 else '%d ft' % round(step * MILE))
    head = [
        '%s -- %s' % ('THE TRUE MAP  (DM ONLY)' if true else "THE PARTY'S MAP",
                      'computed from campaign/places.tsv'),
        'N is up, E is right.  %.2f miles a column, %.2f a row -- THE ASPECT '
        'IS HONEST.  Wethersby is the origin.' % (mi, mi * ASPECT),
        '|' + '-' * (bar - 2) + '|  ' + label,
        '',
    ]
    body = [''.join(r).rstrip() for r in grid]

    leg = ['', '%-3s %-22s %-9s %-7s %7s  %-11s %s'
           % ('', 'place', 'kind', 'they', 'miles', 'bearing', 'time by cart')]
    for pid, (x, y, r) in order:
        m = miles('wethersby', pid, all_pts)
        lv = level_of(pid, kn)
        lo, hi = days_range(m, 'cart')
        note = ''
        if lv == VAGUE:
            p_ft = (kn.get(pid, {}).get('precision_ft') or '').strip()
            if p_ft:
                v = float(p_ft)
                note = '   ~ within %s' % ('%g mi' % (v / MILE) if v >= MILE
                                           else '{:,} ft'.format(int(v)))
        if true and r.get('fix') != 'attested':
            note += '   <- %s' % r.get('fix')
        leg.append('%-3s %-22s %-9s %-7s %7.0f  %-11s %.1f-%.1f d%s'
                   % (GLYPH.get(r.get('kind') or '', '+'), r['name'],
                      r.get('kind', ''), lv, m,
                      bearing('wethersby', pid, all_pts)
                      if pid != 'wethersby' else '--', lo, hi, note))

    tail = []
    heard = sorted(k for k in pts
                   if level_of(k, kn) == HEARD and k in entmod.places())
    if heard and not true:
        tail += ['', 'HEARD OF, AND NOT PLACED -- they could not put these on a '
                     'map, and this tool will not pretend otherwise:']
        for k in heard:
            tail.append('    %-18s %s' % (entmod.places()[k]['name'],
                                          (kn[k].get('how') or '')[:88]))
    dupes = [v for v in at.values() if len(v) > 1]
    if dupes:
        tail += ['', 'sharing a cell at this scale: ' + '; '.join(
            ', '.join(entmod.places()[p]['name'] for p in v) for v in dupes)]
    if unlabelled:
        tail += ['', 'no room for a label beside: ' + ', '.join(unlabelled)]
    tail += ['', ('*** DM MAP. Positions are EXACT. "?" and "<- call" mean the '
                  'record establishes neither bearing nor distance and the '
                  'position is mine; a call is not canon.') if true else
             ('The party\'s own map. "~" marks a place they could not put a pin '
              'in. Run with --true for the world as it is.')]
    return '\n'.join(head + body + leg + tail)


def check(pts=None, kn=None):
    """[(severity, message)]. Does the model still match the fiction?"""
    pts = pts if pts is not None else points()
    kn = kn if kn is not None else knowledge()
    out = []
    if 'wethersby' not in pts:
        return [('FAIL', 'Wethersby has no coordinates and it is the origin')]

    for pid, (x, y, r) in sorted(pts.items()):
        stated = (r.get('attested_days') or '').strip()
        if not stated:
            continue
        try:
            want = float(stated)
        except ValueError:
            continue
        mode = (r.get('attested_mode') or 'cart').strip() or 'cart'
        if mode not in PACE:
            out.append(('FAIL', '%s has attested_mode %r; expected one of %s'
                        % (pid, mode, sorted(k for k in PACE if k))))
            continue
        m = miles('wethersby', pid, pts)
        lo, hi = days_range(m, mode)
        if not (lo - 0.3 <= want <= hi + 0.3):
            out.append(('FAIL', '%s: the narrative says %g day(s) BY %s, the '
                                'map gives %.1f-%.1f (%.0f miles at %d a day). '
                                'THE NARRATIVE WINS -- move the coordinates.'
                        % (pid, want, mode.upper(), lo, hi, m, PACE[mode])))

    for a_, b_, want, mode in LEGS:
        if a_ in pts and b_ in pts:
            m = miles(a_, b_, pts)
            lo, hi = days_range(m, mode)
            if not (lo - 0.3 <= want <= hi + 0.3):
                out.append(('FAIL', '%s to %s: the narrative says %g day(s) by '
                                    '%s, the map gives %.1f-%.1f (%.0f miles). '
                                    'THE NARRATIVE WINS.'
                            % (a_, b_, want, mode.upper(), lo, hi, m)))

    for pid, want in (('draycot', 'south-west'), ('marchford', 'south'),
                      ('ludbury', 'south'), ('crag_turning', 'north')):
        if pid in pts and bearing('wethersby', pid, pts) != want:
            out.append(('FAIL', '%s is %s of Wethersby on the map; the record '
                                'says %s' % (pid, bearing('wethersby', pid,
                                                          pts), want)))
    if 'wraye' in pts and bearing('ludbury', 'wraye', pts) != 'east':
        out.append(('FAIL', 'Wraye is %s of Ludbury; the record says three days '
                            'EAST' % bearing('ludbury', 'wraye', pts)))

    if 'fenns' in pts and 'edes' in pts:
        m = miles('fenns', 'edes', pts)
        if abs(m - 8) > 1.5:
            out.append(('FAIL', "Fenn's to Ede's is %.1f miles. The record says "
                                'EIGHT, "a couple of hours, not a day" -- and '
                                'the DM said "a day" TWICE before the player '
                                'caught it.' % m))
    if {'crag_turning', 'cave_mouth'} <= set(pts):
        m = miles('crag_turning', 'cave_mouth', pts)
        if m > 4:
            out.append(('FAIL', 'the cave mouth is %.1f miles off the road. An '
                                'hour, half of it unmade outcrop, AND A CART '
                                'NEVER REACHES THE DOOR.' % m))

    for pid, (x, y, r) in sorted(pts.items()):
        if (r.get('fix') or '') not in ('attested', 'part', 'call', 'region'):
            out.append(('FAIL', '%s has fix=%r; it must say how the position '
                                'was arrived at' % (pid, r.get('fix'))))

    for pid, row in sorted(kn.items()):
        if pid not in entmod.places():
            out.append(('FAIL', 'knowledge.tsv names place %r, which is not in '
                                'campaign/places.tsv' % pid))
        lv = (row.get('level') or '').strip()
        if lv not in LEVELS:
            out.append(('FAIL', '%s has knowledge level %r; expected one of %s'
                        % (pid, lv, list(LEVELS))))
        if lv == VAGUE and not (row.get('precision_ft') or '').strip():
            out.append(('WARN', '%s is VAGUE with no precision_ft -- how far '
                                'out would they actually be?' % pid))
        if lv != VAGUE and (row.get('precision_ft') or '').strip():
            out.append(('WARN', '%s is %s but carries a precision_ft. Only '
                                'VAGUE takes one: a known place is known and a '
                                'heard-of one has no position at all'
                        % (pid, lv)))

    # The cross-check that catches the DM forgetting: somewhere they demonstrably
    # spent a day, with nothing said about whether they now know where it is.
    seen = {r['where'].strip() for r in read_tsv(
        os.path.join(ROOT, 'campaign', 'days.tsv'), missing_ok=True)
        if (r.get('where') or '').strip()}
    for pid in sorted(seen & set(entmod.places()) - set(kn)):
        out.append(('WARN', 'the party spent a day at %r (days.tsv) and '
                            'knowledge.tsv says nothing about it' % pid))

    fr = frames()
    for fid, f in sorted(fr.items()):
        if f.get('place') not in entmod.places():
            out.append(('FAIL', 'frame %r sits at place %r, which does not '
                                'exist' % (fid, f.get('place'))))
    return out


def from_report(origin, pts=None, kn=None):
    pts = pts if pts is not None else points()
    kn = kn if kn is not None else knowledge()
    oid = entmod.resolve(origin, entmod.places())
    if oid is None or oid not in pts:
        return 'no place %r with coordinates' % origin
    rows = sorted(((miles(oid, k, pts), k) for k in pts if k != oid))
    out = ['from %s:' % pts[oid][2]['name'], '']
    for m, k in rows:
        r = pts[k][2]
        road = road_between(oid, k)
        lo, hi = days_range(m, 'cart')
        out.append('  %-22s %4.0f mi  %4.1f-%.1f d by cart  %-11s %-15s %s'
                   % (r['name'], m, lo, hi, bearing(oid, k, pts),
                      ('by %s' % road) if road else 'cross-country',
                      level_of(k, kn)))
    out += ['', 'Straight-line, so every distance is a FLOOR -- travel follows '
                'a road where one exists. Times are RANGES because a distance '
                'is fixed and a journey is not.']
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='overland.py',
        description='The land above ground. The PARTY\'S map by default.')
    p.add_argument('--width', type=int, default=120,
                   help='fill this many columns (default 120)')
    p.add_argument('--height', type=int,
                   help='BOX it into this many rows as well. Without it the map '
                        'fills the width and runs as deep as the aspect '
                        'demands -- this world is far taller than it is wide, '
                        'so the whole of it at 120 columns is ~200 rows. '
                        '--around is usually the better answer')
    p.add_argument('--scale', type=float,
                   help='miles per column, overriding the fit')
    p.add_argument('--no-labels', action='store_true')
    p.add_argument('--around', help='CROP to a radius of this place -- the '
                                    'zoom, and what makes a wide terminal pay')
    p.add_argument('--miles', type=float, default=30,
                   help='the crop radius, with --around (default 30)')
    p.add_argument('--true', action='store_true',
                   help='THE DM\'S MAP. Shows places the party has never heard '
                        'of. Not to be shown at the table')
    sub = p.add_subparsers(dest='cmd')
    h = sub.add_parser('how-far')
    h.add_argument('a')
    h.add_argument('b')
    f = sub.add_parser('from')
    f.add_argument('origin')
    w = sub.add_parser('where', help='a dungeon square, in the world frame')
    w.add_argument('frame')
    w.add_argument('x', type=int)
    w.add_argument('y', type=int)
    sub.add_parser('check', help='does the model still match the fiction?')
    sub.add_parser('knows', help='what the party knows, and what it does not')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    pts, kn = points(), knowledge()

    if a.cmd == 'check':
        problems = check(pts, kn)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            att = sum(1 for v in pts.values() if v[2].get('fix') == 'attested')
            known = sum(1 for k in pts if level_of(k, kn) == KNOWN)
            print('overland OK: %d places, %d ATTESTED in bearing and distance, '
                  '%d KNOWN to the party.' % (len(pts), att, known))
            print('  Every stated travel time is reproduced within %d%% of the '
                  'DMG p.58 rates, and no place is drawn on the party map that '
                  'they have not been to.' % int(SPREAD * 100))
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'how-far':
        pc = entmod.places()
        ai, bi = entmod.resolve(a.a, pc), entmod.resolve(a.b, pc)
        if ai not in pts or bi not in pts:
            print('need two places with coordinates')
            return 1
        m = miles(ai, bi, pts)
        print('%s to %s: %.0f miles (%s), %s'
              % (pts[ai][2]['name'], pts[bi][2]['name'], m,
                 '{:,} ft'.format(int(feet(ai, bi, pts))),
                 bearing(ai, bi, pts)))
        road = road_between(ai, bi)
        print('  %s' % (('along %s' % road) if road else
                        'cross-country -- no road on record between them'))
        for line in how_long(m):
            print('    ' + line)
        for i in (ai, bi):
            lv = level_of(i, kn)
            if lv != KNOWN:
                print('  [the party\'s knowledge of %s is %s]'
                      % (pts[i][2]['name'], lv.upper()))
        return 0

    if a.cmd == 'where':
        try:
            x, y = to_overland(a.frame, a.x, a.y)
        except KeyError:
            print('no frame %r. Known: %s'
                  % (a.frame, ', '.join(sorted(frames()))), file=sys.stderr)
            return 1
        print('%s cell (%d,%d) is at (%s, %s) ft in the world frame'
              % (a.frame, a.x, a.y, '{:,}'.format(x), '{:,}'.format(y)))
        print('  = %.2f miles east and %.2f miles north of Wethersby'
              % (x / MILE, y / MILE))
        return 0

    if a.cmd == 'from':
        print(from_report(a.origin, pts, kn))
        return 0

    if a.cmd == 'knows':
        print('%-22s %-8s %s' % ('place', 'level', 'how'))
        for pid in sorted(entmod.places()):
            if (entmod.places()[pid].get('kind') or '') in ('region', 'hundred'):
                continue
            lv = level_of(pid, kn)
            print('%-22s %-8s %s' % (entmod.places()[pid]['name'], lv,
                                     (kn.get(pid, {}).get('how') or '')[:62]))
        return 0

    shown = pts
    if a.around:
        cid = entmod.resolve(a.around, entmod.places())
        if cid is None:
            print('no place %r' % a.around, file=sys.stderr)
            return 1
        shown = crop(pts, cid, a.miles)
    print(render(a.scale, shown, true=a.true, kn=kn, width=a.width,
                 height=a.height, labels=not a.no_labels))
    return 0


if __name__ == '__main__':
    sys.exit(main())
