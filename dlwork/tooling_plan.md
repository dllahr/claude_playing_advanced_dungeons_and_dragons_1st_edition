# The plan — schema, phases, and what gets deleted

**Written 2026-09-10, play paused at campaign day 77.** The diagnosis and the options
are in `dlwork/tooling_redesign.md`; this is the buildable version of what we settled
on in discussion.

**Three decisions already made and not to be relitigated:**

1. **The TSVs stay the source of record.** Append-only, git-diffable, editable at the
   table. The SQLite DB is a **derived cache**, rebuilt by a script, gitignored —
   exactly the `mapdb/` pattern, which is the most successful thing in this repo.
2. **Validate on write, rebuild on read.** One entry point (`tools/log.py`) checks a
   row against the canonical entities *before* appending it to the TSV. That is what
   turns a foreign key from "a red build later" into "you cannot write this row."
3. **Every enforceable line that becomes a test gets DELETED from the prose.** If
   `CHECKLIST.md` does not shrink as `tools/tests/` grows, the project has got worse.
   **Phase 6 is not optional.**

---

## 0 · THE SCHEMA

### 0.1 · New TSVs — the source of record

Five new files. Nothing existing is thrown away.

#### `campaign/people.tsv` — the canonical roster
```
id        name      aliases        kind       first_day  status    place      notes
wend      Wend      -              npc        11         active    wethersby  factor; art.1 succession
cuddy     Cuddy     Father Cuddy   npc        41         active    draycot    almoner, 3rd level cleric
ancel     Ancel     -              npc        32         departed  -          returns in spring; 1d/lb 3yr
```
`kind`: `pc | henchman | npc | hireling` · `status`: `active | away | departed | dead`

**This is extracted from `npcs.md`'s roster tables.** It is the half of that file that
is *reference*; the other half is narrative and goes to `sessions/`.

#### `campaign/places.tsv`
```
id          name        aliases     kind      parent          days_from_wethersby
wethersby   Wethersby   Wetherby    town      north_hundred   0
draycot     Draycot     -           hall      -               1
marchford   Marchford   -           town      -               3
basecamp    Coll's basecamp  -      camp      crag            1
```
**Two errors this kills outright.** *Wetherby / Wethersby* — both spellings are in this
repo, some typed by the player, and nothing reconciles them. And the **distance table
currently lives in `calendar.md` prose and was misquoted once** (Fenn's→Ede's read as
"a day" when it is eight miles and a couple of hours).

#### `campaign/interactions.tsv` — **the join table, and the biggest single win**
```
day  seq  place      people       kind            d6s      reaction  summary                            evidence
77   3    wethersby  Wend,Dave    counsel         2,4,6,4  -         carriage gap; Osk no view; run yes  sessions/day-077.md
76   1    wethersby  Ottir,Dave   counsel         2,2,4    -         roof: ask who mended it last       sessions/day-076.md
34   2    wethersby  Ancel,Wend   negotiation     -        127       four buyers; 1d/lb for 3 years     sessions/day-034.md
```
`kind`: `first_contact | counsel | negotiation | promise | payment | grievance |
teaching | report | conflict`

**`people` is a comma list on purpose** — it has to be typeable at the table. The
build normalises it into a proper join and **the validator refuses any name that does
not resolve to `people.tsv`.**

> **This file does not exist in any form today.** Social events live *only* in prose,
> which is why **class D is the largest error class in the campaign.** Every
> misremembered conversation — how Kell died, Sim's two years, Ista's grievance scope,
> Cuddy toward Yrtone — is a query against this table that could not be run.

#### `campaign/loops.tsv` — open items
```
id    opened_day  subject     what                                      expected_day  closed_day  closed_by       status
L019  55          wace        receipt for the account of movables       -             65          77:3            closed
L024  72          wool_party  back from buying; Nan grading             83            -           -               open
L031  76          cuddy       who mended the chapel roof last, who paid -             -           -               open
L032  77          wend        the party must say HOW MUCH and WHOSE money  -          -           -               open
```
**`closed_by` must resolve to an interaction or event row.** A loop cannot be closed
with a flag — **closing requires citing the thing that closed it**, which is the whole
step I failed on art. 11.

> ### ⚠ WHAT MAY NOT GO IN THIS FILE
>
> **The test: does it have a moment at which it stops being true?**
>
> | | |
> |---|---|
> | **LOOP** | *"the wool party back ~83"* · *"Ancel returns in spring"* · *"the receipt is coming"* |
> | **STATE — belongs in `people.tsv` / prose** | *"Cuddy is frail"* · *"Perrin refers upward"* |
> | **FINDING — belongs in `articles.md`** | *"gifts land badly, work lands"* |
>
> **If state gets in here the list grows monotonically and I stop reading it, and then
> it is the next `CHECKLIST.md`.**

