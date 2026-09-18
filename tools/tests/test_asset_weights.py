"""*** assets.tsv's WEIGHTS ARE A CACHE OF rules/equipment.md, AND rules/ WINS.

This file exists because four of them were not, and nobody noticed for weeks.

Found on day 96, when the player asked for the weight of 200 iron spikes and how
much of a cart they would fill:

    iron_spike    50 -> 10     a 5x error, and the worst one: 200 spikes
                               weighed 1,000 lb instead of 200
    oil_flask    100 -> 20     5x
    lantern      300 -> 60     5x
    torch        100 -> 25     4x, and equipment.md ALREADY carried this item
                               as a known OCR slip ("Torch 60 -> 25"). assets.tsv
                               held a third figure agreeing with neither

THREE OF THE FOUR WERE EXACTLY 5x. That is not three typos, it is one habit --
and the giveaway is that the six weights nobody had reason to guess at
(rope, pole, backpack, waterskin, both rations) were all exactly right.

WHY IT SURVIVED: `assets.tsv` is hand-authored and, in its own header's words,
"can be WRONG but it cannot go STALE" -- so nothing recomputed it and nothing
compared it to anything. Every other number in this campaign is derived from a
log by a tool that would have screamed. These were typed once and trusted.

CLAUDE.md: "No rules table is written twice... A table restated in Python would
be a second copy that nobody re-checks against the book." assets.tsv IS that
second copy for these items. It cannot be deleted -- inventory.py needs a weight
per asset id -- so it is PINNED TO THE BOOK BY THIS TEST INSTEAD.

*** WHAT THIS INVALIDATES: L052's encumbrance ceiling of 12,148 gp-weight was
*** computed from these figures and is therefore WRONG AND TOO HIGH. The loop
*** note says the figure is "a CEILING on the load and not a measurement"; it is
*** now a ceiling on a ceiling. No past expedition is retroactively rerated -- a
*** rules correction is prospective (CHECKLIST) -- but nothing new should be
*** computed off the old numbers.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, 'tools')
sys.path.insert(0, TOOLS)

from tsvlog import read_tsv                                       # noqa: E402

# assets.tsv id -> the row heading it must match in DMG p.225 Appendix O.
# A `None` means the book does not price its weight and assets.tsv is the only
# source; those are deliberately NOT checked rather than silently blessed.
APPENDIX_O = {
    'iron_spike':    'spike',
    'oil_flask':     'flask, full',
    'lantern':       'lantern',
    'rope_50ft':     "rope, 50'",
    'ten_foot_pole': "pole, 10'",
    'backpack':      'backpack',
    'torch':         'torch',
    'candle':        'candle',
    'tinder_box':    'tinderbox',
    'mirror':        'mirror',
    'waterskin':     'waterskin, full',
    'rations_iron':  'rations, iron',
    'rations_std':   'rations, standard',
    'quiver':        'quiver',
    'short_bow':     'bow, short',
}


def appendix_o():
    """The weight table, parsed OUT OF rules/equipment.md -- not restated here.

    Writing the numbers into this file would recreate the exact bug it tests
    for: a second copy that nobody re-checks against the book.
    """
    txt = open(os.path.join(ROOT, 'rules', 'equipment.md')).read()
    sec = txt.split('## Encumbrance of standard items — gear')[1].split('*source:')[0]
    out = {}
    for line in sec.splitlines():
        cells = [c.strip().strip('*').strip()
                 for c in line.strip().strip('|').split('|')]
        if len(cells) != 5:
            continue
        for name, w in ((cells[0], cells[1]), (cells[3], cells[4])):
            w = w.replace(',', '')
            if re.fullmatch(r'\d+', w):
                out[name.lower()] = int(w)
    return out


def assets():
    return {r['id']: r for r in read_tsv(os.path.join(ROOT, 'campaign',
                                                      'assets.tsv'))}


def test_the_weight_table_still_parses_out_of_the_rules_file():
    """If equipment.md's heading is renamed this must FAIL, not pass vacuously.

    rules.py's parser finds tables by heading deliberately, for exactly this
    reason -- so a rename breaks loudly instead of returning nothing.
    """
    o = appendix_o()
    assert len(o) > 30, 'only %d weights parsed -- the table moved' % len(o)
    assert o['spike'] == 10 and o['flask, full'] == 20


def test_every_cached_weight_agrees_with_DMG_appendix_O():
    """*** THE ONE THAT MATTERS. *** Four were wrong on day 96."""
    o, a = appendix_o(), assets()
    wrong = []
    for aid, heading in APPENDIX_O.items():
        if aid not in a:
            continue                      # asset retired; not this test's job
        have = (a[aid].get('weight') or '').strip()
        if not have:
            continue                      # blank is honest -- see the header
        if heading not in o:
            wrong.append('%s: %r is not a row in Appendix O' % (aid, heading))
            continue
        if abs(float(have) - o[heading]) > 0.001:
            wrong.append('%s: assets.tsv says %s, DMG p.225 says %d (x%.1f)'
                         % (aid, have, o[heading], float(have) / o[heading]))
    assert not wrong, ('assets.tsv has drifted from rules/equipment.md:\n  '
                       + '\n  '.join(wrong))


def test_the_four_day_96_corrections_specifically():
    """Named, so a regression says WHICH habit came back rather than 'a weight'."""
    a = assets()
    for aid, want in (('iron_spike', 10.0), ('oil_flask', 20.0),
                      ('lantern', 60.0), ('torch', 25.0)):
        assert float(a[aid]['weight']) == want, (
            '%s is back to the wrong weight. Three of the four originals were '
            'EXACTLY 5x the book; if this fails, check whether the others '
            'moved together.' % aid)


def test_a_weight_is_never_a_bare_number():
    """gp-weight and pounds differ by 10x and the SD barrel proved it hurts.

    assets.tsv's own header: "A bare number in one column would be a unit kept
    in somebody's head, which is the shape of every error this project is
    about."
    """
    for aid, r in assets().items():
        if (r.get('weight') or '').strip():
            assert (r.get('weight_unit') or '').strip(), \
                '%s carries a weight with no unit' % aid
