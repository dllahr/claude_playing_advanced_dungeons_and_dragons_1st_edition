# Lab notebook — things that did not work

A record of approaches tried and abandoned, so they are not tried twice. Each
entry says what was attempted, why it looked reasonable, the measurement that
killed it, and what was used instead.

The README documents what the pipeline *does*. This documents what it doesn't,
and why.

---

## Cell and boundary classification

### Otsu bimodality (η) to separate a wall crossing a square from a mark inside it

**Idea.** A hard ink boundary should split a square's pixels into two tight
populations (η near 1) while halftone stipple and antialiased text smear the
histogram (low η). So η should tell a diagonal rock wedge from a room numeral.

**Why it failed.** These scans are clean line art. *Everything* is sharply
bimodal — essentially every intermediate cell measures η > 0.78, including the
pure-white and pure-black ones where Otsu is finding a meaningless split in a
uniform patch. See `output/dmg/images/05_bimodality.png`: the discriminating
variable in that plot is the colour (border contact), not the y-axis.

**Used instead.** Connectivity. The rock is one huge connected mass; a numeral
is a blob of a few hundred pixels, so keeping only dark components ≥900 px
yields the rock and the remainder is the annotation layer. η is retained purely
as a scan-quality diagnostic.

### `t_solid = 0.25`

**Idea.** A quarter-covered square is mostly rock, so call it solid.

**Why it failed.** A full-width 45° corridor leaves about a quarter of a square
open, and calling that solid severs the corridor into disconnected pieces. Three
DMG squares sat at exactly 0.25 and the passage came out in fragments.

**Measurement.** 1006 of 1680 DMG squares measure *exactly* 0.000. Anything with
measurable floor in it is not rock.

**Used instead.** `t_solid = 0.05`.

### Median rock thickness alone to decide a boundary

**Idea.** Thick boundary = wall, thin = printed ruling.

**Why it failed.** It answers "how thick is the rock here", which is the wrong
question where two half-filled squares meet — rock covering *part* of a boundary
still leaves a way through. It severed seven passages on the DMG sheet that
plainly connect on the page.

**Used instead.** `gap`: the fraction of the boundary length the rock does *not*
block. Rock must **span** a boundary to close it.

### Letting stairs fall through to `wall`

**Not an idea so much as an omission**, but the most expensive single bug in the
project, so it is recorded here.

A staircase is drawn as a ladder of treads. That reads as *thick* to the
thickness test and as a *stack of doors* to the hole test, so both rejected it
and the boundary fell through to the `wall` default. Stairs are a way through.

**Cost.** B1's entrance corridor came out sealed off from the other 1,200
squares of the level: 30 reachable of 1,231. Adding `stairs` as a passable edge
kind took it to 1,161, and improved the DMG from 24 unreachable to 21.

**Lesson.** A classifier with a default branch will silently absorb every case
nobody thought about. The reachability check is what surfaced it.

---

## B1's dotted interior features

B1 draws floor mats, a raised stage and a rock outcrop as **dotted rectangles**
inside rooms. The extractor reads them as walls and seals the squares off. Four
attempts, all failed; this is now believed unfixable from the image.

### Connectivity — "a drawn rectangle will be its own rock island"

**Idea.** The trick that separated rock from ink should separate a feature drawn
inside a room from the wall network it is not part of.

**Why it failed.** **98.7% of B1's rock is a single connected component.** The
printed grid rulings run across the entire sheet and connect everything to
everything. Tested on known dotted edges and known real walls: all component 3.

### Higher DPI to resolve the dots

**Idea.** The dots have merged at 200 dpi; render at 400 and they will separate.

**Why it failed.** At 400 dpi the dotted boundaries still show no gaps at all
(min thickness 12–16 px along their length). The source scan has already merged
them — this is not a sampling-rate problem, the information is gone.

### Coefficient of variation along the boundary

**Idea.** A dotted line should ripple along its length; a wall should be flat.

**Why it failed.** The measurement came out *backwards* — dotted 0.35–0.56,
"walls" 0.77–2.33 — because the control group was wrong. The edges picked as
"real walls" were mostly open boundaries with a spike at one end from a
perpendicular wall. **Lesson: sample the control group from the classifier's own
output, not by eye.**

### Thickness statistics against the full wall population

