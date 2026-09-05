#!/usr/bin/env python3
"""Review every door the extractor claims, before the party walks through one.

    python doorcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
        --boxr 0.50 --key b1_key --sheet output/b1/images/30_doors.png

Prints one line per `door` edge with the one-sided test's verdict, and writes a
contact sheet of crops -- the printed page around each glyph, with the boundary
drawn on it -- so the calls can be checked by eye in a single pass.

Why this exists
---------------
Six furnished rooms of B1 were extracted with fabricated doors, and every one
was found the same way: DURING PLAY, by the player noticing that the map on the
table did not match what the DM had narrated. Areas 9, 23, 24, 25, 27 and 28.
Area 25's lobes came out as five doors; area 27's dais as four; area 24 was cut
in half by a drawn bed.

No classifier tweak found them, because the numbers do not separate: area 24's
two fabrications measured thickness 9 and 10 with hole 134, against the genuine
door beside them at 7 and 187 -- the fakes were closer to the middle of the
door band than the real door was.

What DID separate them is structural, and the player supplied it:

    "the furniture lines only exist on one side of the wall,
     unlike the doors that go through the wall"

`extract.door_suspect` measures that (see its docstring). On B1 level 1 it
rejects 9 of the 16 confirmed fabrications and keeps all 7 doors the party has
physically walked through. The remaining 7 are obvious in the crops -- which is
the point of the sheet. This is a REVIEW step, not an automatic reclassifier:
a fabricated door invents a passage and gets someone killed, so the verdict
belongs to a human and goes in the corrections file.

Run it whenever a new level is extracted, and read the sheet.
"""
import argparse
import os
import sys

import build
import extract as E


def survey(run, min_wall=5.0, max_offset=0.14):
    """[(edge, reason-or-None)] for every edge classified `door`, worst first."""
    out = []
    for e in run['edges']:
        if e.get('kind') != 'door':
            continue
        out.append((e, E.door_suspect(e, min_wall, max_offset)))
    # suspects first, then by how far off the wall the glyph sits
    out.sort(key=lambda t: (t[1] is None, -(t[0].get('offset') or 0.0)))
    return out


def sheet(run, rows, path, cells=1.0, cols=6):
    """Contact sheet: the printed page around every door call, boundary marked."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    grid, grey = run['grid'], run['grey']
    H, W = grey.shape
    n = len(rows)
    if not n:
        return None
    nrow = (n + cols - 1) // cols
    fig, axes = plt.subplots(nrow, cols, figsize=(2.7 * cols, 2.9 * nrow),
                             squeeze=False)
    for ax, (e, why) in zip(axes.ravel(), rows):
        x, y, o = e['x'], e['y'], e['orient']
        j = grid.ny - 1 - y
        if o == 'V':
            cx, cy = grid.x0 + (x + 1) * grid.px, grid.y0 + (j + 0.5) * grid.py
        else:
            cx, cy = grid.x0 + (x + 0.5) * grid.px, grid.y0 + j * grid.py
        r = int(cells * grid.px)
        xa, xb = max(0, int(cx - r)), min(W, int(cx + r))
        ya, yb = max(0, int(cy - r)), min(H, int(cy + r))
        ax.imshow(grey[ya:yb, xa:xb], cmap='gray', interpolation='nearest')
        if o == 'V':
            ax.axvline(cx - xa, color='r', lw=1.0, alpha=0.8)
        else:
            ax.axhline(cy - ya, color='r', lw=1.0, alpha=0.8)
        off = e.get('offset')
        ax.set_title('(%d,%d,%s) %s\nwall %.0f  off %s'
                     % (x, y, o, 'SUSPECT' if why else 'ok',
                        e.get('wall') or 0.0,
                        '--' if off is None else '%.2f' % off),
                     fontsize=8, color='darkred' if why else 'darkgreen')
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
        prog='doorcheck.py',
        description='Flag door calls that may be drawn furniture, and render '
                    'a contact sheet of every one for review.',
        epilog='A SUSPECT is not a verdict. Look at the sheet, then record '
               'what you decide in the corrections file.')
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
    p.add_argument('--min-wall', type=float, default=5.0,
                   help='px of rock beside the glyph below which there is no '
                        'wall for a door to be a hole in')
    p.add_argument('--max-offset', type=float, default=0.14,
                   help='cells the glyph may sit off the wall bar')
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
    rows = survey(run, a.min_wall, a.max_offset)
    bad = [r for r in rows if r[1]]
    for e, why in rows:
        print('%-14s %-8s %s'
              % ('(%d,%d,%s)' % (e['x'], e['y'], e['orient']),
                 'SUSPECT' if why else 'ok', why or ''))
    print()
    print('%d door call(s), %d suspect.' % (len(rows), len(bad)))
    if a.sheet:
        print('contact sheet: %s' % sheet(run, rows, a.sheet))
        print('LOOK AT IT. The test is a sieve, not a classifier -- it misses '
              'about a third of the fabrications, and they are obvious on the '
              'page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
