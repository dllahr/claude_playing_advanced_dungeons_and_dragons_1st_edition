# Diagonal walls, part 2: connectivity — a plan

**Status: a PROPOSAL.** Nothing here is implemented. No pipeline file was
changed, `rebuild.sh` was not run, and `output/b1/b1.sqlite` was not written to.
Every measurement below comes from scratch scripts run against a *copy* of the
two databases and a cached render of the two pages. Both regression counts were
re-checked against the copies and are where `rebuild.sh` says they are: DMG **21
unreached of 641**, B1 **5 of 1,196**.

Part 1 (`DIAGONAL_WALLS.md`) solved **detection**. `extract.diagonal_stat` finds
all 13 of B1's 45-degree-walled squares at precision 0.92 / recall 1.00 and
`diagcheck.py` draws them. That work is shipped and this document does not
revisit it.

What is not solved is **what a diagonal wall means for connectivity** — and that
is the half that gets a character killed. `tools/party.py` is the only legal way
to move the party and it validates every move against `dmap.find_path`. It
exists because on expedition 4 the party was walked through a wall from (19,5)
to (19,6). If the grid says two squares connect when a diagonal wall separates
them, `party.py` routes through it and the guard built to make that impossible
never fires.

---

## 0. The live risk, in one table

Measured on the shipped `output/b1/b1.sqlite` as it stands today, against a
half-cell graph built from the detector's own 13 squares. Only pairs where
**neither endpoint is a diagonal square** are counted, so nothing here depends
on how a split square is interpreted:

| B1 level 1, 699,153 square pairs | |
|---|---|
| pairs the live map reports **closer than they are** | **20,931 (2.99%)** |
| pairs the live map reports **further than they are** | **0** |
| worst understatement | **+18 squares** — (6,29) to (9,28), live 4, really 22 |
| pairs called ≤ 2 squares apart that are really 6–16 | **18** |

Those last 18 are the dangerous ones, because `party.py`'s detour guard
(`walked > max(2, straight * 2)`) passes them without complaint. Every one is a
move the tool would permit through a printed wall. All 18 are in **areas 10 and
11**; area 34 contributes none, because it has been corrected.

```
(4,24) area 10 -> (6,24) area 10   live 2 squares /  20 ft   really 12 / 120 ft
(5,26) area 11 -> (6,25) area 10   live 2 squares /  20 ft   really 16 / 160 ft
(6,27) area 11 -> (8,27) area 10   live 2 squares /  20 ft   really 14 / 140 ft
(7,28) area 11 -> (9,28) area 11   live 2 squares /  20 ft   really 14 / 140 ft
...   18 in total, all in areas 10 and 11
```

The error is **always permissive**. The live map never says two squares are
further apart than they are; it only ever says they are closer. That is the same
asymmetry the notebook records for fabricated doors, and it is why no
reachability check has ever seen this.

---

## 1. Extents and paths are different questions

`DIAGONAL_WALLS.md` §3.5 recommended not building half-cell nodes, on the
evidence that a grid staircase of forced orthogonal `wall` edges reproduces area
34's extent exactly — 31 squares either way. That evidence is correct and it
still holds. It is also the wrong test.

> An extent needs the right **set** of squares. A route needs the right
> **graph**. A model can get every set right and still get routes wrong, because
> a set is closed under any relabelling of the edges inside it.

Re-measured, on the four affected rooms:

| | half-cell | staircase | live db |
|---|---|---|---|
| area 34 extent from `extents.py` | 26 sq | 26 sq | 26 (`rooms.extent_sq`), 31 with the hand `member` rows |
| area 34 extent vs the player's outline | identical | identical | identical |
| **routes through area 34** | exact | conservative | — |

The extents agree to the square. The graphs do not. §2 says by how much.

---

## 2. Q1 — does the staircase give a wrong PATH where it gives the right EXTENT?

### 2.1 The two graphs

**H, half-cell.** A square carrying a `SWNE` wall becomes two nodes: `NW`
serving sides {N,W} and `SE` serving {S,E}. `NWSE` gives `NE` {N,E} and `SW`
{S,W}. Orientation comes from `extract.diagonal_stat`, so **H needs no human
input at all** for connectivity.

**S, staircase.** The square stays one node, assigned wholly to one side, and
its other two boundaries are set to `wall`. This is what
`b1_corrections.tsv` already does for area 34 in five `edge` rows. **S needs one
bit per square** — which side owns it — and the image does not carry that bit
(§3).

