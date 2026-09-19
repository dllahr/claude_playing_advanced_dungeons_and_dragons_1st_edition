# Combat & Saving Throws — AD&D 1e

Scope: **PHB + DMG core only.** No Unearthed Arcana.

`tools/rules.py` PARSES THIS FILE. The pipe-tables below are the single source
of truth for `tools/combat.py`; nothing here is duplicated in Python, so the
page citation and the number the dice are compared against are the same object.
If you edit a table, keep the header text identical — the parser finds tables by
their heading.

## To-hit, characters (level 1)

Roll d20, meet or beat the number for the target's AC.

Columns are the level bands the party is actually in: fighters 1–2, clerics 1–3,
thieves 1–4, magic-users 1–5. Fighter and cleric are identical at these levels,
as are thief and magic-user.

| Target AC | Fighter | Cleric | Thief | Magic-User |
|---|---|---|---|---|
| -10 | 25 | 25 | 26 | 26 |
| -9 | 24 | 24 | 25 | 25 |
| -8 | 23 | 23 | 24 | 24 |
| -7 | 22 | 22 | 23 | 23 |
| -6 | 21 | 21 | 22 | 22 |
| -5 | 20 | 20 | 21 | 21 |
| -4 | 20 | 20 | 20 | 20 |
| -3 | 20 | 20 | 20 | 20 |
| -2 | 20 | 20 | 20 | 20 |
| -1 | 20 | 20 | 20 | 20 |
| 0 | 20 | 20 | 20 | 20 |
| 1 | 19 | 19 | 20 | 20 |
| 2 | 18 | 18 | 19 | 19 |
| 3 | 17 | 17 | 18 | 18 |
| 4 | 16 | 16 | 17 | 17 |
| 5 | 15 | 15 | 16 | 16 |
| 6 | 14 | 14 | 15 | 15 |
| 7 | 13 | 13 | 14 | 14 |
| 8 | 12 | 12 | 13 | 13 |
| 9 | 11 | 11 | 12 | 12 |
| 10 | 10 | 10 | 11 | 11 |

*source: **DMG p. 74**, matrices I.A (clerics), I.B (fighters), I.C (magic-users),
I.D.1 (thieves), read from a 200 dpi page render 2026-08-25. This replaces an
earlier transcription from 1eonline; every value agreed, but 1eonline has been
wrong here before (it gave 9 instead of 13 for a 2 HD monster vs AC 3) and a
page render is the standard.*

**Levels above these bands are NOT transcribed.** When someone reaches 3rd
level, render DMG p. 74 again and add the column — do not extrapolate. The
matrices contain a plateau of 20s that a shift-by-one guess gets wrong.

**Party modifiers:** Dave +1 (STR 18/26). Tristle +1 with short sword, long sword,
or bow (elf). Everyone else +0.

## To-hit, monsters (by hit dice)

**Monsters use their own matrix, not a character table.** The two differ: a 1 HD
monster needs **16** to hit AC 3, where a 1st-level fighter needs 17. Getting
this wrong in play is what put the table in `CHECKLIST.md`.

| Target AC | up to 1-1 | 1-1 | 1 | 1+ | 2-3+ | 4-5+ | 6-7+ | 8-9+ | 10-11+ | 12-13+ | 14-15+ | 16+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -10 | 26 | 25 | 24 | 23 | 21 | 20 | 20 | 20 | 20 | 19 | 18 | 17 |
| -9 | 25 | 24 | 23 | 22 | 20 | 20 | 20 | 20 | 19 | 18 | 17 | 16 |
| -8 | 24 | 23 | 22 | 21 | 20 | 20 | 20 | 20 | 18 | 17 | 16 | 15 |
| -7 | 23 | 22 | 21 | 20 | 20 | 20 | 20 | 19 | 17 | 16 | 15 | 14 |
| -6 | 22 | 21 | 20 | 20 | 20 | 20 | 19 | 18 | 16 | 15 | 14 | 13 |
| -5 | 21 | 20 | 20 | 20 | 20 | 20 | 18 | 17 | 15 | 14 | 13 | 12 |
| -4 | 20 | 20 | 20 | 20 | 20 | 19 | 17 | 16 | 14 | 13 | 12 | 11 |
| -3 | 20 | 20 | 20 | 20 | 19 | 18 | 16 | 15 | 13 | 12 | 11 | 10 |
| -2 | 20 | 20 | 20 | 20 | 18 | 17 | 15 | 14 | 12 | 11 | 10 | 9 |
| -1 | 20 | 20 | 20 | 19 | 17 | 16 | 14 | 13 | 11 | 10 | 9 | 8 |
| 0 | 20 | 20 | 19 | 18 | 16 | 15 | 13 | 12 | 10 | 9 | 8 | 7 |
| 1 | 20 | 19 | 18 | 17 | 15 | 14 | 12 | 11 | 9 | 8 | 7 | 6 |
| 2 | 19 | 18 | 17 | 16 | 14 | 13 | 11 | 10 | 8 | 7 | 6 | 5 |
| 3 | 18 | 17 | 16 | 15 | 13 | 12 | 10 | 9 | 7 | 6 | 5 | 4 |
| 4 | 17 | 16 | 15 | 14 | 12 | 11 | 9 | 8 | 6 | 5 | 4 | 3 |
| 5 | 16 | 15 | 14 | 13 | 11 | 10 | 8 | 7 | 5 | 4 | 3 | 2 |
| 6 | 15 | 14 | 13 | 12 | 10 | 9 | 7 | 6 | 4 | 3 | 2 | 1 |
| 7 | 14 | 13 | 12 | 11 | 9 | 8 | 6 | 5 | 3 | 2 | 1 | 0 |
| 8 | 13 | 12 | 11 | 10 | 8 | 7 | 5 | 4 | 2 | 1 | 0 | -1 |
| 9 | 12 | 11 | 10 | 9 | 7 | 6 | 4 | 3 | 1 | 0 | -1 | -2 |
| 10 | 11 | 10 | 9 | 8 | 6 | 5 | 3 | 2 | 0 | -1 | -2 | -3 |

*source: **DMG p. 75**, "II. ATTACK MATRIX FOR MONSTERS (Including Goblins,
Hobgoblins, Kobolds, and Orcs)", read from a 200 dpi page render 2026-08-25.*

**Reading the columns.** A monster with 1 hit die exactly uses the `1` column;
`1+` means 1+1 up to 1+3; `2-3+` covers 2 HD through 3+3, and so on. The DMG's
note: *"Any plus above +3 equals another hit die, i.e. 6+6 equals 7 hit dice."*
So a 3+4 creature is read as 4 HD and uses the `4-5+` column.

Missiles: **−5 at long range, −2 at medium**. Which band a shot falls in is
decided by the range table under *Missile rate of fire and range* below.

## Flank and rear attacks

| Position | To hit | Defender's shield | Defender's DEX bonus |
|---|---|---|---|
| Front | — | applies | applies |
| Flank | — | **negated** | applies |
| Rear flank | — | **negated** | **negated** |
| **Rear** | **+2** | **negated** | **negated** |
| Stunned, prone or motionless | **+4** | negated | negated |

*source: **DMG p. 70**, "Special Types Of Attacks", text layer, cross-checked
2026-08-26.*

