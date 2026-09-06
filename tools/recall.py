#!/usr/bin/env python3
"""Every logged event for one character, in order, out of every campaign TSV.

**This exists because the DM kept inventing the past.**

Across one session (2026-09-06) nine separate factual errors were caught by the
player, and sorting them showed a single cause. Present-tense play was fine --
rolls, rules lookups, encumbrance, saves -- because all of that goes to the
books and the logs. What broke every time was *retrospective colour*: "she
remembers", "he'd been", "when you fell". Three of the nine were outright
invention (a distance to Ede, a document that never existed, Ista going under
twice in the pool). Three more were the DM believing his own prose summary in
`campaign/npcs.md` instead of the log underneath it.

The rule that came out of it is in CHECKLIST.md and is short:

    **The TSVs are evidence. The prose files -- including the DM's own scene
    write-ups -- are an INDEX. Never quote an event from an index.**

CLAUDE.md already said never to quote a running *total* from a prose file. This
is the same rule for *events*, and it kept being broken for a boring reason:
checking was awkward. One character's history is scattered across seven files
with seven different schemas, and nobody greps seven files mid-scene. So the
fix is the same one this project already applied to hit points and lantern oil
-- when the right thing is hard, build the thing that makes it easy.

    python tools/recall.py Ista
    python tools/recall.py Ista --exped 6
    python tools/recall.py Frython Blartho --kind hp

A note on ORDERING, because it would otherwise be a way to invent facts again.
Many rows carry no turn or round (`hp_log` in particular is often blank). Those
rows are ordered by their position in the file, which is append order and
therefore chronological -- but the turn column is printed as `?`, never as the
turn of the row above. **The sort is a convenience; only the printed values are
evidence.**
"""
import argparse
import os
import re
import sys

import tsvlog

CAMPAIGN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'campaign')

# One entry per log: which columns name a character, which column carries the
# clock, and what is worth printing. Files with no character column at all
# (clock.tsv, party.tsv) are searched in their free text only -- the party's
# position is a fact about the party, not about a person.
LOGS = [
    dict(file='hp_log.tsv',        kind='hp',      who=['who'],
         clock='turn',  show=['kind', 'delta', 'reason']),
    dict(file='spells.tsv',        kind='spell',   who=['who'],
         clock='round', show=['spell', 'event', 'note']),
    dict(file='light.tsv',         kind='light',   who=['who'],
         clock='round', show=['source', 'kind', 'what', 'fuel', 'note']),
    dict(file='world_changes.tsv', kind='world',   who=['who'],
         clock='turn',  show=['scope', 'target', 'change', 'item', 'qty', 'note']),
    dict(file='encounters.tsv',    kind='xp',      who=['earned_by'],
         clock=None,    show=['kind', 'encounter', 'xp', 'notes']),
    dict(file='rolls.tsv',         kind='roll',    who=[],
         clock='turn',  show=['notation', 'total', 'reason']),
    dict(file='clock.tsv',         kind='clock',   who=[],
         clock='round', show=['kind', 'anchor', 'detail', 'note']),
    dict(file='party.tsv',         kind='party',   who=[],
         clock='turn',  show=['x', 'y', 'why']),
]

# earned_by and who sometimes say "all" or "party" rather than listing people.
EVERYONE = {'all', 'party', 'everyone'}


def _mentions(row, name, who_cols):
    """Does this row concern `name`? Returns 'named', 'all', 'text' or None.

    A dedicated character column is matched exactly (case-insensitively) against
    each comma-separated element, so `Dellie` never matches because somebody
    else's note mentions her. Everything else is matched on a word boundary in
    the free text, which is how a roll's `reason` or a world change's `note`
    gets found. The two are reported separately so the caller can tell a fact
    ABOUT someone from a fact that merely MENTIONS them.
    """
    for col in who_cols:
        raw = (row.get(col) or '').strip()
        if not raw:
            continue
        parts = [p.strip().lower() for p in raw.split(',')]
        if name.lower() in parts:
            return 'named'
        if any(p in EVERYONE for p in parts):
            return 'all'
    pattern = r'\b%s\b' % re.escape(name)
    for col, val in row.items():
        if col in who_cols:
            continue
        if val and re.search(pattern, val, re.I):
            return 'text'
    return None


def gather(name, campaign=CAMPAIGN, exped=None, kinds=None, include_all=True):
    """Every row concerning `name`, as dicts, sorted for reading."""
    found = []
    for spec in LOGS:
        if kinds and spec['kind'] not in kinds:
            continue
        path = os.path.join(campaign, spec['file'])
        rows = tsvlog.read_tsv(path, missing_ok=True)
        for seq, row in enumerate(rows):
            how = _mentions(row, name, spec['who'])
            if how is None or (how == 'all' and not include_all):
                continue
            e = (row.get('exped') or '').strip()
            if exped is not None and e != str(exped):
                continue
            clock_col = spec['clock']
            raw_clock = (row.get(clock_col) or '').strip() if clock_col else ''
            found.append(dict(
                kind=spec['kind'], file=spec['file'], how=how, seq=seq,
                when=(row.get('when') or '').strip(),
                exped=e,
                clock=raw_clock,
                show=[(c, (row.get(c) or '').strip()) for c in spec['show']
                      if (row.get(c) or '').strip()],
            ))
    # Expedition first, then the clock where a row has one. Rows without a clock
    # keep their file order via `seq`; their turn stays UNKNOWN when printed.
    def key(r):
        try:
            e = int(r['exped'])
        except ValueError:
            e = -1
        try:
            c = int(r['clock'])
            known = 0
        except ValueError:
            c, known = 0, 1
        return (e, c, known, r['file'], r['seq'])
    found.sort(key=key)
    return found


def render(name, rows):
    if not rows:
        return 'recall: nothing logged for %r.\n' % name
    out = ['%s -- %d logged event(s). THIS IS THE EVIDENCE; prose files are not.'
           % (name, len(rows)), '']
    last_exped = object()
    for r in rows:
        if r['exped'] != last_exped:
            last_exped = r['exped']
            out.append('=== expedition %s ===' % (r['exped'] or '-'))
        clock = r['clock'] or '?'
        mark = {'named': ' ', 'all': '*', 'text': '~'}[r['how']]
        body = '  '.join('%s=%s' % (c, v) for c, v in r['show'])
        out.append('%s %-6s %-5s %-6s %s' % (mark, clock, r['kind'], r['when'], body))
    out += ['', "  ' ' names them   '*' an 'all'/'party' row   '~' mentioned in free text",
            '  turn `?` means the row carries no clock; order is file order, not a known turn.']
    return '\n'.join(out) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(
        description='Every logged event for a character, out of the TSVs.')
    p.add_argument('names', nargs='+', help='character name(s)')
    p.add_argument('--exped', help='restrict to one expedition')
    p.add_argument('--kind', action='append',
                   help='restrict to hp/spell/light/world/xp/roll/clock/party')
    p.add_argument('--no-all', action='store_true',
                   help="drop rows that say 'all' or 'party' instead of naming")
    a = p.parse_args(argv)
    for n in a.names:
        sys.stdout.write(render(n, gather(n, exped=a.exped, kinds=a.kind,
                                          include_all=not a.no_all)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
