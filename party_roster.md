# Quasqueton Expedition — Party Roster

AD&D 1st Edition. Rolled 2026-08-15, PHB Method I (4d6 drop lowest, arrange as desired).
All characters 1st level, 0 XP.

> ## WHAT THIS FILE IS — and the one thing it kept getting wrong
>
> **It is the CHARACTER GENERATION RECORD.** Rolled ability scores, starting
> gold, race and class choices, and the ability effects derived from them. Those
> are fixed at creation and this file owns them outright.
>
> **It is NOT the live sheet**, however much the block at the bottom looks like
> one. Anything that changes during play is computed elsewhere:
>
> | | |
> |---|---|
> | hit points | `python tools/hp.py` |
> | experience | `python tools/xp.py` |
> | gear, funds | `campaign/inventory.tsv` |
> | spells memorised | `campaign/spells.tsv` |
> | where they are | `python tools/party.py where` |
>
> **And the trap nobody guarded until 2026-09-05:** a *rules* number can rot here
> too. Tristle's Find/Remove Traps sat at **30%** on this sheet long after
> `rules/thief.md` corrected it to **25%** — the roster kept the very number the
> CHECKLIST records as fixed, because the anti-staleness rules were all written
> about running totals and nobody thought a derived percentage needed one.
>
> **Derived numbers on this sheet are a CACHE of `rules/*.md`.** Where they
> disagree, `rules/` wins and this file gets corrected.

---

## DAVE — Human Fighter, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| **18/26** | 9 | 9 | 10 | 13 | 10 |

- **hp 9** (d10 rolled 9) — the party's anchor
- **Gold: 150 gp** (5d4×10)
- Exceptional strength **18/26** → **+1 to hit, +3 damage**, weight allowance +1,000 gp,
  open doors **1–3 in 6**, bend bars/lift gates **20%** *(PHB Strength Table II, verified)*
- CON 13: no hp bonus (bonus begins at 15)
- Human: unlimited level advancement, may use any weapon or armor

## TRISTLE — Elf Thief, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| 10 | 9 | 7 | **18** | 9 | 9 |

*DEX 17 +1 elf = 18. CON 10 −1 elf = 9. The 7 was moved to Wisdom: elves have a minimum
Charisma of 8 (PHB Race Table III, verified), so CHA 7 was not a legal elf.*

- **hp 3** (d6 rolled 3)
- **Gold: 70 gp** (2d6×10)
- **Thief functions** (base 1st level + elf racial + DEX 18):

| Function | Base | Elf | DEX 18 | **Total** |
|---|---|---|---|---|
| Pick Pockets | 30% | +5 | +10 | **45%** |
| Open Locks | 25% | −5 | +15 | **35%** |
| Find/Remove Traps | 20% | — | +5 | **25%** |
| Move Silently | 15% | +5 | +10 | **30%** |
| Hide in Shadows | 10% | +10 | +10 | **30%** |
| Hear Noise | 10% | +5 | — | **15%** |
| Climb Walls | 85% | — | — | **85%** |
| Read Languages | 0% | — | — | **0%** (4th level) |

- **Backstab**: ×2 damage, +4 to hit, from behind and unnoticed
- Elf racial: 90% resistance to *sleep* and *charm*; infravision 60'; secret door detection
  1-in-6 passing, 2-in-6 actively searching, 3-in-6 for concealed portals; +1 to hit with
  long sword, short sword, and bow
- Languages: common, elvish, gnoll, hobgoblin, gnome, halfling, orcish
- Elf thief: **unlimited** level advancement (the one class elves may pursue without a ceiling)

## BLARTHO — Human Cleric, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| 14 | 8 | **15** | 12 | 13 | 11 |

- **hp 2** (d8 rolled 2) — dangerously fragile, keep him out of the front rank
- **Gold: 120 gp** (3d6×10)
- WIS 15: **+2 bonus 1st-level spells** → **3 first-level spells/day** (1 base + 2 bonus),
  plus a 2nd-level bonus slot unusable until 3rd level. Magical attack adjustment **+1**
  *(standard PHB Wisdom Table II — table too OCR-damaged to verify directly)*
