# The plan — logs, state, watermarks, and what gets deleted

**Written 2026-09-10, play paused at campaign day 77.** Diagnosis and options:
`dlwork/tooling_redesign.md`. This is the buildable version, revised after the player
pushed on three things — **git diffs, SQL-vs-tools, and the log/state distinction** —
each of which changed the design.

---

## 0 · THE ORGANIZING CONCEPT — four kinds of thing, and only one of them can rot

**This is the player's framing and it is the key to the whole design.** Every file in
this repo is exactly one of these, and most of the confusion in the campaign comes
from files that are secretly two.

| | what it is | can it go **wrong**? | can it go **STALE**? | examples |
|---|---|---|---|---|
| **1 · LOG** | append-only, ordered, immutable. **Truth.** Corrections are superseding rows, never edits | yes | **NO — it is the upstream** | `hp_log` · `rolls` · `world_changes` · `light` · `clock` · `encounters` · `spells` |
| **2 · DERIVED STATE** | computed fresh on every call, **never persisted** | only if the code is wrong | **NO — it cannot rot, because it does not exist between calls** | `hp.py` · `xp.py` · `light.py oilstate` · `party.py where` |
| **3 · MATERIALISED STATE** | derived state that **is** persisted | yes | **YES. THIS IS THE ONLY CATEGORY THAT ROTS** | `campaign.sqlite` · `mapdb/output` · **`inventory.tsv`** · `party_roster.md`'s CURRENT STATE · `map_known.md` (retired for exactly this) |
| **4 · REFERENCE** | hand-authored, authoritative in itself, **no upstream** | yes | **NO — nothing to fall behind** | `rules/*.md` · `characters.tsv` · `bestiary/` · `people.tsv` · `places.tsv` |

> ### THE RULE THAT FALLS OUT OF IT
>
> **Prefer (2) over (3) always. Where (3) is unavoidable, it carries a WATERMARK.**
>
> **Every single class-C error in this campaign is a category-3 object with no
> watermark** — the thief percentage, the XP line, the equipment list, `map_known.md`,
> the oil count (twice), the rope count, `CHECKLIST` §11.

### 0.1 · Watermarks — and this is already proven here in miniature

**Every materialised state object records the last log position it was built from:**

```
source          rows   last_day   sha256    built_at
hp_log.tsv      412    77         3f9a…     2026-09-10T14:02
interactions    288    77         c81e…     2026-09-10T14:02
```

Then **staleness is a comparison, not a judgment.** `brief.py` can say
*"⚠ campaign.sqlite is 14 interaction rows behind"* instead of me noticing five weeks
late.

**The precedent: `light.py` already warns when `inventory.tsv` disagrees with the
computed oil pool — and that warning caught the same drift TWICE, including this
session.** Generalising it is the player's idea and it is the right generalisation.

**It applies to prose too, and gives a gentler tool than banning figures outright:** a
markdown block that legitimately caches a number carries `<!-- watermark: hp_log@412
-->`, and a test fails when the watermark falls behind. `party_roster.md`'s CURRENT
STATE block is *deliberately* three expeditions behind — with a watermark that becomes
a stated fact instead of a hope.

### 0.2 · Applying the concept fixes two things in my own draft schema

| | the draft had it as | it is actually | so |
|---|---|---|---|
| **`loops.tsv`** | rows with a mutable `closed_day` — **i.e. state pretending to be a log** | a **LOG of loop events**: `open` / `close` / `supersede` | the open-loop list is **derived**, exactly like `hp.py`. Nothing to keep in sync |
| **`people.tsv`** | identity *and* status *and* condition in one row | **identity is REFERENCE; condition is LOGGED** | `id`/`name`/`aliases`/`kind`/`first_day` are stable, so they make a safe FK target. *"Ancel departed"*, *"Cuddy is frail"* are **dated log rows** |

**That second one matters more than it looks.** *"Cuddy is frail (d6=1, day 76)"* is not
a property of Cuddy — **it is an event with a date**, and filing it as a property is how
*"Unanswered. He will not sit in the square forever"* survived for 43 days.

---

## 1 · THREE DECISIONS, SETTLED

### 1.1 · The TSVs *are* the command log. There is no redundancy and no diff check

**I wrote the first draft in a way that implied two copies cross-checking each other.
That was wrong.** The logs **generate** the database; it is a materialised view, not a
second store.

**The repo already proves the pattern:** `world_changes.tsv` is a log of operations
(`--scope edge --target 22,9,H --change spiked_shut --qty +4`) replayed by
`world.py replay`, whose own help says *"world_changes.tsv is the source of record; the
map database is a cache."* **That is event sourcing, it is the most robust thing here,
and it has never produced a geometry error.**

**So the two checks are different things and must not be conflated:**