Base map for both: the live `b1.sqlite`, with area 34's five hand staircase
corrections reverted to their raw classifier values, so the two models start
from the same un-diagonal-corrected map.

### 2.2 The staircase is conservative. This is a theorem, not a measurement

Through a diagonal square C, H admits exactly two relations: {N↔W} and {S↔E}.
S admits one of them and no others — whichever the assignment keeps — plus C
itself as a destination. So for every assignment,

> **reach(S) ⊆ reach(H), and dist_S(a,b) ≥ dist_H(a,b) for every pair.**

Confirmed empirically over 1.4 million pair comparisons across three
assignments: `staircase shorter 0` in every run. **The staircase can never route
the party through a wall.** It can only refuse a legal move or send them the long
way. That property is worth more than exactness, and it is the reason §7
recommends it.

### 2.3 Where it differs, and by how much

Three assignments, over B1 level 1. `H` is the oracle; `S` is scored against it.

| assignment | reach H | reach S | pairs with **no diagonal endpoint** | of those, differing | worst |
|---|---|---|---|---|---|
| every square to its **north** side | 1191 | **1191** | 693,253 | **0 (0.000%)** | — |
| every square to its **south** side | 1191 | **1184** | 686,206 | **0 (0.000%)** | — |
| **mixed** (area 34 north, areas 10/11 to the room the label sits in) | 1191 | 1184 | 686,206 | **8,923 (1.30%)** | **+24 squares** |

Pairs where one endpoint *is* a diagonal square are reported separately, because
"the distance from (26,24)" is ill-posed under H — see §2.5. There they differ on
23–57% of pairs, by up to +34 squares.

Read the table again, because it is the answer:

**A uniform assignment introduces zero routing error.** Every difference under
an all-north or an all-south choice is at a diagonal endpoint, where the question
is ambiguous anyway. Assign a whole *wall run* to one side and the staircase is
exact for every ordinary pair of squares on the sheet.

**A mixed assignment breaks real passages.** 8,923 pairs, up to 240 feet, none of
them touching a diagonal square. The mechanism is specific and worth naming:

> Two **diagonally adjacent** diagonal squares assigned to **opposite** sides
> seal all four boundaries between them, and the two ordinary squares in the
> other diagonal of that 2×2 are cut apart.

(7,27) belongs to area 10 and (6,28) to area 11. Enclosing area 10 means sealing
(7,27)'s N and W; enclosing area 11 means sealing (6,28)'s S and E. Between them
lie (6,27) and (7,28), which H joins in 2 squares through (7,27)'s NW half and
which S separates by 26. This is not hypothetical geometry — it is the strip
between area 10's north wall and area 11's south wall, and it is on the page.

**A wrong assignment can also seal squares outright.** All-south costs 7 squares
of reachability: (3,28) (4,28) (4,29) (5,28) (5,29) (6,29) (24,41). That is a
useful fact for §6 — reachability is blind to a *missed* diagonal but it does
see a *wrongly assigned* one.

### 2.4 The failure the staircase produces is a refused move, not a wrong one

Ordered pairs where S exceeds `party.py`'s detour limit `max(2, straight*2)`
while H does not:

| assignment | detour refused, diagonal endpoint | detour refused, **neither endpoint diagonal** |
|---|---|---|
| all north | 1,750 | **0** |
| all south | 3,306 | **0** |
| mixed | 1,684 | **2,384** |

Under a uniform assignment `party.py` never refuses a legal move between two
ordinary squares. Under a mixed one it refuses 2,384, and each refusal reads
*"the destination is NOT adjacent the way it looks"* — which is the right words
for the wrong reason, and a DM would enter `--max-squares` to force it through.

### 2.5 The thing half-cells cost that the staircase does not: a square stops being a place

`dmap.at`, `dmap.path`, `party.py where` and `campaign/party.tsv` all identify a
location as `(x, y)`. Under H a diagonal square is two locations, and they are
not close together:

| square | worst disagreement between its two halves' distance maps | median |
|---|---|---|
| (5,25) | **16 squares (160 ft)** | 6 |
| (7,27) | 14 squares (140 ft) | 4 |
| (5,24) | 12 squares | 6 |
| (8,28) | 12 squares | 4 |
| (6,23), (6,28) | 8 squares | 4, 8 |
| (5,27), (7,22) | 4 squares | 4, 2 |