- **Turn undead** as a 1st-level cleric
- Blunt weapons only (mace, club, staff, hammer, sling); any armor

## FRYTHON — Human Magic-User, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| 8 | **17** | 11 | 14 | 12 | 11 |

- **hp 2** (d4 rolled 2)
- **Gold: 30 gp** (2d4×10) — poorest in the party by a wide margin
- INT 17: **75%** chance to know any given spell, **min 8 / max 14** spells per level
- **1 first-level spell/day** at 1st level
- Dagger, dart, or staff only. **No armor.** DEX 14: no defensive adjustment
- Spellbook: to be determined — see below

## YRTONE — Human Cleric, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| 14 | 9 | **16** | 12 | 14 | 12 |

- **hp 7** (d8 rolled 7) — the durable cleric
- **Gold: 110 gp** (3d6×10)
- WIS 16: **+2 bonus 1st-level spells** → **3 first-level spells/day**, plus two 2nd-level
  bonus slots banked until 3rd level. Magical attack adjustment **+2**
- CON 14: no hp bonus (bonus begins at 15)
- Turn undead as 1st-level cleric; blunt weapons only

## TORSAT — Human Fighter, 1st level

| STR | INT | WIS | DEX | CON | CHA |
|---|---|---|---|---|---|
| 13 | 11 | 11 | 11 | 12 | 11 |

- **hp 6** (d10 rolled 6)
- **Gold: 170 gp** (5d4×10) — richest in the party
- STR 13: **no hit or damage adjustment**, open doors **1–2 in 6**, bend bars **4%**
  *(PHB Strength Table II, verified)*
- Human: unlimited advancement, any weapon or armor

---

## Equipment

**Funds pooled.** Total 650 gp, spent 595.495, **54.505 gp remaining** (party treasury).
All prices verified against page renders of PHB pp. 35–37. See `rules/equipment.md`.

### Martial kit

| | Armor | Shield | Melee | Missile | **AC** |
|---|---|---|---|---|---|
| **Dave** | Banded 90 | Large 15 | Long sword, spear | Short bow, 12 arrows | **3** |
| **Torsat** | Banded 90 | Large 15 | Long sword, spear | Short bow, 12 arrows | **3** |
| **Blartho** | Banded 90 | Small wooden 1 | Footman's flail | Sling, 12+20 bullets | **3** |
| **Yrtone** | Banded 90 | Small wooden 1 | Footman's flail | Sling, 12+20 bullets | **3** |
| **Tristle** | Leather 5 *(**worn**)* | — | Long sword | Short bow, 12 arrows | **4** |
| **Frython** | — | — | Dagger *(non-prof.)* | 16 darts | **10** |

Plus **thieves' picks & tools** (30 gp) for Tristle — without these he has no lock or trap
functions at all.

### Marching order — STANDARD, and it is always assumed

## THE WITHDRAWAL ORDER — set round 1548. INVALIDS IN THE MIDDLE

| rank | | | |
|---|---|---|---|
| **1** | **Dave** — short bow | **Torsat** — sword, shield | **Yrtone** — sling, shield |
| **2** | **Ista** | **Blartho** | **Frython** |
| **3** | **Dellie** — spear, shield | **Tristle** | |

**Rank 2 is the three who cannot fight.** Blartho and Frython are under the
week — walking only, no attacking, no defending, no casting, no carrying. **Ista
is armed but she is 4 hit points and −2 to hit.** They go in the middle with a
fighting rank in front and Dellie's mail and spear behind.

**Dave is on a bow in the front rank again.** He has paid the switch cost twice
this expedition and chosen it a third time; it is a deliberate trade for a
first volley and it is not an oversight.

---

## PREVIOUS ORDER — superseded at round 1548

**Same people, same ranks. Dave and Torsat now carry SWORD AND SHIELD** instead
of bows.

