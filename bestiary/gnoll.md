# Gnoll

First fought **day 99, expedition 13**, in the corridor north of (13,32) on level 1.
One of them, alone, and it died at the break-off without landing a blow.

> ## ⚠ SIZE **L**. THIS IS THE FIELD THAT WAS MISSED IN THE FIRST FIGHT.
>
> A gnoll is **7 feet or more** and the Monster Manual prints its size as **L**,
> not M. It is the only man-shaped thing the party has met that is larger than
> man-sized, and `combat.py --target` takes size as an argument precisely so the
> **vs L** damage column gets used.
>
> **It was not passed on day 99, because this file did not exist yet**, so the
> whole fight rolled S/M damage. Two weapons in this party change:
>
> | weapon | vs S or M | **vs L** |
> |---|---|---|
> | Dart | 1-3 | **1-2** |
> | Sling bullet | 2-5 | **2-7** |
> | Arrow | 1-6 | 1-6 — no change |
>
> So **darts get worse and slings get better** against these, and the two
> roughly cancel across a volley — which is exactly why the error was invisible
> at the table and would have stayed invisible. Pass `size L`.

## Gnoll stat block

| Field | Value |
|---|---|
| Armor Class | 5 |
| Hit Dice | 2 |
| Move | 9" |
| Number of Attacks | 1 |
| Damage | 2-8 or by weapon |
| Save As | F2 |
| Treasure Type | Individuals **L, M**; D, Q (x5), S in lair |
| Intelligence | low-average |
| Alignment | Chaotic evil |
| Size | **L (7'+ tall)** |
| Number Appearing | 20-200 |
| Frequency | Uncommon |
| Percent In Lair | 20% |
| Magic Resistance | standard |
| Special Attacks | nil |
| Special Defenses | nil |
| Surprised On | 2 |
| Surprises On | 2 |
| Morale | 55 |
| XP Value | **28 + 2/hp** |

*source: **Monster Manual p. 46**, 160 dpi page render 2026-09-18. XP value from
**DMG Appendix E, printed p. 203**, 250 dpi render `prerotate(90)` 2026-09-18 —
the appendix text layer is unusable, as `rules/experience.md` warns.*

**Morale 55 is derived, not printed:** DMG p.67 gives base 50 +5%/hit die above
1. Two hit dice with no "+n" in the expression means **50 + 5 = 55**, and the
rolled hit points do not enter into it.

## Special attacks

None. The entry prints *Nil*.

## Special defences

| Defence | Detail |
|---|---|
| Infravision | *"They have infravision"* — MM p. 46. No range is printed |
| Nothing else | Special Defenses: *Nil*. No magic resistance beyond standard |

## Languages — and why this one mattered immediately

> *"They speak their racial tongue, chaotic evil, troll, and often (60%) orcish
> and/or hobgoblin."* — MM p. 46

**Tristle speaks gnoll** (`party_roster.md` line 75) **and orcish**. A gnoll that
rolls inside that 60% can be spoken to in either tongue, and the party met orcs
in the same corridor system the same day.

> *"Gnolls will generally be on friendly terms with orcs, hobgoblins, bugbears,
> ogres, and even trolls — providing the weaker types are not very much weaker
> in numbers and the gnolls are relatively equal in strength to the stronger
> monsters."* — MM p. 46

That is a **standing relationship printed in the book, not a DM choice**, and it
cuts both ways: it constrains how gnolls react to the orcs the party has been
parleying with, and it means a gnoll is not automatically an enemy of Ruk's band.

## Behaviour that matters at the table

- **Subterranean 85% of the time.** Above ground they take an abandoned village.
- **Loose bands, largest dominating** — *"they have a so-called king… but his
  authority extends only as far as his reach."* No reliable chain of command.
- **Strong, but they dislike work and are not good miners.** They take captives
  instead: *"1 per 10 gnolls is minimum."*
- Underground they are **30% likely to have 1-3 trolls living with them** as
  guards. Above ground, 65% likely to keep hyenas or hyaenodons.
- Short-lived — **35 years is average.**

## Leaders

| Trigger | What is added |
|---|---|
| every 20 gnolls | a leader-type, **16 hp**, attacks as a 3 HD creature |
| 100 or more | a chieftain — **AC 3, 22 hp**, attacks as 4 HD, **4-10 damage** |
| 100 or more | **2-12 guards** — AC 4, 20 hp, attack as 3 HD, **3-9 damage** |
| in lair | a chieftain always, plus **5-20 guards** |

## Weapons carried

Great bow 15%, **pole arm 35%**, two-handed sword 15%, battle axe 20%, morning
star 15%. *"All carry swords"* in addition.

**The 35% pole arm is the dangerous roll** — a pole arm reaches the second rank
from outside a shield wall, and the party's formation assumes it cannot be.

## Appearance

Greenish-grey skin, darker at the muzzle; a mane running reddish-grey to dull
yellow; **dull black eyes, amber nails**. Armour of horn, metal plates and
leather, all of it shabby, over moth-eaten fur capes and vests in brown, black or
greyish pelt. *"There is a great resemblance between gnolls and hyenas."*

## Module conversion — B1

B1's own monster list, entry 12, as printed:

> *"12. Gnolls (1-4) — AC 5, HD 2, hp 13,7,6,3, #AT 1, D 2-8 or by weapon +1,
> MV 90' (30'), Save F2, ML 8"*

