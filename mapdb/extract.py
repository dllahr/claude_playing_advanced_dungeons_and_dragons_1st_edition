#!/usr/bin/env python3
"""Extract a dungeon grid from a scanned graph-paper map.

Run inside the project conda env:
    conda activate advanced_dnd_1e

Pipeline
--------
1. render the PDF page to a greyscale array (PyMuPDF)
2. locate the map FIELD -- the inked rectangle, so blank page margin is never
   mistaken for open floor
3. deskew check: fit the grid phase in horizontal bands; a monotonic drift
   means the sheet is rotated on the page
4. fit grid pitch + phase by scoring gradient energy at candidate grid lines
5. per cell, measure white fraction and shape statistics
6. classify: open / solid / mixed / glyph

The classifier's hard part is telling a *boundary running through a cell*
(a wall, or solid rock cut diagonally) from a *mark sitting inside a cell*
(a room number, a door glyph, map lettering). Two signals separate them:

  bimodality  -- Otsu's between-class variance ratio. A hard ink boundary
                 splits the cell's pixels into two tight, well-separated
                 populations (eta near 1). Halftone stipple and antialiased
                 text give a smeared histogram (low eta).
  edge contact -- threshold the cell, then ask how many of the four cell
                 borders the dark region touches. A wall enters one side and
                 leaves another (2+ sides). A glyph floats in the middle (0).
"""
import numpy as np
import pymupdf
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.filters import threshold_otsu

INSET = 0.12      # ignore this fraction at each cell edge; grid rulings live there
DARK = 140        # greyscale level below which a pixel counts as ink


# ---------------------------------------------------------------- rendering

CHANNELS = ('mean', 'r', 'g', 'b', 'min')


def render(pdf, page, dpi=200, channel='mean'):
    """Return (grey float array, rgb uint8 array) for one PDF page.

    `channel` selects how colour is collapsed to grey. The DMG map is printed
    in black and 'mean' is right. B1 is printed in BLUE, and blue ink absorbs
    red while paper reflects it, so the RED channel separates ink from paper
    far better than the mean does -- roughly twice the contrast.
    """
    doc = pymupdf.open(pdf)
    pix = doc[page].get_pixmap(dpi=dpi)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    rgb = a[:, :, :3].copy()
    if channel == 'mean':
        grey = rgb.mean(axis=2)
    elif channel == 'min':
        grey = rgb.min(axis=2)
    else:
        grey = rgb[:, :, 'rgb'.index(channel)]
    return grey.astype(float), rgb


def label_boxes(cells, grid, inset=0.15):
    """Pixel rectangles covering the interior of each labelled square.

    Takes an iterable of (x, y). Pass EVERY square a label occupies, not one
    per area: a straddling label sits in two squares and a repeated area in
    several, and an unshielded half bridges into the wall just as readily.

    A room number printed over the rock bridges into the rock mass and is then
    counted as structure, which fabricates walls around the square: areas 29,
    32 and 35 on the DMG sheet all came out ringed by walls that are not on the
    page. But a square carrying a room label is floor by definition, so its
    INTERIOR ink is annotation whatever it touches. Excluding just the interior
    -- not the boundary, where the rulings live -- breaks the bridge and leaves
    the real geometry untouched.
    """
    out = []
    for (x, y) in cells:
        j = grid.ny - 1 - y
        if not (0 <= x < grid.nx and 0 <= j < grid.ny):
            continue
        xa, xb, ya, yb = grid.box(x, j, inset=inset)
        out.append((int(xa), int(ya), int(xb), int(yb)))
    return out


