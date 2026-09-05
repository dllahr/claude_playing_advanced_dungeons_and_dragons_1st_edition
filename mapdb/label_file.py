#!/usr/bin/env python3
"""Read a hand-made table of where each area label is printed on a map.

The file is the SOURCE OF RECORD for label positions -- the key modules read it
rather than copying from it, so editing the file changes the map and there is
no transcription to drift.

Format is tab-separated with a header line:

    number<TAB>locations<TAB>notes
    12<TAB>(30,37)
    12<TAB>straddles: (9,32) (10,32)
    1<TAB>repeated at these locations: (15,8); (17,8); (15,13)
    B (for 2)<TAB>(7,36)<TAB>drawn within the pool

Only the coordinates matter; "straddles", "repeated at", punctuation and any
notes column are ignored. A label may occupy more than one square either
because it straddles a boundary or because the same area is printed in several
places -- B1's area 1 appears six times -- so every entry maps to a LIST.

Names are normalised so sub-locations do not collide. On the DMG sheet areas 1
and 2 each have an "A" and a "B"; a flat namespace silently keeps one of each,
which is how "2B" went missing from the key for a fortnight.

    "12"          -> "12"
    "1A"          -> "1"  and "1A"   (the sheet prints them together)
    "B (for 2)"   -> "2B"
"""
import re

COORD = re.compile(r'\((\s*\d+)\s*,\s*(\d+\s*)\)')
FOR = re.compile(r'^([A-Za-z])\s*\(\s*for\s+(\w+)\s*\)$', re.I)
NUM_LETTER = re.compile(r'^(\d+)([A-Za-z])$')


def normalise(name):
    """Return the list of keys a raw label name maps to."""
    name = name.strip()
    m = FOR.match(name)
    if m:
        return ['%s%s' % (m.group(2), m.group(1).upper())]
    m = NUM_LETTER.match(name)
    if m:
        # the sheet prints "1A": it is both the area's own label and its
        # sub-location A, sitting in the same square
        return [m.group(1), '%s%s' % (m.group(1), m.group(2).upper())]
    return [name]


def load(path):
    """{key: [(x, y), ...]} for every label in the file."""
    out = {}
    with open(path) as fh:
        lines = fh.read().splitlines()
    for raw in lines[1:] if lines and 'location' in lines[0].lower() else lines:
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        fields = raw.split('\t')
        name = fields[0].strip()
        if not name:
            continue
        rest = '\t'.join(fields[1:2])          # locations column only
        cells = [(int(a), int(b)) for a, b in COORD.findall(rest)]
        if not cells:
            continue
        for key in normalise(name):
            out.setdefault(key, [])
            for c in cells:
                if c not in out[key]:
                    out[key].append(c)
    return out


def anchors(rooms):
    """One canonical cell per area, for the node graph and the ASCII render.

    The first listed square. For a straddling label that is its left/lower
    half; for a repeated area it is whichever instance the file names first,
    which is a reading order rather than a claim about the room.
    """
    return {k: v[0] for k, v in rooms.items() if v}


def all_cells(rooms):
    """Every square any label occupies, for shielding them from the rock mask."""
    return [c for v in rooms.values() for c in v]
