# mapdb — reading dungeon maps off scanned pages

Turns a scanned graph-paper dungeon map into a queryable grid: one row per 10'×10'
square, one row per boundary between squares, with a confidence score on every call.

Built as a practice run on the **DMG sample dungeon** (DMG pdf page 96, printed 95)
before applying the same pipeline to B1.

```bash
conda activate advanced_dnd_1e
python -m pytest -q                    # the mapdb suite
```

Outputs live under `output/<map>/`; code, key modules and correction files stay
at the top level. Every tool takes `--help`.

## Running it on each map

The same code drives both sheets. Nothing is forked -- the differences are all
options, and each was **measured on the sheet** rather than guessed. Run
`build.py --help` for the full set.

| option | DMG | B1 | why |
|---|---|---|---|
| `--channel` | `mean` | **`r`** | B1 is printed in blue. Blue ink absorbs red, so the red channel roughly doubles the ink/paper contrast (5th percentile 12 vs 109). |
| deskew | none applied | **-0.37 deg applied** | B1's sheet is genuinely rotated: +0.37 deg, monotonic across 3, 5 and 7 bands. The DMG reports -0.015 deg *non*-monotonic, which is fit noise, and is correctly left alone. Automatic either way. |
| `--t-thick` | `4.5` | **`6.0`** | Where a boundary stops being a printed ruling and starts being a drawn wall. DMG: rulings 0-3 px, walls 6+. B1's heavier blue line: rulings 0-3 px, walls 7-18, empty gap at 4-6. |
| `--key` | `dmg_key` | `none` yet | The DMG's key module carries hand-verified labels and the node graph from the module text. B1's is not written yet. |
| `--max-off-line` (markers) | not needed | **`0.30`** | B1 draws every table, bed and barrel, all in thin strokes, which swamps the marker detector (213 candidates). A door marker annotates a *wall*, so requiring it near a grid line cuts that to 103; furniture sits mid-room. |
| symbols | `S` secret, `C` concealed, boxed `X`/`S` traps | `S` secret, one-way secret, false door | Different legends. B1 has no concealed door. B1 draws doors as white shapes *reversed out of* the wall band but secret doors as dark `S` glyphs *on* it, so the two need different detectors. |

### Rebuild both maps

**Use `./rebuild.sh` rather than the commands below.** The step order is
load-bearing and `extents.py --apply` was being left out of the by-hand
sequence, which leaves `cells.room` covering only the label squares -- 58 of
B1's 1,196 -- while everything still looks fine.

```bash
./rebuild.sh both        # build -> markers -> extents -> world replay -> check
./rebuild.sh b1
```

It ends by printing the two reachability counts as regression checks: DMG **21**
unreached of 641, B1 **4** of 1,196.

The individual commands, for reference:

### DMG sample dungeon (the validated practice case)

```bash
python build.py --plots                                  # -> output/dmg/
python dmap.py render output/dmg/dmg.sqlite 1
python dmap.py reach  output/dmg/dmg.sqlite 1 --from-room 1
python review.py                                         # contact sheet for QC
python markers.py --db output/dmg/dmg.sqlite             # secret-door detector
```

### B1, Quasqueton upper level

```bash
B1="../modules/tsr09023 -In Search of the Unknown .pdf"
python build.py --pdf "$B1" --page 1 --channel r --t-thick 6.0 --boxr 0.50 \
    --key b1_key --corrections b1_corrections.tsv \
    --db output/b1/b1.sqlite --level 1 \
    --name "B1 Quasqueton, upper level" --images output/b1/images
python markers.py --db output/b1/b1.sqlite --key none --pdf "$B1" --page 1 \
    --from-cell 16 1 --max-off-line 0.30 \
    --sheet output/b1/images/20_markers.png --apply
python highlight.py --db output/b1/b1.sqlite --pdf "$B1" --page 1 --channel r \
    --from-cell 16 1 --out output/b1/images/21_unreachable.png \
    --index output/b1/unreachable.txt
python dmap.py reach output/b1/b1.sqlite 1 --from-cell 16 1
```

`b1_key` supplies the label positions and the extent cross-checks, but it has
no `MARKERS` block, so `markers.py` runs with `--key none` and proposes them
itself. Reachability starts from an explicit cell rather than a room anchor:
(16,1), just inside the ENTRANCE, which the sheet prints across (15,0)-(17,0).

## Coordinates

`x` increases **east**, `y` increases **north**, origin at the south-west corner of
the map sheet. Edges are stored once, canonically: `orient='V'` is the **east** side
of `(x,y)`, `orient='H'` the **north** side. The cell↔edge relation is the `cell_edges`
VIEW, computed rather than stored, so it cannot drift out of sync.

## Why it is not just a brightness threshold

Four things all look like "dark pixels" and each needed its own discriminator.

**1. Rock vs printed annotation — connectivity.**
Room numbers are black marks sitting inside white rooms; a naive threshold reads the
numeral "10" as half a square of rock. But the rock is one huge connected mass while a
numeral is a blob of a few hundred pixels, so keeping only dark components of ≥900 px
yields the rock and the discarded remainder is the annotation layer (0.47% of the page).
This moved ~20 numbered rooms from "mixed" to "open".

**2. Ruling vs drawn wall — stroke thickness.**
The sheet is printed graph paper, so a ruling runs along *every* boundary and joins the
rock mass; coverage cannot separate them. Thickness can. Measured perpendicular to the
boundary and taken as a median along it, rulings are 0–3 px at 200 dpi and drawn wall
bars are 6+ px, with the 4–5 px range essentially empty (323 vs 21 of 357 open–open
boundaries). Threshold 4.5 px.

**3. Door vs wall — topology.**
Doors are drawn as small outlined rectangles straddling a boundary, so in the rock mask
they are thick too. But an outline *encloses white* and a filled bar does not. The
largest enclosed-white region in a box on the boundary midpoint is either 0 or ≥50 px —
nothing in between.

**4a. Wall vs partial square — does the rock SPAN the boundary?**
Median thickness answers "how thick is the rock here", which is the wrong
question where two half-filled squares meet: rock covering part of a boundary
still leaves a way through. `gap` measures the fraction of the boundary length
the rock does *not* block, and a boundary with a quarter of it clear is open.
Using the median alone severed seven passages that plainly connect on the page.

**4. Door vs staircase — hole shape.**
Stair treads are a ladder of slots and also enclose white. They are long and thin
(4–5 px × 30 px, aspect 5.6–7.8) where a door leaf is compact (~15×8, aspect ≤ 2.8).
Filtering on aspect ≤ 3.5 removed four phantom doors stacked in the stairwell at (12,41–43).
Stairs are picked up separately by counting rock/void alternations across a square.