> ### ⚠ GETTING TO A FLANK — A HELD LINE CANNOT BE WALKED THROUGH
>
> **The table above says what a flank is worth. It does not say you can reach
> one, and reaching one is the hard part.**
>
> **A CONTESTED FRONTAGE IS A BLOCKED FRONTAGE.** Two defenders facing two
> attackers across a 10-ft corridor hold that corridor: **nobody goes past,
> either way.** The empty third slot is not a lane — it is the space the four of
> them are already using to fight in.
>
> **Only when the opposing side is reduced enough to leave the frontage
> genuinely open** can anyone move round to a flank or a rear. That is how every
> flank and rear attack in this campaign has actually happened — Dave's rear
> attack on the LAST troglodyte of expedition 4, with nothing else left to hold
> the line.
>
> **AND IT GOVERNS THE LANE RULE TOO.** If the rank in front is engaged, the
> corridor counts as **FILLED** for missile purposes, so the harsh row of the
> lane rule applies and not the "allies not directly in the lane" row. **A gap in
> your own rank is not a firing lane while somebody is fighting in it.**
>
> **THE FIGURES ARE IN `rules/exploration.md` AND ARE NOT REPEATED HERE** — that
> file is the only home for them and `test_lane_rule.py` enforces it. This block
> says WHICH ROW APPLIES; go there for what it costs. *(The test caught this
> paragraph restating them within a minute of it being written, which is the
> fourth time it has caught a paraphrase.)*
>
> *source: **CAMPAIGN RULING**, carried in play since the early expeditions and
> written down 2026-09-14 when the DM contradicted it — telling the player there
> was "a clear lane past Blartho's left shoulder" because the rear rank was two
> men in a three-man slot. The player: "for many initial expeditions we did only
> 2 people in the front rank, and the enemy did as well, and you ruled in that
> case we couldn't get by them. It was only when we were down to facing one
> opponent that we could move around and outflank them."*

A flank attack carries **no to-hit bonus of its own** — all it does is take away
the shield. Against something with no shield and no Dexterity bonus (most
monsters, whose AC is hide and not gear) flanking buys nothing at all, and only
getting fully behind it is worth the movement.

## Weapon proficiency

| Class | Initial weapons | Non-proficiency penalty | Added proficiency |
|---|---|---|---|
| Cleric | 2 | -3 | 1 per 4 levels |
| Druid | 2 | -4 | 1 per 5 levels |
| Fighter | 4 | -2 | 1 per 3 levels |
| Paladin | 3 | -2 | 1 per 3 levels |
| Ranger | 3 | -2 | 1 per 3 levels |
| Magic-User | 1 | -5 | 1 per 6 levels |
| Illusionist | 1 | -5 | 1 per 6 levels |
| Thief | 2 | -3 | 1 per 4 levels |
| Assassin | 3 | -2 | 1 per 4 levels |
| Monk | 1 | -3 | 1 per 2 levels |

*source: **PHB p. 37**, WEAPON PROFICIENCY TABLE, 200 dpi page render 2026-08-25.
The penalty "applies to attacks by the character using such a weapon in missile
or melee combat".*

**Tristle's spear: −3, deliberately accepted.** His proficiencies are long sword
and short bow, so every spear attack takes the thief's −3. He carries it anyway
because a **spear reaches from the second rank** and a long sword does not — in a
10-ft corridor behind two shield-bearing fighters, the sword has no target. This
is a standing choice by the player, not an oversight; see `CHECKLIST.md` §3.

## Weapon damage

Damage differs by the **size of the target**: S/M is anything up to man-sized,
L is larger than man-sized.

| Weapon | Weight gp | vs S or M | vs L | Notes |
|---|---|---|---|---|
| Arrow | 2 | 1-6 | 1-6 | |
| Axe, battle | 75 | 1-8 | 1-8 | |
| Axe, hand or throwing | 50 | 1-6 | 1-4 | |
| Bardiche | 125 | 2-8 | 3-12 | |
| Bec de corbin | 100 | 1-8 | 1-6 | |
| Bill-guisarme | 150 | 2-8 | 1-10 | includes Scorpion |
| Bo stick | 15 | 1-6 | 1-3 | |
| Club | 30 | 1-6 | 1-3 | |
| Dagger | 10 | 1-4 | 1-3 | |
| Dart | 5 | 1-3 | 1-2 | |
| Fauchard | 60 | 1-6 | 1-8 | |
| Fauchard-fork | 80 | 1-8 | 1-10 | |
| Flail, footman's | 150 | 2-7 | 2-8 | |
| Flail, horseman's | 35 | 2-5 | 2-5 | |
| Fork, military | 75 | 1-8 | 2-8 | |
| Glaive | 75 | 1-6 | 1-10 | includes Couteaux de Breche |
| Glaive-guisarme | 100 | 2-8 | 2-12 | |
| Guisarme | 80 | 2-8 | 1-8 | includes Bill/Bill Hook |
| Guisarme-voulge | 150 | 2-8 | 2-8 | includes Lochaber Axe |
| Halberd | 175 | 1-10 | 2-12 | |
| Hammer, lucern | 150 | 2-8 | 1-6 | |
| Hammer | 50 | 2-5 | 1-4 | |
| Javelin | 20 | 1-6 | 1-6 | |
| Jo stick | 40 | 1-6 | 1-4 | |
| Lance, light horse | 50 | 1-6 | 1-8 | double damage from a charging mount |
| Lance, medium horse | 100 | 2-7 | 2-12 | double damage from a charging mount |
| Lance, heavy horse | 150 | 3-9 | 3-18 | double damage from a charging mount |
| Mace, footman's | 100 | 2-7 | 1-6 | |
| Mace, horseman's | 50 | 1-6 | 1-4 | |
| Morning star | 125 | 2-8 | 2-7 | includes Godentag, Holy Water Sprinkler |
| Partisan | 80 | 1-6 | 2-7 | includes Bohemian Ear-Spoon |
| Pick, military, footman's | 60 | 2-7 | 2-8 | |
| Pick, military, horseman's | 40 | 2-5 | 1-4 | |
| Pike, awl | 80 | 1-6 | 1-12 | |
| Quarrel (bolt), light | 1 | 1-4 | 1-4 | |
| Quarrel (bolt), heavy | 2 | 2-5 | 2-7 | |
| Ranseur | 50 | 2-8 | 2-8 | includes Chauves Souris, Ransom, Rhonca, Roncie, Runka |
| Scimitar | 40 | 1-8 | 1-8 | includes Cutlass, Sabre, Sickle-sword, Tulwar |
| Sling bullet | 2 | 2-5 | 2-7 | |
| Sling stone | 1 | 1-4 | 1-4 | |
| Spear | 40-60 | 1-6 | 1-8 | double damage when set to receive a charge |
| Spetum | 50 | 2-7 | 2-12 | includes Corseque, Korseke |
| Staff, quarter | 50 | 1-6 | 1-6 | |
| Sword, bastard | 100 | 2-8 | 2-16 | |
| Sword, broad | 75 | 2-8 | 2-7 | |
| Sword, long | 60 | 1-8 | 1-12 | |
| Sword, short | 35 | 1-6 | 1-8 | |
| Sword, two-handed | 250 | 1-10 | 3-18 | |
| Trident | 50 | 2-7 | 3-12 | |
| Voulge | 125 | 2-8 | 2-8 | |

*source: **PHB p. 37**, WEIGHT AND DAMAGE BY WEAPON TYPE, 200 dpi page render
2026-08-25.*

Italicised weapons on the page (fauchard, fauchard-fork, fork military, glaive,
lance light) **do double the rolled damage to L creatures when set to receive a
charge**; the spear does double to any opponent when set. None of the party's
weapons except the spear are in that group.

## Saving throws (levels 1–4)

Roll d20, meet or beat.

| Class | Level | Paralyze/Poison/Death | Petrify/Polymorph | Rod/Staff/Wand | Breath | Spell |
|---|---|---|---|---|---|---|
| Cleric | 1–3 | 10 | 13 | 14 | 16 | 15 |
| Fighter | 1–2 | 14 | 15 | 16 | 17 | 17 |
| Fighter | 3–4 | 13 | 14 | 15 | 16 | 16 |
| Magic-User | 1–5 | 14 | 13 | 11 | 15 | 12 |
| Thief | 1–4 | 13 | 12 | 14 | 16 | 15 |

*source: **DMG p. 79**, "I. SAVING THROW MATRIX FOR CHARACTERS AND HUMAN TYPES",
200 dpi page render 2026-08-25. Every value matched the earlier 1eonline
transcription.*

**A natural 1 always fails**, whatever the modifiers — the DMG states this
explicitly, and no bonus can save a 1.

