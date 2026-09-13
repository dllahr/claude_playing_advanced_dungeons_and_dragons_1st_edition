# Diagonal walls — a design study

**Status.** Section 6's "what to build first" was implemented on 2026-08-29 and
nothing else was: `extract.diagonal_stat` / `side_classes` / `split_orient` /
`diagonal_suspect`, `mapdb/diagcheck.py`, `synth.diagonal_wall`,
`tests/test_diagonal_walls.py`, and one review step in `rebuild.sh`. The section 2
figures below were re-measured against that code and reproduce exactly, except
where noted in section 2.4. **The MODEL is unchanged and the rest of this
document remains a proposal** — no schema column, no half-cell nodes, no
automatic reclassification. **⚠ THE REST OF THIS SENTENCE WAS TRUE UNTIL
2026-09-06 AND IS NOT NOW: areas 10 and 11 WERE corrected in `781bac5`, from
the player's reading of the printed map. The note below is kept for the
reasoning, not for its conclusion.** No correction had been entered for areas
10 and
11. Both regression counts are unmoved: DMG 21 unreached of 641, B1 5 of 1,196.

Everything below was written before that, from scratch scripts run against a
read-only copy of the two databases and a fresh render of the two pages;
`rebuild.sh` was not run.

The problem, in one sentence: `extract.edge_stats` asks *"how much rock lies
along this grid boundary"*, and a wall drawn at 45 degrees answers *"none"*
while completely blocking passage.

Found in play on 2026-08-29 with the party standing in B1's area 34. See
`lab_notebook.md`, "The north-east quadrant: DIAGONAL WALLS defeat a
boundary-based model", for the incident; this file is the follow-up study it
asked for.

---

## 1. What is actually on the sheets

### 1.1 There are two drawing styles, and only one of them is dangerous

Both are 45-degree walls. They fail completely differently, and the distinction
runs through the whole of the rest of this document.

**(a) The face of a rock mass.** The wall is the hypotenuse of a filled black
region; beyond it is more rock. Cell `(25,25)`, on area 34's north-west wall,
rendered from the rock mask at 200 dpi (every second row, inset 0.12 as
`cell_stats` samples it):

```
###############################
###############################
##############################.
#############################..
##########################.....
#########################......
######################.........
####################...........
##################.............
################...............
##############.................
############...................
##########.....................
#########......................
######.........................
```

Rock 63% of the cell. The cells north and west of it measure **1.00** rock, so
`classify_edge` sees `solid` on one side and returns `('wall', 9)` without ever
consulting `thick` or `gap`. **This style works today.**

**(b) A thin partition between two open spaces.** The wall is a drawn band with
*floor on both sides*. Cell `(27,25)`, on area 34's south-east wall:

```
............................##
...........................###
.........................#####
.......................#######
.....................#########
...................#########..
.................#########....
...............#########......
.............#########........
..........##########..........
.........#########............
.......#########..............
.....#########................
...#########..................
.#########....................
```

Rock 27% of the cell. Every neighbour is open floor. **This style is invisible
to the edge model**, and is what leaked area 34 into the Room of Pools.

### 1.2 The partition is a normal-weight wall, measured perpendicular to itself

The player's description — *"the regular thickness but diagonal"* — is exactly
right. Perpendicular width, computed as (rock pixels in the cell) / (cell
diagonal length), over the twelve partition cells found on B1:

| | perpendicular width, px at 200 dpi |
|---|---|
| B1's diagonal partitions (n = 12) | min 5.6, **median 6.3**, max 9.0 |
| B1's genuine orthogonal walls (n = 545, `lab_notebook.md`) | p25 8, p50 8, p75 8 |
| B1's printed graph-paper rulings | 0 – 3 |

6.3 px against 8. These are walls drawn at the light end of the normal range,
not hairlines. **Nothing is wrong with the ink; the measurement axis is wrong.**

### 1.3 What `edge_stats` reports for them

The twelve partition cells sit on 47 distinct grid boundaries. Measured with
the pipeline's own `_edge`:

| | value |
|---|---|
| `thick` min / p25 / median / p75 / max | 0.0 / 2.0 / **2.0** / 3.3 / 20.0 |
| under `--t-thick 6.0` | **40 of 47** |
| classified `open` | **43 of 47** (3 `wall`, 1 `door`) |

Median 2.0 px is *dead centre of the printed-ruling band*. A wall of normal
weight, measured across a boundary it crosses obliquely, is indistinguishable
from graph paper.

This is why the lab notebook's instruction stands: **lowering `--t-thick` is not
the answer.** 6.0 separates rulings from walls across the whole sheet; these
edges are not walls-measured-thin, they are *not walls at all*. The wall is a
foot and a half away, inside the square.