## Grid registration

Pitch and phase come from maximising gradient energy on candidate grid lines:
**40.45 px × 40.65 px at 200 dpi** = 0.2 inch = standard 5-squares-per-inch graph paper.
The fit is verified by drawing it back onto the page (`images/01_grid_overlay.png`).

Rotation is checked by fitting the x-phase in three horizontal bands; a *monotonic*
drift means the sheet is skewed. The DMG sheet gives −0.015°, i.e. square. **B1's sheet
is visibly rotated and will need the correction applied**, not just measured.

## Terrain classes

| class | meaning | confidence |
|---|---|---|
| `solid` | rock fills the square | 10 (8 if not quite pure) |
| `open`  | floor fills the square | 10 (8 if not quite pure) |
| `mixed` | rock covers part of it — diagonal passage, cave wall, irregular chamber edge | **3, always** |

`t_solid` is **0.05**, not a round number. A full-width 45-degree corridor
leaves only about a quarter of a square open, and at the original 0.25 those
squares were called solid and the corridor came out in disconnected pieces.
1006 of 1680 squares measure *exactly* 0.000, so anything with measurable floor
in it is not rock.

`mixed` is not a failure; the 10' grid genuinely cannot express a diagonal. These 76
cells are exactly what `lowconf` surfaces for a human to check, and they cluster where
they should: the staircases, the cave and stream by area 2, and the long diagonal
corridors in the south.

## Two independent readings

`dmg_key.py` holds the node graph built from the **key text alone**, never from the
image. `build_dmg.py` then cross-checks the two. This is the point of the exercise: a
disagreement means one of the readings is wrong, and it is much easier to find that way
than by re-deriving geometry ad hoc under narrative pressure.

The check already paid: the text says area 3 "appears to be a dead end" with a secret
door in its **south** wall leading to 24. The grid independently shows a passage running
south from area 3 at x=12 — correct topology — but had classified that boundary as
ordinary open floor, because the secret door is marked by a printed `S` that lives in the
annotation layer, invisible to a rock-based classifier. The `S` at (12,24) confirms it.

**Secret doors cannot be read from the rock mask and must come from the text or from the
`S` markers.** That is a standing limitation, not a bug to fix.

## Labels

`ocr_labels.py` separates digits into whole labels and runs tesseract over each. On the
DMG map it got roughly 70% right: it misses numerals printed over the rock (29, 32, 35 —
they merge into the rock mass and never reach the ink layer), reads partial numbers
("11"→"1", "14"→"4", "36"→"6"), and calls the boxed secret-door `S` an "18". So OCR
**bootstraps** the label table and the results are then checked by eye against a QA
montage (`images/09_label_qa.png`). The corrected table lives in `dmg_key.py`.

Room anchors are the cell holding the printed label, **not** the room's extent: on these
maps rooms and corridors are both plain white, so the boundary between them is a reading
of the key text rather than a drawn feature.

## Images

| file | what |
|---|---|
| `01_grid_overlay.png` | fitted grid drawn back onto the page |
| `02/03_zoom_*.png` | magnified corners confirming registration |
| `04_ecdf_white.png` | ECDF + histogram of cell openness |
| `05_bimodality.png` | Otsu separability vs openness |
| `06_classified.png` | terrain classes tinted over the map |
| `07_rock_vs_ink.png` | rock (blue) vs annotation (red) |
| `08_final.png` | final classification |
| `09_label_qa.png` | montage for checking OCR by eye |

## Legend symbols, and rotation

`symbols.py` crops templates from the map's own LEVEL KEY and matches them over
the annotation layer. Two things make it work:

