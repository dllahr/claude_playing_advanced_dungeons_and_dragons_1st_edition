# Running this campaign — standing procedure

Everything below became standard because something went wrong once. The failure
that produced each rule is named, because the reason is what makes it stick.

A new session should be able to read this file and `CLAUDE.md` and pick up
without relearning anything.

---

## 1. At the start of a session

```bash
conda activate advanced_dnd_1e
git log --oneline | head -20           # what happened, when — CHEAPEST orientation there is
python tools/xp.py                     # current XP — never quote a stored total
python tools/hp.py                     # current hit points, likewise computed
python tools/world.py state --level 1  # what the party has done to the dungeon
python tools/world.py deployed         # party gear left in the dungeon
python tools/clock.py status           # round count and the wandering clock
```

- [ ] **Check the live sheet's date against actual play.** `party_roster.md`'s
      CURRENT STATE block carries an "As of" line. If it is behind the session,
      say so out loud before using anything on it.
- [ ] **Ask for current hp before combat**, not during. The sheet has been two
      expeditions stale more than once.
- [ ] **OIL IS A POOL, NOT A FLASK COUNT** — `python tools/light.py oilstate`.
      Topping up a lamp that still has fuel in it costs only the **difference**;
      the remainder **stays in the flask**, and the tool tracks that broached
      flask. A `refill` always draws, even with an explicit `--fuel` (that names
      the level brought up to, it does not make the oil free). `new --fuel N`
      *asserts* a level and draws nothing — a lamp found with oil in it.
      **The pool beats `inventory.tsv`'s count and warns when they disagree.**
      *(Built 2026-09-04. Before it, `refill` set the reservoir full and charged
      a whole flask regardless — the turns left in the lamp were thrown away
      twice, once out of the lamp and once off the count. The player caught it
      at expedition 6 round 197 with 4.4 turns in the lamp.)*
- [ ] Read `modules/B1_DM_NOTES_DO_NOT_READ.md` for the stocking key and prior
      rulings. **Never quote or summarise it to the player.**

---

## 2. Which file is authoritative for what

| question | source of record | never |
|---|---|---|
| how much XP has X earned | `python tools/xp.py` | a number written in prose |
| how many hit points has X | `python tools/hp.py` | the roster's CURRENT STATE block |
| what does the party carry | `campaign/inventory.tsv` | the outfitting list |
| what has the party **left in the dungeon** | `python tools/world.py deployed` | a note on the inventory line |
| what has the party **done** to the dungeon | `campaign/world_changes.tsv` → `world.py state` | your memory of last session |
| what has the party *seen* | **`cells.seen` in the map DB**, via `dmap.py at` | your own knowledge of the map, or a prose map |
| what is actually there | `mapdb/output/b1/b1.sqlite` | a crop read under pressure |
| the map vs an old note or narration | **the database wins** | preserving a distance somebody paced once |
| what round is it | `python tools/clock.py status` | counting back through the log |
| how a door opens **in B1** | **the module intro: d6, 1-2 locked, else it opens** | the PHB open-doors roll, which is for *stuck* doors |
| what a rule says | `rules/*.md` (via `tools/rules.py`), then the PDF page render | memory, or 1eonline |
| what a monster's stats are | `python tools/bestiary.py <name>` | the module's block, or memory |
| what treasure a monster has | `python tools/treasure.py --monster <name>` | memory |
| what has already been tried and failed | `mapdb/lab_notebook.md` | trying it again |

**The database supersedes earlier narration.** Ruled by the player 2026-08-25,
when the map put the crossroads' east arm 220 ft from the Room of Pools and
the since-retired `map_known.md` said 70 ft: *"the previous narration /
map_known.md is wrong. You can always supersede that with the new
map/database/connections."* Distances
paced in play before the map existed are estimates; the extraction is measured
and cross-checked three ways. **Do not stall the game to reconcile them** —
correct the note, say so, and carry on.

**Append, don't restate.** `campaign/encounters.tsv` gets one row per award and
no running totals, because a stored total goes stale silently. That is exactly
how the roster came to claim the party's iron spikes were in a door they had
already recovered them from.

---

## 2b. WRITING IT DOWN — which file each kind of event lands in

**Every one of these files went stale in play and was caught by the player, not
by me.** The TSVs are disciplined because tools read them; the **markdown files
have no tool and no test, so nothing fails loudly when they rot.** They are the
ones that need this list.

**The trigger is the event, not the end of the session.** A session that runs out
of context mid-scene loses anything not yet written.

| when this happens | write it here | same turn? |
|---|---|---|
| **A day passes, or any travel** | `campaign/calendar.md` | **YES — it drifts within two days** |
| A named person appears, changes their mind, or is hired | `campaign/npcs.md` | yes |
| Anyone joins or leaves the travelling party | `campaign/npcs.md`, the **who-is-actually-here** table | **YES** |
| Money in or out, or a purchase | `campaign/inventory.tsv` funds line, **with the arithmetic** | yes |
| A cargo bought, a manifest, freight | `campaign/cargo_manifest.md` | yes |
| A venture, share, or written agreement | `campaign/wool_venture.md` | yes |
| Something rolled about the world — a name, a distance, a fact about the district | `campaign/district.md`, **with the die** | yes |
| A rule looked up | `rules/*.md`, **with the page citation** | yes |
| A creature met | `bestiary/<name>.md` before the fight is over | yes |
| A ruling, a DM judgement call, a session beat | `modules/B1_DM_NOTES_DO_NOT_READ.md` | yes |
| The party changes the dungeon | `campaign/world_changes.tsv`, then `world.py replay` | yes |
| A standing instruction from the player | **here**, in this file, with the failure that produced it | **YES** |
| Anything a character asks to have **in writing** | `campaign/articles.md` — succession, authority, roles | **YES** |

### The four that rot silently, and how each one was caught

- **`calendar.md`** — was written *because* day numbers drifted, then **itself
  went stale at day 12 while play was at day 28.** A file being authoritative
  does not make it current. *(2026-09-02.)*
- **`npcs.md`** — its "Open" list still said *"nobody knows where the wool goes"*
  a fortnight after the wool was sold at Ludbury. **A resolved thread left in an
  open list is worse than no list**, because it reads as live. Strike it through
  and say what the answer was; don't delete it.
- **`wool_venture.md`** — stopped at day 16 and did not record the sale. **The
  numbers the party actually got are the ones that matter.**
- **`CHECKLIST.md` §11 itself** — said expedition 4 was in progress for two whole
  expeditions afterwards.

### Rules for the markdown files specifically

- **Supersede, don't rewrite.** Keep the old section, head it *(superseded)*, and
  put the new one above it. The guess and the roll that overturned it are both
  part of the record — see `district.md`'s note on Wend.
- **Never delete a resolved question.** Strike it and name the answer and the day.
- **Reconstructed dates get marked as reconstructed**, so the next reader knows
  which lines are load-bearing.
- **Record the die.** A rolled fact with its die is checkable; the same fact
  without it is something I made up.
- **Put the arithmetic in the note field**, not just the total — a total with no
  working cannot be audited when it disagrees with something. *(The 1,038 gp
  Ludbury spend had to be recovered out of the raw transcript because only the
  summary was ever written down.)*

---

## 3. Every combat round

```bash
python tools/combat.py round --target "berserker AC 7 HD 1" \
    --attack Dave:"long sword" Torsat:"long sword" Yrtone:"footman's flail"
python tools/combat.py monster --name berserker --hd 1 --target-ac 3 \
    --damage 1-8 --attacks 2
python tools/hp.py damage Dave 8 --reason "berserker, round 1" --exped 4
python tools/clock.py advance --action combat
```

`combat.py` prints the die, the target number and **every modifier with its
source**, which is what "roll in the open" means in practice. It does not
narrate, choose targets, or track monster hit points — those stay with the DM.

### HASK, DELLIE AND ISTA ARE CHARACTERS AS OF DAY 39 — roll them normally

**Fighter, Cleric and Thief, 1st level**, in `characters.tsv` with scores,
proficiencies and prime requisites. `combat.py round --attack Hask:"short sword"`
handles them. **Do not hand-roll them and do not reach for the monster matrix.**

Three things about them that will otherwise get played wrong:

- **Dellie may NOT use edged weapons.** The cleric prohibition took her spear
  away. Flail, sling, club, mace, staff, hammer.
- **Dellie is AC 6, not 3.** DEX 4 costs +3 defensive adjustment. Same mail, same
  shield, worse reflexes. She is also −2 on every missile.
- **Ista's CON 3** means −2 hp per die, **system shock 35%**, and she can be
  raised from the dead at most **three times ever** (PHB p.12).

**Monster xp is a FULL share for all three; treasure xp stays HALF.** See the
comment block at the top of `tools/xp.py` for why the two differ, and the day-39
anchor in `encounters.tsv` for why the switch did not rewrite history.

**For the NEXT 0-level NPC who joins** — and there will be one — the tables are
in **`rules/zero-level.md`**: DMG p.74 matrix I.B **column 0** (18 vs AC 3, not
the monster matrix, which is where these three wrongly lived for two
expeditions), and DMG p.79 Fighters row 0. **Recording a normal man as "1 hit
die" is what caused that error**; the MM gives him a flat 1-6 hit points and no
die at all.

### Tristle's spear is NON-PROFICIENT on purpose — do not "fix" it

`combat.py` applies **−3** to every spear attack Tristle makes (PHB p. 37, thief
proficiency penalty). His proficiencies are **long sword and short bow**.

**This is deliberate and the player knows.** He carries the spear because a spear
**reaches from the SECOND RANK** — in a ten-foot corridor with Dave and Torsat
filling the front, a long sword in Tristle's hands cannot reach anything at all.
A −3 attack that happens beats a +0 attack that is physically blocked.

So: do not query it mid-fight, do not "helpfully" swap him to the long sword, and
do not treat the penalty as a bug when it prints. If he steps into the front rank
the calculus reverses — then the long sword is right.

Note also his **elf +1 applies to long sword and short bow only**, never the
spear, so a spear thrust is −3 flat with no racial offset.

- [ ] **"SWITCH AND ATTACK" is the player's shorthand** and means: change weapon
      now, attack **at the earliest opportunity** — usually next round, but it may
      be this one if the target flees melee, is felled by someone else, or the
      situation otherwise frees them. **Enforce the weapon-change cost whenever it
      applies; just say that you are doing it.** *(Standing convention, player
      2026-09-04. The costs are in `rules/combat.md`, "Changing weapons in
      melee" — and note the SLING EXEMPTION: a sling is dropped, not stowed, so
      sling → flail is free.)*
