# Restructuring the campaign's information — a brainstorm

**Written 2026-09-10, campaign day 77, play paused mid-departure for expedition 9.**
The player's framing: *"it seems like we're spending more and more time correcting
things, it's inevitable as the game expands — there are more locations, NPCs, items."*

He is right that it is growing, and right that it is getting worse. But the growth is
not the whole cause, and **the cause determines the fix**, so this starts with a
diagnosis rather than with a schema.

---

## 1 · WHAT ACTUALLY FAILS — the taxonomy, taken off the record

Every row below is drawn from errors the player caught and the repo logged. Not
theory.

| | class of error | instances | can a machine prevent it? |
|---|---|---|---|
| **A** | **Stale forecast.** A ⚠ note that predicted something, left standing after it fired | art. 11's receipt (**11 days**) · Ancel "unanswered" (**43 days**) · `CHECKLIST` §11 (**38 in-game days**) · "Rowe until his foot heals" | **YES, completely** |
| **B** | **The money moved and the thing got no row** | small goods, 357 gp untracked 17 days · **2 carts, 40 days** · 2 mules · 6 ropes, 11 days · dragon scales | **YES, completely** |
| **C** | **A computed number cached in prose** | thief 30% vs **25%** · the XP line · the equipment list · `map_known.md` · the oil count (**twice**) · the rope count · "171 tests" · "expedition 5" | **YES — proved** |
| **D** | **An event narrated from my own summary instead of the log** | how Kell died · Sim's two years · Cuddy toward Yrtone · Ista's grievance scope · "the barrel was never moved" · the area 29 chest · Lyde's board · "the plan was to arrive on the 51st" · Meg and Tibb as two families · "you nearly forgot Wend" | **PARTLY — make retrieval cheaper than recall** |
| **E** | **A rule applied from memory instead of from `rules/`** | the lane rule **×3** · a d12 on a d6 table · the 0-level attack column · p.63 reactions at friends **×4 in one hour** · re-rolling settled reactions | **MOSTLY** |
| **F** | **Procedure violated** | declared the party's combat round · invented a glass-fragility mechanic mid-scene · rolled a d100 on a PC's own negotiating | **YES — make the tool refuse** |
| **G** | **Geometry re-derived ad hoc under narrative pressure** | the spike coordinate split · the graded trail's extent · walking through a wall | **ALREADY FIXED** |

**Note what the big classes have in common.** A, B and C are not memory failures at
all — they are **bookkeeping failures with no double-entry and no close-out**. D is a
retrieval failure. Only E and F are really about me.

---

## 2 · THE ONE FINDING THAT SHOULD DRIVE EVERY DECISION

**Three mechanisms in this repo have a perfect record. All three are machines that
cannot do the wrong thing.**

| | it had failed | since the machine |
|---|---|---|
| `party.py move` — **routes through mapdb and physically cannot cross a wall** | freehand narration walked the party through one | **never again** |
| `tools/tests/conftest.py` — **physically cannot write to `campaign/rolls.tsv`** | **125 test runs wrote ~3,875 rows** into the campaign's own die log | **never again** |
| `test_lane_rule.py` — **will not let a paraphrase carry the figure** | prose failed **three times**, including a warning that said it had already failed twice | **never again — and it caught a fourth on its first run** |

**And the converse, which is harsher: every prose warning in this repo has failed
again after being written.** Including the warnings about prose going stale.
`CHECKLIST.md` is **1,470 lines of rules that exist because prose failed**, and it is
prose. Its own §11 sat 38 in-game days out of date *while telling the reader that
snapshots rot.* `articles.md` art. 11 had a ⚠ box that fired on day 65 and was quoted
as live on day 77.

> ### THE DESIGN RULE
>
> **A rule that has failed twice must stop being a sentence and become something that
> cannot do the wrong thing.** Everything else is decoration — including this file.
>
> **Corollary: every enforceable line that becomes a test must be DELETED from the
> prose.** If the tooling grows and `CHECKLIST.md` does not shrink, the project has
> got worse, because unread instructions are worse than absent ones.

---

## 3 · THE OPTIONS

### 3.1 · SQLite as a DERIVED CACHE over the TSVs — **recommended, and the big one**

