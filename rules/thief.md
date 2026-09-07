# Thief functions — AD&D 1e

Parsed by `tools/rules.py`. Tristle is the party's only thief: **1st level, elf,
DEX 18**.

## Thief function table — base chance by level

| Level | Pick Pockets | Open Locks | Find/Remove Traps | Move Silently | Hide in Shadows | Hear Noise | Climb Walls | Read Languages |
|---|---|---|---|---|---|---|---|---|
| 1 | 30% | 25% | 20% | 15% | 10% | 10% | 85% | - |
| 2 | 35% | 29% | 25% | 21% | 15% | 10% | 86% | - |
| 3 | 40% | 33% | 30% | 27% | 20% | 15% | 87% | - |
| 4 | 45% | 37% | 35% | 33% | 25% | 15% | 88% | 20% |
| 5 | 50% | 42% | 40% | 40% | 31% | 20% | 90% | 25% |

*source: **PHB p. 28**, THIEF FUNCTION TABLE (PLUS RACIAL ADJUSTMENTS), 200 dpi
page render 2026-08-29.*

## Racial adjustments

| Race | Pick Pockets | Open Locks | Find/Remove Traps | Move Silently | Hide in Shadows | Hear Noise | Climb Walls | Read Languages |
|---|---|---|---|---|---|---|---|---|
| Dwarf | - | +10% | +15% | - | - | - | -10% | -5% |
| Elf | +5% | **-5%** | - | +5% | +10% | +5% | - | - |
| Gnome | - | +5% | +10% | +5% | +5% | +10% | -15% | - |
| Half-Elf | +10% | - | - | - | +5% | - | - | - |
| Halfling | +5% | +5% | +5% | +10% | +15% | +5% | -15% | -5% |
| Half-Orc | -5% | +5% | +5% | - | - | +5% | +5% | -10% |

*source: **PHB p. 28**, same table, same render.*

## Dexterity Table II — adjustments for thieves

| Ability Score | Picking Pockets | Opening Locks | Locating/Removing Traps | Moving Silently | Hiding in Shadows |
|---|---|---|---|---|---|
| 9 | -15% | -10% | -10% | -20% | -10% |
| 10 | -10% | -05% | -10% | -15% | -05% |
| 11 | -05% | 0 | -05% | -10% | 0 |
| 12 | 0 | 0 | 0 | -05% | 0 |
| 13 | 0 | 0 | 0 | 0 | 0 |
| 14 | 0 | 0 | 0 | 0 | 0 |
| 15 | 0 | 0 | 0 | 0 | 0 |
| 16 | 0 | +05% | 0 | 0 | 0 |
| 17 | +05% | +10% | 0 | +05% | +05% |
| 18 | +10% | **+15%** | **+05%** | +10% | +10% |

*source: **PHB p. 12**, DEXTERITY TABLE II: ADJUSTMENTS FOR THIEVES, 200 dpi page
render 2026-08-29.*

**Read the row across carefully.** At DEX 18 the columns are +10 / +15 / **+05** /
+10 / +10. Locating/Removing Traps gets only **+5%** — this was misread as +10%
and put Tristle's trap chance in the cache at 30% for most of the campaign. It is
25%.

## Tristle — the numbers actually in play

| Function | Base (lvl 1) | Elf | DEX 18 | **Total** |
|---|---|---|---|---|
| Open Locks | 25% | -5% | +15% | **35%** |
| Find/Remove Traps | 20% | - | +5% | **25%** |
| Move Silently | 15% | +5% | +10% | **30%** |
| Hide in Shadows | 10% | +10% | +10% | **30%** |
| Pick Pockets | 30% | +5% | +10% | **45%** |
| Hear Noise | 10% | +5% | 0 | **15%** |
| Climb Walls | 85% | - | 0 | **85%** |

*source: computed from the two tables above; both verified from page renders.*

## ONE TRY PER LOCK, EVER

> *"Opening Locks may be attempted by any given thief but once per lock. If the
> score generated exceeds the adjusted (for ability and race) base score, the
> thief has failed; and no amount of trying will ever enable him or her to
> succeed with that lock, although the thief may try again when he or she has
> risen to a higher experience level."* — PHB p. 28

**A failed pick is final until Tristle reaches 2nd level.** Not "try again next
round", not "try again with better light". The same wording governs traps:
*"Finding/Removing Traps is accomplished in exactly the same manner as opening
locks… One try only per thief is allowed."*

This is the same family of rule as bend bars/lift gates — a once-ever roll — and
it must be called out **before** the dice, not after.

## Hear Noise, in the book's own words

> *"Hearing Noise is simply listening intently. The thief and his or her
> accomplices must themselves be quiet (but not silent as in moving). This
> function can be repeated as often as desired. It requires a full minute to
> listen, i.e. one-tenth of a normal turn, or time equal to a melee round. Note
> that sleeping creatures, undead, and many other creatures do not make sounds
> discernible through a portal."* — PHB p. 28

Note the contrast: Hear Noise **may be repeated as often as desired**; Open Locks
and Find Traps may not.

> ## ⚠ THE LIMIT IS PER **OBJECT**, NOT A PER-LEVEL BUDGET
>
> **Misapplied 2026-09-06 and caught by the player.** The DM told the party that
> because Tristle and Ista had each used Find/Remove Traps on the area 36 pit
> trap, **neither could check a secret door found an hour later.** That is wrong.
>
> **Read the PHB's own words for locks, which traps explicitly follow "in exactly
> the same manner":** *"once per **lock**… no amount of trying will ever enable
> him or her to succeed **with that lock**."* **Per lock. Per trap. Per object.**
> *"One try only per thief is allowed"* means one try at **that** trap.
>
> A per-level budget would make a thief useless in any dungeon containing more
> than one trap, which is every dungeon.
>
> | | |
> |---|---|
> | Tristle fails on the pit trap at (29,31) | he may never try **that trap** again until 2nd level |
> | A different trap, ten minutes later | **fresh attempt, full percentage** |
> | Ista fails on the same pit trap | same — **her own** attempt at that trap is spent, nothing else is |
>
> **The player's own worked example, which is the rule:** Tristle searched the
> side table in the wizard's bedroom and found nothing; he never gets another try
> **at that table**. Every other table in Quasqueton is a new roll.
