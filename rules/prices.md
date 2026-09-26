# Prices and wages — the working price board

Parsed by `tools/rules.py`. **Set on day 121 (2026-09-25) at the player's word, so that
labour, food and rations do not have to be re-extracted from the books each time.**

**Base unit: the copper piece.** 1 sp = 10 cp; 1 gp = 200 cp (PHB p. 35, COIN EXCHANGE VALUE; `rules/equipment.md`).
A price in this file is in cp, so a wage and a loaf can be compared without converting.

**Where a number came from is in its own column.** Three kinds, and they are not the same
kind of number:

- **PHB / DMG** — printed in the books. `rules/equipment.md` holds the transcription with the
  page render; **these rows are copies of it** and equipment.md is the authority if the two
  ever differ.
- **CAMPAIGN** — a house rule the player set and has used since (e.g. the Inn's board).
- **DM CALL** — nothing in the books prices it; the number was chosen and the player
  approved it. Change it here and nowhere else.

## The price board

| Item | Category | Price (cp) | Unit | Source | Note |
|---|---|---|---|---|---|
| Bearer / porter | wage | 10 | per day | DMG p. 28 | 1 sp; 1 gp a month with quarters |
| Linkboy | wage | 10 | per day | DMG p. 28 | 1 sp |
| Pack handler | wage | 20 | per day | DMG p. 28 | 2 sp |
| Valet / lackey (messenger) | wage | 30 | per day | DMG p. 28 | 3 sp |
| Carpenter | wage | 30 | per day | DMG p. 28 | 3 sp, plus 10% of the price of items fashioned |
| Mason | wage | 40 | per day | DMG p. 28 | 4 sp |
| Teamster | wage | 50 | per day | DMG p. 28 | 5 sp; a man hired to drive somebody else's cart |
| Leather worker | wage | 20 | per day | DMG p. 28 | 2 sp |
| Tailor | wage | 20 | per day | DMG p. 28 | 2 sp |
| Limner | wage | 100 | per day | DMG p. 28 | 10 sp |
| Coll's hand (semi-skilled crew) | wage | 15 | per day | CAMPAIGN, day 121 | 1.5 sp, the upper end of medieval unskilled labour (1-1.5 silver pennies) |
| Rations, standard | food | 600 | per person-week | PHB p. 35 | 3 gp; about 43 cp a day. Packed, no fire, keeps a week or so |
| Rations, iron | food | 1000 | per person-week | PHB p. 35 | 5 gp; keeps a month |
| Ale, pint | food | 10 | per pint | PHB p. 35 | 1 sp, ordinary ale |
| Wine, pint, good | food | 100 | per pint | PHB p. 35 | 10 sp |
| Merchant's meal | food | 10 | per meal | PHB p. 35 | 1 sp |
| Camp food (raw, cooked by the eater) | food | 6.5 | per person-day | DM CALL, day 121 | About two-thirds of a 1 sp wage; medieval labour spent up to two-thirds on food. **The raw-food price, about a sixth of rations** |
| Flour | staple | 2 | per lb | DM CALL, day 121 | Fresh. Needs a cook and a fire |
| Lard | staple | 4 | per lb | DM CALL, day 121 | Fresh |
| Salt | staple | 8 | per lb | DM CALL, day 121 | Fresh |
| Seasoning (dried herbs and spice) | staple | 12 | per lb | DM CALL, day 121 | Fresh; the herbs end. True spice would be dearer |
| Wool-headed ale (strong SD stock ale) | food | 30 | per pint | CAMPAIGN, day 71 | 3 sp: Holt's board price, "threepence a pint", the name the party gave it, and what the party paid for a round of nine (27 sp, transcript line 29932). Three times ordinary ale. **A 36-gallon barrel is 288 pints, 43.2 gp gross** (an earlier '85 gp' figure counted the pints twice) |
| Lodging and board, the Inn | lodging | 200 | per person-night | CAMPAIGN, since expedition 4 | 1 gp, the traveller's rate for the party. Not the workers' rate |

*source: wage rows **DMG p. 28**, STANDARD HIRELINGS TABLE, `rules/equipment.md`; food and drink rows **PHB p. 35**, EQUIPPING THE CHARACTER, `rules/equipment.md`; the rest are the CAMPAIGN and DM CALL rows marked in the Source column, all set or approved by the player on day 121 unless a day is given.*

## Stale stock — the discount

| Item | Category | Factor | Unit | Source | Note |
|---|---|---|---|---|---|
| Stale but sound goods from Quasqueton | discount | 0.75 | of the fresh price | DM CALL, day 121 | B1 area 10: *"usable or edible still, but they nonetheless have an off-taste which suggests staleness."* A quarter off. The player: stale goods are worth less |

*source: **DM CALL, day 121**, set at the player's word (stale barrels are priced below fresh); the quotation is B1 area 10, p. 12.*

## The arithmetic that fixed the food price

A working man's wage is **10 cp a day** (bearer, DMG p. 28). Medieval unskilled labour earned
one to one and a half silver pennies a day and spent up to two-thirds of it on food, so a
day's food is **6 to 7 cp** — the **6.5 cp** above. A pound of flour at 2 cp, a little lard,
salt and pulses get there. **Standard rations at 43 cp a day cost about six and a half times
the raw food:** that is the price of packing, keeping and needing no fire and no cook, and it
is left at the book's figure on purpose.

*source: **DM CALL / player's reasoning, day 121**; the labour figures are the player's, from a search, and are an anchor, not a citation.*