**The honest test**, done properly with 545 genuine wall edges between two open
squares:

| | min thickness along the boundary |
|---|---|
| real walls (n = 545) | p25 = 8, p50 = 8, p75 = 8 |
| the dotted features | 6 – 8 |

Indistinguishable, and 97.8% of real walls sit in the same range.

**Conclusion.** This is information the image does not carry, not a threshold
that needs tuning. It has to come from the module text, which describes area
37's mats as "20' by 20'" — exactly the 2×2 footprint the extractor sealed off.

---

## Finding secret and concealed door markers

### The ink layer

**Idea.** The markers are printed letters, so they should be in the annotation
layer with the room numbers.

**Why it failed.** **Every known marker measures ink = 0.000.** Each is drawn
*astride* the wall it annotates, so it touches the rock and the connectivity
pass swallows it whole. The ink layer cannot see them at all.

**Used instead.** Thin-stroke morphology — print is thin where structure is a
mass, so opening the rock and taking the difference recovers the glyph.

### Edge-centred template matching on raw greyscale

**Idea.** The glyph is centred on the edge it annotates, so score a patch
centred on every boundary against patches from known markers.

**Why it failed.** Raw NCC is dominated by the wall and corridor structure
filling the patch, not by the glyph. Leave-one-out ranks (of 3,360 edges): the
two S markers ranked 1 and 2 — but only because they match *each other* — while
the concealed-door C markers ranked 109, 163, 282, 835 and 1566.

### Matching S and C against each other with no negative class

**Idea.** Two templates from the legend, sweep rotation, take the best match.

**Why it failed.** With nothing else to match against, every digit is assigned
to whichever letter it resembles more — a rotated "2" looks more like an S than
like a C, so it wins by default. **23 of 59 marks came back as secret doors.**

**Used instead.** A negative class learned from the map itself: the verified
ROOMS table says the marks in area 23's square are a "2" and a "3", so digit
templates come free. False positives fell to one. Also asymmetric rotation —
digits matched upright only, symbols swept through 24 angles — since printed
numbers are never rotated and legend symbols routinely are.

### Legend-template NCC for B1's door subtypes

Two attempts, both abandoned. B1's legend distinguishes DOOR, SECRET DOOR,
FALSE DOOR and ONE-WAY SECRET DOOR, and the legend prints them at map scale, so
this looked like the ideal use of a template.

1. **Full 87×41 legend symbol.** Scores capped at **0.53** across all 3,360
   edges. The template carries the wall running off both sides, and that context
   varies everywhere on the map.
2. **Tight 38 px crop plus a plain-wall negative class learned from the map.**
   Better structured, still wrong: it claimed **388 secret doors** on a level
   that has perhaps a dozen.

**Status: unsolved.** B1's door subtypes are still unclassified. The secret
doors currently in `b1.sqlite` were found by the thin-stroke detector and
confirmed by reachability, not by reading their shape.

---

## Reading area numbers

### Learned digit-height filter applied to all blobs

**Idea.** Type on one sheet is one size. B1's digits cluster hard at 18–19 px
against noise spanning 8–30, so filter blobs to the modal height.

**Why it failed.** The mode was taken over *all* blobs, and thin-stroke recovery
admits about five times as much noise as signal — 339 noise components against
28 real ones. The noise won the vote and the filter removed the digits.
**B1 localisation fell from 89% to 11%.**

**Partial fix.** Learning the height from the ink layer alone (which is much
cleaner) recovers it to 76% — still worse than not filtering at all. The option
is in `eval_labels.py`, off by default.

**Lesson.** When learning a parameter from data, check what the data is mostly
made of first.

### Tesseract on B1's digits

Not abandoned, but recorded as unsolved: reading holds at ~30% on B1 (~67% on
the DMG) regardless of localisation improvements. B1's digits are 18 px tall in
blue print. The learned-template classifier in `symbols.py` reached 51/54 on the
DMG and is the obvious next thing to try.

---

## Room extents

### Taking the first dimension in a description as the room's size

**Idea.** Descriptions state room sizes, so parse the first `20' by 20'` in each
area's text and use it to check the extracted extent.

**Why it failed.** Descriptions size their *contents* too, and often first. B1's
area 37 gives "measuring 20' by 20'" for a stack of floor mats, and area 22
gives "10' x 20'" for a rock outcropping in a chamber the text calls the former
"showplace of the entire stronghold". Both would have been read as room sizes
and both would have fired a false disagreement.

