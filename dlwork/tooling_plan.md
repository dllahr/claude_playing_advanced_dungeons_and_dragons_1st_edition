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

### Phase 2 — the auditor · *the only net under "I said it and logged nothing"*
`.claude/agents/auditor.md`. Read-only. **Citation or nothing:** one line per factual
assertion, verdict `SUPPORTED` / `CONTRADICTED` / `UNSUPPORTED`, each with
`file:line`. **No opinions on tone, plausibility or quality** — an auditor that offers
judgment becomes another voice to argue with, and then I start overriding it.

| trigger | on what |
|---|---|
| **before the player sees it** | turns asserting what an NPC previously said or did · turns writing a **finding or rule** into `articles.md` / `CHECKLIST.md` / `rules/` |
| **in the background while he reads** | ordinary play turns |
| **at every commit** | everything narrated since the last one |

**Deliberately ahead of the migration:** it works on greps alone, so it pays from day
one — and it is the right instrument for the phase-4 archaeology.

### Phase 3 — money and inventory become logs · *kills class B*
Extract `money.tsv` from the `funds` notes blob — **the archaeology, and where the
remaining unbooked purchases will surface.** Convert `inventory.tsv` to a log plus
computed state. Then `log.py money`, `ledger.py check`, `test_double_entry.py`.

### Phase 4 — canonical entities and the prose split · *kills class D, the largest*
1. `people.tsv`, `places.tsv`, `assets.tsv` — **identity only**.
2. **`npcs.md`'s ~3,000 lines of write-ups → `sessions/day-NNN.md`. ARCHIVED, NEVER
   DELETED.** Read for pleasure and for quotes, never to answer a question. **The
   prose is the best thing in this repo.**
3. `interactions.tsv`, seeded from those write-ups.
4. `test_entities_resolve.py`.

**The disruptive phase. One sitting, no play in it.**

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
