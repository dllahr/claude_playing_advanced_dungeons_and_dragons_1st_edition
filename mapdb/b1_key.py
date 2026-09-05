#!/usr/bin/env python3
"""Hand-verified key for B1, Quasqueton upper level.

Label positions come from the table under dlwork/archive/, which is the source
of record; this module reads it rather than copying from it.

B1's labelling is more awkward than the DMG's: twelve of the thirty-seven areas
have a label straddling two squares, and two areas are printed repeatedly --
area 1 six times (the entry alcoves flanking the entrance corridor) and area 35
five times. Every one of those squares needs shielding from the rock mask, so
ROOMS maps each area to the full list.

CONNECTIONS is nearly empty, and that is a finding rather than an omission.
Unlike the DMG -- whose text states its secret-door topology, and where that
statement caught a real extraction error -- B1's descriptions are about
contents. Of roughly fifty cross-references in the level-1 text, only three say
anything about where an area leads; the rest are of the form "resembling the bed
in room 5". B1's topology therefore has to come from the map, which inverts the
two-independent-readings check: here the grid is the primary source and the text
corroborates only at those three points.
"""
import os

import label_file as _lf

LABELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                           'dlwork', 'archive',
                           '2026-08-24_b1_lv1_number_locations.txt')
ROOMS = _lf.load(LABELS_FILE)
TEXT_REF = 'B1 pdf pp.10-25 (ENCOUNTER AREAS)'

# Area names, read from the ENCOUNTER AREAS headings. Areas 15 and 16 share a
# single heading ("15 & 16. TELEPORTATION ROOMS"), which is why a regex looking
# for "16." alone finds only 35 of the 37.
NAMES = {'1': 'ALCOVES',
         '2': 'KITCHEN',
         '3': 'DINING ROOM',
         '4': 'LOUNGE',
         '5': "WIZARD'S CHAMBER", '6': 'CLOSET',
         '7': "WIZARD'S ANNEX", '8': "WIZARD'S WORKROOM", '9': "WIZARD'S LABORATORY", '10': 'STOREROOM',
         '11': 'SUPPLY ROOM',
         '12': 'LIBRARY',
         '13': 'IMPLEMENT ROOM',
         '14': 'AUXILIARY STOREROOM',
         '15': 'TELEPORTATION ROOM',
         '16': 'TELEPORTATION ROOM',
         '17': 'CHAR STORAGE CELLAR',
         '18': 'SMITHY',
         '19': 'ACCESS ROOM',
         '20': 'DEAD END ROOM',
         '21': 'MEETING ROOM',
         '22': 'GARDEN ROOM',
         '23': 'STORAGE ROOM',
         '24': "MISTRESS' CHAMBER", '25': "ROGAHN'S CHAMBER", '26': 'TROPHY ROOM',
         '27': 'THRONE ROOM',
         '28': 'WORSHIP AREA',
         '29': "CAPTAIN'S CHAMBER", '30': 'ACCESS ROOM',
         '31': 'ROOM OF POOLS',
         '32': "ADVISOR'S CHAMBER", '33': 'BARRACKS',
         '34': 'ARMORY',
         '35': 'GUEST CHAMBER',
         '36': 'UTILITY ROOM',
         '37': 'RECREATION ROOM'}

# The only three statements in the level-1 text that assert topology.
CONNECTIONS = [
    ('8', '9', 'secret',
     "workroom and laboratory 'are located adjacent to each other, with a "
     "limited access by secret doors'"),
    ('30', '38', 'stairs',
     'a descending stairway that "leads down and directly into room 38 on the '
     'lower level"'),
    ('36', '50', 'trap_door',
     'a covered trap; the bottom, 40ft below, is a pool in room 50 of the '
     'lower level'),
]

# Interior features the module text describes, which the extractor reads as
# walls because they are drawn as dotted rectangles the scan has merged. See
# lab_notebook.md: this is information the image does not carry.
FEATURES = {
    (16, 32): 'mats', (17, 32): 'mats', (18, 32): 'mats',
    (16, 33): 'mats', (17, 33): 'mats', (18, 33): 'mats',
}

# Sizes the descriptions state for the ROOM (not for its contents), in squares.
# Only four of the thirty-five level-1 areas give one, so this is a thin but
# genuine cross-check: the text is an independent reading of the same room, and
# a disagreement means the walls, the label or the extent is wrong.
#
# Area 22 is included but suspect: the Garden Room is described as the former
# "showplace of the entire stronghold", so its 10' x 20' is more likely an
# outcropping than the chamber. Left in deliberately -- if the extent disagrees,
# that tells us which reading is at fault.
DIMENSIONS = {
    '9': 15,      # "50' by 30'"
    '17': 4,      # "This 20' by 20' room"
    # '18' omitted: its "20' by 20'" describes only the square eastern section.
    #   Area 18 is L-shaped -- a 2x2 joined to a 3x2 -- and is 10 squares, so
    #   the stated figure would fire a permanent false disagreement.
    # '22' omitted: the Garden Room's "10' x 20'" is an outcropping inside it,
    #   not the chamber. Confirmed by the extent, which is 16 squares.
}

# Extents confirmed square by square against the sheet. Stronger than a size:
# a count can agree by accident, a set cannot, and a mismatch names the squares.
VERIFIED_EXTENTS = {
    '9': [(x, y) for x in range(11, 16) for y in range(26, 29)],
    '17': [(2, 21), (3, 21), (2, 20), (3, 20)],
    '18': [(5, 20), (6, 20), (5, 19), (6, 19),
           (3, 18), (4, 18), (5, 18), (3, 17), (4, 17), (5, 17)],
}


# Which areas the MODULE TEXT says have a secret or false door. This is a third
# independent reading, and on B1 it is the only one that works: the image
# detector proposes no glyph for some of them (area 9's read as a plain wall at
# thickness 14), and reachability cannot corroborate any of them because every
# one of these rooms has another way in, so nothing is ever sealed.
#
# Treat this as the inventory to check against, not as placed geometry -- the
# text says WHICH rooms, rarely which wall.
# Located and confirmed against the sheet:
#   10 -> edge (8,25,V)    24 -> edge (33,6,H)    32 -> edge (30,19,V)
#   9  -> edge (14,28,H)   25 -> three markers, see b1_corrections.tsv
# Still unlocated: area 8's half of the 8<->9 pair.
SECRET_DOOR_AREAS = {
    '8': 'workroom and laboratory joined "by secret doors" (plural)',
    '9': 'ditto; one confirmed at (14,28,H)',
    '10': 'the storeroom is "hidden by a secret door"',
    '24': '"on the north wall just to the west of the secret door"',
    '25': '"opposite the secret door on the west wall is a bed"',
    '32': 'access "only via a secret door on its west wall" to the Room of Pools',
}
FALSE_DOOR_AREAS = {
    '17': 'false door on the west wall; "cannot be opened"',
    '35': 'false door on the eastern wall of the middle chamber',
    '36': 'false door on the north wall, part of the PIT TRAP',
}
