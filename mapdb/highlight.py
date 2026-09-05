#!/usr/bin/env python3
"""Draw the map with the unreachable squares picked out, for a quick human look.

    conda activate advanced_dnd_1e
    python highlight.py --db output/b1/b1.sqlite --pdf <b1.pdf> --page 1 \\
        --channel r --from-cell 16 1 --out output/b1/images/21_unreachable.png

Every non-solid square on a dungeon level should be reachable from the
entrance. The ones that are not are either genuinely isolated or evidence of a
wall the extractor invented, and telling those apart is a five-second judgement
by eye and a hard problem for code -- so this renders them rather than
describing them.

The map is washed out and the flagged squares are painted over it, so the
answer is visible at a glance without reading any of the underlying detail.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import extract as E
import markers as M


def render_highlight(db, level, pdf, page, dpi, channel, deskew, start_cell,
                     from_room, out, wash=0.62, every=5):
    cfg = M.render_settings(db, level) or {}
    pdf = pdf or cfg.get('pdf')
    page = page if page is not None else cfg.get('page')
    dpi = dpi or cfg.get('dpi', 200)
    grey, rgb = E.render(pdf, page, dpi, channel=cfg.get('channel', channel))
    skew = cfg.get('deskew', 0.0)
    if abs(skew) > 1e-6:
        grey, rgb = E.deskew(grey, rgb, skew)
    elif deskew:
        grey, rgb, _ = E.auto_deskew(grey, rgb)
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)

    regions = M.isolated_regions(db, level, from_room, start_cell)
    regions.sort(key=len, reverse=True)

    # wash the map out so the overlay reads at a glance
    base = Image.fromarray(rgb).convert('RGB')
    base = Image.blend(base, Image.new('RGB', base.size, 'white'), wash)
    d = ImageDraw.Draw(base, 'RGBA')

    for n, region in enumerate(regions, start=1):
        for (x, y) in region:
            j = grid.ny - 1 - y
            xa = grid.x0 + x * grid.px
            ya = grid.y0 + j * grid.py
            d.rectangle([xa, ya, xa + grid.px, ya + grid.py],
                        fill=(220, 30, 30, 130), outline=(150, 0, 0, 255))
        xs = [c[0] for c in region]; ys = [c[1] for c in region]
        lx = grid.x0 + (min(xs) + (max(xs) - min(xs)) / 2.0) * grid.px
        ly = grid.y0 + (grid.ny - 1 - max(ys)) * grid.py - 15
        d.text((lx - 6, max(0, ly)), str(n), fill=(140, 0, 0, 255))

    for i, x in enumerate(grid.xlines()):
        if i % every:
            continue
        d.line([(x, grid.y0), (x, grid.y0 + grid.ny * grid.py)],
               fill=(0, 90, 200, 110), width=1)
        d.text((x + 2, max(0, grid.y0 - 14)), str(i), fill=(0, 70, 170, 255))
    for j, y in enumerate(grid.ylines()):
        if j % every:
            continue
        d.line([(grid.x0, y), (grid.x0 + grid.nx * grid.px, y)],
               fill=(0, 90, 200, 110), width=1)
        lbl = grid.gy(j) if j < grid.ny else ''
        d.text((max(0, grid.x0 - 26), y - 6), str(lbl), fill=(0, 70, 170, 255))

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    base.save(out)

    lines = []
    for n, region in enumerate(regions, start=1):
        xs = [c[0] for c in region]; ys = [c[1] for c in region]
        lines.append('%-4d %3d square(s)   x %2d-%-2d  y %2d-%-2d   %s'
                     % (n, len(region), min(xs), max(xs), min(ys), max(ys),
                        sorted(region)[:10]))
    return regions, lines


def build_parser():
    p = argparse.ArgumentParser(
        prog='highlight.py',
        description='Render a map with unreachable squares highlighted.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--db', default='output/b1/b1.sqlite')
    p.add_argument('--level', type=int, default=1)
    p.add_argument('--pdf', default=None, help='override the recorded pdf')
    p.add_argument('--page', type=int, default=None, help='override the recorded page')
    p.add_argument('--dpi', type=int, default=None)
    p.add_argument('--channel', default='mean', choices=list(E.CHANNELS))
    p.add_argument('--no-deskew', action='store_true')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--from-room', default='1')
    g.add_argument('--from-cell', type=int, nargs=2, metavar=('X', 'Y'))
    p.add_argument('--wash', type=float, default=0.62,
                   help='how far to fade the map towards white, 0-1')
    p.add_argument('--out', default='output/b1/images/21_unreachable.png')
    p.add_argument('--index', default=None, help='optional text index to write')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    regions, lines = render_highlight(
        a.db, a.level, a.pdf, a.page, a.dpi, a.channel, not a.no_deskew,
        tuple(a.from_cell) if a.from_cell else None, a.from_room, a.out, a.wash)
    print('%d unreachable square(s) in %d region(s)'
          % (sum(len(r) for r in regions), len(regions)))
    print('\n'.join(lines))
    if a.index:
        with open(a.index, 'w') as fh:
            fh.write('\n'.join(lines) + '\n')
    print('\nwrote %s' % a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