**Monster saves** (DMG p. 79, matrix II): monsters use the *character* matrix.
Hit dice equate to experience level, with pluses in hit points moving the
creature up one hit die (1+1 through 1+4 becomes level 2, 1+5 through 1+8
becomes 3, and so on). **Most monsters save as fighters**; one with another
class's abilities gets the most favourable score, and one with no real
offensive capability saves in its area of ability. **Non-intelligent creatures
save at half their hit dice, rounded up** — except against poison or death
magic, where they use the full value.

**Party modifiers:** Blartho +1 and Yrtone +2 vs mind-affecting (Wisdom magical attack
adjustment). Tristle 90% resistance to *sleep* and *charm* (elf) — this is a flat resistance
roll, not a saving throw, and applies before any save.

## Missile rate of fire and range

**A previous note in this file said the missile table "did not survive OCR in
these scans". That was wrong.** The text layer is indeed destroyed — grepping
the `.txt` for a dart's range returns nothing, and `page.get_text()` on PHB
p. 38 dissolves the whole block into `L 7 L A f 4` — but the *printed page* is
clean and completely legible at 400 dpi. The table below was read off the render.
Rate of fire is no longer "confirmed by the player"; it is the book's own column,
and it agrees with what the player said.

**Ranges are printed in inches (″), and the inch is not a fixed distance.**
This is the whole rule, and it is what decides the to-hit modifier:

> *"Outdoors, 1″ equals 10 yards. Indoors 1″ equals 10 feet."* — **PHB p. 39**,
> DISTANCE

So **underground, multiply the inches below by 10 to get feet.** A dart's 1½″
short range is **15 feet**; anything past that is medium and takes −2. Getting
this backwards (reading 1½″ as 15 yards, or as 45 feet) hands the party three or
four extra squares of unpenalised throwing down a corridor.

| Weapon | Fire rate | S | M | L |
|---|---|---|---|---|
| Axe, hand | 1 | 1 | 2 | 3 |
| Bow, composite, long | 2 | 6 | 12 | 21 |
| Bow, composite, short | 2 | 5 | 10 | 18 |
| Bow, long | 2 | 7 | 14 | 21 |
| Bow, short | 2 | 5 | 10 | 15 |
| Club | 1 | 1 | 2 | 3 |
| Crossbow, heavy | ½ | 8 | 16 | 24 |
| Crossbow, light | 1 | 6 | 12 | 18 |
| Dagger | 2 | 1 | 2 | 3 |
| **Dart** | **3** | **1½** | **3** | **4½** |
| Hammer | 1 | 1 | 2 | 3 |
| Javelin | 1 | 2 | 4 | 6 |
| Sling (bullet) | 1 | 5 | 10 | 20 |
| Sling (stone) | 1 | 4 | 8 | 16 |
| Spear | 1 | 1 | 2 | 3 |

*source: **PHB p. 38**, "WEAPON TYPES, GENERAL DATA, AND 'TO HIT' ADJUSTMENTS",
the lower block headed "Hurled Weapons and Missiles", 400 dpi page render
2026-08-29. S/M/L are inches; the page's own note reads "Ranges are: S = Short,
M = Medium, L = Long."*

**Fire rate ½ (heavy crossbow) means one shot every OTHER round**, not half
damage. The page prints it as the fraction. Everything else is shots per round.

**The oil flask is not on this table.** Hurled containers are handled separately
by the DMG, and their range is much shorter than any bow:

> *"Range: The range of all such container missiles is 3″. Beyond 1″ is medium,
> and beyond 2″ is long (−2 and −5 'to hit' respectively)."* — **DMG p. 64**,
> COMBAT (MISSILE DISCHARGE), GRENADE-LIKE MISSILES

So a **flask of oil, holy water, acid or poison is S 1″ / M 2″ / L 3″** — 10 / 20
/ 30 feet indoors, and it **cannot be thrown past 30 feet at all**. That sentence
is also the clearest statement in either book of how the bands are read: the S
number is the top of short, the M number the top of medium, the L number the top
of long, and beyond L is out of range.

Missile modifiers: **−5 at long range, −2 at medium** — *verified from a 300 dpi
render of **DMG p. 74** 2026-08-29; the line "Missiles: −5 at **long** range, −2
at **medium** range." is printed under each attack matrix on pp. 74–75.* The PHB
prints the same thing at the foot of p. 38: *"Adjust by −2 at all medium ranges,
−5 at all long ranges."*

## Missile ranges underground — the same numbers in feet

Arithmetic, not a second source: every value is the inches above × 10, per PHB
p. 39. It is written out because the conversion is done under time pressure in
the middle of a round and 1½″ is exactly the kind of figure that gets fumbled.

| Weapon | Short (ft) | Medium (ft), −2 | Long (ft), −5 | Beyond |
|---|---|---|---|---|
| **Dart** | **to 15** | **over 15 to 30** | **over 30 to 45** | **no shot** |
| Dagger, hand axe, spear, club, hammer | to 10 | over 10 to 20 | over 20 to 30 | no shot |
| Oil flask (and any hurled container) | to 10 | over 10 to 20 | over 20 to 30 | no shot |
| Javelin | to 20 | over 20 to 40 | over 40 to 60 | no shot |
| Sling (stone) | to 40 | over 40 to 80 | over 80 to 160 | no shot |
| Sling (bullet) | to 50 | over 50 to 100 | over 100 to 200 | no shot |
| Bow, short | to 50 | over 50 to 100 | over 100 to 150 | no shot |
| Bow, composite, short | to 50 | over 50 to 100 | over 100 to 180 | no shot |
| Bow, long | to 70 | over 70 to 140 | over 140 to 210 | no shot |
| Bow, composite, long | to 60 | over 60 to 120 | over 120 to 210 | no shot |
| Crossbow, light | to 60 | over 60 to 120 | over 120 to 180 | no shot |
| Crossbow, heavy | to 80 | over 80 to 160 | over 160 to 240 | no shot |

*source: derived by multiplying the inch values in **PHB p. 38** by 10, the
indoor scale given at **PHB p. 39** ("Indoors 1″ equals 10 feet"); oil flask from
**DMG p. 64**. No new page reading — check the table above if a number here
looks wrong.*

**Outdoors, multiply by 10 YARDS instead** (PHB p. 39), i.e. every distance here
triples. B1 is entirely underground, so the feet column is the one in play, but
do not carry it out of the dungeon.

**Nothing in this table is a corridor-length problem in B1.** A 10′ corridor is
one inch. Almost every indoor exchange in this module happens inside short range
for a bow and inside *medium* range for a dart — which is precisely why the dart
figure matters and the bow figure never comes up.

**DM ruling — throwing into a melee:** a natural 1 strikes a friendly at random among those
engaged. No blanket penalty otherwise.

**Frython at 3 darts/round is the party's highest volume of attacks.** Thrown darts are
recoverable after a fight. At 15 feet or less he throws at no range penalty; past
15 feet each of those three darts is at −2, which is a bigger loss than it looks
because it applies three times a round.

## Missile weapon adjustment by target armor class — NOT IN PLAY

The same PHB p. 38 block carries a per-AC "to hit" adjustment for each missile
weapon, the missile counterpart of the melee weapon-vs-armor table. **This
campaign has not been applying weapon-vs-AC adjustments in either direction**,
and it is recorded here so the numbers exist without being switched on silently
mid-fight. Turning it on is a DM decision to make between expeditions, not in the
middle of a missile exchange; if it is ever turned on, the melee half of the same
table (upper block, PHB p. 38) has to go on with it.