**A negative class.** Matching S and C against nothing but each other makes
every digit score as one or the other — a rotated "2" resembles an S more than
it resembles a C, so it wins by default. 23 of 59 marks came back as secret
doors. The verified ROOMS table supplies labelled examples for free (the marks
in area 23's anchor square are, left to right, a "2" and a "3"), so digit
templates are *learned from the map itself*. False positives fell to one.

**Asymmetric rotation.** Printed numbers are never rotated; legend symbols
routinely are, and one S on this sheet stands at 45° against a diagonal wall.
So digits are matched upright only and symbols swept through 24 angles. That
asymmetry is what stops an upright "5" being claimed by a rotated S — the digit
matches its own template near 1.0. The winning angle is kept, since it says
which wall a marker belongs to.

Glyphs are normalised (cropped to ink, scaled to a common canvas, centred)
before comparison, so the score measures shape rather than size or position.

## The stream

Water is drawn as a winding band through the rock and is not a corridor. Its
squares have a distinctive signature — `sides=NSWE`, rock touching all four
borders, because the thread never reaches an edge cleanly — which is exactly
the opposite of a diagonal passage (rock on two *adjacent* sides). It is
excluded from the walkable network; without that it contributes fourteen
unreachable squares that are not rooms at all.

## Reachability — the strongest single check

Every non-solid square should be reachable from the entrance, through doors,
secret doors and trap doors. A square that is not is either genuinely isolated
or, far more often, evidence of a wall the extractor invented or a door it
missed.

```bash
python dmap.py reach dmg.sqlite 1 --from-room 1
```

It is a *global* check, which is what makes it valuable: it needs no reference
map and it catches errors anywhere on the sheet, including ones sitting in
squares the confidence score was happy about.

On the DMG sheet it went 70 unreachable -> 24 across Phase 1, and the 24 that
remain are all correct:

| squares | why unreachable |
|---|---|
| 11 | area 29, the treasury — behind the secret door at 28, which the map draws as a **door in a 45° wall inside one square**. The schema has no way to say that. |
| 6+1 | the area 39 corner: stairs and a half-width corridor. The sole exception predicted in advance. |
| 4 | the stairwell between areas 4 and 5, reached only through the two **secret trap doors** flanking it. |
| 2 | two squares of a half-width diagonal whose rock sides are not the adjacent-pair pattern. |

The first and last are honest modelling gaps rather than misreadings, and both
are about geometry finer than a 10' square.

A corner step is allowed between two cells that both carry `passage='diagonal'`.
Full-width diagonals do not need it -- they clip the neighbouring squares and
the chain is orthogonally contiguous -- but a **half-width** 45-degree corridor
connects only at the corner, and the squares that would bridge it orthogonally
measure 0-3% open. Marking those walkable would invent floor that is not on the
page.

## Tests

```bash
python -m pytest -q            # everything
python -m pytest -q -m "not integration"    # skip the real-PDF tests
```

`tests/synth.py` draws maps with planted ground truth -- known pitch, known
skew, a numeral overlapping rock, stair hatching, door glyphs, wall bars. Tests
that only ever compare against the real DMG page can check that today's output
matches yesterday's; they cannot check that the output is *right*. The
synthetic maps can.

The suite found four real bugs on first run: `concealed` and `trap_door` were
missing from the schema's edge-kind constraint, `reachable()` accepted a
`diagonal` flag it never honoured, and the synthetic generator itself painted
rock across the whole sheet so `find_field` saw the page as the map.

## B1 (Quasqueton) — what differs from the DMG sheet

```bash
python build.py --pdf "../modules/tsr09023 -In Search of the Unknown .pdf" \
    --page 1 --channel r --t-thick 6.0 --db b1.sqlite --level 1 \
    --name "B1 Quasqueton, upper level"
python markers.py --db b1.sqlite --pdf "<same>" --page 1 \
    --from-cell 16 1 --max-off-line 0.30 --apply
```

Five things had to change, and each was measured rather than guessed:

**Blue ink.** B1 is printed in blue. Blue absorbs red, so the RED channel
separates ink from paper about twice as well as the mean does (5th percentile
12 vs 109). `--channel r`.

**The sheet is rotated.** +0.37 degrees, monotonic across 3, 5 and 7 bands --
unmistakable next to the DMG's non-monotonic -0.015. That is ~10 px of drift
over the height of the map, a quarter of a square, so it is corrected rather
than merely noted. After `-0.37` the residual is -0.03 and non-monotonic.

**Heavier line weight.** Rulings 0-3 px, walls 7-18 px, gap at 4-6. The DMG
separates at 4.5; B1 needs 6.0. Always plot the histogram on a new sheet.

**Different symbol scheme.** B1's legend has no concealed door; it has FALSE
DOOR and ONE-WAY SECRET DOOR instead. More importantly its doors are drawn as
white shapes REVERSED OUT of the wall band, while its secret doors are dark S
glyphs drawn ON the band -- so the hole test finds the first pair and the
thin-stroke detector finds the second.

**The rooms are furnished.** B1 draws every table, bed and barrel, all in thin
strokes, so the marker detector's precision collapses without a positional
constraint: 213 candidates. A door marker annotates a WALL, so requiring it to
lie within 0.30 of a square of a grid line cuts that to 103 while keeping the
markers -- furniture sits out in the middle of a room.

## Stairs are a way through

Found while chasing B1's entrance corridor, which came out sealed off from the
other 1200 squares of the level. A staircase is drawn as a ladder of treads,
which reads as *thick* to the thickness test and as a *stack of doors* to the
hole test, so both rejected it and the boundary fell through to `wall`.

Adding `stairs` as a passable edge kind took B1 from **30 reachable squares to
1161**, and the DMG from 24 unreachable to 21. It is the single largest
correctness fix in the project, and the reachability check is what surfaced it.

## Two bugs worth remembering

**A tool must reproduce the build's grid exactly.** `markers.py` re-rendered the
page with its own defaults -- mean channel, no deskew -- while B1's database had
been built from a red-channel, deskewed render. The grids disagreed by up to a
quarter of a square, so every marker it found was attributed to the wrong edge.
It looked like success: the run reported markers applied and regions opened.

The fix is structural rather than a flag: `levels` now stores `pdf`, `page`,
`dpi`, `channel` and `deskew_deg`, and every tool that reopens the page reads
them back. Re-running the marker pass afterwards applied *four* markers instead
of seven and reached MORE squares -- three of the original seven were spurious.

**`--apply` mutates the database, so it is not idempotent.** Running it twice
gives different answers, because the second run sees the regions the first one
opened. Always rebuild before applying.

## What the image cannot tell you

B1 draws some interior features -- floor mats, a raised stage, a rock outcrop --
as **dotted rectangles**, and the dots have merged in the scan. Measured against
the whole population of genuine walls between two open squares:

| | min thickness |
|---|---|
| real walls (n=545) | p25 = 8, p50 = 8, p75 = 8 |
| the dotted features | 6 - 8 |

They are indistinguishable, and rendering at 400 dpi does not separate them
either -- the source scan has already merged the dots. This is not a threshold
that needs tuning; it is information the image does not carry. It has to come
from the module text, which describes area 37's mats as "20' by 20'" -- exactly
the 2x2 footprint the extractor sealed off.

## Drawn furniture reads as a door — run `doorcheck.py` and look at the sheet

The single most damaging error this pipeline makes. Six of B1's furnished rooms
-- 9, 23, 24, 25, 27, 28 -- shipped **fabricated doors**: a drawn bed cut area 24
in half, area 25's lobes came out as five doors, area 27's dais as four. Every
one was found *during play*, by the player noticing the printed map did not match
what the DM had narrated. A fabricated door invents a passage the party can be
walked down.

No threshold separates them. Area 24's two fabrications measured thickness 9 and
10 with hole 134, against the genuine door beside them at 7 and 187 -- the fakes
sat closer to the middle of the door band than the real door did. `thick` cannot
work here, because with `half=0.30, trim=0.25` it samples a band 0.5 cell long
centred on the boundary, which is **entirely inside the door glyph**: it has
always measured the drawing, never the wall.

What does separate them is structural, and the player supplied it:

> *"the furniture lines only exist on one side of the wall, unlike the doors
> that go through the wall"*

`extract.door_suspect` measures exactly that, in two parts:

- **`wall`** -- median perpendicular rock on the boundary *beside* the glyph
  (0.55-1.05 cells either side). A drawn wall bar is 8-26 px; furniture inside a
  room sits on a 2-4 px graph-paper ruling. No wall, no door.
- **`offset`** -- how far the glyph's enclosed-white centroid lies from that
  measured bar, in cells. Doors the party has walked through: <= 0.13.
  Fabrications abutting a real wall: 0.14-0.35.

Both are measured against the **bar found on the flanks**, not the nominal grid
line -- a few px of grid-fit and deskew error is a large fraction of an 8 px
glyph, and two earlier attempts that split about the grid line failed completely
(see `lab_notebook.md`).

```bash
python doorcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
    --boxr 0.50 --key b1_key --sheet output/b1/images/30_doors.png
```

On B1 level 1 it keeps **7 of 7** doors the party has physically walked through
and rejects **9 of 16** confirmed fabrications. It is a **sieve, not a
classifier**: it misses about a third, and the `ok` list still contains scenery
curves and shelving.

**A `no wall` flag alone is weak; `one-sided` is strong.** `_flank` samples the
boundary 0.55-1.05 cells either side of the glyph, so where a wall is only ONE
SQUARE long -- a stub of jamb between two openings -- both flanks land in open
floor and a genuine door is flagged "no wall". Area 29's real door `(23,6,V)`
does exactly this: flank 2.0 px, but `offset` 0.09 and `hole` 193, both
door-perfect. When only `no wall` fires and `offset` is under about 0.10, look at
the crop: that is a door in a short wall more often than it is furniture.

**So it flags and draws; it never reclassifies.** The contact sheet is the
deliverable -- every door call as a crop of the printed page with the boundary
marked -- because reading that sheet is what actually found all six rooms, and it
found them faster than any number did. The verdict is human and goes in
`b1_corrections.tsv`, which always wins. `rebuild.sh` runs it as a review step.

## A 45-degree wall is invisible to an edge model — run `diagcheck.py`

`edge_stats` asks *"how much rock lies along this grid boundary"*, and a wall
drawn at 45 degrees answers *"none"* while completely blocking passage: the rock
sits **inside** the square. So `extents.py` floods straight through it. B1's
area 34 came out as 41 squares holding the Room of Pools' own markers, and it
was found **in live play**, with the party standing in it.

The full study, including the model options that were rejected, is in
`DIAGONAL_WALLS.md`. The one general rule:

> A diagonal wall is invisible to a boundary-based model precisely when the space
> on the far side of it is FLOOR rather than ROCK.

That is why the DMG sheet never showed this and B1 did — every DMG diagonal is
the flank of a corridor cut through rock, so the neighbouring cells read `solid`
and `classify_edge` short-circuits to `wall` on terrain alone.

**Lowering `--t-thick` cannot reach these.** The twelve partition cells sit on 47
boundaries whose median thickness is 2.0 px — dead centre of the printed-ruling
band. They are not walls measured thin; there is no wall on the boundary at all.

`extract.diagonal_stat` measures instead a **Radon transform restricted to the
two angles the sheet uses**: project the cell's rock along constant `row+col` and
constant `col-row` and take the strongest line over the cell side. A band drawn
corner to corner projects onto one diagonal index for its whole length, so the
peak reaches 1.0; furniture is short, curved or off 45 degrees. Gated on rock
fraction 0.15–0.45, because a corner wedge's hypotenuse is a 45-degree line too
and only gets long enough to score by filling the square.

| B1 level 1, 1,358 in-frame cells | peak / cell side |
|---|---|
| the 12 adjudicated diagonal walls | **0.90 – 1.00** |
| the 7 adjudicated false positives | 0.33 – 0.83 |
| control cells, rock 10–45% (n=295) | p50 0.23, p90 0.50 |

Precision 0.92, recall 1.00. `extract.side_classes` asks the independent
topological question — *which of the square's four sides are mutually reachable
through its own floor* — and 0.85 / 0.92; the conjunction is 1.00 / 0.92, and the
one it drops, (5,27), is a real wall. So the detector reports both.

```bash
python diagcheck.py --pdf "$B1_PDF" --page 1 --channel r --t-thick 6.0 \
    --boxr 0.50 --key b1_key --db output/b1/b1.sqlite \
    --sheet output/b1/images/31_diagonals.png
```

**It flags and draws; it never reclassifies**, for `doorcheck.py`'s reason. It
prints the hits, the topology verdict, the room on each side of the wall (the
same area on both sides is a room that has flooded through it) and the `edge`
corrections each hit implies — for a human to accept. `--db` is opened
**read-only**; nothing here writes to a database. `rebuild.sh` runs it as a
review step.

Two things the image cannot supply: **which side of the wall owns the square**
(the band runs through the centre, so the offset carries no signal — it is a
reading of the room), and the extents themselves, which still need `member` rows.

## Rooms versus corridors

An anchor says where a label is printed; it does not say which squares are the
room. Nothing in the image says either -- rooms and corridors are both plain
white. But a corridor is narrow and a room is not, and on a grid that has an
exact form:

> **a corridor never contains a 2x2 block of open floor, and a room does.**

Testing for the block rather than measuring a width needs no threshold and
behaves at junctions, where a T of 1-wide corridors gives cells three open
neighbours but still no block. Rooms then grow from their labels by
multi-source breadth-first search inside that mask, nearest seed winning, with
sub-locations folded into their base area so 1, 1A and 1B stay one room.

Only `open` boundaries conduct. A door or a staircase is a way through but it is
also a boundary between spaces, so a room cannot grow through one.

Corridor and room are kept strictly separate -- a doorway square is corridor --
which keeps "which squares are area 12" unambiguous, and makes the wide areas
that end up with no label informative rather than noise.

| | DMG | B1 |
|---|---|---|
| areas given an extent | 39 of 39 | 37 of 37 |
| median room | 6 squares | 6 squares |
| corridor squares | 268 of 641 | 829 of 1196 |
| wide but unlabelled | 0 | 92 |

`extents.py` must run **after** `markers.py --apply`: applying a secret door
changes which boundaries are open, and extents depend on that.

### Why both checks are needed

Reachability and the size check catch **different** faults, and neither subsumes
the other:

- a fabricated **wall** seals squares off, so reachability sees it;
- a fabricated **door** is still passable, so connectivity is undisturbed and
  reachability is blind to it — only the room coming out the wrong size reveals it.

B1's areas 17 and 18 supplied one of each, both from furniture drawn inside the
room. Area 18's fabricated door would not have been found by any connectivity
argument.

### The size cross-check

Descriptions state room dimensions, so an extent can be checked rather than
trusted -- and this is the independent reading B1's node graph could not supply,
since its text says how big things are but not what they connect to.

Beware which dimension. Taking the first one in a description is wrong:
B1 sizes area 37's floor mats ("measuring 20' by 20'") and an outcropping in
area 22 before it ever sizes a room. `stated_squares()` only accepts a dimension
with a room word within 45 characters of it.

On B1 it flags three of the four areas that state a size, and the three are
different in kind: area 22's stated 2 squares against an extracted 16 says the
*dimension* is a feature, not the room; areas 17 and 18 disagree by 2 squares
each and are worth a look at the walls.

## Playing from the database

```bash
python dmap.py at    output/b1/b1.sqlite 1 32 13     # where am I, what are the exits
python dmap.py path  output/b1/b1.sqlite 1 16 1 32 13   # squares, feet, turns, rounds
python dmap.py seen  output/b1/b1.sqlite 1 --room 25 # record what the party verified
python dmap.py light output/b1/b1.sqlite 2 14 9 --radius 3 --mark-seen  # what a lantern there actually reveals
python dmap.py walk  output/b1/b1.sqlite 2 14 9 E                       # advance east until something stops it
```

`seen` is DM-side only. It exists because describing geography the party has not
verified is the specific mistake this database was built to prevent.

**`light` is `seen`'s computed replacement for "which cells is the light close
enough to reach."** Built day 139 after a session with several geometry errors
that all came from eyeballing grid distance instead of asking the map, the
worst being a `seen --cells` list hand-picked from squares that only *looked*
close on a printed page. It ray-casts: draws the exact line from the light's
cell centre to a candidate cell's centre and asks whether it crosses a wall,
a shut door, or solid rock before it gets there — not graph distance, not
Euclidean distance alone, an actual line of sight. That is why it correctly
sees clear across an open room on the diagonal (naive grid math undercounts
this) but does **not** see around a corner even when the far cell is well
inside the nominal radius (naive Euclidean distance overcounts this). `-
-radius` is in cells, 10 ft each; a hooded lantern's 30 ft is the default.
`--mark-seen` calls `seen` on exactly the newly-lit squares, so narrating what
a light source reveals and recording it are one call, not two guesses.
See `mapdb/dmap.py`'s `line_of_sight()` docstring for the exact rule on the
one genuinely ambiguous case, a ray that grazes a lattice corner precisely —
and `mapdb/tests/test_line_of_sight.py` for the worked cases (open room,
around a corner, a secret door that still looks like wall, a diagonal squeeze
between two solid corners).

**`walk` is `light`'s companion for open-ended movement** — "advance east",
"keep going until something changes" — replacing a guessed destination
retried against `party.py move`'s REFUSED errors, which is what several of
day 139's geometry mistakes actually were. It takes the one way forward
through a plain corridor on its own and stops the instant there is a real
event: a junction (2+ ways on, once the way just walked is excluded — a real
choice, handed back rather than picked for the player), a dead end, an
area-label change (leaving a numbered room counts as much as entering one),
or a feature already visible to the party (its own `feature` tag, or a
secret/concealed edge that is already `seen` — an unfound secret is invisible
to this exactly as it is to a passing glance). Simply stepping onto ground
nobody has walked is deliberately **not** a stop condition — a long plain
corridor should not stop every ten feet just because it is new.

**Level 2's room labels are unreliable** (see "Treat `cells.room` on level 2
as nearest numbered area" above) — an area-boundary stop there can fire on a
label flicker that means nothing in the fiction, over one large, patchily
labelled cavern. `walk` does not try to filter that out; read a level-2
area-boundary stop the way any low-confidence call in this database is read,
not as certain. See `mapdb/tests/test_walk.py` for the worked cases.

**Deliberately knows nothing about monsters, wandering or placed.** Wandering
checks stay exactly where they are, on `clock.py`'s round-based schedule,
independent of geometry — `walk`'s square/foot count is what tells the DM
how big a block to advance before the next check. Placed-monster presence
lives in a separate, DM-only registry — `tools/stocking.py`, reading
`modules/private/b1_stocking.tsv` — and `walk`/`light` are deliberately kept
ignorant of it, the same separation `clock.py` and `mapdb` already keep —
`walk` is kept a pure geometry query on purpose, the same separation
`clock.py` and `mapdb` already keep.

**Rebuilding clears it.** `seen` lives in the extracted tables, so a rebuild
wipes it, exactly like a correction made directly in SQLite. Re-run the `seen`
calls after any rebuild, or move them into a key module if they become numerous.

---

# READ THE MAP'S LEGEND FIRST — B1 prints one, and it was missed

**This cost 60 wrong door calls on B1 level 1.** The instruction already existed
(`CHECKLIST.md` §10, *"Read the map's own legend before writing any classifier"*);
it was followed for the DMG sample dungeon and **never for B1**, whose sheet
carries its own legend at the foot of the map page (pdf page index 1).

| symbol | meaning |
|---|---|
| a box **STRADDLING** the wall, floor showing both sides | **DOOR** |
| an `S` set into the wall | **SECRET DOOR** |
| an `S` with an arrow | **ONE-WAY SECRET DOOR** |
| **a box on ONE side of an UNBROKEN wall** | **FALSE DOOR** |
| even hatching / tapering | **STAIRS, UP / STAIRS, DOWN** |
| a star in a circle | **STATUE** |
| a boxed `X` | **PITS, COVERED** |

### The trap in that table

**A FALSE DOOR is drawn exactly like furniture-against-a-wall.** Both are a
one-sided box on an unbroken wall. So `door_suspect`'s "one-sided" flag finds
*both* and cannot tell them apart — **only the legend can**, and only by eye.
B1 level 1 contains one genuine false door, at `(29,31,H)`, at the dead end of a
corridor with two covered pits in the floor in front of it.

## The ink profile — the test that works where thickness does not

Thickness bands (**B1: doors 4-11, walls 7-18, printed rulings 0-3**) are a net,
not a verdict. `(13,20,H)` measured **thick=9 at confidence 9** — dead inside the
door band — and was a kitchen counter drawn against a solid wall.

**Sample a perpendicular ink profile at ~19 points across the boundary, 200 dpi:**

| | signature |
|---|---|
| **genuine door** | the wall value held (7-8 px) with **two narrow spikes** flanking it — the drawn box's edges |
| **plain wall** | flat 7-8 px |
| **furniture / false door** | flat but **ELEVATED by +3 to +8 px** over the same wall bar either side |

The three doors B1's own text calls false measure the same way (+4 to +8 over
their own wall), which is what identified a fourth.