**Used instead.** A dimension only counts when a room word ("room", "chamber",
"cellar", "smithy"...) sits within 45 characters of it. That keeps "This 20' by
20' room is used for..." and drops the mats.

**Residual.** Area 22 still passes the filter and still looks wrong -- extent 16
squares against a stated 2. It is left in deliberately: when the two readings
disagree this loudly, it is evidence about which reading is at fault.

## Furniture drawn inside rooms

Not a failed approach but a failure mode worth naming, because it produced the
two hardest errors to find and it is the same root cause as the dotted features.

B1 draws the contents of its rooms — tables, beds, equipment. Those drawings sit
inside a room and get classified as structure. Areas 17 and 18 each lost part of
themselves to one, and **they failed differently**:

| area | what the furniture became | how it was found |
|---|---|---|
| 17 | a fabricated **wall** (thick = 10 px) | size cross-check |
| 18 | a fabricated **door** (hole = 47 px) | size cross-check |

**The important half is area 18.** A fabricated *wall* seals squares off, so the
reachability check sees it. A fabricated *door* is still passable — connectivity
is undisturbed and every square remains reachable — so **no reachability check
can ever find one**. It only showed up because the room came out the wrong size.

**Lesson: the two checks are complementary, not redundant.** Reachability finds
walls that should not be there; the extent/size check finds doors that should
not be there. Neither subsumes the other, and a map that passes only one is not
validated.

Both were fixed as corrections rather than by classifier work, for the reason
recorded above under the dotted features: a drawing inside a room is not
distinguishable from structure at this scan resolution.

## What the checks cannot see — and the third reading

Reachability and the room-size check are complementary, but B1 showed that
together they are still not enough.

**Neither can find a secret door in a room that has another way in.** Nothing is
sealed, so reachability is untroubled; the room comes out the right size, so the
extent check is untroubled. Area 9's secret door read as a plain wall at
thickness 14 with no glyph proposed at all, and would have gone unnoticed
indefinitely.

**The module text is a third independent reading, and on B1 it is the only one
that works for this.** A sweep of the level-1 descriptions for "secret door",
"false door" and "one-way" named eight areas carrying doors the image extraction
had wrong or missing:

| | text says | extraction had |
|---|---|---|
| areas 8/9, 10, 24, 25, 32 | secret doors | 3 secret edges, one of them right |
| areas 17, 35, 36 | false doors | **zero** false doors |

Area 10 is the sharpest case: a 32-square storeroom the module calls *hidden*,
which the map had standing wide open.

**Lesson for a new map: run the text sweep FIRST** and treat the image
extraction as the thing being checked, rather than the other way round. That
inverts the order used for the DMG, where the image was reliable and the text
was thin.

**And know when to stop.** Areas 10, 24 and 32 were left unplaced rather than
guessed: the candidate glyphs are there, but the text says which room, rarely
which wall, and inventing an edge to make a number look better is the failure
this notebook exists to prevent.

## Process mistakes

### Writing classifiers before reading the map's own legend

Four classifiers were written before anyone looked at the DMG's LEVEL KEY on the
facing page. It defines `S` = secret door, `C` = **concealed door** (which had no
handling at all), boxed `X` = trap door, boxed `S` = secret trap door, even
hatching = stairs **up**, tapering = stairs **down**, and the stream glyph.
Several early misreadings were symbols the book defines explicitly.

**Rule: read the legend first.** B1's legend then turned out to differ — no
concealed doors, but false doors and one-way secret doors, and its doors are
white shapes *reversed out of* the wall band where its secret doors are dark
glyphs *on* it.

### Tools re-rendering the page with their own defaults

`markers.py` re-rendered with the mean channel and no deskew while B1's database
had been built from a red-channel, deskewed render. The grids disagreed by up to
a quarter of a square, so **every marker it found was attributed to the wrong
edge** — and it looked like success, reporting markers applied and regions
opened.

**Fixed structurally**, not with a flag: `levels` now stores `pdf`, `page`,
`dpi`, `channel` and `deskew_deg`, and every tool reads them back. Re-running
afterwards applied *four* markers instead of seven and reached more squares —
three of the original seven were spurious.