#### `campaign/money.tsv` — append-only, and `asset_id` is NOT NULL
```
day  delta   asset_id      qty  counterparty  interaction  reason
67   -2.4    rope_50ft     6    -             67:1         six ropes for the barrel descent
67   -24     rations_std   8    -             67:1         eight person-weeks standard
71   +30     ale_barrel_sd -1   holt          71:4         first half of 58 gp for the SD cask
65   +250    lab_glass     -1   toller        65:2         full valuation, paid on Wace's receipt
73   -10     service       -    cuddy         76:2         almonry account, art. 14
```
**Funds become `SUM(delta)` — computed, never stored**, exactly like hp, xp and oil.

**`asset_id` is required, with synthetic ids** (`service`, `wages`, `lodging`,
`toll`, `licence`) so the constraint is satisfiable without inventing goods for a
lodging payment.

> **This replaces the `funds` row's notes column in `inventory.tsv`**, which is
> currently a **~4,000-character prose blob** carrying every transaction in the
> campaign. **All five class-B errors are purchases recorded in that blob and nowhere
> else** — the carts (40 days), the mules, the small goods (357 gp, 17 days), the six
> ropes (11 days), the dragon scales.

### 0.2 · The derived database

`campaign/output/campaign.sqlite` — **gitignored**, rebuilt by
`tools/build_campaign_db.py` from the TSVs plus `mapdb`.

```sql
people        (id PK, name, kind, status, place_id → places)
person_alias  (alias PK, person_id → people)
places        (id PK, name, kind, parent_id → places)
place_alias   (alias PK, place_id → places)
assets        (id PK, name, kind)
edges         (id PK, x, y, orient, level)        -- imported from mapdb

interactions  (id PK, day, seq, place_id → places, kind, reaction, summary, evidence)
interaction_person (interaction_id → interactions, person_id → people, role,
                    PRIMARY KEY (interaction_id, person_id))

money         (id PK, day, delta, asset_id → assets NOT NULL,
               interaction_id → interactions NULL, counterparty_id → people NULL)

loops         (id PK, opened_day, subject_person_id → people NULL,
               expected_day, closed_day,
               closed_by_interaction_id → interactions NULL,
               CHECK (closed_day IS NULL OR closed_by_interaction_id IS NOT NULL))

events        (id PK, day, exped, turn, kind, place_id, edge_id → edges NULL)
event_person  (event_id → events, person_id → people)
```

**Four already-happened errors that these keys make impossible:**

| the error | what it really was | the key |
|---|---|---|
| **The spike phantom negative** — two correcting rows, the first over-corrected to 7 | **Two labels for one door**: `(14,29,H)` and `(14,28,H)`, ledger holding +2 at one and −2 at the other | `edge_id → edges`. One door, one identity |
| **`wrought hanging iron −1`** | An orphan: minus one object in a corridor | qty cannot go negative against a referent never emplaced |
| **The area 9 glass**, still shown in the room 7 days after it was carried out | A row whose referent moved, with nothing linking them | `asset_id` + a location that must resolve |
| **Wetherby / Wethersby** | Two towns where there is one | `place_alias` |

### 0.3 · New tools

| tool | what it does |
|---|---|
| **`tools/log.py`** | **THE ONLY WRITE PATH.** `interaction` · `loop open` · `loop close` · `money`. **Validates every name against the canonical entities and refuses the row before appending.** This is what makes the FKs *block* rather than merely *catch* |
| **`tools/loops.py`** | `open [--day N] [--subject X]` · `due --day N` · `history` |
| **`tools/brief.py`** | The session-start briefing: day · positions · hp · xp · funds · light · spikes · **open loops** · last N interactions |
| **`tools/ledger.py`** | `check` — unmatched legs, assets that moved with no money, money with no asset |
| **`tools/recall.py`** | **rewritten as a query.** Every interaction, utterance, promise, payment, wound and roll for one person, in order, with citations |

### 0.4 · New tests

| test | what it forbids |
|---|---|
| `test_entities_resolve.py` | any name in `interactions`/`money`/`loops` that is not in `people`/`places`/`assets` |
| `test_loops_close_evidentially.py` | a closed loop with no `closed_by`, or a `closed_by` that resolves to nothing |
| `test_double_entry.py` | a money row with no asset; an asset quantity that changed with no money row |
| `test_no_cached_figures.py` | **generalises `test_lane_rule.py`** — no prose file may restate a figure that a tool computes |
| **`test_checklist_shrinks.py`** | **`CHECKLIST.md` may not grow in the same commit that adds a test.** The ratchet that makes phase 6 real |

---

## 1 · THE PHASES

### Phase 0 — free, today, no code
- **Pre-commit the die mapping in `--reason` before rolling.** *"d6: 1-2 no view, 3-4
  partial, 5-6 already thought it through."* Today the roll is auditable and the
  interpretation is not, because I choose the direction after seeing the number.
- **Stop citing a ⚠ box without grepping for the event that discharges it.**