- [ ] **Pause after each round for declarations.** Do not resolve two rounds in
      one go. *(Three rounds were once run without stopping and had to be
      retconned.)*
- [ ] **Before ANY missile attack, ASK ONE QUESTION FIRST: IS ANYBODY IN CONTACT?**
      *(This item used to state the penalty before the trigger, and that is how the
      DM got it wrong a THIRD time on 2026-09-08. The trigger comes first now.)*
      - **NOBODY IN CONTACT** — enemies at a distance, the party merely standing in
        a column — **NO PENALTY AT ALL. Range modifiers only. Every missile in the
        column fires.** *"Allies merely standing in front are not a melee"*
        (`rules/exploration.md`).
      - **SOMEBODY IS IN CONTACT** — then and only then does the lane rule bite,
        and **the exact figures live in `rules/exploration.md` and nowhere else.
        GO AND READ THEM.** They carry a second condition as well, which every
        paraphrase in this repo has dropped at least once.
      - **A natural 1 hits a friendly regardless**, whenever there is a melee to
        shoot into.
      *(Three darts were resolved with no penalty and no ally risk in expedition 4
      and had to be retracted. Then the opposite error, twice.)*
- [ ] **Report the result of every declared action.** Every attack, every spell,
      every search — including the misses. *(Tristle's spear attack was silently
      dropped twice.)*
- [ ] **Roll in the open** — attacks, damage, saves, morale, searches, all of
      it, with every modifier and its source. `tools/combat.py` prints that
      working for you. **The wandering check is the one exception** (§5).
- [ ] **NEVER GIVE THE PLAYER ANY CONCRETE MONSTER STATISTIC.** Not hit points,
      not hit dice, not Armour Class, not damage dice, not morale, not XP value,
      not number appearing, not "surprised on" — **and never paste a stat block
      or a bestiary dump.** Describe what the characters can see: what it looks
      like, how it moves, whether it is hurt, whether it flinched.
      *(Standing instruction, restated and widened by the player 2026-09-04
      after I printed a giant rat's AC, its hit-dice line and the individual hit
      points of all four of them. The old wording said only "never state hit
      points" and I read it narrowly. **It covers every number.**)*
- [ ] **You may still roll in the open** — that is the other standing
      instruction and it does not conflict. Show **the die, the target number
      and the modifiers on the PARTY's side**, and the outcome. What you must
      not do is say where the target number came from in the monster's terms, or
      how much of it is left.
- [ ] Cite rules pages for the party's own numbers freely. **Do not cite the
      bestiary or the Monster Manual at the player** — those are DM-side.
- [ ] **Check the monster's hp before narrating it surviving a hit.** *(A
      berserker was described shrugging off 7 damage when he had 5 hp.)*

---

### Things that STOP the narrative immediately

When one of these happens, **stop mid-move, discard every remaining declared
action, and ask.** Do not finish the movement that was ordered before the
discovery — the player gave that order without knowing this.

- [ ] **A secret or concealed door is found.** *(Asked for by the player
      2026-08-26, after Tristle spotted one in passing and the narration walked
      the party on past it to the far side of the room.)*
- [ ] **NEVER MOVE A CHARACTER TO MAKE AN OBSERVATION POSSIBLE.** If the declared
      position cannot see the thing, **they do not see it** — say what is blocking
      the line and offer the move as a choice. *(2026-09-04: the player had Dave
      "peek round the corner" at (27,29). I quietly stood him in (27,30) so he
      could see the east arm, then described a dead end, a door and a floor full
      of returning boot-prints — none of which is visible from where he actually
      was, and all of which put him alone ten feet ahead of the party holding the
      only light with his sword sheathed. The player caught it by asking which
      square he was standing on.)*
      **Corollary: state the square.** When a look depends on position, say where
      the character is before describing what they see.
      **AND TRACE THE LINE OF SIGHT ON THE MAP BEFORE DESCRIBING.** Twice in
      three exchanges on 2026-09-04 I described a door that was round a corner —
      first from (27,29), then again from (27,30) when the arm turns a SECOND
      time at (29,30). Corridors in this dungeon bend more than once. **Walk the
      squares in `dmap.py at` from the viewer outward and stop at the first
      wall**; do not assume a corridor runs straight because the last one did.
- [ ] **IN UNEXPLORED SPACE, ANYTHING NOTICED STOPS THE PARTY — anything at all.**
      A door, a side passage, a mark, a dropped object, a smell. Do not report it
      *en route* and keep narrating to the declared destination. **In new ground
      the party does not walk past things.** *(Standing instruction from the
      player 2026-09-03, after I reported a door mid-corridor and carried the
      move on to the far end anyway. Known ground is different — there, a
      declared destination stands.)*
- [ ] A wandering monster actually appears.
- [ ] A trap fires, or is detected.
- [ ] Any character reaches 0 hit points or below.
- [ ] Anything the party could not have anticipated when they declared.

The test is simple: **would they have given that order if they had known?** If
not, the order is void and the turn is theirs again.

---

## 3b. Experience — the two rules that get re-derived every time