| | |
|---|---|
| **STALENESS** | *was the view rebuilt from the current logs?* → **one watermark comparison** |
| **VALIDITY** | *does every name resolve? does every close cite evidence?* → **the log validated against itself.** Not a comparison of copies |

### 1.2 · An operations log, NOT raw SQL

| | raw SQL log | **operations log** |
|---|---|---|
| Expressiveness | maximal | a verb must be added when a new need arises |
| **Append-only by construction** | **NO. `UPDATE` and `DELETE` exist, and a logged `UPDATE hp SET … WHERE day=46` is a rewrite of the past wearing an append's clothes** | **YES. There is no UPDATE verb** |
| Semantic validation | foreign keys only — and **no FK can express *"a closed loop must cite the event that closed it"*** | `log.py` refuses it |
| Readable by the player | poorly | `world_changes.tsv` rows read almost like prose |

**The append-only row decides it.** Raw SQL would hand me the one weapon `CLAUDE.md`
marks as absolutely forbidden.

### 1.3 · Reads ad-hoc, writes never — and it is enforced, not merely policy

| | |
|---|---|
| **Writes** | **only** through `tools/log.py`. Never SQL, never by hand |
| **Reads** | **anything, including ad-hoc `SELECT`** — that is exactly where a database earns its keep, on joins that cannot be run today |

**Everything except the builder opens the DB read-only** — `file:campaign.sqlite?mode=ro`.
A stray `UPDATE` raises an error instead of silently rewriting the past.

> **And the honest note on git, because it was load-bearing in the first draft and
> should not have been:** I have never run `git diff` on a campaign TSV. What git
> actually gives this repo is **commit messages as a campaign index that survives
> context loss**, and **checkpoints before `/compact`**. `CLAUDE.md` already says so:
> *"Git is the safety net for the PROSE, not for the game state."* The two real
> arguments for the TSV format are **grep** — a great deal of this campaign lives in
> free-text `notes` columns — and **append-only by construction.**

---

## 1.4 · THE DEMAND SIDE — what most needs to be on hand

**Built by asking what I actually reach for during play, ranked by frequency × cost to
get it now × how often it has gone wrong.** This is the justification for the schema
below, and it turned up one thing the schema was missing entirely.

### Tier 1 — needed constantly, currently prose or **in my head**, with a track record

| what | where it lives now | errors |
|---|---|---|
| **The day** | `calendar.md` prose | day drift, player-caught on Torsat's illness |
| **Who is available** — present / away / hurt / dead | **nowhere.** Re-derived every time: *"Hask on the wool, Rowe with Halm, so eight"* | — |
| **Open loops** | nowhere | **4** |
| **Funds, committed vs free** | a ~4,000-char notes blob; `finances.md`, which says it is not a source of truth | **5** |
| **⚠ Who knows what** | **nowhere at all** | ≥2 — *"a fact nobody in this room mentioned"* · *"Halm genuinely does not know about the barrel"* |
| **⚠ LIVE ENCOUNTER STATE** | **entirely in my own narration** | **1, and it was the worst** |

### ⚠ The encounter gap, which was not in the plan at all

A fight runs ten messages. Across them I hold: round · initiative order · who is
engaged with what · **who held an action** · each monster's remaining hp · surprise ·
what is spiked · light. **All of it by re-reading my own previous messages.**

> **That is the "narrate from my own summary" failure mode operating in the
> highest-stakes context in the game** — and the day-70 violation, where I resolved the
> party's round without asking, happened in exactly that context.

**`encounter.tsv`** — append-only log of the live fight; round, combatant hp and
conditions **derived**. `combat.py` reads it, and can then **refuse an undeclared party
action**, because it knows whose turn it is and that nothing has been declared.
**Slotted into phase 3** — small, independent of the migration, and it hardens the
context where errors cost most.

### Tier 2 — needed per scene, partly covered

One person's full history (`recall.py` exists, cannot join) · last reaction and
standing loyalty adjustment (prose) · what they have been promised (prose) ·
**spell loadouts** (`spells.tsv`, *"no tool reads it yet"*) · goods with **weights** ·
what is still unexplored (derivable from `cells.seen`, never surfaced).

### Tier 3 — already good, **leave alone**

`hp.py` · `xp.py` · `light.py` · `clock.py` · `mapdb` · `world.py deployed` ·
`rules.py` · `combat.py`'s resolution · `dice.py`.

### And three conclusions that change the design

**1 · ⚠ Almost nothing should be materialised, because the data is tiny.** ~7,000
rolls, a few hundred entities, a few hundred interactions. **Rebuilding the whole view
is milliseconds.** So **default to derived**; materialise only what is genuinely
expensive (`mapdb`, which does image extraction) or what a human wants to read.
**Category 3 nearly disappears — and what does not exist between calls cannot rot.**
Watermarks therefore matter in two narrow places, not everywhere: **`mapdb`, and prose
blocks that legitimately cache a figure.**