> ### ⚠ SUPERSEDED — see the NINE-PERSON ORDER below, adopted day 69
>
> **This table has eight slots and no HASK**, and it still gives Dellie a spear the
> cleric prohibition took off her on day 39. **Player-caught 2026-09-08.**

| rank | | | |
|---|---|---|---|
| **1** | **Yrtone** — sling *(free switch to flail; see the weapon-change ruling)* | **Dave** — long sword and large shield | **Torsat** — long sword and large shield |
| **2** | **Frython** — darts | **Ista** — **THE LANTERN** | **Tristle** — short bow |
| **3** | **Dellie** — spear, shield | **Blartho** — flail, shield | |

## ★ STANDARD FORMATION — NINE ABREAST-BY-THREE, adopted day 69

**This is the order. It is assumed on every move unless the player changes it.**

| rank | | | |
|---|---|---|---|
| **1** | **Yrtone** — sling | **Dave** — long sword, large shield | **Torsat** — long sword, large shield |
| **2** | **Frython** — darts | **ISTA** — **the lantern**, and a dart or her dagger in the other hand | **HASK** — **SPEAR FROM THE SECOND RANK**, banded mail, large shield, AC 3 |
| **3** | **Dellie** — **flail**, large shield | **Blartho** — flail, small shield | **Tristle** — short bow |

**WHY HASK AND TRISTLE SWAPPED:** *"a spear reaches from the second rank and a long
sword does not"* — CHECKLIST §3 and `rules/combat.md`. **Hask in rank 2 with a spear
fights every round the front rank is engaged**, and it puts an **AC 3** body in what
used to be the soft centre.

**WHAT IT COSTS, and it is on this file's own record:** *"an ally between shooter and
target is **−4 with a 50% chance of hitting the ally in front**."* **Tristle now has
two ranks in front of his bow and the man immediately ahead of him is Hask.** He
shoots when there is a lane, not as a volley; the rest of the time he is the thief —
**listening, searching, reading doors.**

**Ista cannot use a two-handed weapon at all while she holds the lantern**, class list
or no class list. One hand is spoken for.

## ★ HOUSE RULE — CLASS WEAPON LISTS, settled by the player day 69

**PHB p.19 Table II reads, strictly: THIEF — leather armour, NO shield, and club,
dagger, dart, sling, sword only** *(with the footnote allowing short, broad and long
swords but not bastard or two-handed)*. **CLERIC — club, flail, hammer, mace,
staff.**

> **The table was never used in this campaign and the player has ruled it stays that
> way**, citing **Unearthed Arcana**, which widened the class weapon lists —
> **thieves may use short bows here, and clerics may use slings.**
>
> **SO: Tristle keeps his short bow. Yrtone keeps her sling. Ista keeps her studded
> leather and her darts.** *(Her spear remains unusable in practice, because she is
> holding a lantern.)*
>
> **DO NOT RE-LITIGATE THIS.** It was raised on 2026-09-08, checked against a 175 dpi
> render of PHB p.19, and decided. **And it would have been prospective only in any
> case — a rules correction never reaches backwards.**

**WHY, and it is worth keeping:** the party was surprised at contact range
**twice** in one expedition — a troglodyte out of a side passage, then four orcs
out of the dark — and both times the front rank spent the first round stowing
bows instead of fighting. **Everything down here sees a lantern before the
lantern sees it** (troglodyte infravision 90 ft; orcs see well in total
darkness). A missile-forward front rank buys a volley the party rarely gets and
costs a round it always needs.

**The soft centre and armoured rear are unchanged and deliberate** — see below.

---

## PREVIOUS ORDER — superseded at round 653. Missile-forward front rank

**Adopted once DMG p. 97 established that a 10-ft passage takes THREE abreast**
(3.5 ft per character). Two-abreast was leaving a slot empty in every rank and
costing 10-20 ft of lit corridor.

| rank | | | |
|---|---|---|---|
| **1** | **Yrtone** — sling | **Dave** — short bow | **Torsat** — short bow |
| **2** | **Frython** — darts | **Ista** — **THE LANTERN** | **Tristle** — short bow |
| **3** | **Dellie** — spear, shield | **Blartho** — flail, shield | |