So under H, `party.py move --to 5,25` is a question with two answers 160 feet
apart, and `campaign/party.tsv` has no column to say which. Under S the square
has one answer, which is wrong by at most the width of the square.

H also produces routes that are not simple in squares: **0.57% of sampled
shortest paths (1,156 of 203,831) enter the same square twice, once per half.**

```
(5,28) -> (5,27) :  5,28   5,27/NW   4,27   4,26   5,26   5,27/SE
```

That route is geometrically correct — you walk round the wall — but
`path_report` counts `len(route)-1`, `party.py` writes the route string into
`party.tsv`, and `dmap.mark_seen` iterates it. All three would see `5,27` twice.

### 2.6 Answer to Q1

**Yes, but only through the human's hand.** With a uniform per-wall assignment
the staircase and the half-cell graph agree on every path between two ordinary
squares — 0 of 693,253 pairs differ. The staircase's error is entirely a
function of the side choice, and it appears exactly where two walls face each
other across a narrow strip, which is areas 10 and 11 and not area 34. Area 34
is a *single wall run*; that is why §3.5 of part 1 found no difference, and it
is why that finding does not generalise: **the one room with ground truth is the
easy case.**

Both models are safe in the direction that matters. Neither can produce a route
the wall forbids. The staircase's failure mode is a refused move; the half-cell
model's is an ambiguous position.

---

## 3. Q2 — can wall-side ownership be derived automatically?

Part 1 concluded "which side owns the square is the human's reading". That is
right for `cells.room` and **wrong for connectivity**, and the distinction is the
useful part of the answer.

### 3.1 Connectivity does not need the bit at all

`diagonal_stat` returns the orientation. The orientation alone determines which
sides pair with which: `SWNE` → {N,W} and {S,E}. The half-cell graph is fully
determined by the image. **Connectivity is automatic.** Only the staircase needs
the bit, because it must throw one of the two pairs away.

### 3.2 Rule A — the bigger floor half wins. Measured, and it is not noise

Part 1 looked at the Radon *offset* (where the line lies) and found it ~0, and
concluded the image carries no signal. The offset is the wrong statistic. The
band has width, and it sits wholly on one side of the corner-to-corner diagonal,
so the two floor **areas** are not equal even when the line is central. Floor
pixels either side, from `side_classes`' own components:

| square | orient | NW / NE | SE / SW | bigger | ratio | documented |
|---|---|---|---|---|---|---|
| (26,24) | SWNE | 383 | 190 | **NW** | 0.67 | **area 34 = NW** |
| (27,25) | SWNE | 375 | 190 | **NW** | 0.66 | **area 34 = NW** |
| (28,26) | SWNE | 379 | 192 | **NW** | 0.66 | **area 34 = NW** |
| (29,27) | SWNE | 386 | 189 | **NW** | 0.67 | **area 34 = NW** |
| (7,27) | SWNE | 373 | 162 | NW | 0.70 | — |
| (8,28) | SWNE | 459 | 136 | NW | 0.77 | — |
| (5,25) | SWNE | 271 | 161 | NW | 0.63 | — |
| (7,22) | NWSE | 330 | 202 | NE | 0.62 | — |
| (6,23) | NWSE | 302 | 263 | NE | **0.53** | — |
| (5,24) | NWSE | 266 | 284 | SW | **0.52** | — |
| (6,28) | SWNE | 246 | 254 | SE | **0.51** | — |

**4 of 4 on the only ground truth**, at ratio 0.66–0.67. But three squares sit at
0.51–0.53, which is a coin toss, and the offset is ±1 px on all of them. So rule
A is a **proposal with a confidence**, not a decision: print it, and print the
ratio beside it so a 0.52 reads as "no opinion" rather than as an answer.

It is also unvalidated as a *convention*. n = 4, one wall, one sheet.

### 3.3 Rule B — let the extents growth decide, over half-cells

Run `extents.py`'s own algorithm — 2×2 wide mask, multi-source nearest-label
growth — over half-cell nodes instead of squares. Each **half** then gets a room
automatically, and the square's owner is the room of the half that wins.

| area | half-cell extent | live db | note |
|---|---|---|---|
| 34 | **26** | 26 (`extent_sq`) | identical to the staircase; the 31 in `cells.room` are the hand `member` rows |
| 10 | 21 | 32 | stops leaking |
| 11 | **4** | 19 | stops leaking, and then collapses — see below |
| 31 | 68 | 66 | takes back the far side of area 34's wall |
| 33 | 5 | 5 | **unchanged — area 33 is not a diagonal problem** (§8) |
| the other 32 areas | identical to the live db, square for square | | |