**2 · "Who knows what" needs no new file — knowledge is DERIVED FROM PRESENCE.** Who
was in the room is already logged (`interaction_person`); what was said is already
logged (`interactions`). **So it is a join.** It is also the one query with a spoiler
dimension, which is exactly why it should be structural rather than remembered.

**3 · There are three different kinds of "on hand", wanting three different tools** —
and the first draft conflated all three into `brief.py`:

| | shape | tool |
|---|---|---|
| **Briefing** — session start, after a compact | broad, shallow | `brief.py` |
| **Scene** — this moment, this person | narrow, deep | `recall.py` as a query |
| **Encounter** — live, mutable within a fight | small, fast, rewritten every round | `encounter.tsv` + `combat.py` |

---

## 2 · THE SCHEMA

### 2.1 · Existing logs: UNTOUCHED

`hp_log` · `rolls` · `world_changes` · `light` · `clock` · `encounters` · `spells` ·
`party` are already append-only operation logs with 185 tests behind them.
**Migrating them buys nothing. Leave them.**

### 2.2 · ⚠ `inventory.tsv` — the defect the log/state distinction exposes

**It is the one campaign file edited *in place*. It is a category-3 object with no
watermark. And it is the file that has rotted five times** — the carts (40 days), the
mules, the small goods (357 gp, 17 days), the six ropes (11 days), the oil (twice).

**That is not a coincidence, and I had not connected it until this conversation.**

> **`inventory.tsv` becomes a LOG plus computed state**, exactly like hp, xp and oil.
> *"Never quote a running total from a prose file"* has a sibling: **never store one in
> a hand-edited cell either.**
>
> **This is a bigger win than the database.**

### 2.3 · New logs

#### `campaign/interactions.tsv` — the join table, and the biggest single win
```
day  seq  place      people      kind         d6s      reaction  summary                           evidence
77   3    wethersby  Wend,Dave   counsel      2,4,6,4  -         carriage gap; Osk no view; run    sessions/day-077.md
76   1    wethersby  Ottir,Dave  counsel      2,2,4    -         roof: ask who mended it last      sessions/day-076.md
34   2    wethersby  Ancel,Wend  negotiation  -        127       four buyers; 1d/lb for 3 years    sessions/day-034.md
```
`kind`: `first_contact | counsel | negotiation | promise | payment | grievance |
teaching | report | conflict | fact`

`people` is a **comma list on purpose** — it must be typeable at the table. The build
normalises it; **the validator refuses any name that does not resolve.**

> **Social events live ONLY in prose today. That is why class D is the largest error
> class in this campaign.** Every misremembered conversation — how Kell died, Sim's two
> years, Ista's grievance scope, Cuddy toward Yrtone, *"the plan was to arrive on the
> 51st"* — is a query against this table that could not be run.

#### `campaign/loops.tsv` — a log of loop events
```
day  loop  verb        subject     expected_day  evidence  what
55   L019  open        wace        -             55:4      receipt for the account of movables
65   L019  close       wace        -             65:2      receipt arrived, recites the contents
72   L024  open        wool_party  83            72:6      back from buying; Nan grading
76   L031  open        cuddy       -             76:1      who mended the chapel roof last, and who paid
77   L032  open        wend        -             77:3      the party must say HOW MUCH and WHOSE money
```
**`close` requires `evidence` resolving to a real interaction or event.** A loop cannot
be closed with a flag — **closing requires citing the thing that closed it**, which is
precisely the step skipped on art. 11.

> ### ⚠ WHAT MAY NOT GO IN HERE — the test is: *does it have a moment at which it stops being true?*
>
> | | |
> |---|---|
> | **LOOP** | *"the wool party back ~83"* · *"Ancel returns in spring"* · *"the receipt is coming"* |
> | **LOGGED FACT** → `interactions` with `kind=fact` | *"Cuddy is frail"* · *"Ancel departed"* |
> | **FINDING** → `articles.md` | *"gifts land badly, work lands"* |
>
> **If facts get in here the list grows monotonically, I stop reading it, and it becomes
> the next `CHECKLIST.md`.**

#### `campaign/money.tsv` — append-only, `asset_id` NOT NULL
```
day  delta   asset_id      qty  counterparty  interaction  reason
67   -2.4    rope_50ft     6    -             67:1         six ropes for the barrel descent
67   -24     rations_std   8    -             67:1         eight person-weeks standard
71   +30     ale_barrel_sd -1   holt          71:4         first half of 58 gp for the SD cask
65   +250    lab_glass     -1   toller        65:2         full valuation, paid on Wace's receipt
76   -10     service       -    cuddy         76:2         almonry account, art. 14
```
**Funds become `SUM(delta)` — derived, never stored.** Synthetic asset ids
(`service`, `wages`, `lodging`, `toll`, `licence`) keep the constraint satisfiable
without inventing goods for a lodging payment.

