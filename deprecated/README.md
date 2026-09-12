# Deprecated — kept for the record, not for reference

**Nothing in this directory is authoritative.** Do not read a fact out of these
files and do not update them. They are here because deleting a file that was
once cited makes an old citation unresolvable, not because they are still true.

## `map_known.md` — retired 2026-09-05

A prose map of discovered geography, kept by hand from expeditions 1–4.

**Why it went:** it was the same failure mode as the stale XP line in
`party_roster.md` — a running record kept in prose, in parallel with a computed
one, which then rotted. Its last update was **2026-08-26**; expeditions 5 and 6
both ran after that and neither was written into it. **It was two expeditions
stale while still being listed as authoritative for "what has the party seen."**

It also said so itself, in its own masthead:

> *"The extracted map outranks this file. Where a distance or a connection here
> disagrees with `mapdb/output/b1/b1.sqlite`, the database is right and this note
> is wrong — ruled by the player 2026-08-25."*

**What replaces it:**

| for | use |
|---|---|
| what the party has seen | **`cells.seen` in `mapdb/output/b1/b1.sqlite`**, via `dmap.py at` |
| what they did to the dungeon | `campaign/world_changes.tsv`, replayed by `tools/world.py` |
| where they are now | `campaign/party.tsv`, via `tools/party.py where` |
| what they *concluded* — the fiction | `campaign/journal.md` |

**Careful with `dmap.py at`:** it also prints the names of rooms the party has
never entered. See CHECKLIST §8.

---

## `inventory.tsv` — retired 2026-09-11

**The second occupant, and it is here for the same reason as the first.**

It was **the one campaign file still edited in place** — materialised state with
no watermark, which is the only category of thing in this repo that can rot —
**and it is the file that rotted five times**: the two carts (forty days with no
row at all), the two mules, the small goods (357 gp, seventeen days untracked),
six 50-ft ropes (eleven days while the row still said 2), and the dragon scales
(carried as unsold long after they had been sold).

### And its `qty` column was prose pretending to be a number

Every tool that read it took the first integer it could find:

| the cell | read as | |
|---|---|---|
| `~2.5 IRON + 8 STANDARD` | **2** | two things crammed into one cell |
| `1,072 gp 1 sp` | **1** | |
| `~100 lb, ~97 gp` | **100** | a **weight** read as a **count** |
| `18 sealed (+1 broached)` | 18 | right by luck; the broached flask invisible |
| `8 (7 sound, 1 damaged)` | 8 | right by luck — and the damaged rope is the one that nearly dropped Blartho |

**Superseded by:**

| | |
|---|---|
| `campaign/inventory_log.tsv` + `tools/inventory.py` | what the party owns — **one row per (asset, condition), with an explicit `unit`** |
| `campaign/money.tsv` + `tools/ledger.py` | the purse |
| `campaign/light.tsv` + `tools/light.py` | lanterns, oil and torches |
| `campaign/world_changes.tsv` + `tools/world.py` | gear left in the dungeon |

**The notes in the retired file are still worth reading as provenance. The
numbers are not.** The ones that mattered were carried across with their notes
attached.
