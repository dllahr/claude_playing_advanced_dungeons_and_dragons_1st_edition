# Zero-level characters — "normal men" in AD&D 1e

Scope: **PHB + DMG + MM core only.** Written 2026-09-05 to answer *"what happens
when Hask, Dellie or Ista accumulate enough experience?"*

**The short answer is that the question has no printed answer, and the reason is
worth stating exactly rather than paraphrasing:** in 1e, 1st level begins at
**zero** experience points. Nothing stands between a 0-level person and 1st level
except the *capacity* to hold a class at all — and the PHB says most people do not
have it.

> *"Each player character begins the campaign at 1st level with no experience
> points accumulated. … It is important to keep in mind that **most humans and
> demi-humans are "0 level". They do not have the ability to gain experience
> levels.** Player characters are unusual and superior."*

*source: **PHB p. 106**, EXPERIENCE. Read from a 200 dpi page render 2026-09-05
by the research agent; **not independently re-rendered.** The sentence carries no
digits.*

## Why there is no XP threshold to reach

| class | XP range for 1st level | hit die | level title |
|---|---|---|---|
| Fighter | 0–2,000 | d10 | Veteran |
| Cleric | 0–1,500 | d8 | Acolyte |

*source: **PHB p. 22** (FIGHTERS TABLE) and **PHB p. 20** (CLERICS TABLE I), page
renders 2026-09-05. Thief (0–1,250, d6) and magic-user (0–2,500, d4) are taken
from `campaign/characters.tsv` and are **UNVERIFIED here** — render PHB pp. 25-26
before quoting them.*

**An NPC's accumulated half shares are therefore never "enough for 1st level".**
Either the person can hold a class, in which case they would already be 1st level,
or they cannot, in which case no total will ever do it.

## To hit — 0-level HUMANS use the CHARACTER matrix, column 0

DMG p. 74's matrix I.B is headed *"ATTACK MATRIX FOR FIGHTERS, PALADINS, RANGERS,
BARDS, AND **0 LEVEL HALFLINGS AND HUMANS**\*"* and carries a column labelled **0**
to the left of 1-2. Its footnote: *"Dwarves, elves and gnomes are never lower than
1st level (unlike halflings and humans, **which may be of 0 level**)."*

PHB p. 105: *"**Normal men such as men-at-arms are always considered at level
0.**"*

| Target AC | 0 level | Fighter 1-2 |
|---|---|---|
| 2 | 19 | 18 |
| 3 | 18 | 17 |
| 4 | 17 | 16 |
| 5 | 16 | 15 |
| 6 | 15 | 14 |
| 7 | 14 | 13 |
| 8 | 13 | 12 |
| 9 | 12 | 11 |
| 10 | 11 | 10 |

*source: **DMG p. 74**, ATTACK MATRIX I.B, columns "0" and "1-2".
**Re-rendered and read directly at 400 dpi 2026-09-05** — this table is
first-hand, not relayed.*

> ### THIS CORRECTS HOW HASK, DELLIE AND ISTA WERE BEING RUN
>
> `campaign/npcs.md` had them on the **monster** matrix (DMG p. 75) column "1" —
> **16 to hit AC 3**. The right number for a 0-level *human* is **18**, two points
> worse.
>
> The DMG's own two tables agree once the row is right: monster-matrix column
> *"up to 1-1"* is also 18 vs AC 3, and p. 85's XP footnote sorts peasants into
> "up to 1-1" and men-at-arms into "1-1 to 1". **The "1 HD" column is the one row
> nothing in the books puts a normal man in.**
>
> **Per CHECKLIST §9 this is PROSPECTIVE.** Every attack already resolved at 16
> stands.

## Saves at 0 level — its own row, above 1st-2nd

*(Heading deliberately avoids the words "saving throws": `combat.py` calls
`rules.find('Saving throws')` and the cache treats an ambiguous match as an
error rather than picking one. It fired the moment this file was added, which is
the guard working.)*

| Fighters, level | Paral./Poison/Death | Petrif./Polymorph | Rod/Staff/Wand | Breath | Spell |
|---|---|---|---|---|---|
| **0** | 16 | 17 | 18 | 20 | 19 |
| 1-2 | 14 | 15 | 16 | 17 | 17 |
| 3-4 | 13 | 14 | 15 | 16 | 16 |

*source: **DMG p. 79**, SAVING THROW MATRIX I FOR CHARACTERS AND HUMAN TYPES,
Fighters rows 0, 1-2, 3-4. **Re-rendered and read directly at 350 dpi
2026-09-05.** Footnote b to the Fighters block: "Includes Paladins, Rangers, and
**0 level types**."*

## Hit points — a normal man has no hit DIE

| General Classification | Hit Points | Combat Ability |
|---|---|---|
| sedentary females | 1-3 | −3 |
| sedentary males | 1-4 | −2 |
| active females | 1-4 | −1 |
| active males | 2-5 | 0 level |
| laboring females | 2-5 | 0 level |
| laboring males | 2-7 | 0 level |

