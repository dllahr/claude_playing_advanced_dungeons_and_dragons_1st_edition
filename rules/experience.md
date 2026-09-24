# Experience — AD&D 1e

Parsed by `tools/rules.py`. Monster XP values come from **DMG Appendix E,
"Alphabetical Recapitulation of Monsters"**, which is the only place in 1e that
prints them — the Monster Manual entries do not carry an XP line.

**Appendix E's text layer is unreadable.** The appendix is printed *sideways*
(landscape) across DMG pdf pages 195–214, and its OCR is pure noise — the page
dumps read `z 0 4 z 4 x d u m I- K I- W`. Every value below was read off a page
render rotated 270°. Do not try to grep these out of the `.txt`.

To find a monster's page: render at 150 dpi, `.rotate(270, expand=True)`, and OCR
*that* to locate the name; then crop the row and read it. Straight OCR of the
unrotated page finds nothing.

## Monster experience point values

| Monster | Hit Dice | AC | To hit AC 0 | XP value |
|---|---|---|---|---|
| Centipede, giant | 1/4 | 9 | 20 | 30 + 1/hp |
| Kobold | 1/2 | 7 (6) | 20 | 5 + 1/hp |
| Rat, giant | 1/2 | 7 | 20 | 7 + 1/hp |
| **Orc** | **1** | 6 | 19 | **10 + 1/hp** |
| Troglodyte | 2 | 5 | 16 | 36 + 2/hp |
| Ghoul | 2 | 6 | 16 | 65 + 2/hp |

*source: **DMG Appendix E**, pp. 197, 205, 209, 213 (pdf pages 196, 204, 208,
212), 190 dpi page renders rotated 270°, read 2026-08-28.*

**"36 + 2/hp" means base 36 plus 2 per ACTUAL HIT POINT the creature had** — not
per hit die. A troglodyte rolled at 6 hp is worth 36 + 12 = **48**, one at 5 hp
is 36 + 10 = **46**. This is why the campaign records monster hit points at the
moment of the encounter: without them the award cannot be computed later.

**ORC transcribed 2026-08-31** from a 300 dpi render of **DMG Appendix E, printed
p. 208**, rotated 90 degrees (the appendix is printed sideways and its text layer
is unusable):

| creature | X.P. value |
|---|---|
| **orc** | **10 + 1/hp** |
| orc, guard or subchief (11 hp) | 20 + 2/hp |
| orc, bodyguard or chief (13-16 hp) | 20 + 2/hp |
| ogre | 90 + 5/hp |
| ogre, leader / chieftain | 225 + 8/hp |

*source: **DMG Appendix E, p. 208**, ALPHABETICAL MONSTER LISTING, 300 dpi page
render 2026-08-31.*

**Render note for next time:** `prerotate(90)`, not 270 — 270 comes out upside
down. The XP Value column is the LAST column, which sits in the **top 16%** of the
unrotated page; the Monster/Size/AC/HD columns are at y 45-100%. Clip in
unrotated page space.

Values for berserkers (MEN) are **still not transcribed**. Expedition 3
scored both as *base 10 + 1/hp*; that figure is **unverified against Appendix E**
and should be checked before any further award relies on it.

## When experience is awarded

**B1 awards XP only when the party gets out of the dungeon alive.** Kills and
treasure accumulate as a pending ledger during an expedition and are credited on
emerging — this is the module's own rule and it is why `campaign/encounters.tsv`
can legitimately show nothing for an expedition still in progress. The pending
ledger lives in the DM notes.

Treasure is worth **1 XP per gold piece of value**, counted when it is brought
out. Magic items have their own XP values in the DMG; an **unidentified** item
earns nothing until the party establishes what it is.

**The prime-requisite bonus applies ONCE to the whole earned total**, not to each
award — `tools/xp.py` does this, and doing it per-award lets truncation eat the
bonus on small kills.

## Magic items — keep it or sell it (DMG pp. 85, 121)

> *"The suggested experience point (x.p.) values are for characters who **keep**
> the items. Gold piece sale values are the usual sums which characters will be
> paid for magic items, and **if so sold, the x.p. award should be based on the
> selling price of the items, not the x.p. value.**"* — DMG p. 121

> *"All items (including magic) or creatures sold for gold pieces prior to the
> awarding of experience points for an adventure must be considered as treasure
> taken… (Those magic items **not** sold gain only a relatively small amount of
> experience points, for their value is in their usage.)"* — DMG p. 85

> *"Treasure must be **physically taken out of the dungeon** or lair and turned
> into a transportable medium or stored in the player's stronghold to be counted
> for experience points."* — DMG p. 85