**This replaces the `funds` row's notes column in `inventory.tsv` — currently a
~4,000-character prose blob holding every transaction in the campaign. All five
class-B errors are purchases recorded in that blob and nowhere else.**

### 2.4 · New reference files

```
campaign/people.tsv   id  name  aliases  kind  first_day  notes_ptr
campaign/places.tsv   id  name  aliases  kind  parent  days_from_wethersby
campaign/assets.tsv   id  name  kind  unit_weight
```
**Identity only. No status, no condition, no location** — those are logged.

**`places.tsv` kills two live errors:** *Wetherby / Wethersby*, both spellings present
in this repo and some of them typed by the player; and the **distance table, which
lives in `calendar.md` prose and was misquoted once** — Fenn's→Ede's read as *"a day"*
when it is eight miles and a couple of hours.

### 2.5 · The materialised view

`campaign/output/campaign.sqlite` — **gitignored**, built by
`tools/build_campaign_db.py`, **opened read-only by everything else.**

```sql
people        (id PK, name, kind, first_day)
person_alias  (alias PK, person_id → people)
places        (id PK, name, kind, parent_id → places)
place_alias   (alias PK, place_id → places)
assets        (id PK, name, kind, unit_weight)
edges         (id PK, x, y, orient, level)          -- imported from mapdb

interactions       (id PK, day, seq, place_id → places, kind, reaction, summary, evidence)
interaction_person (interaction_id → interactions, person_id → people, role,
                    PRIMARY KEY (interaction_id, person_id))

money         (id PK, day, delta, asset_id → assets NOT NULL,
               interaction_id → interactions NULL, counterparty_id → people NULL)

loop_events   (id PK, day, loop_id, verb, subject_person_id → people NULL,
               expected_day, evidence_interaction_id → interactions NULL,
               CHECK (verb <> 'close' OR evidence_interaction_id IS NOT NULL))

events        (id PK, day, exped, turn, kind, place_id, edge_id → edges NULL)
event_person  (event_id → events, person_id → people)

build_meta    (source PK, rows, last_day, sha256, built_at)   -- THE WATERMARK
```

**Four already-happened errors the keys make impossible:**

| the error | what it really was | the key |
|---|---|---|
| **The spike phantom negative** — two correcting rows, the first over-corrected to 7 | **two labels for one door**, `(14,29,H)` and `(14,28,H)`, ledger holding +2 at one and −2 at the other | `edge_id → edges`. One door, one identity |
| **`wrought hanging iron −1`** | an orphan — minus one object sitting in a corridor | a qty cannot go negative against a referent never emplaced |
| **Area 9's glass**, still shown in the room 7 days after it was carried out | a row whose referent moved, with nothing linking them | `asset_id` + a location that must resolve |
| **Wetherby / Wethersby** | two towns where there is one | `place_alias` |

### 2.6 · Tools

| tool | |
|---|---|
| **`tools/log.py`** | **THE ONLY WRITE PATH.** `interaction` · `loop open|close` · `money` · `inventory`. **Validates every name and every close-citation before appending.** This is what makes a foreign key *block* instead of merely *catch* |
| **`tools/loops.py`** | `open [--day N] [--subject X]` · `due --day N` · `history L019` |
| **`tools/brief.py`** | session-start briefing: day · positions · hp · xp · funds · light · spikes · **open loops** · last N interactions · **⚠ any stale watermark** |
| **`tools/ledger.py`** | `check` — money with no asset, assets that moved with no money |
| **`tools/recall.py`** | **rewritten as a query.** Every interaction, promise, payment, wound and roll for one person, in order, with citations |
| **`tools/stale.py`** | compares every watermark against the live logs. **Runs inside `brief.py` and in the test suite** |

### 2.7 · Tests

| test | what it forbids |
|---|---|
| `test_entities_resolve.py` | a name in `interactions`/`money`/`loops` not present in `people`/`places`/`assets` |
| `test_loops_close_evidentially.py` | a `close` with no evidence, or evidence resolving to nothing |
| `test_double_entry.py` | money with no asset; an asset quantity that moved with no money |
| **`test_watermarks.py`** | **any category-3 object whose watermark is behind its source** — including watermarked prose blocks |
| `test_no_cached_figures.py` | **generalises `test_lane_rule.py`** — no prose file may restate a computed figure **unless it carries a current watermark** |
| **`test_checklist_shrinks.py`** | **`CHECKLIST.md` growing in the same commit that adds a test.** The ratchet that makes phase 6 real |

---

## 3 · PHASES

