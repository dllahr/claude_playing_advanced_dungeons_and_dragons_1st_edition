-- Dungeon map database
-- Coordinate system: x increases EAST, y increases NORTH. Origin (0,0) at the
-- south-west corner of the map sheet. One cell = one 10' x 10' graph square.
--
-- Edges are stored ONCE, canonically:
--   orient 'V'  = vertical edge on the EAST side of cell (x,y); separates (x,y) from (x+1,y)
--   orient 'H'  = horizontal edge on the NORTH side of cell (x,y); separates (x,y) from (x,y+1)
-- This avoids double-counting. The cell<->edge relation is a VIEW, not a table,
-- so it can never drift out of sync with the edges.

DROP VIEW  IF EXISTS cell_edges;
DROP VIEW  IF EXISTS low_confidence;
DROP TABLE IF EXISTS connections;
DROP TABLE IF EXISTS edges;
DROP TABLE IF EXISTS cells;
DROP TABLE IF EXISTS room_labels;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS levels;

-- The render settings are stored, not just described. Every tool that reopens
-- the page (markers.py, highlight.py, review.py) must reproduce the SAME grid
-- the database was built on, and the settings are map-specific: B1 needs the
-- red channel and a -0.37 degree deskew. A tool that re-renders with defaults
-- silently lands on a grid offset by up to a quarter of a square, which puts
-- door markers on the wrong edges.
CREATE TABLE levels (
    level      INTEGER PRIMARY KEY,        -- 1 = upper, 2 = lower
    name       TEXT NOT NULL,
    source     TEXT,                       -- which pdf page the map is on
    pdf        TEXT,
    page       INTEGER,
    dpi        INTEGER,
    channel    TEXT,                       -- how colour was collapsed to grey
    deskew_deg REAL,                       -- rotation applied, degrees
    notes      TEXT
);

CREATE TABLE rooms (
    level      INTEGER NOT NULL,
    number     TEXT NOT NULL,              -- '1', '31', 'a' for lettered pools, etc.
    name       TEXT,
    -- cell the printed label sits in. This is an ANCHOR, not the room's extent:
    -- on these maps rooms and corridors are both plain white, so the boundary
    -- between them is a reading of the key text, not a drawn feature.
    anchor_x   INTEGER,
    anchor_y   INTEGER,
    -- how many squares the extent covers, from extents.py. An anchor says
    -- where the label is printed; this says how big the room is.
    extent_sq  INTEGER,
    text_ref   TEXT,                       -- where the key text lives
    notes      TEXT,
    -- Area-level play state: 'cleared', 'looted', 'occupied', 'burned'.
    -- Replayed from campaign/world_changes.tsv; see edges.state on why it is
    -- unconstrained.
    state      TEXT,
    state_note TEXT,
    confidence INTEGER NOT NULL DEFAULT 5 CHECK (confidence BETWEEN 1 AND 10),
    PRIMARY KEY (level, number)
);

-- Every printed instance of an area's label. An area may be labelled in more
-- than one square: because the label straddles a boundary (12 of B1's 37 do),
-- or because the same keyed area is printed in several places (B1's area 1
-- appears six times, area 35 five). `rooms` keeps one canonical anchor; this
-- keeps them all, which is what lets every label be shielded from the rock
-- mask -- an unshielded numeral bridges into the wall and fabricates one.
CREATE TABLE room_labels (
    level      INTEGER NOT NULL,
    number     TEXT NOT NULL,
    x          INTEGER NOT NULL,
    y          INTEGER NOT NULL,
    source     TEXT,                       -- 'human' | 'ocr'
    confidence INTEGER NOT NULL DEFAULT 5 CHECK (confidence BETWEEN 1 AND 10),
    PRIMARY KEY (level, number, x, y)
);

CREATE TABLE cells (
    level      INTEGER NOT NULL,
    x          INTEGER NOT NULL,
    y          INTEGER NOT NULL,
    -- 'mixed' = rock covers part of the square but not all of it: a diagonal
    -- passage, a cave wall, an irregular chamber edge. Passable in principle,
    -- but the 10' grid cannot express it exactly, so these always carry low
    -- confidence and are the first thing to review by eye.
    terrain    TEXT NOT NULL DEFAULT 'unknown'
               CHECK (terrain IN ('open','solid','mixed','unknown')),
    room       TEXT,                       -- room number this cell belongs to, if any
    feature    TEXT,                       -- 'stairs_up','stairs_down','pit','statue','pool','water', etc.
    -- Sub-grid geometry the 10' square cannot express on its own.
    -- 'diagonal': a 45-degree passage crosses this square. Where such a
    -- passage is full width it also clips the neighbouring squares, so the
    -- chain is orthogonally contiguous and needs nothing special. Where it is
    -- HALF width it connects only at the corner -- the squares that would
    -- bridge it orthogonally contain no floor at all, so marking them walkable
    -- would invent floor that is not on the page. Reachability therefore
    -- allows a corner step between two cells that both carry 'diagonal'.
    passage    TEXT CHECK (passage IN ('diagonal','half_width','diagonal_half')),
    width_ft   INTEGER,                    -- corridor width where not the full 10'
    notes      TEXT,
    -- Has the PARTY seen this square? Kept separate from what is actually
    -- there, because describing geography the party has not verified is the
    -- specific mistake this whole database exists to prevent. DM-side only.
    seen       INTEGER NOT NULL DEFAULT 0,
    -- What the PARTY has DONE to this square: 'burned', 'flooded', 'blocked',
    -- 'pit_sprung', 'searched', 'cleared'. See edges.state for why there is no
    -- CHECK constraint here, and campaign/world_changes.tsv for the log these
    -- are replayed from -- a rebuild wipes them, tools/world.py puts them back.
    state      TEXT,
    state_note TEXT,
    confidence INTEGER NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 1 AND 10),
    PRIMARY KEY (level, x, y)
);