**Ista is centre of rank 2**, which puts the light in the middle of the column
and level enough with the front to throw its 30 ft usefully forward.

### Three things follow from this and must not be quietly ignored

- **Every one of rank 1 opens with a missile weapon.** None of them can bow and
  shield at once. **On contact they need a round to sling the bow and get sword
  and shield up, or they fight the first round holding a bow.** State the cost
  when it happens; do not fix it silently.
- **THE RANKS ARE SORTED BY ARMOUR ON PURPOSE. DO NOT QUERY IT.** Player's
  reasoning, stated at round 207: *"I want my back rank to be heavily armoured,
  that's why she's in the back. I want my least armoured people in the middle."*

  | rank | AC |
  |---|---|
  | **1** Yrtone 3 · Dave **2** · Torsat 3 | the wall |
  | **2** Frython **10** · Ista **8** · Tristle 4 | **the soft centre, shielded front AND back** |
  | **3** Dellie **3** · Blartho **3** | banded mail and shields, because **a rear attack is the one nobody sees coming** |

  **Dellie's spear does not reach a front-rank fight from rank 3, and that is an
  accepted cost, not an oversight.** She is back there for her armour class. Do
  not flag it again.
- **The lane rule applies ONLY IN MELEE — this paraphrase used to omit that and
  misled the DM again on 2026-09-06.** `rules/exploration.md` is the authority
  and it is unambiguous:
  > | **No melee** — enemies at a distance, nobody in contact | **no penalty at
  > all.** Range modifiers only. **Allies merely *standing* in front are not a
  > melee.** |
  >
  > **The test is CONTACT, not geometry.** Ask *"is anyone actually engaged?"*
  > before asking *"who is in the lane?"*

  **So:** if the front rank is **in contact**, a shot past them down a filled
  10-ft corridor is **−4 with a 50% chance of hitting the ally in front**. If
  nothing is engaged — enemies at a distance, the party standing ready — **every
  missile in the column fires with range modifiers only.**

  *(Caught by the player at round 1203 of expedition 4 and cached then; caught
  again on day 46 of expedition 7, when this line made the DM tell the party that
  only rank 1 could shoot at a doorway with nobody in contact.)*

---

## EXPEDITION 6 OPENING ORDER — superseded at round 197. Two abreast