### Comparing runs across a mutated database

`markers.py --apply` writes to the database, so it is **not idempotent**: a
second run sees the regions the first one opened and behaves differently. Two
"before and after" comparisons were meaningless before this was noticed.

**Rule: always rebuild before applying.**

### Building an exception around an unverified coordinate

Area 39 was the one DMG region reachability could not explain, and it was
treated as a genuine exception for several sessions. The hand-made label table
later showed **its anchor was two squares out** — (18,0) recorded against a real
position of (17,1)–(18,2).

### A flat namespace for sub-locations

DMG areas 1 and 2 each have an "A" and a "B". Keyed as bare letters, the second
of each silently overwrote the first and **2B was absent from the key entirely**
until the ground-truth table surfaced it. Sub-locations are now `1A`, `2B`.

## Drawn furniture on a grid line reads as a door — four found in one session

**Status: not solved by any classifier. Caught only by measurement and by play.**

Expedition 4 turned up **four** fabricated doors in three consecutive furnished
rooms, all the same mechanism: an object drawn on the sheet happens to sit on a
grid boundary, its outline encloses white, and the topological door test fires.

| edge | classified | thickness | hole | what it really was |
|---|---|---|---|---|
| (31,8,V) | door | 13 | **283** | the drawn dais in area 27 |
| (31,9,V) | door | 14 | 95 | the second throne on that dais |
| (32,9,H) | door | **2** | 95 | the dais outline's north arc |
| (32,7,H) | door | **2** | 69 | the dais outline's south arc |
| (26,8,H) | door | **2** | 60 | a printed ruling in area 28 |

**Thickness is the discriminator, and it works in both directions.** B1's genuine
doors measure **4–11**; its walls measure **7–18**; its printed rulings measure
**0–3**. Anything classified `door` outside 4–11 deserves the page render:

- **too thin (0–3)** — it is a ruling with something drawn over it
- **too thick (12+)** — it is a wall with a furnishing drawn on it

The 283-hole on the dais is nearly twice the largest genuine door on the level.

**Why neither automated check catches these.** Reachability cannot: a fabricated
door stays *passable*, so nothing is sealed. The extent-vs-stated-size check
cannot when the room has another way in. What caught all four was **arithmetic on
the classifier's own output** plus, twice, the play record — once because
`dmap.py path` reported the party "crossing a door" walking across open floor,
and once because an internal door between two squares that both opened into the
same room made no architectural sense.

**Do not try to fix this with a smarter door test.** It was tried: the hole test,
the aspect-ratio test and the box radius are all already tuned, and every one of
these five passed them. The fix is a **flag**, not a filter — list every `door`
whose thickness falls outside 4–11 and render those pages. 


**CORRECTION, same session.** The first version of this entry said "there were
five on the whole of B1 level 1". That was the number I had FOUND, not the number
the flag produces. Running it properly gives **48 of level 1's doors outside the
4-11 band**, with thicknesses from 1 to 24. The 4-11 band was inferred from about
four examples; it is not a measured distribution.

So the flag as first stated is far noisier than claimed, and 48 page renders is
not a ten-minute job. What survives:

- the **five confirmed fabrications** all sat outside the band
- the **tails carry the signal**: thickness **1-3** is a printed ruling, not a
  wall at all; thickness **18+** is a heavy wall with something drawn on it. The
  middle of the excluded range, 12-15, holds plenty of edges that are probably
  genuine doors on slightly heavy line work.

**Before relying on this, plot the thickness distribution of edges classified
`door` against those confirmed genuine in play.** Until then it is a triage
order, not a verdict: render the 1-3s and the 18+s first.


## Furniture that measures exactly like a door

**Status: no automated discriminator exists. Page render or play record only.**

The thickness flag (see the entry above) catches drawn objects that sit on a
grid ruling or on a heavy wall, because those land outside B1's genuine 4-11
door band. It does **not** catch a rounded rectangle of furniture drawn *beside*
a wall at ordinary line weight.

Area 24, the Mistress' Chamber, produced two of these on 2026-08-28:

| edge | classified | thickness | hole | actually |
|---|---|---|---|---|
| (32,2,H) | door | **9** | 134 | the drawn nightstand/chest |
| (31,3,V) | door | **10** | 134 | the same furniture group |