### 1.4 They are all at 45 degrees

Principal-axis angle of the rock in each cell (second moments, dungeon axes,
0 = east–west, +45 = SW–NE):

| population | n | p10 | p50 | p90 |
|---|---|---|---|---|
| B1 partition cells, SW–NE | 11 | 38.9 | **44.3** | 47.8 |
| B1 partition cells, NW–SE | 5 | −49.4 | **−45.9** | −45.7 |
| DMG diagonal-corridor flanks | 3 | −50.2 | **−44.4** | −43.2 |

No other angle appears anywhere on either sheet. Both maps are drawn on
5-squares-per-inch graph paper and every non-orthogonal straight line on them is
a graph-paper diagonal. **Assuming 45 degrees is safe on these two sheets**; it
is an assumption to re-check on a new one, and the detector in §2 reports its
peak strength so a 30-degree wall would fail loudly rather than quietly.

The remaining non-orthogonal geometry on B1 is *curved*, not diagonal: the great
arch north of area 12, area 25's four-lobed outline, area 27's oval dais. Those
are a different problem and are out of scope here.

### 1.5 Census

Cells carrying a 45-degree wall, by style, over the whole of each sheet
(detector of §2.4 at peak ≥ 0.90, cells outside the drawn map frame excluded):

| | B1 level 1 (1,665 cells) | DMG sample (1,680 cells) |
|---|---|---|
| **partition style** (rock 15–45% of the cell) | **13** — 12 true + 1 mass face | **2** — both legend glyphs, 0 true |
| **mass-face style** (rock 45–90%) | 50 | 32 |
| cells classed `mixed` overall | 199 | 94 |

The 12 true B1 partitions belong to **three rooms**:

| structure | partition cells | what it is |
|---|---|---|
| **area 34**, ARMORY | (26,24) (27,25) (28,26) (29,27) | 20 ft wide diagonal chamber, SW–NE; NW wall is mass-face, SE wall is a partition against the Room of Pools |
| **area 10**, hidden storeroom | (5,24) (6,23) (7,22) — south wall; (5,25) (7,27) (8,28) — north wall | a chevron-shaped room; both arms are bounded by partitions |
| **area 11**, SUPPLY ROOM | (5,27) (6,28) | a 45-degree-rotated **diamond** room; its SE wall is a partition |

The 50 B1 mass-face cells are the north wall of the area-35 block (a sawtooth of
five triangular alcoves, ~20 cells at y = 41–42), area 34's NW wall (6 cells),
areas 10 and 11's outer walls (12 cells), three chamfered corners in the area-35
block, and about six false hits where a *curve* happens to run at 45 degrees
across a cell (the arch at (7,35)/(12,35), area 25's lobes at (34,15)/(34,13)/
(31,11)/(34,11)).

### 1.6 Why the DMG never showed this and B1 did

**Every diagonal on the DMG sheet is the flank of a diagonal corridor cut
through solid rock.** The long southern diagonals, the (22,7)–(23,9) run, area
30's diagonal staircase, area 28's chamfered corner — in each case the far side
of the wall is rock, so the neighbouring cells read `solid`, so `classify_edge`
short-circuits to `('wall', 9)` on terrain alone. The DMG has **zero** diagonal
partitions. The two cells the detector flags are `(5,27)`, area 30's diagonal
stair hatching, and `(23,18)`, the boxed-`X` trap-door glyph — both legend
symbols the existing `is_stairs` / hole tests already own.

B1 is a *stronghold*, not a cave complex. Its diagonal chambers are rooms with
other rooms on the far side of the wall, which is exactly the configuration the
edge model cannot express.

**This is the general rule and it is worth stating on its own line:**

> A diagonal wall is invisible to a boundary-based model precisely when the
> space on the far side of it is FLOOR rather than ROCK.

That predicts where the problem will appear on any new sheet, and it says the
DMG was never a test of this at all.

### 1.7 The DMG has the *dual* fault, and it costs 11 squares

The same modelling gap bites the DMG in the opposite direction: a **door drawn
on a diagonal**, which no grid edge can carry.

Area 28's south-east corner is chamfered at 45 degrees and the chamfer carries a
printed `S` rotated to match — the secret door into the area-29 treasury.
`README.md` records the consequence: 11 of the DMG's 21 unreached squares.
Measured now:

```
(5,24,V)  kind=wall  conf=3  thick=8  hole=25     <- the grid edge the chamfer crosses
```

Flooding the live `dmg.sqlite` with that single edge changed to `secret`:

```
before  UNREACHED 24        (my flood; dmap's own count is 21, it also allows the corner step)
after   UNREACHED 13
recovered: (6,24) (7,24) (8,24) (8,23) (9,23) (8,22) (9,22) (9,21)=area 29 (10,21) (9,20) (10,20)
```