*source: **DMG p. 88**, TYPICAL INHABITANTS, 200 dpi page render 2026-09-05 by the
research agent; **not independently re-rendered.** "Sedentary" = clerk, scribe;
"Active" = serving maid, **carpenter**; "Laboring" = farming, mining, menial
labour. **MM p. 66** (MEN): "Normal men have from 1-6 hit points each."*

**Recording a normal man as "1 hit die" is a campaign convenience, not a book
number** — and it is exactly what put Hask and Dellie on the wrong attack column.

## XP VALUE of a 0-level man as an opponent

| opponent | XP hit-dice category | Basic XPV | XP per hit point |
|---|---|---|---|
| peasants / levies | up to 1 − 1 | 5 | 1 |
| men-at-arms | 1 − 1 to 1 | 10 | 1 |

*source: **DMG p. 85**, footnote to EXPERIENCE POINTS VALUE OF MONSTERS — "Treat
peasants/levies as up to 1 − 1, men-at-arms as 1 − 1 to 1, and all levels as the
n + 1 hit dice category." 200 dpi page render 2026-09-05 by the research agent.*

## Ability scores for an NPC — the DMG's two methods

| NPC type | method | resulting range |
|---|---|---|
| General Characters | 3d6 per ability, **any 1 counts as 3, any 6 counts as 4** | **9–12 on every ability** |
| Special Characters, **including Henchmen** | 3d6 full range (3–18), except the ability germane to the profession: use a PC method, **or add +1 to each of the 3 dice that rolled under 6** | 3–18, germane ability boosted |

*source: **DMG p. 11**, NON-PLAYER CHARACTERS, 200 dpi page render 2026-09-05 by
the research agent.*

**The 9–12 consequence is arithmetic, not text:** forcing every die to 3 or 4
makes 9 the floor and 12 the ceiling. A General Character therefore
**automatically clears fighter (STR 9), cleric (WIS 9) and thief (DEX 9)** and
**can never** reach the 16 needed for a prime-requisite bonus, nor qualify as
paladin, ranger, illusionist, assassin or monk.

## Class minimums — the gate

| class | printed minimum | page | verified? |
|---|---|---|---|
| Fighter | strength 9, constitution 7+ | PHB p. 22 | render |
| Cleric | wisdom 9 | PHB p. 20 | render |
| Thief | dexterity not less than 9 | PHB p. 26 | render |
| Paladin | STR 12, INT 9, WIS 13, CON 9, CHA 17, human | PHB p. 22 | render |
| Magic-User | intelligence 9, dexterity 6 | PHB p. 25 | **TEXT LAYER ONLY** |
| Illusionist | intelligence 15, dexterity 16 | PHB p. 26 | **TEXT LAYER ONLY** |
| Assassin | strength 12, intelligence 11, dexterity 12 | PHB p. 28 | **TEXT LAYER ONLY** |

*source: PHB class descriptions, pp. 20, 22, 25, 26, 28, read 2026-09-05 by the
research agent. **The last three are unverified — render before relying on them.***

## How the books choose an NPC's class — a die roll, not a biography

| class | share | sub-roll |
|---|---|---|
| CLERICS | 20% | d6, 1 = druid |
| FIGHTERS | 44% | d10, 1 = ranger, 2 = paladin |
| MAGIC-USERS | 20% | d6, 1 = illusionist |
| THIEVES | 15% | d6, 1 = assassin |
| MONKS | 1% | — |

*source: **DMG p. 35**, HENCHMEN → Classes Of Prospective Henchmen, applied to
"the total number of prospective characters **who are capable of working upwards
in level**." 200 dpi page render 2026-09-05 by the research agent.*

**This is the only NPC class-determination procedure in the three books**, and it
is written for a faceless applicant pool, not a person with a played history.

## Henchmen — who they are, and that they DO level

| fact | text | page |
|---|---|---|
| Henchmen arrive **at 1st level** | "As a general rule, **only characters of 1st level of experience will be attracted to service** with a player character." | DMG p. 34 |
| Only 1% of humans can advance at all | "Human and half-orc characters **suitable for level advancement are found at a ratio of 1 in 100**." | DMG p. 35 |
| Of those, 1 in 1,000 population takes service | "about **1 in 1,000 population will be interested** in offers of employment as a henchman" | DMG p. 35 |
| Henchmen arrive with nothing | "All henchmen will come with nothing except the (normal) clothes they wear… **no armor or weapons, nothing!**" | DMG p. 36 |
| Henchmen **do** gain levels | "not only will their **player characters and henchmen gain levels of experience**…" | DMG p. 112 |
| Henchmen draw a **HALF share** | "each survivor gains 430 — adjusted for difficulty and for being actual player characters or **halved for henchman characters**" | DMG p. 85 |
| Henchmen check morale; PCs never do | "Your character's **henchmen will probably have to check morale**, so too will hirelings." | PHB p. 106 |

