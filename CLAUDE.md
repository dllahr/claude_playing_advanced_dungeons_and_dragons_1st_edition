# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ## Read `CHECKLIST.md` first
>
> It is the standing procedure for running this campaign — which file is
> authoritative for what, what to check every combat round, how wandering
> monsters are timed, and the specific rules that have been got wrong from
> memory and are now cached. Every item on it exists because something went
> wrong once.

## What this is

This is not a software project. It is a personal reference library of AD&D 1st Edition
rulebooks and adventure modules, used to answer rules questions and to prep/run games —
which has grown a live campaign, a rules cache, a map database and a test suite around it.
There is no build step and no dependencies beyond the conda env.

**It IS a git repo as of 2026-09-05** — see *Version control* below. The scans and
everything generated from them are gitignored; the ~2 MB of text is tracked.

Work is therefore mostly **retrieval**: find the authoritative passage in the source books
and quote or summarize it accurately.

```
manuals/      core rulebooks (PHB, DMG, Monster Manual, Monster Manual II)
modules/      adventure modules (B1 In Search of the Unknown, B2 Keep on the Borderlands)
rules/        curated rules cache — transcribed tables, parsed by tools/rules.py
bestiary/     one file per creature met, in the same format
campaign/     the live campaign: append-only logs, computed state
tools/        the code that computes it
mapdb/        the dungeon as a queryable SQLite grid
dlwork/       working notes and archived extraction inputs
deprecated/   RETIRED. Nothing here is authoritative — see deprecated/README.md
```

**`deprecated/` exists so that retiring a file does not orphan an old citation.**
Do not read facts out of it, and do not update it. `tools/deprecated/` is the
same idea for code. *(First occupant, 2026-09-05: `map_known.md`, a prose map
kept in parallel with the database, which rotted two expeditions behind while
still being listed as authoritative for what the party had seen.)*

## Version control — what git is for HERE

Initialised 2026-09-05. `.gitignore` keeps out `manuals/`, module PDFs,
`mapdb/output/` and the conversation exports: 229 MB on disk, ~2 MB tracked.

**Git is the safety net for the PROSE, not for the game state.** The TSVs are
append-only and the tools have hundreds of tests (`pytest --collect-only` for the
current count), so both fail loudly when they break.
The ten markdown files have no tool and no test — nothing fails when they rot,
which is how a wrong thief percentage sat on `party_roster.md` for weeks and how
`map_known.md` fell two expeditions behind. **Those are what git protects.**

> ### ⚠ NEVER `checkout`, `reset` or `revert` A CAMPAIGN TSV TO UNDO PLAY
>
> `encounters.tsv`, `world_changes.tsv`, `hp_log.tsv`, `clock.tsv`, `light.tsv`,
> `rolls.tsv` and `spells.tsv` are **append-only by design**. Rewinding one
> deletes events that actually happened at the table, and the tools will then
> compute a confidently wrong answer from the truncated log.
>
> **A wrong game event is corrected by APPENDING** — a superseding row, or an
> `anchor` row that sets totals outright. That is what the day-39 XP anchor is.
> Git may revert **code, rules and prose**. It may not revert the past.

### When to commit

**STANDING AUTHORIZATION, granted 2026-09-05: commit without asking.** Do not
stop play to request permission, and do not narrate the commit — just make it at
the right boundary and mention it in a line if it is worth knowing.

**What that authorization does NOT cover:**

- **`git push` — DO NOT ATTEMPT IT. THE PLAYER DOES ALL PUSHING.** *(Corrected
  2026-09-17. It was listed as authorized from 2026-09-05 and that was wrong in
  practice.)* `origin` is
  `git@github.com:dllahr/claude_playing_advanced_dungeons_and_dragons_1st_edition`
  over **SSH with a password-protected key**, and the player will not bypass the
  passphrase. A push from here fails with *"Please make sure you have the correct
  access rights"*, which reads like a broken remote and is not one.

  **So: commit freely, never push, and do not diagnose the failure** — it is
  expected. If commits are worth getting off the machine, say so in one line and
  let the player run `git push origin main` himself. Force-push and pushing
  rewritten history remain forbidden regardless.

  > ### THE REPO IS PUBLIC AND THE DM NOTES ARE IN IT — SETTLED, DO NOT RE-RAISE
  >
  > `modules/B1_DM_NOTES_DO_NOT_READ.md`, `modules/private/b1_wandering.tsv`,
  > `modules/private/b1_stocking.tsv` and the B1 level-1 map PNG are tracked and
  > published. **This was flagged and the
  > player decided: the repo stays public and he will not read the notes.**
  >
  > **Nothing about this relaxes CHECKLIST §8.** The player choosing not to look
  > is not permission to tell him. **Preserve surprise exactly as before** — the
  > arrangement is trust, and the whole value of it is that it is never tested.
  >
  > A future session will notice this and want to raise it again. **Don't.** It
  > is decided. *(The scanned rulebooks and module PDFs are gitignored and are
  > NOT published.)*
- **Anything that rewrites history** — `reset --hard`, `rebase`, `commit
  --amend` on an existing commit, force-anything.
- **Reverting a campaign TSV.** See the box above. Standing permission to
  *commit* is not permission to *undo*.

The trigger is a **coherent boundary**, not a clock:

