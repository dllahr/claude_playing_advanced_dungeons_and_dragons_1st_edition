#!/usr/bin/env python3
"""Rotation-aware matching of the map's own legend symbols.

The DMG prints a LEVEL KEY defining every symbol used on the sheet: S = secret
door, C = concealed door, a boxed X = trap door, a boxed S = secret trap door,
plus stairs and the stream. That key is the authority on what each mark looks
like, so templates are cropped from it rather than invented -- and B1 carries
its own key to crop from.

Symbols are ROTATED on the map: doors, stairs and the stream follow the wall
they sit on, and at least one S is turned 45 degrees to stand perpendicular to
a diagonal wall. Matching is therefore done over a sweep of angles, and the
winning angle is kept -- it says which wall a marker belongs to.

Glyphs are compared after normalisation (crop to ink, scale to a common canvas,
centre) so the score is a shape comparison and not a size or position one.
"""
import numpy as np
import pymupdf
from PIL import Image
from scipy import ndimage

CANVAS = 32          # normalised glyph is CANVAS x CANVAS
ANGLES = tuple(range(0, 360, 15))
DARK = 150

# Where each symbol sits in the DMG LEVEL KEY, in PDF points. The '=' signs and
# labels are in the page's text layer, so these were read off it rather than
# guessed; see the docstring of legend_boxes().
DMG_LEGEND_PAGE = 94
DMG_LEGEND = {
    'secret':    (356, 372, 370, 390),     # plain S
    'concealed': (494, 372, 508, 390),     # plain C
}


def legend_boxes(pdf, page=DMG_LEGEND_PAGE):
    """Locate the legend rows from the page's text layer.

    Returns {label: (x0,y0,x1,y1)} in PDF points for the '=' sign of each row,
    which anchors the symbol drawn to its right. Used to derive DMG_LEGEND and
    to port the same trick to another module's key page.
    """
    doc = pymupdf.open(pdf)
    words = doc[page].get_text('words')
    return [(w[4], w[:4]) for w in words if 270 < w[1] < 400 and 280 < w[0] < 540]


def crop_template(pdf, box, page=DMG_LEGEND_PAGE, dpi=200, pad=3):
    """Crop one legend symbol and trim it to its ink."""
    doc = pymupdf.open(pdf)
    pix = doc[page].get_pixmap(dpi=dpi)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)[:, :, :3].mean(axis=2)
    s = dpi / 72.0
    x0, y0, x1, y1 = box
    sub = a[int(y0 * s):int(y1 * s), int(x0 * s):int(x1 * s)]
    dark = sub < DARK
    if not dark.any():
        return sub
    ys, xs = np.where(dark)
    return sub[max(0, ys.min() - pad):ys.max() + 1 + pad,
               max(0, xs.min() - pad):xs.max() + 1 + pad]


def load_templates(pdf, spec=None, page=DMG_LEGEND_PAGE, dpi=200):
    """{name: normalised glyph} for every symbol in the legend spec."""
    spec = spec or DMG_LEGEND
    return {name: normalise(crop_template(pdf, box, page, dpi) < DARK)
            for name, box in spec.items()}