Compare the room's ONE genuine door at (33,2,H): thickness **7**, hole **187**.
The fabrications sit *closer to the middle of the genuine band than the real
door does*. There is nothing in thickness, hole, aspect or box radius that
separates them.

**What actually found them:** the player read the printed map. Before that, the
room had also been HALVED — the drawn walnut bed made (32,4) read as 36% rock,
which fabricated two walls and a door and stopped the 2x2 extent test at half
the room's length.

**The lesson is not a better classifier.** It is that **a furnished room's
boundaries cannot be trusted from the extraction alone**, and the cheap check is
to render the page for any room the party is about to enter and spend a minute
on it. Five rooms have now produced fabrications: 9, 24, 25, 27, 28 — every
heavily furnished room on the level, and no unfurnished one.


## THE TEST THAT ACTUALLY WORKS: a door crosses the wall, furniture does not

**Proposed by the player 2026-08-28. Verified against the sheet. IMPLEMENTED
2026-08-28** as `extract.door_suspect` + `doorcheck.py`; results and the two
false starts are recorded at the end of this section.

Every fabricated door found this session shares one property, and every genuine
door lacks it:

> **A real door glyph STRADDLES the wall band — white shows on both sides of the
> wall centreline, because the door goes THROUGH the wall.**
>
> **Drawn furniture sits entirely on ONE side of it.** It is in the room. It
> never crosses into the space beyond, because there is nothing to cross into.

Checked on the south corridor at 500 dpi: the two genuine doors at (31,2,H) and
(33,2,H) each show a rounded rectangle spanning the wall band with floor visible
above and below it. The fabrication at (29,2,H) is a rounded rectangle lying
wholly on the room side, with unbroken wall band beneath it.

**Why this beats everything tried so far.** Thickness fails — the area 24
fabrications measured 9 and 10 against a genuine door's 7, dead inside the band.
Hole size fails — 134 against 187. Aspect fails. Box radius fails. All of those
ask "what does the glyph look like"; this one asks **"does the wall actually
have a hole in it"**, which is the question that was always being answered by
proxy.

**How to implement it.** For each edge classified `door`, take the rock mask
along the wall centreline and a band a few pixels either side. A genuine door
shows the enclosed white region present on BOTH sides of the centreline; a
furnishing shows it on one side only, with continuous rock on the other. That is
a two-sided occupancy test on the existing masks — no new imaging, no new
thresholds, and it should be checkable against every door on level 1 in one pass.

**Validation set is already here**: five confirmed fabrications (areas 9, 24, 25,
27, 28) and every door the party has physically walked through.

### Implementation, 2026-08-28 — and two false starts worth keeping

The plan above says "enclosed white on both sides of the wall **centreline**".
Implemented literally, **it does not work**, twice:

**Attempt 1 — largest hole component, split about the box centreline.** Four
doors the party has physically walked through scored **0.000**, identical to the
furniture. Cause: a door glyph straddling a wall has its interior *cut in two by
the wall bar*, so the largest single component lies wholly on one side. The
metric was measuring the exact opposite of the thing it was named for.

**Attempt 2 — all hole components, split about the box centreline.** Still
overlapping: fabrications ran to 0.475, genuine doors down to 0.000. Cause: the
*nominal grid boundary is not where the wall bar is*. A few px of grid-fit and
deskew error is a large fraction of an 8 px glyph, so the sign of the split was
noise.

**What fixed it was rendering the crops and looking at them** — 16 tiles, doors
and known fabrications side by side. Two things are obvious on the page and
neither is a centreline test:

1. Most fabrications have **no wall at all** — the ovals and beds of areas 27
   and 28 sit on a 2 px graph-paper ruling. A door is a hole in a wall; if there
   is no wall there is no door. This is not in the original plan and it catches
   the largest group.
2. The rest sit **beside** a real wall bar rather than on it.

So the implemented test measures the wall **on the flanks, outside the glyph**,
and then the glyph's offset from *that measured bar*, not from the grid line:

| metric | what it is | door | furniture |
|---|---|---|---|
| `wall` | median perpendicular rock on the boundary 0.55–1.05 cells either side of the glyph | 8–26 px | 2–4 px if drawn in a room |
| `offset` | distance from the glyph's enclosed-white centroid to that bar, in cells | ≤ 0.13 | 0.14–0.35 |