**All eleven.** This matters for §5: it is a one-line correction that would move
a documented regression count.

---

## 2. Detection

Ground truth for this section is the twelve cells adjudicated TRUE by rendering
3×3-cell crops of the printed page and looking at them, plus seven adjudicated
FALSE. Precision below is scored against **all 1,358 in-frame cells**, not
against those nineteen, so a detector that fires anywhere else on the sheet is
charged for it.

The seven known false positives, all confirmed by page render:

| cell | what it really is |
|---|---|
| (12,4) | a rotated crate in area 2's storeroom |
| (22,19) | a small drawn table |
| (6,20) | a drawn object beside area 10's wall |
| (17,21) | rods and dots in a workshop |
| (12,22) | a drawn tool lying at exactly 45 degrees |
| (33,23) | two drawn containers in area 33 |
| (31,27) | the circled pool marker `n` plus the wall east of it |

That list is the warning the brief asked for. **B1 draws furniture at every
angle, and `doorcheck.py`'s history says ad-hoc shape tests lose to it.** Any
detector here must be scored against furnished rooms, not against the diagonal
corridors it was designed on.

### 2.1 Second-moment / principal-axis analysis

Orientation and elongation of the cell's rock mask. Fires on 40 ≤ |angle| ≤ 50,
elongation ≥ 3, rock fraction 0.15–0.45.

**Precision 1.00, recall 0.83** (10 of 12; misses (6,28) and (5,25), where a
piece of drawn furniture sits in the same cell as the wall and rotates the
principal axis off 45).

Clean, but the moment is a *single* summary of the whole cell, so any second
object in the cell corrupts it — which is the failure mode B1 is full of.

### 2.2 Corner occupancy

Rock fraction in each of the four corner quadrants (0.33 of a side), thresholded
at 0.40. A partition running SW–NE occupies the SW and NE quadrants and leaves
NW and SE clear.

**Precision 0.69, recall 0.92.** Five false positives, all furniture: (33,23)
(12,22) (17,21) (6,20) (22,19).

Cheap and interpretable, but it cannot tell a diagonal **wall** from a diagonal
**corridor**: rock in the NW and SE quadrants is *either* a NW–SE wall *or* the
flanks of a SW–NE corridor. Only the rock fraction separates them (partition
0.27–0.42, corridor flanks 0.5–0.7), and that is a threshold on a continuum. On
the DMG it fires on (22,7), (23,8), (7,28) — all diagonal corridors and stairs,
i.e. 3 false positives out of 3 hits.

### 2.3 Topological side-connectivity split

Ask the question the reachability graph actually needs: **which of the cell's
four sides are mutually reachable through the cell's own floor?**

- ordinary open cell → `{N,S,E,W}`
- solid → `{}`
- a wall on the SW–NE diagonal → `{N,W}` and `{S,E}` — two classes
- a wall on the NW–SE diagonal → `{N,E}` and `{S,W}`
- a corner wedge (mass face) → one class, e.g. `{S,E}`

Implementation notes that cost two failed attempts to find:

- Label the *floor* with 4-connectivity, and **dilate the rock by one pixel
  first**. A band drawn corner to corner leaves a one-pixel leak at the cell
  corner and a 4-connected label walks straight through it. Without the
  dilation all twelve partitions came back as a single floor component.
- Measure side contact as **the fraction of the shared border the component
  reaches**, with the same 0.25 floor `classify_edge` already uses for `gap` —
  not "does it touch an 18% border band". A diagonal band exits through the cell
  *corners*, so the far component clips a couple of pixels of every band and
  every component read as touching all four sides.

**Precision 0.85, recall 0.92.** Two false positives: (12,4), a rotated crate;
(31,27), a circled letter beside a wall. On the DMG it returns **zero** hits,
correctly — a diagonal corridor's floor is one component touching all four
sides, so the test distinguishes corridor from wall where corner occupancy
cannot.

### 2.4 Two-angle Radon — recommended

Project the cell's rock mask along the two 45-degree families (constant
`row+col` and constant `col−row`) and take the strongest single line, normalised
by the cell side. A rock band drawn corner to corner projects onto **one**
diagonal index for its whole length, so the peak reaches 1.0. Nothing else on a
line-art dungeon map does: furniture is short, curved or off-45, and an
orthogonal wall projects onto the *orthogonal* axis, not a diagonal one.

This is a Hough/Radon transform restricted to the two angles that exist on the
sheet. The general form is not worth it — a full `hough_line` over 180 angles on
1,665 cells costs 100× more and would have to be told to ignore the 179 angles
the map never uses.