**Hask is not here** (he is Wend's until market day). **Ista is**, and she has the
lantern.

| rank | | |
|---|---|---|
| **1** | **Dave** — **short bow** | **Torsat** — **short bow** |
| **2** | **Dellie** — **sling** | **Tristle** — **short bow** |
| **3** | **Ista** — **THE LANTERN** | **Frython** — darts |
| **4** | **Blartho** — sling and shield | **Yrtone** — sling and shield |

**Every rank but the fourth has a missile weapon out.** This is an *approach*
posture, and two things follow from it that the DM must not silently ignore:

- **Dave and Torsat cannot bow and shield at once.** On contact they need a round
  to sling the bow and get sword and shield up, or they fight the first round
  with a bow in their hands. **State the cost when it happens; do not fix it
  quietly.**
- **NOBODY IN RANK 2 CAN REACH A FIGHT IN A 10-FT CORRIDOR.** The old order put
  spears there for exactly this reason (CHECKLIST §3). **Dellie has her own spear
  on her back** — mention it once when the first melee starts, then drop it.
- And the standing lane rule still applies: **allies filling a 10-ft corridor
  between shooter and target is −4 with a 50% chance of hitting the ally in
  front** (`rules/exploration.md`). In a corridor, ranks 2-4 mostly cannot shoot.
  In a room they can.

**Ista in rank 3 puts the light in the middle of the column**, which is correct
and is her whole job.

---

### PREVIOUS ORDER — superseded, kept for the record

**Set day 18 (expedition 5), when Hask and Dellie march with the party.**

| rank | | |
|---|---|---|
| **1** | **Dave** — long sword and **large shield** | **Torsat** — long sword and **large shield** |
| **2** | **Hask** — spear | **Dellie** — spear |
| **3** | **Tristle** — short bow | **Frython** — darts, and the lantern |
| **4** | **Yrtone** — flail and shield | **Blartho** — flail and shield |

**A spear reaches from the second rank and a long sword does not** (CHECKLIST §3),
which is why rank 2 carries spears and rank 1 keeps its shields. The party owns
two spears (Dave's, and Torsat's which Hask carries); Dellie has her own and
Tristle keeps his. **That is enough for this order.** **Never ask the player to restate this**
— it is assumed on every move unless they change it.

**Without Hask and Dellie** the order is the older one: Dave and Torsat front,
Tristle and Frython second, Yrtone and Blartho rear.

### Weapon proficiencies (PHB Weapon Proficiency Table)

| | Slots | Proficient in | Spare | Non-prof. penalty |
|---|---|---|---|---|
| Dave | 4 | long sword, short bow, spear | **1** | −2 |
| Torsat | 4 | long sword, short bow, spear | **1** | −2 |
| Blartho | 2 | flail, sling | 0 | −3 |
| Yrtone | 2 | flail, sling | 0 | −3 |
| Tristle | 2 | long sword, short bow | 0 | −3 |
| Frython | **1** | **darts** | 0 | **−5** |

**Frython's dagger is non-proficient at −5** — he needs a 16 to hit AC 10 with it. It is a
last resort, not a weapon. Darts are his attack.

### Damage

- Dave: long sword **4–11** (1–8 +3 STR), spear 4–9, short bow **1–6** *(no STR bonus — the
  1e strength damage bonus applies to melee and hurled weapons, not ordinary bows)*
- Torsat: long sword 1–8, spear 1–6, short bow 1–6
- Blartho / Yrtone: flail **2–7** vs man-sized, **2–8 vs large**; sling bullet **2–5** / 2–7 vs large
- Tristle: long sword 1–8, short bow 1–6, **+1 to hit with both** (elf). Backstab **×2 damage,
  +4 to hit** — works with sword or dagger, not the bow
- Frython: dart 1–3

### Shared gear (distributed evenly)

| Item | Qty | Carried by |
|---|---|---|
| Backpack | 6 | one each |
| Rations, 1 week | 6 | one each |
| Waterskin | 6 | one each |
| Torch | 6 | one each |
| Oil flask | 6 | one each |
| Lantern, hooded | 2 | Dave (front), Yrtone (rear) |
| Rope, 50' | 2 | Torsat, Tristle |
| 10' pole | 3 | Dave, Torsat, Tristle |
| Iron spike, large | 4 | Dave, Torsat, Blartho, Yrtone |
| Wooden spikes (3) & mallet | 1 | Tristle |
| Tinder box, flint & steel | 1 | Blartho |

### Movement & encumbrance

Four characters in banded mail fall in the PHB's **"heavy gear"** band — **9" movement**, a
"lumbering run." The party marches at its slowest member, so **the whole party moves at 9"**.
Tristle's armor choice does not change this.

### Spells

**Blartho** — 3/day: *cure light wounds*, *cure light wounds*, ***command***
**Yrtone** — 3/day: *cure light wounds*, *cure light wounds*, ***command***

*Both clerics swapped bless for **command** early in the campaign and have kept it there:
it is V-only (castable with hands full), one word, and allows **no saving throw** against
anything with INT under 13 or fewer than 6 hit dice. Berserkers are men, understand common,
never check morale, and cannot resist it. See the CURRENT STATE block for what is spent.*

Four *cure light wounds* across the party, 1–8 hp each. *Bless* = +1 to hit for all
friendlies in a 5"×5" area **not already engaged in melee** — cast it before contact.

**Frython** — spellbook (DMG "Acquisition of Magic-User Spells", rolled d10 per category):

| Category | d10 | Spell |
|---|---|---|
| — | auto | ***Read Magic*** |
| Offensive | 8 | ***Shocking Grasp*** — 1–8 +1/level = **2–9**, touch |
| Defensive | 8 | ***Spider Climb*** — 3" climb, 1 rnd +1/level |
| Miscellaneous | 3 | ***Erase*** — removes writing |

**Memorizes ONE per day.** Shocking grasp is the highest-damage 1st-level M-U spell in the
game but requires him to touch the target — DM ruling: **a normal to-hit roll is required**
(M-U column, so 11 to hit AC 10). With 2 hp and AC 10 that is a desperate measure.

Max spells known at 1st level for INT 17: **14** (minimum 8). Every scroll or captured
spellbook is a **75%** roll to add a spell. This is how he gets *sleep*.

### Standing notes

- **Tristle wears his leather** (from day 2, turn 58). 1e imposes **no thief-function
  penalty** for leather — verified against the PHB thief description and the function tables.
- Dave and Torsat each have **1 unused weapon proficiency**.
- Both clerics carry a wooden holy symbol (7 sp each) — spell component and turning focus.
- Large shield defends against **3** attacks per round; small shield only **1**.

---

# EXPEDITION 1 — CLOSED

Three days in Quasqueton, twelve encounters, **no deaths, nobody ever below 1 hp.**

**Recovered:** the Rogahn & Zelligar painting (sold **250 gp**, buyer did *not* recognise its
origin — the location stays secret), 41 gp / 43 sp / 21 cp in coin, a 10 gp gold ring,
salvage sold for 9 gp 8 sp. **≈313 gp recovered → 313 XP, ~52 each.**

**Resupplied:** 2 large shields (replacing the small wooden ones — no AC change, but they now
cover **3 attacks/round** instead of 1), 12 arrows, **18 flasks of oil**, 6 weeks of rations,
large metal mirror, 4 iron spikes, 5 wooden spikes, 6 wax candles. **≈78 gp spent.**

**Party funds: ≈289 gp.**

**Left in the hill:** the hide (node 8, barrable) and the Advisor's Chamber (node 10, secret,
never found by anyone else). Unexplored: crossroads north & west arms, the QUASQUETON panel,
corridor 11 east and west, all 14 pools untested, and a second level.