- [ ] **XP is paid for what you TAKE OFF AN ENEMY, never for what you already
      own.** The line is **property, not geography**. Treasure experience prices
      *the guardian overcome* (DMG p.85's 1:1 to 4:1 bands, PHB p.106's downward
      modifier); **there is no band for "no guardian."** So: bandits and
      everything the bandits owned, yes, full rate. The party's own wool, its
      capital, its trade profit, a cargo stolen and retaken — **no**. Full
      working and citations in `rules/experience.md`.
      *(I first ruled this off "must be physically taken out of the dungeon",
      which is a LOGISTICS clause and collapses against PHB p.106's "one gold
      piece GAINED". Right answer, wrong reason, corrected 2026-09-01.)*
- [ ] **A LEVEL COSTS 1,500 gp PER LEVEL PER WEEK, for 1-4 weeks** (DMG p.86),
      and **XP FREEZES at the threshold until it is paid.** Nobody in this party
      can afford second level. This is why the wool venture exists and it should
      be said plainly whenever levelling comes up.
- [ ] **DMG p.25's 100 gp/level/month upkeep is NOT USED — house rule, settled
      2026-08-25.** Town costs are **1 gp per person per night**, which is what
      has been charged since expedition 1; a 150 gp deduction was reversed
      retroactively when the rule was set aside. Reasoning and the DMG quote are
      in `rules/equipment.md`, "Cost of living in town".
      *(I raised this again on 2026-09-01 as an unflagged gap. It was not a gap —
      it was a settled ruling, cached, with its reasoning. **Check `rules/` before
      flagging anything as missing.** Fresh research is not evidence that the
      cache is silent.)*

---

## 4. Monster mechanics

- [ ] **Use the DMG Attack Matrix for Monsters (p.75), not a character table.**
      They differ: a 1 HD monster needs **16** to hit AC 3, where a level-1
      fighter would need 17.
```bash
python tools/bestiary.py troglodyte              # the whole entry
python tools/combat.py monster --creature troglodyte --target-ac 3 --attacks 2
```

- [ ] **Check `bestiary/` first, then the MM** — never the module's stat block
      alone. B1 is statted for Basic D&D and disagrees; every bestiary file
      carries both readings side by side. Berserkers strike **twice, or once at
      +2**, and **never check morale** — none of which is in the module block.
- [ ] **Surprise is not always 1–2.** Read `Surprises On` off the creature and
      pass it: `combat.py surprise --surprised-on 4 --why "..."`. Troglodyte
      chameleon skin is **1–4**, and taking the default got two separate
      encounters wrong before the number was put in data.
- [ ] **A creature not in `bestiary/` gets an entry before the fight is over.**
      Render the MM page, read it, write the file, cite the page. It is ten
      minutes once instead of five minutes every time.
- [ ] **Morale is the DMG percentage system**, not Basic's ML 2–12.
- [ ] **Treasure**: `python tools/treasure.py --monster <name>`. Coin columns are
      **thousands** (hundreds for platinum); types **J–N are literal pieces per
      individual**.
- [ ] **XP is awarded on emerging from the dungeon**, per the module — not at the
      moment of the kill.

---

## 5. Wandering monsters

**`tools/clock.py` owns this now.** `start` pre-rolls the whole jitter series
and hides it; `advance` fires whatever is due and reports the anchor it came
from. The round count, the anchors and the jitter used to live only in the DM's
context and were all lost to one cleared session.

```bash
python tools/clock.py start --exped 4
python tools/clock.py advance --action move90 --why "corridor 1, mapping"
python tools/clock.py extra --why "hammering spikes"
```

- [ ] Checks anchor at **every multiple of 30 rounds**, 1 in 6 — B1 p. 4, *"every
      third turn of adventuring."* **This was 20 for the whole campaign** and ran
      the game at 1.5× the module's encounter rate; the cache asserted "20 rounds,
      the module's rate" with no page citation and the code trusted it. Fixed
      2026-08-30 off a page render. Changing `clock.ANCHOR` is **not enough** —
      the anchors live in `campaign/clock.tsv`, so use `clock.py reanchor --why`.
- [ ] Each fires at its anchor **+ (1d6 − 1)**, rolled in advance and hidden.
- [ ] **SAY NOTHING UNLESS A MONSTER TURNS UP.** No "the round-40 check fired,
      nothing there" — that tells the player the next twenty rounds are safe,
      which their characters cannot know, and an empty check should be
      indistinguishable from no check at all. When one does fire, describe the
      creature; **do not recite the dice.** Everything is in `campaign/clock.tsv`
      and `clock.py advance --show-checks` replays it. *(Asked for by the player
      2026-08-26, after several rounds of narrated empty checks.)*
- [ ] **The die says what, never where.** If the rolled approach is impossible —
      a sealed room, a corridor the party has bottled — relocate it to a
      plausible approach or void the encounter. Verify the approach exists:
      `python mapdb/dmap.py at <db> <level> <x> <y>`.
- [ ] **THE STANDING ROUTE IN AND OUT IS THE SECRET DOOR, NOT THE SHORT WAY.**
      `dmap.py path` and `party.py move` will route down the **x=16 corridor**
      because it is ~40 ft shorter. **That corridor runs under the MAGIC MOUTHS**
      at the third alcove pair. The one-way slab at **(17,13,V)** — spiked open
      since expedition 3 — emerges BELOW them, which is the entire reason the
      party props it. Always take the long way: down the spine to the four-way at
      (22,13), west along y=13, through the slab. *(Standing preference stated by
      the player 2026-09-01, after the pathfinder routed an exit west past the
      mouths AND past (17,21), where Kell is buried and Hask will not go.)*
- [ ] **Never let the pathfinder pick a route the player has named.** It optimises
      for distance and knows nothing about mouths, graves, or promises.
- [ ] **DOORS ARE CLOSED BEHIND THE PARTY BY DEFAULT.** Standing instruction from
      the player 2026-08-31. Do not ask, do not narrate them left open, and do not
      make them say it again. Spiking is still a separate declared action; this is
      only about the door being shut. *(It arose because area 5 and area 26 were
      both left standing open at the end of expedition 4 and both had been visited
      in the sixteen days between trips — the trophy room stripped of eleven
      spears and its dwarf gone through.)*
- [ ] **RESOLVE A CHECK AT THE ROUND IT FIRES — never bank one.** If the creature
      cannot reach the party at that round, the check is **SPENT** and they never
      knew it was there. Holding a rolled monster and placing it in their path
      later collapses the 30-round interval into nothing, is invisible in the log,
      and is usually a movement-rate absurdity besides. *(Caught by the player
      2026-08-30: a centipede rolled at round 2183 while the party was sealed in
      area 5 was parked in the corridor and met them at 2220 — two rounds before
      the next check fired. On the clock: 39 rounds. At the table: three.)*
- [ ] **BLOCKED is not ABSENT.** Void only when there is *no path at all* (a true
      dead end like area 7). A **spiked or barred door still has a corridor on the
      far side** — run the encounter *there* and let the barrier do its work.
      Voiding those would teach the player that spiking a door makes the party
      invisible, which is not what a spike does. *(Corrected 2026-08-29 at round
      1816: three voids in the area 5/6/7 pocket, and the fourth was two kobolds
      who shoved the spiked door, failed, and went away — having heard the camp.)*
- [ ] Extra checks only for genuinely loud events (hammering spikes, smashing
      doors, the magic mouths). **One extra, not one per action.**
- [ ] **No wilderness encounters.** Travel between town and the dungeon is
      narrated. *(Introducing them mid-campaign on a retreat, with the party
      half-dead, was unfair and was voided.)*

---

### Read the module's front matter FIRST

`rules/b1-module.md` holds every standing rule B1 states in its introduction.
**It was written after twenty hours of play**, because the door rule was
stumbled on by accident while grepping for something else — and reading the
introduction properly then turned up a second rule that had never been applied
at all: **the air in Quasqueton resists combustion.**

For any new module: **read the introduction end to end and cache it before the
room key.** General rules live there, they override the PHB/DMG procedure, and
nothing will ever prompt you to look.

---

## 6. Every rules question

**Look it up. Do not answer from memory.** In order:

1. `rules/*.md` — the verified cache. `python tools/rules.py --list` shows every
   table in it and flags any without a source line; `--show` and `--cite` print
   one. **`tools/combat.py` reads these same tables**, so a rule and the number
   the dice are compared against cannot drift apart.
2. Render the PDF page and read it: `d[p].get_pixmap(dpi=170).save(...)` then
   `Read` the PNG
3. **Add the table to `rules/` with its page citation**

Never trust: the OCR `.txt` for any number, or 1eonline for anything
load-bearing. Both have produced wrong answers here.

**Things that were got wrong from memory and are now cached:**

| got wrong | actually |
|---|---|
| to-hit, 2 HD vs AC 3 | 13, not 9 *(1eonline was wrong)* |
| elf minimum Charisma | 8 — a CHA 7 elf is illegal |
| starting gold | per class, not a flat 3d6×10 |
| several equipment prices | holy symbol 7 **sp**, rations 3 gp, rope 4 sp, dagger 2 gp |
| STR 8 encumbrance | **normal — only 3–7 are penalised** |
| monster to-hit | its own matrix, not the fighter table |
| non-proficiency | thief **−3** (cleric −3, fighter −2, M-U −5) |
| 0 hit points | unconscious to **−3 from the same blow**, then 1/round to −10 |
| monster morale "+1%/hit point" | the **+n in the hit dice**, not rolled hp — a 3+2 monster is 62%, a lucky 1 HD one is still 50% *(DMG p.67)* |
| Tristle's missile attacks | **+3 from DEX 18** (PHB p.11) *on top of* the +1 elf bonus — +4 with the short bow. This was not being applied |

All eight are now enforced by `tools/combat.py` and asserted in
`tools/tests/`, so they cannot come back through the code path.

---

## 7. Every geography question

**Query the database. Never re-derive geometry from a crop.** All six of the
original errors came from reading a map image under narrative pressure.

```bash
python mapdb/dmap.py at    <db> <level> <x> <y>   # terrain, area, every exit
python mapdb/dmap.py path  <db> <level> x0 y0 x1 y1   # squares, feet, turns, rounds
python mapdb/dmap.py reach <db> <level> --from-cell x y
python mapdb/dmap.py graph <db> <level>
```

- [ ] **PATH EVERY MULTI-SQUARE MOVE. Do not eyeball a route from a cell dump.**
      `dmap.py path <db> <lvl> x0 y0 x1 y1` cannot route through a wall; reading
      a column of cells can, and did. *(Expedition 4 round 1111: a query printed
      `(19,5) N=wall` on screen and the party was still walked from (19,5) to
      (19,6) — through it — and given a corridor opening that does not exist.
      The player caught it by reading the printed map. `path` reproduced their
      route exactly, first try.)*
- [ ] Movement has **THREE speeds**, not two *(PHB p. 102, verified)*:
      **1" = 10 ft per TURN** exploring and mapping; **5× faster on a known
      route** (90 ft per 2 rounds for this party); **10× faster fleeing or in
      combat** (90 ft per round). The middle one was missing for a whole
      expedition and known ground was run 4–5× too slow. `clock.py cost` lists
      them; `dmap.py path --rate` takes feet per turn.
- [ ] Mark what the party verifies by **logging it**, not by editing the DB:
      `python tools/world.py log --scope seen --target area:9 --change yes`.
      A rebuild wipes `cells.seen`; the log is what puts it back.
- [ ] **Do NOT keep a second map in prose.** `map_known.md` was exactly that and
      is now in `deprecated/`: it rotted two expeditions behind the database
      while still being cited. What the party has *seen* is `cells.seen`; what
      they *concluded* goes in `campaign/journal.md`, which is fiction, not
      geography.

### When the party changes the dungeon

Spiking a door, burning a tapestry, blocking a passage, looting a room — none of
it goes into the database by hand, because `mapdb/build.py` deletes and
recreates that file from the scanned page.

```bash
python tools/world.py log --scope edge --target 17,13,V --change spiked_open \
    --exped 4 --turn 58 --who Tristle --item "iron spike" --qty 2 \
    --note "two at the bottom"
python tools/world.py replay --db mapdb/output/b1/b1.sqlite --level 1
```

`dmap.py at` then reports the change beside the geography, which is the point —
there is no second file to remember to open mid-session.

- **Rows are events, not states.** Undo by logging the reverse, never by
  deleting a row.
- **Recovering gear must be logged too**, with a negative `--qty`. Nothing is
  inferred from a `revert`: a door can be unspiked with the spikes left on the
  floor.
- **`--map` matters.** Both maps have a level 1; filtering on level alone once
  applied all of Quasqueton's changes to the DMG sample dungeon and reported 73
  cheerful successes.

### The three independent checks, and what each is blind to

| check | finds | cannot see |
|---|---|---|
| **reachability** | walls that should not be there | a **door** that should not be there — it stays passable |
| **room extents vs stated size** | fabricated doors splitting a room | a secret door in a room with another way in |
| **module text sweep** | doors the image never drew | anything the text does not mention |

**All three are needed.** B1's area 18 had a fabricated door invisible to
reachability; area 9 had a secret door invisible to both automated checks and
only the text found it.

---

## 8. Spoiler discipline

- [ ] **`dmap.py at` ALSO PRINTS THE NAMES OF ROOMS THE PARTY HAS NEVER
      ENTERED.** A blocked exit still reports what is on the far side —
      `W wall -> (15,27) area 9 WIZARD'S LABORATORY (blocked)`. **Naming that
      room tells the player what is behind a solid wall.** Only ever name a room
      the party has been inside or been told about; for anything else the answer
      is "rock, and no opening." *(Player correction 2026-09-04, round 223: I
      read a laboratory's name off an `at` dump for a room they have never been
      near. The party knew area 5 was behind the other wall because they slept in
      it; the west side they knew nothing about.)*
- [ ] **`dmap.py at` prints secret doors. Do not read its output aloud.** It
      reports every edge on a square including `secret` and `one_way`, because it
      is a DM tool. Filter it against what the party has actually found before it
      becomes narration. *(A second secret door in area 25 was described to the
      player as visible and had to be retracted.)*
- [ ] **NPCs DO NOT SPEAK IN MECHANICS.** No character says "you only get one
      attempt", "that's a 35% chance", "roll for it", or "until you level up".
      Tell the *player* the number in your own voice, out of character — this
      table rolls in the open and wants the arithmetic — but **never put it in an
      NPC's mouth.** *(Player correction 2026-09-03: I had Ista say "if he's only
      got the one go at it." She has no idea what a "go" is.)*
- [ ] **THE TWO-VOICE PATTERN — the player's own fix, and it is better than
      just deleting the number.** *(Given 2026-09-05, after I had Ista say
      "anything I throw from behind Torsat is minus four with a coin-flip that I
      hit him instead.")* **Do not simply make the character vaguer and lose the
      mechanic.** Say the mechanic **in DM voice first**, plainly and with the
      arithmetic, and *then* let the character say the same thing the way a
      person would:
      > **DM:** *ranks 2 and 3 have no lane down a 10-ft corridor; a missile
      > through the front rank is −4 with a chance of hitting Torsat.*
      >
      > **Ista:** *"I'm not going to be firing through a crowd of people stood
      > in front of me."*
      **The player gets the number AND the scene.** This is the standing
      technique for every case where a character's reasoning is mechanical.
- [ ] **THE TSVs ARE EVIDENCE. THE PROSE FILES ARE AN INDEX.** *(2026-09-06,
      after NINE factual errors in one session, all caught by the player.)*
      CLAUDE.md already forbids quoting a running **total** from a prose file.
      **This is the same rule for EVENTS, and it is the big one.** `npcs.md`,
      `articles.md`, `journal.md` and every scene write-up are **summaries the
      DM wrote**. Three of the nine errors were believing one of those instead
      of the log underneath it: Kell's death (read my own note backwards), Sim's
      history (read "two years" as time away when it meant the SILENCE between
      him and his father), and Cuddy (ran him cold off a reaction score that
      described eight armed strangers at a gate, ignoring an evening of shared
      offices that followed).
      > **`rules/*.md` IS EVIDENCE TOO — it is not the prose category.** Those
      > files carry page citations, are parsed by `tools/rules.py`, and record
      > rulings already made. **Read the cache before re-deriving anything.**
      > *(2026-09-06: I spread nine people over three corridor squares by
      > re-reasoning about formation depth, when `rules/combat.md` already held
      > the ruling — made 2026-09-04 on the player's own argument — that three
      > ranks stand inside 10-11 ft, i.e. one square and a little.)*
      > **`python tools/recall.py <name>`** prints every logged event for a
      > character across all seven TSVs, in order. **Run it before narrating
      > anyone's past.** It exists because checking used to be awkward, and
      > awkward is why the rule kept getting broken.
- [ ] **PAST-TENSE GUARD — the single biggest tell.** Present-tense play has
      never been the problem: rolls, saves, encumbrance and rules lookups all go
      to the books and hold up. **Every error was retrospective colour** — *"she
      remembers…", "he'd been…", "when you fell…"*. Three were pure invention: a
      distance to Ede, a **sealed causeway report that never existed**, and Ista
      going under twice in the pool while nobody noticed *(the log says she was
      pulled out and given the party's FIRST cure, and that Blartho bled an
      extra round after her)*.
      **If you are writing a past-tense sentence about something that happened
      at the table and you have not opened the log, STOP.** Either check, or be
      unspecific. Vague is recoverable; a confident wrong detail is not.
- [ ] **A LOW ROLL DOES NOT LICENSE INVENTED BACKSTORY.** Rolled a **1** for
      Ista, went looking for a wound that would explain it, and **invented one.**
      **Reaction rolls describe MOOD, not history.** Find the reason in the
      record; if the record hasn't got one, a bad reaction is *mundane* — tired,
      distracted, a long day, bad news an hour ago. Wend's 26 and Toller's 36
      were both correctly played that way and both were better for it.
- [ ] **ESTABLISH IT IN DM VOICE BEFORE PUTTING IT IN A MOUTH.** Retracting a
      line of narration costs a sentence. Retracting a **speech** costs the
      character's coherence — Ista said *"what I want is the second one in a
      hand… not in a sack"*, and two messages later I offered the sack back as a
      compromise, which made her look like she didn't know her own mind.
      **Put the load-bearing claim in DM voice first. Let the character speak
      only once it has survived.**
- [ ] **MARK THE REACH.** When going past the record, say so inline —
      *"not in the log; I'm inferring"* — so the player can veto in one word
      instead of after a page of prose. **The player has been doing this QA and
      it should not be their job.**
- [ ] **AN `open` EDGE BETWEEN TWO OPEN SQUARES MEANS THE SPACE IS WIDER — NOT
      THAT THERE IS A DOORWAY.** *(2026-09-06, the passage north of (10,21).)*
      I read `(10,22) W=open` as *"an opening in the west wall"* and narrated two
      side passages and tracks turning into them. **There are no openings.** The
      passage is simply **20 feet wide** — x=9 and x=10 are the same corridor —
      and its real west wall is the `W=wall` on the x=9 column, with **area 10's
      secret door** the only thing in it.
      **The test: look at the square BEYOND the open edge.** If it is open floor
      with its own outer wall, you are inside one wide space. A doorway needs a
      `door`/`secret`/`archway` edge, or open floor that leads somewhere else.
      **`cells.width_ft` and `cells.passage` are NULL throughout B1**, so the
      database will not tell you the width — you must read the neighbours.
      *(This is the same root cause CLAUDE.md names for six earlier geometry
      errors: re-deriving layout ad hoc under narrative pressure. The player has
      the printed map; when he says a wall is a wall, check the neighbour columns
      before arguing.)*
- [ ] **RESOLVE A WANDERING CHECK SILENTLY, THEN REPORT ONLY PERCEPTION.**
      *(2026-09-06, twice in one hour, the second time badly.)* First I wrote
      *"the hammering brought something"* before verifying an approach existed.
      Then I wrote **"four orcs in that passage again"** into the player-facing
      reply — **naming the creature and the count** for an encounter the party
      could not perceive: it was behind a spiked slab, Tristle's Hear Noise
      failed at 73 vs 15%, and nobody else was listening.
      **The sequence is: fire the check -> decide WHERE -> decide whether the
      characters perceive anything -> narrate ONLY that.** Very often the honest
      answer is *nothing happens* and the player never learns a check fired at
      all. `clock.py` prints **THE DIE SAYS WHAT, NOT WHERE** for exactly this.
- [ ] **NEVER TELL THE PLAYER WHEN THE NEXT WANDERING CHECK FALLS.** *(Standing
      instruction, given 2026-09-06.)* `clock.py status` prints *"next check falls
      between round X and Y"* and it is right to keep that in the log — **it is
      wrong to put it in the reply.** The exact round was already hidden; the
      WINDOW must be hidden too. Knowing there is half an hour of safety before
      the dice look at you is the same as being told there is nothing in the
      corridor, and it lets the party spend risk it has not actually bought.
      **Track it carefully. Say nothing.** Report a check only when it FIRES, and
      then only through what the characters perceive.
- [ ] **`earned_by=all` MEANS THE SIX PCs. NAME HASK, DELLIE AND ISTA.**
      *(2026-09-06 — I wrote the guard in `xp.py` on day 39 and fell into it on
      day 46.)* `'all'` is **deliberately** the six full-share PCs, so the three
      cannot be swept into awards they were not present for. **When all nine
      fight, write `all,Hask,Dellie,Ista`.**
      Both expedition-7 monster rows went in as bare `all`, so the six were each
      **5 xp over** and the three got **nothing** — including Dellie, who killed
      the rat standing over Ista. **Fixed by an anchor computed with `xp.py`'s own
      arithmetic**, not by hand.
      > **The tell:** log an award, then run `python tools/xp.py` and **look at
      > the bottom three rows.** If Hask, Dellie and Ista did not move and they
      > were in the fight, the row is wrong.
- [ ] **OPEN LOCKS AND FIND TRAPS: THE LIMIT IS PER *OBJECT*, NOT PER LEVEL.**
      *(Misapplied 2026-09-06, player-caught.)* I told the party that because
      both thieves had used Find/Remove Traps on the pit trap, **neither could
      check a secret door found an hour later.** Wrong, and badly so — a
      per-level budget would make a thief useless in any dungeon with two traps
      in it.
      > PHB p. 28, locks: *"once per **lock**… no amount of trying will ever
      > enable him or her to succeed **with that lock**."*
      > Traps: *"accomplished **in exactly the same manner as opening locks**…
      > **One try only per thief** is allowed."*
      **"One try only per thief" means one try at THAT trap.** A failed pick on
      the armoury door does not spend Open Locks; it spends *that door*.
      **The player's worked example is the rule:** Tristle searched the side
      table in the wizard's bedroom and found nothing, so he never gets another
      try **at that table** — every other table in Quasqueton is a fresh roll.
      **And a FAILED trap check is not a clean bill of health.** It means the
      thief cannot tell. Say that, rather than "no trap".
- [ ] **IF A CLASS FUNCTION COVERS THE QUESTION, ROLL THE CLASS FUNCTION.**
      *(2026-09-06, the jammed pit trap.)* Tristle got a proper **Find/Remove
      Traps 25%** check. For Ista I improvised a **d6** "observation" roll instead
      — and she is a **thief with Find/Remove Traps 20%.** The improvised die
      quietly **denied her a roll she was entitled to**, and printing a bare "a 1"
      next to a percentile check made it read as a failed 20% when 1 would have
      been a *success*.
      - **The once-per-level limit on Open Locks and Find Traps is per THIEF, not
        per TRAP.** Two thieves get two attempts. That is part of what a second
        thief is FOR.
      - **Don't invent a d6 for something the rules already price.** Ad-hoc dice
        look like fairness and are actually the DM choosing the odds.
      - **Label the die when two kinds are in play.** "d6 = 1" beside "d100 = 38"
        is unreadable, and the player has to ask.
      **And when a roll fails, give the failure a REASON in DM voice or the
      character's** — *"she is nowhere near the mechanism"*, *"he has years and it
      wasn't enough; she has a week"*. A bare "nothing" is a worse scene than a
      stated one, and the player asked for this explicitly.
- [ ] **DO NOT MANUFACTURE AN NPC OBJECTION.** *(Caught by the player
      2026-09-05, Wend and the wool floor. The worst NPC failure of the campaign
      so far, and it took three exchanges to notice.)* **A sharp NPC generates
      sharpness whether or not there is anything to be sharp about**, and the
      material gets manufactured by **ignoring what the player already said.**
      What went wrong, concretely:
      - The player said *"I don't know the amount of wool"*, then *"as I said…
        **you'll need to calculate that**."* I had Wend object that **a share is
        not a unit of wool** — chastising him for the exact thing he had twice
        handed her as her job.
      - His price was anchored to *"what would have been 80 gold per share **in
        the last round**"* — rate-based, and therefore already immune to the
        two-years-vs-one-year volume question. I had Wend "catch" it anyway.
      - **Wend** raised the affordability worry; **Dave answered it flatly.** I
        then had Wend say *"you were frightening yourself over six hundred"* —
        putting her own anxiety in the player's mouth and having her be gracious
        about it. **Never hand an NPC a rhetorical win the player never conceded.**
      **AND DO NOT PAD A CONSEQUENCES LIST.** *(2026-09-07: after Dave broke with
      Bern I tabled "what the rupture touches" and put **Toller** in it, on the
      strength of Toller teaching Tristle for nothing and Bern teaching the party
      furniture for nothing. **An echo is not a consequence.** Bern and Toller
      have no recorded relationship whatsoever. The four real rows -- Ista's bed,
      Corm's bench and Ottir's surety, Wend's looms and spindles, Perrin's
      possible commission -- were weakened by a fifth that was there to make the
      list look four-square.)* **Every row in a consequences table must have a
      traceable path through the log. If it only rhymes, cut it.**
      **AND CHECK WHICH WAY THE ARROW POINTS.** The same table listed Perrin's
      possible commission and the loom-and-spindle work as things the rupture
      cost the PARTY. They are **business the party GAVE Bern** -- his income,
      not their exposure, and the loom work is the very PAID WORK he accepted
      at 68 when every gift landed at 8. **Before writing a consequence, ask
      whose asset it is.** Of four rows, three were Bern's and one -- Ista
      living there -- was awkwardness rather than cost.
      **THE TEST, before any NPC pushes back: re-read the player's own words and
      find the sentence that already answers it.** If it is there, the objection
      does not exist. An NPC may supply information, do arithmetic the player
      asked for, price a risk, or say what it costs — **all of that is texture
      and none of it requires the player to be wrong.**
      *(And when this does happen: fix it in DM voice as a retraction. Do NOT
      make the player spend a scene correcting an NPC for the DM's mistake.)*
- [ ] **How the one-attempt thief rules read IN THE FICTION.** Open Locks and
      Find Traps may not be retried until the thief gains a level. The character
      does not know that and must not act like it. **A failed roll means he
      worked at it until he was STUMPED** — he tried long enough to satisfy
      himself he cannot solve this one. He may keep fiddling all he likes; he
      simply will not get there. *(The player's framing, and it is better than
      the rule: it converts a bookkeeping limit into a fact about the character.)*
      Contrast **Hear Noise**, which the PHB explicitly allows to be repeated as
      often as desired.
- [ ] Make DM judgement calls silently and write them to the DM notes.
- [ ] Surface a rule only when a declared action actually invokes it.
- [ ] **Anything read with the `Read` tool appears in the transcript.** To check
      a secret door without spoiling the player, work from the module *text* and
      from measurements, and write findings to the DM notes — not into a reply.
- [ ] `campaign/` is player-safe.
      `modules/B1_DM_NOTES_DO_NOT_READ.md` is not.

---

## 9. When something is wrong

- [ ] **A RULES CORRECTION IS PROSPECTIVE, NEVER RETROACTIVE.** If the table has
      been playing something a certain way and you discover the book says
      otherwise, **the decisions already made under the old reading stand.**
      Announce the correct rule, say when it starts, and start it *then*.
      *(2026-09-04: the table had run "0 hp + cure light wounds = back in action"
      all campaign. I found DMG p.82's coma-and-a-week paragraph mid-scene and
      applied it to a cure the player had just spent on the old understanding.
      The player's own words: "the reason I cast CLW was based on the previous
      rule". Grandfather the incident; start the rule next time.)*
- [ ] **Say so plainly and immediately**, in play. Two corrections were issued
      mid-combat this campaign and both mattered to the player's decisions.
- [ ] **DO NOT OVERRIDE THE PLAYER'S OWN CONSTRUCTION WITH WORSE PHYSICS.** When
      a plan specifies how a thing is built or held, **adjudicate the thing they
      described**, not a vaguer version of it. *(2026-09-05: the player braced a
      10-ft pole ACROSS a 10-ft corridor, sides against the rising slabs. I
      adjudicated it as a beam bridging a 4-ft gap end-to-end, gave it a snap
      roll, and dropped a character. Wrong object, wrong loading, wrong outcome.)*
- [ ] **DO NOT PRESENT AS NEW INFORMATION SOMETHING THE PARTY HAS JUST WATCHED
      HAPPEN.** *(Same scene: I revealed "the trap resets" as a twist the plan
      hadn't accounted for, ten minutes after the party saw that exact floor close
      over six of their friends.)* Before framing a fact as a surprise, ask what
      they have already seen.
- [ ] **Do not invent geography to justify a die roll.** A "wall stub" was once
      invented to explain where monsters came from; it was retracted.
- [ ] **DO NOT ROLL A FACT THE GEOGRAPHY THEN HAS TO SUPPORT. CHECK FIRST.**
      *(2026-09-04.)* I rolled "does the worn path turn through this door?" at
      (24,29) **without first asking whether the room behind it has another
      exit.** It does not — area 36 is a dead end with one door — so the die
      produced a daily thoroughfare that goes into an empty room and stops. I
      then narrated a wear-arc on the threshold, a path crossing the room, eight
      steps out of the far corner and a change in the air, **none of which
      exists.**

      This is the same rule as §5's *"the die says WHAT, never WHERE"*, applied
      to narration instead of to monsters: **before rolling a fact about the
      dungeon's layout or use, query the layout.** If the roll's answer is
      impossible, it is void — do not build on it and do not rationalise it.
- [ ] **DO NOT INVENT AN INSTRUCTION THE PLAYER NEVER GAVE.** On 2026-09-02 I had
      Coll defend himself against a "hire nobody without me" order that **does not
      exist in the transcript**. What the player actually said was *"if there's
      anyone desperate around, who's out on the road - I need you bring them in"*
      and *"if people need work I trust your judgement"*, and later *"you did
      rightly to bring them in."* I made a competent NPC look timid and built a
      scene and a reaction roll on it. **The player caught it and was right.**
      An NPC's constraints come from the play record, not from what would make a
      better scene. **Grep the transcript before asserting what was ordered** —
      `~/.claude/projects/<project>/<session>.jsonl`, filter `message.role ==
      'user'`. **A reaction rolled against an invented premise is VOID** — say so
      and re-roll, as with a wandering monster that cannot reach the party.
- [ ] **Prefer "I don't know" to a reconstructed number.** The XP totals before
      expedition 3 are represented by a single anchor row for exactly this
      reason.
- [ ] Record the failure in `mapdb/lab_notebook.md` if it is a method that did
      not work, so it is not tried twice.

---

## 10. The map extraction pipeline

Read `mapdb/README.md` before touching it, and `mapdb/lab_notebook.md` before
trying anything clever. Both maps are driven by the same code with different
options — the differences are measured, not guessed, and the table of them is in
the README.

> ### `rebuild.sh` WAS SILENTLY ABORTING PART-WAY THROUGH. Read this.
>
> *(Found 2026-09-04, and only because a game query hit a table that should
> have had rows in it.)*
>
> The script runs under **`set -euo pipefail`**, and **`world.py replay` exits 1**
> whenever any log row fails to match the map — three legacy rows always do.
> **So the script died at that line every run**, silently skipping everything
> after it: the level-2 merge, the door review and the diagonal review. Level 1's
> numbers all printed correctly first, so nothing looked wrong.
>
> **The lower level vanished from `b1.sqlite` this way** and was not noticed for
> an hour of play.
>
> **Two rules out of it:**
> - **NEVER run a rebuild with its output suppressed.** No `>/dev/null`, no bare
>   `tail -3`. If you must filter, filter and then check the LAST line is the one
>   you expect. I hid this from myself with `>/dev/null 2>&1`.
> - **A step that legitimately exits nonzero needs `|| echo …`, not `|| true`.**
>   Swallow the status, keep the message.

**Rebuild with `mapdb/rebuild.sh`, never by hand.** The step order is
load-bearing and one step was being skipped: `extents.py --apply` runs after
`markers.py` and before `world.py replay`, and without it `cells.room` covers
only the 58 label squares of B1's 1,196, which looks like success and quietly
makes every area-scoped query wrong.

```bash
./mapdb/rebuild.sh both                # build, markers, extents, replay, check
python -m pytest mapdb/tests tools/tests -q      # 359 tests
```

`rebuild.sh` prints the two reachability counts as **regression checks**: DMG
**21** unreached of 641, B1 **5** of 1,196 *(was 4 until 2026-08-28; (34,13) is a
rock outcrop that should never have been reachable)*. If either moves, something changed
behaviour — find out what before playing on it.

Standing facts that carry to any new sheet:

- **Read the map's own legend first.** Four classifiers were written before
  anyone looked at the DMG's LEVEL KEY, and several early misreadings were
  symbols the book defines explicitly. **AND THEN IT HAPPENED AGAIN:** B1's sheet
  prints its own legend too, nobody read it, and **60 of level 1's 106 doors were
  wrong** (audit 2026-09-03). The legend defines **FALSE DOOR** — a box on one
  side of an unbroken wall — which is **drawn identically to furniture against a
  wall**, so the "one-sided" flag finds both and cannot separate them. See
  `mapdb/README.md`.
- **The INK PROFILE beats thickness.** Sample ~19 points perpendicular across the
  boundary at 200 dpi: a genuine door holds the wall value with **two narrow
  spikes** flanking; a wall is flat; **furniture is flat but elevated +3 to +8**
  over the same bar either side. Thickness is a net — `(13,20,H)` measured 9, in
  band, confidence 9, and was a counter drawn against a solid wall.
- **Secret doors cannot be read from the image.** They come from the text.
- **Room anchors are label positions, not room extents.**
- **DIAGONAL walls are invisible to the edge model** — the rock sits inside the
  squares, so every boundary measures thin and open and a room's extent floods
  through it. Four B1 rooms are affected: **34** (fixed from the player's own
  reading of the printed map), and **10, 11 and 33**, all still wrong. Run
  `mapdb/diagcheck.py`, read the contact sheet, and note that its `room` column
  names the fault directly: a corrected room reads `34/34 | 31/None`, a leaking
  one reads `10/10 | 10/10` — the same area on both sides of a wall.
  See `mapdb/DIAGONAL_WALLS.md`.
- **BOTH LEVELS NOW LIVE IN `b1.sqlite`** — level 1 **6 unreached of 1,197**, level
  2 **0 of 923**. `rebuild_b1` rebuilds and re-merges level 2 itself; **do not
  remove those lines.** `build.py` deletes and recreates its target, so every
  rebuild destroys the lower level, and **nothing fails when it does** — level 1's
  checks all still pass, so the loss is silent.
- **`b1_corrections.tsv` HAS NO LEVEL COLUMN.** `apply_corrections(db,file,level)`
  stamps every row at the level passed. Level 2 has its own
  `b1_lv2_corrections.tsv` and `b1_lv2_key.py`. Never mix them.
- **CHECK EVERY MAP PAGE FOR ITS OWN LEGEND.** B1 page 1 prints doors/stairs/
  statue/pits; **page 2 prints a DIFFERENT legend — POOL, DEPRESSION, WEBS.**
- **`extract._edge` samples only the MIDDLE HALF of a boundary.** Right for a
  stronghold, **wrong for a cavern**, where the floor crosses a grid line near the
  cell *corner*. It fabricated **125 walls** on level 2 and accounted for 90 → 18
  of the unreached squares. Measure the full boundary when the map is caves.
- **`label_boxes` shields a cell's interior but NOT its border**, so a numeral
  straddling two squares invents a wall **inside its own room**. Seven cases on
  level 2.
- **On a cavern sheet, secret-door `S` glyphs sit on rock plugs INSIDE squares,
  not on grid lines** — the module says the doors are disguised as rock and the
  map draws them that way. Placing them on the nearest boundary leaves them
  bypassable; **sealing them changed reachability by zero, which is how it was
  caught.**
- **DO NOT QUOTE LEVEL 2'S ROOM EXTENTS.** `cells.room` there means "nearest
  numbered area", not "inside room N" — and the lower text states no dimension
  anywhere, so the extent cross-check does not exist on that level.
- **`markers.py --apply` mutates the database and is not idempotent.** Rebuild
  first. (`world.py replay` *is* idempotent, deliberately — it always starts
  from what the build produced and applies the whole log.)
- Every tool that reopens a page must reproduce the build's grid — the render
  settings are stored in the `levels` table for that reason.
- **A real door CROSSES the wall; furniture does not.** On the page a genuine
  door glyph straddles the wall band with floor showing on both sides, because
  the door goes through the wall. Drawn furniture lies wholly on the room side.
  **This is the one test that separates them reliably** — thickness does not, and
  area 24's fabrications measured *closer to the middle of the genuine band than
  its real door did*. Player's insight, 2026-08-28.
  **IMPLEMENTED** as `extract.door_suspect` + `mapdb/diagcheck.py`'s sibling
  `mapdb/doorcheck.py`, which flags and draws a contact sheet but never
  reclassifies. It has since caught **seven** fabricated doors in live play —
  and **NINE** by 2026-09-03. Both of the last two were called by the player from
  the module text alone, before any tool was run:
  **(18,19,H)** in **area 3, the DINING ROOM** — thick=17, deep in the WALL band,
  stools drawn against the room's south wall; and
  **(13,20,H)** in **area 2, the KITCHEN** — **thick=9, INSIDE the genuine door
  band, confidence 9**, a counter drawn against the north wall leaving a white gap
  read as hole=200.
- [ ] **AN IN-BAND THICKNESS DOES NOT CLEAR A DOOR THAT OPENS OFF A FURNISHED
      ROOM.** (13,20,H) passed the 4-11 test and was still fabricated. The
      thickness flag is a *net*, not a verdict: render the page at 8-10x with the
      grid drawn on it and apply the only reliable test — **a real door CROSSES
      the wall band with floor showing on both sides; furniture lies wholly on
      the room side.**
- [ ] **THE FURNISHED-ROOM LIST IS THE RED FLAG.** In B1 so far: **areas 2, 3, 9,
      18, 24, 27, 28.** Before narrating any door on the boundary of one of
      these, render it. *(The player has now caught two in a row that no
      automated check flagged, purely from knowing what the room is for.)* Read
  `wall` and `offset` TOGETHER: a lone `no wall` flag is weak (a genuine door in
  a one-square stub of wall trips it), while `one-sided` is strong.
- **Flag every `door` whose thickness falls outside 4-11** and render that page.
  B1's genuine doors measure 4-11, its walls 7-18, its printed rulings 0-3 — so a
  door outside that band is suspect. **Four fabricated doors were found this way
  in one session**, in three consecutive furnished rooms (areas 9, 27, 28).
  Neither automated check can see them: a fabricated door stays passable, and the
  extent check is blind when the room has another way in. **But the flag is
  noisy** — it lists 48 edges on level 1, not a handful. Render the **thickness
  1-3** and **18+** tails first; the 12-15 band is mostly genuine doors on heavy
  line work. See `mapdb/lab_notebook.md`.
- **The play record is a fourth check on the map**, and it catches what the
  other three cannot. The party walked through a boundary at the end of
  expedition 3 that the database recorded as a plain wall at thickness 15: no
  glyph was proposed, reachability was blind because both sides were reachable
  anyway, and no text names it. `world.py check` now reports that class of
  disagreement.


---

## 11. Where the campaign stands *(updated 2026-09-05, day 39)*

> **Read `git log --oneline` first.** It is the campaign history and it costs
> almost nothing. This section is a snapshot and snapshots rot — this very
> heading said "day 28" while play was at day 39.

**NOBODY IS IN THE DUNGEON. Campaign day 39, in Wethersby**, expedition 6
closed — all eight came out alive after 26 hours 20 minutes under.

### THE IMMEDIATE AGENDA — the player's own list, given 2026-09-05

**Six check-ins, in Wethersby, day 39-40.** Named in this order and all owed a
scene:

| | and the thing they are actually waiting on |
|---|---|
| ~~**Wend**~~ | **DONE day 39 late.** 59, then **101** on Dave's three items. See `npcs.md` `## DAY 39, late — WEND` and `articles.md` arts. **6** (the money lives with her) and **7** (buyer of last resort, **price/cap/season still unnamed**). **She asked for a CLERK and did not know Sarn existed as one.** New holders want into the pool. **Wat's terms still not agreed** |
| ~~**Ottir**~~ | **DONE day 40 morning.** 81 · 87 · 93. See `npcs.md` `## DAY 40, morning — REEVE OTTIR`. **THE SURETY IS SATISFIED.** **MASTER WACE HAS WRITTEN: account of the hundred at Draycot, DAY 52** — yield, hands, and traffic on the north road. **The party told him everything about Quasqueton** and he asked the one hard question: *whose is it?* **Causeway CLOSED by Dave — do not reopen it** |
| **Bern** | the loom. **May or may not have started it** — the party left Wend in charge and did not say. Ista told him about the caves herself and asked that nobody help; **outcome unknown, do not resolve it for her** |
| **Coll** | basecamp and the barn. Has his authority in writing now. All six unlisted hands went to Marrow's with a written right of return |
| **Halm** | the guide. **Genuinely does not know about the barrel** (d6=1, answered honestly) |
| ~~**Sarn**~~ | **DONE day 39 evening.** See `npcs.md` `## DAY 39, evening — SARN`. Learning his letters off Frython from first light day 40; **Toller banked a week** and Dave holds the line that opens that door. **He is still unpaid for a month of running the store** |

**Do not front-load these with mechanics.** Reaction rolls per DMG p.63 with the
adjustment said aloud first, and remember the standing finding in
`campaign/articles.md`: **gifts land badly, work lands.**

### State

- **Nine characters, not six.** Hask (Fighter), Dellie (Cleric) and Ista (Thief)
  were promoted day 39. **Dellie may not use edged weapons and is AC 6.**
  **Ista's CON 3** caps her resurrections at three.
- **Funds 595 gp 6 sp** (617 gp 6 sp less Ista's 22 gp kit).
- **Frython and Blartho are invalid until day 45** — a week off their feet.
- **13 iron spikes carried; 3 left in the dungeon.** Three of them hold the
  **pit trap at (29,31) jammed open** — that is a world change, not a memory.
- **Tristle: 641 XP, needs 1,251 — and 1,500 gp of training he cannot afford.**
- **The ring is still unidentified.** Only lead is **Wraye**, three days east of
  Ludbury, which has a library.

### Owed in the fiction

Fetch **Ede** — **due about DAY 58** *(CORRECTED 2026-09-05, player-caught. This
line said "~17 days out" and I wrote it myself earlier the same day; it does not
follow from anything attested and I could not reconstruct it. The attested fact is
`calendar.md` day 28: **she wants a MONTH to shut up her cottage**, so day 28 + 30
= **day 58**, which is **19 days from day 39**. Travel is NOT attested either — the
distance table gives Wethersby↔Fenn's as **4 days by cart** plus 8 miles
cross-country to her door; "2½ days on horseback" was also mine. Derive it before
quoting it.)* · send a lad to the
weaver at **Lyde** · **Wat's terms** · Ottir's report to **Master Wace** ·
**Draycot's second letter** about the headboard · **art. 7 fair copy to Ottir,
day 40** · **the floor chalked on the board and read to every holder** · **Sarn
onto Coll's standing roll at a clerk's wage** (Wend and Coll are doing it; the
party is not to be involved, and *nobody tells Sarn it is because he was owed
it*) · **Wat's terms — Coll's to settle, the party has stood back**.

### Dungeon threads

**Areas 10 and 11 are still mis-mapped — do not take the party there.**
**Level 2 is built and merged but entirely unexplored**: two exits from room 50,
and something in the east passage. Level 2's room extents are "nearest numbered
area", not "inside room N", and are not reliable.

### Known unfixed

**`combat.py` does not cycle a multi-value damage list** — it rolls the first
value for every attack in the list. Roll those by hand.

**`clock.py status` still reports expedition 5, round 358. That clock is CLOSED**
— there is no `close` subcommand, and `clock.py start --exped 6` will supersede
it. Do not read a live dungeon clock off it while the party is overland.

**Tests: 171 in `tools/`** (`conda run -n advanced_dnd_1e python -m pytest tools/tests -q`),
plus the `mapdb` suite — `python -m pytest mapdb tools -q` runs both.
**Reachability regression: DMG 21/641, B1 6/1197.** B1 moved 5 -> 6 on 2026-08-29
and that was a FIX; `rebuild.sh` explains why in its footer.

**Four rooms have needed the player's own reading of the printed map** — areas
34, 33, 5 and (partly) 29 — because heavy furniture and 45-degree walls defeat the
extractor. **Areas 10 and 11 are still broken and the party must not be taken
there yet.** New correction scopes exist for this: `member` (assign a square to a
room, `none` clears) and `feature` (clear a false `stairs`).

**New 2026-09-05:** `rules/zero-level.md` (normal men, and the 0-level attack
column the three henchmen were NOT being run off), `deprecated/` and
`tools/deprecated/`, `.gitignore`, and **the repo is now under git** — see
CLAUDE.md's *Version control* section for the commit cadence and for the one
hard rule: **never revert a campaign TSV to undo play.**

`tools/xp.py` now weights **monster xp full and treasure xp by share**; the
day-39 anchor row in `encounters.tsv` is what keeps that prospective.


## SAY WHICH NUMBER IT IS — a bare number in a mouth reads as a COUNT

Day 51. Yrtone told Cuddy about **six** skeletons, and two lines later the DM had
him ask *"on what number?"* and Blartho answer *"**Twelve.**"* — meaning the d20
turning roll. **The player read it as twelve skeletons and was right to**, because
nothing in the sentence said otherwise and the last number in play was a count.

**A number spoken in dialogue attaches to whatever was just being counted.** If an
NPC says a bare figure, name what it is in the same breath — *"twelve on the
turning"*, *"twelve on the die"* — or keep the die out of the dialogue entirely
and put it in the DM-voice line above.

**And the related half of the same error:** the DM told Cuddy about the six
skeletons and **left out the dwarf who had been hanging in irons in area 26 since
expedition 4** — which is the thing an almoner cares about most, and which the
party's own cleric had already said a rite over. `world_changes.tsv` had it all
along. **When telling an NPC about something, run `tools/recall.py` or grep the
log for the WHOLE class of thing, not the most recent instance of it.**


## AN NPC WITH DELEGATED AUTHORITY MUST NOT ASK PERMISSION TO USE IT

**Day 54, player-caught, and the error was the DM's phrasing.** Wend holds art. 8 —
authority to hire, self-capped at *"a clerk and one pair of hands in the barn"* — **a scope, never a figure**. The DM then wrote her the line
**"Let me spend it,"** and the player took it apart correctly:

> *"It sounds like you're asking for permission that is not mine to give — you
> already have that permission. If I say yes to that, you'll come back angry that
> we usurped your authority. **How are we supposed to handle that? It seems like a
> trap.**"*

**It was a trap, and the DM built it.** A delegated power that comes back for
approval is not delegated; and a party that approves it has taken it back.

**THE RULE:**

- **An NPC who has been given authority ANNOUNCES, it does not petition.** *"I'm
  hiring two"* — not *"let me hire two."*
- **If the NPC genuinely wants something from the party, it is not permission.** It
  is one of: **indemnity** (*"don't second-guess me if it goes wrong"*), **a
  higher ceiling** (which, if the NPC set the ceiling, is theirs to raise),
  **hands**, or **information.** Name which one and have them ask for THAT.
- **And when a player says a situation is a double bind, check whether it is one
  before defending the NPC.** Here it was. The dice (41, and d6=2 to dig in) were
  honest and the *line they were reacting to* was not.

### AND THE SHARPER VERSION, ten minutes later — the player got there again

The DM first defended the line as a trader's idiom (*"let me spend it" = I am going
to and you're hearing it first*). **The player demolished that in one sentence:**

> *"Just so we're clear — if I say to you 'let me sleep in your house', in trader
> talk that isn't me asking permission, that's me telling you I'm going to start
> sleeping in your house?"*

**It isn't the idiom. `"Let me X"` IS a request, always.** Wend laughed (67, d6=6)
and gave him the words, then took back the substance, correctly:

> **"It's whose thing it is. Hiring's mine — you gave me that and I set the figure.
> Your bed's yours. Same three words, and one of them's a notice and one of them's
> a cheek, and the difference isn't in my mouth, it's in what I've already got the
> right to do."**

**SO THE RULE IS ABOUT POWER, NOT PHRASING:**

- **An NPC who holds the right says *"I'm hiring two."*** Flat indicative. No modal.
- **An NPC who does not hold the right asks** — and then it is a real request with a
  real possible no.
- **If the DM cannot tell which, the delegation is not written down clearly enough.**
  Go and read the article.

*(She conceded the separate "capable hands" point in full and without a fight.
**But the DM should not have needed the player to find any of this.**)*


## DO NOT PUT A CLOCK ON A THING THE NPC EXPLICITLY UNCLOCKED

**Day 54, player-caught.** Cuddy accepted the dwarf's remains and said, unprompted
and twice over, that there was no hurry: ***"Bring him when you can. He's waited
forty years, he'll wait a season."*** He also said he would not bury the man until
his letter came back telling him what a dwarf is owed — **so the burial is blocked
on HIS correspondence and arriving early buys nothing.**

The DM then listed the dwarf's box in a "collision" of competing pressures against
the eleven-day southern trip, as one of *"the four things Cuddy is owed."*

> **He is owed WORD when it happens. He is not owed a date.** Being told about a
> thing is not the same as being promised it by a deadline.

**This is the same error class as `DO NOT MANUFACTURE AN NPC OBJECTION`: inventing
a pressure the NPC had deliberately removed.** Relieving the party of a clock was
one of the kindest things Cuddy did, and the DM handed it straight back.

**Before writing the words *deadline*, *owed*, *collision* or *cannot do both*:
check what the NPC actually said about timing, and quote it.**


## A LOGGED GRIEVANCE COVERS WHAT IT SAYS AND NOT WHAT IT RHYMES WITH

**Day 54, player-caught.** Ista's file carries a real, specific wound: **two months
of asking to go underground and never being answered** (day 31 — reaction **9**,
then **45**). The DM then applied it to the party leaving on an ELEVEN-DAY CART
TRIP while she was laid up, calling it *"that wound in a new coat."*

**It is not. The wound is about the EXPEDITIONS. A cart to Lyde is not going
underground** — and the party's actual practice is documented, consistent, and was
watched by Ista herself:

- **Days 39-44:** Frython and Blartho out for a week under the same DMG p.82
  clause, and the party did six solid days of town and road business.
- **Day 45:** they **waited** for the week to expire before the expedition set out,
  then asked all nine individually.
- **Days 49-54:** the Draycot ride, while Ista was laid up, and nobody proposed
  waiting.

> **The rule the party follows is: the caves wait for the injured, nothing else
> does.** That is a policy, applied evenly, in front of witnesses.

**THE RULE:** *an NPC's logged grievance is evidence for the thing it names and
nothing else.* Before extending one to a new situation, check whether the party's
conduct in that situation is already **documented and consistent** — because if it
is, the NPC has seen it and cannot reasonably be surprised by it. **This is the
`A LOW ROLL DOES NOT LICENSE INVENTED BACKSTORY` rule wearing a different hat:**
here the roll was a 21 with *does nothing*, which is *a person deciding not to make
a fuss* — and the DM inflated it into a reopened injury.


## A TRADE GOOD WITH NO ROW STOPS EXISTING. THE SMALL GOODS ALMOST DID

**Day 54, player-caught, and the question was simply *"are you still tracking
them?"* The answer was no.**

357 gp of small goods came up from Ludbury on day 27. **Their only record was a
sentence inside the notes column of the MONEY row**, plus one clause in
`calendar.md` day 39. **Last roll: market day 37. Nothing for the seventeen days
after it.** The player's own day-48 line — *"we've only sold half of the small
goods"* — came from the player, not from the DM.

> **CLAUDE.md already says this: a fact with no row, no tool and no test does not
> fail loudly, it rots quietly.** The XP line and the equipment list on
> `party_roster.md` went stale exactly this way. **`map_known.md` was RETIRED for
> exactly this.**

**FIXED, and the fix is the shape of every other fix in this project:**

- **`inventory.tsv` now has a `stock` row** with a quantity, a location, a full
  ledger, and **the sell rule written into the row itself.**
- **Wethersby market is WEEKLY** (DM call: day 37 was one, so 37 / 44 / 51 / 58 /
  65 ...). **On every market day the calendar crosses while that row is non-zero,
  roll it.** d6 quality, 3d6 scale, Wend's margin ×1.75 off the day-37 measurement.
- **Diminishing returns are part of the rule, not a fudge.** The first market in a
  town clears the novelty; the same people the next week have already bought.

**AND THE GENERAL RULE:** **when the party buys stock, open a row for it the same
day.** If it is worth 357 gp it is worth a line. **And when a player asks *"are you
still tracking X?"* — go and look, do not answer from memory.** The answer here was
no, and it took one grep to find out.


## ADJUST THE REACTION ROLL. THE LOYALTY HALF OF DMG p.63 IS NOT OPTIONAL

**Player-caught 2026-09-08 after sixty game days of bare d100s.**

DMG p.63 says to adjust an encounter reaction by the speaker's **Charisma** *and by
"any applicable **loyalty adjustment**, as if the creature were a henchman of the
character speaking."* `rules/abilities.md` had established that **nobody in this
party has a Charisma reaction adjustment** — and the DM read that as *therefore the
rolls are unmodified.* **The loyalty half was never applied once.**

**The result was exactly what the player named:** *"I don't think it's realistic
that they would have such wild shifts in their response to us."* Cuddy ran 102 → 6
→ 53 → 5 → 71 → 81 → 25 in three days. **Some of that is real and some of it was a
missing modifier.**

- **Tables now cached** in `rules/combat.md` (DMG p.37: Special Considerations,
  Alignment of Liege, Situation Modifiers).
- **A STANDING PER-NPC MODIFIER TABLE is in `campaign/npcs.md`.** Look it up. Add
  it. Say the adjusted number.
- **DMG p.37 caps it: one penalty and one bonus maximum, the higher of each.**
- **Situation modifiers are combat-time only** and are not part of a shopkeeper's
  reaction.
- **Book-strict for hirelings and henchmen.** For independent townspeople,
  extending the tiers on a record of fair dealing is a **DM call and must be marked
  as one.**

> **AND THE SECOND HALF OF THE SAME FAILURE: don't invent a story for a low roll.**
> The same day, Hask rolled 23 on being offered a job and the DM built a whole beat
> out of it — that he was being asked to tell a woman what to leave behind — **when
> the player's own words had been *"with her willing, of course."* The player's
> explicit safeguard was turned into the source of the problem.** `CHECKLIST` already
> forbids this under `DO NOT MANUFACTURE AN NPC OBJECTION` and `A LOW ROLL DOES NOT
> LICENSE INVENTED BACKSTORY`. **Read the player's sentence again before explaining
> a number.**


## DO NOT RE-ROLL A SETTLED REACTION

**Day 60.** Two desperate men reacted at **81** — DMG p.63, *"friendly, immediate
action."* Three sentences later the party made them a substantive offer, and the
temptation was to roll a fresh d100 for it.

**Don't.** A second roll can come up 20, and then the DM is explaining why a man
who was friendly a moment ago is hostile — which is manufacturing, and which is
**precisely the wild swing the player objected to on 2026-09-08.**

- **The reaction roll sets the DISPOSITION of an encounter.** Roll it once.
- **Roll the SPECIFICS instead** — is he free to travel, how bad is the injury, does
  he name a wage. Those are facts, and a die is the honest way to find them.
- **Roll a new reaction when something genuinely changes the relationship**: a new
  scene, a new day, a new offer of a different order, an insult, a rescue.
- **And add the standing modifier** from `campaign/npcs.md` every time.


## ⚠⚠ THE p.63 REACTION TABLE IS A FIRST-CONTACT MECHANIC. STOP ROLLING IT AT FRIENDS

**Player-caught 2026-09-08, researched from a 175 dpi render, and the page is
unambiguous.**

**DMG p. 63's running heads are `COMBAT (ENCOUNTER REACTIONS)` and `COMBAT (MISSILE
DISCHARGE)`.** The table sits between **initiative** and **avoiding / parleying /
missile discharge**, and its two hostile results footnote *"or morale check if
appropriate."* **It is the disposition of something you have just met, in a
situation that may become a fight.**

**1e's ongoing-relationship mechanic is LOYALTY, DMG pp. 36-37** — modified by
treatment history, checked at danger and temptation. **p. 63 borrows the loyalty
adjustment, which proves loyalty is the relationship system and reaction is the
meeting system.**

> **THE DM MADE THIS ERROR IN THREE LAYERS:**
> 1. rolled p.63 conversationally with **no modifiers at all** for sixty game days;
> 2. was corrected, and added the **loyalty modifiers** — better, and still wrong;
> 3. **the real answer is that most of those rolls should not have been made.**

### ⚠ AND THE "STEP-CHANGE" EXCEPTION IS DELETED — it was the DM's and it lasted an hour

**The first version of this rule allowed a reaction roll for a "step-change" —
a rupture, a rescue, an offer of a different order. THAT IS NOT IN DMG p.63 OR
ANYWHERE ELSE. The DM invented it as part of the fix and then used it four times
inside the hour** (Bern 50 and Ista 124 on day 66, both long-established, one of
them a 1st-level character on `characters.tsv`). **Player-caught, both rolls
voided, and the exception is struck.**

> **The tell: neither d100 changed a single word of what was written.** Bern's
> behaviour came from his file and Ista's came from hers. **The dice were noise
> wearing the clothes of rigour.**

### AND THE BOOK ITSELF SAYS TO USE JUDGMENT — DMG p. 37, foot of the loyalty tables

> *"**If you are certain of your DM ability, most of these factors should be apparent
> without actually checking them out, simply by empathizing with the character or
> group in question, and having them act accordingly.** Until you are absolutely
> certain, however, it is urged that you use these tables."*

### THE DISCIPLINE — three cases and no exceptions

| | |
|---|---|
| **A CREATURE OR PERSON MET FOR THE FIRST TIME** | **roll DMG p. 63.** This is what the table is: an encounter mechanic in the combat chapter |
| **ANYONE ALREADY ESTABLISHED** | **NO ROLL, EVER.** Read their file, decide what they do, and **say the reason out loud.** If there is no reason on the record, they do not change |
| **AN UNKNOWN FACT** | **roll, on a table declared before the die.** *Is he free to travel · how bad is the foot · what has she been doing for nineteen days · how wide is the loom · what is in the vial.* **This is the honest use and it has carried this campaign** |

**LOYALTY** is checked per DMG pp. 36-37 at **danger, temptation and hardship** —
never conversationally.

> **AND THE GENERAL LESSON, which is bigger than reactions:** when the DM fixes a
> rule and writes an exception into the fix, **the exception is where the old
> behaviour goes to live.** Fix the rule without the escape hatch.

**And the tell that this was going wrong was available for days:** every low roll
needed a story invented for it, and `CHECKLIST` already forbade inventing stories
for low rolls. **When a mechanic keeps forcing you to break another rule, the
mechanic is being misapplied.**


## THE LANE RULE HAS ITS OWN TEST NOW, BECAUSE PROSE FAILED THREE TIMES

**`tools/tests/test_lane_rule.py`.** It fails if any markdown file outside
`rules/` and `deprecated/` states the ally-hit figure without the word *melee*
nearby, and it fails if the authoritative row in `rules/exploration.md` ever loses
either of its two conditions.

**Why a test and not another warning:** `party_roster.md` already carried a note
reading *"the lane rule applies ONLY IN MELEE — this paraphrase used to omit that
and misled the DM again on 2026-09-06."* **The note was there. The DM misquoted a
different paraphrase in the same file an hour later on 2026-09-08.** A warning that
has failed twice is not a mechanism.

> **AND THE GENERAL FORM OF THIS FAILURE:** the numbers were correct in
> `rules/exploration.md` the whole time, **including a row that says in so many
> words *"allies merely standing in front are not a melee."*** The DM quoted a
> prose paraphrase instead — **which is the first thing `CLAUDE.md` forbids.**
> **When a rule has a cached table, quote the table. Paraphrases lose conditions.**


## DO NOT INVENT A MECHANIC MID-SCENE THAT CHANGES A DECISION ALREADY TAKEN

**Day 70, player-caught.** The party went back into areas 8 and 9 for ~97 gp of
blown glass. The DM introduced a **fragility mechanic** — a 3d6 for how much
arrived unbroken, packing materials, spoiled rations — **which has never existed in
this campaign.**

**Expedition 7 carried ~200 lb of laboratory glass worth ~250 gp out of that exact
room**, and `world_changes.tsv` records exactly one constraint on it:

> *"Too bulky to carry without dropping the party from 9″ to 6″."*

**It is a WEIGHT problem. It always was.** And the invention came **after** the
party had walked in, so they could not have brought straw or boxes **from the carts
sitting half an hour away** — which is what they would have done.

> ### THE RULE
>
> **A new mechanic may not be introduced after the players have committed to a
> course of action based on its absence.** If something has been resolved one way
> once, it is resolved that way again, or it is raised **before** the party decides
> — never as a surprise cost on the way out.
>
> **This is the same principle as `a rules correction is prospective, never
> retroactive`**, pointed at the DM's own inventions rather than at the books.
>
> **AND THE TEST FOR IT:** *would the party have equipped differently if they had
> known?* **If yes, it is too late.**


## ⚠⚠ THE DM DOES NOT DECLARE THE PARTY'S ACTIONS. EVER. ASK.

**Day 70, player-caught, and it is the worst procedural error of the campaign.**
The DM rolled a full combat round for the party against a troglodyte **without
asking what anybody was doing** — and in doing so decided, silently:

- that **Yrtone swapped her sling for a flail** (a real tactical choice with a
  real ruling attached);
- **which four characters engaged**, and which five did not;
- that **nobody fired a missile** (the DM even argued the lane rule to justify it);
- that **nobody cast a spell** — Frython's *sleep* and nine memorised cleric spells
  went unmentioned;
- that **nobody dropped a load, withdrew, closed a door or ran.**

> **`CHECKLIST` already said "pause after each round for declarations."** That
> rule was written about PACING. **This is bigger than pacing: it is the DM
> playing the player's characters.**

### THE PROCEDURE, and there is no version of it that skips a step

1. **Announce what the party can perceive.** Nothing more.
2. **Roll surprise and initiative** — those are the DM's.
3. **Resolve the side that won initiative** if it is the monsters'; that side's
   behaviour IS the DM's.
4. **THEN STOP AND ASK.** *"What does everyone do?"* — and wait.
5. Resolve the declared actions and nothing else.
6. **Stop again.**

**A monster's actions are the DM's. A character's actions are never the DM's** —
not the six PCs, and not Hask, Dellie or Ista, who are 1st-level characters on
`characters.tsv` that the player plays.


## "FIRST ENCOUNTER" MEANS FIRST ENCOUNTER, NOT FIRST LINE OF DIALOGUE

**Day 71, player-caught.** The DM rolled a p.63 reaction for **HOLT the innkeeper**
on the grounds that he was unnamed in `npcs.md` and had never spoken on the page —
**and the party has been paying for his rooms for two months** and had held two
meetings in his common room.

> **An NPC who has never had a line of dialogue is not therefore a stranger.**
> The test is not *"is he in the file?"* — it is **"has the party had dealings with
> him?"** Rooms paid for, goods bought, a road shared, a meeting held in his room:
> **all of that is dealings.**

**The player's own test settles it:** *"in theory you could go back two months and
roll the initial reaction, but what does that change?"* **Nothing. So don't roll
it.** Decide what he does from what is known about him and say why.

**And the useful half:** the FACT rolls in that same scene were correct and
survived — whether he could name the contents off the bung, and whether he wanted
it and could pay. **Dice for facts. Judgment for feelings.**


## ENTERPRISE MATTERS GO TO WEND BY DEFAULT. DO NOT STAGE THEM AT THE PARTY

**Day 72, player-caught — and the DM had it backwards.** The DM wrote that the party
had *"nearly forgotten"* to route a new venture through Wend. **The player's answer:**

> *"We didn't nearly forget it twice, we've been reminding you and/or Wend about it.
> **Nothing would make me happier than if all of this happened automatically.**"*

**And the record is on the player's side.** In one session they told Wat his reports
go to Wend and not the party; ruled the loom was hers to buy and refused to nag her
about it; left the wool leads with her; and said to ask Wend and Coll about Dill.
**The DM kept staging those conversations at the party anyway.**

> ### THE RULE
>
> **Art. 8 and art. 13 are real. Play them.** Hiring, stock, prices, ventures, land,
> the wage roll and anything touching the enterprise's money are **WEND'S** —
> and the DM should show her **exercising that authority unprompted**, not wait for
> the party to hand it to her.
>
> - **A new commercial idea gets taken to Wend. The DM does not resolve it at the
>   party first.**
> - **When information arrives that is hers, it goes to her** — Wat's report, a
>   drover's names, a price seen in another town.
> - **She acts between scenes.** She hires, she orders, she writes, she decides —
>   and the party finds out because she tells them, or because it is done.
> - **THE TEST: if the party has to remind the DM whose job something is, the DM has
>   made the party the switchboard again.**

**This is the third form of the same failure in one session** — after *an NPC with
delegated authority must not ask permission to use it*, and *the DM does not declare
the party's actions*. **All three are the DM taking back agency that was given away
in writing.**


---

## A ⚠ BOX IS A PROMISE TO COME BACK AND CLOSE IT

**Day 76. Asked when the wool party was due, the DM added a caveat: the Wace receipt
is still travelling toward a Wend who has never seen the letter.** Player: *"Wend did
see the receipt."*

**She did — on day 65.** It recited the letter, Toller paid his full ~250 gp against
it the same day, and his day-42 condition was discharged and closed. **The thing had
resolved eleven days earlier and the warning was still on the page.**

### WHY IT HAPPENED, and it is not the same failure as quoting a running total

The rule already in force is *never quote a running total or an event from a prose
file.* **This was neither.** It was a **⚠ FORECAST** — a correct, well-reasoned note
written on day 55 about something that had not happened yet. It said *"the receipt
will reach Wend, who never saw the letter, while the party is south."*

> ### A WARNING IS THE ONE KIND OF PROSE THAT NEVER LOOKS STALE
>
> A stale total looks like a number and can be checked against a tool. **A stale
> warning looks like a warning.** There is nothing on its face that says it already
> fired. It reads as live for ever, and it will be quoted as live for ever.

### THE RULE

1. **When you write a ⚠ box that predicts something, you have opened a loop.**
2. **When the thing resolves, close the box IN THE SAME EDIT that logs the
   resolution.** Not later, not "when I next touch the file." The day-65 calendar row
   recorded the receipt arriving and paying out; the art. 11 box should have been
   struck in that same commit.
3. **Close it by REWRITING it, not deleting it** — ✅, what actually happened, and the
   fact that it was true when written. The old citation must not be orphaned
   (`deprecated/README.md`, same principle).
4. **Before offering an unprompted caveat out of a prose file, check the log for the
   event that discharges it.** `calendar.md` had it in a row the DM had itself
   written. **One grep.**

**And the general form, which is worth more than the instance:** *the prose files are
an index, and an index of the FUTURE goes out of date faster than an index of the
past.*