def normalise(mask, canvas=CANVAS):
    """Crop a boolean glyph to its ink, scale to a common canvas, centre it.

    Removes size and position from the comparison so what remains is shape.
    """
    if not mask.any():
        return np.zeros((canvas, canvas))
    ys, xs = np.where(mask)
    sub = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = sub.shape
    scale = (canvas - 6) / max(h, w)
    img = Image.fromarray((sub * 255).astype(np.uint8)).resize(
        (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
        Image.LANCZOS)
    out = Image.new('L', (canvas, canvas), 0)
    out.paste(img, ((canvas - img.width) // 2, (canvas - img.height) // 2))
    return np.asarray(out, dtype=float) / 255.0


def ncc(a, b):
    """Normalised cross-correlation of two equal-shaped arrays, in [-1, 1]."""
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def match(glyph, templates, angles=ANGLES):
    """Best (name, score, angle) for a normalised glyph.

    The glyph is rotated rather than the template, so every template is
    compared against the same set of orientations and the returned angle is the
    rotation that had to be undone to make the glyph upright.
    """
    best = (None, -1.0, 0)
    rotations = {}
    for ang in angles:
        rotations[ang] = normalise(
            ndimage.rotate(glyph, ang, reshape=True, order=1) > 0.4)
    for name, tmpl in templates.items():
        for ang, rot in rotations.items():
            s = ncc(rot, tmpl)
            if s > best[1]:
                best = (name, s, ang)
    return best


def blobs(ink, field, grid, min_area=40):
    """Every printed mark in the map field, with its cell and normalised shape."""
    r0, r1, c0, c1 = field
    m = np.zeros_like(ink)
    m[r0:r1, c0:c1] = ink[r0:r1, c0:c1]
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        blob = (lab[sl] == k)
        if blob.sum() < min_area:
            continue
        cy = (sl[0].start + sl[0].stop) / 2.0
        cx = (sl[1].start + sl[1].stop) / 2.0
        j = int((cy - grid.y0) // grid.py)
        out.append(dict(glyph=normalise(blob),
                        x=int((cx - grid.x0) // grid.px), y=grid.gy(j),
                        px=cx, py=cy, x0=sl[1].start, x1=sl[1].stop,
                        h=sl[0].stop - sl[0].start, w=sl[1].stop - sl[1].start,
                        area=int(blob.sum())))
    return out


def digit_templates(marks, rooms):
    """Learn digit shapes from the map's own verified room numbers.

    Matching S and C against nothing but each other makes every digit score as
    one or the other -- a rotated "2" resembles an S more than it resembles a
    C, so it wins by default. The fix is a negative class, and the verified
    ROOMS table supplies labelled examples for free: the marks sitting in the
    anchor cell of area 23 are, left to right, a "2" and a "3".

    Returns {character: averaged normalised glyph}.
    """
    acc = {}
    by_cell = {}
    for m in marks:
        by_cell.setdefault((m['x'], m['y']), []).append(m)
    for number, (x, y) in rooms.items():
        if not number.isdigit():
            continue
        here = sorted(by_cell.get((x, y), []), key=lambda m: m['x0'])
        if len(here) != len(number):
            continue                     # merged into rock, or split oddly
        for ch, m in zip(number, here):
            acc.setdefault(ch, []).append(m['glyph'])
    return {ch: np.mean(v, axis=0) for ch, v in acc.items()}


def classify_marks(marks, symbol_templates, digit_templates_, min_score=0.55,
                   margin=0.05, angles=ANGLES):
    """Label each printed mark as a legend symbol, a digit, or unknown.

    Digits are compared upright only -- printed numbers are never rotated on
    these sheets -- while legend symbols are swept through every angle, because
    a door follows its wall and one S on this map stands at 45 degrees against
    a diagonal wall. That asymmetry is what keeps an upright "5" from being
    claimed by a rotated S: the digit matches its own template near 1.0.
    """
    out = []
    for m in marks:
        scores = []
        for ch, t in digit_templates_.items():
            scores.append((ncc(m['glyph'], t), 'digit', ch))
        for name, t in symbol_templates.items():
            best, best_a = -1.0, 0
            for a in angles:
                r = normalise(ndimage.rotate(m['glyph'], a, reshape=True,
                                             order=1) > 0.4)
                s = ncc(r, t)
                if s > best:
                    best, best_a = s, a
            scores.append((best, 'symbol', '%s@%d' % (name, best_a)))
        scores.sort(reverse=True)
        top = scores[0]
        second = scores[1][0] if len(scores) > 1 else -1.0
        rec = dict(m)
        rec.pop('glyph')
        rec.update(score=float(top[0]), runner_up=float(second),
                   kind=top[1], label=top[2],
                   confident=bool(top[0] >= min_score and top[0] - second >= margin))
        out.append(rec)
    return out


def classify_glyphs(ink, field, templates, grid, min_area=40, min_score=0.55,
                    margin=0.04):
    """Find legend symbols among the printed annotation.

    Only the ink layer is searched: S and C are printed marks sitting in open
    floor, not structural rock. Each blob is normalised and matched against
    every template at every angle.

    `margin` is how far the winner must beat the runner-up. A digit resembles
    an S more than it resembles nothing, so an unconfident win is discarded
    rather than guessed.
    """
    r0, r1, c0, c1 = field
    m = np.zeros_like(ink)
    m[r0:r1, c0:c1] = ink[r0:r1, c0:c1]
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        blob = (lab[sl] == k)
        if blob.sum() < min_area:
            continue
        g = normalise(blob)
        scores = sorted(
            ((max(ncc(normalise(ndimage.rotate(g, a, reshape=True, order=1) > 0.4), t)
                  for a in ANGLES), name) for name, t in templates.items()),
            reverse=True)
        top, name = scores[0]
        second = scores[1][0] if len(scores) > 1 else -1.0
        cy = (sl[0].start + sl[0].stop) / 2.0
        cx = (sl[1].start + sl[1].stop) / 2.0
        i = int((cx - grid.x0) // grid.px)
        j = int((cy - grid.y0) // grid.py)
        out.append(dict(name=name if (top >= min_score and top - second >= margin)
                        else None,
                        score=float(top), runner_up=float(second),
                        x=i, y=grid.gy(j), px=float(cx), py=float(cy),
                        h=sl[0].stop - sl[0].start, w=sl[1].stop - sl[1].start,
                        area=int(blob.sum())))
    return out


def marker_edge(marker, terrain, grid):
    """Which boundary a marker annotates.

    A printed S or C sits *inside* a square but denotes a door in one of that
    square's walls. The wall is the side facing rock: a door leads somewhere,
    and the only direction with anywhere to lead is through the rock. Where
    more than one side qualifies the marker is returned unresolved, for a human
    to settle.

    Returns (x, y, orient, side) in canonical edge form, or None.
    """
    x, y = marker['x'], marker['y']
    sides = []
    for side, (dx, dy) in (('N', (0, 1)), ('S', (0, -1)),
                           ('E', (1, 0)), ('W', (-1, 0))):
        if terrain.get((x + dx, y + dy)) == 'solid':
            sides.append(side)
    if len(sides) != 1:
        return None
    side = sides[0]
    if side == 'N':
        return (x, y, 'H', side)
    if side == 'S':
        return (x, y - 1, 'H', side)
    if side == 'E':
        return (x, y, 'V', side)
    return (x - 1, y, 'V', side)