*source: **DMG pp. 34, 35, 36, 85, 112** and **PHB p. 106**, page renders
2026-09-05 by the research agent; **not independently re-rendered.***

## Loyalty consequences of status — DMG p. 36

Normal loyalty base **50%**, ± the liege's charisma adjustment.

| Enlistment Or Association | Modifier |
|---|---|
| associated non-player character | −10% |
| captured and enlisted | −15% |
| henchman | +5% |
| hired mercenary | 0% |
| hired mercenary, short term | −5% |
| slave | −30% |

*source: **DMG p. 36**, LOYALTY BASE MODIFIERS, 200 dpi page render 2026-09-05 by
the research agent.*

| Training Or Status Level | Modifier |
|---|---|
| untrained or peasant | −25% |
| little training, levied troops | −15% |
| newly recruited regulars | −5% |
| trained regulars | +10% |
| elite, sub-officers, minor officials / expert hireling | +20% |
| guards, officers, or major officials / henchmen | +30% |

*source: **DMG p. 36**, LOYALTY BASE MODIFIERS, 200 dpi page render 2026-09-05 by
the research agent.*

**"Untrained or peasant" and "henchman" are 55 points apart.** The books never say
what moves someone between those rows — but those two rows are the before and
after of this entire question.

## Training, if any of them ever does become classed

> *"**LEVEL OF THE TRAINEE CHARACTER × 1,500 = WEEKLY COST DURING STUDY/TRAINING.**
> The level of the aspiring character should be computed at **current (not to be
> gained) level.**"*
>
> *"Initial study and/or training must be conducted under the tutelage of a
> character of the same class and profession as the trainee…"*
>
> *"**ONCE A CHARACTER HAS POINTS WHICH ARE EQUAL TO OR GREATER THAN THE MINIMUM
> NUMBER NECESSARY TO MOVE UPWARDS IN EXPERIENCE LEVEL, NO FURTHER EXPERIENCE
> POINTS CAN BE GAINED UNTIL THE CHARACTER ACTUALLY GAINS THE NEW LEVEL.**"*

*source: **DMG p. 86**, 200 dpi page render 2026-09-05 by the research agent.
**The word "henchman" does not appear in the training section at all** — it says
"character" throughout, and never says who pays.*

Note what the printed formula returns for a 0-level trainee: **0 × 1,500 = 0 gp.**
DMG p. 35's hiring bonus of "not less than 100 gold pieces per level of the
applicant" is likewise 0. **Both are inference from printed formulae, not printed
rules.**

## "Upward progress is never automatic" — and what it actually licenses

> *"**UPWARD PROGRESS IS NEVER AUTOMATIC.** … The gaining of sufficient experience
> points is necessary to indicate that a character is *eligible* to gain a level
> of experience, but **the actual award is a matter for you, the DM, to decide.**"*

*source: **DMG p. 86**, GAINING EXPERIENCE LEVELS, 200 dpi page render 2026-09-05
by the research agent.*

**Read what this authorises: the DM may WITHHOLD a level from an eligible
character.** It does not say the DM may grant a *class* to someone who has none.

## WHERE THE BOOKS ARE SILENT — searched, and genuinely absent

Text-layer search across all three PDFs, 2026-09-05:
`(become|becoming) a (1st|first) level` → **one hit**, DMG p. 38, about a *player*
cleric's novitiate. `(attain|reach|rise to|gain) (1st|first) level` → **zero**.
`from 0 level` / `0 level to 1st` / `no longer 0 level` → **zero**.
`non-player character` within 200 chars of `experience` in the DMG → **zero**.

The books say **nothing** about:

1. any procedure for a 0-level person to acquire a class
2. any XP threshold for entering 1st level (structurally impossible — see above)
3. whether accumulated half shares carry over, reset, or void
4. what happens to hit points when a flat 1-6 becomes a d10
5. whether henchmen pay their own training, or the liege does
6. whether DMG p. 86's 1,500 gp/level/week applies to NPCs at all
7. how a *specific* NPC's class is chosen from their history (p. 35 rolls it)
8. whether "1 in 100" is a per-person die roll or a population statistic
9. whether "0 level" is a permanent condition or a starting one

**The only place the books call 0 level permanent is a penalty clause:**

> *"If this brings the character below 1st level of experience, then the
> individual is a **0 level person never capable of gaining experience again**.
> If a 0 level individual is drained an energy level, he or she is dead."*

*source: **DMG p. 119**, ENERGY DRAIN BY UNDEAD OR DEVICE, 300 dpi crop
2026-09-05 by the research agent.*

That **"again"** is the only textual hook suggesting an ordinary 0-level person
differs from a drained one. **It is one adverb in a passage about wights. Do not
build on it.**

## Do not fill these gaps from later editions

There is no 1e "0-level character advancement" rule, no XP-to-first-level number,
and no class-on-promotion procedure. **Anything that feels like one is coming from
somewhere else.** Rulings made to bridge these gaps belong in
`modules/B1_DM_NOTES_DO_NOT_READ.md`, marked as rulings — not restated here as if
the books said them.