| boundary | why |
|---|---|
| **Before every `/compact`, without exception** | The conversation is about to become a summary. Whatever is on disk and committed is what survives. **This is the important one.** |
| **End of an in-game day** | Same trigger as the `calendar.md` row. Keeps play history granular enough to bisect. |
| **End of an expedition** | The big narrative boundary. |
| **After a `rules/` or `tools/` change — SEPARATELY from play** | So a bad rules edit can be reverted without unwinding a session of play. Never mix the two in one commit. |

> ### ⚠ A BLOCKED COMMIT LEAVES THE INDEX FULLY STAGED. The next one sweeps it.
>
> *Day 99, 2026-09-19.* `git add -A && git commit` was **refused by the
> `audit.py` hook**. The staged index survived the refusal. The next commit —
> a `tools/` fix, staged with two explicit paths — picked up **all of it**:
> `clock.tsv`, `party.tsv`, `world_changes.tsv` and 58 lines of DM notes went
> into `c98bc34`, a commit whose message is about `xp.py`.
>
> **Naming paths on `git commit` does not narrow what is committed.** Only the
> index decides, and a hook rejection does not clear it.
>
> **So after ANY refused commit: `git status --short` before the next one**, or
> `git reset` to unstage and re-add deliberately. `reset` with no arguments is
> not history rewriting and is not covered by the ban above — it only moves the
> index. **`reset --hard` remains forbidden.**
>
> The mixed commit stands. History is not rewritten to tidy a mistake, and the
> repair for a bad commit is the same as for a bad game event: **say so, and
> move forward.**
>
> **SECOND VARIANT, SAME DAY — `git add -A` AS A SCRATCH BUFFER.**
> `audit.py --staged` reads the index, so the obvious way to test a document
> against it is `git add -A && python tools/audit.py --staged`. **That leaves
> the index full**, and the next commit — `7ee7a84`, titled *"tools: audit.py
> unwraps hard-wrapped prose"* — swept in `light.tsv`, `inventory_log.tsv`,
> `rolls.tsv` and 48 lines of DM notes.
>
> **No hook was involved this time.** The cause is not refusal; it is that
> `add -A` is being used as a verb meaning *"show me the diff"*. Either
> `git reset` straight after the check, or run the checker on the file:
> `python tools/audit.py path/to/file.md`.

> ### ⚠ NEVER PUT BACKTICKS IN A BASH DOUBLE-QUOTED STRING. Day 103.
>
> A `--note` written for `light.py` contained the word *who* in backticks —
> ``"light.tsv carries a `who` for every source"`` — inside a double-quoted
> argument. **Bash ran the Unix `who` command** and spliced twenty-seven lines
> of tty listings into `campaign/light.tsv`, shattering one row into
> twenty-eight and breaking the suite.
>
> These notes are full of prose about code, so the temptation to backtick an
> identifier is constant. **Use plain words, or single quotes, or a heredoc.**
>
> **Shell corruption is not an event**, so repairing it is not the forbidden
> kind of revert: the append-only rule protects things that happened at the
> table, and twenty-seven tty listings did not happen at the table. Repair it,
> say so in the row, and move on.
| **Before a risky refactor** | Today's `xp.py` reweighting would have been much easier to abandon. |

### Message convention — because `git log` is a session index

**Prefix play commits with the day number, infrastructure with its area:**

```
day 39: Hask, Dellie and Ista become 1st-level characters
day 40: check-ins in Wethersby
rules: zero-level.md, and the 0-level attack column correction
tools: xp.py weights monster and treasure xp separately
map:   level 2 built and merged
```

**This matters more than it looks.** `git log --oneline` is a complete campaign
history that costs almost no context to read — far cheaper than opening
`calendar.md`, `npcs.md` and the DM notes to reconstruct what happened when. **At
the start of a session, read it.** It is the cheapest orientation available.

Each book is a scanned PDF; most also have a sibling `.txt` of the same basename.

## The PDF/txt split — which to use

The `.txt` files are dumps of the OCR text layer embedded in the scanned PDFs, in page
order. They are the **search index**; the PDF is the **source of truth**.

Standard workflow: grep the `.txt` to locate a passage, estimate its page from the line
offset (line N of M ≈ page N/M × page count), then `Read` that PDF page range to get the
text as printed — including the tables and stat blocks that OCR mangles.

Never quote a rule, a die range, or a stat-block number straight from the `.txt` without
checking the PDF page. OCR corruption in these scans routinely hits exactly the characters
that matter. From the Monster Manual's aerial servant entry:

```
SPECIAL  DEFENSES:  Con  be  Mr        ("Can be hit only by magic weapons")
onJy  by  magjc  weapons
TREASURE  TYPE:  NfJ                   ("Nil")
```

Digits corrupt as readily as letters, and a garbled `1-4` vs `1-6` is not visibly wrong.

## Grepping the text dumps

**The Monster Manual (`tsr02009`) is double-spaced between words.** Every other `.txt` here
uses single spaces. This silently breaks the obvious search — `grep -i "armor class"` on
that file returns zero hits while the phrase appears hundreds of times.

Write whitespace-tolerant patterns and they work across all five files:

```bash
grep -inE "armor +class" manuals/*.txt
grep -inE "magic[- ]+user" "manuals/tsr02100 - AD&D Player's Handbook.txt"
```

Other things that will bite:

- **Filenames need quoting.** They contain spaces, `&`, and an apostrophe. Note also that
  `modules/tsr09023 -In Search of the Unknown .txt` has a stray space before the extension
  and a missing one after `tsr09023`; glob it rather than typing it.
- **~40-50% of lines are blank** (page whitespace from the scan). Use `grep -A/-B` for
  context rather than `sed -n` line ranges, which often land in empty gutters.
