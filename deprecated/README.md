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