---

# SPELL TRACKER — *update on every cast*

**Memorised** = what's in the head right now. **Cast** = spent this cycle. Renew with 4 hours'
rest + 15 min prayer/study per spell level.

**Expedition 3 loadout:**

| Caster | Slots | Memorised | Cast | **Remaining** |
|---|---|---|---|---|
| **Blartho** | 3 | 2× *cure light wounds*, ***command*** | — | **2× CLW, *command*** |
| **Yrtone** | 3 | 2× *cure light wounds*, ***command*** | — | **2× CLW, *command*** |
| **Frython** | 1 | *shocking grasp* | — | ***shocking grasp*** |

### Why two *commands*

*Command* is **V only** (castable with hands full), **one word**, and allows **no saving throw**
against anything with **INT under 13 or fewer than 6 hit dice**. Its one limit: *"The command
must be uttered in a language which the spell recipient is able to understand."*

**Nothing in Quasqueton has understood common — except berserkers.** They are *men*. They
have morale 12, never check, never flee, and strike twice a round for 1–8. **"Flee" is the
only counter this party has ever found to them**, and it cannot be resisted.

**Spellbook (Frython):** *read magic*, *shocking grasp*, *spider climb*, *erase*, ***SLEEP***.
(Sleep transcribed from the area 5 scroll, day 4 after expedition 4 — d100 = 75 against a 75% chance to know. Scroll consumed.)
Max known at 1st level for INT 17: **14**. Chance to learn a found spell: **75%**.

**Cleric spell list available on re-memorising:** bless, command, create water, cure light
wounds, detect evil, detect magic, light, protection from evil, purify food & drink, remove
fear, resist cold, sanctuary. Full details in `rules/spells-1st-level.md`.

---

# CURRENT STATE — *the live sheet, keep this updated*