Whole-sheet distribution of the peak, over B1 cells with rock < 90%:

| population | n | peak / cell side |
|---|---|---|
| the 12 true partitions | 12 | **0.90 – 1.00** |
| the 7 adjudicated false positives | 7 | 0.27 – 0.83 |
| random furnished cells, rock 10–45% | 60 | p50 0.23, p90 0.40, **max 0.50** |

A real gap, not a tuned threshold: everything true is ≥ 0.90, and only one
control cell in 67 exceeds 0.63 — (12,22), a drawn tool that genuinely does lie
at 45 degrees.

> **Re-measured 2026-08-29 against the implementation.** The control row is the
> one number here that was a sampling artefact: over the WHOLE control pool
> (every in-frame cell at rock 10–45% outside the adjudicated nineteen, n = 295)
> the peak is p50 **0.23** and p90 **0.50** as stated, but **8** cells exceed
> 0.63 rather than one, and a redrawn sample of 60 tops out at 0.61–0.87
> depending on the draw, not at 0.50. The gap that matters survives intact:
> **exactly one** cell in the 295 reaches 0.90, and it is (24,41), the mass-face
> wall already accounted for as the single false positive. The seven adjudicated
> false positives measure 0.33–0.83 ungated, against 0.27–0.83 as recorded.
> Everything else in section 2.6 reproduces to the cell, including the
> conjunction dropping (5,27).

**Precision 0.92, recall 1.00.** Its single "false" positive, (24,41), is
*not* furniture: it is a genuine 45-degree wall on the sawtooth, of the mass-face
style, whose rock fraction (0.43) happens to fall inside the partition band.

