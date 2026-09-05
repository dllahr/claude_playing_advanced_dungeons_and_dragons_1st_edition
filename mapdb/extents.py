#!/usr/bin/env python3
"""Work out which squares belong to which area, and check the answer.

    conda activate advanced_dnd_1e
    python extents.py --db output/b1/b1.sqlite --key b1_key --apply

On these maps rooms and corridors are both plain white, so nothing in the image
says where one ends and the other begins. But a corridor is narrow and a room is
not, and on a grid that has an exact form: **a corridor never contains a 2x2
block of open floor, and a room does**. Testing for the block rather than
measuring a width needs no threshold and behaves at junctions, where a T of
1-wide corridors gives cells three open neighbours but still no block.

Rooms then grow from their printed labels -- multi-source breadth-first within
the wide mask, nearest seed winning -- with sub-locations folded into their base
area so 1, 1A and 1B stay one room rather than three.

Corridor and room are kept strictly separate: a doorway square is corridor. That
keeps "which squares are area 12" unambiguous, and it makes the wide areas that
end up with no label genuinely informative -- they are unlabelled chambers, or
extents that grew wrong.
"""
import argparse
import collections
import re
import sqlite3
import sys

import dmap

BASE = re.compile(r'^(\d+)')


def base_area(number):
    """'12' -> '12', '1B' -> '1'. Sub-locations belong to their area."""
    m = BASE.match(number)
    return m.group(1) if m else number


def opener(edges):
    """A function saying whether two adjacent squares are joined by open floor.

    Only 'open' counts. A door, a staircase or a secret door is a way through
    but it is also a boundary between spaces, so it must not let a room grow
    into the next one.
    """
    def is_open(a, b):
        (ax, ay), (bx, by) = a, b
        if bx == ax + 1:
            e = (ax, ay, 'V')
        elif bx == ax - 1:
            e = (bx, by, 'V')
        elif by == ay + 1:
            e = (ax, ay, 'H')
        else:
            e = (bx, by, 'H')
        return edges.get(e, 'unknown') == 'open'
    return is_open


def wide_cells(walk, is_open):
    """Squares belonging to some 2x2 block of mutually open floor."""
    wide = set()
    for (x, y) in walk:
        for ox, oy in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
            a = (x + ox, y + oy)
            b = (x + ox + 1, y + oy)
            c = (x + ox, y + oy + 1)
            d = (x + ox + 1, y + oy + 1)
            if not (a in walk and b in walk and c in walk and d in walk):
                continue
            if is_open(a, b) and is_open(c, d) and is_open(a, c) and is_open(b, d):
                wide.update((a, b, c, d))
    return wide


def grow(walk, wide, seeds, is_open):
    """{area: {cells}} by nearest-seed growth inside the wide mask.

    A label sitting in a 1-wide alcove -- B1's area 1 is six of them off the
    entrance corridor -- has no block to grow into, so it keeps its own square
    and nothing more.
    """
    owner = {}
    frontier = []
    for area, cells in seeds.items():
        for c in cells:
            if c in wide and c not in owner:
                owner[c] = area
                frontier.append(c)
    while frontier:
        nxt = []
        for (x, y) in frontier:
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in wide and n not in owner and is_open((x, y), n):
                    owner[n] = owner[(x, y)]
                    nxt.append(n)
        frontier = nxt
    for area, cells in seeds.items():
        for c in cells:
            if c not in owner and c in walk:
                owner[c] = area
    out = collections.defaultdict(set)
    for c, a in owner.items():
        out[a].add(c)
    return dict(out), {c for c in wide if c not in owner}