### Phase 0 — free, today, no code
- **Pre-commit the die mapping in `--reason` before rolling** — *"d6: 1-2 no view, 3-4
  partial, 5-6 already thought it through."* Today the roll is auditable and the
  interpretation is not, because I pick the direction after seeing the number.
- **Never cite a ⚠ box without grepping for the event that discharges it.**

### Phase 1 — loops and the briefing · *kills class A*
`loops.tsv` · `loops.py` · `brief.py` · `stale.py` ·
`test_loops_close_evidentially.py`. **Seed it by walking `CHECKLIST` §11 and every ⚠
box in `articles.md` — that walk IS the first audit.**
**No database, no migration. Play resumes immediately after this.**

### Phase 2 — the auditor · ✅ BUILT 2026-09-11 · *the only net under "I said it and logged nothing"*

**Split in two, which was the right call and came out of the discussion: a third
of the errors in this campaign were plain arithmetic and needed no language
model at all.**

#### 2a · `tools/audit.py` — deterministic, and it cannot be forgotten

Checks the figures in a block of text against the tool that owns each one.
**Catches all seven of the real historical number errors** — funds 595 vs 1,072,
spikes 3 vs 9, Tristle 641 vs 712, Yrtone 6/7 vs 7/7, 19 flasks vs 18, 2 ropes
vs 8, 171 tests vs 198 — **and stays silent on correct text, which is the harder
requirement.**

> **The design constraint that mattered more than coverage: it must not cry
> wolf.** A checker that fires on a true statement teaches me to ignore it, and
> an ignored checker is prose again.
>
> Three mechanisms enforce that: a figure is checked **only when an anchor
> phrase for that quantity is within 80 characters of it**; a sentence naming a
> campaign day **other than today** is treated as historical and skipped; and
> the report **always prints how many figures went unchecked**, so coverage is
> visible rather than implied.
>
> **The bug that proved the point:** the first implementation compared every
> figure in a sentence against every anchor in it, so *"19 sealed flasks and 2
> ropes"* reported the rope count as a bad flask count, and *"Dave is at 9/9 and
> Yrtone is 6 of 7"* produced four findings from two facts, two of them wrong.
> `_nearest()` fixed it and `test_audit.py` holds the line.

**Wired into `tools/hooks/pre-commit`** (`git config core.hooksPath tools/hooks`).
**It BLOCKS** — a warning that does not block is prose. Escape hatches are
`audit-skip` in the line, which is self-documenting, or `--no-verify`, which is
not. `dlwork/`, `deprecated/`, `tools/tests/` and `audit.py` itself are skipped,
because their whole job is to quote the wrong numbers on purpose.

#### 2b · the `auditor` agent — `.claude/agents/auditor.md`

Read-only, `Bash Read Grep Glob`, **citation or nothing.** One line per
assertion; three verdicts (`SUPPORTED` / `CONTRADICTED` / `UNSUPPORTED`) and no
others; **a verdict with no citation may not be emitted.**

> ### ⚠ AND EVERY VERDICT NAMES ITS SOURCE TIER
>
> **The evidence base contains files known to be wrong.** `npcs.md` is *the*
> file that misleads the DM, so contradicting him out of it could be the auditor
> repeating the very error it was built to catch, wearing a badge.
>
> | tier | | weight |
> |---|---|---|
> | **1 EVIDENCE** | `campaign/*.tsv` · `mapdb` · `git log` | authoritative |
> | **2 AUTHORITY** | `rules/` · `bestiary/` · the PDFs | authoritative for rules and monsters |
> | **3 INDEX** | `npcs.md` · `articles.md` · `calendar.md` | **suggestive, never conclusive** |
>
> **Tier 1 beats tier 3 and the auditor reports both — that disagreement is
> itself a finding, because it means a prose file has rotted.**

**Explicitly out of scope for the agent:** figures (they belong to `audit.py`,
exactly and for free — *running an exact answer past a language model makes it
approximate*), dialogue being invented now, and **tone, plausibility,
characterisation or quality.** An auditor that offers judgment becomes another
voice to argue with, and then it gets overridden.

**And it may not read `modules/B1_DM_NOTES_DO_NOT_READ.md` or
`modules/private/`.** A claim checkable only against those returns
`UNCHECKABLE — DM-only source` and nothing further. *A hint is a spoiler with
deniability.*

| trigger | on what | how it fires |
|---|---|---|
| **every commit** | the staged diff's added lines | **the hook. Automatic** |
| **before the player sees it** | turns asserting what an NPC said or did · turns writing a finding or rule | **the DM invokes the agent** |
| **while he reads** | ordinary play turns | held back until we see what it catches |

**219 tests pass** (185 → 198 after phase 1 → 219 now).

### Phase 3 — money and inventory become logs · *kills class B*