Two results in that table matter.

**It reproduces the whole sheet.** 32 of 37 areas come out byte-identical to the
database the game is played from. The model does not disturb anything it should
not.

**Exactly one square on B1 has its two halves in different areas**: (27,25),
`{31, 34}`. `cells.room` is a single column and cannot hold that — but it is
one square, and the player has already assigned it to 34.

**And rule B is not usable as it stands**, because of the interaction in the
next line.

### 3.4 The blocker rule B runs into: `wide_cells` cannot see a diamond

`extents.wide_cells` calls a square part of a room iff it belongs to a 2×2 block
of mutually open floor. Area 11 is a **45-degree-rotated diamond**. Once the
diagonals are honoured it contains **no 2×2 block at all**, so every square of it
reads as corridor and the area collapses to its 4 label squares.

Today's 19 is a leak; the half-cell 4 is a collapse. **Neither model gives area
11 its extent.** That needs `member` rows read off the printed page, exactly as
area 34 did — and it is not a diagonal-connectivity problem, it is the
room-vs-corridor rule meeting a room the rule was not designed for.

### 3.5 Answer to Q2

**Automatic for connectivity. Not automatic for ownership.**

- The half-cell **graph** is fully determined by `diag_orient`. No human input.
- The staircase needs **one bit per wall run**, not per square. Areas 10, 11 and
  34 are four wall runs between them, so B1's entire outstanding human input is
  **four bits** — not thirteen.
- Rule A proposes that bit from the image and is right 4/4 where it is confident
  (ratio ≥ 0.6) and abstains where it is not (ratio ≤ 0.53). That is the shape of
  the smallest human input: **`diagcheck.py` prints the proposed side and its
  ratio; the human confirms or flips it.**
- Ownership of `cells.room` still needs the player, and so do the `member` rows,
  and neither model changes that.

---

## 4. Q3 — blast radius, by function

`H` = half-cell nodes in the schema. `S` = staircase corrections only.

| file | function | what H needs | what S needs |
|---|---|---|---|
| `schema.sql` | `cells` | new `diagonal TEXT CHECK (diagonal IN ('SWNE','NWSE'))`. **Must not reuse `cells.passage`** — `dmap.reachable` reads that column to *grant* a corner step, so a wall would be given an extra connection (part 1 §3.1) | **nothing** |
| | `cell_edges` VIEW | an edge now separates two *(cell, half)* pairs, not two cells; the view must join `cells.diagonal` and emit the half. This is the view's whole purpose — it exists so the relation cannot drift | **nothing** |
| `extract.py` | `_measure` | already stores `diag_orient/peak/offset` and `side_classes` | same |
| | `classify_edge` | a boundary touching a diagonal cell is half-open; new branch | unchanged |
| | `passage_kind` | must keep rejecting the opposite-sides pattern | unchanged |
| `build.py` | `write_db` | persist the column | unchanged |
| | `apply_corrections` | new `diag` scope | uses the existing `edge` scope, which already works |
| `dmap.py` | `load` | select the column | unchanged |
| | `reachable` | flood over `(x,y,half)`; **interacts with the existing corner-step rule** — see §6.1, where this regresses the DMG | unchanged |
| | `find_path` | BFS over `(x,y,half)`; endpoints are ambiguous by up to 16 squares (§2.5); the returned route may repeat a square (0.57% of paths) | unchanged |
| | `path_report` | `len(route)-1` double-counts a repeated square. See §5 | unchanged |
| | `room_graph` | component flood over halves; one B1 region genuinely spans two areas | unchanged |
| | `describe` | the `exits:` list is **wrong today** for a diagonal square: it prints all four, and only two are reachable from where the party stands. Under H it needs the half; under S it is already right once the two boundaries are `wall` | fixed by the corrections |
| | `render` | **no slot exists.** The cell body is 3 characters and the room number owns it | nothing — the walls appear as ordinary `\|` and `---` |
| | `check` | add the diagonal-debt contradiction (§6.2) | **same — this is the point of §7** |
| | `mark_seen` | a repeated square is marked twice; harmless but sloppy | unchanged |
| `extents.py` | `opener` | `is_open(a,b)` takes two cells and needs the entry side | unchanged |
| | `wide_cells` | the 2×2 block test must run over halves — **and then area 11 collapses to 4 squares (§3.4)** | unchanged |
| | `grow` | BFS over halves | unchanged |
| | `apply_to_db` | `cells.room` cannot hold two rooms; one B1 square needs it | unchanged |
| `markers.py` | `isolated_regions` | has **its own copy** of the flood. It must match `dmap.reachable` exactly or markers land on the wrong edges — this precise class of drift is already in the notebook (the re-render bug) | unchanged |
| `highlight.py` | `render_highlight` | follows `reachable` | unchanged |
| `diagcheck.py` | `survey`, `corrections` | already emits both assignments | already emits both |
| `tools/party.py` | `route` | inherits `find_path`'s ambiguity | unchanged |
| | `move` | the detour guard: 0 false refusals under a uniform assignment, 2,384 under a mixed one (§2.4) | same |
| | `campaign/party.tsv` | **needs a `half` column** to say where the party is standing. Append-only log, live campaign | unchanged |
| `tools/world.py` | `replay` | cell `state` is keyed on `(x,y)`; a half-square state has no key | unchanged |
| `tests/` | `synth.diagonal_wall` exists | new reachability, extents and corrections tests | corrections regression only |