- **There are no page markers or form feeds** in the `.txt`. Bare-number lines are
  unreliable as page numbers — table values look identical. Estimate pages by proportion.
- **Multi-column pages interleave.** Headers, captions, and facing-column text can appear
  mid-sentence. If a passage reads as a non-sequitur, that is the layout, not the rule.
- **`B2 Keep on the Borderlands` has no `.txt`** — it is PDF-only, so it is invisible to
  every `manuals/*.txt modules/*.txt` grep. Search it separately, or generate the missing
  dump (see below).

## Reading tables — the one technique that matters

**Tables do not survive the OCR text layer.** Columns interleave with the facing page,
price columns vanish entirely, and digits corrupt silently. Never transcribe a table from
the `.txt` or from `page.get_text()`.

**`Read` with the `pages` parameter does not work here** — it needs `pdftoppm`/poppler,
which is not installed. Use PyMuPDF to render the page to PNG, then `Read` the PNG:

```bash
python3 -c "
import fitz
d = fitz.open('manuals/tsr02100 - AD&D Player's Handbook.pdf')
d[35].get_pixmap(dpi=150).save('/path/to/scratchpad/phb_35.png')
"
```

Then `Read` that PNG. At 150 dpi these scans are fully legible, this is **ground truth**,
and it is the only reliable way to read a table, a stat block, or a map. Note the index is
0-based and runs ~2 ahead of the printed page number in the PHB.

To find the right page, grep the `.txt` for a phrase and scale by line position, or search
the text layer directly:

```bash
python3 -c "
import fitz
d = fitz.open('manuals/tsr02100 - AD&D Player's Handbook.pdf')
print([p for p in range(d.page_count) if 'Magic Missile' in d[p].get_text()])
"
```

No PDF CLI tools are installed on the base system (`pdftotext`, `pdfgrep`, `mutool`,
`qpdf` are all absent). Base Python has `fitz` (PyMuPDF), `pypdf`, and `pdfplumber`.

## Python environment

Anything beyond a one-line page render belongs in the project conda env:

```bash
conda activate advanced_dnd_1e
```

It carries numpy, scipy, matplotlib, plotly, pandas, scikit-image, Pillow, PyMuPDF,
opencv, and **tesseract + pytesseract** (tesseract is *not* on the base system, only
inside this env). Created 2026-08-19 for the map-extraction work.

## Map extraction — `mapdb/`

`mapdb/` turns a scanned dungeon map into a queryable SQLite grid: one row per 10'×10'
square, one per boundary, with a 1–10 confidence on every call. Read `mapdb/README.md`
before touching it — the classifiers are not brightness thresholds, and the reasons why
are documented there with the measurements that justify each one.

The DMG sample dungeon (`dmg.sqlite`) is the validated practice case. Two facts carry
over to any new map:

- **Secret doors cannot be read from the image.** They are marked by a printed `S` in
  the annotation layer, not by anything structural. They must come from the key text.
- **Room "anchors" are label positions, not room extents.** Rooms and corridors are both
  plain white; where one ends and the other begins is a reading of the text.

Two checks matter more than any classifier tweak: build the node graph from the key
text *independently* of the image and let `build.py` compare them, and run
`dmap.py reach` — every non-solid square should be reachable from the entrance, so
anything unreachable is an invented wall or a missed door.

**`dmap.py light <db> <level> <x> <y> --radius N [--mark-seen]`** answers "what does a
light source here actually reveal" by ray-casting — the exact line from cell centre to
cell centre, blocked by a wall, a shut door or solid rock, not graph distance and not
raw Euclidean distance either (both get corners wrong in opposite directions). Use it
instead of eyeballing which nearby cells are "close enough" or hand-picking a `seen
--cells` list — both were the direct cause of geometry mistakes in play (day 139).
**A diagonal neighbour of the source gets a second check if the direct ray fails**:
that ray is always exactly 45 degrees, so it always grazes the shared corner, and a
single solid cell pinching that corner used to read as "dark" even when light plainly
reaches around it at a slightly different angle. The second check is the player's own:
does the cell have an open border with one of the source's orthogonal neighbours, and
is THAT neighbour lit? Confirmed day 140 against a line drawn on the actual page
render. Reported as `'corner'` in `light_reach`'s output, distinct from a direct `'los'`.

