#!/usr/bin/env python3
"""Hand-verified key for the DMG sample dungeon, and the text-derived node graph.

ROOMS -- anchor cell of every printed label. Produced by OCR (ocr_labels.py)
and then checked by eye against images/09_label_qa.png; the OCR-only pass got
about 70% right, missing labels printed over the rock (29, 32, 35) and
misreading partial numbers, so these values are the corrected ones.

MARKERS -- printed 'S' secret-door markers, recorded as cell features.

CONNECTIONS -- built from the DMG key text (pdf pages 95 and 97), entirely
independently of the map image. This is the cross-check: anything the text
asserts should be visible in the grid, and a disagreement means one of the two
readings is wrong.
"""

# Where each area label is printed. Read from the hand-made table rather than
# copied into this file, so that file stays the single source of record.
#
# It supersedes an OCR-plus-eye pass that was 41 of 43 right: area 39's anchor
# was two squares out, and the sub-location letters had collided -- areas 1 and
# 2 each have an "A" and a "B", and a flat namespace had silently kept one of
# each, losing 2B entirely.
import os

import label_file as _lf

LABELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                           'dlwork', 'archive',
                           '2026-08-24_dmg_lv1_number_locations.txt')
ROOMS = _lf.load(LABELS_FILE)
TEXT_REF = 'DMG pdf p.95/97'

# printed 'S' markers: cell -> what they annotate
MARKERS = {
    (10, 42): 'secret door / passage between areas 4 and 5',
    (13, 42): 'secret door / passage between areas 4 and 5',
    (15, 39): 'secret door off the area 1 corridor',
    (12, 24): 'secret door in the SOUTH wall of area 3, leading toward 24',
    (32, 3): 'secret door near area 38',
}

# Edges the text pins down exactly. (x, y, orient, kind, note)
SECRET_EDGES = [
    (12, 24, 'H', 'secret',
     'DMG p.94: area 3 "appears to be a dead end"; secret door in the south '
     'wall, 8.5ft wide, 10ft above the floor, swings inward (east)'),
]

# Node graph read from the key text ONLY -- never from the map.
# (from, to, kind, note)
CONNECTIONS = [
    ('2', '1C', 'open',
     'door C moans: "the strong breeze which goes through area 2"'),
    ('2', '2A', 'open', 'location A: 8 rotting barrels, within the water room'),
    ('2', '2B', 'open', 'location B: pool holding the limed-over abbot skeleton'),
    ('3', '1', 'none',
     'area 3 has "roof supports similar to chamber 1" -- similarity, NOT a link'),
    ('3', '24', 'secret',
     'secret door in area 3 south wall; the vellum map shows the passage to 24 '
     'about 20ft south of it'),
    ('28', '29', 'secret',
     'the abbot\'s key makes the secret door at 28 open to the treasury (29)'),
    ('28', '30', 'secret',
     'without the key, 28 opens instead to the steps down to the caverns (30)'),
]

# Claims the text makes that the grid should corroborate.
ASSERTIONS = [
    ('3', 'dead_end',
     'area 3 is a dead end apart from its secret door and its entry corridor'),
    ('2', 'natural_cavern',
     'area 2 is a natural cavern, so its cells should read "mixed", not clean rectangles'),
    ('2', 'stream_north_south',
     'the stream "enters on the north from a passage which it fills entirely, '
     'and it exits to the south in the same manner"'),
]


# The stream, from the DMG key text (pdf p.97): "cold and fast flowing... from
# 5' to 7' wide and 3' to 5' deep. It enters on the north from a passage which
# it fills entirely, and it exits to the south in the same manner."
#
# It is water, not floor, and it is drawn as a winding band through the rock
# rather than as a corridor. Every one of these squares reads `sides=NSWE` --
# rock touching all four borders, because the thread never reaches an edge
# cleanly -- which is the opposite signature to a diagonal passage (rock on two
# ADJACENT sides). They are excluded from the walkable network; without that
# they show up as fourteen unreachable squares that are not rooms at all.
STREAM = [(0, 44), (1, 44), (2, 43), (4, 42), (5, 41), (6, 40), (6, 34),
          (4, 33), (5, 33), (2, 32), (3, 32), (1, 31), (0, 30)]


# The DMG's sample-dungeon text describes only areas 1-3, so there is just the
# one stated size to check against.
DIMENSIONS = {
    '1': 9,       # "a damp and vaulted chamber 30' square"
}