**The renderer.** There is no way to draw a diagonal in a 3-character cell body
that already holds the room number. Three options, cheapest first: a **legend
line** under the map (`diagonals: (26,24)\ (27,25)\ ...`), stealing the body when
there is no room name (which almost never fires — every B1 diagonal is inside a
numbered room), or two-line cells (a rewrite of `render`, and a 45-row map
becomes 90 lines). Under S the renderer needs nothing at all: the wall is drawn
as the staircase it was converted to, which is arguably more honest for a tool
whose job is telling the DM which way the party can walk.

---

## 5. Q4 — a half-square is not a 10-foot square

`FEET_PER_SQUARE = 10` and `path_report` costs a route at `(len(route)-1) * 10`.
`tools/clock.py` turns those feet into rounds and `campaign/light.tsv` burns oil
against them.

**Do not cost a half-square at 5 feet.** A route through a diagonal square
enters one half and leaves it — one square entered, 10 feet, exactly as today.
Cutting the corner is geometrically about 14 feet rather than 20, but the grid
already rounds every corner that way and has since the first route was costed.
Introducing 5-foot steps would change every distance on the sheet to fix an
error the sheet does not have.

**The one real change is the repeated square.** 0.57% of half-cell shortest paths
enter a square twice, once per half. `len(route)-1` then counts it twice, which
is *correct* — the party really did walk into that square on both sides of the
wall — but the route string prints the coordinate twice and any consumer that
treats the route as a set (`mark_seen`, `world.py`) will double-handle it. Under
the staircase this cannot happen at all.

**The detour guard behaves sensibly under S with a uniform assignment and badly
under a mixed one.** Measured (§2.4): 0 false refusals versus 2,384. And it
already does the right thing on the live map's worst case:

```
party.py move --to 5,27   from (5,28)
    live map:      1 square,  10 ft   -- permitted, and it crosses a wall
    half-cell:     5 squares, 50 ft   -- DETOUR raised, correctly
```

The guard is not the problem. The graph under it is.

---

## 6. Q5 — migration and safety

### 6.1 Would the regression counts move?

| change | DMG | B1 |
|---|---|---|
| baseline (`rebuild.sh` prints these) | 21 of 641 | 5 of 1,196 |
| detection only, as shipped | 21 | 5 |
| **half-cells applied to the detector's own output** | **25 — a REGRESSION** | 5 |
| staircase, uniform assignment | 21 | 5 |
| staircase, all-south assignment | 21 | **12 — a regression** |
| the DMG's `(5,24,V)` corrected to `secret` (part 1 §1.7) | **10 — a FIX** | 21 |

The DMG line is the important one and it was not in part 1. Applying half-cell
nodes automatically to the two squares the Radon test fires on for the DMG loses
**(6,27) (6,28) (7,28) (7,29)** — the area-30 diagonal staircase. `(5,27)` is a
diagonal **passage** carrying legend hatching, not a wall, and splitting it
severs the stairwell.

> **The half-cell model must be driven by an adjudicated list, never by the
> detector's output.** On the DMG the detector's two hits are both known legend
> glyphs and both are false; acting on them costs four squares.