> # ⚠ SUPERSEDED — DO NOT READ NUMBERS OUT OF THE BLOCK BELOW
>
> **Its "As of" was expedition 3. Play is at day 39, after expedition 6.**
> Three expeditions stale, exactly as its own warning predicted. **Left in place
> rather than deleted** (supersede, don't rewrite — CHECKLIST §2b), and
> deliberately **not** brought up to date: keeping it current would recreate the
> second source of truth that made it dangerous.
>
> Run the tools. They take a second and they are never wrong.

**As of: in town, after expedition 3, week of rest served, outfitted for expedition 4.**

> **This block is a convenience copy and has been two expeditions stale twice.**
> The sources of record are computed, not written down:
>
> ```bash
> python tools/hp.py        # hit points
> python tools/xp.py        # experience
> ```
>
> and `campaign/inventory.tsv` for gear. If this table disagrees with those,
> **they are right and this is wrong.**

| | Class | hp | **AC** | Weapons |
|---|---|---|---|---|
| **Dave** | Fighter | **9 / 9** | **3** | Long sword **4–11**, spear, short bow |
| **Torsat** | Fighter | **6 / 6** | **3** | Long sword 1–8, spear, short bow |
| **Tristle** | Elf Thief | **3 / 3** | **4** | Long sword **+1**, short bow **+4** (17 arrows), spear *(−3)* |
| **Blartho** | Cleric | **2 / 2** | **3** | Footman's flail 2–7, sling 2–5 |
| **Yrtone** | Cleric | **7 / 7** | **3** | Footman's flail 2–7, sling 2–5 |
| **Frython** | M-U | **2 / 2** | **10** | 15 darts 1–3 (3/round) |

**Spells, expedition 4 — RENEWED after a night's rest in Rogahn's Chamber (round 958):**

| Caster | Memorised | Cast | **Remaining** |
|---|---|---|---|
| **Blartho** | 2× *cure light wounds*, *command* | — | **2× CLW, *command*** |
| **Yrtone** | 2× *cure light wounds*, *command* | 1× CLW (3 hp, on Dave) | **1× CLW, *command*** |
| **Frython** | one 1st-level slot | — | *(loadout not yet declared)* |

**Four cures again**, and both *commands*. Frython's 1st-level slot is **not yet
declared** — he chooses from *read magic*, *shocking grasp*, *spider climb*, *erase*, ***sleep***.

**Dave is fit.** He served the full week the DMG requires and healed 1 hp per day of it
(2 → 9). Yrtone healed to full on the same rest.

**Funds 594 gp 3 sp 8 cp.** Lodging for the seven-night stay (42 gp — six at 1 gp per
person per night, the campaign's house rule), the salvage sale (+29 gp 5 sp) and the
restock (24 arrows, 10 flasks of oil, 12 iron spikes) are all applied. Town business is
closed.

*The DMG's 100 gp per level per month upkeep (p.25) is **not used in this campaign** — see
`rules/equipment.md`. It was applied briefly on 2026-08-25 and reversed.*

**Tristle's short bow is +4, not +1.** DEX 18 carries a **+3 Reaction/Attacking
Adjustment**, which PHB p.11 applies to *"both surprise situations and missile combat
attacks"*, and that is separate from his +1 elf bonus. This was not being applied in
expeditions 1–3. `tools/combat.py` applies it now and a test asserts it.

### Dave's condition — DMG p. 82, verified

Brought to **−1** by a single blow (7 hp, took 8), which is inside the "optionally as low as
−3 from the same blow" clause, so **unconscious rather than dead**. Blartho bound the wounds,
which stops the bleeding immediately. Yrtone's *cure light wounds* restored 3, putting him at
**2 hp**.

**The spell does not lift the incapacity.** The DMG is explicit that a character revived from
0 or below is comatose 1–6 turns (**rolled 2**) and thereafter "must rest for a full week,
minimum", and "cannot attack, defend, cast spells, use magic devices, **carry burdens**, run"
— *"This is true even if cure spells and/or healing potions are given"*. Only a *heal* spell
would clear it, and the party has none.

**Consequences for the march out:** Dave carries nothing and fights not at all. He can walk
slowly. The party's plan is to accept **3"** movement with the other four each carrying a
tapestry.

### Encumbrance, by the numbers (PHB pp. 101–102)

A tapestry is **600 gp = 60 lbs**. Bands are 350 / 700 / 1050 gp plus the STRENGTH TABLE II
allowance. Tristle (10, no allowance) and Frython (8, **normal — 8–9 is not penalised**) are
light enough to take one at 6". Blartho and Yrtone (14, +200) come to ~1300 against a ceiling
of 1250, so a whole tapestry each puts them at **3"**.

## Session log

### Expedition 1
**Day 1** — entered, cleared entrance corridor to the second alcoves, killed 1 troglodyte
and 3 orcs, withdrew and camped outside.
**Day 2** — reached the crossroads, searched the dead, explored the dining hall, lounge, and
the concealed hide. Killed a centipede and a troglodyte (Tristle, solo). Scouted the Room of
Pools by infravision.
**Day 3** — found and looted the Advisor's Chamber (gas trap, empty drawer, **the painting**),
fought kobolds, withdrew. Sold the painting for **250 gp, unrecognised** — the location of
Quasqueton stays secret.

### Expedition 2 — the near-disaster
**Day 1** — troglodytes at the crossroads, then **two more from behind in corridor 3**.
**Five of six went below 0.** No healing left. Dave stabilised them all in the right order
and held the corridor alone.
**Day 3** — Dave went down to giant rats outside the door. **Yrtone crawled out at −3 and
staunched him.** Five helpless people stood in the doorway and **roared four giant rats into
a rout**, then dragged Dave in on a rope.
**Days 3–10** — eleven days sealed in the dining hall. **Tristle found the drinking pool**
by reasoning that spring water runs cold, and ran the water route in the dark at −4 hp.
Discovered the **pool of healing** (present only 30% of the time, and its virtue does not
survive leaving the room).
**Day 11** — marched out. Killed a troglodyte at the crossroads (Yrtone down again) and two
berserkers in the entrance corridor (Torsat down) — the berserker fight won by **flanking**
for the rear-attack +2.

**Nobody has died. Fifteen-plus encounters across two expeditions.**

### Standing problems
- **Out of food.** Provisioned 66 person-days, spent 66.
- Torsat and Yrtone both need **another full week** of enforced rest.
- One *cure light wounds* in the party.


---

# EXPERIENCE AND INVENTORY — see `campaign/`

**These are no longer kept on this sheet.** The XP figures here were last correct on
day 2 of expedition 1 and were quoted as authoritative for weeks afterwards; the
equipment list was the original outfitting plus day-2 recoveries, which is how the party
was told its iron spikes were in a door they had long since recovered them from.

| what | where | how to read it |
|---|---|---|
| every encounter and award | `campaign/encounters.tsv` | append one row per award; never store a running total |
| who gets the +10% | `campaign/characters.tsv` | prime requisite and score |
| current totals | `python tools/xp.py` | computed fresh every time |
| what the party carries | `campaign/inventory.tsv` | edited in place, source of record |
| treasure by monster | `python tools/treasure.py` | the MM appendix, encoded once |

Reconstructed from the session transcript on 2026-08-25. Expeditions 1 and 2 are
represented by a single **anchor row** carrying the per-character totals stated at the
return to town (Dave 240, Tristle 208, Yrtone 156, Frython 156, Torsat 142, Blartho 142),
because the individual awards before that point cannot be recovered reliably. Everything
from expedition 3 onward is itemised.

## Dave

DMG p.82: comatose 1-6 turns (**rolled 2**), then **a full week of rest, minimum** — not
shortened by any cure spell, only by *heal*. DMG p.82 also gives natural healing at **1 hp
per day of rest, up to 7 days**; CON 13 carries no penalty, so the week he owes and the
healing he needs are the same week: **2 → 9, full**. Buying temple healing would be wasted
money.

Yrtone 5/7 → full on the same rest. Everyone else already is.