#### 3a · money · ✅ BUILT 2026-09-11

`campaign/assets.tsv` (**reference — identity only, no quantities**),
`campaign/money.tsv` (**log, `asset` required**), `tools/ledger.py`,
`tools/log.py`, `tools/tests/test_ledger.py`. **The purse is now `SUM(delta)`,
computed, and `brief.py` and `audit.py` both take it from the ledger rather than
from the `inventory.tsv` cell** — a checker must not check a figure against a
copy of itself.

**THE ARCHAEOLOGY, and its finding:** the 4,910-character notes blob on the old
`funds` row **reconciles exactly from day 39 onward** —
`595.6 −25 +61 +235 −31 −1.1 +250 −42.4 +30 = 1,072.1`, which is what the cell
said and what the tools compute. **Before day 39 it does not.** The day-34 chain
lands about a gold piece away from the day-35 opening figure and the blob does
not say where the difference is.

> **That is the finding, not a failure: a running total kept in prose stopped
> being reconcilable somewhere around day 34 and nobody could have known.**
> Inventing eight rows to close a 1 gp gap would put false precision into an
> append-only log, so days 1–38 are **one anchor carrying the narrative**,
> exactly as the day-39 XP anchor does in `encounters.tsv`.

**The service ids** (`wages`, `lodging`, `licence`, `loan`, `kit`, `service`)
are not a fudge. Money leaves the purse for things that are not goods, and
without them the double-entry rule would be **unsatisfiable on its first real
use** — and a rule that cannot be obeyed is a rule that gets quietly broken.

**`tools/log.py` is the gate.** It refuses a money row with no asset, an asset id
not in `assets.tsv` (and suggests the near miss), a zero delta, a campaign day
running backwards, and an unknown character. **Validate on write, rebuild on
read.**

#### ⚠ AND TWO REAL BUGS FOUND WHILE BUILDING IT — both pre-existing, both silent

**1 · Short rows are read with every later field shifted one column left.**
`tsvlog.read_tsv` pads short rows *on purpose* (a trailing note left off is
still a usable event), so a line missing a **middle** field is misread in
silence. It happened twice within an hour of `money.tsv` being written by hand.
`log.py` now always writes the full width.

**2 · TWO EVENTS GLUED BY A MISSING NEWLINE, invisible since 2026-08-28.**
Checking field counts across every campaign log found two over-wide rows, and in
both cases **the second event had never been read by any tool**:

| | lost |
|---|---|
| `clock.tsv` | **round 959 — Yrtone casting cure light wounds on Dave** |
| `world_changes.tsv` | **the square (20,8) marked SEEN** — so the map believed the party had never looked at a square they walked through |

**`world.py replay` went from 404 applied changes to 405 once the line was
split.** `test_no_campaign_log_has_an_over_wide_row` now guards every log, and a
second test names both recovered rows so a future merge cannot re-glue them.

#### 3b · inventory becomes a log · ✅ BUILT 2026-09-11 — **and the `unit` column is the player's design**

`campaign/inventory_log.tsv` + `tools/inventory.py`. The old `campaign/inventory.tsv`
is **retired to `deprecated/`** with a full explanation, so no citation is orphaned.

> ### THE OLD `qty` CELL WAS PROSE PRETENDING TO BE A NUMBER
>
> Every tool that read it took the first integer it could find:
>
> | the cell | read as | |
> |---|---|---|
> | `~2.5 IRON + 8 STANDARD` | **2** | **two things crammed into one cell** |
> | `1,072 gp 1 sp` | **1** | |
> | `~100 lb, ~97 gp` | **100** | a **weight** read as a **count** |
> | `18 sealed (+1 broached)` | 18 | right by luck; the broached flask invisible |
> | `8 (7 sound, 1 damaged)` | 8 | right by luck — **and the damaged rope is the one that nearly dropped Blartho** |
>
> **Three of those were simply wrong.** Now: **one row per `(asset, condition)`, and
> the `unit` is what forces the split** — you cannot write "2.5 person-weeks of iron
> and 8 of standard" into a single signed quantity. The unit vocabulary is **closed
> and tested**, so a typo is a failure rather than a second silent unit.

**AND THE SECOND HALF: ONE FACT, ONE HOME.** Two long-standing duplications are gone,
and with them the cross-checks that existed only because the duplication did:

| | was | now |
|---|---|---|
| **Oil flasks** | counted in `inventory.tsv` *and* derived in `light.tsv`. **Drifted apart twice** | `light.py reserves()` takes `sealed` from the pool. **The disagreement warning is deleted — there is nothing left to disagree with** |
| **Iron spikes** | a hand-kept "carried" figure beside a separate emplacement log. This is how the ledger showed a phantom negative and needed two correcting rows, the first over-correcting to 7 | **`carried = owned − emplaced`, derived** |
| **The purse** | computed by `ledger.py` *and* stored in a cell | one home; the cell cross-check is gone |

