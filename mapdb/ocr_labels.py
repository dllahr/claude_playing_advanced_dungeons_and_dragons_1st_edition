#!/usr/bin/env python3
"""Read the printed labels off a dungeon map and attach them to grid cells.

The map's annotation layer -- separated from the rock by extract.rock_mask() --
holds room numbers ("12"), sub-location letters ("A", "B", "C") and secret-door
markers ("S"). Individual digits arrive as separate connected components, so
they are merged into labels first, then each label is cropped, upscaled and
passed to tesseract with a tight character whitelist.
"""
import numpy as np
import pytesseract
from PIL import Image
from scipy import ndimage

MIN_AREA = 40        # ignore specks
MAX_GAP = 16         # px between digits of the same number, at 200 dpi
WHITELIST = '0123456789ABCS'


def components(ink, field, min_area=MIN_AREA):
    """Bounding boxes of ink blobs inside the map field."""
    r0, r1, c0, c1 = field
    m = np.zeros_like(ink)
    m[r0:r1, c0:c1] = ink[r0:r1, c0:c1]
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        area = int((lab[sl] == k).sum())
        if area >= min_area:
            out.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop, area])
    return out


def merge(boxes, max_gap=MAX_GAP):
    """Group digit blobs into whole labels.

    Two blobs belong to the same label when they overlap vertically (same line
    of type) and sit within `max_gap` horizontally.
    """
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    parent = list(range(len(boxes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            vov = min(a[3], b[3]) - max(a[1], b[1])
            hgap = max(a[0], b[0]) - min(a[2], b[2])
            if vov > 0.5 * min(a[3] - a[1], b[3] - b[1]) and hgap <= max_gap:
                parent[find(i)] = find(j)

    groups = {}
    for i, b in enumerate(boxes):
        groups.setdefault(find(i), []).append(b)
    out = []
    for g in groups.values():
        out.append((min(b[0] for b in g), min(b[1] for b in g),
                    max(b[2] for b in g), max(b[3] for b in g),
                    sum(b[4] for b in g), len(g)))
    return out


def read(grey, box, pad=6, scale=6):
    """OCR one label box."""
    x0, y0, x1, y1 = box[:4]     # accepts a raw component box or a merged label
    crop = grey[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
    if crop.size == 0:
        return ''
    img = Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8))
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    cfg = '--psm 10' if (x1 - x0) < 22 else '--psm 8'
    cfg += ' -c tessedit_char_whitelist=' + WHITELIST
    return pytesseract.image_to_string(img, config=cfg).strip().replace(' ', '')


def to_cell(box, grid):
    cx = (box[0] + box[2]) / 2.0
    cy = (box[1] + box[3]) / 2.0
    i = int((cx - grid.x0) // grid.px)
    j = int((cy - grid.y0) // grid.py)
    return i, grid.gy(j)


def labels(grey, ink, field, grid):
    """[(text, x, y, area, nblobs)] for every label found."""
    out = []
    for b in merge(components(ink, field)):
        t = read(grey, b)
        x, y = to_cell(b, grid)
        out.append(dict(text=t, x=x, y=y, area=b[4], blobs=b[5],
                        w=b[2] - b[0], h=b[3] - b[1]))
    return out
