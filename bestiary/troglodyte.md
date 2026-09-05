# Troglodyte

Reptilian humanoid. Fought twice: expedition 3, corridor 3; expedition 4, area 27.

## Troglodyte stat block

| Field | Value |
|---|---|
| Armor Class | 5 |
| Hit Dice | 2 |
| Move | 12" |
| Number of Attacks | 3 or 1 |
| Damage | 1-3/1-3/2-5 or by weapon |
| Save As | F2 |
| Treasure Type | A |
| Intelligence | low |
| Alignment | Chaotic evil |
| Size | M |
| Number Appearing | 10-100 |
| Surprised On | 2 |
| Surprises On | 4 |
| Morale | 50 |
| XP Value | **36 + 2/hp** |

*source: **Monster Manual p. 97**, read from a 200 dpi page render 2026-08-26.*

**XP value 36 + 2/hp** — *DMG Appendix E, p. 213* (see `rules/experience.md`;
the "+n/hp" is per ACTUAL HIT POINT, not per hit die).

**`Surprises On` is 4, not the usual 2.** This is the single most important row
in the file. Chameleon skin gives troglodytes surprise on **1-4**, and taking
the default cost this campaign two mis-rolled encounters — once in expedition 3,
announced as "party alert" and corrected mid-fight, and once in expedition 4,
caught only because the number was checked again. Feed it to the tool
explicitly:

```bash
python tools/combat.py surprise --who party --surprised-on 4 \
    --why "troglodyte chameleon skin, MM p.97"
```

## Special attacks

| Attack | Trigger | Save | Effect | Duration |
|---|---|---|---|---|
| Revulsion odor | when aroused for battle | vs poison | **-1 Strength per melee round, cumulative**, for 1-6 rounds | loss lasts 10 melee rounds after final effect |
| Javelin | 50% of a group is armed | — | +3 to hit, 2-8 damage | — |

> *"When aroused for battle, troglodytes emit a secretion which smells extremely
> disgusting to humans — including dwarves, elves, gnomes, half-elves and
> halflings. Those humans failing their saving throw versus poison are affected
> by revulsion so as to lose 1 point of strength per melee round for 1-6 rounds,
> cumulative. Loss of strength lasts 10 melee rounds after it has taken final
> effect."* — MM p. 97

Note the odor affects **elves and halflings too** — the MM's "humans" is
inclusive here and says so. Tristle is not exempt.

## Special defences

| Defence | Detail |
|---|---|
| Chameleon skin | changes to grey, brown or green; **surprise on 1-4** |
| — but | *"unless they are angry and excreting their stench"* — once it stinks, the camouflage is gone and it surprises normally |
| Infravision | 9" (90 ft) — it sees a lantern long before the lantern sees it |

**The camouflage and the stench are mutually exclusive**, which the campaign
house rule already half-covers: chameleon surprise is *"by sight only"* and
conceals nothing from infravision, since it cannot hide body heat
(`rules/exploration.md`).

## Weapons carried

50% of any group is armed. Of the armed half: javelin ×2 **25%**, stone battle
axe 10%, stone morning star 10%, sword 5%. The rest fight with claws and teeth.

## Module conversion — B1

| | B1 prints | Monster Manual | Use |
|---|---|---|---|
| Armor Class | 5 | 5 | agree |
| Hit Dice | 2 | 2 | agree |
| Damage | 1-4/1-4/1-4 | **1-3/1-3/2-5** | **MM** — two claws and a bite, not three identical claws |
| Move | 120' (40') | 12" | same rate, Basic notation |
| Morale | ML 9 | DMG percentage, base 50% | **DMG** |

## Play record

| Expedition | Where | hp | Outcome |
|---|---|---|---|
| 3 | corridor 3, turn 10 wandering | 6 | Killed. Surprised the party on a 3. Torsat 6→1, Yrtone 7→1. Dave and Torsat both **failed** stench saves; Dave lost 6 rounds of cumulative -1 STR, 18/26 down to 12. 50 XP. |
| 4 | area 27, round 64 wandering | 6 | Killed in one round. Surprised the party on a 3 again. Both stench saves **made**. All three of its surprise attacks missed AC 3. Died to Dave's rear attack for 11; **initiative was tied, so it still struck as it fell** and took Torsat 6→0. |

**The lesson from both:** AC 3 turns most of its attacks aside, but it gets
three of them every round and one landing hit is most of a 1st-level fighter.