Not "move the campaign into a database." **Keep `campaign/*.tsv` as the append-only
source of record** — git-diffable, editable at the table, and already guaranteed by
171→185 tests — and build `campaign.sqlite` that is **rebuilt from them by a script**.
This is exactly the `mapdb/` pattern, which is the most successful thing in the repo.

**What it buys that nothing today can do:**

- **`recall.py` becomes a real query.** Every utterance, promise, reaction, wound and
  transaction for one person, in order, with citations. It exists now and it reads
  seven TSVs; it cannot join.
- **Joins nobody can perform today:**
  - *which NPCs are owed something, and by what day*
  - *every gift given and the reaction it drew* — this would have produced the
    gifts-fail/work-lands finding automatically instead of by my noticing
  - *every good with money against it and no asset row* → **class B, dead**
  - *every reaction roll ever made for person X* → **class E's p.63 error, dead**
- **Class D gets cheap.** The reason I misremember is that `npcs.md` is 3,300 lines,
  so I grep and get a fragment and fill the gaps. A query returns the whole of one
  person.

| pros | cons |
|---|---|
| Answers questions that cannot currently be asked at all | A schema to design, and it is the one irreversible-ish decision here |
| Keeps git as the safety net and append-only as the guarantee | **The ETL is the real work:** facts are currently buried in prose paragraphs inside `notes` columns |
| Proven pattern in this repo | Two representations to keep honest — mitigated by `check` commands, as mapdb does |

> **⚠ The DB must stay DERIVED.** If it becomes authoritative we lose git-diffable
> evidence, the append-only guarantee, and the ability to fix a row at the table. That
> is a bad trade for query convenience. **SQLite, not Postgres** — no ops, no
> concurrency need, and `mapdb` already proves it here.

### 3.2 · Split reference from narrative — **highest value per hour**

**`npcs.md` is two documents wearing one filename:** a roster of current facts, and
~3,000 lines of session write-ups. So is `articles.md`. So was `party_roster.md`,
which is why its CURRENT STATE block had to be marked superseded.

- **Roster → TSV**, one row per person, small enough to hold in context *entirely* and
  therefore small enough to be right.
- **Narrative → `sessions/day-NNN.md`** — **archive, not reference.** Never read to
  answer a question; read for pleasure and for quotes.

| pros | cons |
|---|---|
| Attacks class D directly and mechanically | Requires discipline about which file a new fact goes in |
| No new technology, can be done in an afternoon | The prose is genuinely good and must be **archived, never deleted** |
| Makes the roster testable (every person has a location, a status, a last-seen day) | A one-time migration of 3,300 lines |

### 3.3 · Open loops as data — **cheapest big win**

One row per forward-looking commitment: `opened_day · owner · what · expected_day ·
closed_day · closed_by · evidence`. `loops.py open` prints what is live.

**This kills class A outright** and replaces `CHECKLIST`'s *"Owed in the fiction"*
prose block — which has itself gone stale twice.

| pros | cons |
|---|---|
| Four known instances, all with the same shape | Needs the habit of opening a row when a ⚠ thought occurs |
| Doubles as the session-start agenda | Nothing else |

### 3.4 · Double-entry for money and goods

Every coin movement gets a matching asset leg; `ledger.py check` **fails on an
unmatched leg**. Kills class B — five instances, one of which ran 40 days.

It is also, pleasingly, exactly what Wend keeps saying in the fiction. *"I spent six
days separating your money from the venture's money."* The joke is that she was right
about the tooling.

### 3.5 · Tools that REFUSE

Extend the `party.py move` principle to the procedures that have failed:

| tool | what it should refuse |
|---|---|
| `combat.py` | a **party** attack roll without `--declared "<what the player actually said>"`. The day-70 violation becomes impossible |
| `reaction.py` *(new)* | a p.63 roll for anyone with a prior logged encounter. **Four violations in one hour** |
| `dice.py` | a notation that does not match the named table's range — the d12-on-a-d6-table error |
| `rules.py` | already does this well: renamed heading → loud failure, not a plausible wrong table |

### 3.6 · Subagents — two very different proposals, and only one of them is good

