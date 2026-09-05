#!/usr/bin/env python3
"""Find secret-door, concealed-door and trap-door markers on a scanned map.

    conda activate advanced_dnd_1e
    python markers.py --db dmg.sqlite --sheet images/15_markers.png

Why this needs its own detector
-------------------------------
These markers are printed letters -- S, C, a boxed X -- drawn ASTRIDE the wall
they annotate. Straddling the wall means they touch the rock, and touching the
rock means the connectivity pass in extract.rock_mask() swallows them into the
rock mass: every known marker on the DMG sheet measures ink = 0.000. They are
invisible to the annotation layer that finds room numbers.

What they do leave is a signature in the rock itself. A printed letter is built
from THIN STROKES (4-6 px at 200 dpi) where structural rock is a thick mass, so
a morphological opening erases the glyph and keeps the rock; the difference is
the glyph. Rulings are thin too, so the grid lines are masked off, and what
survives near a boundary is a mark somebody drew there.

This does NOT replace reading the module text. It is a second, independent
reading of the same fact, and the two are meant to disagree loudly.
"""
import argparse
import os
import sqlite3
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import extract as E

PASSABLE = ('open', 'door', 'secret', 'concealed', 'archway', 'one_way',
            'portcullis', 'trap_door', 'stairs')
WALKABLE = ('open', 'mixed')


def thin_rock(rock, radius=4):
    """Rock that a disk of `radius` cannot fit inside: printed strokes, not mass."""
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    disk = (xx * xx + yy * yy) <= radius * radius
    return rock & ~ndimage.binary_opening(rock, disk)


def _ruling_mask(grid, shape, band=0.16):
    """True away from every grid line, where the printed rulings live."""
    h, w = shape
    gx = np.ones(w, bool)
    gy = np.ones(h, bool)
    b = max(1, int(band * grid.px))
    for v in grid.xlines():
        gx[max(0, int(v) - b):min(w, int(v) + b)] = False
    for v in grid.ylines():
        gy[max(0, int(v) - b):min(h, int(v) + b)] = False
    return np.outer(gy, gx)


def candidates(rock, grid, radius=4, min_area=40, min_dim=5, max_aspect=4.5,
               max_off_line=None):
    """Glyph-sized clumps of thin rock lying clear of the rulings.

    A single letter often breaks into pieces where it crosses a ruling, so
    fragments within about half a square of each other are merged.
    """
    mask = thin_rock(rock, radius) & _ruling_mask(grid, rock.shape)
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    raw = []
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        area = int((lab[sl] == k).sum())
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if area < min_area or min(h, w) < min_dim:
            continue
        if max(h, w) > 1.5 * grid.px:
            continue
        if max(h, w) / max(1, min(h, w)) > max_aspect:
            continue
        raw.append(dict(area=area, w=w, h=h,
                        cx=(sl[1].start + sl[1].stop) / 2.0,
                        cy=(sl[0].start + sl[0].stop) / 2.0))
    out = []
    for c in sorted(raw, key=lambda c: -c['area']):
        for m in out:
            if (abs(m['cx'] - c['cx']) < 0.6 * grid.px
                    and abs(m['cy'] - c['cy']) < 0.6 * grid.py):
                m['area'] += c['area']
                break
        else:
            out.append(c)
    for c in out:
        c.update(_locate(c, grid))
    # keep only marks inside the drawn grid: the printed legend sits below the
    # map on B1's sheet and otherwise arrives as candidates at negative y
    out = [c for c in out if 0 <= c['x'] < grid.nx and 0 <= c['y'] < grid.ny]
    if max_off_line is not None:
        # a door marker annotates a WALL, so it is drawn on or beside one. On a
        # furnished map (B1 draws every table and bed) this is what separates a
        # marker from the furniture, which sits out in the middle of a room.
        out = [c for c in out if c['off_line'] <= max_off_line]
    return sorted(out, key=lambda c: -c['area'])


def _locate(c, grid):
    """Cell the glyph sits in, and the boundary it most likely annotates."""
    fx = (c['cx'] - grid.x0) / grid.px
    fy = (c['cy'] - grid.y0) / grid.py
    i, j = int(fx), int(fy)
    dx = abs(fx - round(fx))
    dy = abs(fy - round(fy))
    if dx <= dy:                      # nearer a vertical ruling
        line = int(round(fx))
        edge = (line - 1, grid.gy(j), 'V')
    else:
        line = int(round(fy))
        edge = (i, grid.gy(line), 'H')
    return dict(x=i, y=grid.gy(j), edge=edge, off_line=float(min(dx, dy)))


# ------------------------------------------------------------- corroboration

