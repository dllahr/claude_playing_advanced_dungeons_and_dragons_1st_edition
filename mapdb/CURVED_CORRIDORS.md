# Curved corridors — why a grid narrates them as a junction

**Player-caught at the table, day 99, 2026-09-19:**

> *"This is a problem with our mapping framework relying on a grid — the
> corridor only goes in one direction, it actually curves around in a
> half-circle (or half-ellipse to be more precise). The top of the curve is
> (9,37) and (10,37) when it is running east-west, then it continues to curve
> until it reaches (6,34) where it is running north-south again."*

He was right, and the database already agreed with him. The failure was in how
the database gets **read**.

---

## The failure, in one sentence

**`dmap at` reports four compass exits. A curve has no compass direction, so its
discretisation comes back as a T-junction with walls — and the DM narrates two
ways on where the map has one.**

That is exactly what happened. The party stood at (13,35), `dmap at` returned

```
N  open  -> (13,36) open
W  open  -> (12,35) open
```

and it was narrated to the player as *"two ways on … the passage carries on
north, and the corridor opens west."* Both of those squares are **the rock inside
the bend.** There was one way on and it curved.

---

## The arc, as measured

B1 upper level. A 10-foot corridor sweeping a half-ellipse around **area 12, the
library**, which sits inside the arc at x 9-11, y 32-34.

| leg | squares | open fraction | step to next |
|---|---|---|---|
| right, N–S | (13,34) → (13,35) | 1.00 → 0.62 | N |
| bend | (13,35) → (12,36) | 0.62 → 0.95 | **diagonal NW** |
| bend | (12,36) → (11,37) | 0.95 → 0.53 | **diagonal NW** |
| **top, E–W** | (11,37) (10,37) (9,37) (8,37) | 0.53 **0.97 0.97** 0.64 | W W W |
| bend | (8,37) → (7,36) | 0.64 → 0.99 | **diagonal SW** |
| bend | (7,36) → (6,35) | 0.99 → 0.91 | **diagonal SW** |
| left, N–S | (6,35) → (6,34) | 0.91 → 1.00 | S |

**The squares inside the bends, which are NOT ways on:**

| (13,36) | (12,35) | (11,36) | (12,37) | (7,37) | (8,36) | (6,36) | (7,35) |
|---|---|---|---|---|---|---|---|
| 0.00 | 0.23 | 0.37 | 0.00 | 0.01 | 0.23 | 0.07 | 0.06 |

Four of the arc's eleven steps are **diagonal**, and (11,37) and (8,37) are
already flagged `passage='diagonal'` by the detector — this is the shipped half
of `DIAGONAL_WALLS.md` meeting the *unimplemented* half,
`DIAGONAL_CONNECTIVITY.md`.

---

## How these numbers were checked, because the first two attempts were wrong

Two renders were produced with a wrong grid mapping before this one. The first
was mirrored (I assumed image rows ran the same way as dungeon y); the second was
off by one cell in both axes. Both **looked plausible** and both would have
produced a confident wrong map correction.

**The convention, from `extract.py` — read it, do not re-derive it:**

- `Grid.dungeon_y`: **dungeon y = ny − 1 − j**, where `j` is the row index from
  the top of the page. y increases NORTH; image rows increase south.
- Dungeon **x is the 0-based column index** directly.
- Cell pixel box: `x0 + x*px … x0 + (x+1)*px`, `y0 + j*py … y0 + (j+1)*py`.
- Grid parameters live in `levels.notes`, e.g.
  `Grid(x0=85.3 px=40.35 nx=37 | y0=91.9 py=40.05 ny=45)`.
- Edges, from `schema.sql`: **`V` is the EAST side of (x,y)**, separating it from
  (x+1,y); **`H` is the NORTH side**, separating it from (x,y+1).

**And then verify the mapping numerically rather than by eye.** Re-measuring the
white fraction of every cell and comparing against the extractor's own stored
`open=` values gave **median absolute error 0.009 across 1,665 cells**. A
mirrored or off-by-one grid does not come close to that. *One number decided
whether the whole reading was trustworthy, and it cost one script.*

---

## What was actually broken in the data

**Eleven of the arc's twelve edges were already open** — two of them corrected by
hand in earlier sessions, `(12,35,V)` with hole=331 and `(6,35,V)` with hole=241,
both at confidence 10. Exactly **one** link was missing:

```
edge 7 35 H   wall   confidence 3   thick=12 hole=0
```

With that one wall in place, `dmap path (13,35) → (6,34)` routed **600 feet
through a secret door** instead of 120 feet round the curve. Opening it:

```
(13,35) -> (6,34):  12 squares, 120 feet
```

**Its failure signature was already documented two bends away.** The day-95 audit
of `(6,36,H)` reads: *"this is not a dressed ruled wall, it is the edge of a
LARGE MASS OF NATURAL ROCK with a curved irregular boundary, which is exactly
what an extractor built to measure straight ruled bands scores badly."*
`thick=12 hole=0` at confidence 3 on a curved boundary is that same artifact.

Opening an edge is **monotonic for reachability** — it can only connect, never
isolate — so this correction cannot cause a reach regression. 204 mapdb tests
pass; unreached is 8 of 1,199 walkable, and one of those, (6,36) at 0.07 open, is
rock the day-95 audit already confirmed solid.

---

## The rule that comes out of this

> ### ⚠ BEFORE NARRATING A JUNCTION, CHECK THE OPEN FRACTION OF EACH EXIT.
>
> `dmap at` says `open -> (13,36) open`. That tells you the **edge** is passable
> and the **cell** is not solid. It does not tell you the cell is **floor**.
>
> | neighbour's open fraction | what it is |
> |---|---|
> | **0.90 – 1.00** | floor. A real way on. |
> | **0.50 – 0.90** | floor, with the wall cutting a corner — usually a bend |
> | **0.00 – 0.40** | **the inside of a bend, or rock.** NOT a way on |
>
> A square in that bottom band with an "open" edge is the grid telling you
> *"something continues past here"* — and what continues is a **curve**. Follow
> the high-fraction squares, including diagonally, and describe the bend.
>
> **Two exits both in the bottom band means you are standing at a bend, not a
> junction.** At (13,35) they measured 0.00 and 0.23.

Corollary for `party.py`: routing along a curve costs one extra square per bend,
because the grid must step through a corner to stay orthogonal. The arc above is
~11 squares of real corridor and routes as 12. That overstates distance by about
10 feet per bend, which is well inside the precision of a 90 ft/turn explore
rate and is not worth correcting.

---

## Not done

**Diagonal cell connectivity is still unimplemented.** `connections` is
room-to-room and `find_path` does not read it, so there is no cell-level
diagonal link. This arc is traversable only because an orthogonal staircase
through the bend corners exists. **A curve whose bends have rock on both
orthogonal corners would be genuinely impassable in this database**, and two of
this arc's four bends came close — (6,36) at 0.07 and (7,35) at 0.06.

That is the case `DIAGONAL_CONNECTIVITY.md` was written for, and it remains a
proposal.