**This belongs in `extract.py`.** A working implementation is in the audit
scratchpad as `profile.py`, alongside `crop_edge.py` (grid-annotated crops),
`perim.py`, `border.py` and `reach2.py` (per-change reachability delta).

## The 2026-09-03 audit

All **106** `door` edges on level 1 examined on a rendered crop; **61** measured
additionally with the profile. **43 kept, 62 corrected, 5 held back.**

- Every kept edge was cross-checked against `campaign/world_changes.tsv` — **no
  edge the party has physically walked through was changed.** 21 of the 43 keeps
  are doors they have opened themselves.
- Causes: **27 furniture**, 17 printed rulings, **9 circled floor-markers in area
  31**, 4 floor outlines and cave channels, 2 diagonal room walls, 2 legend
  symbols, 2 inverse errors (`wall` at exactly the 6.0 threshold, cutting area 37
  in half).
- **Held back:** the five edges in the strip east of area 31 — the only reason the
  audit's reachability moved 6 → 9. The cause is the **area 33 barracks bed
  frames**, already corrected once on 2026-08-29 for the same class of error.
  That strip was already broken and needs its own pass.
- Artefacts: `mapdb/output/b1/audit/` — 65 crops, `BY_CAUSE.md`, and the
  paste-ready `proposed_corrections.tsv`.