| Weapon | AC 2 | AC 3 | AC 4 | AC 5 | AC 6 | AC 7 | AC 8 | AC 9 | AC 10 |
|---|---|---|---|---|---|---|---|---|---|
| Axe, hand | -4 | -3 | -2 | -1 | -1 | 0 | 0 | 0 | +1 |
| Bow, composite, long | -2 | -1 | 0 | 0 | +1 | +2 | +2 | +3 | +3 |
| Bow, composite, short | -3 | -3 | -1 | 0 | +1 | +2 | +2 | +2 | +3 |
| Bow, long | -1 | 0 | 0 | +1 | +2 | +3 | +3 | +3 | +3 |
| Bow, short | -5 | -4 | -1 | 0 | 0 | +1 | +2 | +2 | +2 |
| Club | -7 | -5 | -3 | -2 | -1 | -1 | -1 | 0 | 0 |
| Crossbow, heavy | -1 | 0 | +1 | +2 | +3 | +3 | +4 | +4 | +4 |
| Crossbow, light | -2 | -1 | 0 | 0 | +1 | +2 | +3 | +3 | +3 |
| Dagger | -5 | -4 | -3 | -2 | -1 | -1 | 0 | 0 | +1 |
| Dart | -5 | -4 | -3 | -2 | -1 | 0 | +1 | 0 | +1 |
| Hammer | -2 | -1 | 0 | 0 | 0 | 0 | 0 | 0 | +1 |
| Javelin | -5 | -4 | -3 | -2 | -1 | 0 | +1 | 0 | +1 |
| Sling (bullet) | -2 | -2 | -1 | 0 | 0 | 0 | +2 | +1 | +3 |
| Sling (stone) | -5 | -4 | -2 | -1 | 0 | 0 | +2 | +1 | +3 |
| Spear | -3 | -3 | -2 | -2 | -1 | 0 | 0 | 0 | 0 |

*source: **PHB p. 38**, "Hurled Weapons and Missiles", Armor Class Adjustment
columns, 400 dpi page render 2026-08-29. There is no AC 1 or better column and no
AC 0 column — the printed table starts at AC 2.*

**These figures assume short range.** The page says so explicitly: *"Armor Class
Adjustment is based on the weapon or missile being discharged at short range."*
The −2/−5 range penalty is applied on top, not instead. The dart and javelin rows
really do print +1 at AC 8, 0 at AC 9 and +1 at AC 10 — that non-monotonic step is
in the book, not a transcription slip.

## Morale (DMG, verified)

> *"Each monster has a base morale of 50%, +5%/hit die above 1, +1%/hit point
> above any hit dice."* — **DMG p. 67**, MORALE SCORES, read from the text layer
> and cross-checked 2026-08-25.

**"Hit points above any hit dice" is the `+n` in the hit-dice expression, not
the creature's rolled hit points.** A 3+2 HD monster scores 50 + 10 (two dice
above 1) + 2 (the "+2") = **62%**. A 1 HD berserker with a lucky 8 hit points
still scores **50%** — its hit dice carry no plus. Reading it as rolled hp
would make every well-rolled goblin braver than a hobgoblin.

| Check triggered when | Modifier |
|---|---|
| Faced by obviously superior force | check each round |
| 25% of party (or personal wound damage) | +5% |
| Leader unconscious | +10% |
| 50%+ of party (or personal wound damage) | +15% |
| Leader slain or deserts | +30% |

Roll d100, apply the modifier to the roll; if the adjusted result exceeds the morale score,
morale fails. The **margin of failure** determines the result:

| Margin | Result |
|---|---|
| 1–15% | Fall back, fighting |
| 16–30% | Disengage — retreat |
| 31–50% | Flee in panic |
| 51%+ | Surrender |

**Berserkers never check morale** (MM). Neither do unintelligent undead or
anything the module states is fighting to the death.

## Surprise — segments, not a coin flip

**Adopted in full 2026-09-13, day 79, by the player, mid-ambush**, after nine
expeditions of running it as "surprised or not, one free round." Both halves
below were in the books the whole time.

### How many segments

Roll d6 per side. **The lost segments are the DIFFERENCE between the two dice**,
not the fact of being surprised:

| Surprise dice difference | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Lost segments** | **0** | **1** | **2** | **3** |

*source: **DMG p. 61**, COMBAT (ENCOUNTERS, COMBAT, & INITIATIVE).*

> ### ⛔ THE TABLE ABOVE IS THE *BOTH-SURPRISED* CASE ONLY. IT WAS CACHED ALONE.
>
> **Found day 95, with one side surprised and the other not, and the cache had
> no rule for it.** The sentence immediately before the table is the general
> rule and it was left out:
>
> > *"**Each 1 of surprise equals 1 segment (six seconds) of time lost to the
> > surprised party**, and during the lost time the surprising party can freely
> > act to escape or attack or whatever. **If both parties are surprised, then
> > the effect is negated or reduced:** [the difference table]"* — **DMG p. 61**
>
> | situation | lost segments |
> |---|---|
> | **ONE side surprised** | **the surprised side's OWN DIE ROLL.** A 1 costs one segment, a 2 costs two |
> | **BOTH sides surprised** | **the DIFFERENCE**, per the table above |
>
> **So a lower roll is BETTER for the surprised side**, which is counter-intuitive
> and is why it must be written down. Day 95, expedition 11, at the smithy door:
> the party rolled 6 against a 1-5 range and was not surprised; the huge spiders
> rolled **1** and lost **one** segment. Had they rolled 2 they would have lost
> two, and two segments is two full rounds of attacks against a helpless enemy.
>
> *This is the same failure this file already warns about in its own header — **A
> PARAPHRASE LOSES CONDITIONS** — committed by the file itself. The difference
> table is the exception; the sentence above it is the rule.*

> *"If surprise is indicated for both parties concerned, the party which has
> lesser surprise subtracts its result from the result of the greater to find the
> number of segments the latter are inactive. Nonetheless, it is possible for
> both parties to be surprised **equally** — with surprise thus having no
> effect."* — DMG p. 61

**"Both surprised means nobody is surprised" is the EQUAL case only.** It is the
difference-of-0 row above. Day 70's troglodyte was party 2 vs trog 2 and
`rolls.tsv` records it as *"MUTUAL, cancels"* — correct, and the same rule that
gives 2 lost segments on a 4 against a 2.

### What a segment buys

> *"the surprising party will be able to attempt telling blows during each
> segment of surprise **as if the segment were an entire round!** That is, a
> fighter able to attack twice during a normal round of combat will be able to do
> so twice during each surprise segment… Even if distance prevents striking with
> weapons, the discharge of arrows, bolts or hand-hurled weapons is permissible at
> **three times the normal rate** providing the weapon/missiles are ready."*
> — **DMG p. 62**

### ⚠ WHO THAT PARAGRAPH IS ABOUT — read the subject before quoting it

**BOTH of those benefits belong to the SURPRISING side ONLY, and the DMG states
the premise in the same sentence: *"BECAUSE THE PARTY SURPRISED IS (RELATIVELY)
INACTIVE, the surprising party will be able to…"*.** They exist because the
targets are helpless.

So **two lost segments is two full rounds of attacks for the side that
surprised**, and missiles already in hand fire at **3x** — *for that side*.

**NEITHER APPLIES TO SOMEBODY WHO MERELY IS NOT SURPRISED.** A character who
negates his own segments on dexterity is **not frozen and not a free target, and
that is the whole of it**. His opponents are not inactive, so nothing multiplies:
he acts at his **normal rate of fire, once**.

> *Caught by the player 2026-09-13, day 79, within the hour of this section
> being written — the DM told him Tristle's bow fired at 3x because the rule had
> been cached WITHOUT ITS SUBJECT. That is the same defect, in the same file,
> that this whole section was written to fix: A PARAPHRASE LOSES CONDITIONS.
> The condition here is six words long and it is the first six words.*

Possible in a surprise segment: avoiding, parleying, waiting, **missile
discharge**, setting weapons against a charge, and **1-segment spells** — which is
most 1st-level magic-user spells. Longer spells may only be *begun*.

### Dexterity, per individual (DMG p. 62)

> *"if there is a dexterity penalty, the individual will suffer that many
> additional segments of time in a surprised state. On the other hand, if the
> dexterity bonus applies the individual negates that many segments of surprise
> **as far as the individual only is concerned**."*

Use the **Reaction/Attacking** column of `rules/abilities.md`. It never creates
surprise in the other side, and it never touches anybody else's count.