The all-south line says the same thing about the staircase from the other
direction: a wrong side choice seals 7 real squares. Which is *useful* —
reachability cannot see a missed diagonal but it does see a wrongly assigned
one, so the count is a partial guard on the human's bit.

### 6.2 Reachability cannot see a missed diagonal. This can

A missed diagonal wall leaves everything **passable**. Nothing is sealed, so no
connectivity check can ever see it. That is why area 34 was found by a player
standing in it.

What *is* checkable, globally, with no reference map — the property that makes
`dmap reach` worth running:

> **Diagonal debt.** A square shows a 45-degree split in its own floor, and its
> passable boundaries are not contained in one half of that split. The pixels and
> the edge table contradict each other.

It is cheap: `side_classes` and `diagonal_stat` already run in `_measure`. Run on
the live databases as they stand:

| signal | B1 debt | DMG debt |
|---|---|---|
| A. shipped Radon, gate 0.15–0.45 | 8 | 2 |
| B. `side_classes` split (`split_orient`) | 7 | 0 |
| C. Radon **ungated**, rock < 0.90 | **11** | **3** |
| union | **11** | **3** |

```
B1   (4,26) SWNE rock 0.63 passable=NSE   room 11      <- signal C only
     (4,27) NWSE rock 0.72 passable=SE    room -       <- signal C only
     (5,24) (5,25) (5,27) (6,23) (6,28) (7,22) (7,27) (8,28)   areas 10, 11
     (8,21) NWSE rock 0.68 passable=NSW   room 10      <- signal C only
DMG  (5,24) NWSE rock 0.59 passable=NSW   room 28      <- signal C only
     (5,27)  the area-30 diagonal stair   -- known, benign
     (23,18) the boxed-X trap-door glyph  -- known, benign
```

Four things about that table.

**Area 34's four squares carry zero debt.** The staircase corrections paid them
off. So debt is a **burn-down number**: it starts at 11, and every adjudicated
wall reduces it. That is what `rebuild.sh` should print, beside the two
reachability counts.

**Signal C finds three squares neither shipped test can see.** (4,26), (4,27) and
(8,21) are mass-face-style walls at rock 0.63–0.72 — above `DIAG_HI`, so the
Radon gate rejects them — whose `side_classes` come back as a single class or as
an *opposite* pair (`NS`), so `split_orient` rejects them too. All three are on
areas 10 and 11. Part 1 §7 said *"I did not find a place where a 45-degree wall's
mass is only one cell thick with `mixed` on both flanks"*. Here are three.

**The 0.45 gate is not arbitrary, and this measures why.** Of 50 B1 cells in the
0.45–0.90 rock band with a Radon peak ≥ 0.90, **48 already have two or fewer
passable sides** — `classify_edge` sealed them on terrain or on `gap` without
ever knowing there was a diagonal. The gate's upper bound is roughly where the
boundary model starts working again. `(6,26)`, the square between two detected
diagonals on area 10's north wall, is one of the 48: rock 0.54, undetected, and
its S and E boundaries are already `wall` in the raw build. The detector's
recall gap at the top of the band is mostly harmless — but 2 of 50 is not 0 of
50, and both exceptions are in the two rooms that are wrong.

**The DMG's (5,24) is the chamfered corner of area 28** carrying the secret door
into the area-29 treasury, which `README.md` already documents as 11 of the
DMG's 21 unreached squares. The debt check finds it from a completely different
direction. That is corroboration, not coincidence.

Two known-benign DMG entries — the diagonal stair and the trap-door glyph —
mean debt is a **review list, not an assertion**, exactly like `doorcheck.py`'s.
They should be suppressible by name in a key module once adjudicated.

### 6.3 Staging, so a live campaign never runs on a half-migrated map

The party is at **(32,31)**, inside area 33, door spiked shut behind them
(`campaign/party.tsv`, expedition 4 turn 129). They have never entered any of the
13 diagonal squares — checked, all 28 move rows and every route string. So the
migration has no in-flight state to preserve, and the recorded trail up area 34
hugs the north-west side of the wall throughout:

```
25,24  25,25  26,25  26,26  27,26  27,27  28,27  28,28  29,28  29,29  30,29
```

That route is legal under all three models. Nothing that has happened at the
table needs re-adjudicating.

Order, each step separately revertible:

1. **Measure only.** Add the debt check and the staircase-vs-half-cell oracle to
   `diagcheck.py` (§7). Nothing is written to a database. **Both reachability
   counts must be byte-identical after this step**; if they are not, the change
   touched something it should not have. The debt counts (B1 11, DMG 3) are
   recorded as new expected values in `rebuild.sh`.
2. **Review with the player.** Areas 10 and 11, four wall runs, plus the three
   signal-C squares. Ask for the printed outline, as for area 34.
3. **Enter `edge` staircase rows and `member` rows** in `b1_corrections.tsv`.
   One side per **wall run**, never per square (§2.3). This is the only step that
   changes the map the game reads, it goes through the file that always wins, and
   it is revertible by deleting lines.
4. **Re-run and diff.** Areas 10, 11 and 31 change; nothing else does.
   Reachability must hold at **5** — a move to 12 means a side was chosen wrong,
   which is §6.1's all-south result and is a real signal. Debt must fall from 11
   toward 0.
5. **Only if 1–4 prove insufficient**, consider half-cell nodes, on a *copy*, with
   `reach`, `path` and `party.py move` exercised against the recorded route
   first, and with the DMG's 21→25 regression (§6.1) understood and prevented.

`markers.py --apply` is not idempotent and `extents.py` clears `cells.room`, so
corrections are already applied three times in `rebuild.sh`. **Any new writer of
`cells` or `edges` must be slotted into that order explicitly**, not appended.

And separately, on its own commit, with the expected count edited in the same
change: correct the DMG's `(5,24,V)` to `secret` and move `rebuild.sh`'s DMG
expectation from 21 to 10. **Do not bundle it with anything else.**

---

## 7. Q6 — recommendation

> **Fix the connectivity with the staircase, one side per wall run. Build the
> half-cell graph as a read-only ORACLE that audits the staircase, and do not put
> it in the schema.**

The measurements say the staircase is right for this map and this campaign:
it can never route through a wall (§2.2, a theorem with 1.4M confirming
comparisons); with a uniform per-run assignment it is exact for every pair of
ordinary squares (§2.3, 0 of 693,253); it costs nothing downstream (§4, one
column of the blast-radius table is empty); and it uses a correction scope that
already exists and already always wins. Half-cells are exact but they make a
square stop being a place (§2.5), collapse area 11 (§3.4), need a column in a
live database and a column in an append-only campaign log, and regress the DMG
by four squares if driven by the detector (§6.1).

But the staircase's one weakness — the human's side choice — is real, costs up
to 240 feet and 7 sealed squares, and is silent. So build the oracle that checks
it. That is the increment.

### The smallest useful first increment

One flag on one existing file. `diagcheck.py --connectivity`. It writes nothing;
`--db` stays read-only.

1. **Diagonal debt**, over all three signals of §6.2, printed as a count and a
   list. Add signal C (`diagonal_stat` ungated, rock < 0.90) — that is a
   two-line change and it is what finds (4,26), (4,27) and (8,21). Print the
   count next to the reachability counts in `rebuild.sh`: **B1 11, DMG 3**, to be
   burned down, not held.
2. **The oracle.** Build the half-cell graph in memory from `diag_orient`, and
   for each proposed staircase assignment report:
   - squares the staircase would **seal** that the half-cell graph reaches;
   - ordered pairs whose distance the staircase inflates past
     `max(2, straight*2)`, i.e. moves `party.py` would refuse;
   - **pairs the current database understates** — the §0 table, which is the
     number that says how much wall the party can walk through today.
3. **The side proposal.** Print rule A's bigger-half ratio (§3.2) beside each
   square, and say `no opinion` below about 0.60. Group the squares into **wall
   runs** by diagonal adjacency and ask for one bit per run, not per square.
4. **A chain note.** Report, per hit, whether the wall continues into the
   diagonally adjacent square at each end (another diagonal, or rock). On B1 the
   only hit that continues at *neither* end is (24,41) — the single known false
   positive. It is a hint, not a rule: a one-square chamfer legitimately
   continues at neither end.
5. One `rebuild.sh` line, in the review block beside `doorcheck.py`. Nothing
   written to a database, both reachability counts unmoved.

Then, and only then, step 2 of §6.3: review areas 10 and 11 with the player.

### What I would deliberately NOT build