**`thick` never worked because it samples the glyph.** With `half=0.30,
trim=0.25` the band is 0.5 cell long centred on the boundary — entirely inside
the door box. It was measuring the drawing, never the wall. That is the whole
reason area 24's fabrications came out *thicker* (9, 10) than the genuine door
beside them (7).

**Result on B1 level 1** (`--min-wall 5.0 --max-offset 0.14`):

| | count |
|---|---|
| doors the party has physically walked through, kept | **7 / 7** |
| confirmed fabrications rejected | **9 / 16** |
| fabrications surviving the sieve | 6 |
| fabrications never called a door in the first place | 1 |

Across the whole page: 180 door calls, **105 suspect**. A random sample of 18
suspects rendered as crops is **furniture in every single tile** — crates,
barrels, tables, beds, drawn circles. B1's upper level is heavily furnished well
beyond the explored band, so most of those 105 are real fabrications waiting in
rooms the party has not reached.

**It is a sieve, not a classifier, and it is deliberately not automatic.** The
`ok` sample also contains obvious non-doors — scenery curves, shelving, an `S`
glyph. The two failure modes are not symmetric: a fabricated door invents a
passage the party can be walked down, a missed door merely seals a room until
someone checks. So `doorcheck.py` **flags and draws**; the verdict is human and
goes in `b1_corrections.tsv`, which always wins.

Run it on every new level and **read the contact sheet** — that is the step that
found all six of these rooms, and it found them faster than any number did.

### Known limitation, found in play 2026-08-28: SHORT walls give false positives

`(23,6,V)`, the real door into area 29, is flagged **"no wall"** — flank
thickness 2.0 px. It is a genuine door: the 200 dpi render shows an unmistakable
rounded rectangle straddling a heavy vertical bar, and `offset` agrees at
**0.09** with `hole` 193, both squarely door-like.

The cause is structural. `_flank` samples the boundary 0.55-1.05 cells to either
side of the glyph. Where the wall is only ONE SQUARE long -- a short jamb between
two openings -- both flanks land in open floor and report a graph-paper ruling.
The test asks "does the wall continue past this door", and for a door in a stub
of wall the honest answer is no.

**Reading the two metrics together is what works:**

| | `wall` | `offset` | verdict |
|---|---|---|---|
| genuine door in a long wall | high | low | door |
| genuine door in a SHORT wall | **low (false alarm)** | **low** | door -- trust `offset` |
| furniture against a wall | high | high | furniture |
| furniture in open floor | low | high or unmeasurable | furniture |

So a `no wall` flag ALONE is weak evidence; a `one-sided` flag (a bar was found
and the glyph is off it) is strong. When only `no wall` fires and `offset` is
under about 0.10, look at the crop before touching anything -- that combination
is a door in a stub wall more often than it is furniture.

This is exactly why `doorcheck.py` flags rather than reclassifies.

### Area 29 CAPTAIN'S CHAMBER — the seventh shrunken extent, 2026-08-28

Found the same way as the other six, mid-play. The room is **30 x 20**
(x24-26, y5-6); the extractor had it as 4 squares because furniture drawn on
(26,5) made the square read `mixed` and an interior furnishing at `(26,5,H)` was
read as a door. Three fabrications on its south wall alone:

| edge | was | measured | truth |
|---|---|---|---|
| (25,4,H) | stairs | thick 13, slots 1, hole 89, offset 0.15 | a drawn chest against the inside of the wall |
| (26,4,H) | door | thick 13, wall 12.5, **hole 160** | furniture. **Hole and thickness are both door-perfect** -- only `offset` 0.22 catches it |
| (26,5,H) | door | thick 1.0, wall 1.0 | a furnishing in the middle of the room floor |

`(26,4,H)` is the single best argument for the one-sided test: hole 160 sits
inside the genuine range of 95-187, and thickness 13 is heavier than most real
doors. Every earlier discriminator passes it. Only "is it ON the wall bar" fails
it.

Rooms with fabrications now: **9, 23, 24, 25, 27, 28, 29** — still every
heavily furnished room on the level, and still no unfurnished one.

## The north-east quadrant: DIAGONAL WALLS defeat a boundary-based model

**Found in play 2026-08-29, round 1221, with the party standing in it.**