The transform also returns two things the other tests do not, and both are
needed downstream: the **orientation** (which family peaked) and the **offset**
(which diagonal index peaked, i.e. where inside the cell the wall lies — what
you need to decide which side a half-cell belongs to, or to place a door on the
diagonal, as the DMG's area 28 requires).

### 2.5 Template correlation — do not

`lab_notebook.md` already records two attempts to match B1's door glyphs against
legend templates: the full symbol capped at 0.53 across all 3,360 edges because
the template carried surrounding wall that varies everywhere, and a tight crop
with a learned negative class claimed 388 secret doors on a level that has about
a dozen. A diagonal wall is *worse* material for a template than a door glyph:
it has no fixed extent, it is a straight line of arbitrary length, and its
appearance in a cell depends entirely on where the cell boundary happens to cut
it. There is nothing to correlate against. **Skip it.**

### 2.6 Head to head

B1 level 1, 1,665 cells, 307 excluded as outside the drawn frame:

| detector | hits | TP | FP | precision | recall |
|---|---|---|---|---|---|
| second moment (40–50°, elong ≥ 3) | 10 | 10 | 0 | 1.00 | 0.83 |
| corner occupancy | 16 | 11 | 5 | 0.69 | 0.92 |
| topological side split | 13 | 11 | 2 | 0.85 | 0.92 |
| **two-angle Radon + rock-fraction band** | 13 | 12 | 1 | 0.92 | **1.00** |
| corner **and** topology | 10 | 10 | 0 | 1.00 | 0.83 |
| **Radon and topology** | 11 | 11 | 0 | **1.00** | 0.92 |
| Radon **or** topology | 15 | 12 | 3 | 0.80 | 1.00 |

DMG sample dungeon, same code, no retuning: Radon 2 hits (both legend glyphs),
topology 0, conjunction **0**. Correct.

**Recommended: run the Radon test alone at peak ≥ 0.90, and print the topology
verdict beside every hit.** Two agreeing tests is a stronger claim than either,
and their false positives are disjoint on this sheet — but the conjunction
silently drops (5,27), a real wall on area 11. Following `doorcheck.py`'s
precedent, the deliverable is a **contact sheet and a flag, not a
reclassification**: 13 crops of the printed page is a five-minute review, and
the two failure modes are asymmetric in the same way doors are. A missed
diagonal wall merges two rooms in the extent table; an invented one seals a
room. Both are worse than a human looking at thirteen pictures.

---

## 3. The model

This is the harder half, and the measurement below decides it in a direction I
did not expect when I started.

### 3.1 What the schema has now, and why it must not be reused

`cells.passage` already carries `'diagonal'` — but for 45-degree **passages**,
and `dmap.reachable` reads it to *grant a corner step* between two such cells:

```python
diag = {k for k, v in cells.items() if v[3] in ('diagonal', 'diagonal_half')}
...
if diagonal and (x, y) in diag:
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
```

A diagonal **wall** is the dual problem, and putting it in the same column would
be actively dangerous: a cell that must *break* a connection would be granted an
extra one. `extract.passage_kind` reinforces this — it returns `'diagonal'` for
rock on two **adjacent** sides and explicitly rejects rock on two **opposite**
sides as "a straight corridor pinched from both flanks, which is not the same
thing". Rock on two opposite corners is precisely the partition signature. A
diagonal wall needs its own column.

### 3.2 Option A — half-cell nodes

`cells.diagonal TEXT CHECK (diagonal IN ('SWNE','NWSE'))`. A cell carrying it is
two graph nodes: for `SWNE`, one owning sides `{N,W}` and one owning `{S,E}`;
for `NWSE`, `{N,E}` and `{S,W}`. Every graph walk becomes a walk over
`(x, y, half)` instead of `(x, y)`.

**What it costs.** Every consumer of the cell graph has to be taught about
halves — see §4 — and one thing genuinely does not fit: **`cells.room` is a
single column**, so a cell split between two rooms cannot be recorded. Area
34's (26,24) is half armory and half Room of Pools and the schema has one slot
for it.

**What it buys.** Exactness of *connectivity*, and the ability to place a door
on the diagonal itself.

### 3.3 Option B — an explicit non-connection relation

A `blocked_turns` table, or a `no_connect(level, ax, ay, bx, by)` relation: "these
two adjacent cells do not connect, despite the boundary between them". Cheaper
to write than half-cells and it composes with the existing edge model.

But it is the wrong shape. A diagonal wall does not block a *boundary*, it
blocks a *turn through the interior of a cell*: entering (26,24) from the north
and leaving to the east is forbidden, while entering from the north and leaving
to the west is fine. A pairwise "a and b do not connect" cannot express that —
it is a relation on cell pairs, and the fact being modelled is a relation on
(entry side, exit side) within one cell. Writing it as pairs loses information
and produces wrong answers wherever a diagonal cell has three or four open
boundaries, which is all four of area 34's.

If you go this way, make it a **turn restriction** keyed on `(level, x, y,
from_side, to_side)` — which is exactly Option A written out longhand, with
6 rows per diagonal cell instead of one column value.

### 3.4 Option C — the staircase approximation

Do not change the model at all. Convert each detected diagonal into the set of
grid boundaries the 45-degree line crosses, and set those to `wall`, assigning
each diagonal cell wholly to one side.

This is not a hypothetical: **it is what `b1_corrections.tsv` already does for
area 34**, by hand, five rows:

```
edge  26 23 H  wall     edge  27 24 H  wall     edge  27 25 V  wall
edge  28 25 H  wall     edge  29 27 V  wall
```

The rule is mechanical. For a `SWNE` cell assigned to the north-west side, wall
its south and east boundaries; for `NWSE` assigned north-east, wall its south
and west. Applied to the four area-34 cells that reproduces those five
corrections exactly (three of the eight boundaries were already `wall`).

### 3.5 The measurement that decides it

Flood area 34 from the party's square (24,23) on the **raw classifier output**,
before any key or correction is applied, three ways:

| run | squares | bounding box |
|---|---|---|
| 1. as the pipeline does it today, orthogonal edges only | **103** | x22–31, y14–31 |
| 2. + the ten diagonal cells as half-cell nodes (Option A) | **31** | x22–31, y19–31 |
| 3. + the five hand edge corrections (Option C) | **31** | x22–31, y19–31 |
| the player's outline, read off the printed map | **31** | |

```
run 1 vs documented: missing []  extra [72 squares]
run 2 vs documented: missing []  extra []
run 3 vs documented: missing []  extra []
```

Two conclusions, and the second is the important one.

**The detector alone recovers the room.** Run 2 used no human input at all — the
diagonal cells came straight from §2.4 — and it reproduced, square for square,
an outline that previously required the player to read the printed map and
thirty-one hand-entered `member` rows.

**Half-cell nodes and the staircase give the identical answer.** They differ only
in how they round a half-square, and *the ground truth rounds too*: the player's
own reading assigns (26,24), (27,25), (28,26) and (29,27) wholly to area 34,
because a 10-foot square is the unit the map is drawn in and the unit the party
moves in. On the one room where ground truth exists, the extra machinery of
Option A buys nothing.

### 3.6 What the staircase genuinely cannot do

Being honest about it, because §6 rests on this:

1. **It needs one bit of human input per cell** — which side owns it — and the
   image does not carry that bit. The band runs corner to corner through the
   centre; the Radon offset is ~0 and gives no signal. The choice comes from
   which *room* the cell belongs to, which is a reading of the text or of the
   printed page. Option A does not need the bit for connectivity (it needs it
   only for `cells.room`, and could store `NULL` there honestly).
2. **It loses half a square of floor per diagonal cell** to the neighbour. 50
   square feet, below the resolution of the grid.
3. **It cannot express two rooms sharing a square.** Neither can `cells.room`,
   so this is a schema limit rather than an option-C limit.
4. **A cell where two diagonals meet is ambiguous.** (5,25), the vertex of area
   10's chevron, carries a SW–NE wall and abuts a NW–SE one. The staircase must
   pick; half-cells would need four quarter-nodes.

### 3.7 The two rooms nobody has looked at

The reason this is not simply "the `member` corrections are good enough" is that
running the extent derivation on the live database and cross-referencing the
detected diagonals shows **two more rooms currently leaking across a diagonal
wall**, with no correction and no play record:

| detected diagonal | owner of the cell | owner NW of it | owner SE of it |
|---|---|---|---|
| (6,28) SWNE | area **11** | 11 / 11 | 11 / 11 |
| (7,27) SWNE | area **10** | 11 / 11 | 10 / 10 |
| (5,25) SWNE | area **10** | 10 / **11** | 10 / 10 |
| (5,24) NWSE | area **10** | 10 / 10 | 10 / 10 |
| (6,23) NWSE | area **10** | 10 / 10 | 10 / 10 |
| (7,22) NWSE | area **10** | 10 / 10 | 10 / 10 |
| (26,24) (27,25) (28,26) (29,27) | area 34 | 34 / 34 | 31 / — |

Area 34's row is what a *corrected* room looks like: the extent stops at the
wall, and the Room of Pools owns the far side. Areas 10 and 11 have **the same
area on both sides of the wall** — they have flooded straight through it, five
times over. Extracted extents today: **area 10 = 32 squares, area 11 = 19
squares**, both unverified against the printed page, both containing at least
one diagonal wall they have grown across. Area 11 is a rotated *diamond* of
about nine squares; nineteen is not a rounding error.

So: **three of B1's thirty-seven areas are affected, one is fixed by hand, and
two are wrong right now.**

---

## 4. Blast radius

Named functions, by option. Option C's column is the point of the table.

| file | function | Option A (half-cells) | Option C (staircase) |
|---|---|---|---|
| `extract.py` | `_measure` / `cell_stats` | add the Radon peak, orientation and offset to the per-cell dict | same |
| | `passage_kind` | must NOT return the wall case (see §3.1); add a sibling `diagonal_wall(s)` | same |
| | `classify_edge` | a boundary touching a diagonal cell is only half-open — new branch | unchanged |
| `build.py` | `extract_map`, `write_db` | set and persist the new column | set it as a diagnostic only |
| | `apply_corrections` | new `diag` scope | uses the existing `edge` scope |
| `schema.sql` | `cells` | new `diagonal` column + CHECK | **unchanged** |
| `dmap.py` | `load` | select the column | unchanged |
| | `reachable` | flood over `(x,y,half)`; interacts with the existing corner-step rule for `passage='diagonal'` | unchanged |
| | `find_path` | BFS over `(x,y,half)`; `path_report`'s square and foot counts must not double-count a split cell | unchanged |
| | `room_graph` | component flood over halves | unchanged |
| | `describe` | the `exits:` list must say which exits are reachable *from where the party is standing in the square* | unchanged |
| | `render` | **no way to draw this today** — see below | unchanged |
| | `check` | new contradiction: an `open` boundary a diagonal crosses | could flag it |
| `extents.py` | `opener` | `is_open(a,b)` takes only two cells; needs the entry side | unchanged |
| | `wide_cells` | the 2×2 block test must not straddle a diagonal | unchanged |
| | `grow` | BFS over halves | unchanged |
| | `apply_to_db` | `cells.room` cannot hold two rooms (§3.2) | unchanged |
| `markers.py` | the `--from-cell` reachability used to propose markers | must match `dmap.reachable` or markers land wrong (this exact class of drift is in the notebook) | unchanged |
| `highlight.py` | unreachable overlay | follows `reachable` | unchanged |
| `tools/party.py` | `route` → `dmap.find_path` | inherits | unchanged |
| | `move` | check the **DETOUR guard** (`walked > max(2, straight * 2)`). Travel *along* a diagonal chamber is safe — measured, (24,23)→(31,31) is 15 squares against a straight-line 15, and half-cells do not change that, because a monotone staircase costs exactly the Manhattan distance. The risk is a short hop that must now go round a wall, where the floor of 2 is easy to exceed. Not demonstrated; must be re-measured against the party's recorded route before shipping | unchanged |
| `tests/synth.py` | | new `diagonal_wall()` — the existing `diagonal()` draws a corridor in `FLOOR`; the wall version is the same line in `ROCK` | same |
| `tests/test_reachability.py` | | new: a planted diagonal wall must break a chain the orthogonal edges leave open | same |
| `tests/test_classify.py` | | `passage_kind` must still reject the opposite-sides pattern | same |
| `tests/test_extents.py`, `test_corrections.py` | | growth must stop at a planted diagonal | corrections regression |

### The ASCII renderer

`dmap.render` draws a cell as a three-character body between two edge glyphs:

```python
body = room[:3].center(3) if room else CELL.get(terrain, '?') * 3
```

There is no slot for a diagonal, and the room number already owns the body. The
options, in increasing cost:

1. **Legend line.** Print the diagonal cells under the map: `diagonals: (26,24)\
   (27,25)\ ...`. No layout change. This is the right first move.
2. **Steal the body when there is no room name.** `body = '\\'.center(3)` or
   `'/'` — but every diagonal cell on B1 is inside a numbered room, so this
   almost never fires.
3. **Two-line cells.** Double the row height so each cell has a `\` line and a
   name line. That is a rewrite of `render`, and it doubles the height of a
   45-row map to 90 lines plus separators.

Under Option C, `render` needs nothing at all — the walls appear as ordinary
`|` and `---` glyphs, drawn as the staircase they were converted to. That is
arguably *more* honest for a tool whose job is telling the DM which way the
party can walk.

---

## 5. Migration and safety

**A game is in progress.** `rebuild.sh` prints two counts as regression checks:
DMG **21 unreached of 641**, B1 **5 of 1,196**.

### Would the proposal move them?

**Detection alone: no.** Simulating the half-cell model on the live databases,
with the detector's own output and no hand input:

```
B1   baseline   walkable 1196  reached 1191  UNREACHED 5
     with diags walkable 1196  reached 1191  UNREACHED 5     newly unreachable: 0
DMG  0 diagonal cells detected; unchanged
```

**Zero change.** This is not a lucky result, it is the structure of the problem,
and it is the same asymmetry the notebook records for fabricated doors:

> A diagonal wall the extractor missed leaves everything *passable*. Nothing is
> sealed, so no reachability check can ever see it. It shows up only in the room
> extents.

So reachability is the wrong regression check for this work, and passing it
proves nothing. The check that would have caught area 34 is the extent
cross-check, and the check that did catch it was the player reading the map.

**One change would move a count**, and it is the DMG's secret door on the
diagonal at §1.7: marking `(5,24,V)` as `secret` takes the DMG from **21
unreached to 10**. That is a **correct** improvement, not a regression — the
eleven squares recovered are area 29's treasury, which `README.md` already
documents as unreachable for exactly this reason. But it must be made as a
deliberate, separately-committed change with the expected count in `rebuild.sh`
updated in the same edit, or the next person to run the script will read a moved
number as a break. **Do not bundle it with anything else.**

### Staging, so a live campaign never runs on a half-migrated map

The order matters and each step is separately revertible:

1. **Measure only.** Add the Radon statistic to `cell_stats` and a
   `diagcheck.py` that prints hits and writes a contact sheet. It writes nothing
   to the database. `rebuild.sh` gains a review step next to `doorcheck.py`.
   Both regression counts must be *byte-identical* after this step; if they are
   not, the change touched something it should not have.
2. **Review the thirteen crops with the player**, exactly as the six furnished
   rooms were reviewed. Areas 10 and 11 are the live questions.
3. **Enter the verdicts as ordinary `edge`/`member` corrections** in
   `b1_corrections.tsv`. This is the only step that changes the map the game is
   read from, and it goes through the file that already always wins. It is
   revertible by deleting lines.
4. **Re-run and diff the extents.** Areas 10, 11 and 34 should change and
   nothing else should. Reachability must hold at 5.
5. Only if steps 1–4 prove insufficient, consider the schema change — and do it
   on a *copy* of the database with `dmap.py reach`, `dmap.py path` and
   `tools/party.py move` exercised against the party's actual recorded route
   before it goes anywhere near `output/b1/b1.sqlite`.

`markers.py --apply` is not idempotent and `extents.py` clears `cells.room`, so
corrections are already applied three times in `rebuild.sh`. **Any new writer of
`cells` must be slotted into that order explicitly**, not appended.

---

## 6. Recommendation

**Build the detector. Do not change the model.**

### What to build first

A single new file, `mapdb/diagcheck.py`, modelled on `doorcheck.py`, plus about
fifteen lines in `extract.py`:

- `extract.diagonal_stat(rk)` — the two-angle Radon of §2.4, returning
  `(orientation, peak, offset)`; called from `_measure`, stored on the cell dict
  as three more fields. This is the whole imaging change.
- `diagcheck.py` — lists every cell with `peak ≥ 0.90` and rock fraction
  0.15–0.45, prints the topological verdict beside it, and writes a contact
  sheet of 3×3-cell crops of the printed page with the candidate boxed. For each
  hit it also prints the **proposed staircase correction lines**, ready to paste
  into the corrections file once a human has agreed.
- `rebuild.sh` gains one review step. Nothing is written to the database.
- `tests/synth.py` gains `diagonal_wall(x0,y0,x1,y1,width)` — the existing
  `diagonal()` with `fill=ROCK` — and one test that a planted 45-degree wall of
  a given width is detected at its planted orientation, plus one that a planted
  *corridor* of the same width is **not**. That second test is the one that
  matters; it is the distinction corner occupancy gets wrong.

That is the smallest useful increment: it turns a fault that was found by a
player standing in the room into a fault found by a five-minute contact sheet,
and it changes no behaviour at all.

### What to do next

Review the thirteen B1 hits and enter verdicts for **areas 10 and 11** as
corrections. Those two rooms are wrong today, and they are wrong in the way that
walks a party through a wall.

Separately and on its own, correct the DMG's `(5,24,V)` to `secret` and update
the expected count in `rebuild.sh` from 21 to 10.

### What I would deliberately NOT do

- **Not lower `--t-thick`.** Already recorded in `lab_notebook.md` and confirmed
  here: the diagonal partitions' 48 boundaries have a median thickness of 2.0 px,
  inside the printed-ruling band. No global threshold reaches them without
  destroying the wall/ruling separation everywhere else.
- **Not add half-cell nodes, a `cells.diagonal` column, or a turn-restriction
  table.** On the only room with ground truth, half-cells and the staircase give
  the identical 31 squares (§3.5), and the staircase costs *nothing* downstream
  while half-cells touch `reachable`, `find_path`, `room_graph`, `describe`,
  `render`, all four of `extents.py`'s functions, `markers.py`'s flood and
  `party.move`'s detour guard. Twelve cells on one sheet do not justify that
  surface area, and `party.py` exists to make illegal moves an exception — a
  bug introduced there mid-campaign is worse than the fault being fixed.
- **Not reclassify automatically.** `doorcheck.py` earned its "flag and draw,
  never reclassify" rule the hard way. The Radon detector is cleaner than
  anything in the door work — precision 0.92 with a real gap — but it has been
  validated on **one** sheet with **twelve** positives. That is not enough to
  let it write to a database a live game is read from.
- **Not attempt curved walls.** The arch north of area 12, area 25's lobes and
  area 27's oval are the same *class* of problem — non-orthogonal geometry the
  grid cannot express — but a curve has no orientation to record and no
  staircase that is obviously right. They already have hand corrections.
- **Not build a general Hough transform.** Two angles is all these sheets use;
  180 angles costs ~100× and buys a robustness nobody has a use for.

---

## 7. What I could not determine

- **Whether the twelve are all of them.** The detector's recall is 1.00 against
  *adjudicated* ground truth, but the ground truth was built by adjudicating the
  detectors' own union (19 cells). A diagonal wall that all four tests miss would
  be invisible to this study. The one guard I have is that no candidate list from
  any of the four detectors contained a true positive the others entirely
  missed.
- **The true extents of areas 10 and 11.** I can show they have flooded across a
  diagonal wall; I cannot say what the right answer is. That needs the player to
  read the printed page, exactly as it did for area 34. Guessing an outline to
  make a number look better is the failure this project's notebook exists to
  prevent.
- **Whether the mass-face style is as safe as it looks.** It works because the
  cells beyond it read `solid`. I did not find a place on either sheet where a
  45-degree wall's mass is only one cell thick with `mixed` on both flanks — the
  configuration where both boundaries would fall through to `classify_edge`'s
  mixed branch and `gap ≥ 0.25` would call them open. Area 34's north-west wall
  is 1–2 cells of pure rock and its neighbours measure exactly 1.00, so the
  margin there is large. But "I did not find one" is not "there is none", and on
  B1's lower level or a new module it could easily occur.
- **Whether 45 degrees is universal.** True on these two sheets and on graph
  paper it is the natural angle, but it is an assumption. The Radon peak is
  reported so a wall at another angle scores low and is *missed* rather than
  mis-oriented — a safe failure, but a silent one.
- **The DMG's diagonal staircase at area 30.** `(5,27)`, `(6,28)` and `(7,29)`
  are a 45-degree staircase — a diagonal *passage* carrying a legend symbol.
  They are reached today only through `dmap.reachable`'s corner step for
  `passage='diagonal'`; a flood without that rule loses all three. The Radon test
  fires on `(5,27)` because tread hatching at 45 degrees projects like a wall. I
  did not work out whether the corner-step rule, the stairs edge kind or a
  diagonal-wall model is the right description of that square, and a detector
  that writes to the database would have to decide.