### Phase 1 — loops and the briefing · *kills class A*
`loops.tsv` · `loops.py` · `brief.py` · `test_loops_close_evidentially.py`.
**Seed it by walking `CHECKLIST` §11's "Owed in the fiction" and every ⚠ box in
`articles.md`** — that walk *is* the first audit.
**No database, no migration. Play can resume immediately after this.**

### Phase 2 — the auditor · *the backstop for everything, including "I said it and logged nothing"*
`.claude/agents/auditor.md`. Read-only. **Citation or nothing:** one line per factual
assertion, verdict `SUPPORTED` / `CONTRADICTED` / `UNSUPPORTED`, each with
`file:line`. **No opinions on tone, plausibility or quality.**

**Three triggers:**

| when | on what |
|---|---|
| **before the player sees it** | turns that assert what an NPC previously said or did · turns that write a **finding or rule** into `articles.md` / `CHECKLIST.md` / `rules/` |
| **in the background while he reads** | ordinary play turns |
| **at every commit** | everything narrated since the last one |

**Moved ahead of the migration deliberately:** it works on greps alone, so it pays
from day one — and it is the right instrument for the phase-4 archaeology.

### Phase 3 — money double-entry · *kills class B*
Extract `money.tsv` from the `funds` notes blob — **the archaeology, and the place
where the remaining unbooked purchases will surface.** Then `log.py money`,
`ledger.py check`, `test_double_entry.py`. Funds become computed.

### Phase 4 — canonical entities and the prose split · *kills class D, the largest class*
1. `people.tsv` and `places.tsv` extracted from `npcs.md` and `calendar.md`.
2. **`npcs.md`'s ~3,000 lines of session write-ups → `sessions/day-NNN.md`.**
   **ARCHIVED, NEVER DELETED** — read for pleasure and for quotes, never to answer a
   question. The prose is the best thing in this repo.
3. `interactions.tsv`, seeded from those write-ups.
4. `test_entities_resolve.py`.

**The disruptive phase. Do it in one sitting, not across sessions.**

### Phase 5 — the database and validate-on-write
`build_campaign_db.py` with the keys above · `log.py` validates against it before
appending · `recall.py` rewritten as a query · `test_no_cached_figures.py`.

### Phase 6 — **the ratchet, and it is not optional**
For every rule now covered by a test: **delete the instruction from `CHECKLIST.md`,
keep the reason inside the test's docstring and its assertion message.** Then
`test_checklist_shrinks.py` holds the line.

> **The gate, so the trade cannot go bad:** delete the prose **only** when the test
> covers the same ground **and** its failure message says everything the prose said.
> `test_lane_rule.py` is the worked example — its docstring is 25 lines of failure
> history and its assertion reads *"THE TRIGGER IS GONE."*

---

## 2 · WHAT THIS KILLS, AND WHAT IT DOES NOT

| class | instances | after |
|---|---|---|
| **A** stale forecast | 4 | **gone** — phase 1 |
| **B** money moved, no row | 5 | **gone** — phase 3, blocked at the write |
| **C** computed number in prose | 8 | **gone** — phase 5/6 |
| **D** event from summary, not log | ~10 | **mostly gone** — phase 4, and the auditor behind it |
| **E** rule from memory | ~9 | **mostly** — the refusing tools |
| **F** procedure violated | 3 | **blocked** — `combat.py --declared` |
| **G** geometry ad hoc | 6 | **already gone** since `party.py move` |

### ⚠ What survives all of it, honestly

- **"Do I need to check?"** is decided by the same faculty that is wrong. **Nothing
  blocks it. The auditor only catches it afterwards.**
- **A loop I never open at all** is in no table. The auditor's `UNSUPPORTED` verdict is
  the only net.
- **Arithmetic in my head** — the 51%-by-weight calculation that produced the
  fourth finding was unchecked by anything, and still would be. *(Candidate for later:
  a weights column and a `carriage` query.)*
- **Tone, character, spoiler judgment, whether a scene is any good.** These stay prose
  **permanently**, and they are what `CHECKLIST.md` should shrink down *to*.

---

## 3 · CAN WE PLAY WHILE THIS HAPPENS?

| phase | play? |
|---|---|
| **0, 1, 2** | **yes** — purely additive. Resume at day 78 as soon as phase 1 lands |
| **3** | yes, with care — funds go computed mid-stream |
| **4** | **no.** One sitting, files moving |
| **5, 6** | yes |

**Suggested: build 0–2, resume play, then take 3–6 at the next natural pause.** That
gets the auditor running before the disruptive migration, which is also what makes the
migration safe.

---

## 4 · WHY THIS PLAN IS NOT ALSO A WEB PAGE

**It would be a second copy, outside git, that diverges from the repo** — which is the
exact defect this entire document exists to remove. The plan lives here, `git log`
carries its history, and it gets deleted as it is executed.
