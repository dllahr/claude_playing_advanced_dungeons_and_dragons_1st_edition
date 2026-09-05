#!/usr/bin/env python3
"""Hand-verified key for B1, Quasqueton LOWER level (pdf page index 2).

Label positions come from the table under dlwork/archive/, which is the source
of record; this module reads it rather than copying from it.

WHY THIS SHEET IS NOT THE UPPER LEVEL WITH DIFFERENT NUMBERS
------------------------------------------------------------
The upper level is a stronghold: rectilinear rooms, drawn wall bars, 106 door
glyphs. The lower level is a CAVE COMPLEX. The module says so itself:

    "The lower level of the complex is rough and unfinished. The walls are
     irregular and coarse, not at all like the more finished walls of the
     level above (except for the two rooms on this level which are more like
     those in the upper portion...). The corridors are roughly 10' wide, and
     they are irregular and rough, making mapping difficult."
                                             -- B1 pdf p.23, KEY TO THE LOWER LEVEL

Three consequences for the extraction, all measured:

1. There are only FOUR door glyphs on the whole sheet, and two of them are
   drawn at 45 degrees because the passage they close is diagonal. On level 1
   the danger was FABRICATED doors (60 of 106 wrong); here the danger is the
   opposite -- almost every boundary is rock-against-floor and the door
   inventory is tiny, so a single missed door seals a wing of the level.
2. The floor/rock boundary almost never runs along a grid line. 433 of the
   1,728 squares classify `mixed` (25%, against level 1's 12%), and the
   45-degree-partition problem of DIAGONAL_WALLS.md is the NORMAL case here,
   not the exception.
3. The sheet's own legend is DIFFERENT: it prints POOL, DEPRESSION and WEBS
   and nothing else. The door/secret-door/stairs/statue/pit symbols are the
   ones defined on the UPPER level sheet's legend (pdf page index 1) and are
   used here without being re-printed. Read that legend, not this page's.

CONNECTIONS is again nearly empty, and again that is a finding. B1's room
descriptions are about contents, not topology. Six statements on this level say
anything about where an area leads, and they are all below. So, as on level 1,
the grid is the primary reading and the text corroborates at a handful of
points -- with the important exception of the SECRET doors, which the image
cannot carry at all.
"""
import os

import label_file as _lf

LABELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                           'dlwork', 'archive',
                           '2026-09-03_b1_lv2_number_locations.txt')
ROOMS = _lf.load(LABELS_FILE)
TEXT_REF = 'B1 pdf pp.23-26 (KEY TO THE LOWER LEVEL)'

# Area names, read from the ENCOUNTER AREAS headings on pdf pp.23-26.
# NOTE the module's own typo: area 55's heading is printed "35. EXIT CAVE".
# It is the fifty-fifth area -- it sits between 54 and 56 in the key and the
# map prints "55" -- so it is recorded here as 55.
NAMES = {'38': 'ACCESS ROOM',
         '39': 'MUSEUM',
         '40': 'SECRET CAVERN',
         '41': 'CAVERN',
         '42': 'WEBBED CAVE',
         '43': 'CAVERN',
         '44': 'CAVERN',
         '45': 'CAVERN OF THE MYSTICAL STONE',
         '46': 'SUNKEN CAVERN',
         '47': 'CAVERN',
         '48': 'ARENA CAVERN',
         '49': 'PHOSPHORESCENT CAVE',
         '50': 'WATER PIT',
         '51': 'SIDE CAVERN',
         '52': 'RAISED CAVERN',
         '53': 'GRAND CAVERN OF THE BATS',
         '54': 'TREASURE CAVE',
         '55': 'EXIT CAVE',
         '56': 'CAVERN OF THE STATUE'}

