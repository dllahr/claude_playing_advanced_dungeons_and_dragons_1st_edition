# Ghoul

Undead. Two are stocked in area 22, the Garden Room (B1 DM key). Statted from a
150 dpi render of Monster Manual pp. 43-44 on 2026-09-24, day 119, before the
party reached the garden.

## Ghoul stat block

| Field | Value |
|---|---|
| Armor Class | **6** |
| Hit Dice | **2** |
| Move | **9"** |
| Number of Attacks | **3** |
| Damage | **1-3** |
| *(damage note)* | Three attacks: **1-3 / 1-3 / 1-6** (two claws, one bite). The tool reads one cell, so the first value stays here and the bite is in this note. |
| Special Attacks | Paralyzation |
| Special Defenses | See below |
| Magic Resistance | Standard |
| Intelligence | Low |
| Alignment | Chaotic evil |
| Size | M |
| Number Appearing | 2-24 |
| Treasure Type | B, T |
| % in Lair | 20 |
| XP Value | **65 + 2/hp** *(DMG App. E p. 201, read off a 250 dpi render rotated 270 degrees, 2026-09-24)* |
| Morale | **NONE. "Ghoul packs always attack without fear."** |
| Surprised On | 2 |
| Surprises On | 2 |

*source: **Monster Manual pp. 43-44**, 150 dpi page renders 2026-09-24.*

**Both surprise numbers are the 1-2 default and are a DM call, not an MM figure.**
The MM gives neither. Ghouls hunt with "a terrible cunning", which is a reason
to think about it if a pack ever stalks the party, but nothing in the entry moves the number.

> **KEEP VALUE CELLS BARE.** `tools/bestiary.py` feeds them to `dice.py` and
> `int()`. Numbers in the table, reasoning underneath.

## Special attacks

| Trigger | Save | Effect | Duration |
|---|---|---|---|
| **Any hit** (claw or bite) — *"Their touch causes humans ... to become rigid"* | **Save vs paralyzation** (Dave/Torsat/Hask fighters 14 at 1st-2nd level; clerics 10; thieves 13; M-U 14 — `rules/combat.md`, DMG p. 79) | **Paralyzed** | **NOT GIVEN in the ghoul entry.** Flag it. Fix it by DM ruling before the first hit lands and write the ruling here. |
| **Elves are IMMUNE** — *"including dwarves, gnomes, half-elves, and halflings, but excluding elves"* | — | Tristle cannot be paralyzed by a ghoul. (Half-elves would be affected. Nobody in the party is one.) | — |
| **A human killed by a ghoulish attack** | none unless blessed | **Becomes a ghoul.** *"unless blessed (or blessed and then resurrected)."* | — |

## Special defences

*"subject to all attack forms except **sleep and charm** spells. They can be
**turned** by clerics. The magic circle of **protection from evil** actually keeps
these monsters completely at bay."* MM p. 44. Also from p. 43, on ghasts and by
extension the circle: it does not keep them at bay unless used with cold iron.

| | |
|---|---|
| **Sleep, charm** | no effect. **Frython's only spell is sleep** |
| **Everything else** | works: ordinary weapons, fire, oil, spells other than sleep and charm |
| **Turning** | clerics can turn them (DMG turning matrix, not in the cache yet — look it up) |
| **Never flee** | no morale check |

## Module conversion — B1

B1 line: **"Ghouls (1-2) — AC 6, HD 2*, hp 6,4, #AT 3, D 1-3 each + special, MV 90' (30'), Save F2, ML 9."**
AC, HD, attacks agree with the MM. B1's damage is 1-3 *each*; the MM has the bite at 1-6.
**Use the MM per the standing precedence** (DMG over module for adjudication; MM over module for the creature).
B1's ML 9 is Basic D&D. The MM says they never flee, so it is ignored here.

## Play record

**Day 119, round 419, expedition 16, area 22 mouth end.** One ghoul (hp 6) met crouched at (11,11) from the corridor mouth at (10,10). Party 3 (not surprised), ghoul 1 on 1-2 (SURPRISED, one segment lost). Dave (bow, 3x in the surprise segment) hit for 5 and Torsat (bow) for a natural 20 and 6: dead in the first third. **Award 77** (65 + 2x6). A second ghoul (hp 4) is stocked in the north arm and has not been met.
