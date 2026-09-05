"""Synthetic maps with known ground truth.

Tests that assert against the real DMG page can only ever check that today's
output matches yesterday's. To assert that the extractor is *correct* we need a
map whose answer we already know, so this module draws one: a rock field with
chosen squares opened, printed rulings on every boundary, drawn wall bars, door
glyphs, stair hatching, isolated numerals, diagonal corridors and diagonal walls
-- each planted at a known coordinate and returned alongside the image.

Values are chosen to sit either side of extract.DARK (140):
rock and ink are well below it, floor well above, rulings dark but thin.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

PAGE = 250        # blank paper outside the drawn map field
ROCK = 45
FLOOR = 235
RULING = 95
INK = 25


class SynthMap:
    """Draw a dungeon map on graph paper and remember what was drawn."""

    def __init__(self, nx=16, ny=12, pitch=40, margin=70):
        self.nx, self.ny, self.p, self.m = nx, ny, pitch, margin
        self.W = nx * pitch + 2 * margin
        self.H = ny * pitch + 2 * margin
        self.img = Image.new('L', (self.W, self.H), PAGE)
        self.d = ImageDraw.Draw(self.img)
        # the map field: rock everywhere until squares are opened in it
        self.d.rectangle([margin, margin,
                          margin + nx * pitch, margin + ny * pitch], fill=ROCK)
        self.terrain = {(x, y): 'solid' for x in range(nx) for y in range(ny)}
        self.edges = {}
        self.labels = {}
        self.stairs = set()
        self.diagonals = {}

    # -- geometry helpers; dungeon y increases north, image rows increase south
    def cx(self, x):
        return self.m + x * self.p

    def cy(self, y):
        return self.m + (self.ny - 1 - y) * self.p

    # -- drawing
    def open_cell(self, x, y):
        self.d.rectangle([self.cx(x), self.cy(y),
                          self.cx(x) + self.p, self.cy(y) + self.p], fill=FLOOR)
        self.terrain[(x, y)] = 'open'
        return self

    def open_rect(self, x0, y0, x1, y1):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.open_cell(x, y)
        return self

    def corridor(self, cells):
        for x, y in cells:
            self.open_cell(x, y)
        return self

    def rulings(self, width=2):
        """Printed graph paper: a thin line on every grid boundary."""
        for i in range(self.nx + 1):
            x = self.cx(i)
            self.d.line([(x, self.m), (x, self.m + self.ny * self.p)],
                        fill=RULING, width=width)
        for j in range(self.ny + 1):
            y = self.m + j * self.p
            self.d.line([(self.m, y), (self.m + self.nx * self.p, y)],
                        fill=RULING, width=width)
        return self

    def wall(self, x, y, orient, width=9):
        """A drawn wall bar: same place as a ruling, several times thicker."""
        if orient == 'V':
            xc = self.cx(x + 1)
            self.d.rectangle([xc - width // 2, self.cy(y),
                              xc + width // 2, self.cy(y) + self.p], fill=ROCK)
        else:
            yc = self.cy(y)
            self.d.rectangle([self.cx(x), yc - width // 2,
                              self.cx(x) + self.p, yc + width // 2], fill=ROCK)
        self.edges[(x, y, orient)] = 'wall'
        return self

    def door(self, x, y, orient, half_long=11, half_short=7, stroke=2):
        """A door leaf: an outlined rectangle straddling the boundary."""
        if orient == 'V':
            xc, yc = self.cx(x + 1), self.cy(y) + self.p // 2
            box = [xc - half_short, yc - half_long, xc + half_short, yc + half_long]
        else:
            xc, yc = self.cx(x) + self.p // 2, self.cy(y)
            box = [xc - half_long, yc - half_short, xc + half_long, yc + half_short]
        self.d.rectangle(box, fill=FLOOR, outline=ROCK, width=stroke)
        self.edges[(x, y, orient)] = 'door'
        return self

    def stair(self, x, y, bars=5, thick=3):
        """Stair treads: a ladder of parallel bars filling the square."""
        step = self.p // (bars + 1)
        for k in range(1, bars + 1):
            yy = self.cy(y) + k * step
            self.d.rectangle([self.cx(x) + 3, yy,
                              self.cx(x) + self.p - 3, yy + thick], fill=ROCK)
        self.stairs.add((x, y))
        return self

    def label(self, x, y, digits=2, h=28, w=13, gap=4):
        """An isolated numeral inside an open square: ink, not rock."""
        total = digits * w + (digits - 1) * gap
        x0 = self.cx(x) + (self.p - total) // 2
        y0 = self.cy(y) + (self.p - h) // 2
        for k in range(digits):
            xa = x0 + k * (w + gap)
            self.d.rectangle([xa, y0, xa + w, y0 + h], fill=INK)
        self.labels[(x, y)] = digits
        return self

    def label_touching_rock(self, x, y, h=28, w=13):
        """A numeral printed half over the rock, so it bridges into the mass.

        This is the failure that fabricated walls around areas 29, 32 and 35 on
        the real DMG sheet.
        """
        x0 = self.cx(x) - w // 2          # straddles the west boundary
        y0 = self.cy(y) + (self.p - h) // 2
        self.d.rectangle([x0, y0, x0 + w, y0 + h], fill=INK)
        return self

    def diagonal(self, x0, y0, x1, y1, width=None):
        """A 45-degree corridor from one cell centre to another."""
        width = width or int(self.p * 0.8)
        a = (self.cx(x0) + self.p // 2, self.cy(y0) + self.p // 2)
        b = (self.cx(x1) + self.p // 2, self.cy(y1) + self.p // 2)
        self.d.line([a, b], fill=FLOOR, width=width)
        return self

    def diagonal_wall(self, x0, y0, x1, y1, width=8):
        """A 45-degree WALL: the same line as diagonal(), drawn in ROCK.

        Corner to corner across the run, which is how these sheets draw one, so
        every square it crosses is cut cleanly in half. `width` defaults to 8 px
        at pitch 40 -- normal wall weight; B1's measured 5.6-9.0 perpendicular.

        This is the shape no boundary measurement can see. The rock sits INSIDE
        the square, so the grid boundaries around it measure a printed ruling and
        `extents.py` floods straight through what is plainly a wall on the page.
        Note the distinction that matters: the same line drawn in FLOOR is a
        diagonal CORRIDOR, whose cells hold rock in the same two corners.
        """
        sx, sy = (1 if x1 >= x0 else -1), (1 if y1 >= y0 else -1)
        a = (self.cx(x0) if sx > 0 else self.cx(x0) + self.p,
             self.cy(y0) + self.p if sy > 0 else self.cy(y0))
        b = (self.cx(x1) + self.p if sx > 0 else self.cx(x1),
             self.cy(y1) if sy > 0 else self.cy(y1) + self.p)
        self.d.line([a, b], fill=ROCK, width=width)
        orient = 'SWNE' if sx == sy else 'NWSE'
        for k in range(max(abs(x1 - x0), abs(y1 - y0)) + 1):
            self.diagonals[(x0 + k * sx, y0 + k * sy)] = orient
        return self

    # -- output
    def render(self, rotate=0.0):
        a = np.asarray(self.img, dtype=float)
        if rotate:
            a = ndimage.rotate(a, rotate, reshape=False, order=1, cval=PAGE)
        return a

    def truth(self):
        return dict(nx=self.nx, ny=self.ny, pitch=self.p, margin=self.m,
                    terrain=dict(self.terrain), edges=dict(self.edges),
                    labels=dict(self.labels), stairs=set(self.stairs),
                    diagonals=dict(self.diagonals))


def simple_map():
    """A small map exercising every feature, with its ground truth."""
    m = SynthMap(nx=16, ny=12, pitch=40)
    # an east-west corridor across the middle
    m.corridor([(x, 6) for x in range(1, 15)])
    # a room hanging off it
    m.open_rect(2, 2, 4, 4)
    m.corridor([(3, 5)])
    # a north-south corridor
    m.corridor([(10, y) for y in range(2, 10)])
    m.rulings()
    m.wall(7, 6, 'V')          # a bar across the east-west corridor
    m.door(4, 6, 'V')          # a door in the same corridor
    m.door(10, 7, 'H')         # a door in the north-south corridor
    m.stair(12, 6)
    m.label(6, 6, digits=2)
    return m
