# Crab spider → MM HUGE SPIDER

**B1 stocks "crab spiders" and THE MONSTER MANUAL HAS NO SUCH MONSTER.** B1 is a
Basic module; the crab spider is a B/X creature. Written the moment it came up —
day 95, expedition 11, with the party's hand on the smithy door — so the
conversion is a recorded decision and not something improvised at the reveal.

## The conversion, and why

B1's own wandering table prints the B/X stats: *"CrabSpider(1) — AC 7, HD 2\*,
hp 12, #AT 1, D 1-8 + poison, MV 120'(40'), Save F1, ML 7."* The MM offers five
spiders (p. 90). Two are candidates:

| | **LARGE spider** | **HUGE spider** | B/X crab spider |
|---|---|---|---|
| Armor Class | 8 | **6** | 7 |
| Hit Dice | 1+1 | **2+2** | **2** |
| Damage | **1** | **1-6** | **1-8** |
| Move | 6"/\*15" (climbs) | **18"** | 120' (40') |
| Poison save | +2 | **+1** | — |
| Surprises prey on | — | **1-5 in 6** | — |
| Size / Int | S / non- | **M / animal** | — |

**HUGE SPIDER is the conversion.** The hit dice, the damage and the ambush role
all match; the large spider's **HD 1+1 and damage 1** are far too weak for a
creature B1 gives 2 HD and a d8 bite.

**What is given up by not choosing the large spider:** its *"on walls, ceilings,
and floors"* line, which is the crab spider's signature in B/X. **That behaviour
is kept anyway** — the huge spider's own text has it *"build carefully hidden
places of concealment and rush forth upon prey, i.e. trapdoor spiders of huge
size"*, which is the same ambush by a different route, and is what its surprise
number is for.

*source: **Monster Manual p. 90**, read from a 170 dpi page render 2026-09-17.*

## Stat block — MM HUGE SPIDER

| Field | Value |
|---|---|
| Armor Class | **6** |
| Hit Dice | **2+2** |
| Move | **18"** |
| Number of Attacks | 1 |
| Damage | **1-6** + poison |
| Save As | F1 |
| Treasure Type | J-N, Q |
| Intelligence | Animal |
| Alignment | Neutral |
| Size | M |
| Number Appearing | 1-12 |
| Surprised On | 2 |
| **SURPRISES ON** | **5** |
| To hit AC 0 | **16** |
| **XP value** | **145 + 3/hp** |
| Morale | — (MM gives none; use DMG morale) |

*source: **Monster Manual p. 90** (the five-spider table, 170 dpi page render
2026-09-17) **cross-checked against DMG Appendix E, pdf p. 211** (300 dpi,
rotated 270, read by eye). Both books give AC 6, HD 2+2, 1 attack, 1-6 damage
and surprise on 1-5 independently of each other. The `To hit AC 0` and the XP
value come from Appendix E, which is the only place in 1e that prints either.*

> ### ⛔ `Surprises On` IS 5. THIS IS THE ROW THAT MATTERS.
>
> *"Note that these creatures **surprise prey on a roll of 1-5 (out of 6)**."*
> — MM p. 90
>
> **That is worse than the troglodyte's chameleon 4**, which this campaign
> already applies and which cost it two mis-rolled encounters before the number
> was written down. Feed it to the tool explicitly:
>
> ```bash
> python tools/combat.py surprise --who party --surprised-on 5 \
>     --why "MM huge spider surprises prey on 1-5, p.90"
> ```
>
> **Do not take the default.** The default is 2 and it is wrong by three pips.

## Poison

> *"All saving throws versus the poison of huge spiders are at **+1** on the
> dice."* — MM p. 90

**A failed save against MM poison is DEATH unless the entry says otherwise, and
this entry does not** (DMG; cf. the giant spider's *"must save versus poison or
be killed"* on the same page). The +1 is the only mercy in it.

**Party saves vs poison** — see `rules/combat.md`; at 1st level everyone in this
party saves on **14** or better on a d20, so **13+ with the +1.**

## It can leap

> *"It can **leap 3"** upon prey and deliver its deadly bite."* — MM p. 90

**Thirty feet, from concealment, in one action.** Nobody in a corridor is out of
reach because they are standing at the back.

## XP value — **145 + 3/hp**, and it VALIDATED THE WHOLE CONVERSION

*source: **DMG Appendix E, pdf p.211**, read the hard way on 2026-09-17 — the
appendix is printed sideways and its OCR is noise, so: render 300 dpi, rotate
270 expand, OCR to find the row, then crop and READ IT BY EYE. The figure was
confirmed visually, because digits corrupt silently in these scans.*

**The row is the cross-check that makes the huge-spider conversion safe rather
than merely argued.** Appendix E prints, independently of MM p.90:

> **huge — M, to hit AC 0 = 16, AC 6, HD 2+2, 1 attack, 1-6 damage,
> "surprise on 1-5, poison", defences nil, animal, 145 + 3/hp**

**Every figure matches the MM entry, including the surprise on 1-5.** Two books,
two pages, one monster. The large spider's row on the same line reads AC 8,
HD 1+1, damage 1 — which is how far off the rejected alternative was.

**First kills, day 95:** hp 6 → 145 + 18 = **163**; hp 5 → 145 + 15 = **160**.
Total **323**.

## B1's stocking — DM-side, do not quote to the player

Two are placed in **area 18, the smithy**, and one in **area 52**. Their hit
points were rolled under B/X's HD 2 and **are kept, not re-rolled**, per the
standing rule that B1's stocking is rolled once and is the only copy.

## Play record

**Day 95, expedition 11, area 18 the smithy — BOTH KILLED IN THE SURPRISE
SEGMENT, no damage taken.**

The party rolled **6** on a **1-5** surprise range — a one-in-six escape from the
thing these creatures are built for — and they rolled **1**, losing one segment
(DMG p.61: *one side surprised loses segments equal to its OWN roll*; a 2 would
have cost them two). Frython's *sleep* took the smaller one (1d4 = 1 affected;
equal hit dice, so PHB p.68 breaks the tie on hit points). Torsat and Tristle
put **twelve arrows** into the other at the DMG's 3x rate, which applied because
their bows were the ready weapons — **19 damage against 6 and 5 hit points.**

**The slings and darts were never loosed.** A sling must be loaded and whirled,
so it is not "ready" in the DMG's sense, and by the time it was the fight was
over. Four stones and three darts saved.

**Nothing got to use its poison, its leap, or its 1-5 surprise.** On a different
d6 this would have been two men down before anyone moved.

**Day 140, expedition 31, area 52 the raised cavern — IT GOT THE ROLL THIS
TIME.** Hidden near (32,34), it surprised Tristle alone (surprised-on 5,
rolled 1) as he approached the stairs up from area 53. Its leap missed (needs
12 vs AC4, rolled 6). Tristle tried to break off and rejoin the party — this
is what exposed the "breaking off from melee" rule's full DMG p.70 cost (+6
total, shield+DEX negated, not the +2 this file and `rules/exploration.md`
had been using): its free attack hit (18 vs AC8) for 3, taking Tristle's 3hp
to 0. He made the poison save (14+1 vs 13). The decision was reopened once
the rule was corrected (see `rules/exploration.md`), and healed back to 3/3.

**Redeclared: Tristle stood and fired point-blank instead of retreating**,
calling the party in. His shot alone (5 dmg) plus Blartho's flail (nat 20, 3
dmg) killed it outright in one round, 8 of 7hp, before it got a second
action. Dave and Torsat spent the round only closing and switching to
sword+shield (DMG weapon-change rule), no attack. Untouched otherwise.