`extents.py` gave area 34 **41 squares spanning x24-31, y22-31** — and the 200 dpi
render shows the Room of Pools' own lettered markers h(27,22), i(27,24), k(29,22),
l(29,24), m(29,26) sitting inside that block. Two different rooms, one extent.

**First-pass analysis, flood fill from (24,23) crossing only OPEN boundaries,
measured raw rather than read off the database:**

- **103 squares, bounding box x22-31, y14-31.** It leaks straight through the
  Room of Pools and out the far side. There is no enclosing boundary to find.

**Why: the walls in this quadrant are DIAGONAL, and a diagonal wall lies on no
grid boundary at all.** The rock is *inside* the squares, not on the edges
between them, so every boundary measures thin and open and the fill runs through
what is plainly a wall on the page. Traced as cell-interior rock:

| the band | squares |
|---|---|
| solid | (24,25) (24,26) (25,26) (26,27) (26,28) (27,28) (28,29) (31,28) (32,29) |
| mixed, rock cutting the square | (24,24) (25,25) (26,26) (27,27) (28,28) (29,29) (29,30) (29,31) |

That is a single 45-degree band running from about (24,24) up to (29,31).

**This is a model limitation, not a threshold to tune.** `edge_stats` asks "how
much rock lies along this boundary"; a diagonal wall answers "none" while
completely blocking passage. The schema already carries a `diagonal` feature for
45-degree *passages* — the reachability rule that lets two `diagonal` cells share
a corner — but there is **nothing for a diagonal WALL**, which is the opposite
problem: two cells that must NOT connect despite an open boundary between them.

**What IS reliable here.** Boundary measurement still works where walls are
orthogonal, and door detection is unaffected. Six door edges bound this region:

| edge | note |
|---|---|
| (23,23,V) | the door the party opened, verified |
| (25,19,H) | |
| (27,23,H) | |
| (29,26,V) | |
| (30,21,V) | |
| (31,31,V) | the second exit the player identified from the printed map |

And the party's immediate space is firmly walled east: **(25,22,V) thick 9,
(25,23,V) thick 10, both gap 0.00.**

### RESOLVED, same session, with the player reading the printed map

The player documented area 34 square by square. It is **31 squares**, not 41: a
short corridor from (22,19), a 2x2 antechamber at (24,22)-(25,23) where the party
is standing, a **20 ft wide diagonal chamber** running SW to NE in six rows of
"half, full, half", and a 2x2 at (30,30)-(31,31). Two exits: the door west of
(24,23) and the door east of (31,31) — matching the module's own "the second exit".

**Their description matched the measurements exactly.** The solid cells already
traced — (24,25) (25,26) (26,27) (27,28) (28,29) — are precisely the diagonal's
north-west wall, and none of them fall inside their outline.

**Why it leaked — and the first explanation here was WRONG.** This was written up
as "the SE wall is drawn thinner than a normal wall". The player corrected it:
it is a **regular-thickness wall that runs at 45 degrees**. Those are not the
same claim, and the second one is the useful one.

A normal wall crossing a grid boundary diagonally covers only a fraction of that
boundary and presents its width along the wrong axis, so an axis-aligned
measurement reports it as thin AND gappy — the exact signature of a graph-paper
ruling. The numbers below are not a thin wall; they are what a **normal wall
measured in the wrong frame** looks like. Only FIVE boundaries had to be forced:

| edge | measured |
|---|---|
| (26,23,H) | thick 3.0, gap 0.62 |
| (27,24,H) | thick 5.0, gap 0.20 |
| (27,25,V) | thick 2.5, gap 0.60 |
| (28,25,H) | thick 3.0, gap 0.55 |
| (29,27,V) | thick 2.0, gap 0.65 |

Lowering the global threshold to catch them is NOT the answer — 6.0 was measured
against the whole population and separates rulings from walls everywhere else on
the sheet. And it would not be a fix even if it were safe: the measurement is
being taken in the wrong frame, so a different threshold on the same wrong number
would only trade these five misses for false walls elsewhere.

A design study of proper diagonal-wall handling — detection and model — is
commissioned separately; see `mapdb/DIAGONAL_WALLS.md` when it lands.

**Implemented:** a new `member` correction scope (`build.apply_corrections`)
assigns one square to a room by hand. `extents.py` CLEARS `cells.room`, so
`rebuild.sh` now applies corrections a **third** time, after extents. Tests in
`tests/test_corrections.py`.

