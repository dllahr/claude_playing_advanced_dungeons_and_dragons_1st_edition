#!/usr/bin/env python3
"""Measure area-label detection against a hand-made ground-truth table.

    conda activate advanced_dnd_1e
    python eval_labels.py --db output/b1/b1.sqlite \\
        --truth ../dlwork/archive/2026-08-24_b1_lv1_number_locations.txt

Detection is split into two questions, because they fail for different reasons
and want different fixes:

  LOCALISE  did anything get found in the square where a label is printed?
            Failures here mean the mark never reached the annotation layer --
            on B1 it merged into a wall or a piece of furniture.
  READ      of those found, was the number read correctly?
            Failures here are OCR accuracy on small blue-printed digits.

Reporting a single combined score hides which of the two is worth working on.
On B1 the split was 20 localised of 37, and 12 read of those 20 -- so the work
belonged in localisation, not in the OCR.
"""
import argparse
import sys

import numpy as np
from scipy import ndimage

import extract as E
import label_file as LF
import markers as M
import ocr_labels as O


def thin_components(rock, grid, radius=4, min_area=60, min_dim=7,
                    max_aspect=3.5):
    """Digit-shaped clumps of thin rock.

    A label that touches a wall is swallowed by the connectivity pass in
    rock_mask and never reaches the ink layer. But print is thin where
    structure is a mass, so opening the rock and taking the difference
    recovers the glyph even where it merged.
    """
    mask = M.thin_rock(rock, radius)
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        area = int((lab[sl] == k).sum())
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if area < min_area or min(h, w) < min_dim:
            continue
        if max(h, w) > 1.1 * grid.px or max(h, w) / max(1, min(h, w)) > max_aspect:
            continue
        out.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop, area])
    return out


def digit_height(boxes, lo=8, hi=40):
    """The printed digit height, learned from the marks themselves.

    Type on one sheet is one size, so the heights of real digits cluster hard
    while noise scatters: on B1 the digits are 18-19 px at 200 dpi (p10 to p90)
    against noise spanning 8-30, and on the DMG they are 29. Taking the mode
    rather than fixing a constant keeps this working across sheets printed at
    different scales.
    """
    hs = [b[3] - b[1] for b in boxes if lo <= b[3] - b[1] <= hi]
    if not hs:
        return None
    counts = np.bincount(np.asarray(hs))
    return int(counts.argmax())


def detect(grey, ink, rock, field, grid, use_thin=False, max_gap=O.MAX_GAP,
           height_tol=None):
    """[(text, x, y)] for every label found.

    `height_tol` filters blobs to those within that fraction of the learned
    digit height. Thin-stroke recovery finds the labels that merged into walls,
    but it also admits five times as much noise, and noise adjacent to a real
    digit corrupts the merge that turns "1" and "3" into "13". Filtering by
    height first is what makes the recovery usable.
    """
    boxes = O.components(ink, field)
    # Learn the digit height from the INK layer alone. Thin-stroke recovery
    # brings in five times as much noise as signal, and that noise outvotes the
    # digits in a mode taken over everything -- which filtered the real labels
    # away and dropped B1 from 89% localised to 11%.
    h0 = digit_height(boxes) if height_tol else None
    if use_thin:
        r0, r1, c0, c1 = field
        for b in thin_components(rock, grid):
            if r0 <= b[1] and b[3] <= r1 and c0 <= b[0] and b[2] <= c1:
                boxes.append(b)
    if h0:
        boxes = [b for b in boxes
                 if abs((b[3] - b[1]) - h0) <= height_tol * h0]
    out = []
    for b in O.merge(boxes, max_gap=max_gap):
        x, y = O.to_cell(b, grid)
        out.append((O.read(grey, b), x, y))
    return out


def score(found, truth):
    """(localised, read, total) areas."""
    cells = {}
    for name, cs in truth.items():
        for c in cs:
            cells.setdefault(c, set()).add(name)
    localised, read = set(), set()
    for text, x, y in found:
        for name in cells.get((x, y), ()):
            localised.add(name)
            if text == name:
                read.add(name)
    return localised, read, set(truth)


def build_parser():
    p = argparse.ArgumentParser(
        prog='eval_labels.py',
        description='Measure label detection against a ground-truth table.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--db', required=True, help='map database (for render settings)')
    p.add_argument('--level', type=int, default=1)
    p.add_argument('--truth', required=True, help='hand-made label table')
    p.add_argument('--thin', action='store_true',
                   help='also recover labels that merged into the rock')
    p.add_argument('--max-gap', type=int, default=O.MAX_GAP,
                   help='px between digits of one number')
    p.add_argument('--height-tol', type=float, default=None,
                   help='keep only blobs within this fraction of the learned '
                        'digit height (try 0.2)')
    p.add_argument('--numeric-only', action='store_true',
                   help='score only the numbered areas, ignoring sub-locations')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    cfg = M.render_settings(a.db, a.level)
    if not cfg:
        print('no render settings in %s' % a.db)
        return 1
    grey, rgb = E.render(cfg['pdf'], cfg['page'], cfg['dpi'], channel=cfg['channel'])
    if abs(cfg['deskew']) > 1e-6:
        grey, rgb = E.deskew(grey, rgb, cfg['deskew'])
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)
    rock, ink = E.rock_mask(grey)

    truth = LF.load(a.truth)
    if a.numeric_only:
        truth = {k: v for k, v in truth.items() if k.isdigit()}
    found = detect(grey, ink, rock, field, grid, a.thin, a.max_gap,
                   height_tol=a.height_tol)
    loc, read, total = score(found, truth)

    print('blobs merged into labels : %d' % len(found))
    print('areas in ground truth    : %d' % len(total))
    print('LOCALISED (something found in the right square) : %d  (%.0f%%)'
          % (len(loc), 100 * len(loc) / max(1, len(total))))
    print('READ      (and the number was correct)          : %d  (%.0f%%)'
          % (len(read), 100 * len(read) / max(1, len(total))))
    miss_loc = sorted(total - loc, key=lambda s: (len(s), s))
    miss_read = sorted(loc - read, key=lambda s: (len(s), s))
    print('\nnot localised (%d): %s' % (len(miss_loc), miss_loc))
    print('localised but misread (%d): %s' % (len(miss_read), miss_read))
    return 0


if __name__ == '__main__':
    sys.exit(main())