**A negated segment is not a won initiative.** The DMG grants *the non-surprised
side* the segments of initiative; dexterity only removes one individual's
inactivity. That person acts **within** the same segments and is not a free
target — he does not act **before** the surprising side, and there is no
initiative roll inside a surprise segment.

**This party's non-zero adjustments are TRISTLE (DEX 18, +3) and DELLIE (DEX 4,
−2), and nobody else.** Dave 10, Torsat 11, Yrtone 12, Blartho 12, Ista 13,
Frython 14 and Hask 11 all sit in the 0 band.

### What does NOT end a surprise once it is rolled

**Nothing the surprised side's own allies do.** A shout, a warning, a torch
thrown — none of it returns a segment to anybody.

> *"While each possible cause of surprise could be detailed, with a matrix and
> **factors of time for recovery from the condition** calculated to a nicety, the
> overall result would not materially add to the game — in fact, the undue
> complication would detract from the smooth flow of play."* — **DMG p. 62**

Gygax considered modelling recovery and declined. And the roll already contains
the thing a warning would address:

> *"The second factor represented in surprise is **morale**… Panic or fear
> reactions to the situation take their toll. Again, this is all **subsumed in
> the single surprise roll**."* — DMG p. 62

Set against *"during the surprise segment or segments, the surprised party is
**unable to react in any way**"*, a shout is by definition something they cannot
react to.

**Do not confuse this with the noise rule.** *"Noise can negate surprise
considerations"* sits beside *"prior detection"* and *"light can spoil the chance
of surprise"* — those decide whether surprise is **rolled at all**. They do not
reach backwards into a roll already made. *(Asked by the player 2026-09-13, day
79, with six of his eight frozen and the one free character holding a bow he did
not want to fire into their backs.)*

### Encounter distance

Surprise **shortens** it: subtract the surprise value from normal distance
(DMG p. 49). Underground the binding limit is usually light —

> *"A light source reliance limits the encounter distance to twice the normal
> vision radius of the source (2 x radius of the light source)."* — **DMG p. 62**

A 30-ft lantern therefore caps it at **60 ft**, before surprise takes its bite.

### What negates surprise outright

> *"Prior detection negates the possibility of surprise… Noise can negate
> surprise considerations, whether the sound is the normal progress of the party
> or the effect of a fruitless attempt to open a door. **Light can spoil the
> chance of surprise.**"* — DMG p. 62

And: *"surprise can be and often is unilateral… merely roll for the party which
is subject to the condition and do not roll for the other."*

## Time

- 1 turn = 10 melee rounds. 1 melee round = 10 segments.
- Casting time in segments determines initiative order within a round.

## Combat sequence (Gygaxian rigor)

1. Determine surprise (d6, 1–2 surprised unless modified)
2. Roll initiative (d6 per side, **high wins**)
3. Apply casting times / weapon speed factors within the round
4. Resolve attacks, then damage, then morale checks if triggered

*Weapon speed factors and the full DMG initiative procedure are not yet transcribed —
pull from DMG before the first real melee.*

## Disease (DMG p. 14)

Rolled in three steps, then adjusted:

1. **d100** on the DISEASE (OR DISORDER) TABLE for the **area of body affected**
2. **d8** for **occurrence** — acute (a single attack) or chronic (recurs)
3. **d8** for **severity** — mild, severe or terminal

Each area of the body has its own bands for both, so the same d8 means different
things depending on step 1.

**Both the occurrence and the severity roll take the same Constitution adjustment:**

| Condition | Adjustment |
|---|---|
| Constitution under 3 | +2 |
| Constitution 3-5 | +1 |
| already has a chronic disease or disorder | +1 |
| severe parasitic infestation | +1 |
| under 25% of normal hit points | +1 |
| Constitution 10-12 | -1 |
| Constitution 13-15 | -2 |
| Constitution 16-17 | -3 |
| Constitution 18 | -4 |

*source: **DMG p. 14**, CHARACTER AGE, AGING, DISEASE & DEATH, 200 dpi page
render 2026-08-28.*

**A die score of 0 or less on either roll means the disease is not contracted at
all.** A healthy character shrugs most of them off before they start.

### What each severity does

| Severity | Effect |
|---|---|
| **Mild** | Cannot perform strenuous activity, must rest. **1-3 weeks.** |
| **Severe** | Hit points to **50% of normal**, totally disabled **1-2 weeks**, then a further 1-2 weeks in the mild state while recovering. |
| **Terminal** | Death, or loss of the body part or function, in **1-12 days** unless the entry says otherwise. |

*source: **DMG p. 14**, the SEVERITY paragraphs, 200 dpi page render 2026-08-28.*

**Incubation is NOT given by this table.** DM ruling 2026-08-28: **1-4 days**
before symptoms show. Recorded so it is the same next time.

**Cure disease is a 3rd-level cleric spell.** Neither of this party's clerics is
anywhere near it, so a disease runs its course or is treated by somebody in town.

## Encounter reactions (DMG p. 63)

**Any intelligent creature which can be conversed with will react in some way to
the character that is speaking.** Roll percentile dice, adjust for the speaker's
**Charisma** and any applicable loyalty adjustment *"as if the creature were a
henchman of the character speaking"*, and read:

| Adjusted d100 | Reaction |
|---|---|
| 01 or less - 05 | Violently hostile, immediate attack* |
| 06 - 25 | Hostile, immediate action* |
| 26 - 45 | Uncertain, but 55% prone toward negative |
| 46 - 55 | Neutral - uninterested - uncertain |
| 56 - 75 | Uncertain, but 55% prone toward positive |
| 76 - 95 | Friendly, immediate action |
| 96 - 00 or greater | Enthusiastically friendly, immediate acceptance |

*source: **DMG p. 63**, ENCOUNTER REACTIONS, text layer read 2026-08-29.*

\* *"Or morale check if appropriate."*

### ⚠⚠ WHAT THIS TABLE IS FOR — AND IT IS **NOT** ONGOING CONVERSATION

**Player-caught 2026-09-08, and the page settles it. THIS IS A COMBAT-CHAPTER
FIRST-CONTACT MECHANIC.**

**The running heads on DMG p. 63 read `COMBAT (ENCOUNTER REACTIONS)` and
`COMBAT (MISSILE DISCHARGE)`.** The table's neighbours on that page, in order, are:

> initiative · ties · inflicting damage · **ENCOUNTER REACTIONS** · *Avoiding*
> (fleeing and pursuit) · *Parleying* · *Awaiting Action* · **MISSILE DISCHARGE**

**That is one procedure for what happens when two parties meet and it might become a
fight.** *Parleying* says so outright: *"**Upon encountering another party**, the
party with initiative can always elect to attempt some form of communication."*

**And the footnote clinches it.** The two hostile results carry `*` = *"Or morale
check if appropriate."* **A morale check belongs to the moment of confrontation. You
do not morale-check a shopkeeper.**

> ### THE RULE FOR THIS CAMPAIGN — DICE FOR FACTS, JUDGMENT FOR FEELINGS, REACTIONS FOR STRANGERS
>
> | situation | what to do |
> |---|---|
> | **first meeting with a new NPC** | **roll p. 63.** Correct for Rud, Pell, Trebb, Ossery, Dill, Rowe, Lyde, Father Doule |
> | **an ESTABLISHED NPC in conversation** | **DO NOT ROLL.** They have a standing disposition; it moves for **reasons that are on the record**, and the DM states the reason |
> | **a “step-change”** | **NO. The DM invented this exception on 2026-09-08 and used it four times inside the hour; it is struck. See `CHECKLIST.md`** |
> | **an unknown FACT** | **always roll, on a table declared before the die.** This is the honest use and it has carried the campaign: the vial's contents, Dill's history, the loom's width, whether Marchford owned a font |
> | **loyalty** | **DMG pp. 36-37, when the books call for it** — danger, temptation, hardship. **Never conversationally** |
>
> **WHY IT MATTERS:** rolled per-conversation, Cuddy ran 102 → 6 → 53 → 5 → 71 → 81
> → 25 and Wend ran 101 → 60 → 57 → 26 → 46 → 12 → 41 → 37 → 88 → 46. **That is not
> a person. That is a d100 with a name on it.**

