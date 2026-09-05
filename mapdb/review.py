#!/usr/bin/env python3
"""Build a contact sheet of everything the extractor is unsure about.

Reviewing "cell (6,39) is mixed" costs the reviewer a hunt across the map sheet
to find (6,39). That hunt, not the judgement, is the expensive part. So group
the uncertain cells into contiguous clusters, crop each one, and number the
tiles: the reviewer answers "tile 4 is solid" and never touches a coordinate.

    conda activate advanced_dnd_1e
    python review.py --db dmg.sqlite --level 1
"""
import argparse
import os
import sqlite3
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import extract as E


def clusters(cells, nx, ny):
    """Group flagged cells into 8-connected blobs, biggest first."""
    m = np.zeros((ny, nx), bool)
    for x, y in cells:
        if 0 <= x < nx and 0 <= y < ny:
            m[y, x] = True
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    out = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        out.append(sorted(zip(xs.tolist(), ys.tolist())))
    return sorted(out, key=len, reverse=True)


def sheet(db, level, pdf, page, dpi, max_conf, tile, cols, out_png, out_index,
          pad=1.2):
    con = sqlite3.connect(db)
    flagged = [(x, y) for x, y in con.execute(
        'SELECT x,y FROM cells WHERE level=? AND confidence<=?', (level, max_conf))]
    grey, rgb = E.render(pdf, page, dpi)
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)
    groups = clusters(flagged, grid.nx, grid.ny)

    im = Image.fromarray(rgb).convert('RGB')
    tiles, index = [], []
    for n, g in enumerate(groups, start=1):
        xs = [c[0] for c in g]; ys = [c[1] for c in g]
        xa = grid.x0 + (min(xs) - pad) * grid.px
        xb = grid.x0 + (max(xs) + 1 + pad) * grid.px
        ya = grid.y0 + (grid.ny - 1 - max(ys) - pad) * grid.py
        yb = grid.y0 + (grid.ny - min(ys) + pad) * grid.py
        crop = im.crop((max(0, int(xa)), max(0, int(ya)), int(xb), int(yb)))
        s = min(tile / crop.width, tile / crop.height)
        crop = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))),
                           Image.LANCZOS)
        t = Image.new('RGB', (tile, tile), 'white')
        ox, oy = (tile - crop.width) // 2, (tile - crop.height) // 2
        t.paste(crop, (ox, oy))
        d = ImageDraw.Draw(t)
        for (cx, cy) in g:
            px = (grid.x0 + cx * grid.px - xa) * s + ox
            py = (grid.y0 + (grid.ny - 1 - cy) * grid.py - ya) * s + oy
            d.rectangle([px, py, px + grid.px * s, py + grid.py * s],
                        outline=(255, 0, 0), width=2)
        d.rectangle([0, 0, tile - 1, tile - 1], outline=(0, 0, 0), width=1)
        d.rectangle([2, 2, 34, 20], fill=(255, 255, 255))
        d.text((6, 6), '#%d' % n, fill=(200, 0, 0))
        tiles.append(t)
        near = con.execute(
            'SELECT number FROM rooms WHERE level=? AND anchor_x IS NOT NULL ORDER BY'
            ' (anchor_x-?)*(anchor_x-?)+(anchor_y-?)*(anchor_y-?) LIMIT 1',
            (level, xs[0], xs[0], ys[0], ys[0])).fetchone()
        index.append('#%-3d %2d cell(s)  x %2d-%-2d y %2d-%-2d   nearest label: %s'
                     % (n, len(g), min(xs), max(xs), min(ys), max(ys),
                        near[0] if near else '?'))
    con.close()

    rows = max(1, (len(tiles) + cols - 1) // cols)
    canvas = Image.new('RGB', (cols * (tile + 6), rows * (tile + 6)), 'white')
    for k, t in enumerate(tiles):
        canvas.paste(t, ((k % cols) * (tile + 6), (k // cols) * (tile + 6)))
    os.makedirs(os.path.dirname(out_png) or '.', exist_ok=True)
    canvas.save(out_png)
    with open(out_index, 'w') as fh:
        fh.write('\n'.join(index) + ('\n' if index else ''))
    return len(flagged), index


def build_parser():
    p = argparse.ArgumentParser(
        prog='review.py',
        description='Contact sheet of the squares the extractor is least sure about.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--db', default='output/dmg/dmg.sqlite', help='SQLite map database')
    p.add_argument('--level', type=int, default=1, help='dungeon level number')
    p.add_argument('--pdf', default="../manuals/tsr02011 - Advanced Dungeons & "
                                    "Dragons (Ad&D) 1St Ed - Dungeon Master'S Guide.pdf",
                   help='PDF the map was extracted from')
    p.add_argument('--page', type=int, default=95, help='0-based page index')
    p.add_argument('--dpi', type=int, default=200, help='render resolution')
    p.add_argument('--max-conf', type=int, default=3,
                   help='include cells at or below this confidence (1-10)')
    p.add_argument('--tile', type=int, default=260, help='tile size in pixels')
    p.add_argument('--cols', type=int, default=4, help='tiles per row')
    p.add_argument('--out', default='output/dmg/images/10_review_sheet.png',
                   help='contact sheet to write')
    p.add_argument('--index', default='output/dmg/review_index.txt',
                   help='text index of tiles to write')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    n, index = sheet(args.db, args.level, args.pdf, args.page, args.dpi,
                     args.max_conf, args.tile, args.cols, args.out, args.index)
    print('%d flagged cells in %d clusters' % (n, len(index)))
    print('\n'.join(index))
    print('\nwrote %s and %s' % (args.out, args.index))
    return 0


if __name__ == '__main__':
    sys.exit(main())