def derive(db, level):
    """(extents, corridor, unlabelled_wide) for a level."""
    cells, edges = dmap.load(db, level)
    walk = {k for k, v in cells.items()
            if v[0] in dmap.WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    is_open = opener(edges)
    wide = wide_cells(walk, is_open)
    con = sqlite3.connect(db)
    labels = list(con.execute(
        'SELECT number,x,y FROM room_labels WHERE level=?', (level,)))
    con.close()
    seeds = collections.defaultdict(set)
    for number, x, y in labels:
        seeds[base_area(number)].add((x, y))
    ext, spare = grow(walk, wide, dict(seeds), is_open)
    claimed = {c for v in ext.values() for c in v}
    return ext, walk - claimed, spare


# ---------------------------------------------------------------- checking

DIM = re.compile(
    r"(\d{1,3})\s*'\s*(?:by|x|X)\s*(\d{1,3})\s*'|(\d{1,3})\s*'\s*square", re.I)
ROOMWORD = re.compile(
    r'\b(room|chamber|hall|cellar|area|smithy|kitchen|library|barracks|armory|'
    r'annex|closet|lounge|storeroom)\b', re.I)


def stated_squares(text, foot=10, window=45):
    """Squares implied by a dimension the description gives FOR THE ROOM.

    Taking the first dimension in the text is wrong: descriptions size their
    contents too, and B1 sizes the floor mats in area 37 ("measuring 20' by
    20'") and an outcropping in area 22 before they ever size the room. The
    dimension only counts when a room word sits within `window` characters of
    it -- "This 20' by 20' room is used for..." qualifies, the mats do not.
    """
    text = text or ''
    for m in DIM.finditer(text):
        near = text[max(0, m.start() - window): m.end() + window]
        if not ROOMWORD.search(near):
            continue
        if m.group(3):
            side = int(m.group(3)) / foot
            return int(round(side * side))
        a, b = int(m.group(1)) / foot, int(m.group(2)) / foot
        return int(round(a * b))
    return None


def check_dimensions(ext, dims, tol=0.35):
    """Compare each extent to the size its description states.

    The text is an independent reading of the same room, so a disagreement
    means the walls, the label or the extent is wrong. This is the cross-check
    that the node graph could not provide for B1, whose descriptions say how big
    things are but not what they connect to.
    """
    rows = []
    for area, want in sorted(dims.items(), key=lambda kv: int(base_area(kv[0]))):
        got = len(ext.get(area, ()))
        if not want:
            continue
        ok = got and abs(got - want) <= max(1, tol * want)
        rows.append((area, want, got, ok))
    return rows


def check_extents(ext, verified):
    """Compare extents against sets of squares confirmed against the sheet.

    Stronger than comparing counts: a count can agree by accident, and when it
    disagrees it does not say where. This names the squares.
    """
    rows = []
    for area, cells in sorted(verified.items(), key=lambda kv: int(base_area(kv[0]))):
        want = set(map(tuple, cells))
        got = set(ext.get(area, ()))
        rows.append((area, want, got, want - got, got - want))
    return rows


# ---------------------------------------------------------------- cli

def apply_to_db(db, level, ext):
    con = sqlite3.connect(db)
    con.execute('UPDATE cells SET room=NULL WHERE level=?', (level,))
    for area, cells in ext.items():
        for (x, y) in cells:
            con.execute('UPDATE cells SET room=? WHERE level=? AND x=? AND y=?',
                        (area, level, x, y))
        con.execute('UPDATE rooms SET extent_sq=? WHERE level=? AND number=?',
                    (len(cells), level, area))
    con.commit()
    con.close()


def build_parser():
    p = argparse.ArgumentParser(
        prog='extents.py',
        description='Assign squares to areas by the 2x2 room-vs-corridor test.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='Run AFTER markers.py --apply: extents depend on which boundaries '
               'are open, and applying a secret door changes that.')
    p.add_argument('--db', default='output/dmg/dmg.sqlite')
    p.add_argument('--level', type=int, default=1)
    p.add_argument('--key', default=None,
                   help='key module supplying DIMENSIONS for the cross-check')
    p.add_argument('--apply', action='store_true',
                   help='write cells.room and rooms.extent_sq')
    p.add_argument('--tol', type=float, default=0.35,
                   help='fractional tolerance when comparing to stated size')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    ext, corridor, spare = derive(a.db, a.level)
    sizes = sorted(len(v) for v in ext.values())
    print('areas with an extent : %d' % len(ext))
    print('median / p90 / max   : %d / %d / %d squares'
          % (sizes[len(sizes) // 2], sizes[int(len(sizes) * 0.9)], sizes[-1]))
    print('corridor squares     : %d' % len(corridor))
    print('wide but unlabelled  : %d  (unnamed chambers, or an extent that grew wrong)'
          % len(spare))

    if a.key:
        import importlib
        dims = getattr(importlib.import_module(a.key), 'DIMENSIONS', {}) or {}
        verified = getattr(importlib.import_module(a.key), 'VERIFIED_EXTENTS', {}) or {}
        vrows = check_extents(ext, verified)
        if vrows:
            bad_v = [r for r in vrows if r[3] or r[4]]
            print('\nverified-extent check: %d areas confirmed by hand, %d disagree'
                  % (len(vrows), len(bad_v)))
            for area, want, got, missing, extra in bad_v:
                print('  area %-4s %d/%d squares; missing %s; extra %s'
                      % (area, len(got & want), len(want),
                         sorted(missing) or '-', sorted(extra) or '-'))
        rows = check_dimensions(ext, dims, a.tol)
        bad = [r for r in rows if not r[3]]
        print('\ndimension cross-check: %d areas state a size, %d disagree'
              % (len(rows), len(bad)))
        for area, want, got, ok in bad:
            print('  area %-4s text says %3d squares, extraction gives %3d'
                  % (area, want, got))
    if a.apply:
        apply_to_db(a.db, a.level, ext)
        print('\nwrote cells.room and rooms.extent_sq to %s' % a.db)
    return 0


if __name__ == '__main__':
    sys.exit(main())