# Every statement in the lower-level text that asserts topology. Built from the
# TEXT ALONE, before the grid was consulted, so that build.py's cross-check is
# a genuine second reading.
#
# '30' and '36' are UPPER-level areas and have no anchor here, so build.verify
# reports "no anchor for one end" for those two rows. That is correct and
# deliberate: they are the level's two connections to level 1 and they belong
# in the record.
CONNECTIONS = [
    ('30', '38', 'stairs',
     'area 30 (upper) has "a descending stairway that leads down and directly '
     'into room 38 on the lower level"'),
    ('36', '50', 'trap_door',
     'area 36 (upper) is a covered trap; the bottom, 40 ft below, is the pool '
     'in room 50'),
    ('53', '52', 'stairs',
     '53: "steps to the southeast lead up to room 52"; 52: "off the southeast '
     'corner of the grand cavern, is accessible by climbing four upward steps"'),
    ('53', '54', 'secret',
     '53 has "a secondary entrance/exit ... via a secret door to the west"; '
     '54 is "a secret room, itself opening to a corridor shielded by secret '
     'doors on either end". NOTE: this row asserts only that BOTH are reached '
     'through secret doors, not that they are adjacent -- the text never says '
     'what lies west of 53. It is here to be CONTRADICTED if the grid '
     'disagrees.'),
    ('55', 'outside', 'one_way',
     '55: "a secret one-way passage out of the stronghold is hidden in the '
     'northeast corner of the cave"; egress only, "never entrance"'),
    ('45', '42', 'none',
     'the mystical stone teleports a character to the webbed cave on a roll of '
     '1 -- magical, NOT a passage; kind "none" so verify() skips it'),
]

# --------------------------------------------------------------- secret doors
#
# THE IMAGE CANNOT CARRY THESE. B1's lower level draws a secret door as a
# printed `S` glyph on the annotation layer, and the module says outright that
# they are "either rock or disguised by rock so as to appear unnoticeable" --
# i.e. there is deliberately nothing structural to find. Every one below was
# located by reading the module text FIRST and then finding the `S` on a
# grid-annotated render, in that order.
#
# Four `S` glyphs are printed on the sheet. They are listed with the boundary
# each annotates; the reasoning for each boundary is in the report.
SECRET_DOOR_AREAS = {
    '40': '"SECRET CAVERN"; the `S` is printed at (30.6, 6.7), on the neck '
          'between the cavern and the corridor north-east of it',
    '53': '"A secondary entrance/exit is via a secret door to the west" -- the '
          'EAST end of the hidden corridor; `S` printed at (14.0, 39.4)',
    '54': '"This secret room, itself opening to a corridor shielded by secret '
          'doors on either end" -- the room\'s own door; `S` printed at '
          '(9.75, 36.4)',
    '55': '"a secret one-way passage out of the stronghold is hidden in the '
          'northeast corner of the cave" -- egress to the OUTSIDE, drawn as '
          'the thread at (11,44) running north into the vegetation, with no '
          '`S` printed on it. Area 55 is ALSO the west end of the hidden '
          'corridor; that `S` is printed at (7.94, 36.4)',
}

# THE HIDDEN CORRIDOR -- the level's one real piece of topology, and the three
# `S` glyphs in the north-west quadrant are one structure, not three.
#
# Reading the three sentences together:
#
#   54: "This SECRET ROOM, itself opening to a CORRIDOR SHIELDED BY SECRET
#        DOORS ON EITHER END"
#   53: "A secondary entrance/exit is via a SECRET DOOR TO THE WEST"
#   55: the EXIT CAVE, whose own secret is the one-way way out of the mountain
#
# gives one corridor running east from area 55 at y=36, past the head of area
# 54's descent, on through the cave at (10,36)-(12,37) to (13,38), and into
# area 53. Its two ends are S1 and S3; area 54 hangs off it through S2, which
# is the "secret room's" own door. Every one of the three sentences is then
# satisfied, and all three glyphs are used.
#
# HOW THE GLYPHS SIT ON THE GRID, because this cost the most work on this sheet
# and the answer is not the obvious one. Each `S` is drawn on a PLUG OF ROCK
# INSIDE a square, not on a grid line -- the module says so outright: "the
# secret doors are either rock or disguised by rock so as to appear
# unnoticeable". Sampling the rock mask at 16 points per square:
#
#   (9,36)  rows 1-9 are the corridor floor, row 9 is solid rock across the
#           square, rows 10-15 are the head of the descent to area 54. The `S`
#           is drawn over that row-9 bar. The passage it blocks runs N-S, so on
#           the grid the door has to sit on the square's SOUTH boundary:
#           (9,35,H).
#   (13,39) rows 1-2 are area 53's floor reaching west, ROW 3 IS SOLID ROCK
#           ACROSS THE SQUARE, rows 4-8 are the corridor heading south-west.
#           The `S` is drawn on that bar. Same argument: (13,38,H).
#   (7,36)  here the rock genuinely spans the grid line -- no row of the square
#           has floor crossing x=8 -- so this one IS a boundary: (7,36,V).
#
# Putting the first two on the boundary the glyph LOOKS nearest -- (9,36,V) and
# (13,39,V) -- is wrong and is not a small error: it leaves both doors
# bypassable, because the cave floor runs round them through the corner of the
# next square. Sealing all three then changes reachability by ZERO squares,
# which is how the mistake was caught.
SECRET_EDGES = [
    (7, 36, 'V', 'secret',
     'S1: WEST end of the hidden corridor, out of area 55 (B1 p.25). Printed '
     'S at (7.94, 36.4). The only one of the three that sits on a grid line: '
     'no row of (7,36) has floor crossing x=8.'),
    (9, 35, 'H', 'secret',
     "S2: area 54's own door (B1 p.25, \"this secret room\"). Printed S at "
     '(9.75, 36.4) on a rock bar INSIDE (9,36) that separates the corridor '
     'from the head of the descent to 54.'),
    (13, 38, 'H', 'secret',
     'S3: EAST end of the hidden corridor, into area 53 (B1 p.24, "a secondary '
     'entrance/exit ... via a secret door to the west"). Printed S at '
     '(14.0, 39.4) on a rock bar INSIDE (13,39).'),
    (30, 6, 'H', 'secret',
     'secret door into area 40, SECRET CAVERN (B1 p.23): printed S at '
     '(30.6, 6.7), on the pinch between (30,6) and (30,7). The one secret '
     'door the image and the text agree on without argument, and the only one '
     'the raw extraction already sealed a region behind.'),
]