---

# LEVEL 2, THE CAVERNS — built 2026-09-04, and what it taught

`b1.sqlite` now holds **both** levels. Level 1: 1,665 cells, **48 doors**, 9 secret,
**6 unreached of 1,197**. Level 2: 1,728 cells, **4 doors**, 4 secret,
**0 unreached of 923**. Page index **2** of the module PDF, grid
`x0=127.1 px=40.30 nx=36 | y0=89.2 py=40.05 ny=48` at 200 dpi, **no deskew** —
the lower sheet is square on the page where level 1 has a genuine +0.37 deg skew.

## THE MERGE IS PART OF `rebuild.sh` AND MUST STAY THERE

**`build.py` deletes and recreates its target database.** Every run of
`rebuild_b1` therefore destroys level 2, and **nothing fails when it does** —
level 1's reachability, extents and door counts all still check out, so the loss
is silent. `rebuild_b1` now rebuilds and re-merges the lower level before its
reachability check. `merge_lv2.sql` deletes level 2 first, so it is idempotent.

**`b1_corrections.tsv` has NO LEVEL COLUMN.** `apply_corrections(db, file, level)`
stamps every row at the level you pass. Level 2 therefore has its own
`b1_lv2_corrections.tsv` (177 rows) and its own key module `b1_lv2_key.py`.

