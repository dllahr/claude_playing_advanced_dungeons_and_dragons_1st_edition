#!/usr/bin/env python3
"""Review every 45-degree wall the extractor cannot see, before it merges two rooms.

    python diagcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
        --boxr 0.50 --key b1_key --sheet output/b1/images/31_diagonals.png

Prints one line per square carrying a 45-degree wall, with the Radon peak, the
independent topological verdict beside it, and the edge corrections that would
express the wall as the staircase of grid boundaries it crosses. Writes a
contact sheet of 3x3-cell crops of the printed page -- the candidate boxed, the
detected diagonal drawn on it -- so the calls can be checked by eye in one pass.

It writes NOTHING to any database, and `--db` is opened READ-ONLY.

Why this exists
---------------
`edge_stats` asks "how much rock lies along this grid boundary". A wall drawn at
45 degrees answers "none" -- the rock sits a foot and a half INSIDE the square --
while completely blocking passage. So `extents.py` floods straight through it.

B1's area 34, the ARMORY, came out as 41 squares containing another room's
markers, and it was found ON 2026-08-29 IN LIVE PLAY, with the party standing in
it and the player reading the printed map at the table. Repairing it took five
hand `edge` corrections and thirty-one hand `member` rows. Two more rooms are in
the same state right now -- see DIAGONAL_WALLS.md section 3.7.

Nothing about this is a threshold that wants tuning. The partitions' boundaries
measure a median 2.0 px, dead centre of the printed-ruling band, so no `--t-thick`
reaches them without destroying the wall/ruling separation everywhere else. The
measurement axis is wrong, not the threshold.

Flag, draw, never reclassify
----------------------------
The same rule `doorcheck.py` earned the hard way, and for the same asymmetry: a
MISSED diagonal wall merges two rooms in the extent table, an INVENTED one seals
a room the party needs to walk out of. Both are worse than a human looking at
thirteen pictures. The detector is cleaner than anything in the door work --
precision 0.92 with a real gap between 0.50 and 0.90 -- but it has been validated
on ONE sheet with TWELVE positives, which is not enough to let it write to a
database a live game is read from.

So the verdict is human and goes in the corrections file, which always wins.
Two things the image genuinely cannot tell you, and both are on the human:

  * WHICH SIDE owns the square. The band runs corner to corner through the
    centre, so the offset is ~0 and carries no signal; the answer comes from
    which room the square belongs to, which is a reading of the text or of the
    printed page. Both assignments are printed and you pick one.
  * The extents on either side. `member` rows still have to be entered by hand;
    the staircase corrections stop the flood, they do not draw the room.
"""
import argparse
import os
import sqlite3
import sys

import build
import extract as E

# The staircase (DIAGONAL_WALLS.md section 3.4): converting a 45-degree wall into
# the grid boundaries it crosses, once a human has said which side owns the
# square. A SWNE wall cuts the square into a north-west half and a south-east
# half; assigning it to the north-west means sealing its south and east sides.
# Edges are canonical -- 'V' is the EAST side of (x,y), 'H' the NORTH side -- so
# "south of (x,y)" is (x, y-1, H) and "west of (x,y)" is (x-1, y, V).
SIDES = {
    ('SWNE', 'NW'): (('H', 0, -1), ('V', 0, 0)),      # seal S and E
    ('SWNE', 'SE'): (('H', 0, 0), ('V', -1, 0)),      # seal N and W
    ('NWSE', 'NE'): (('H', 0, -1), ('V', -1, 0)),     # seal S and W
    ('NWSE', 'SW'): (('H', 0, 0), ('V', 0, 0)),       # seal N and E
}


def survey(run, min_peak=E.DIAG_PEAK):
    """[(cell, topology-orientation-or-None)] for every diagonal-wall call.

    The Radon test decides the list and the topology test is reported beside it,
    as DIAGONAL_WALLS.md section 2.6 recommends: two agreeing tests are a
    stronger claim than either, but their conjunction silently drops (5,27), a
    real wall on area 11.
    """
    out = []
    for s in run['cells']:
        if s.get('feature') == 'outside':
            continue
        if E.diagonal_suspect(s, min_peak):
            out.append((s, E.split_orient(s.get('side_classes') or ())))
    out.sort(key=lambda t: (-(t[0]['diag_peak']), t[0]['x'], t[0]['y']))
    return out