### THE HALF OF THAT RULE THE DM IGNORED FOR SIXTY GAME DAYS

*(This section stands, and is now SECONDARY: when a reaction roll IS called for, it
still gets the modifiers below. But most of the rolls that prompted this section
should never have been made at all.)*

**Read the sentence above again: adjust for Charisma AND "any applicable loyalty
adjustment."** `rules/abilities.md` established that **nobody in this party has a
Charisma reaction adjustment** — and the DM took that to mean reaction rolls here
are unmodified. **They are not.** The loyalty half is a large, cumulative,
book-supported bonus and it has never once been applied.

**Player-caught 2026-09-08:** *"I don't think it's realistic that they would have
such wild shifts in their response to us."* **Correct, and the books agree.**

## Loyalty modifiers — SPECIAL CONSIDERATIONS (DMG p. 37)

**How the party has actually TREATED people. This is the anti-swing mechanism.**

| Special consideration | Modifier |
|---|---|
| killed faithful henchman or hireling in front of witness(es) | **−40%** |
| tortured faithful henchman or hireling in front of witness(es) | **−30%** |
| reputed to have slain faithful henchmen or hirelings, or actually left them to die | **−20%** |
| foresworn, oath breaker or deserter | **−15%** |
| rumored to have tortured faithful henchmen or hirelings | **−10%** |
| discharged faithful henchmen or hirelings without cause | **−5%** |
| **given a choice gift or bonus within the last two months (hireling) or three months (henchman)** | **+5%** |
| **risked life for within the last six months (hireling) or one year (henchman)** | **+10%** |
| **ransomed or rescued within one year** | **+15%** |
| **saved life directly or personally** | **+25%** |
| **uses and diminishes his or her own magic to benefit the NPC (including use of spells, especially cures)** | **+25%** |
| **returned henchman or hireling to normal state from a death-like state, had raised or resurrected** | **+50%** |

*source: **DMG p. 37**, HENCHMEN (LOYALTY), Special Considerations, 170 dpi page render 2026-09-08.*

> **"Apply only ONE penalty and ONE bonus maximum, whichever of either category is
> the higher."** — DMG p. 37. **It is bounded. It does not stack into nonsense.**

## Alignment of the liege (DMG p. 37)

| Alignment | Modifier |
|---|---|
| lawful good | **+15%** |
| lawful neutral | **+10%** |
| lawful evil | +5% |
| neutral good | 0% |
| neutral | 0% |
| chaotic good | −5% |
| chaotic neutral | −10% |
| neutral evil | −15% |
| chaotic evil | −20% |

*source: **DMG p. 37**, HENCHMEN (LOYALTY), Alignment of Liege, 170 dpi page render 2026-09-08.*

> **⚠ NO CHARACTER IN THIS CAMPAIGN HAS A RECORDED ALIGNMENT.** `party_roster.md`
> has ability scores, race and class and no alignment line. **This is worth up to
> +15% on every reaction roll in the game and it cannot be applied until the player
> states it** (alignment is a player declaration, PHB p. 33).

## Situation modifiers (DMG p. 37) — these are for the moment of danger

| | |
|---|---|
| liege dead, or surrounded and outnumbered | −25% |
| liege *hors de combat* | −15% |
| each henchman dead or *hors de combat* | −5% |
| each hit die or level dead, friendly | −3% |
| each hit die or level alive, enemy | −1% |
| each hit die or level dead, enemy | +1% |
| each hit die or level alive, friendly | +2% |
| each henchman present, in sight, alive | +5% |
| **liege present, in sight, alive** | **+15%** |

*source: **DMG p. 37**, HENCHMEN (LOYALTY), Situation Modifiers, 170 dpi page render 2026-09-08.*

> **"When all modifying factors have been checked, adjust the base loyalty and roll
> percentile dice as noted above."** — DMG p. 37
>
> **HOW THIS CAMPAIGN APPLIES IT.** The Special Considerations and Alignment tables
> are a **STANDING modifier per NPC**, computed once and carried in
> `campaign/npcs.md`; the Situation modifiers are **combat-time only** and are not
> part of a shopkeeper's reaction. **Book-strict for hirelings and henchmen. For
> independent townspeople who are neither, extending the +5/+10/+15 tiers on a
> record of fair dealing is a DM CALL and is marked as one wherever it is used.**


**This applies to MEN and other intelligent creatures the party talks to** —
bandits, gnomes, the berserkers had they been hailed. It does not apply to
animals or the non-intelligent. **Roll it when the party opens with words**, and
roll it BEFORE deciding what the creature does; a DM who decides first and rolls
second is not running a reaction table.

### Avoiding an encounter, from the same page

- Flight is **always possible if the other party is surprised**.
- Flight is **never possible when the opponent is in striking range**.
- **A party can always flee if it wins the first initiative.**


## Missile fire — cover and concealment (DMG p. 64)

**The book's "+N" is an IMPROVEMENT to the target's armour class, and 1e armour
class DESCENDS — so you SUBTRACT it.** 50% concealment is "+2", which takes an
AC 7 creature to **AC 5**: two points *harder* to hit. Read the worked right-hand
column rather than doing it in your head.

| Target has about | Book's "AC bonus" | Applied to a base AC 7 target |
|---|---|---|
| 25% cover | +2 | AC 5 |
| 50% cover | +4 | AC 3 |
| 75% cover | +7 | AC 0 |
| 90% cover | +10 | AC −3 |
| 25% concealment | +1 | AC 6 |
| **50% concealment** | **+2** | **AC 5** |
| 75% concealment | +3 | AC 4 |
| 90% concealment | +4 | AC 3 |

*source: **DMG p. 64**, "Missile Fire Cover And Concealment Adjustments", 200 dpi
page render 2026-08-30. The right-hand column is worked, not printed.*

### GOT THIS BACKWARDS ONCE — 2026-08-30, player-caught

I read "+2" as *add 2 to the AC number* and shot at three concealed kobolds as
**AC 9** instead of **AC 5**. That is not a rounding error: it turned a penalty
for shooting into the dark into a **bonus**, and made concealment help the
archer.

**The tell is the phrase "armor class bonus."** Every AC bonus in 1e — a ring of
protection +1, a shield, a Dexterity defensive adjustment — moves the number
**down**, because down is better. Nothing that protects you ever raises your AC
number. If an adjustment makes a target easier to hit, it has been applied the
wrong way round.

*(The volley itself stood: Tristle needed 12 against the correct AC 5 and rolled
14 and 19. Torsat needed 15 and rolled 6 and 10. Same outcome, by luck.)*

**Cover is hard substances which protect; concealment is soft substances which
screen.** Shadow, smoke, brush and mist are concealment, and concealment is worth
far less — 90% concealment is only +4 where 90% cover is +10. An arrow that cannot
see you can still find you.

> *"25% is cover or concealment to the knees, or part of the left or right side of
> the body screened; it might also be a target which is seen for only
> three-quarters of a round… 50% cover or concealment equals protection or
> screening to the waist, half of one side of the body, or being seen for only half
> the round."* — DMG p. 64

**Standing ruling for this campaign — shooting into the dark.** A target at the
ragged edge of the lantern's reach, or in a side passage the light only clips, is
**50% concealment: two points BETTER AC**. This comes up constantly in a dungeon
lit by one lamp and it should be the same number every time.

**Darkness is concealment, never cover** — it stops nothing. Something behind an
actual stone corner has cover, and the numbers are two to five times harsher.

### Dexterity and missile initiative, from the same page

> *"The Dexterity Attacking Adjustment is for missile firing considerations when
> initiative is considered. It adjusts the initiative die roll for the concerned
> individual only. Thus, it may well allow the concerned individual to discharge a
> missile prior to the opponent's attack even though the opponent has gained the
> initiative."* — DMG p. 64

So **Tristle's +3 applies twice**: once to his initiative die as an individual, and
once as the to-hit adjustment. A high-DEX archer shoots early even when his side
loses the round.

