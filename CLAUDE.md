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
append-only and the tools have 171 tests, so both fail loudly when they break.
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

- **`git push`** — **there IS a remote**: `origin` →
  `github.com:dllahr/claude_playing_advanced_dungeons_and_dragons_1st_edition`.
  Pushing publishes. **Ask first, every time.** Committing is local and safe;
  pushing is not the same act.

  > **Tracked and therefore published: `modules/B1_DM_NOTES_DO_NOT_READ.md`**,
  > `modules/private/b1_wandering.tsv`, and the B1 level-1 map PNG. The first is
  > the campaign's spoiler file — the rolled stocking key that must never be
  > shown to the player. **If the repo is public, it is readable by anyone,
  > including the player.** The scanned rulebooks and module PDFs are gitignored
  > and are NOT published. Flagged 2026-09-05; the player's call, not mine.
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

- `campaign/encounters.tsv` — append-only award log; `anchor` rows set totals outright
- `campaign/characters.tsv` — prime requisites, AC, hp_max, proficiencies, and the
  Strength/Dexterity adjustments, so every modifier is applied consistently
- `campaign/inventory.tsv` — what the party **carries**, edited in place
- `campaign/world_changes.tsv` — what the party has **done to the dungeon**, and what
  gear it has left there. Append-only, reversible, replayed onto the map database
- `campaign/hp_log.tsv` — every wound, heal and rest; current hp is computed, never stored
- `campaign/clock.tsv` — the round count and the pre-rolled wandering jitter
- `campaign/light.tsv` — every lighting, hooding, extinguishing and refill; fuel is
  computed against clock rounds, never stored. **Hooding does not stop the burn**, so
  log `out` before a rest or the party sleeps through eight hours of lamp oil
- `campaign/rolls.tsv` — an audit trail of every die rolled
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
- `campaign/npcs.md` — the named NPCs and, importantly, **Dave's standing surety
  for the four ex-bandits**. Ten named people arrived in two days of play; a
  cleared context loses them all at once. Nothing in it is DM-side secret

| tool | what it computes fresh |
|---|---|
| `tools/xp.py` | totals; the +10% applies **once to earned experience**, not per award, or truncation eats it on small kills |
| `tools/hp.py` | current hit points, negative values **not** clamped |
| `tools/world.py` | replays world changes onto the map DB — **run after every rebuild** |
| `tools/clock.py` | the dungeon clock and wandering checks |
| `tools/light.py` | lantern oil and torch stubs, burnt against clock rounds; burn times come from `rules/exploration.md`, never from the code |
| `tools/combat.py` | attacks, damage, saves, morale, initiative, surprise |
| `tools/rules.py` | parses `rules/*.md`; every table `combat.py` uses comes from there |
| `tools/dice.py` | dice, including 1e range notation ("3-18" is 3d6, not a flat pick) |
| `tools/bestiary.py` | reads `bestiary/` — the campaign's own Monster Manual, one file per creature |
| `tools/treasure.py` | the MM treasure-type appendix; the per-creature letters come from `bestiary/` |
| `tools/party.py` | where the party is; **`move` refuses to cross a wall**, which freehand narration once did |
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