def topology_only(run, min_peak=E.DIAG_PEAK):
    """Squares the topology test splits but the Radon peak did not reach."""
    return [s for s in run['cells']
            if s.get('feature') != 'outside'
            and E.split_orient(s.get('side_classes') or ())
            and not E.diagonal_suspect(s, min_peak)]


def rooms_of(db, level, cells):
    """{(x,y): room} read STRICTLY READ-ONLY, or {} if there is no database.

    Which side of the wall a square belongs to is the one bit the image does not
    carry, and the current extent is the evidence for it -- a room with the SAME
    area on both sides of a diagonal has flooded through it.
    """
    if not db or not os.path.exists(db):
        return {}
    con = sqlite3.connect('file:%s?mode=ro' % os.path.abspath(db), uri=True)
    try:
        rows = con.execute('SELECT x, y, room FROM cells WHERE level=?',
                           (level,)).fetchall()
    finally:
        con.close()
    want = set(cells)
    return {(x, y): r for x, y, r in rows if (x, y) in want and r}


def corrections(s, side, who='?'):
    """The staircase correction lines for one square, given the side that owns it."""
    plan = SIDES.get((s['diag_orient'], side))
    if not plan:
        return []
    return ['edge\t%d\t%d\t%s\twall\t%s\t%s'
            % (s['x'] + dx, s['y'] + dy, o, who,
               '%s wall drawn inside (%d,%d), square assigned to the %s side '
               '(diagcheck peak %.2f) -- UNVERIFIED, check the crop'
               % (s['diag_orient'], s['x'], s['y'], side, s['diag_peak']))
            for o, dx, dy in plan]


