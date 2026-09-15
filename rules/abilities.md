# Ability score adjustments — AD&D 1e

Only the tables that bear on play in this campaign. Parsed by `tools/rules.py`.

## Dexterity

| Score | Reaction/Attacking | Defensive |
|---|---|---|
| 3 | -3 | +4 |
| 4 | -2 | +3 |
| 5 | -1 | +2 |
| 6 | 0 | +1 |
| 7 | 0 | 0 |
| 8 | 0 | 0 |
| 9 | 0 | 0 |
| 10 | 0 | 0 |
| 11 | 0 | 0 |
| 12 | 0 | 0 |
| 13 | 0 | 0 |
| 14 | 0 | 0 |
| 15 | 0 | -1 |
| 16 | +1 | -2 |
| 17 | +2 | -3 |
| 18 | +3 | -4 |

*source: **PHB p. 11**, DEXTERITY TABLE I, 200 dpi page render 2026-08-25.*

**Reaction/Attacking Adjustment** applies to *"both surprise situations and
missile combat attacks"* — the PHB's own wording. It is a **to-hit bonus on
every missile attack**, and it is separate from any racial weapon bonus.

**Defensive Adjustment** *"subtracts from the armor class of the character"* —
a bonus improves AC. Tristle's leather (AC 8) with DEX 18 (−4) is **AC 4**.

*This table does NOT modify melee to-hit.* Melee to-hit and damage come from
Strength; a high-DEX character with an ordinary Strength swings at +0.

## Intelligence — ABILITY FOR MAGIC-USERS (PHB p. 10, TABLE II)

| Score | Chance to know each listed spell | Min spells/level | Max spells/level |
|---|---|---|---|
| 9 | 35% | 4 | 6 |
| 10-12 | 45% | 5 | 7 |
| 13-14 | 55% | 6 | 9 |
| 15-16 | 65% | 7 | 11 |
| **17** | **75%** | **8** | **14** |
| 18 | 85% | 9 | 18 |
| 19 or more | 95% | 10 | All |

*source: **PHB p. 10**, INTELLIGENCE TABLE II, read from a 200 dpi page render
2026-09-15. **THE TEXT LAYER DROPS ROWS 15-16, 17 AND 18 ENTIRELY** — it runs
13-14 straight to 19 — which is exactly the row FRYTHON needs. Transcribed from
the render for that reason.*

**FRYTHON IS INT 17.** 75%, minimum 8, maximum 14 first-level spells.

> ### ⚠ "EACH SPELL MAY BE CHECKED ONLY ONCE"
>
> *"Percentile dice are rolled, and if the number generated is equal to or less
> than the percentage chance shown, then the character can learn and thus know
> that spell… **Each spell may be checked only once.**"* — PHB p. 10
>
> **A failed check is permanent for that spell**, at that Intelligence. Not "try
> again next level" — *"Change in Intelligence: if intelligence goes down or up
> for any reason… the magic-user must check again."* **Only a change in INT
> reopens it.**
>
> **THE ONE ESCAPE, and it is narrow:** if a complete check through the whole
> level group fails to produce the MINIMUM number, the character may go back and
> re-check the ones he failed, repeating until the minimum is met. **That is a
> floor on the SIZE OF THE BOOK, not a second chance at a chosen spell** — and it
> only bites once a full group has been checked.

**Acquiring new spells later** — *"New spells can be gained from captured or
otherwise acquired spell books or from scrolls of magic spells. In the latter
event **the scroll is destroyed** in learning."*

## Wisdom — magical attack adjustment

| Score | Magical attack adjustment |
|---|---|
| 3 | -3 |
| 4 | -2 |
| 5 | -1 |
| 6 | -1 |
| 7 | -1 |
| 8 | 0 |
| 9 | 0 |
| 10 | 0 |
| 11 | 0 |
| 12 | 0 |
| 13 | 0 |
| 14 | 0 |
| 15 | +1 |
| 16 | +2 |
| 17 | +3 |
| 18 | +4 |

*source: **PHB p. 11**, WISDOM TABLE I, 200 dpi page render 2026-08-25.*

Applies **only to mental attack forms involving will force** — the PHB lists
beguiling, charming, fear, hypnosis, illusion, magic jarring, mass charming,
phantasmal forces, possession, rulership, suggestion, telepathic attack. It is
*not* a general saving-throw bonus. Blartho (WIS 15) +1, Yrtone (WIS 16) +2.

## Strength

| Score | Hit probability | Damage | Weight allowance | Open doors | Bend bars/lift gates |
|---|---|---|---|---|---|
| 3 | -3 | -1 | -350 | 1 | 0% |
| 4-5 | -2 | -1 | -250 | 1 | 0% |
| 6-7 | -1 | none | -150 | 1 | 0% |
| 8-9 | normal | none | normal | 1-2 | 1% |
| 10-11 | normal | none | normal | 1-2 | 2% |
| 12-13 | normal | none | +100 | 1-2 | 4% |
| 14-15 | normal | none | +200 | 1-2 | 7% |
| 16 | normal | +1 | +350 | 1-3 | 10% |
| 17 | +1 | +1 | +500 | 1-3 | 13% |
| 18 | +1 | +2 | +750 | 1-3 | 16% |
| 18/01-50 | +1 | +3 | +1000 | 1-3 | 20% |
| 18/51-75 | +2 | +3 | +1250 | 1-4 | 25% |
| 18/76-90 | +2 | +4 | +1500 | 1-4 | 30% |
| 18/91-99 | +2 | +5 | +2000 | 1-4 | 35% |
| 18/00 | +3 | +6 | +3000 | 1-5 | 40% |