## Charging (DMG p. 66)

| | |
|---|---|
| Charger's to-hit | **+2** |
| **Charger's own AC** | **one worse** while charging — *"an AC 3 creature becomes AC 4"* |
| vs AC 10 creatures | **no AC penalty to the charger** |
| Initiative at the end of a charge | **NOT checked.** The opponent with the **longer weapon or reach attacks first** |
| Frequency | **one charge move per turn** — nine rounds before another |

*source: **DMG p. 66**, COMBAT (FURTHER ACTIONS), text layer read 2026-08-31 and
cross-checked against the surrounding block.*

**The AC penalty is the price and it is easy to forget.** A charging Dave is AC 3,
not 2. It costs nothing against a surprised opponent and it costs a great deal
against a set spear.

**"The opponent with the longer weapon attacks first" is the real danger.** A
charge into a braced polearm or spear means taking the hit before delivering one,
with no initiative roll to save you. Charging a **set** weapon is how a
first-level fighter dies.

## Breaking off from melee — the free attack (DMG p. 70)

> *"At such time as any creature decides, it can break off the engagement and flee
> the melee. To do so, however, **allows the opponent a free attack or attack
> routine. This attack is calculated as if it were a rear attack upon a stunned
> opponent.** When this attack is completed, the retiring/fleeing party may move
> away at full movement rate, and unless the opponent pursues and is able to move
> at a higher rate of speed, the melee is ended and the situation becomes one of
> encounter avoidance."*

*source: **DMG p. 70**, "Breaking Off From Melee", text layer read 2026-08-31.*

| | |
|---|---|
| Rear attack | **+2** |
| Stunned / prone / motionless | **+4** |
| **Free attack on a creature breaking off** | **+6 total**, shield negated, DEX negated |

*source: the two modifiers are the DMG p.70 flank-and-rear table above; this rule
invokes both by name.*

**There is no "attack of opportunity" in 1e.** This is the rule people are
reaching for and it is far more generous — a full attack **routine**, not one
swing, at +6.

**It costs the fleer nothing else.** After the free attack it moves away at **full**
rate, and unless somebody is genuinely faster, the melee is simply over. **Armoured
characters cannot chase an unarmoured one.**


## Clerics may not use edged or pointed weapons

> *"All clerics have certain holy symbols which aid them and give power to their
> spells. **All are likewise forbidden to use edged and/or pointed weapons which
> shed blood.** All clerics have their own spells, bestowed upon them by their
> deity for correct and diligent prayers and deeds."*

And on magic items, same page:

> *"Clerics can employ a fair number of magic items including most potions;
> clerical and 'protection' scrolls; most rings; some wands, rods, and staves;
> many other magical items; and **all of the non-edged, non-pointed magical
> weaponry.**"*

**This is a prohibition, not a proficiency penalty.** There is no to-hit modifier
to apply — a cleric simply does not carry the thing.

| | |
|---|---|
| **YRTONE and BLARTHO may NOT have** | dagger, sword, spear, arrow, bolt, javelin, hand axe — anything that cuts or pierces — **and MORNING STAR** |
| **They may have** | **footman's flail** (carried), **sling** (carried), club, mace, quarterstaff, war hammer |

> ### ⚠ A MORNING STAR IS NOT A MACE. Added 2026-09-19, player-caught.
>
> The gnoll on day 99 dropped one and I offered it to the clerics as *"blunt,
> which means a cleric may legally carry it."* **Wrong.** A morning star is a
> **spiked** head — the table above even groups it with the Godentag and the
> Holy Water Sprinkler, both spiked — and a spike pierces and sheds blood.
>
> **The list of permitted weapons in the row above was already complete and
> already excluded it.** The error was reading the weapon's silhouette instead of
> reading this file. A mace and a war hammer are permitted because they are
> *smooth* striking heads; the spikes are the whole difference.
>
> **The permitted list is a WHITELIST. If a weapon is not on it, the answer is
> no** — do not reason about whether it looks blunt.

*source: **PHB p. 20**, THE CLERIC — verified from a 170 dpi page render, printed
footer reads 20.*

*(Caught 2026-09-02 when the party tried to buy a dagger for every character.
It is a **multi-class exemption only**: PHB p. 32, "Cleric combinations (with
fighter types) may use edged…" — neither of this party's clerics is multi-class.)*

## Changing weapons in melee — the standing ruling

**Set expedition 6 and applied twice.** Swapping weapons costs the round; you
switch **or** you attack.

| | |
|---|---|
| **Two-handed missile weapon → sword and shield** *(a short bow slung, a shield off the back)* | **THE WHOLE ROUND.** No attack |
| **Sling → flail, mace or the like** | **FREE.** A sling is a strip of leather you let fall, and the weapon is on the belt with the shield already on the arm. **Attack normally** |
| Sheathed weapon → another sheathed weapon | the round |

*source: **NOT A BOOK RULE.** Neither the PHB nor the DMG prices a weapon change.
This is a DM ruling, set 2026-09-04, and the sling exemption was added the same
day for consistency rather than invented mid-round. Recorded so it is applied
the same way every time.*

**The consequence the party has paid twice:** a missile-forward marching order
buys you a free volley at range and costs you a full round the moment anything
reaches you. That is a real trade, not a gotcha — but it must be charged the
same way each time.

## How deep a rank formation actually stands

**Player's argument, 2026-09-04, and it is correct:** if the DMG allows **three
abreast in a 10-ft passage at 3.5 ft per character** (p. 97), then the same 3.5
ft is the sensible front-to-back spacing. **Three ranks therefore stand inside
about 10-11 feet, not 30.**

| | |
|---|---|
| **Width** per character | **3.5 ft** — DMG p. 97 |
| **Depth** per rank | **~3.5 ft** — same figure, DM ruling by symmetry |
| A 3-rank, 8-person column | **about 10-11 ft front to back**: one 10-ft square and a little |

*source: **DMG p. 97** for the 3.5 ft per character; the DEPTH figure is a DM
ruling by symmetry, set 2026-09-04 after the player pointed out the
inconsistency. Not a book table.*

**What this changes, and it is a lot:**

- **A touch spell from rank 3 reaches rank 1.** Cure light wounds does not need a
  round of movement first; rank 2 makes room. *(I had been treating rank 3 as 20
  ft back, which is wrong and had already cost the party a round of healing.)*
- **Area spells centred on the enemy will engulf the WHOLE column**, not just the
  front rank. A 3" sleep circle is 30 ft across and the party is 11 ft deep.
- **Rank 2's spears reach**, which was already the rule, and now the geometry
  agrees with it.

## Zero hit points — and the part that is always forgotten

> *"When any creature is brought to 0 hit points (optionally as low as −3 if from
> the same blow which brought the total to 0), it is unconscious. In each of the
> next succeeding rounds 1 additional (negative) point will be lost until −10 is
> reached and the creature dies… **it ceases immediately on any round a friendly
> creature administers aid to the unconscious one. Aid consists of binding
> wounds, starting respiration, administering a draught… or otherwise doing
> whatever is necessary to restore life.**"*
>
> *"**Any character brought to 0 (or fewer) hit points and then revived will
> remain in a coma for 1-6 turns.** Thereafter, he or she must **rest for a full
> week, minimum.** He or she will be incapable of any activity other than that
> necessary to move slowly to a place of rest and eat and sleep when there. The
> character **cannot attack, defend, cast spells, use magic devices, carry
> burdens, run**, study, research, or do anything else. **This is true even if
> cure spells and/or healing potions are given to him or her**, although if a
> *heal* spell is bestowed the prohibition no longer applies."*
>
> *"If any creature reaches a state of −6 or greater negative points before being
> revived, this could indicate **scarring or the loss of some member**, if you so
> choose."*
>
> — **DMG p. 82**, ZERO HIT POINTS