def isolated_regions(db, level, start_room='1', start_cell=None):
    """Connected groups of walkable squares that cannot reach the entrance.

    An isolated region is not merely a curiosity: on a real dungeon level every
    square is reachable, so the region MUST have a way in, and the way in must
    be something the extractor could not see -- which is exactly what a secret
    or concealed door is. This is the independent check on the glyph detector,
    and it needs no human and no reference map.
    """
    import dmap
    cells, edges = dmap.load(db, level)
    walk = {k for k, v in cells.items()
            if v[0] in WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    if start_cell is None:
        con = sqlite3.connect(db)
        row = con.execute(
            'SELECT anchor_x,anchor_y FROM rooms WHERE level=? AND number=?',
            (level, str(start_room))).fetchone()
        con.close()
        if not row or row[0] is None:
            return []
        start_cell = (row[0], row[1])
    if start_cell not in walk:
        return []
    seen, stack = {start_cell}, [start_cell]
    while stack:
        x, y = stack.pop()
        for dx, dy, ex, ey, o in ((1, 0, x, y, 'V'), (-1, 0, x - 1, y, 'V'),
                                  (0, 1, x, y, 'H'), (0, -1, x, y - 1, 'H')):
            nxt = (x + dx, y + dy)
            if nxt in seen or nxt not in walk:
                continue
            if edges.get((ex, ey, o), 'unknown') in PASSABLE:
                seen.add(nxt)
                stack.append(nxt)
    missed = walk - seen
    if not missed:
        return []
    idx = {c: n for n, c in enumerate(sorted(missed))}
    parent = list(range(len(idx)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for (x, y), n in idx.items():
        for nb in ((x + 1, y), (x, y + 1)):
            if nb in idx:
                parent[find(n)] = find(idx[nb])
    groups = {}
    for c, n in idx.items():
        groups.setdefault(find(n), []).append(c)
    return [sorted(v) for v in groups.values()]


def boundary_edges(region):
    """Every canonical edge on the outside of a region."""
    cells = set(region)
    out = set()
    for x, y in cells:
        if (x + 1, y) not in cells:
            out.add((x, y, 'V'))
        if (x - 1, y) not in cells:
            out.add((x - 1, y, 'V'))
        if (x, y + 1) not in cells:
            out.add((x, y, 'H'))
        if (x, y - 1) not in cells:
            out.add((x, y - 1, 'H'))
    return out


def corroborate(cands, regions, radius=1):
    """Match candidates against isolated regions.

    A candidate sitting on the boundary of a region that cannot otherwise be
    reached is confirmed by two independent readings at once, and needs no
    human at all. A region with no candidate on its boundary means the detector
    missed something and is where a human should actually look.
    """
    confirmed, unexplained = [], []
    used = set()
    for region in regions:
        bounds = boundary_edges(region)
        hits = []
        for k, c in enumerate(cands):
            ex, ey, eo = c['edge']
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if (ex + dx, ey + dy, eo) in bounds:
                        hits.append(k)
                        break
                else:
                    continue
                break
        if hits:
            for k in hits:
                if k not in used:
                    used.add(k)
                    confirmed.append((cands[k], region))
        else:
            unexplained.append(region)
    unmatched = [c for k, c in enumerate(cands) if k not in used]
    return confirmed, unmatched, unexplained


def near(edge, bounds, radius=1):
    ex, ey, eo = edge
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if (ex + dx, ey + dy, eo) in bounds:
                return True
    return False


def resolve(db, level, cands, from_room='1', kind='secret', max_rounds=20,
            confidence=6, start_cell=None, report=None):
    """Iteratively open sealed regions using the candidates on their boundaries.

    One pass is not enough. A sealed region the size of half the map touches
    dozens of candidates, and confirming any one of them explains the whole
    region at once, leaving the rest looking spurious. Applying the best
    candidate and re-running reachability shrinks the region, which sharpens
    the next attribution -- so the map is opened one door at a time and each
    door has to earn its own sealed region.

    Matching is EXACT-FIRST. A candidate whose edge lies exactly on a region's
    boundary is assigned to that region before any near-miss is considered
    anywhere on the map. Without that ordering a neighbouring region claims the
    candidate through the +/-1 tolerance and marks it used, and the region that
    actually needed it stays sealed -- which is how B1's area 14 secret door
    was detected and then silently dropped.

    `report` collects candidates that touched a sealed region but were never
    applied, so a drop is always visible rather than silent.
    """
    applied, used = [], set()
    skipped = report if report is not None else []
    for _ in range(max_rounds):
        regions = isolated_regions(db, level, from_room, start_cell)
        if not regions:
            break
        bounds = [boundary_edges(r) for r in regions]
        # (0 = exact, 1 = near) then largest glyph first, globally ordered
        pairs = []
        for ri, b in enumerate(bounds):
            for n, c in enumerate(cands):
                if n in used:
                    continue
                if c['edge'] in b:
                    pairs.append((0, -c['area'], ri, n))
                elif near(c['edge'], b):
                    pairs.append((1, -c['area'], ri, n))
        pairs.sort()
        taken_region, taken_cand = set(), set()
        con = sqlite3.connect(db)
        progress = False
        for rank, _, ri, n in pairs:
            if ri in taken_region or n in taken_cand:
                continue
            c = cands[n]
            ex, ey, eo = c['edge']
            cur = con.execute(
                "UPDATE edges SET kind=?, confidence=?,"
                " notes=notes||' | marker glyph area '||?||', corroborated by "
                "reachability (sealed '||?||' squares, '||?||' match)'"
                " WHERE level=? AND x=? AND y=? AND orient=? AND kind='wall'",
                (kind, confidence, c['area'], len(regions[ri]),
                 'exact' if rank == 0 else 'near', level, ex, ey, eo))
            if not cur.rowcount:
                continue
            taken_region.add(ri)
            taken_cand.add(n)
            used.add(n)
            applied.append(dict(c, sealed=len(regions[ri]),
                                match='exact' if rank == 0 else 'near'))
            progress = True
        con.commit()
        con.close()
        if not progress:
            # nothing could be applied: record what was on offer and stop
            for ri, b in enumerate(bounds):
                for n, c in enumerate(cands):
                    if n not in used and (c['edge'] in b or near(c['edge'], b)):
                        skipped.append(dict(c, sealed=len(regions[ri])))
            break
    return applied


# ------------------------------------------------------------- contact sheet

def sheet(cands, rgb, grid, path, tile=250, cols=5, confirmed=()):
    conf = {id(c) for c in confirmed}
    im = Image.fromarray(rgb).convert('RGB')
    tiles = []
    for n, c in enumerate(cands, start=1):
        xa, xb = int(c['cx'] - 1.3 * grid.px), int(c['cx'] + 1.3 * grid.px)
        ya, yb = int(c['cy'] - 1.3 * grid.py), int(c['cy'] + 1.3 * grid.py)
        crop = im.crop((max(0, xa), max(0, ya), xb, yb))
        s = min(tile / max(1, crop.width), tile / max(1, crop.height))
        crop = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))),
                           Image.LANCZOS)
        t = Image.new('RGB', (tile, tile + 20), 'white')
        t.paste(crop, ((tile - crop.width) // 2, 20))
        d = ImageDraw.Draw(t)
        ex, ey, eo = c['edge']
        d.text((4, 5), '#%d (%d,%d) %s edge %d,%d,%s%s'
               % (n, c['x'], c['y'], 'OK' if id(c) in conf else '?', ex, ey, eo,
                  ''), fill=(180, 0, 0))
        d.rectangle([0, 0, tile - 1, tile + 19], outline=(0, 0, 0))
        tiles.append(t)
    if not tiles:
        return path
    rows = (len(tiles) + cols - 1) // cols
    canvas = Image.new('RGB', (cols * (tile + 4), rows * (tile + 24)), 'white')
    for k, t in enumerate(tiles):
        canvas.paste(t, ((k % cols) * (tile + 4), (k // cols) * (tile + 24)))
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    canvas.save(path)
    return path


def render_settings(db, level):
    """The pdf/page/dpi/channel/deskew the database was built with.

    Reproducing the build's grid exactly is not optional: a tool that
    re-renders with its own defaults gets a grid offset by up to a quarter of a
    square on a map that needed deskewing, and then assigns every marker it
    finds to the wrong edge.
    """
    con = sqlite3.connect(db)
    try:
        row = con.execute('SELECT pdf,page,dpi,channel,deskew_deg FROM levels'
                          ' WHERE level=?', (level,)).fetchone()
    except sqlite3.OperationalError:
        return None
    finally:
        con.close()
    if not row or row[0] is None:
        return None
    return dict(pdf=row[0], page=row[1], dpi=row[2] or 200,
                channel=row[3] or 'mean', deskew=row[4] or 0.0)


def build_parser():
    p = argparse.ArgumentParser(
        prog='markers.py',
        description='Find secret/concealed/trap-door markers and corroborate them '
                    'against the reachability check.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--db', default='output/dmg/dmg.sqlite',
                   help='map database to check against')
    p.add_argument('--level', type=int, default=1)
    p.add_argument('--pdf', default=None,
                   help='override the pdf recorded in the database')
    p.add_argument('--page', type=int, default=None,
                   help='override the page recorded in the database')
    p.add_argument('--dpi', type=int, default=None,
                   help='override the dpi recorded in the database')
    p.add_argument('--key', default='dmg_key',
                   help='key module, used to shield room labels; "none" to skip')
    p.add_argument('--from-room', default='1', help='entrance room for reachability')
    p.add_argument('--from-cell', type=int, nargs=2, metavar=('X', 'Y'),
                   help='start from an explicit cell instead of a room anchor')
    p.add_argument('--radius-px', type=int, default=None,
                   help=argparse.SUPPRESS)
    p.add_argument('--radius', type=int, default=4,
                   help='opening radius; rock a disk this big fits inside is structure')
    p.add_argument('--min-area', type=int, default=40, help='smallest glyph in px')
    p.add_argument('--min-dim', type=int, default=5, help='smallest glyph side in px')
    p.add_argument('--max-off-line', type=float, default=None,
                   help='discard marks further than this fraction of a square '
                        'from the nearest grid line. Needed on a furnished map '
                        'such as B1, where room furniture is also thin strokes')
    p.add_argument('--sheet', default='output/dmg/images/15_markers.png',
                   help='contact sheet of candidates to write')
    p.add_argument('--apply', action='store_true',
                   help='write corroborated markers into the database as secret '
                        'doors, opening sealed regions one at a time')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    protect_cells = None
    if args.key.lower() != 'none':
        import importlib
        import build
        protect_cells = build.label_cells(importlib.import_module(args.key))
    cfg = render_settings(args.db, args.level) or {}
    pdf = args.pdf or cfg.get('pdf')
    page = args.page if args.page is not None else cfg.get('page')
    dpi = args.dpi or cfg.get('dpi', 200)
    grey, rgb = E.render(pdf, page, dpi, channel=cfg.get('channel', 'mean'))
    if abs(cfg.get('deskew', 0.0)) > 1e-6:
        grey, rgb = E.deskew(grey, rgb, cfg['deskew'])
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)
    rock, _ = E.rock_mask(
        grey, protect=E.label_boxes(protect_cells, grid) if protect_cells else ())
    cands = candidates(rock, grid, args.radius, args.min_area, args.min_dim,
                       max_off_line=args.max_off_line)
    start = tuple(args.from_cell) if args.from_cell else None
    regions = isolated_regions(args.db, args.level, args.from_room, start)
    confirmed, unmatched, unexplained = corroborate(cands, regions)

    print('candidates            %d' % len(cands))
    print('isolated regions      %d' % len(regions))
    print('  corroborated        %d  (a marker on the boundary of a sealed region)'
          % len(confirmed))
    print('  unexplained         %d  (sealed, but no marker found -- look here)'
          % len(unexplained))
    print('unmatched candidates  %d  (a marker not sealing anything)' % len(unmatched))
    for c, region in confirmed:
        ex, ey, eo = c['edge']
        print('  CONFIRMED edge (%2d,%2d,%s)  glyph at (%2d,%2d) area %d'
              '  seals %d square(s)' % (ex, ey, eo, c['x'], c['y'], c['area'],
                                        len(region)))
    for region in unexplained:
        xs = [c[0] for c in region]; ys = [c[1] for c in region]
        print('  UNEXPLAINED region of %d squares, x%d-%d y%d-%d'
              % (len(region), min(xs), max(xs), min(ys), max(ys)))
    if args.apply:
        skipped = []
        applied = resolve(args.db, args.level, cands, args.from_room,
                          start_cell=start, report=skipped)
        print('\napplied %d marker(s), largest sealed region first:' % len(applied))
        for a in sorted(applied, key=lambda a: -a['sealed']):
            ex, ey, eo = a['edge']
            print('  edge (%2d,%2d,%s)  glyph (%2d,%2d) area %3d  opened %d square(s)'
                  % (ex, ey, eo, a['x'], a['y'], a['area'], a['sealed']))
        if skipped:
            print('\n%d candidate(s) touched a sealed region but could not be '
                  'applied (the edge was no longer a wall):' % len(skipped))
            for c in skipped[:12]:
                print('  edge %-14s glyph (%2d,%2d) area %3d  region of %d'
                      % (str(c['edge']), c['x'], c['y'], c['area'], c['sealed']))
        left = isolated_regions(args.db, args.level, args.from_room, start)
        print('still sealed after applying: %d region(s), %d square(s)'
              % (len(left), sum(len(r) for r in left)))
        for r in left:
            print('  %s' % sorted(r)[:8])
    if args.sheet:
        sheet(cands, rgb, grid, args.sheet, confirmed=[c for c, _ in confirmed])
        print('\nwrote %s' % args.sheet)
    return 0


if __name__ == '__main__':
    sys.exit(main())