def sheet(run, rows, path, cells=1.5, cols=5):
    """Contact sheet: 3x3 cells of the printed page around every call."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    grid, grey = run['grid'], run['grey']
    H, W = grey.shape
    n = len(rows)
    if not n:
        return None
    nrow = (n + cols - 1) // cols
    fig, axes = plt.subplots(nrow, cols, figsize=(3.0 * cols, 3.3 * nrow),
                             squeeze=False)
    for ax, (s, topo) in zip(axes.ravel(), rows):
        cx = grid.x0 + (s['i'] + 0.5) * grid.px
        cy = grid.y0 + (s['j'] + 0.5) * grid.py
        rx, ry = cells * grid.px, cells * grid.py
        xa, xb = max(0, int(cx - rx)), min(W, int(cx + rx))
        ya, yb = max(0, int(cy - ry)), min(H, int(cy + ry))
        ax.imshow(grey[ya:yb, xa:xb], cmap='gray', interpolation='nearest')
        # the candidate square, and the diagonal the detector claims across it
        lx, rx2 = cx - 0.5 * grid.px - xa, cx + 0.5 * grid.px - xa
        ty, by = cy - 0.5 * grid.py - ya, cy + 0.5 * grid.py - ya
        ax.plot([lx, rx2, rx2, lx, lx], [ty, ty, by, by, ty],
                color='r', lw=1.0, alpha=0.8)
        if s['diag_orient'] == 'SWNE':
            ax.plot([lx, rx2], [by, ty], color='c', lw=1.0, ls='--', alpha=0.9)
        else:
            ax.plot([lx, rx2], [ty, by], color='c', lw=1.0, ls='--', alpha=0.9)
        agree = (topo == s['diag_orient'])
        ax.set_title('(%d,%d) %s  peak %.2f\ntopology %s'
                     % (s['x'], s['y'], s['diag_orient'], s['diag_peak'],
                        'agrees' if agree else (topo or 'no split')),
                     fontsize=8, color='darkgreen' if agree else 'darkred')
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in axes.ravel()[n:]:
        ax.axis('off')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def build_parser():
    p = argparse.ArgumentParser(
        prog='diagcheck.py',
        description='Flag squares carrying a 45-degree wall -- which no boundary '
                    'measurement can see -- and render a contact sheet of every '
                    'one for review.',
        epilog='A hit is not a verdict, and the proposed corrections are not '
               'applied. Look at the sheet, decide which side of the wall each '
               'square belongs to, then paste the lines you accept into the '
               'corrections file. Nothing here writes to a database.')
    p.add_argument('--pdf', required=True)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--channel', default='mean', choices=list(E.CHANNELS))
    p.add_argument('--key', default=None,
                   help='key module, for label protection ("none" to skip)')
    p.add_argument('--t-solid', type=float, default=0.05)
    p.add_argument('--t-open', type=float, default=0.75)
    p.add_argument('--t-thick', type=float, default=4.5)
    p.add_argument('--t-gap', type=float, default=0.25)
    p.add_argument('--boxr', type=float, default=0.42)
    p.add_argument('--stair-slots', type=int, default=5)
    p.add_argument('--min-peak', type=float, default=E.DIAG_PEAK,
                   help='Radon peak, as a fraction of the cell side, at which a '
                        '45-degree line is claimed. B1: true walls 0.90-1.00, '
                        'furnished control cells 0.50 at p90')
    p.add_argument('--db', default=None,
                   help='map database to read room membership from. Opened '
                        'READ-ONLY; a room with the same number on BOTH sides of '
                        'a wall has flooded through it')
    p.add_argument('--level', type=int, default=1)
    p.add_argument('--who', default='?',
                   help='initials to stamp on the proposed correction lines')
    p.add_argument('--brief', action='store_true',
                   help='print the hits and the counts only, without the block '
                        'of proposed corrections (what rebuild.sh wants)')
    p.add_argument('--sheet', default=None, help='write the contact sheet here')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    key = None
    if a.key and a.key != 'none':
        key = __import__(a.key)
    run = build.extract_map(a.pdf, a.page, a.dpi, a.t_solid, a.t_open,
                            a.stair_slots, rooms=build.label_cells(key),
                            channel=a.channel, t_thick=a.t_thick,
                            t_gap=a.t_gap, boxr=a.boxr)
    rows = survey(run, a.min_peak)
    room = rooms_of(a.db, a.level,
                    [(s['x'] + dx, s['y'] + dy) for s, _ in rows
                     for dx in (-1, 0, 1) for dy in (-1, 0, 1)])

    for s, topo in rows:
        x, y = s['x'], s['y']
        # the two squares on each side of the wall. The SAME area on both sides
        # is a room that has flooded straight through it (section 3.7).
        n, s_, e, w = (x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)
        if s['diag_orient'] == 'SWNE':
            a_side, a_at, b_side, b_at = 'NW', (n, w), 'SE', (s_, e)
        else:
            a_side, a_at, b_side, b_at = 'NE', (n, e), 'SW', (s_, w)
        print('(%2d,%2d) %-4s peak %.2f  off %+.2f  rock %.2f  topology %-9s%s'
              % (x, y, s['diag_orient'], s['diag_peak'], s['diag_offset'],
                 s['rock_frac'],
                 'agrees' if topo == s['diag_orient'] else (topo or 'no split'),
                 '' if not room else
                 '  room %s  (%s %s/%s | %s %s/%s)'
                 % (room.get((x, y)),
                    a_side, room.get(a_at[0]), room.get(a_at[1]),
                    b_side, room.get(b_at[0]), room.get(b_at[1]))))
    print()
    agreed = sum(1 for s, t in rows if t == s['diag_orient'])
    print('%d square(s) carry a 45-degree wall; %d confirmed by the topology '
          'test.' % (len(rows), agreed))
    also = topology_only(run, a.min_peak)
    if also:
        print('%d more split topologically but scored under the peak: %s'
              % (len(also), ' '.join('(%d,%d)' % (s['x'], s['y']) for s in also)))

    if rows and not a.brief:
        print()
        print('--- proposed corrections, NOT applied -------------------------')
        print('# The image cannot say which side of the wall owns the square.')
        print('# Pick one block per square, check it against the crop, and')
        print('# paste it into the corrections file. Membership (`member` rows)')
        print('# still has to be entered by hand -- these lines stop the flood,')
        print('# they do not draw the room.')
        for s, _ in rows:
            print('# (%d,%d) %s -- if the square belongs to the %s side:'
                  % (s['x'], s['y'], s['diag_orient'],
                     'NW' if s['diag_orient'] == 'SWNE' else 'NE'))
            for line in corrections(s, 'NW' if s['diag_orient'] == 'SWNE'
                                    else 'NE', a.who):
                print(line)
            print('# (%d,%d) %s -- if it belongs to the %s side:'
                  % (s['x'], s['y'], s['diag_orient'],
                     'SE' if s['diag_orient'] == 'SWNE' else 'SW'))
            for line in corrections(s, 'SE' if s['diag_orient'] == 'SWNE'
                                    else 'SW', a.who):
                print(line)

    if a.sheet:
        print()
        print('contact sheet: %s' % sheet(run, rows, a.sheet))
        print('LOOK AT IT. A missed diagonal merges two rooms; an invented one '
              'seals one. The detector has been validated on one sheet with '
              'twelve positives.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