*source: **DMG pp. 85 and 121**, 200-280 dpi page renders 2026-08-30.*

**So there are two mutually exclusive awards, never both:** the item's printed XP
value if kept, or the gold it fetched if sold. Selling is usually worth far more —
a *potion of sweet water* is 200 xp kept and 250 gp sold; *treasure finding* is
600 kept against 2,000 sold.

### THE DMG PRINTS NO XP VALUE FOR A SCROLL OF SPELLS

Table **III.B SCROLLS** (DMG p. 121) has columns for *Dice*, *Result* and *Spell
Level Range* and **no experience column at all**. Only the eight *protection*
scrolls carry a value, in parentheses: Demons and Devils 2,500; Petrification and
Possession 2,000; Elementals, Magic and Undead 1,500; Lycanthropes 1,000. The
spell scrolls (dice 01–60) have nothing, and the item-description section adds no
per-spell-level figure either. **Checked; it is genuinely absent.**

**DM RULING, 2026-08-30 — a scroll of one 1st-level spell is worth 100 x.p.**
Anchored *below* the cheapest thing on the potions table (*sweet water*, 200),
because a single 1st-level spell is the least valuable magic item in the game.
Recorded here so it is the same number next time, and flagged as a ruling rather
than a rule because **the book does not give one.**

**Consuming a scroll to transcribe it counts as keeping, not selling.** The value
went into a spellbook permanently, which is the strongest form of *"its value is
in its usage."*

## Dividing experience — and the HALF SHARE for non-player characters

> *"X.p. for the slain monsters are totalled. All surviving characters who took
> part (no matter how insignificantly) in slaying the monsters are totalled.
> X.p. total is divided by the number of characters, each getting an equal
> share… **Exception:** Monsters slain single-handedly… accrue x.p. only to the
> slayer."*
>
> *"…so each survivor gains 430 — adjusted for difficulty and for being actual
> player characters or **halved for henchman characters**."* — **DMG p. 85**

*source: **DMG p. 85**, EXPERIENCE (Division of Experience Points), 200 dpi page
render 2026-08-30.*

**So an NPC fighting on the party's side draws a HALF share** — not a full one and
not nothing.

**A half share does not halve everyone else's award.** The pot is divided by the
sum of the *weights*, not by the head count. Six PCs and two NPCs is **seven**
shares, not eight: each PC takes 1/7 and each NPC 1/2 of 1/7.

| party | shares | a 700 xp award |
|---|---|---|
| 6 PCs | 6.0 | 116.7 each |
| 6 PCs + 2 NPCs | **7.0** | **100 each PC, 50 each NPC** |

*source: computed from the rule above.*

**Implemented in `tools/xp.py` via a `share` column on
`campaign/characters.tsv`** — `full` or `half`.

### `all` MEANS THE PARTY, AND HALF-SHARE NPCs MUST BE NAMED

`earned_by: all` resolves to every **full-share** character and nobody else.
Half-share allies have to be listed by name on the awards they were actually
present for.

**This is not fussiness.** The first attempt let `all` mean *everyone in the file*,
and simply adding Hask and Dellie to the roster **retroactively cut them in on a
carrion crawler they never saw**, taking Dave from 567 to 520. An `all` that
silently absorbs every new ally re-divides the entire campaign's history every
time somebody joins.

**Player's standing rule, 2026-08-30:** *"split XP with them — make that the case
for any group of people fighting on the same side in a combat."* **Treasure is a
separate question and is settled by agreement, not by this table.**

## "One gold piece GAINED" — PHB p. 106, and a correction to my own ruling

> *"As a rule, one point of experience will be awarded for **one gold piece gained
> by a character**… Magic items gained and retained have only a low experience
> point value, for they benefit the character through their use. Magic items
> gained and sold immediately are treated as gold pieces, the selling price
> bringing an award in experience on the stated one for one basis. Experience
> points awarded for treasure gained — monetary or magical — are **modified
> downward if the guardian of the treasure** (whether a monster, device, or
> obstacle, such as a secret door or maze) **was generally weaker than the
> character who overcame it.** A 4th level character versus a single orc is an
> overmatch, and only about 10% of the treasure value gained could count towards
> experience points; but if nine or ten orcs were involved, the experience points
> awarded would generally be on the one for one basis."*
>
> *"Monsters captured or slain always bring a full experience point award.
> **Captured monsters ransomed or sold bring a gold piece: experience point ratio
> award.**"*

*source: **PHB p. 106**, EXPERIENCE, 300 dpi page render 2026-09-01.*