> **A tool that compares a figure against a copy of itself was never a check — it was
> an early warning that the design was wrong.** All three warnings are now deleted, and
> deleting them is the improvement.

**Also: the `weight`/`weight_unit` split in `assets.tsv`, same reasoning, and it has
teeth in 1e** — DMG Appendix O counts encumbrance in **gp weight, ten to the pound**,
while every merchant and cart in the fiction talks in **pounds**. The SD barrel is
**460 lb and 4,600 gp weight**, and the mule-capacity ruling turns on not confusing
them. And `money.tsv` gained a `unit` column because 1e has five coin types: the day-39
anchor records *"28 ep off the orc bodies, +14"* and **the electrum survives only in
that prose**, because the conversion happened before the column existed.

#### 3c · `encounter.tsv` · ✅ BUILT 2026-09-11 — **the day-70 error made impossible**

`campaign/encounter.tsv` + `tools/encounter.py`, and **a gate inside
`combat.py round`.**

> ### `combat.py round` REFUSES to roll for a character who has not declared
>
> ```
> REFUSED: Torsat has not declared an action this round.
>   ASK THE PLAYER, then:  python tools/encounter.py declare <who> "<what they said>"
>   Choosing for them is the day-70 error: four attack rolls voided at round 285.
> ```
>
> **`CHECKLIST`'s ⚠⚠ *THE DM DOES NOT DECLARE THE PARTY'S ACTIONS. EVER. ASK.*
> stops being a sentence and becomes a required input.** It names exactly who is
> missing, which is the difference between a gate and an obstacle.

**Two things the gate gets right that a naive one would not:**

- **A HELD action is a declaration.** Day 70 had two of them — Blartho and
  Dellie held, ready to close or cast — and a gate that read "held" as "said
  nothing" would refuse the one round the DM got right.
- **A declaration does not carry into the next round.** Actions are declared
  every round, not once per fight.

**It is a speed bump and not a wall**, and the tool says so: the DM could type a
declaration the player never made, exactly as he could log a move `party.py`
never routed. **That tool has held for two expeditions anyway**, because the
friction arrives at the instant of the error rather than in a file read at the
start of a session.

**And the state is computed, not remembered:** round, initiative, who declared,
who held, who is out, and **monster hit points — `--hidden`, never shown
otherwise.**

#### ⚠ AND A THIRD HOLE IN THE ROLL LOG, found by building this

`dice.roll()` logs by default, which is right for play. `tools/tests/conftest.py`
closed that for **pytest only** — and **driving `combat.py` from a shell to check
the new gate put three real d20s into `campaign/rolls.tsv` within a minute of the
gate being written.** Same hole, other door.

**`dice.ROLLS` now honours `$DND_ROLL_LOG`.**

> **And then the test written to guard it opened the leak itself.** The first
> version called `importlib.reload(dice)`, which reset `dice.ROLLS` to the module
> default and **undid the conftest fixture**, and the suite immediately wrote 56
> rows into the campaign log. **A test for a leak that opened the leak.** It runs
> in a subprocess now; a full suite run moves the file by zero lines. Both batches
> are voided in place by appended rows — **nothing deleted, because the log is
> append-only.**

**266 tests pass** (185 → 198 → 219 → 239 → 252 → 266). **Phase 3 is complete.**

### Phase 4 — canonical entities and the prose split · ✅ BUILT 2026-09-11 · *kills class D, the largest*

**`campaign/people.tsv`, `campaign/places.tsv`, `campaign/interactions.tsv`,
`tools/entities.py`, and `campaign/sessions/` — 24 files, days 32 to 77.**

#### The split

**3,075 lines of session write-ups moved out of `npcs.md` into
`campaign/sessions/day-NNN.md`, verbatim and complete**; 470 lines of reference
stayed. Every session file opens with a banner saying **ARCHIVE — read for
pleasure and for quotes, NEVER to answer a question**, and a test enforces it.
`npcs.md`'s own header now points at the tools instead of at itself.

> **The prose is the best thing in this repository. It is archived, not
> deleted.** What changed is that it is no longer where an answer comes from.

#### The query the campaign never had

```
$ python tools/entities.py who Ancel
Ancel  (npc)   first appears day 32
3 scene(s):
  day 32   first_contact  reaction 11    BADLY FRIGHTENED -- pulled to 81 when Dave took his mail off
  day 34   negotiation    reaction 127   *** THE ANSWER TO ANCEL'S QUESTION, TWO DAYS AFTER HE ASKED IT ***
  day 35   first_contact  reaction 114   Brokered by Wend. Marrow bought him his dinner
```