### Two kinds of correction, and they are not the same claim

Day 118: the player asked, of `(4,15,H)`, "what's the right way to store this" —
a passage the DM added mid-session to explain where six orcs went, with the
player's explicit permission, that **is not on the printed page at all.** Most
rows in a corrections file fix a MISREAD of the page; this kind asserts
something the page never showed. Conflating them means a future page-render
verification pass reports a correct, deliberate override as a mismatch.

**`apply_corrections` takes an optional 8th column, `provenance`.** Omit it, or
write `extraction`, for the ordinary case. Write `play` for a deliberate,
player-permitted departure from the page — it prefixes `build.PLAY_OVERRIDE_MARKER`
onto the stored note, so any future check that renders the page and diffs it
against the database can `grep` for that marker and skip the cell/edge instead
of flagging it. `(4,15,H)` in `b1_corrections.tsv` is the one example so far.

## THE SHEET HAS A SECOND LEGEND

Page 1 prints DOOR / SECRET DOOR / FALSE DOOR / ONE-WAY SECRET DOOR / STAIRS /
STATUE / PITS COVERED. **Page 2 prints a DIFFERENT one: POOL, DEPRESSION, WEBS.**
Two legends in one module. **Check every map page for its own legend** — that is
now twice this map has explained itself and been ignored.

## `extract._edge` SAMPLES THE MIDDLE HALF OF A BOUNDARY

**This is the single biggest finding of the level-2 build.** `_edge` trims 25% off
each end of a boundary and takes the median of what remains.

- **On a stronghold that is correct.** A doorway is cut in the middle of a wall.
- **On a cavern it is wrong.** The floor crosses a grid line wherever the cave
  happens to run — very often within a couple of feet of the cell **corner**. The
  sampling window then sees nothing but rock and calls a wall.

Measured over the **full** boundary instead (perpendicular rock thickness at every
pixel, longest run thinner than the printed-ruling band):

| `wall` edges between two walkable squares | 268 |
|---|---|
| clear run 0-2 px — rock genuinely spans it | 100, left alone |
| clear run 3-7 px — ambiguous | 43, **left alone and still uncertain** |
| **clear run >= 8 px (2+ ft of open floor)** | **125, OPENED** |

That one pass took the unreached count from **90 in 28 regions to 18**. All 125
were rendered and confirmed by eye; a stratified control of 18 more at run 0-7
showed rock spanning the boundary every time.

### A real bug inside that: `label_boxes` does not shield a cell's BORDER

It insets by 0.15, so an area numeral **straddling two squares** has the half near
the boundary join the rock mask, and **fabricates a wall between two squares of
its own room.** Seven cases on level 2 — under the labels for areas 38, 42, 44,
45, 47, 54 and 55. Drawn symbols do the same: the statue at (3,18,H), the covered
pit at (7,22)-(8,23), area 50's pool contours.

## SECRET DOORS ON A CAVERN SHEET ARE NOT ON GRID LINES

The module says the secret doors *"are either rock or disguised by rock so as to
appear unnoticeable"*, **and that is literally how they are drawn: each `S` sits
on a plug of rock INSIDE a square.** Placing them on the boundary the glyph looks
nearest leaves them bypassable, because the cave floor runs round through the
corner of the next square.

**How it was caught: sealing all three changed reachability by ZERO squares.**
Sample the rock mask at 16 points per square, find which row or column of the
square is solid across, and put the door on the boundary the blocked passage
actually crosses.

And a fact about the map rather than the extraction: **only one of the four
secret doors seals anything.** (30,6,H) cuts off 13 squares; the other three are
shortcuts, because the caverns loop.

## DO NOT QUOTE LEVEL 2'S ROOM EXTENTS

`extents.py` grows a room from "contains a 2x2 block of open floor". **On a cavern
every bulge in a winding passage passes that test**, and nearest-seed growth runs
until it meets another label: area 51 gets 96 squares, area 53 gets 180, area 44
gets 2, area 50 gets 4, and 175 squares come out "wide but unlabelled".

**Treat `cells.room` on level 2 as "nearest numbered area", NOT "inside room N".**

**And the lower-level text states no room dimension anywhere**, so the
extent-vs-stated-size cross-check — one of CHECKLIST section 7's three
independent checks — **does not exist on this level.** Reachability and the text
sweep carry the whole load.

## No 45-degree walls at all on level 2

`diagcheck.py` returns **0**: `diag_peak` max 0.83 over all 1,277 in-frame cells,
against level 1's twelve true partitions at 0.90-1.00. The non-orthogonal
geometry here is **curved**, which `DIAGONAL_WALLS.md` puts explicitly out of
scope. **Different sheet, different failure mode** — do not go looking for the
last map's bug.