**`dmap.py walk <db> <level> <x> <y> <N|S|E|W>`** advances the party in a direction
until there is something to stop FOR — a junction (2+ REAL ways on, a real choice,
handed back rather than picked), a dead end, a closed loop, an area-label change, or
an already-visible feature (a cell's own `feature` tag, or a found secret door) — and
deliberately does **not** stop merely for stepping onto ground nobody has walked
before. Use it for open-ended declarations ("advance east", "keep going until
something changes") in place of guessing a destination and retrying against
`party.py move`'s REFUSED errors, which is what several of day 139's geometry
mistakes actually were. A destination the player names explicitly still goes
straight to `party.py move`. **Level 2's room labels are unreliable**
(`mapdb/README.md`: "nearest numbered area", not "inside room N") — an
area-boundary stop there may fire on a label flicker that means nothing in the
fiction; read it the way any low-confidence call in this database is read, not
as certain.

**A junction is decided by REAL ways on, not raw exits.** `frontier_exits` floods
the whole bubble of already-`seen` ground reachable from a cell and reduces it to
the directions that actually reach something unseen, so two raw exits that both
wind around one loop to the same single frontier collapse into ONE real choice
instead of a false fork (`mapdb/README.md` has the full day-140 writeup: B1 level
2's alcove at (6,8)-(10,8), where "north" and "west" out of (7,8) both only curled
back through squares already lit). This is also why `party.py move` now marks
every square it actually walks as `seen` — a square walked but never light-checked
was still reading as fair game for that search to wander back through.

**A junction also needs STRUCTURE, not just two different destinations.**
`structural_options` collapses two directions into one if the lattice corner
between them is open (`_corner_passable`, the same check `light` uses for a
grazed corner) — nothing separates the paths, so it is one pocket widening,
not a fork. Same session, one cell further: (6,6)'s "south" and "west" both
reached genuinely different unseen ground, so `frontier_exits` correctly
called both real, but there was no wall between them either — confirmed
against the actual page render, not re-derived, since a freshly-refit grid
drifted enough to misread a confidently-solid cell as open (`mapdb/README.md`
has the full writeup, including why the page must be rendered at the level's
own stored `pdf`/`page`/`dpi`/`channel`). **Only ADJACENT direction pairs
share one corner** (S/W, S/E, N/W, N/E) — a first pass checked only those and
missed the SAME false fork one cell further on at (5,4), where the real
choices were the OPPOSITE pair "east"/"west". Fixed by adding `came_from` (the
direction just walked, never itself offered) into the comparison as a bridge:
E and W each corner-connect to `came_from`, so they merge transitively through
it even with no direct corner of their own.

**Read the map's own legend before writing any classifier.** The DMG prints a LEVEL
KEY (pdf p.95) defining `S`=secret door, `C`=concealed door, boxed `X`=trap door,
boxed `S`=secret trap door, even hatching=stairs up, tapering=stairs down, and the
stream glyph. Several early misreadings were symbols the book defines explicitly.
Symbols are also **rotated** on the map (doors, stream, stairs; and one `S` at 45°),
so matching must be rotation-aware. Six geometry errors during play all had
the same root cause: re-deriving layout ad hoc from crops under narrative pressure,
with no durable map to check against.

## Curated rules cache — check here first

`rules/` holds tables already transcribed from page renders, as markdown pipe-tables.
**`tools/rules.py` parses them**, so these files are data as well as documentation:

- `rules/combat.md` — character and **monster** to-hit matrices, saving throws, weapon
  damage and proficiency penalties, morale, time/round structure
- `rules/abilities.md` — Strength/Dexterity/Wisdom adjustments and, importantly, **where
  each one does and does not apply**
- `rules/exploration.md` — light, encumbrance, searching, the wandering-check procedure
- `rules/spells-1st-level.md` — all 12 1st-level cleric spells, most 1st-level M-U spells
- `rules/equipment.md` — Armor Class Table, armor/weapon/gear prices
- `rules/experience.md` — XP values, the +10% prime-requisite rule, training costs
- `rules/thief.md` — thief function table, racial and DEX adjustments, **and
  Tristle's actual numbers** (his Find/Remove Traps is **25%**, not the 30% that
  sat wrong on `party_roster.md` for weeks)
- `rules/b1-module.md` — B1's own rules, which **override the PHB** where they
  differ: the module's own door procedure is d6, 1-2 locked, else it opens
- `rules/zero-level.md` — **"normal men."** 1e has no 0-level→1st progression;
  1st level *begins* at 0 XP and the gate is capacity, not points. Carries the
  0-level attack column (DMG p.74 matrix I.B col 0) and save row, both of which
  Hask and Dellie were run off the *wrong* table for two expeditions. **Read
  this before giving any new NPC a stat line.**

`python tools/rules.py --list` lists every table and flags any lacking a `*source:*`
line. Keep headings stable — the parser finds tables by their heading, deliberately,
so a renamed heading fails loudly instead of returning a plausible wrong table.

**Read these before re-deriving anything.** Add to them whenever a new table is looked up —
the cache is meant to grow. Each table carries a provenance line; keep that habit, and mark
anything unverified as unverified rather than silently trusting it.

## Online reference

[1eonline.info](https://1eonline.info) mirrors the three core books as clean HTML, which is
much faster than rendering pages:

- PHB `https://1eonline.info/2ph/ph.htm` — e.g. `dexterity.htm`, `thief.htm`, `q.htm`
- DMG `https://1eonline.info/3dmg/dmg.htm` — `ct.htm` (combat tables), `st.htm` (saves),
  `morale.htm`, `experience.htm`
- MM `https://1eonline.info/1mm/mm.htm` — one page per monster, e.g. `carrioncrawler.htm`,
  and these include XP value, saves, and morale alongside the MM stat block

Two caveats. **It carries post-PHB material** — its Dexterity table runs to 25, it has a
two-weapon-fighting column, and its 1st-level cleric list includes *Ceremony, Combine,
Portent, Magic Stone* and others that are **not** 1e PHB spells. Strip that back to core.
And **WebFetch summarizes through a small model**, so an exact number can get paraphrased;
it has matched the PDFs everywhere checked so far, but for anything load-bearing, confirm
against a page render.

## Answering rules questions

- **Cite book and page**, e.g. "DMG p. 82" — the point of keeping the PDFs is verifiability.
- **1e is not 5e.** Descending AC, THAC0-era to-hit matrices, segments/turns, and
  race/class restrictions all differ. Do not fill gaps from later-edition memory; if it
  isn't in these books, say so.
- **Precedence** when sources disagree: DMG over PHB for adjudication and DM-facing
  procedure; PHB for player-facing character rules; Monster Manual over Monster Manual II
  where a creature appears in both.
- **Module contents are DM-facing.** B1 and B2 are unspoiled adventures in active use —
  treat room keys, traps, and treasure as spoilers unless the ask is clearly DM prep.

Related material sits one level up in `../old_school_essentials/` (OSE / Advanced Fantasy
tomes, plus loose character notes). It is a different retroclone ruleset — do not mix its
rules into a 1e answer without flagging the swap.

## Campaign bookkeeping — `campaign/` and `tools/`

**Never quote a running total from a prose file.** Both the XP line and the equipment list
in `party_roster.md` went stale by two expeditions and were cited as fact, once leading the
DM to tell the player their spikes were in a door they had already recovered them from.

> ### AND NEVER QUOTE AN **EVENT** FROM ONE EITHER — added 2026-09-06
>
> Same rule, and it took nine caught errors in one session to see that it
> generalised. **`campaign/npcs.md`, `articles.md`, `journal.md` and every scene
> write-up are summaries the DM wrote. They are an INDEX. The TSVs are the
> evidence.** Believing my own summary produced three wrong facts in one day —
> how Kell died, whether Sim had been away for two years, and how cold Father
> Cuddy is to Yrtone.
>
> **`python tools/recall.py <name>` prints every logged event for a character
> across all seven logs, in order.** Run it before narrating anyone's past.
> `tools/tests/test_recall.py` carries the regression: Ista was hauled out of
> the pool and given the party's **first** cure light wounds, and Blartho bled an
> extra round *after* that. The DM once narrated the exact opposite.

- `campaign/encounters.tsv` — append-only award log; `anchor` rows set totals outright
- `campaign/characters.tsv` — prime requisites, AC, hp_max, proficiencies, and the
  Strength/Dexterity adjustments, so every modifier is applied consistently
- **`campaign/inventory_log.tsv`** — what the party **owns**, append-only, quantities
  derived. **Every quantity carries its `unit`** and there is one row per
  `(asset, condition)`. ⚠ **Oil FUEL LEVELS are NOT counted here** —
  `light.tsv` owns them, because that log knows which flasks have been broached. **Where
  a thing is in the dungeon** is `world_changes.tsv`'s. Its `holder` column is
  **retired as of day 103, read-only** — `carry.tsv` is now the single answer to
  where a thing is. *(The old `campaign/inventory.tsv`
  was retired to `deprecated/` on 2026-09-11: it was the one file still edited in place
  and it had rotted five times.)*
- **`campaign/carry.tsv`** — **THE SINGLE "WHERE IS EVERYTHING" LOG**, append-only.
  `who` is closed to a character name (`characters.tsv`), a `people.tsv`/`places.tsv`
  id, or the literal `party` for shared kit whose bearer isn't tracked.
  `tools/carry.py check` demands **located == owned**, not merely `<=`: an owned
  thing with nowhere logged for it is the exact shape of the headboard and the
  diary, which had an inventory row and no location anywhere for seventy days.
  Also computes per-person encumbrance bands off the Strength allowance table and
  `pack`s the shared kit onto the strongest bearers first
- **`campaign/venture.tsv`** / **`campaign/venture_shares.tsv`** — **TWO
  VENTURES, NOT THE PARTY'S PROPERTY** (`wool_venture.md`). **`wool-venture-1`**
  is the day 12-27 buy-and-sell, 14 shares (6 PCs at 1, Hask/Dellie at ½, Wend 1,
  the six holders as one `holders_six` row) — **CLOSED**, except a flagged open
  tail: 229 gp to the holders with no close row on `loops.tsv` L003.
  **`ongoing-venture`** is everything since (the standing art.7 wool buy, the
  cloth-making plant) — **party capital only, no other investor, no cap table**;
  Wend is paid a **wage** to run it, not a share (checked against the record,
  day 103). `venture.tsv` answers only (a) what each venture physically holds
  and (b) who is owed what — **never (c) valuation**, figured out only when
  needed. `tools/venture.py`
- `campaign/world_changes.tsv` — what the party has **done to the dungeon**, and what
  gear it has left there. Append-only, reversible, replayed onto the map database
- `campaign/hp_log.tsv` — every wound, heal and rest; current hp is computed, never stored
- `campaign/clock.tsv` — the round count and the pre-rolled wandering jitter
- `campaign/light.tsv` — every lighting, hooding, extinguishing and refill; fuel is
  computed against clock rounds, never stored. **Hooding does not stop the burn**, so
  log `out` before a rest or the party sleeps through eight hours of lamp oil
- **`campaign/money.tsv`** — **every movement of coin, append-only, and `asset` is
  REQUIRED.** Funds are `SUM(delta)`, computed. Anchored at day 39 because the prose
  blob it was reconstructed from **stops reconciling around day 34** — from 39 onward it
  reconciles to the gold piece. **Five purchases in this campaign were recorded only as
  a sentence inside the notes column of the old `funds` row** and the thing bought got no
  row anywhere; naming an asset is what makes that impossible
- **`campaign/assets.tsv`** — **REFERENCE: identity only, no quantities.** So that
  `money.tsv` and `inventory.tsv` can name the same thing and be checked against each
  other. The **service ids** (`wages`, `lodging`, `licence`, `loan`, `kit`) exist because
  money leaves the purse for things that are not goods, and a rule that cannot be obeyed
  is a rule that gets quietly broken
- **`campaign/days.tsv`** — **the campaign day, machine-readable.** The current day is
  `max(day)`, derived, so it cannot drift the way it did before the player caught it on
  Torsat's illness. `calendar.md` stays the far richer narrative record
- **`campaign/loops.tsv`** — **things that will one day CLOSE.** A log of loop *events*,
  not a table with a mutable `closed` cell; the open set is derived. **A `close` must
  cite the event that closed it.** Built because a warning is the one kind of prose that
  never *looks* stale: art. 11's fired on day 65 and was quoted as live on day 77, and
  Ancel's *"Unanswered"* outlived its answer by **43 days**
- **`campaign/availability.tsv`** — **who is present, away, invalid or dead.** Append-only,
  current status derived. This lived nowhere and was re-derived out of prose every time an
  expedition was outfitted
- **`campaign/encounter.tsv`** — **the live fight.** Append-only; round, initiative,
  declarations, holds and monster damage all derived. **Empty when no fight is in
  progress**, which is how `combat.py` knows to refuse
- `campaign/rolls.tsv` — an audit trail of every die rolled. ⚠ **`dice.py` honours
  `$DND_ROLL_LOG`** — set it before driving any tool by hand, or the rolls land in the
  campaign's evidence. `tools/tests/conftest.py` closes the same hole for pytest
- `campaign/party.tsv` — **where the party is**, and the only legal way to move
  it. `tools/party.py move` routes through `mapdb`, which physically cannot walk
  through a wall; freehand narration once did exactly that
- `campaign/spells.tsv` — memorised spells, append-only, current loadout
  **computed**. No tool reads it yet — it is maintained by hand
- `campaign/journal.md` — **player-facing discoveries and conclusions.** The
  fiction of what the party thinks it knows, as distinct from `cells.seen`,
  which is what they have actually looked at
- `campaign/wool_venture.md` — the party's first commercial undertaking, its
  share structure and the reason it must be in writing. **The clip sold at
  Ludbury for 1,200 on day 27**; the six holders' 229 gp is still travelling
- `campaign/articles.md` — **what is written down in the fiction**: the party's
  SUCCESSION (Wend manages everything for two years, then spends it on the town
  as she sees fit), Coll's authority while they are away, Ista's line, Hask's
  stake. Also the **gifts-fail-work-lands** table, which is the single most
  useful behavioural note in the campaign
- `campaign/cargo_manifest.md` — **the freight**: every item bought at Ludbury,
  what it cost, and what it is for, plus the exact money reconciliation.
  `inventory.tsv` is what the party *carries*; this is what is on the carts
- `campaign/calendar.md` — **the day count and the distances.** Day numbers were
  kept in my head and drifted until the player caught it on Torsat's illness.
  Nothing else gets to disagree with this file
- `campaign/district.md` — the SETTING, built at the table on dice because B1
  supplies a crag and a dungeon and nothing else. The wool staple moved; every
  acre is held; the layoffs are upstream of the robberies. Not DM-side secret
- **`campaign/people.tsv`** · **`campaign/places.tsv`** — **REFERENCE, identity only** —
  and `places.tsv` also carries **the overland grid** (`x`, `y`, `fix`) and
  **`day_mode` beside every travel time**, because a day is not a distance: cart 18
  miles, ride 30, walk 14.
  Aliases resolve *Wetherby*→*Wethersby* and *"Rell's brother"*→*Gyll*. **No status or
  condition columns**: those change, so they are events with dates
- **`campaign/interactions.tsv`** — **who was in the room and what happened.** The join
  table. Social events used to live only in prose, which is why misremembering one was
  the largest error class here
- **`campaign/sessions/day-NNN.md`** — **the session write-ups, ARCHIVED.** Verbatim and
  complete. **Read for pleasure and for quotes, never to answer a question**
- `campaign/npcs.md` — now the **roster and how people are run**: Dave's standing
  surety, the ex-bandits' sheet, and the loyalty-adjustment table. Nothing DM-side

| tool | what it computes fresh |
|---|---|
| **`tools/brief.py`** | **THE SESSION BRIEFING. RUN IT FIRST, EVERY SESSION AND AFTER EVERY COMPACT.** Day · who is available · hp · xp · oil · gear left in the dungeon · position · clock · **open loops** · what is stale. Every figure computed by the tool that owns it, so nothing in it can be 38 in-game days out of date the way `CHECKLIST` §11 was |
| **`tools/log.py`** | **THE ONLY WRITE PATH for money, scenes, days and availability. It VALIDATES, then appends** — and refuses a money row that names no asset, an asset id not in `assets.tsv`, a zero delta, **a citation to a scene that does not exist**, a campaign day running backwards, an unknown character, or **a scene naming somebody not in `people.tsv`**. Validate on write, rebuild on read |
| **`tools/build_campaign_db.py`** | **builds `campaign/output/campaign.sqlite` — a DERIVED VIEW, gitignored, rebuilt from the TSVs.** Real foreign keys, `PRAGMA foreign_keys=ON`, **and a violation FAILS THE BUILD** rather than dropping the row. `--check` compares a **watermark** (rows + sha256 per source) so staleness is a comparison, not a judgment. `--query` runs ad-hoc SQL **read-only** |
| **`tools/overland.py`** | **distances, bearings, and what the party knows** -- computed, in feet. `how-far` | `from` | `where <frame> x y` (a dungeon square in the world frame) | `knows` | **`check`, which recomputes every travel time off `rules/overland.md` (DMG p.58) and FAILS if the model stops agreeing with the fiction.** **Distances are EXACT; times are RANGES.** ⚠ **IT DOES NOT DRAW A MAP** -- an ASCII one lived here for a day and was removed, because reading a position off a character grid is harder than reading the coordinates, and **a pasted map is stale the instant anything moves** |
| **`tools/mapimg.py`** | **THE MAP, as SVG or an HTML page.** ⚠ **Draws the PARTY'S map by default; `--true` is the DM's and is named so in the filename.** `--around <place> --miles N` crops; `--px-per-mile` zooms. **A vague position is drawn as a dashed ring TO SCALE -- or not at all**, because inflating one so it can be seen would draw a bigger doubt than the party has. Output is gitignored: it is derived |
| **`tools/entities.py`** | **`who <name>` is the query this campaign never had** — every scene a person was in, with a day, a reaction and a citation. `check` refuses any name that does not resolve, so *Wetherby*/*Wethersby* and *"Rell's brother"*/*Gyll* are each one thing. **Run `who` before narrating anybody's past** |
| **`tools/encounter.py`** | **the LIVE FIGHT**, computed from `campaign/encounter.tsv` — round, initiative, **who has declared**, **who HELD**, and monster hit points (`--hidden`; never shown otherwise). All of this used to live only in the DM's own narration, re-read every turn out of his own previous messages |
| **`tools/inventory.py`** | **what the party OWNS**, computed from `campaign/inventory_log.tsv`. **One row per (asset, condition), with an explicit `unit`** — so `~2.5 IRON + 8 STANDARD` is two rows in person-weeks instead of one cell that read as the number 2. **`carried` derives spikes as owned − emplaced**, so the two can never drift |
| **`tools/carry.py`** | **WHO IS CARRYING WHAT, and WHERE EVERYTHING ELSE IS**, computed from `campaign/carry.tsv`. `check` demands **located == owned**. `pack` fills the shared kit onto the strongest bearers first, up to a target encumbrance band, off the Strength allowance table in `rules/exploration.md`. `where` is the complement of `roster` — every place's or NPC's contents, not a person's — added day 139 after a hand-rolled query got a basecamp total wrong by summing anchors additively |
| **`tools/venture.py`** | **the wool/cloth venture's holdings and money position**, computed from `campaign/venture.tsv`, and its **cap table** from `campaign/venture_shares.tsv`. Deliberately answers only (a) what it holds and (b) who is owed what — never a share's price |
| **`tools/ledger.py`** | **the purse, computed from `campaign/money.tsv`** — never stored, never quoted from a cell. `check` is the double-entry audit: every movement names an asset, every *good* has an inventory row, and the computed purse is compared against the `inventory.tsv` cell rather than trusting it |
| **`tools/audit.py`** | **checks the FIGURES in a block of text against the tool that owns each one.** `--text "…"` · a file · `--staged` · `--show` lists every truth it knows. **Wired into `tools/hooks/pre-commit`, so it runs on every commit and cannot be forgotten** — enable once per clone with `git config core.hooksPath tools/hooks`. It **blocks** on a mismatch; `audit-skip` in a line, or naming a day in the sentence, marks a figure as of-its-time. **If it ever cries wolf, LOOSEN THE CHECKER — do not learn to pass `--no-verify`** |
| **the `auditor` agent** | `.claude/agents/auditor.md`. The half that needs reading comprehension. **Citation or nothing**, three verdicts, and **every verdict names its SOURCE TIER** — tier 1 the TSVs, tier 2 `rules/`, tier 3 the prose, which is *suggestive, never conclusive*. **Run it before asserting what an NPC previously said or did, and before writing any finding or rule into `articles.md` / `CHECKLIST.md` / `rules/`.** It may not read the DM notes |
| **`tools/loops.py`** | **things that will one day CLOSE**, derived from `campaign/loops.tsv`. **`--touching "Wend, Osk"` is the one that matters: run it EVERY TURN with whoever the player just named.** A `close` **requires evidence and the tool refuses without it** — closing means citing the thing that closed it |
| `tools/xp.py` | totals; the +10% applies **once to earned experience**, not per award, or truncation eats it on small kills |
| `tools/hp.py` | current hit points, negative values **not** clamped |
| `tools/world.py` | replays world changes onto the map DB — **run after every rebuild** |
| `tools/clock.py` | the dungeon clock and wandering checks |
| `tools/light.py` | lantern oil and torch stubs, burnt against clock rounds; burn times come from `rules/exploration.md`, never from the code. **Who carries a lantern comes from `carry.tsv`** as of day 103, not from `light.tsv`'s own `who` column — the two were answering the same question and drifting |
| `tools/combat.py` | attacks, damage, saves, morale, initiative, surprise. ⚠ **`round` REFUSES to roll for a character with no `declare` row in the current round** — *THE DM DOES NOT DECLARE THE PARTY'S ACTIONS* stops being a sentence and becomes a required input. A **held** action counts as a declaration; a declaration **does not carry into the next round** |
| `tools/rules.py` | parses `rules/*.md`; every table `combat.py` uses comes from there |
| `tools/dice.py` | dice, including 1e range notation ("3-18" is 3d6, not a flat pick) |
| `tools/bestiary.py` | reads `bestiary/` — the campaign's own Monster Manual, one file per creature |
| `tools/treasure.py` | the MM treasure-type appendix; the per-creature letters come from `bestiary/` |
| `tools/party.py` | where the party is; **`move` refuses to cross a wall**, which freehand narration once did. **It also PRINTS any known secret door the route passes**, both sides — DMG p.97's elf passive 1-in-6 is owed on EVERY pass, and day 118 found four crossings of a known door (L051, `(3,41,V)`) with no check ever rolled for any of them |
| `tools/recall.py` | **every logged event for one character, across all seven TSVs, in order.** `python tools/recall.py Ista --exped 6`. **Run it before narrating anybody's past** — the prose files are an index, the TSVs are the evidence |
| **`tools/offscreen.py`** | **WHAT THE NPCs DO WHILE THE PARTY IS ELSEWHERE.** `campaign/agendas.tsv` holds one row per NPC task on a **weekly** cadence with its outcome table **written down before the first roll**; `tick` rolls what has come due (through `dice.py`, so every roll is in `rolls.tsv`) into `campaign/offscreen.tsv`. **`log.py day` runs it on every new day**, so a day cannot open without the queue catching up, and it prints a COUNT only. **THE NEWS IS HIDDEN UNTIL THE PARTY MEETS THE PERSON (player's ruling, day 135): run `offscreen.py news --who NAME` when they do, tell it in the person's voice, then `deliver`.** Never read out a waiting tick early. `brief.py` shows counts, never content. `close`/`pause` an agenda when a loop closes. Built because Wend's queue sat at OVERDUE 110 for two weeks: an NPC who only moves when asked is not a person |
| **`tools/account.py`** | **RUNNING ACCOUNTS WITH NPCs, computed from `campaign/accounts.tsv`.** Positive = the NPC owes the party. The first is **`holt`** (loop L065): goods sold on a schedule, coin now, a **tab** at the Inn (board and ale come off the balance a night at a time) and 40 gp a month. **A tab or credit is not coin and does not touch `money.tsv`; coin paid does.** Never quote the balance from a note |
| **`tools/stocking.py`** | **B1's stocked monster placement, computed from `modules/private/b1_stocking.tsv`.** DM-only, same standing as the DM notes and `b1_wandering.tsv` — tracked, published, never quoted to the player. Append-only per INDIVIDUAL (`troglodyte_41a`, not "the troglodytes"), so a wounded one that flees keeps its real remaining hp if met again. `status`/`at` are the read side; `stock`/`hp`/`move`/`flee`/`die` are the write side. **`flee` gives a limited findable window** (rounds, expires on a change of day or expedition regardless of the exact count) rather than the individual vanishing — built after the orcs that ran from (4,19) on level 1 forced a retcon (an invented passage) because there was nowhere real for them to have gone. **`simulate`** is the dice-driven mover on top of `dmap.py`'s `random_walk`/`exits`: give it an individual and its own move rate (from `bestiary/`) and it walks the REAL map, choosing uniformly at random at every junction, for a rolled 1d3 turns, stopping early at a dead end — then rolls the 5+1d4-turn linger window and records it as one `flee` event, so wherever it ends up is a real, reachable square. Backfilled day 139 from the master stocking table (rolled once, 2026-08-15, never re-rolled) and cross-checked against `world_changes.tsv`/`bestiary/` for what has actually been resolved in play so far |
| `tools/tsvlog.py` | the shared TSV reader every other tool uses; not run directly |

`bestiary/` holds one markdown file per creature in the same pipe-table format, with
the MM stat block, its special attacks and defences as rows, the B1 conversion, and the
play record. Read `bestiary/README.md` before adding one.

**No rules table is written twice.** `rules/*.md` holds the numbers *and* the page
citation; the code parses that file. A table restated in Python would be a second copy
that nobody re-checks against the book.

## Active campaign — B1, In Search of the Unknown

A game is in progress. **The user plays all six characters; Claude is the DM.**

**As of day 39 there are NINE characters, not six.** Hask, Dellie and Ista —
taken in as henchmen at 0 level — had ability scores rolled in the open on
2026-09-05 and became **Fighter, Cleric and Thief**, 1st level, in
`characters.tsv`. They are rolled by `combat.py` like anyone else. Two
consequences that will otherwise be played wrong: **Dellie may not use edged
weapons** (cleric prohibition took her spear) and is **AC 6, not 3** (DEX 4);
**Ista's CON 3** means −2 hp per die and she can be raised at most three times.
They draw a **full share of monster XP and a half share of treasure** — see the
comment block atop `tools/xp.py` for why those differ.

- `party_roster.md` — **the character-generation record**: rolled ability scores,
  starting gold, race/class, and the effects derived from them. Player-facing and
  safe to discuss. **It is not the live sheet** — its CURRENT STATE block is
  marked superseded and deliberately left three expeditions behind, because
  keeping it current would recreate the second source of truth that made it
  dangerous. hp, XP, gear, spells and position are all computed (see the tables
  above). **Derived numbers on it are a cache of `rules/*.md`, and `rules/` wins.**
- `modules/B1_DM_NOTES_DO_NOT_READ.md` — **DM-only.** The stocked monster/treasure key,
  AD&D conversion notes, and session log. Never quote or summarize this to the user.

Two standing instructions from the user:

1. **Preserve surprise.** Make DM judgment calls silently and write them to the DM notes.
   Do not narrate stocking decisions, module content, or rules facts that telegraph an
   encounter. Surface a rule only when a declared action actually invokes it.
2. **Full Gygaxian rigor**, pure PHB/DMG/MM. Roll in the open, apply encumbrance, morale,
   and training costs, and do not soften outcomes.

B1 ships **unstocked by design** — the monster and treasure placement in the DM notes was
rolled, not authored, and is the only copy. Do not re-roll it.