**That is the 43-day error, answered in one command.** The prose said
*"Unanswered. He will not sit in the square forever"* until day 77.

#### Identity is reference; condition is an event

`people.tsv` holds only what is stable — id, name, aliases, kind, first day —
and **a test forbids a `status`, `condition` or `reaction` column.** *"Cuddy is
frail"* is not a property of Cuddy; it became true on day 76 and was rolled for,
so it is a scene with `kind=fact`. **Filing that sort of thing as a property is
precisely how the Ancel line outlived its answer.**

#### And a name must RESOLVE

| | |
|---|---|
| **Wetherby / Wethersby** | both are in this repo, some typed by the player → one place |
| **"Rell's brother" / Gyll** | one man whose name nobody used for two years → one person |
| **Father Cuddy / Cuddy**, Reeve Ottir, Master Wace, Father Doule | titles resolve |

`entities.py check` refuses a scene naming somebody who does not exist **and
suggests the near miss in both directions**. It also enforces that `day:seq` is
unique, because `money.tsv` and `loops.tsv` cite scenes as `"77:3"` and that must
mean exactly one thing.

#### ⚠ And the phase-3a test caught a defect in a file written ten minutes earlier

`test_no_campaign_log_has_an_over_wide_row` failed on **`places.tsv:31`** — an
extra empty field in the `fenns` row, which would have shifted `days_from_wethersby`
into `parent` for exactly the holding whose distance had already been misquoted
twice. **The mechanism catching its own author is the strongest evidence it works.**

**280 tests pass** (185 → 198 → 219 → 239 → 252 → 266 → 280).

### Phase 5 — the view, the keys, validate-on-write
`build_campaign_db.py` with the schema above · `build_meta` watermarks · `log.py`
validating against the view before appending · `recall.py` as a query ·
`test_watermarks.py` · `test_no_cached_figures.py`.

### Phase 6 — **the ratchet, and it is NOT OPTIONAL**
For every rule a test now covers: **delete the instruction from `CHECKLIST.md`** and
keep the reason inside the test's docstring and assertion message. Then
`test_checklist_shrinks.py` holds the line.

> **The gate, so the trade cannot go bad:** delete the prose **only** when the test
> covers the same ground **and** its failure message says everything the prose said.
> `test_lane_rule.py` is the worked example — 25 lines of failure history in its
> docstring, and an assertion that reads *"THE TRIGGER IS GONE."*
>
> **I have done the fun half of this twice and never the deleting. That is why the file
> is 1,470 lines and why its own §11 sat 38 in-game days stale.**

---

## 4 · WHAT THIS KILLS — AND WHAT SURVIVES IT

| class | n | after |
|---|---|---|
| **A** stale forecast | 4 | **gone** — phase 1 |
| **B** money moved, no row | 5 | **gone** — phase 3, blocked at the write |
| **C** computed figure cached | 8 | **gone** — watermarks, phases 3 and 5 |
| **D** event from summary, not log | ~10 | **mostly** — phase 4, auditor behind it |
| **E** rule from memory | ~9 | **mostly** — refusing tools |
| **F** procedure violated | 3 | **blocked** — `combat.py --declared` |
| **G** geometry ad hoc | 6 | **already gone** since `party.py move` |

### ⚠ Stated plainly, what none of this fixes

- **"Do I need to check?"** is decided by the same faculty that is wrong. **Nothing
  blocks it.** The auditor only catches it afterwards.
- **A loop I never open is in no table.** The auditor's `UNSUPPORTED` verdict is the
  only net, and it is a soft one.
- **Arithmetic in my head.** The 51%-by-weight calculation behind the fourth finding
  was checked by nothing and still would be. *(Later candidate: unit weights on
  `assets.tsv` and a `carriage` query.)*
- **A validator can only check that a name resolves, never that the row is true.** I
  can log a well-formed interaction that never happened.
- **Tone, character, spoiler judgment, whether a scene is any good.** These stay prose
  **permanently** — and they are what `CHECKLIST.md` should shrink down *to*.

---

## 5 · CAN WE PLAY WHILE THIS HAPPENS?

| phase | play? |
|---|---|
| **0 · 1 · 2** | **yes** — purely additive. **Resume at day 78 as soon as phase 1 lands** |
| **3** | yes, with care — funds and inventory go computed mid-stream |
| **4** | **no.** One sitting, files moving |
| **5 · 6** | yes |

**Recommended: build 0–2, resume play, take 3–6 at the next natural pause.** That puts
the auditor in place *before* the disruptive migration, which is also what makes the
migration safe.

---

## 6 · WHY THIS IS NOT ALSO A WEB PAGE

**It would be a second copy, outside git, that diverges from the repo — the exact
defect this document exists to remove.** It lives here, `git log` carries its history,
and **it gets deleted as it is executed.**