> ### ⚠ AND LEVEL 1 HAS A CURVE TOO — see `CURVED_CORRIDORS.md`
>
> Out of scope for detection is not out of scope for **reading**. A half-ellipse
> corridor sweeps round area 12, and on day 99 `dmap at` reported its bend as a
> **T-junction with two open exits** — both of which were the rock inside the
> curve, at 0.00 and 0.23 open. It was narrated to the player as two ways on.
>
> **The rule, before narrating any junction: check the open fraction of each
> candidate exit.** An "open" edge means the boundary is passable and the cell is
> not solid; it does **not** mean the cell is floor. Two exits both under 0.40
> means you are standing at a bend.

## KNOWN BUG in `dmap.py reach`

On level 2 it reports `walkable 923 reached 925` — **reached exceeds walkable.**
The corner step for `passage='diagonal'` does not re-check that the destination
is walkable, so it counts two squares that are now `solid`. Pre-existing and
harmless to routing, but it makes the headline number nonsense and will confuse
the next reader. **Worth fixing.**

## Still uncertain on level 2 — itemised

1. **(21,8,V)** kept as a door: the glyph is the sheet's door glyph but sits 0.34
   squares off the boundary in open floor with nothing to straddle, and area 38's
   contents include *"rock carts"*. No route depends on it.
2. The three western secret doors' **exact** boundaries — the plugs are 0.3-0.5
   squares from the line the door was placed on.
3. **The 43 boundaries at a 3-7 px clear run**, left as `wall`. Some are probably
   squeezes.
4. **The WEBS glyph** could not be found printed anywhere, though the legend
   defines it and area 42 is the WEBBED CAVE. Left unplaced rather than guessed.
5. Four squares called `solid` at 5-8% open: (13,43), (30,28), (8,29), (6,26).
6. **Area 39, the MUSEUM, carries no printed number** — 18 of 19 areas are
   labelled and it is not. Position inferred from the text, then confirmed
   independently; recorded at **confidence 6**, not 10.
7. `markers.py` corroborates only **one** of the four `S` glyphs; its thin-stroke
   detector is much weaker on this sheet.

