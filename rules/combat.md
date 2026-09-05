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
| **YRTONE and BLARTHO may NOT have** | dagger, sword, spear, arrow, bolt, javelin, hand axe — anything that cuts or pierces |
| **They may have** | **footman's flail** (carried), **sling** (carried), club, mace, quarterstaff, war hammer |

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

### THE HOUSE RULE, confirmed by the player 2026-09-05 — a CURE lifts it

**The DMG paragraph above is played in full, with ONE amendment this table has
used all campaign:**

**THE LINE IS AT ZERO. It is the number they stopped on, not how they were revived.**

| where they stopped | outcome |
|---|---|
| **EXACTLY 0**, then given a cure spell or potion | **BACK IN ACTION.** No coma, no week. Normal |
| **−1 OR LOWER** | **OUT FOR A WEEK, EVEN WITH A CURE.** Coma 1-6 turns, then shuffling to a place of rest and nothing else — no attacking, no defending, no casting, no carrying, no running |
| Any of the above, bandaged only | as −1 or lower: the week applies |

*source: **HOUSE RULE, not RAW.** DMG p. 82 applies the coma and the week to
anyone brought to 0 **or fewer**, and says explicitly that a cure does not lift
it. This table draws the line at **exactly zero** instead. Confirmed by the
player 2026-09-05 as how it has been played all campaign.*

**That is a deliberate departure from RAW**, which says the prohibition applies
*"even if cure spells and/or healing potions are given"* and lifts only for
*heal*. **This table lifts it for a cure.** It is why a party carries clerics.

**The practical shape of it, and it is brutal:** a cure is only a rescue if it
reaches them **at exactly zero**. One point further down and the spell buys their
life and nothing else — they are still carried out and still gone for a week,
which for a cleric means gone for the next expedition too.

**So the cleric's decision is about SPEED, not about spell economy.** Getting a
cure into somebody the round they drop is worth far more than the hit points on
the die.

*(I got this wrong twice in one scene on 2026-09-04/05 — first applying RAW to a
cure the player had already spent, then forgetting the week applied to the
bandaged one. Both halves are above.)*

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

