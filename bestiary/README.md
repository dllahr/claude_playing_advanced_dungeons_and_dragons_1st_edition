# bestiary/ — the campaign's own Monster Manual

One markdown file per creature, in exactly the format of `rules/*.md`, parsed by
`tools/bestiary.py` (which is `tools/rules.py` pointed at this directory rather
than a second parser).

```bash
python tools/bestiary.py --list
python tools/bestiary.py troglodyte
python tools/bestiary.py troglodyte --field "Surprises On"

python tools/combat.py monster --creature troglodyte --target-ac 3 --attacks 2
python tools/treasure.py --monster troglodyte --lair
```

## Why

Every stat block here was read off a Monster Manual **page render** — find the
page, render it, read it. Before this directory existed that work was thrown
away after each fight and redone at the next one, and in between the numbers
lived only in the DM's memory. That is not a hypothetical cost:

- **Troglodyte surprise was got wrong twice**, in two different expeditions,
  because the chameleon range is 1–4 and the default is 1–2.
- **A berserker was narrated shrugging off 7 damage on 5 hit points.**
- **`tools/treasure.py` carried a hand-typed table of treasure types that was
  wrong for two of its six creatures** — orc lair "D" where the MM says
  C, O, Q (×10), S; kobold lair "Q, D" where the MM says O, Q (×5). Nothing ever
  compared them to the book. That table is deleted; the letters now come from
  these files.

## What every file carries

| Section | Heading must be | Why |
|---|---|---|
| Stat block | `## <Name> stat block` | `bestiary.py` finds it by that phrase |
| Special attacks | `## Special attacks` | trigger / save / effect / duration as **rows** — a paragraph is not readable mid-round |
| Special defences | `## Special defences` | immunities, and what harms it |
| Morale | `## Morale` | base score, or **that it never checks** |
| Module conversion | `## Module conversion — B1` | B1 is statted for Basic D&D and disagrees; keep both so you can see which book a number came from |
| Play record | `## Play record` | what it actually did to this party |
| Provenance | a `*source:*` line under the stat block | MM page and render date, same standard as `rules/` |

Two fields in the stat block are load-bearing and easy to leave out:

- **`Surprised On`** — how easily *it* is surprised (usually 2).
- **`Surprises On`** — how easily it surprises *you*. **This is not always 2.**
  Feed it to `combat.py surprise --surprised-on N --why "..."` every time.

## Adding a creature

1. Find the entry: search the MM text layer for a line that is just the name and
   is followed by `FREQUENCY`.
2. **Render the page and read it.** Never transcribe a stat block from the OCR
   text layer — digits corrupt silently in these scans and a stat block is
   nothing but digits.
3. Copy an existing file's headings exactly. The parser finds tables by heading,
   deliberately, so a renamed heading fails loudly instead of returning the
   wrong table.
4. Cite the page and the render date.