**Result:** flood fill from the party's square now returns **exactly the 31
documented squares** and **exactly two doors**. Reachability held at 5/1196.

A sixth fabricated door fell out of the same check: `(29,30,V)` was a third exit
the player says does not exist, and `doorcheck` agreed — offset **0.23** against
**0.08** and **0.13** for the two genuine ones. Corrected.

**The lesson is the two-readings rule, again.** The image alone could not give
this room; the player's independent reading could, and the two agreed everywhere
except the five thin edges — which is exactly the signal a second reading is for.


## OPEN — a possible FALSE STAIRS at the kitchen's west end (2026-09-03)

`(11,19,H)` and `(11,20,H)` are both classified **stairs** (thick=11/hole=111 and
thick=9/hole=146, confidence 5 each), and `(11,20)` carries terrain `mixed [stairs]`.

**The module text for area 2 mentions no stairs at all.** It describes **two cooking
pits at the southwest corner**, each about 3 ft deep and large enough for a deer,
plus a chimney. At 8x there is a large **semicircular arc** in (11,19) and heavy
drawn features along the room's south side.

**Hypothesis: the pits (and/or a domed oven) are being read as stairs.** Same class
of error as furniture-read-as-door, different glyph. NOT yet verified and NOT
corrected. The party has not seen it — it sits at the edge of their light.

**A feature audit is warranted after the door audit:** sweep every `stairs` call on
level 1 against the module text, the way the door calls were swept. The DMG LEVEL
KEY defines stairs glyphs (even hatching = up, tapering = down) and rotation-aware
matching is required.

### CONFIRMED BY THE PLAYER 2026-09-03 — apply after the door audit lands

> *"no stairs in this room."*

The player's own reading of the printed map is the arbiter for B1 extents and
features, as it has been for areas 34, 33, 5, 29, 3 and 2. **`(11,19,H)` and
`(11,20,H)` are NOT stairs** and `(11,20)`'s `[stairs]` feature is false. They are
the two cooking pits (and the chimney draw) of area 2.

**HELD, not applied** — a door audit is reading b1.sqlite right now and a rebuild
mid-audit would pull the map out from under it. Apply with the audit's own
corrections in one rebuild, then re-run reach (expect 6/1197) and the 367 tests.

Open question for the feature audit: whether `(11,19)` is INSIDE area 2 (making
the row 19/20 boundary at x=11 `open`) or outside it (`wall`). The pits sit at the
room's south-west corner per the module text; the boundary kind follows from that
and should be settled off a render, not guessed.

## 2026-09-14 — adjudicating a BORDERLINE boundary in play, and a wrong turn

Checking the west wall of area 37 mid-session, the quick ink-mean test came out
at **0.31 against a 0.35 threshold** — too close to act on. Two lessons.

**The wrong instrument, tried first.** I reached for *continuity*: sample a
narrow window on the boundary, take the darkest pixel per row, and call it a
wall if every row is inked. **That misclassifies every open boundary on the
map**, because *B1 rules a light grid over its floors* — there is ink on every
ten-foot line whether or not there is a wall there. It duly called a boundary the
party had walked through a wall.

**The right one is THICKNESS**, which is what `extract.py --t-thick 6.0` already
measures and what the `thick=` figures in `edges.notes` record. Print the column
profile and read it:

```
(19,31,V) open floor   0  0  0  0  0  0 .2  1 .7  0  0  0  0     2px = grid ruling
(16,32,V) open floor   0  0  0  0  0 .3 .9 .4  0 .3 .6 .8 .6     ruling + mat stipple
(14,34,V) a WALL       0  0  0 .1 .6  1  1 .9 .9 .9 .9  1  1     10px band
```

**Why the mean was borderline:** a 2-px ruling in an 11-px window averages ~0.15
and a 9-px wall ~0.7, so the mean normally separates them cleanly. Here the
**stippling of the 20'x20' woven mats** sat just inside the room and dragged the
window average up to 0.31. *Room texture adjacent to a boundary inflates the
mean; it does not thicken the line.*

**Procedure when a mean lands between about 0.25 and 0.45: print the profile.**
Do not reach for a new statistic in the middle of a session — the existing one
has a known failure mode and the profile shows it directly.