| | |
|---|---|
| **Bleeding** | 1/round to −10. **Stops the instant anyone binds wounds** — no roll, no check |
| **Coma** | **1-6 TURNS**, always, once revived |
| **Then** | **A WEEK, MINIMUM.** No attacking, no defending, **no spellcasting**, no carrying, no running |
| **A cure spell does NOT lift it** | only *heal* does, which is 6th level and out of reach |
| **−6 or worse** | DM may rule scarring or the loss of a limb |

*source: **DMG p. 82**, ZERO HIT POINTS, read from the page 2026-09-04.*

**THE TRAP IN THIS RULE:** a *cure light wounds* puts hit points back and looks
like it has fixed the problem. **It has not.** The character is still comatose,
then still an invalid for a week. A cleric who drops to 0 is out of the
expedition AND cannot cast on the way home.

### ⛔ THE HOUSE RULE IS RETIRED — RAW GOVERNS FROM DAY 79

**Retired by the player 2026-09-13, day 79**, with Torsat lying at −1 in the
corridor at (24,37):

> *"I think we ruled that going forward we would stick with the official rule,
> that 0 or less puts you out of action for a week."*

**THE LINE IS NOW AT ZERO OR FEWER, AS THE DMG WRITES IT.** There is no longer a
cure-lifts-it exception at exactly 0.

| where they stopped | outcome |
|---|---|
| **0 OR FEWER**, however revived | **COMA 1-6 TURNS, THEN A WEEK MINIMUM.** No attacking, no defending, no casting, no carrying, no running |
| **A cure spell or potion** | **restores the hit points and NOTHING ELSE.** It does not lift the coma or the week |
| ***heal*** | lifts the prohibition — 6th level, and out of this party's reach |
| **−6 or worse** | DM may rule scarring or the loss of a limb |

*source: **DMG p. 82**, ZERO HIT POINTS, quoted in full above. RAW.*

**What this changes in practice:** it used to be that a cure reaching somebody at
**exactly** zero bought them back whole, so the cleric's decision was about
SPEED. That is gone. **A cure now buys a life and nothing more, at any number.**
Getting there fast still matters — but only because of the bleeding, which is a
separate clock.

**The retired table is kept below because citations point at it**, and because
the campaign ran on it for sixty-odd days. It is **NOT authoritative** and must
not be applied to anything after day 79.

> #### RETIRED — do not apply. Ran 2026-09-05 to 2026-09-13.
>
> | where they stopped | outcome |
> |---|---|
> | ~~**EXACTLY 0**, then given a cure spell or potion~~ | ~~**BACK IN ACTION.** No coma, no week~~ |
> | ~~**−1 OR LOWER**~~ | ~~out for a week even with a cure~~ |
> | ~~bandaged only~~ | ~~as −1 or lower~~ |

**The past stands as it was played.** Ista and Blartho's area-36 pit-trap
revivals, and every ruling made under the old table between day 39 and day 79,
are correct as adjudicated — see the corollary immediately below, which is the
rule that says so and which was itself written after I broke it.

### Corollary: rules corrections are prospective

**The table had been running "0 hit points + cure light wounds = back in action"
for the whole campaign, and I had never corrected it.** On 2026-09-04 I found the
DMG paragraph mid-scene and applied it retroactively to a player who had *just
spent a cure light wounds on the strength of the old rule.*

**That is the thing CHECKLIST section 3 exists to prevent** — *would they have
given that order if they had known?* The player would have saved the spell.

**Ruling: the entire area-36 pit-trap incident runs under the OLD rule.** Ista and
Blartho are both revived to full function, no coma, no week. **Blartho went into
that pool under the old rule too**, and splitting the incident would punish him
for the order the dice happened to fall in.

**From the next character to reach 0, the DMG paragraph above governs**, and it
has been said out loud in advance. A rules correction is prospective or it is a
retcon.

## Natural healing — 1 hit point per DAY of rest

| | |
|---|---|
| **Per 24 hours of rest** | **1 hit point** |
| A first week of rest | about **7** |
| **A second week** | 7 **plus the Constitution bonus** — the DMG's worked example is a fighter with CON 18 recovering **11** in the second week |
| **Four weeks continuous** | restores any character to full, whatever their total |

*source: **DMG p. 82**, and the way this table has played it all campaign.*

**What this means in a dungeon: sleeping does not heal you.** A night's rest is
for **spells** and for the cold; it is worth **nothing** in hit points. A party at
1 and 2 hit points that beds down underground wakes up at 1 and 2 hit points.

**The only thing that puts points back inside an expedition is a cure spell.**


## Turning undead — the matrix, and the two things the books do not say

### III. MATRIX FOR CLERICS AFFECTING UNDEAD (DMG p. 75)

| Type of Undead | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9-13 | 14+ |
|---|---|---|---|---|---|---|---|---|---|---|
| **Skeleton** | **10** | 7 | 4 | T | T | D | D | D* | D* | D* |
| Zombie | 13 | 10 | 7 | T | T | D | D | D | D* | D* |
| Ghoul | 16 | 13 | 10 | 4 | T | T | D | D | D | D* |
| Shadow | 19 | 16 | 13 | 7 | 4 | T | T | D | D | D* |
| Wight | 20 | 19 | 16 | 10 | 7 | 4 | T | T | D | D |
| Ghast | - | 20 | 19 | 13 | 10 | 7 | 4 | T | T | D |
| Wraith | - | - | 20 | 16 | 13 | 10 | 7 | 4 | T | D |
| Mummy | - | - | - | 20 | 16 | 13 | 10 | 7 | 4 | T |
| Spectre | - | - | - | - | 20 | 16 | 13 | 10 | 7 | 4 |
| Vampire | - | - | - | - | - | 20 | 16 | 13 | 10 | 4 |
| Ghost | - | - | - | - | - | - | 20 | 16 | 13 | 7 |
| Lich | - | - | - | - | - | - | - | 19 | 16 | 10 |
| Special | - | - | - | - | - | - | - | 20 | 19 | 13 |

*source: **DMG p. 75**, III. MATRIX FOR CLERICS AFFECTING UNDEAD, 300 dpi page render 2026-09-06.*

**A number is a d20 score to beat. `T` = turned automatically. `D` = destroyed
(dispelled) automatically.** † *Paladins turn as a cleric two levels below.*

> **PARSER TRAP, hit on this very table 2026-09-06.** `rules.py` closes a table at
> the first line that does not begin with `*`, so a **wrapped** bold paragraph
> whose second line starts with anything else eats the association and the
> `*source:*` line below it is never attached. **Put the source line immediately
> after the table, before any prose.** `test_every_combat_table_is_cited` caught
> it, which is the guard working.

**A 1st-level cleric needs 10 on d20 against skeletons.** This party has three
1st-level clerics, so three attempts.

### The procedure, in the book's own words (DMG p. 65)

> *"this function may be attempted **only once by each cleric.** Of course, if
> there are two, both may attempt the function, each trying once… **Any failure
> to turn undead disallows a further attempt by the same cleric.** Turning can
> occur at the same time as missile discharge, magical device attacks, and/or
> spell casting. **It also is subject to initiative determination.**"*
>
> *"**Mindless undead, skeletons and zombies, cannot be considered**"* — for the
> mixed-group rule only. Skeletons are on the table and **are turnable**;
> "attack until destroyed" is a MORALE fact, not a turning exemption.

### ⚠ TWO GAPS — these are DM CALLS, not book rules

**Neither the PHB nor the DMG states how many undead a success affects, or for
how long.** Searched both, 2026-09-06. DMG p. 65's *"to the maximum number
indicated by the dice roll or otherwise indicated by the rules"* points at a rule
that is not in either book.

| | DM call, set 2026-09-06 |
|---|---|
| **How many** | **2d6 of that type.** The near-universal convention, and the table is organised *by type* rather than per creature, which implies a group effect |
| **For how long** | **3d4 rounds.** They turn away and will not voluntarily approach the turning cleric while it lasts |
| **What breaks it** | the cleric attacking them, or being cut off from retreat. **Turned undead in a dead-end room have nowhere to go** — they cower rather than flee |

*source: **NOT A BOOK RULE.** Recorded so it is the same every time. If a printed
1e figure is ever found, it wins.*
