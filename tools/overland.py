#!/usr/bin/env python3
"""The land above ground: distances, bearings, and what the party knows.

    python tools/overland.py                      # everywhere, from Wethersby
    python tools/overland.py how-far Draycot Marchford
    python tools/overland.py from Marchford
    python tools/overland.py where b1_level1 16 1  # a dungeon square, in the world
    python tools/overland.py knows
    python tools/overland.py check                 # does the model still match
                                                   # the fiction? exit 1 if not

*** THIS TOOL NO LONGER DRAWS A MAP, AND THAT IS DELIBERATE. ***

An ASCII renderer lived here for a day. The player asked the right question --
was it actually easier to READ than the data behind it? -- and the answer was
no. Reading "which town lies north-west of Wethersby" off a character grid means
reconstructing coordinates from column positions, which is strictly harder than
reading the coordinates. Every question the DM actually asks has a better answer
in a query, and all of them are above.

*** AND A PASTED MAP IS A STALE MAP. *** A rendering in the conversation is
correct at the instant it is made and never again; reading a position back off
one is narrating from a summary instead of from the log, which is the largest
error class in this campaign. **Render it for the player -- `tools/mapimg.py`,
which draws SVG and can show an uncertainty as an actual circle. Query it for
yourself, here.**

THE TWO LAYERS. `campaign/places.tsv` is the TRUE map and it is EXACT: the world
is where it is, distance is fixed, and only TIME varies. `campaign/knowledge.tsv`
is what the PARTY knows, which is where the uncertainty belongs -- known, vague,
heard, unknown. The campaign already drew that distinction one level down, where
`mapdb` separates what a square IS from `cells.seen`.

THE SCALE IS THE BOOK'S: `rules/overland.md`, DMG p.58. A cart does 25 miles a
day on a road, a laden walk 20, a medium mount 40. An earlier draft used a
DM-invented 18 per CART-day, taken off a WALKING figure.
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

# A road is NORMAL terrain for a vehicle; a track is RUGGED; a path is neither.
# rules/overland.md, DMG p.58 -- so `kind` here changes how long a journey
# takes, and is not decoration.
WAY_PACE = {'road': {'cart': 25, 'ride': 40, 'walk': 20},
            'track': {'cart': 15, 'ride': 20, 'walk': 10},
            'path': {'cart': None, 'ride': 20, 'walk': 10}}

KNOWN, VAGUE, HEARD, UNKNOWN = 'known', 'vague', 'heard', 'unknown'
LEVELS = (KNOWN, VAGUE, HEARD, UNKNOWN)



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOW = os.path.join(ROOT, 'campaign', 'knowledge.tsv')
WAYS = os.path.join(ROOT, 'campaign', 'roads.tsv')
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


# *** A DAILY RATE IS NOT AN HOURLY PACE, AND DIVIDING ONE BY A DAY IS WRONG ON
# *** A SHORT LEG. Player-caught, day 98.
#
# rules/overland.md's figures are DMG p.58 DAILY rates: what a party covers in a
# day of travel, rests, obstacles, watering and all. Everything in this file
# divides them, which is right at the scale they were written for -- Wethersby to
# Ludbury, Draycot to the south-west way -- and quietly absurd below it.
#
# THE CASE: basecamp to the dry watercourse is 2 miles. "off the road" divides
# 10 mi/day and prints 0.2-0.3 days, which the DM read as two and a half hours
# and narrated. The player: "If we took 2 hours to go those 2 miles, which would
# be very, very slow, we would be there at 1 PM." He is right. A party on a
# beaten trail walks two miles in an hour and a half without trying.
#
# The numbers are NOT changed -- they are the book's and they are correct for a
# day's march. What is added is the warning, because the failure was in the
# READING and the tool printed a figure that invited it.
SHORT_LEG_MI = 6.0
SHORT_LEG_WARNING = [
    '  *** SHORT LEG -- THESE TIMES ARE DAILY RATES DIVIDED AND THEY OVERSTATE',
    '  IT. *** DMG p.58 gives what a party covers in a DAY, rests and obstacles',
    '  included; nobody walks a full day at a constant pace. Under a few miles,',
    '  cost it at the ACTUAL pace: ~3 mi/hour on a road, ~2 leading animals,',
    '  ~1.5 over rough ground or a game trail, and less only if something in the',
    '  fiction says so. THE DISTANCE IS STILL EXACT. It is the clock that needs',
    '  reading with judgment.',
]


def how_long(m):
    """Every ordinary way of covering `m` miles, as a range of days.

    *** ride_light IS LISTED BECAUSE THE PARTY OWNS LIGHT HORSES. *** It was in
    PACE from the start and printed nowhere, so `how-far` answered "at a medium
    ride 40" for two riders the record puts at SIXTY -- days 84 and 90 were both
    planned on 60 and are right (rules/overland.md, DMG p.58: light 60, medium
    40). A mode the party is actually in, missing from the only place anybody
    reads, is a wrong answer waiting for a session that does not remember why.
    """
    out = []
    for mode, label in (('cart', 'by cart'), ('ride_light', 'at a light ride'),
                        ('ride', 'at a medium ride'),
                        ('walk', 'walking laden'), ('walk_rough', 'off the road')):
        lo, hi = days_range(m, mode)
        out.append('%-18s %4.1f - %.1f days' % (label, lo, hi))
    if m < SHORT_LEG_MI:
        out.append('')
        out += SHORT_LEG_WARNING
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


def roads(path=None):
    """{id: row}. Was a dict inside this file, which is data in code."""
    return {r['id']: r for r in read_tsv(path or WAYS, missing_ok=True)
            if r.get('id')}


def stops_of(r):
    return [s.strip() for s in (r.get('stops') or '').split(',') if s.strip()]


ROADS = None        # filled on first use, so callers can still iterate ways


def ways(kn=None, true=True):
    """{name: [stops]}. With `true=False`, only what the PARTY knows about.

    *** A ROAD IS A SPOILER TOO. *** The party has never asked where Sir Aymer's
    clip goes, and it goes to Ludbury by a road that does not pass their town --
    which is most of why nobody in Wethersby could say where the staple went.
    Drawing that road on their map would hand them the answer in a picture.
    """
    kn = kn if kn is not None else knowledge()
    out = {}
    for r in roads().values():
        if not true and level_of(r['id'], kn) in (HEARD, UNKNOWN):
            continue
        out[r['name']] = stops_of(r)
    return out


def road_between(a, b):
    for r in roads().values():
        st = stops_of(r)
        if a in st and b in st:
            return r['name']
    return None


def way_kind(a, b):
    for r in roads().values():
        st = stops_of(r)
        if a in st and b in st:
            return r.get('kind') or 'road'
    return None


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

    ids = set(entmod.places())
    for r in roads().values():
        for st in stops_of(r):
            if st not in ids:
                out.append(('FAIL', 'road %r stops at %r, which is not in '
                                    'campaign/places.tsv' % (r['id'], st)))
        if (r.get('kind') or '') not in WAY_PACE:
            out.append(('FAIL', 'road %r has kind %r; expected one of %s'
                        % (r['id'], r.get('kind'), sorted(WAY_PACE))))

    # A turning must actually BE on the road it turns off.
    for tid, main in (('lyde_turning', 'north_road'),
                      ('fenns_turning', 'north_road')):
        if tid in pts and main in roads():
            if tid not in stops_of(roads()[main]):
                out.append(('FAIL', '%s is not a stop on %s -- a junction that '
                                    'is not on the road is not a junction'
                            % (tid, main)))
            elif abs(pts[tid][0] - pts['wethersby'][0]) > 2000:
                out.append(('FAIL', '%s sits %0.1f miles off the line of the '
                                    'north road' % (tid,
                                                    abs(pts[tid][0]) / MILE)))

    # "A day off the road each way" -- on a TRACK, which is the point.
    if {'lyde', 'lyde_turning'} <= set(pts):
        m = miles('lyde_turning', 'lyde', pts)
        d = m / WAY_PACE['track']['ride']
        if not (0.6 <= d <= 1.4):
            out.append(('FAIL', 'the Lyde track is %.0f miles, %.1f days by a '
                                'rider at track pace. The record says A DAY OFF '
                                'THE ROAD EACH WAY.' % (m, d)))
    if {'fenns', 'fenns_turning'} <= set(pts):
        m = miles('fenns_turning', 'fenns', pts)
        if abs(m - 4) > 1:
            out.append(('FAIL', "the Fenn's track is %.1f miles. The record "
                                'says FOUR MILES EAST OF THE ROAD.' % m))

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

    # A knowledge row is about a PLACE or about a WAY. Both are things the
    # party can know, and a road they have never heard of is exactly as real as
    # a town they have never heard of.
    ways_ = roads()
    for pid, row in sorted(kn.items()):
        is_place, is_way = pid in entmod.places(), pid in ways_
        if not (is_place or is_way):
            out.append(('FAIL', 'knowledge.tsv names %r, which is neither a '
                                'place nor a road' % pid))
        lv = (row.get('level') or '').strip()
        if lv not in LEVELS:
            out.append(('FAIL', '%s has knowledge level %r; expected one of %s'
                        % (pid, lv, list(LEVELS))))
        # A PRECISION IS A RADIUS AROUND A POINT, so only a place takes one.
        # You do not know a road to within a thousand feet; you know where it
        # goes or you do not quite.
        if is_place:
            if lv == VAGUE and not (row.get('precision_ft') or '').strip():
                out.append(('WARN', '%s is VAGUE with no precision_ft -- how '
                                    'far out would they actually be?' % pid))
            if lv != VAGUE and (row.get('precision_ft') or '').strip():
                out.append(('WARN', '%s is %s but carries a precision_ft. Only '
                                    'VAGUE takes one: a known place is known '
                                    'and a heard-of one has no position at all'
                            % (pid, lv)))
        elif (row.get('precision_ft') or '').strip():
            out.append(('WARN', '%s is a ROAD and carries a precision_ft. A '
                                'precision is a radius around a point' % pid))

    for rid in sorted(ways_):
        if rid not in kn:
            out.append(('WARN', 'road %r has no row in knowledge.tsv. Every '
                                'way gets one explicitly -- a default would be '
                                'a guess about what the party has travelled'
                        % rid))

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
        kind = way_kind(oid, k)
        out.append('  %-22s %4.0f mi  %4.1f-%.1f d by cart  %-11s %-24s %s'
                   % (r['name'], m, lo, hi, bearing(oid, k, pts),
                      ('by %s%s' % (road, ' (TRACK)' if kind == 'track' else ''))
                      if road else 'no way on record', level_of(k, kn)))
    out += ['', 'Straight-line, so every distance is a FLOOR -- travel follows '
                'a road where one exists. Times are RANGES because a distance '
                'is fixed and a journey is not.']
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='overland.py',
        description='Distances, bearings, and what the party knows. '
                    'For a DRAWN map see tools/mapimg.py.')
    sub = p.add_subparsers(dest='cmd')
    h = sub.add_parser('how-far')
    h.add_argument('a')
    h.add_argument('b')
    f = sub.add_parser('from', help='everywhere, by distance from one place')
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
        road, kind = road_between(ai, bi), way_kind(ai, bi)
        if road:
            print('  along %s -- a %s, so %s'
                  % (road, kind,
                     'cart 15 a day, rider 20' if kind == 'track'
                     else 'no cart at all' if kind == 'path'
                     else 'cart 25 a day, rider 40 on a medium horse '
                          'and 60 on a light one'))
        else:
            print('  NO WAY ON RECORD between them -- a straight line across '
                  'somebody\'s fields is not a route')
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

    # No subcommand: the TABLE, which is the thing worth reading.
    print(from_report('wethersby', pts, kn))
    return 0


if __name__ == '__main__':
    sys.exit(main())