### I RULED THIS RIGHT FOR THE WRONG REASON — corrected 2026-09-01

I told the player that the wool venture's profit earns no experience, citing DMG
p.85's *"treasure must be physically taken out of the dungeon or lair."*

**That sentence is a LOGISTICS clause, not a jurisdictional one.** It exists to
stop a party claiming a hoard they saw but could not carry, and to force the
conversion step. Read as *"XP only comes from dungeons"* it collapses at once:
**PHB p.106 says "one gold piece GAINED" with no location qualifier at all**,
wilderness treasure counts, sold magic items count, ransomed prisoners count.

**The load-bearing reason is the GUARDIAN RELATION.** Treasure experience in 1e
is the price of taking wealth **from something that was keeping it from you**.
Every band of the DMG p.85 ratio — 1:1, 5:4, 3:2, 2:1, 3:1, 4+:1 — is set by
*"the degree of challenge the Dungeon Master had the monster(s) pose the treasure
taker."* **There is no band for "no guardian."** Wool bought at the floor from six
willing holders had no guardian, so the ratio is **undefined, not 1:1**.

And PHB p.106's *"major aims"* test finishes it: treasure gained by pursuit of a
class's major aims earns a full share. Buying and selling wool is none of them —
it is the mundane professional work the PHB explicitly *"discarded and subsumed
as taking place on a character's off hours."*

### THE STANDING RULE, stated so it does not have to be re-derived

> **Experience is paid for what you take off an enemy, never for what you already
> own.**

| | XP? |
|---|---|
| Bandits slain or captured defending the caravan | **Yes — full**, on actual hit points |
| The bandits' own coin, gear and camp | **Yes — 1 xp/gp**, ratio adjusted for their strength |
| Bandits ransomed or sold | **Yes — gp:xp ratio** (PHB p.106) |
| The 450 gp capital, the ~1,300 gp sale, the party's profit share | **No.** No guardian |
| Cargo stolen and then retaken by force | **No for the goods; yes for the thieves and their loot.** Otherwise a party farms XP by losing and reclaiming the same cart |
| Trade goods bought south and sold at home | **No** |
| An ambush evaded by wit rather than fought | **A small discretionary award** — DMG p.84, *"the level of challenge, be it thinking or fighting"* |

**Note the line is PROPERTY, not GEOGRAPHY.** Wealth taken off bandits on that
road is full-rate treasure. The distinction is *whose it was before the fight*.

## Training — what a level actually COSTS (DMG p. 86)

> *"Not only must game time be spent by the character desiring advancement, but
> **treasure will have to be spent as well**… **LEVEL OF THE TRAINEE CHARACTER
> × 1,500 = WEEKLY COST DURING STUDY/TRAINING.** The level of the aspiring
> character should be computed at **current (not to be gained) level.**"*

*source: **DMG p. 86**, GAINING EXPERIENCE LEVELS, 300 dpi page render 2026-09-01.*

- **Weeks required = the DM's performance rating**, 1 (Excellent) to 4 (Poor),
  averaged over the adventures since the last level.
- **Training must be under a tutor of the same class**, though *"the tutor might
  possibly accept some combination of gold and service."*
- **XP FREEZES AT THE THRESHOLD.** DMG p.86, in capitals: once a character has
  points equal to or greater than the minimum for the next level, **no further
  experience can be gained until the level is actually gained.**

**For this party, going 1st to 2nd: 1 × 1,500 = 1,500 gp PER WEEK, for one to
four weeks. Between 1,500 and 6,000 gp a character.**

**This is the answer to "what is the wool venture for."** It is not a distraction
from adventuring — **it is the only thing that will ever pay for a level.** Six
characters at even the best rating is 9,000 gp, and the party's entire lifetime
earnings to date are a fraction of that.

## Upkeep — DMG p. 25. **NOT USED IN THIS CAMPAIGN**

**See `rules/equipment.md`, "Cost of living in town" — this rule was set aside by
the player on 2026-08-25 and town costs are 1 gp per person per night.** The
passage is kept here only because the experience section references it; do not
charge it.


> *"Each player character will automatically expend **not less than 100 gold
> pieces per level of experience per month.** This is simply support, upkeep,
> equipment, and entertainment expense. **These costs are to be deducted by the
> Dungeon Master automatically.**"* Henchmen: **100 gp per level per month, in
> addition to all treasure shares.**

*source: **DMG p. 25**, PLAYER CHARACTER EXPENSES, per the agent's 300 dpi render
2026-09-01. **NOT independently re-verified by me — check before charging it.***

Six 1st-level PCs is **600 gp a month** before anything else.