**3.6a · Domain agents that NARRATE** ("the Wend agent", "the combat agent", "the
enterprise agent").

| pros | cons |
|---|---|
| Smaller corpus each, so more of it fits in context | **An agent that narrates has exactly my failure mode with less context. It relocates class D, it does not fix it** |
| Parallelism across independent threads | **No merge exists for character.** Two agents each holding a view of Wend produce two Wends, and nothing reconciles them |
| Could enforce local consistency | **The surprise boundary multiplies.** Today exactly one process may read `B1_DM_NOTES_DO_NOT_READ.md`. With N agents that is N boundaries, and the failure mode is spoiling your own campaign |
| | **They cannot see the table.** Tone continuity inside a scene is most of what this campaign is made of |

**Verdict: not yet, and probably not ever for narration.** Possibly worth it for the
*enterprise*, which is the one thread that is genuinely separable, mostly numeric, and
has no spoiler surface — Wend's operation now runs without the party by design.

**3.6b · Read-only researchers and an AUDITOR, under a citation contract** —
**recommended.**

An agent whose **only permitted output is rows of evidence with `file:line`**. No
conclusions, no narration. It burns its own context on the search and hands back
something checkable.

> ### AND THE AUDITOR IS THE SINGLE MOST VALUABLE ITEM ON THIS LIST
>
> At the end of each session, an agent **diffs what I narrated against the logs and
> reports contradictions.**
>
> **That is the job the player has been doing by hand, and it has caught roughly
> thirty errors.** Nine in one day. Automating the player's audit is worth more than
> any schema.
>
> It is also the safest possible agent: **it holds no state, authors nothing, and
> every claim it makes comes with a citation.**

### 3.7 · A session-start briefing command

One command prints: day · where everyone is · hp · XP · funds · light · spikes · open
loops · the last N events. Right now I reconstruct that from four prose files, **which
is precisely where the class-C and class-D errors come from.** `git log --oneline` was
the existing answer and it is good; a tool is better.

---

## 4 · WHAT I WOULD NOT DO

| | why |
|---|---|
| **Postgres** | No ops budget, no concurrency, no second reader. `mapdb` already proves SQLite here |
| **Make the DB authoritative** | Loses git-diffable evidence and the append-only guarantee — the two things that have actually saved this campaign |
| **Auto-generate narration** | The prose *is* the product. Nothing here should write it |
| **Add tools without deleting prose** | Twelve tools plus a 1,470-line checklist is already at the edge of what I reliably retrieve. **More instructions I forget to follow is not an improvement** |
| **Rebuild what already works** | `mapdb`, `world.py`, `light.py`, `xp.py`, `hp.py` and `rules.py` are not the problem. **Not one geometry error since `party.py move` shipped** |

---

## 5 · RECOMMENDED ORDER

| phase | what | kills |
|---|---|---|
| **1** | open-loops table · double-entry `check` · **split roster from narrative** · briefing command | **A, B, most of C, much of D** |
| **2** | `campaign.sqlite` as a derived cache + a real `recall` query | **the rest of D** |
| **3** | tools that refuse: combat declaration · reaction gate · dice-table gate | **E, F** |
| **4** | **the auditor agent** | the residue, and it is the backstop for everything |
| **ongoing** | **`CHECKLIST.md` shrinks as tests absorb it** | the file's own weight |

**Phase 1 is most of the value and needs no new technology.**

---

## 6 · QUESTIONS FOR THE PLAYER

**The four that fork the design are being asked directly.** These are the softer ones,
for the discussion:

1. **How much of the prose do you want to keep reading?** The write-ups in `npcs.md`
   are, to me, the best thing in the repo. I want to archive them somewhere they stay
   readable, not bury them.
2. **Do you want the auditor's findings in front of you, or fixed silently?** My
   instinct is **in front of you** — you have caught things an auditor would not, and
   the corrections have themselves become rules.
3. **Should the enterprise become semi-autonomous in the fiction as well as the
   tooling?** Wend's wool operation now runs without the party by design. It is the
   one thread that could be resolved between sessions and reported.
4. **Is there anything you want to be able to ASK that you currently cannot?** That is
   the best possible input to a schema, and better than anything I would invent.