*source: **B1 printed p. 26** (pdf page 27), 320 dpi clipped render 2026-09-18.*

| field | B1 (Basic) | MM (1e) | which we use |
|---|---|---|---|
| AC / HD / #AT / damage | 5 / 2 / 1 / 2-8 | 5 / 2 / 1 / 2-8 | **agree** |
| weapon damage | **"or by weapon +1"** | "or by weapon" | **MM — no +1** |
| Move | 90' (30') | 9" | same rate, different notation |
| Morale | ML 8 (of 12) | — | **DMG percentage system, 55** |

**The `+1` is the only real disagreement and the MM wins** — precedence is
Monster Manual over module for creature statistics in a 1e conversion. Basic
D&D gives gnolls that bonus; AD&D does not.

**The hit points 13, 7, 6, 3 are the module's own pre-rolled four.** The one met
on day 99 was **hp 13**, the first of them, so three of B1's gnolls remain
unspent at 7, 6 and 3.

## Play record

**Day 99, expedition 13, round 245 — corridor north of (13,32), one gnoll, hp 13.**

| | |
|---|---|
| Reaction | **17** — hostile (DMG p.63) |
| Surprise | none either side. Its roll was **voided**: it had been awake and holding for four rounds and had watched the party come up the corridor |
| Initiative | monsters **5**, party **2** — it acted first |
| Its attack | charged the front rank, dice gave it **Dave**, **missed 7 against 12** |
| The volley | seven shooters at ten feet: Torsat 1, Tristle 2, Blartho sling 3, Frython dart 3, Ista dart 2 — **eleven as rolled**, ~10 on the corrected vs-L columns |
| Friendly fire | **Dave's first arrow was a natural 1** and went into **Yrtone** for 2 |
| Morale | **d100 88, +15 for wound damage past half = 103 vs 55. Broke by 48% — flee in panic** |
| The kill | **DMG p.70 free attack at +6**, shield and DEX negated, from the three engaged: Dave 3 and 6, Torsat 3 and 3, Yrtone 2. **All five hit for 17** on a creature holding 2 |

**It never touched anybody.** The only blood the party lost in the fight was to
one of its own arrows.

**What this fight is actually evidence of:** the party's massed missile volley is
the strongest thing it does, and its cost is that the front rank fights at AC 4
instead of 3 with shields slung, and that a natural 1 has somewhere bad to go.
Eleven points in one half-round out of eight people is more than any two of them
can do in melee.