*(Module typo, for the record: area 55's heading is printed "35. EXIT CAVE".)*

---

# Appendix — moved out of `CHECKLIST.md` on 2026-09-12

**This was section 10 of `CHECKLIST.md`, which is the standing procedure for
RUNNING THE CAMPAIGN. 147 lines of map-pipeline procedure is not that, and
keeping it there made the file longer without making it more read.**

Nothing is changed and nothing is lost. `CHECKLIST.md` now carries a pointer to
here.

## The map extraction pipeline

Read `mapdb/README.md` before touching it, and `mapdb/lab_notebook.md` before
trying anything clever. Both maps are driven by the same code with different
options — the differences are measured, not guessed, and the table of them is in
the README.

> ### `rebuild.sh` WAS SILENTLY ABORTING PART-WAY THROUGH. Read this.
>
> *(Found 2026-09-04, and only because a game query hit a table that should
> have had rows in it.)*
>
> The script runs under **`set -euo pipefail`**, and **`world.py replay` exits 1**
> whenever any log row fails to match the map — three legacy rows always do.
> **So the script died at that line every run**, silently skipping everything
> after it: the level-2 merge, the door review and the diagonal review. Level 1's
> numbers all printed correctly first, so nothing looked wrong.
>
> **The lower level vanished from `b1.sqlite` this way** and was not noticed for
> an hour of play.
>
> **Two rules out of it:**
> - **NEVER run a rebuild with its output suppressed.** No `>/dev/null`, no bare
>   `tail -3`. If you must filter, filter and then check the LAST line is the one
>   you expect. I hid this from myself with `>/dev/null 2>&1`.
> - **A step that legitimately exits nonzero needs `|| echo …`, not `|| true`.**
>   Swallow the status, keep the message.

**Rebuild with `mapdb/rebuild.sh`, never by hand.** The step order is
load-bearing and one step was being skipped: `extents.py --apply` runs after
`markers.py` and before `world.py replay`, and without it `cells.room` covers
only the 58 label squares of B1's 1,196, which looks like success and quietly
makes every area-scoped query wrong.

```bash
./mapdb/rebuild.sh both                # build, markers, extents, replay, check
python -m pytest mapdb/tests tools/tests -q      # both suites
```

`rebuild.sh` prints the two reachability counts as **regression checks**: DMG
**21** unreached of 641, B1 **5** of 1,196 *(was 4 until 2026-08-28; (34,13) is a
rock outcrop that should never have been reachable)*. If either moves, something changed
behaviour — find out what before playing on it.

Standing facts that carry to any new sheet:

- **Read the map's own legend first.** Four classifiers were written before
  anyone looked at the DMG's LEVEL KEY, and several early misreadings were
  symbols the book defines explicitly. **AND THEN IT HAPPENED AGAIN:** B1's sheet
  prints its own legend too, nobody read it, and **60 of level 1's 106 doors were
  wrong** (audit 2026-09-03). The legend defines **FALSE DOOR** — a box on one
  side of an unbroken wall — which is **drawn identically to furniture against a
  wall**, so the "one-sided" flag finds both and cannot separate them. See
  `mapdb/README.md`.
- **The INK PROFILE beats thickness.** Sample ~19 points perpendicular across the
  boundary at 200 dpi: a genuine door holds the wall value with **two narrow
  spikes** flanking; a wall is flat; **furniture is flat but elevated +3 to +8**
  over the same bar either side. Thickness is a net — `(13,20,H)` measured 9, in
  band, confidence 9, and was a counter drawn against a solid wall.
- **Secret doors cannot be read from the image.** They come from the text.
- **Room anchors are label positions, not room extents.**
- **DIAGONAL walls are invisible to the edge model** — the rock sits inside the
  squares, so every boundary measures thin and open and a room's extent floods
  through it. Four B1 rooms are affected: **34** (fixed from the player's own
  reading of the printed map), and **10, 11 and 33**, all still wrong. Run
  `mapdb/diagcheck.py`, read the contact sheet, and note that its `room` column
  names the fault directly: a corrected room reads `34/34 | 31/None`, a leaking
  one reads `10/10 | 10/10` — the same area on both sides of a wall.
  See `mapdb/DIAGONAL_WALLS.md`.
- **BOTH LEVELS NOW LIVE IN `b1.sqlite`** — level 1 **6 unreached of 1,197**, level
  2 **0 of 923**. `rebuild_b1` rebuilds and re-merges level 2 itself; **do not
  remove those lines.** `build.py` deletes and recreates its target, so every
  rebuild destroys the lower level, and **nothing fails when it does** — level 1's
  checks all still pass, so the loss is silent.
- **`b1_corrections.tsv` HAS NO LEVEL COLUMN.** `apply_corrections(db,file,level)`
  stamps every row at the level passed. Level 2 has its own
  `b1_lv2_corrections.tsv` and `b1_lv2_key.py`. Never mix them.
- **CHECK EVERY MAP PAGE FOR ITS OWN LEGEND.** B1 page 1 prints doors/stairs/
  statue/pits; **page 2 prints a DIFFERENT legend — POOL, DEPRESSION, WEBS.**
- **`extract._edge` samples only the MIDDLE HALF of a boundary.** Right for a
  stronghold, **wrong for a cavern**, where the floor crosses a grid line near the
  cell *corner*. It fabricated **125 walls** on level 2 and accounted for 90 → 18
  of the unreached squares. Measure the full boundary when the map is caves.
- **`label_boxes` shields a cell's interior but NOT its border**, so a numeral
  straddling two squares invents a wall **inside its own room**. Seven cases on
  level 2.
- **On a cavern sheet, secret-door `S` glyphs sit on rock plugs INSIDE squares,
  not on grid lines** — the module says the doors are disguised as rock and the
  map draws them that way. Placing them on the nearest boundary leaves them
  bypassable; **sealing them changed reachability by zero, which is how it was
  caught.**
- **DO NOT QUOTE LEVEL 2'S ROOM EXTENTS.** `cells.room` there means "nearest
  numbered area", not "inside room N" — and the lower text states no dimension
  anywhere, so the extent cross-check does not exist on that level.
- **`markers.py --apply` mutates the database and is not idempotent.** Rebuild
  first. (`world.py replay` *is* idempotent, deliberately — it always starts
  from what the build produced and applies the whole log.)
- Every tool that reopens a page must reproduce the build's grid — the render
  settings are stored in the `levels` table for that reason.
- **A real door CROSSES the wall; furniture does not.** On the page a genuine
  door glyph straddles the wall band with floor showing on both sides, because
  the door goes through the wall. Drawn furniture lies wholly on the room side.
  **This is the one test that separates them reliably** — thickness does not, and
  area 24's fabrications measured *closer to the middle of the genuine band than
  its real door did*. Player's insight, 2026-08-28.
  **IMPLEMENTED** as `extract.door_suspect` + `mapdb/diagcheck.py`'s sibling
  `mapdb/doorcheck.py`, which flags and draws a contact sheet but never
  reclassifies. It has since caught **seven** fabricated doors in live play —
  and **NINE** by 2026-09-03. Both of the last two were called by the player from
  the module text alone, before any tool was run:
  **(18,19,H)** in **area 3, the DINING ROOM** — thick=17, deep in the WALL band,
  stools drawn against the room's south wall; and
  **(13,20,H)** in **area 2, the KITCHEN** — **thick=9, INSIDE the genuine door
  band, confidence 9**, a counter drawn against the north wall leaving a white gap
  read as hole=200.
- [ ] **AN IN-BAND THICKNESS DOES NOT CLEAR A DOOR THAT OPENS OFF A FURNISHED
      ROOM.** (13,20,H) passed the 4-11 test and was still fabricated. The
      thickness flag is a *net*, not a verdict: render the page at 8-10x with the
      grid drawn on it and apply the only reliable test — **a real door CROSSES
      the wall band with floor showing on both sides; furniture lies wholly on
      the room side.**
- [ ] **THE FURNISHED-ROOM LIST IS THE RED FLAG.** In B1 so far: **areas 2, 3, 9,
      18, 24, 27, 28.** Before narrating any door on the boundary of one of
      these, render it. *(The player has now caught two in a row that no
      automated check flagged, purely from knowing what the room is for.)* Read
  `wall` and `offset` TOGETHER: a lone `no wall` flag is weak (a genuine door in
  a one-square stub of wall trips it), while `one-sided` is strong.
- **Flag every `door` whose thickness falls outside 4-11** and render that page.
  B1's genuine doors measure 4-11, its walls 7-18, its printed rulings 0-3 — so a
  door outside that band is suspect. **Four fabricated doors were found this way
  in one session**, in three consecutive furnished rooms (areas 9, 27, 28).
  Neither automated check can see them: a fabricated door stays passable, and the
  extent check is blind when the room has another way in. **But the flag is
  noisy** — it lists 48 edges on level 1, not a handful. Render the **thickness
  1-3** and **18+** tails first; the 12-15 band is mostly genuine doors on heavy
  line work. See `mapdb/lab_notebook.md`.
- **The play record is a fourth check on the map**, and it catches what the
  other three cannot. The party walked through a boundary at the end of
  expedition 3 that the database recorded as a plain wall at thickness 15: no
  glyph was proposed, reachability was blind because both sides were reachable
  anyway, and no text names it. `world.py check` now reports that class of
  disagreement.


---

## ⚠ B1'S PRINTED LEGEND IS INCOMPLETE — it does not list every glyph it uses

The map page prints a key: **DOOR · SECRET DOOR · FALSE DOOR · ONE-WAY SECRET
DOOR · STAIRS UP · STAIRS DOWN · STATUE · PITS COVERED.** Reading it is still the
first thing to do — it settled three edges in one afternoon on day 95, because
*door = a rectangle drawn **across** the wall line*, *secret = a printed **S***,
and *false = a rectangle on **one side***, and those three shapes are impossible
to confuse once you have seen them side by side.

**But the legend is not exhaustive, and assuming it is will cost you.**
`(10,41,V)` is a **PORTCULLIS** — on the page a narrow band of very fine circles
sitting on the boundary — and **portcullis appears nowhere in the key.** The
extractor called it wall; a human reading the legend would find nothing to match
it either.

**So when a glyph matches nothing in the key, the answer is in the ROOM TEXT, not
in the symbol.** Area 13's entry names this one in passing, while describing
something else entirely: *"a counterweight mechanism for the portcullis trap in
the corridor just outside the room."* The map never labels it; the prose does.

**The measurement that flagged it first:** ink thickness on that boundary was
**5 px**, against **1 px** for an open floor ruling and **8-13** for a wall. *A
boundary that measures between the two classes is carrying a drawn symbol,* and
the symbol is the thing to go and identify. Do not round it to the nearer class.

**And the check that proved it independently was `dmap.py reach`.** Correcting a
neighbouring false secret door to wall stranded three squares, 8 unreached → 11.
Squares reachable only through a door that is not on the page were never
reachable, so a real connection had to exist elsewhere — and the only candidate
was the 5 px boundary. Restoring it put unreached back to 8.