def rock_mask(grey, min_area=900, protect=()):
    """Separate structural rock from printed annotation.

    On these maps solid rock is drawn as a filled black mass and everything
    open is left white; room numbers, letters and door glyphs are printed as
    small isolated marks *inside* the white. Both are simply "dark pixels", so
    a raw darkness threshold cannot tell a diagonal rock wedge from the numeral
    "10" sitting in an open room.

    Connectivity does tell them apart. The rock is a huge connected mass (plus
    a few sizeable islands enclosed by corridor loops); a numeral is a blob of
    a few hundred pixels. Keeping only dark components of at least `min_area`
    pixels yields the rock; the discarded remainder is the annotation layer.

    `protect` is a list of pixel boxes whose ink can never be rock -- see
    label_boxes(). Excluding them BEFORE the connectivity pass is what stops a
    numeral printed over the rock from dragging its square into the rock mass.

    Returns (rock, ink) boolean masks.
    """
    dark = grey < DARK
    dark = ndimage.binary_closing(dark, np.ones((3, 3)))   # heal scanner speckle
    candidate = dark
    if len(protect):
        shield = np.zeros_like(dark)
        for x0, y0, x1, y1 in protect:
            shield[max(0, y0):y1, max(0, x0):x1] = True
        candidate = dark & ~shield
    lab, n = ndimage.label(candidate, structure=np.ones((3, 3)))
    if not n:
        return np.zeros_like(dark), dark
    sizes = ndimage.sum(candidate, lab, range(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    keep[1:] = sizes >= min_area
    rock = keep[lab]
    return rock, dark & ~rock


def find_field(grey, frac=0.30, margin=50):
    """Bounding box of the inked map field: (r0, r1, c0, c1).

    Rows/columns whose ink count exceeds `frac` of the image extent are
    considered inside the field. `margin` skips scanner artefacts at the very
    edge of the page.
    """
    ink = (grey < DARK)
    h, w = ink.shape
    rows = ink.sum(axis=1)
    cols = ink.sum(axis=0)
    r = [i for i in range(margin, h - margin) if rows[i] > frac * w]
    c = [i for i in range(margin, w - margin) if cols[i] > frac * h]
    return r[0], r[-1] + 1, c[0], c[-1] + 1


# ---------------------------------------------------------------- grid fit

def _gradients(grey, field):
    r0, r1, c0, c1 = field
    sub = grey[r0:r1, c0:c1]
    gx = np.abs(np.diff(sub, axis=1)).sum(axis=0)
    gy = np.abs(np.diff(sub, axis=0)).sum(axis=1)
    return gx, gy


def fit_axis(sig, lo=35.0, hi=46.0, step=0.05):
    """Search pitch and phase maximising mean gradient energy on grid lines."""
    best = (None, None, -1.0)
    for p in np.arange(lo, hi, step):
        for ph in np.arange(0.0, p, 0.1):
            idx = np.round(np.arange(ph, len(sig), p)).astype(int)
            idx = idx[idx < len(sig)]
            if len(idx) < 5:
                continue
            s = float(sig[idx].mean())
            if s > best[2]:
                best = (float(p), float(ph), s)
    return best


def fit_phase(sig, pitch):
    """Pitch known; find the phase only."""
    best = (None, -1.0)
    for ph in np.arange(0.0, pitch, 0.05):
        idx = np.round(np.arange(ph, len(sig), pitch)).astype(int)
        idx = idx[idx < len(sig)]
        s = float(sig[idx].mean())
        if s > best[1]:
            best = (float(ph), s)
    return best


class Grid:
    """A fitted grid. Cell (i, j) is column i from the left, row j from the TOP.

    Dungeon coordinates put y increasing NORTH, so dungeon y = ny - 1 - j.
    """

    def __init__(self, x0, px, nx, y0, py, ny):
        self.x0, self.px, self.nx = x0, px, nx
        self.y0, self.py, self.ny = y0, py, ny

    def xlines(self):
        return [self.x0 + i * self.px for i in range(self.nx + 1)]

    def ylines(self):
        return [self.y0 + j * self.py for j in range(self.ny + 1)]

    def gy(self, j):
        """Image row index -> dungeon y."""
        return self.ny - 1 - j

    def box(self, i, j, inset=INSET):
        """Pixel bounds (x0, x1, y0, y1) of the interior of cell (i, j)."""
        return (self.x0 + (i + inset) * self.px, self.x0 + (i + 1 - inset) * self.px,
                self.y0 + (j + inset) * self.py, self.y0 + (j + 1 - inset) * self.py)

    def __repr__(self):
        return ("Grid(x0=%.1f px=%.2f nx=%d | y0=%.1f py=%.2f ny=%d)"
                % (self.x0, self.px, self.nx, self.y0, self.py, self.ny))


def fit_grid(grey, field, pitch=None):
    """Fit a Grid to the map field. `pitch` may be given as (px, py) to pin it."""
    r0, r1, c0, c1 = field
    gx, gy = _gradients(grey, field)
    if pitch:
        px, py = pitch
        phx, _ = fit_phase(gx, px)
        phy, _ = fit_phase(gy, py)
    else:
        px, phx, _ = fit_axis(gx)
        py, phy, _ = fit_axis(gy)
    # absolute position of the first grid line at or after the field edge
    x0, y0 = c0 + phx, r0 + phy
    # step back while a whole cell still fits inside the field
    while x0 - px >= c0 - 2:
        x0 -= px
    while y0 - py >= r0 - 2:
        y0 -= py
    nx = int((c1 + 2 - x0) // px)
    ny = int((r1 + 2 - y0) // py)
    return Grid(x0, px, nx, y0, py, ny)


def deskew(grey, rgb, angle, fill=255.0):
    """Rotate a page so its grid is square with the pixel axes."""
    g = ndimage.rotate(grey, angle, reshape=False, order=1, cval=fill)
    r = None
    if rgb is not None:
        r = np.dstack([ndimage.rotate(rgb[:, :, k], angle, reshape=False,
                                      order=1, cval=255) for k in range(3)])
        r = np.clip(r, 0, 255).astype(np.uint8)
    return g, r


def auto_deskew(grey, rgb=None, bands=7, tol=0.06, max_iter=3):
    """Measure the sheet's skew and correct it. Returns (grey, rgb, applied).

    The measurement is the phase of the vertical grid lines fitted in
    horizontal bands: a sheet laid straight gives scatter, a rotated one gives
    a *monotonic* drift down the page. Only a monotonic drift is acted on,
    which is what keeps this from chasing fit noise -- the DMG sheet reports
    -0.015 degrees non-monotonic and is left alone, while B1 reports +0.37
    degrees monotonic across 3, 5 and 7 bands and is corrected.

    The correction is applied with the OPPOSITE sign to the measurement and
    then re-measured, so a wrong sign shows up immediately as a doubled
    residual rather than silently.
    """
    applied = 0.0
    for _ in range(max_iter):
        field = find_field(grey)
        grid = fit_grid(grey, field)
        rot = rotation_check(grey, field, grid.px, bands=bands)
        if not rot['monotonic'] or abs(rot['angle_deg']) < tol:
            break
        grey, rgb = deskew(grey, rgb, -rot['angle_deg'])
        applied += -rot['angle_deg']
    return grey, rgb, applied


def rotation_check(grey, field, pitch, bands=3):
    """Fit the x-phase in horizontal bands. Monotonic drift => the sheet is rotated."""
    r0, r1, c0, c1 = field
    h = (r1 - r0) // bands
    phases = []
    for k in range(bands):
        sub = grey[r0 + k * h: r0 + (k + 1) * h, c0:c1]
        sig = np.abs(np.diff(sub, axis=1)).sum(axis=0)
        ph, _ = fit_phase(sig, pitch)
        phases.append(ph)
    # unwrap so a phase that wraps past the pitch is not read as a huge jump
    unwrapped = [phases[0]]
    for p in phases[1:]:
        prev = unwrapped[-1]
        cands = [p + k * pitch for k in (-1, 0, 1)]
        unwrapped.append(min(cands, key=lambda v: abs(v - prev)))
    drift = unwrapped[-1] - unwrapped[0]
    mono = all(a < b for a, b in zip(unwrapped, unwrapped[1:])) or \
           all(a > b for a, b in zip(unwrapped, unwrapped[1:]))
    span = (r1 - r0) * (bands - 1) / bands
    angle = np.degrees(np.arctan2(drift, span)) if span else 0.0
    return dict(phases=phases, unwrapped=unwrapped, drift=drift,
                monotonic=bool(mono), angle_deg=float(angle))


# ---------------------------------------------------------------- per-cell stats

def cell_stats(grey, rock, ink, grid):
    """Measure every cell. Returns a list of dicts, one per cell."""
    rows = []
    H, W = grey.shape
    for j in range(grid.ny):
        for i in range(grid.nx):
            xa, xb, ya, yb = grid.box(i, j)
            xa, xb = max(0, int(round(xa))), min(W, int(round(xb)))
            ya, yb = max(0, int(round(ya))), min(H, int(round(yb)))
            if (xb - xa) * (yb - ya) < 25:
                continue
            rows.append(_measure(grey[ya:yb, xa:xb], rock[ya:yb, xa:xb],
                                 ink[ya:yb, xa:xb], i, j, grid))
    return rows


def _measure(patch, rk, nk, i, j, grid):
    hh, ww = rk.shape
    rock_frac = float(rk.mean())
    open_frac = 1.0 - rock_frac
    ink_frac = float(nk.mean())

    # --- how the rock sits in the cell: crossing it, or filling it?
    n = 4
    bh, bw = max(1, hh // n), max(1, ww // n)
    touch = sum([bool(rk[:bh, :].mean() > 0.5), bool(rk[-bh:, :].mean() > 0.5),
                 bool(rk[:, :bw].mean() > 0.5), bool(rk[:, -bw:].mean() > 0.5)])
    # which sides the rock reaches at all (used to infer where the wall lies)
    sides = ''.join(s for s, v in
                    (('N', rk[:bh, :].mean()), ('S', rk[-bh:, :].mean()),
                     ('W', rk[:, :bw].mean()), ('E', rk[:, -bw:].mean())) if v > 0.5)

    lab, ncomp = ndimage.label(rk, structure=np.ones((3, 3)))
    biggest = 0.0
    if ncomp and rk.sum():
        biggest = float(ndimage.sum(rk, lab, range(1, ncomp + 1)).max() / rk.sum())

    # --- bimodality of the greyscale, kept as a scan-quality diagnostic
    v = patch.ravel().astype(float)
    if v.max() - v.min() < 5 or v.var() == 0:
        eta, thr = 0.0, float(v.mean())
    else:
        thr = float(threshold_otsu(patch))
        lo, hi = v[v <= thr], v[v > thr]
        if len(lo) == 0 or len(hi) == 0:
            eta = 0.0
        else:
            w0, w1 = len(lo) / len(v), len(hi) / len(v)
            eta = float(w0 * w1 * (lo.mean() - hi.mean()) ** 2 / v.var())

    # a ladder of alternating rock/void bands = drawn stair treads. The treads
    # run the full width of the square, so they touch the crop border and the
    # enclosed-hole test cannot see them; counting runs along each axis can.
    slots = _hatch(rk)

    # a 45-degree wall drawn INSIDE the square, which no boundary measurement
    # can see. Diagnostic only -- see diagonal_stat() and diagcheck.py.
    diag_orient, diag_peak, diag_offset = diagonal_stat(rk)

    return dict(i=i, j=j, x=i, y=grid.gy(j),
                open_frac=open_frac, rock_frac=rock_frac, ink_frac=ink_frac,
                edges_touched=touch, rock_sides=sides, slots=slots,
                ncomp=int(ncomp), biggest=biggest, eta=eta,
                diag_orient=diag_orient, diag_peak=diag_peak,
                diag_offset=diag_offset, side_classes=side_classes(rk))


# ---------------------------------------------------------------- classify

def classify(s, t_solid=0.25, t_open=0.75):
    """open | solid | mixed

    Terrain is decided by ROCK coverage alone. Printed annotation -- room
    numbers, letters, door glyphs -- is excluded upstream by rock_mask(), so a
    numbered room reads as fully open rather than as a partial cell.
    'mixed' means rock genuinely covers part of the square: a diagonal
    passage, a cave wall, an irregular chamber edge.
    """
    o = s['open_frac']
    if o >= t_open:
        return 'open'
    if o <= t_solid:
        return 'solid'
    return 'mixed'


# ---------------------------------------------------------------- edges

def edge_stats(rock, grid, half=0.30, trim=0.25, boxr=0.42):
    # `boxr` is PRINT-SPECIFIC: it must cover the door glyph, and B1 draws
    # a door about half again the size of the DMG's. Too small and the
    # enclosed white falls outside the box, so the door reads as a plain
    # wall -- which sealed B1's area 28 completely.
    """Measure the rock lying along every cell boundary.

    Coverage is useless here: the sheet is printed graph paper, so a *ruling*
    runs along every boundary and joins the rock mass. What separates a ruling
    from a drawn wall is STROKE THICKNESS -- measured perpendicular to the
    boundary and taken as a median along its length, a ruling is 0-3 px at
    200 dpi while a drawn wall bar is 6+ px.

    Doors are drawn as small outlined rectangles straddling the boundary, so in
    the rock mask they are thick too. They are distinguished topologically: an
    outline ENCLOSES white, a filled bar does not. `hole` is the largest
    enclosed white region in a box centred on the boundary midpoint.

    Edges are canonical: 'V' is the EAST side of (x,y), 'H' the NORTH side.
    """
    H, W = rock.shape
    out = []
    for y in range(grid.ny):
        j = grid.ny - 1 - y                       # image row for this dungeon row
        for x in range(grid.nx):
            xc = grid.x0 + (x + 1) * grid.px      # east boundary of (x,y)
            yc = grid.y0 + (j + 0.5) * grid.py
            out.append(_edge(rock, x, y, 'V', xc, yc, grid, half, trim, boxr, H, W))  # noqa: E501
            xc2 = grid.x0 + (x + 0.5) * grid.px
            yc2 = grid.y0 + j * grid.py           # north boundary of (x,y)
            out.append(_edge(rock, x, y, 'H', xc2, yc2, grid, half, trim, boxr, H, W))
    return out


def _edge(rock, x, y, orient, cx, cy, grid, half, trim, boxr, H, W):
    if orient == 'V':
        xa, xb = cx - half * grid.px, cx + half * grid.px
        ya, yb = cy - (0.5 - trim) * grid.py, cy + (0.5 - trim) * grid.py
    else:
        xa, xb = cx - (0.5 - trim) * grid.px, cx + (0.5 - trim) * grid.px
        ya, yb = cy - half * grid.py, cy + half * grid.py
    xa, xb = max(0, int(round(xa))), min(W, int(round(xb)))
    ya, yb = max(0, int(round(ya))), min(H, int(round(yb)))
    if xb - xa < 3 or yb - ya < 3:
        return dict(x=x, y=y, orient=orient, thick=0.0, cover=0.0, hole=0)
    band = rock[ya:yb, xa:xb]
    # thickness perpendicular to the boundary, sampled along its length
    prof = band.sum(axis=1 if orient == 'V' else 0)
    thick = float(np.median(prof))
    # `gap`: how much of the boundary the rock does NOT block. A wall has to
    # SPAN a boundary to close it; a boundary the rock only partly covers is
    # still a way through. Using the median alone called a wall wherever two
    # half-filled squares met, which severed passages that plainly connect on
    # the page.
    gap = float((prof < 4.5).mean()) if prof.size else 0.0

    # enclosed white in a square box on the boundary midpoint => door outline
    bxa, bxb = max(0, int(cx - boxr * grid.px)), min(W, int(cx + boxr * grid.px))
    bya, byb = max(0, int(cy - boxr * grid.py)), min(H, int(cy + boxr * grid.py))
    hole, ar, thin, cent = 0, 0.0, 0, None
    p = rock[bya:byb, bxa:bxb]
    if p.size:
        hole, ar, thin, cent = _holes(p)

    # THE ONE-SIDED DOOR TEST. Proposed by the player 2026-08-28, after six
    # furnished rooms in a row had been mis-extracted:
    #
    #   "the furniture lines only exist on one side of the wall, unlike the
    #    doors that go through the wall"
    #
    # A door is a way THROUGH a wall, so its glyph is bisected by the wall bar.
    # Drawn furniture sits against an intact wall, wholly on the room side.
    # `offset` is how far the glyph's centre lies from the wall bar's centre,
    # in cells, measured perpendicular to the boundary. See door_suspect().
    wall, wall_pos = _flank(rock, cx, cy, orient, grid, half, H, W)
    offset = None
    if cent is not None and wall_pos is not None:
        gpos = (bxa + cent[1]) if orient == 'V' else (bya + cent[0])
        offset = abs(gpos - wall_pos) / (grid.px if orient == 'V' else grid.py)
    return dict(x=x, y=y, orient=orient, thick=thick, gap=gap,
                cover=float(band.mean()), hole=hole, hole_aspect=ar,
                slots=thin, wall=wall, offset=offset)


def _flank(rock, cx, cy, orient, grid, half, H, W, inner=0.55, outer=1.05):
    """(thickness, position) of the wall bar BESIDE the glyph, not under it.

    `thick` above samples a band 0.5 cell long centred on the boundary midpoint
    -- which is entirely INSIDE the door glyph, so it measures the glyph and
    never the wall. That is why thickness could never tell a door from a drawn
    bed: area 24's fabrications measured 9 and 10 against a genuine door's 7,
    i.e. closer to the middle of the genuine band than the real door was.

    This looks at the boundary on either SIDE of the glyph instead, and returns
    the stronger flank together with the ink-weighted position of its bar. A
    door is a hole in a wall, so the wall carries on past it; furniture drawn
    inside a room sits on nothing but a 2 px graph-paper ruling.
    """
    best_thick, best_pos = 0.0, None
    for sgn in (-1, 1):
        if orient == 'V':
            xa = max(0, int(cx - half * grid.px))
            xb = min(W, int(cx + half * grid.px))
            lo, hi = sorted((cy + sgn * inner * grid.py,
                             cy + sgn * outer * grid.py))
            ya, yb = max(0, int(lo)), min(H, int(hi))
            if yb - ya < 3 or xb - xa < 3:
                continue
            sub = rock[ya:yb, xa:xb]
            prof, base = sub.sum(axis=0), xa
            thick = float(np.median(sub.sum(axis=1)))
        else:
            ya = max(0, int(cy - half * grid.py))
            yb = min(H, int(cy + half * grid.py))
            lo, hi = sorted((cx + sgn * inner * grid.px,
                             cx + sgn * outer * grid.px))
            xa, xb = max(0, int(lo)), min(W, int(hi))
            if xb - xa < 3 or yb - ya < 3:
                continue
            sub = rock[ya:yb, xa:xb]
            prof, base = sub.sum(axis=1), ya
            thick = float(np.median(sub.sum(axis=0)))
        if prof.sum() and thick > best_thick:
            best_thick = thick
            best_pos = base + float(
                (prof * np.arange(len(prof))).sum() / prof.sum())
    return best_thick, best_pos


def _hatch(rk):
    """Largest number of rock/void alternations across the square.

    Stair treads are drawn as a ladder of parallel bars: collapsing the square
    perpendicular to them gives many runs. Plain rock gives none, a diagonal
    gives one or two.
    """
    best = 0
    for axis in (0, 1):
        prof = rk.mean(axis=1 - axis) > 0.5
        if prof.size > 1:
            best = max(best, int((prof[1:] != prof[:-1]).sum()))
    return best


def _holes(p, slot_aspect=3.0, slot_thin=6):
    """(largest enclosed-white area, its aspect ratio, thin slots, centroid).

    A door leaf is drawn as a compact rectangle roughly 15x8 px at 200 dpi.
    Stair treads are drawn as a ladder of long thin slots -- same "enclosed
    white" signature, very different shape -- so aspect ratio is what keeps
    a staircase from being read as a stack of doors.

    The centroid is of ALL the enclosed white in the box, not of the largest
    component, because a door glyph straddling a wall has its interior CUT IN
    TWO BY THE WALL BAR: the largest half alone sits off to one side, which is
    exactly backwards for the test in _flank/door_suspect.
    """
    h = ndimage.binary_fill_holes(p) & ~p
    if not h.any():
        return 0, 0.0, 0, None
    lab, n = ndimage.label(h)
    best, best_ar, thin = 0, 0.0, 0
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        area = int((lab[sl] == k).sum())
        hh = sl[0].stop - sl[0].start
        ww = sl[1].stop - sl[1].start
        ar = max(hh, ww) / max(1, min(hh, ww))
        if area >= 15 and ar >= slot_aspect and min(hh, ww) <= slot_thin:
            thin += 1
        if area > best:
            best, best_ar = area, ar
    ys, xs = np.nonzero(h)
    return best, float(best_ar), thin, (float(ys.mean()), float(xs.mean()))


def door_suspect(e, min_wall=5.0, max_offset=0.14):
    """Is this `door` call actually a piece of drawn furniture?

    Returns a reason string, or None if the call looks sound.

    This FLAGS; it does not reclassify. The two failure modes are not
    symmetric: a fabricated door invents a passage the party can be walked
    down and is caught only when someone reads the printed page, whereas a
    missed door merely seals a room until someone checks. So the flag drives a
    contact sheet for review (`doorcheck.py`) and the human verdict goes into
    the corrections file, which always wins.

    Two things separate a door from furniture, and both come from the same
    observation -- a door goes THROUGH the wall:

      * `wall`: there has to BE a wall. Ovals and beds drawn inside a room sit
        on a 2-4 px graph-paper ruling; a drawn wall bar is 8+ px.
      * `offset`: the glyph has to be ON that wall, not beside it. Area 24's
        fabricated pair sit 0.35 and 0.17 cells off the bar they abut.

    Validated on B1 level 1 against 7 doors the party has physically walked
    through and 16 confirmed fabrications: rejects 9 of the 16, keeps 7 of 7.
    It is a sieve, not a classifier -- the contact sheet catches the rest.
    """
    wall = e.get('wall') or 0.0
    if wall < min_wall:
        return ('no wall -- the boundary beside the glyph is %.1f px, a '
                'graph-paper ruling, not a drawn wall' % wall)
    off = e.get('offset')
    if off is None:
        return 'no wall bar found to measure the glyph against'
    if off > max_offset:
        return ('one-sided -- the glyph sits %.2f cells off the wall bar, so '
                'it does not go through the wall' % off)
    return None


def is_door(e, t_hole=35, max_aspect=3.5):
    """A compact enclosed rectangle on the boundary, not a stair tread."""
    return (e['hole'] >= t_hole and e['hole_aspect'] <= max_aspect
            and e['slots'] < 2)


def is_stairs(e, min_slots=1, min_aspect=3.5, min_hole=30):
    """A ladder of long thin treads crossing the boundary.

    Stairs are drawn as parallel bars, which look like a thick barrier to a
    thickness test and like a stack of doors to a hole test -- so both reject
    them and the boundary falls through to 'wall'. But a staircase is a way
    THROUGH, and calling it a wall severs the passage it belongs to: on B1 it
    sealed the entrance corridor off from the rest of the level.
    """
    return (e['slots'] >= min_slots and e['hole'] >= min_hole
            and e['hole_aspect'] >= min_aspect)


def classify_edge(e, terrain, nx, ny, t_thick=4.5, t_hole=25, t_gap=0.25):
    """unknown | open | wall | door, plus a confidence 1-10.

    Terrain decides first -- a boundary against solid rock is a wall. Between
    two open cells the boundary itself decides, by thickness and by the
    enclosed-hole test. A boundary touching a 'mixed' cell is recorded but
    flagged: the map is ambiguous there and a human should look.
    """
    x, y, o = e['x'], e['y'], e['orient']
    bx, by = (x + 1, y) if o == 'V' else (x, y + 1)
    a = terrain.get((x, y), 'unknown')
    b = terrain.get((bx, by), 'unknown')

    if not (0 <= bx < nx and 0 <= by < ny):
        # the sheet's own edge: nothing is drawn beyond it, so it bounds the map
        return ('wall', 8) if a == 'open' else ('wall', 10)
    if a == 'unknown' or b == 'unknown':
        return ('unknown', 1)
    if a == 'solid' and b == 'solid':
        return ('wall', 10)
    if a == 'solid' or b == 'solid':
        return ('wall', 9)
    if 'mixed' in (a, b):
        # A partial square's boundary is rarely a clean full-width wall. What
        # matters is whether any of it is clear: rock must SPAN the boundary to
        # close it.
        if is_door(e):
            return ('door', 5)
        if is_stairs(e):
            return ('stairs', 5)
        if e['gap'] >= t_gap:
            return ('open', 3)
        return ('wall', 3) if e['thick'] >= t_thick else ('open', 3)
    # both open
    if is_door(e):
        return ('door', 9)
    if is_stairs(e):
        return ('stairs', 7)
    if e['thick'] >= t_thick:
        return ('wall', 8)
    return ('open', 9)


ADJACENT_SIDES = ('NW', 'NE', 'SW', 'SE')


def passage_kind(s, klass):
    """Is a partly-filled square a 45-degree passage?

    `rock_sides` records which of the four borders the rock reaches. Rock on
    two ADJACENT sides means it occupies one corner and the floor runs corner
    to corner -- a diagonal. Rock on two OPPOSITE sides is a straight corridor
    pinched from both flanks, which is not the same thing.

    Flagging matters because a HALF-width diagonal connects only at the corner:
    the squares that would bridge it orthogonally hold no floor at all, so
    reachability has to be allowed to step corner-to-corner between two squares
    that both carry this flag.
    """
    if klass != 'mixed':
        return None
    sides = ''.join(sorted(s['rock_sides']))
    for pair in ADJACENT_SIDES:
        if sides == ''.join(sorted(pair)):
            return 'diagonal'
    return None


# ------------------------------------------------- diagonal walls (MEASURE ONLY)
#
# `edge_stats` asks "how much rock lies along this grid boundary", and a wall
# drawn at 45 degrees answers "none" while completely blocking passage: the rock
# sits INSIDE the square, a foot and a half from the boundary the model can talk
# about. Everything below MEASURES that; nothing acts on it. See
# DIAGONAL_WALLS.md, and diagcheck.py for the review tool that reads it.

DIAG_LO, DIAG_HI = 0.15, 0.45   # rock fraction of a drawn PARTITION, measured
DIAG_PEAK = 0.90                # peak / cell side at which a 45-degree line is claimed


def diagonal_stat(rk, lo=DIAG_LO, hi=DIAG_HI):
    """(orientation, peak, offset): a 45-degree line drawn ACROSS the square.

    A Radon transform restricted to the only two angles these sheets use.
    Project the rock onto the two 45-degree families -- constant `row+col` is
    the SW-NE family, constant `col-row` the NW-SE one -- and take the strongest
    single line, normalised by the cell side. A band drawn corner to corner
    projects onto ONE diagonal index for its whole length, so the peak reaches
    1.0; nothing else on a line-art map does. Furniture is short, curved or off
    45 degrees, and an orthogonal wall projects onto the orthogonal axis.

    Gated on rock fraction because the peak alone cannot separate a diagonal
    WALL from the flank of a diagonal CORRIDOR: a corner wedge's hypotenuse is
    also a 45-degree line, and it only gets long enough to score by filling most
    of the square. Measured on B1: partitions 0.15-0.45 rock, corridor flanks
    0.5-0.7.

    `offset` is where the winning line lies inside the cell, as a fraction of
    the cell side from its centre -- ~0 for the usual corner-to-corner band, and
    what you would need to decide which half of a split square is which.

    Measured on B1 level 1 (1,358 in-frame cells) against 12 adjudicated
    partitions: peak 0.90-1.00 for all twelve, max 0.50 over 60 random furnished
    cells, and 0.27-0.83 for the seven adjudicated false positives.
    """
    h, w = rk.shape
    side = float(min(h, w))
    if side < 4 or not (lo <= float(rk.mean()) <= hi):
        return (None, 0.0, 0.0)
    ys, xs = np.nonzero(rk)
    best = (None, 0.0, 0.0)
    for orient, idx in (('SWNE', ys + xs), ('NWSE', xs - ys + (h - 1))):
        prof = np.bincount(idx, minlength=h + w - 1)
        k = int(prof.argmax())
        peak = float(prof[k]) / side
        if peak > best[1]:
            best = (orient, peak, (k - (h + w - 2) / 2.0) / side)
    return best


def side_classes(rk, min_side=0.25, min_area=0.05):
    """Which of the square's four sides are mutually reachable through its floor.

    The question the reachability graph actually needs, asked of one square:

        open cell        -> ('NSEW',)          one class, all four sides
        solid            -> ()                 no floor at all
        wall on SW-NE    -> ('NW', 'SE')       TWO classes: it is cut in half
        wall on NW-SE    -> ('NE', 'SW')
        corner wedge     -> ('NSEW',) or one class -- a mass face does not cut it

    Three details cost two failed attempts to find, and two of them are corners:

      * DILATE the rock by one pixel before labelling the floor. A band drawn
        corner to corner leaves a one-pixel leak at the cell corner and a
        4-connected label walks straight through it -- without the dilation all
        twelve of B1's partitions came back as a single component.
      * Score a side by the FRACTION of it the component reaches, against the
        same 0.25 floor `classify_edge` uses for `gap`. A diagonal band exits
        through the corners, so the far component clips a few pixels of every
        border and a "does it touch at all" test reads every component as
        touching all four sides.
      * Drop components below `min_area` of the square. B1's rooms are drawn
        full of furniture and a table against a wall shaves slivers off the
        floor; unfiltered, a fifth of the sheet reports three or four classes.

    Independent of diagonal_stat() and with disjoint false positives on B1
    (precision 0.85, recall 0.92 alone); the conjunction is precision 1.00.
    """
    h, w = rk.shape
    if h < 4 or w < 4:
        return ()
    lab, n = ndimage.label(~ndimage.binary_dilation(rk, np.ones((3, 3))))
    out = []
    for k in range(1, n + 1):
        m = (lab == k)
        if m.mean() < min_area:
            continue
        sides = ''.join(s for s, v in (('N', m[0].mean()), ('S', m[-1].mean()),
                                       ('E', m[:, -1].mean()), ('W', m[:, 0].mean()))
                        if v >= min_side)
        if sides:
            out.append(sides)
    return tuple(sorted(out))


# the only two ways a 45-degree wall can cut a square in half
SIDE_SPLIT = {('NW', 'SE'): 'SWNE', ('NE', 'SW'): 'NWSE'}


def split_orient(classes):
    """'SWNE' | 'NWSE' | None -- the wall implied by a side_classes() tuple.

    A wall running SW-NE leaves the north and west sides on one side of it and
    the south and east sides on the other, so the split is exactly two classes
    on COMPLEMENTARY ADJACENT PAIRS. Anything else -- one class, a class holding
    an opposite pair (N and S), a leftover singleton -- is not a square cut in
    two by a diagonal. On B1 that pattern is what separates a wall from the
    twelve-odd cells where furniture merely fragments the floor.
    """
    return SIDE_SPLIT.get(tuple(classes))


def diagonal_suspect(s, min_peak=DIAG_PEAK):
    """Does this square carry a 45-degree wall? Returns a reason, or None.

    FLAGS; never reclassifies, for the same reason door_suspect does not (see
    its docstring and diagcheck.py). Validated on ONE sheet with TWELVE
    positives, which is not enough to let it write to a database a live game is
    read from.
    """
    if not s.get('diag_orient') or (s.get('diag_peak') or 0.0) < min_peak:
        return None
    return ('%s wall: 45-degree rock spans %.2f of the cell side, rock %.2f of '
            'the cell' % (s['diag_orient'], s['diag_peak'], s['rock_frac']))


def frame_depth(terrain, nx, ny, max_depth=4, thresh=0.85):
    """How many cells deep the drawn map border runs.

    A printed dungeon map is enclosed by a solid frame, and outside it sits
    scenery that is not dungeon at all -- B1 draws a ragged hillside along the
    bottom and a compass rose in the corner, and both read as floor. On B1 that
    scenery was 33 of the 56 unreachable squares, so it is worth removing
    before anyone tries to explain it.

    Returned depth d means rings 0..d are frame. Measured per side and taken as
    the deepest, because a side may be pierced (B1's south ring 0 is the
    hillside at 0.05 solid while ring 1 behind it is 0.97).
    """
    def solid_frac(cells):
        vals = [terrain[c] for c in cells if c in terrain]
        return sum(1 for t in vals if t == 'solid') / max(1, len(vals))

    depth = -1
    for r in range(max_depth):
        sides = (solid_frac([(x, ny - 1 - r) for x in range(nx)]),
                 solid_frac([(x, r) for x in range(nx)]),
                 solid_frac([(r, y) for y in range(ny)]),
                 solid_frac([(nx - 1 - r, y) for y in range(ny)]))
        if max(sides) >= thresh:
            depth = r
    return depth


def outside_cells(terrain, nx, ny, depth=None):
    """Squares in the frame rings that are not a passage through it.

    A frame square that reads as clear floor is how you get in -- B1's entrance
    pierces the frame at exactly one column -- so 'open' is kept and everything
    else in the rings is scenery.
    """
    if depth is None:
        depth = frame_depth(terrain, nx, ny)
    if depth < 0:
        return set()
    out = set()
    for (x, y), t in terrain.items():
        in_ring = (x <= depth or y <= depth
                   or x >= nx - 1 - depth or y >= ny - 1 - depth)
        if in_ring and t != 'open':
            out.add((x, y))
    return out


def cell_confidence(s, klass):
    """How much to trust a terrain call, 1-10."""
    o = s['open_frac']
    if klass == 'solid':
        return 10 if o <= 0.02 else 8
    if klass == 'open':
        return 10 if o >= 0.98 else 8
    return 3          # mixed: always worth a human glance


# ---------------------------------------------------------------- images

def overlay(rgb, grid, path, field=None, every=5, cells=None):
    """Draw the fitted grid back onto the page so alignment can be eyeballed."""
    img = Image.fromarray(rgb.astype(np.uint8)).convert('RGB')
    d = ImageDraw.Draw(img, 'RGBA')
    if field:
        r0, r1, c0, c1 = field
        d.rectangle([c0, r0, c1, r1], outline=(0, 160, 0, 255), width=3)
    if cells:
        fill = {'solid': (0, 0, 255, 60), 'mixed': (255, 140, 0, 90),
                'glyph': (255, 0, 255, 70)}
        for s in cells:
            k = fill.get(s.get('klass'))
            if k:
                xa, xb, ya, yb = grid.box(s['i'], s['j'], inset=0.02)
                d.rectangle([xa, ya, xb, yb], fill=k)
    for n, x in enumerate(grid.xlines()):
        heavy = (n % every == 0)
        d.line([(x, grid.y0), (x, grid.y0 + grid.ny * grid.py)],
               fill=(255, 0, 0, 220 if heavy else 90), width=2 if heavy else 1)
        if heavy:
            d.text((x + 2, grid.y0 - 16), str(n), fill=(200, 0, 0, 255))
    for n, y in enumerate(grid.ylines()):
        heavy = (n % every == 0)
        d.line([(grid.x0, y), (grid.x0 + grid.nx * grid.px, y)],
               fill=(255, 0, 0, 220 if heavy else 90), width=2 if heavy else 1)
        if heavy:
            d.text((grid.x0 - 34, y - 6), str(grid.gy(n)) if n < grid.ny else '',
                   fill=(200, 0, 0, 255))
    img.save(path)
    return path
