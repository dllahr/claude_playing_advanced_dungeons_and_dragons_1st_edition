# Skeleton

Magically animated bones. **Undead.** Met in expedition 7, day 46, behind the
secret door into area 9, the Wizard's Laboratory.

## Skeleton stat block

| Field | Value |
|---|---|
| Armor Class | **7** |
| Hit Dice | **1** |
| Move | **12"** |
| Number of Attacks | **1** |
| Damage | **1-6** |
| Special Attacks | Nil |
| *(damage note)* | **1-6 REGARDLESS of the weapon carried** — MM p.88. Kept out of the Damage row because `tools/bestiary.py` feeds it to `dice.py` and prose in a numeric field crashes it. It did, on first use. |
| Special Defenses | **See below — this is the whole encounter** |
| Magic Resistance | See below |
| Intelligence | Non- |
| Alignment | Neutral |
| Size | M |
| Number Appearing | 3-30 |
| Treasure Type | Nil |
| % in Lair | Nil |
| XP Value | **7 + 1/hp** *(DMG App. E, p. 205: 1 HD, no special abilities beyond defences)* |
| Morale | **NONE. "Skeletons attack until destroyed."** |
| Surprised On | 2 |
| Surprises On | 2 |

*source: **Monster Manual pp. 87-88**, 300 dpi page renders 2026-09-06.*

**Both surprise numbers are the 1-2 default and are a DM call, not an MM figure.**
Skeletons have no senses to sharpen and no reason to be alert, and they do not
stalk, hide or ambush — MV 12" and no stealth of any kind.

> **KEEP VALUE CELLS BARE.** `tools/bestiary.py` feeds these cells to `dice.py`
> and to `int()`. Prose in a value column crashes the tool or fails a test — it
> did **twice** on this entry the day it was written, once on Damage and once on
> Surprised On. **Numbers in the table, reasoning underneath it.**

## THE SPECIAL DEFENCES — read these before rolling any damage

> *"The skeleton strikes with some form of weapon, but **regardless of the weapon
> type the damage caused by a hit will be 1-6 hit points**."*
>
> *"**Skeletons suffer only one-half damage from sharp and/or edged weapons**
> (such as spears, daggers, swords). **Blunt weapons such as clubs, maces,
> flails, etc. score normal damage. Fire scores normal damage.** *Sleep, charm,
> hold* and *cold*-based spells **do not affect skeletons**. **Holy water causes
> 2-8 hit points of damage** on a skeleton for each vial which strikes it.
> **Skeletons attack until destroyed**."*
>
> — MM p. 88

| | |
|---|---|
| **Half damage** | sharp and/or edged — *"spears, daggers, swords"*. **Arrows, darts and bolts are pointed: HALVED.** DM ruling on rounding: **round DOWN, minimum 1** — the MM gives no rounding rule, so this is fixed here so it is the same number every time |
| **Normal damage** | **blunt** — clubs, maces, **flails** — and **fire** |
| **No effect at all** | *sleep*, *charm*, *hold*, cold-based spells |
| **2-8 per vial** | **holy water** |
| **Never flee** | attack until destroyed. Do not roll morale |

## WHAT THIS MEANS FOR THIS PARTY — day 46

**Everything decided in the last two days bears on this, and mostly badly.**

| | |
|---|---|
| Dave, Torsat, Tristle — **long swords** | **HALVED** |
| Hask — **short sword** | **HALVED** |
| Ista — **darts (1-3)** and spear | **HALVED**, so mostly 1 point a throw |
| **Yrtone, Blartho, DELLIE — footman's flails** | **FULL DAMAGE.** The three clerics are the party's best weapons here |
| Frython — **his only spell is *sleep*** | **NO EFFECT. He is carrying a dead card** |
| Yrtone's and Blartho's ***command*** | **undead are immune** (PHB p. 43). Also dead |
| **Holy water** | **the party has NONE** — the question of where to get it was raised on day 45 and the answer was *ask Cuddy at Draycot on day 51* |
| **Oil flasks** | fire scores **normal** damage, and Ista is carrying the fuel |

> **The cleric prohibition that took Dellie's spear on day 39 — and that she was
> unhappy about at 40 — handed her the correct weapon for the first fight she
> ever walks into.** Nobody planned that.

**And the clerics can TURN them.** Three 1st-level clerics against 1 HD undead is
the strongest card the party holds. Look up the turning matrix (DMG p. 75) before
rolling — it is not in the cache yet.

### Open question, DM call needed if it comes up

**Does *light* blind a skeleton?** DMG p. 45 gives −4 to hit, saves and AC when
cast *"upon the visage or before the visual organs of a creature."* **A skeleton
has eye sockets and no eyes.** Dellie is holding two castings. Decide before she
asks, not after.

## Play record

*(nothing yet — first contact is expedition 7, day 46, round ~86)*