CREATE TABLE edges (
    level      INTEGER NOT NULL,
    x          INTEGER NOT NULL,
    y          INTEGER NOT NULL,
    orient     TEXT NOT NULL CHECK (orient IN ('V','H')),
    kind       TEXT NOT NULL DEFAULT 'unknown'
               CHECK (kind IN ('unknown','open','wall','door','secret','concealed',
                               'trap_door','secret_trap_door','one_way','false_door','stairs',
                               'archway','portcullis')),
    -- for doors: which way the leaf swings, expressed as the compass direction
    -- it opens TOWARD. NULL if not a door or not yet known.
    opens_toward TEXT CHECK (opens_toward IN ('N','S','E','W')),
    -- for one-way doors: the side it can be operated FROM
    operable_from TEXT CHECK (operable_from IN ('N','S','E','W')),
    locked     INTEGER,                    -- 1/0/NULL unknown
    notes      TEXT,
    seen       INTEGER NOT NULL DEFAULT 0,
    -- What the PARTY has DONE to this boundary, as distinct from what is
    -- printed on the page: 'spiked_open', 'spiked_shut', 'wedged', 'broken',
    -- 'barred', 'locked', 'unlocked', 'stuck', 'open', 'closed'.
    --
    -- `kind` stays what the map says -- a spiked-open secret door is still a
    -- secret door -- so the two must not be conflated.
    --
    -- DELIBERATELY NO CHECK CONSTRAINT. The edge-kind CHECK above shipped
    -- without 'concealed' and 'trap_door' and rejected correct data mid-run;
    -- that was found by the tests, but the same failure at the table during
    -- play would stop the game. A state nobody anticipated must degrade to a
    -- warning, not an exception, so tools/world.py validates against a known
    -- list and warns. Legal values are documented, not enforced.
    state      TEXT,
    state_note TEXT,
    confidence INTEGER NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 1 AND 10),
    PRIMARY KEY (level, x, y, orient)
);

-- Room-level node graph, built from the KEY TEXT independently of the grid.
-- Reconciling this against the grid is how we catch transcription errors.
CREATE TABLE connections (
    level        INTEGER NOT NULL,
    from_room    TEXT NOT NULL,
    to_room      TEXT NOT NULL,
    kind         TEXT,                     -- 'door','secret','open','stairs', ...
    distance_ft  INTEGER,
    source       TEXT NOT NULL,            -- 'text' | 'grid' | 'both'
    notes        TEXT,
    confidence   INTEGER NOT NULL DEFAULT 5 CHECK (confidence BETWEEN 1 AND 10),
    PRIMARY KEY (level, from_room, to_room, kind)
);

-- Which two cells each edge separates. Computed, never stored.
CREATE VIEW cell_edges AS
    SELECT level, x, y, orient, kind, confidence,
           x                                AS ax,
           y                                AS ay,
           CASE orient WHEN 'V' THEN x+1 ELSE x   END AS bx,
           CASE orient WHEN 'V' THEN y   ELSE y+1 END AS by
    FROM edges;

-- Everything we are least sure about, worst first.
CREATE VIEW low_confidence AS
    SELECT 'cell' AS what, level, x, y, NULL AS orient, terrain AS detail, confidence, notes
      FROM cells
    UNION ALL
    SELECT 'edge', level, x, y, orient, kind, confidence, notes
      FROM edges
    UNION ALL
    SELECT 'conn', level, NULL, NULL, NULL, from_room || '->' || to_room, confidence, notes
      FROM connections
    ORDER BY confidence ASC, level, y, x;