# --------------------------------------------------------------- features
#
# Symbols read off the sheet against the UPPER level's printed legend, plus the
# two the lower sheet's own legend defines (POOL, DEPRESSION; WEBS is drawn but
# falls outside any square cleanly). Each is named in the module text as well,
# which is why they are here rather than in a corrections file.
FEATURES = {
    (20, 14): 'stairs',      # the stairway up to area 30 on the upper level;
                             # tapering hatching in a 1x1 alcove north of 38
    (30, 36): 'stairs',      # "four upward steps" from 53 up to 52 -- four
                             # even strokes, the legend's STAIRS UP
    (8, 22): 'pit',          # "a large covered pit at the intersection of
                             # three corridors", 12 ft across; drawn as a
                             # circled X centred on the (7,23)|(8,23) corner
    (3, 19): 'statue',       # 56: "a solitary stone figure ... in the southern
                             # end of this cavern"
    (7, 26): 'statue',       # 54: one of the two "short human statues"
    (9, 29): 'statue',       # 54: the other
    (29, 34): 'pool',        # 50: "The pool is about 20' across"
    (29, 33): 'pool',
}

# NOT placed, deliberately -- the two features the text describes and the sheet
# does not draw anywhere I could find:
#
#   WEBS. The lower sheet's own legend defines a WEBS symbol, and area 42 is
#   the WEBBED CAVE whose "entrance ... is covered with silky but sticky webs,
#   which must be cut or burned through". I could not find the glyph printed
#   anywhere on the sheet; area 42's approach at (15,6)-(15,7) carries nothing.
#   So the web is a TEXT fact and the square it sits on is a judgement. Left
#   unplaced rather than guessed.
#
#   The area 55 ONE-WAY SECRET EXIT to the outside world. The passage is drawn
#   -- the thread at (11,44) running north out of the frame into the
#   vegetation -- but no `S` and no arrow is printed on it, and the squares
#   beyond the frame are `outside`, so there is nothing to connect it to. It is
#   in CONNECTIONS as ('55','outside','one_way') and nowhere else.

# --------------------------------------------------------------- dimensions
#
# DELIBERATELY EMPTY, and that is itself the finding: the lower-level text
# states no room dimension anywhere. The only measurements it gives are of
# CONTENTS or of vertical relief -- the pool "about 20' across", the pit "about
# 12' across and 10' deep", area 48's centre "sunken about 15'", 53's ceiling
# "almost 60' above", 52's "only 5'" headroom. `stated_squares()` would take
# the first of those and fire a permanent false disagreement, exactly as area
# 22's outcropping did on level 1.
#
# So the extent cross-check -- one of the three independent checks in
# CHECKLIST.md section 7 -- IS NOT AVAILABLE ON THIS LEVEL. Reachability and
# the text sweep have to carry the whole load.
DIMENSIONS = {}

# Extents confirmed square by square against the sheet. Only rooms with a wall
# that actually runs along the grid qualify; a cavern's outline does not, and
# claiming one would be inventing precision the map does not have.
VERIFIED_EXTENTS = {
    # 39, the MUSEUM: the one room on this level with four straight walls, all
    # four visible on the render, 4 squares by 2.
    '39': [(x, y) for x in range(26, 30) for y in range(10, 12)],
}