*source: **PHB p. 9**, STRENGTH TABLE II: ABILITY ADJUSTMENTS, 200 dpi page
render 2026-08-27.*

**Open doors is the chance out of 6 on THAT TRY**, and the PHB is explicit about
what a failure costs: *"Successive attempts may be made at no penalty… but each
such attempt requires time and makes considerable noise."* A door that does not
give on the first shove is a round gone **and** grounds for an extra wandering
check.

**Bend bars/lift gates may be attempted ONCE, ever.** Fail and the character
will never succeed at that task.

**The party:** Dave 18/26 → **+1 hit, +3 damage, +1,000 gp allowance, open doors
1-3, bend bars 20%**. Torsat 13, Tristle 10, both open doors **1-2**, no combat
adjustments. Blartho and Yrtone 14 (+200 allowance). Frython 8 — **normal, not
penalised**; only 3-7 carry a penalty.

## Strength — where the bonuses do and do not apply

Dave's **18/26** gives **+1 to hit, +3 damage** *(PHB Strength Table II,
verified 2026-08-15)*.

**Neither applies to bow fire.** The Strength adjustments are melee-and-hurled;
a bow's force comes from the bow. Dave's short bow is a flat 1–6 at +0 to hit,
while his long sword is 4–11 at +1. Hurled weapons — darts, hand axes, thrown
spears — *do* take the Strength bonuses; missile weapons that store their own
energy do not.

Missile to-hit comes from **Dexterity** instead, above.

## Charisma Table (PHB p. 13)

Reactions are rolled constantly in this campaign and the speaker's Charisma is
the **only** adjustment the DMG names by rule. It was being applied from memory.

| Ability Score | Max. Henchmen | Loyalty Base | Reaction Adjustment |
|---|---|---|---|
| 3 | 1 | −30% | −25% |
| 4 | 1 | −25% | −20% |
| 5 | 2 | −20% | −15% |
| 6 | 2 | −15% | −10% |
| 7 | 3 | −10% | −05% |
| 8 | 3 | −05% | normal |
| 9 | 4 | normal | normal |
| 10 | 4 | normal | normal |
| 11 | 4 | normal | normal |
| 12 | 5 | normal | normal |
| 13 | 5 | normal | **+05%** |
| 14 | 6 | +05% | +10% |
| 15 | 7 | +15% | +15% |
| 16 | 8 | +20% | **+25%** |
| 17 | 10 | +30% | +30% |
| 18 | 15 | +40% | +35% |

*source: **PHB p. 13**, CHARISMA TABLE, 220 dpi page render 2026-08-30.*

**The reaction bonus does not start until 13.** Scores 9–12 are all flatly
"normal", so **this party has no talker.**

| | CHA | Reaction adj. | Max henchmen |
|---|---|---|---|
| Dave | 10 | **none** | **4** |
| **Yrtone** | **12** | **none** | 5 |
| Blartho | 11 | none | 4 |
| Frython | 11 | none | 4 |
| Torsat | 11 | none | 4 |
| Tristle | 9 | none | 4 |

*source: `party_roster.md` ability-score blocks, read column by column 2026-08-30.*

**THIS PARTY HAS NO REACTION ADJUSTMENT AT ALL.** Not one of the six reaches 13.
The best is 12, which the table prints as flatly *normal*. There is no better
speaker to send forward and there never has been. **Every reaction roll this
campaign has been, and will be, unmodified by Charisma** — every point of movement
has come from the circumstance adjustments the DM applies for gifts, honesty and
services rendered, which PHB p.13 explicitly licenses:

> *"if the charisma of the character is low, he or she will be working under a
> handicap which will have to be overcome by **generous offers and gifts** if a
> chance of success is hoped for."*

### I GOT THIS WRONG ONCE — 2026-08-30, player-caught, and it is the SAME error as the thief table

I put **Blartho at CHA 15 with a +15% adjustment** and announced it to the player
as a free unused resource. **Blartho's Charisma is 11.** The 15 is his **WISDOM**,
and it is bolded in `party_roster.md` because it drives his spell slots — so the
bold drew the eye to the wrong column of a six-column row.

This is precisely the failure that put Tristle's Find/Remove Traps at 30% for most
of the campaign: **reading DEXTERITY TABLE II across the wrong columns.** Two
separate errors, same cause. **Read ability-score rows by counting columns, not by
looking at what is emphasised.** Bold marks what mattered to whoever wrote the
line, not what you are looking for.

Worse than the number: it was delivered to the player as advice — *"send Blartho
to talk"* — which would have changed how they played the scene, for nothing.

**Max henchmen is not the same as hirelings.** *"It does not affect the number of
mercenary soldiers, men-at-arms, servitors, and similar persons in the pay of the
character."* Four ex-bandits taking wages are hirelings, not henchmen.