- **Not half-cell nodes, not a `cells.diagonal` column, not a turn-restriction
  table.** §4's table is the argument: they touch `reachable`, `find_path`,
  `path_report`, `room_graph`, `describe`, `render`, `check`, all four functions
  of `extents.py`, `markers.py`'s private flood, the `cell_edges` VIEW,
  `party.py`'s guard and `campaign/party.tsv`'s columns — to buy exactness on
  13 squares whose connectivity a uniform staircase already gets exactly right.
  `party.py` exists to make an illegal move an exception; a bug introduced there
  mid-campaign is worse than the fault being fixed.
- **Not automatic reclassification**, and now with a number: driving half-cells
  from the detector's output regresses the DMG 21 → 25 (§6.1). `doorcheck.py`
  earned "flag and draw, never reclassify" the hard way; this is the same rule
  with the same evidence.
- **Not 5-foot half-squares, and not a change to `FEET_PER_SQUARE`.** §5.
- **Not a `half` column in `campaign/party.tsv`.** Append-only, live, and the
  staircase makes it unnecessary.
- **Not a two-line ASCII renderer.** A legend line under the map, or nothing.
- **Not per-square side choices.** Per **wall run**. §2.3 shows that mixing
  within a run is where every routing error comes from, and it reduces B1's
  outstanding human input from thirteen bits to four.
- **Not a fix for `wide_cells` and the diamond.** Area 11 needs `member` rows
  either way (§3.4). Rewriting the room-vs-corridor rule to handle rotated rooms
  is a separate piece of work with its own evidence to gather, and doing it under
  the cover of this one would put two unvalidated changes into a live map at once.
- **Not curved walls.** Out of scope in part 1 and still out of scope.

---

## 8. What I could not determine — and one thing the brief got wrong

**Area 33 is not a diagonal problem.** The brief lists it with 10, 11 and 34.
Its extent is 5 squares for a barracks the module fills with forty beds, and the
cause is measured and different:

| | |
|---|---|
| diagonal debt in x30–35, y21–33 | **0** |
| the 45-degree band on its north-west flank | mass-face, rock 0.68–1.00, boundaries already `wall` — correctly handled |
| `door` edges in that block | **39**, from drawn beds |
| cells flagged `feature='stairs'` | **15**, from rows of beds reading as treads |
| `room_labels` rows for area 33 | **2**, at (32,31) and (33,31) |
| `33` labels actually printed on the sheet | **4** — a second pair at (32,24) and (33,24), confirmed by page render |

`extents.grow` conducts only through `open` boundaries, so a room fenced by 39
fabricated doors cannot grow, and half its labels are missing from the key. This
is `doorcheck.py`'s failure mode at scale plus a key-module omission. **It will
not be fixed by anything in this document**, it is live right now — the party is
standing in (32,31) — and it deserves its own review pass.

Genuinely undetermined:

- **The true extents of areas 10 and 11.** Same answer as part 1: it needs the
  player to read the printed page. Guessing an outline to make a number look
  better is the failure the notebook exists to prevent.
- **Whether rule A's bigger-half convention is a convention.** 4/4 on one wall on
  one sheet. It could be how this draughtsman inked area 34 and nothing more.
- **Whether the 13 (plus signal C's 3) are all of them.** Ground truth was built
  by adjudicating the detectors' own union. Debt is a better guard than recall
  because it needs no ground truth — but it inherits the same signals.
- **Whether `side_classes` returning an OPPOSITE pair (`NS`, `EW`) is always a
  wall.** (8,21) returns `NS` and is a real 45-degree wall; `split_orient`
  rejects opposite pairs by design, because that pattern is also a corridor
  pinched from both flanks. I did not find a rule that separates them and did not
  look hard.
- **The DMG's area-30 diagonal staircase, (5,27)/(6,28)/(7,29).** Still
  unresolved from part 1, and now with a cost attached: it is why blind
  half-cells lose four DMG squares. Whether the corner-step rule, the `stairs`
  edge kind or a diagonal-wall model is the right description of that square is
  still open, and any model that writes to a database has to decide it.
- **Whether a diagonal square should be `seen`-able in halves.** The party has
  never stood in one, so nothing forced the question.

---

## Reproducing the numbers

Everything above came from read-only scripts over a copy of the two databases
and a cached render of the two pages. Nothing in `mapdb/` was modified and
`rebuild.sh` was not run. The scripts are not checked in; each measurement in
this document names the population it was scored against so it can be redone.
The one figure to re-check first, because the whole recommendation rests on it,
is §2.3's `0 of 693,253` — a uniform per-wall-run staircase must introduce no
routing error between two ordinary squares, or §7 is wrong.
