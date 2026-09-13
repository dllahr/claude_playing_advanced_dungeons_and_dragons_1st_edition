"""Surprise, which this campaign ran wrong for NINE EXPEDITIONS.

`rules/exploration.md` carried one sentence -- *"a surprised party loses 1
segment (or more) of action"* -- and every ambush from expedition 1 to
expedition 9 was adjudicated off it as "surprised or not, one free round for
whoever surprised." Two separate rules were missing from that sentence:

  THE COUNT      the lost segments are the DIFFERENCE of the two dice
                 (DMG p.61), not the fact of being surprised. Day 70's
                 troglodyte was logged "MUTUAL, cancels" on 2 against 2 --
                 which is the difference-of-0 row, correct, and the SAME rule
                 that gives 2 segments on a 4 against a 2. The player
                 remembered the outcome as a house rule; it was the book.

  WHAT ONE BUYS  "as if the segment were an entire round" (DMG p.62). Two lost
                 segments is TWO FULL ROUNDS of attacks. This is the half that
                 was actually missing, and it is the harsh one.

And DEXTERITY IN SURPRISE (DMG p.62) had never once been applied -- every
surprise roll in rolls.tsv carries adjust=0 -- although `rules/abilities.md`
has quoted the PHB's own *"applies to both surprise situations and missile
combat attacks"* the entire time. It sat in the cache, correct and unused.

Adopted in full by the player 2026-09-13, day 79, mid-ambush at (24,37).

The lesson is the one `test_lane_rule.py` already carries: A PARAPHRASE LOSES
CONDITIONS -- THAT IS WHAT A PARAPHRASE IS FOR. So the figures live in exactly
one file and this test refuses to let any other carry them.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import rules                                                     # noqa: E402


def table():
    t = rules.find('How many segments')
    assert t, 'the difference table is gone from rules/combat.md'
    return t


# ------------------------------------------------------- the count

def test_lost_segments_are_the_DIFFERENCE_of_the_dice():
    t = table()
    got = dict(zip(t['columns'], t['rows'][0]))
    assert got['Surprise dice difference'].strip('*') == 'Lost segments'
    for d in ('0', '1', '2', '3'):
        assert got[d].strip('*') == d, (d, got)
    assert 'DMG p. 61' in t['source'], t['source']


def test_both_surprised_cancels_ONLY_when_the_dice_are_EQUAL():
    """The reading the campaign had been carrying -- "both surprised means
    nobody is surprised" -- is the difference-of-0 row and nothing more. On a 4
    against a 2 it is 2 lost segments, not zero."""
    body = open(os.path.join(ROOT, 'rules', 'combat.md'),
                encoding='utf-8').read()
    assert 'equally' in body and 'difference' in body.lower()
    assert 'MUTUAL, cancels' in body, (
        'the day-70 precedent should be quoted here -- it is the reason this '
        'looks like a house rule, and it is the same rule')


def test_a_segment_buys_a_WHOLE_ROUND_of_attacks():
    """The half that was genuinely missing, and the one that kills characters."""
    body = open(os.path.join(ROOT, 'rules', 'combat.md'),
                encoding='utf-8').read()
    assert 'as if the segment were an entire round' in body
    assert 'three times the normal rate' in body, (
        'missiles already in hand fire at 3x in a surprise segment, DMG p.62')


# ------------------------------------------------------- dexterity

def test_dexterity_in_surprise_is_PER_INDIVIDUAL_and_is_not_an_initiative():
    body = open(os.path.join(ROOT, 'rules', 'combat.md'),
                encoding='utf-8').read()
    assert 'as far as the individual only is concerned' in body
    assert 'not a won initiative' in body.lower() or \
           'A negated segment is not a won initiative' in body, (
        'The DMG grants the segments of initiative to the NON-SURPRISED SIDE. '
        'Dexterity only removes one individual\'s inactivity -- he acts WITHIN '
        'those segments, not BEFORE them, and there is no initiative roll '
        'inside a surprise segment. The player asked this exact question on '
        'day 79 and the answer must not drift.')


def test_the_two_characters_it_touches_are_named_and_the_rest_are_zero():
    """Tristle +3 and Dellie -2. Everyone else in the party is in the 0 band,
    so if a third name ever appears here somebody has changed a DEX score."""
    t = rules.find('Dexterity')
    assert t, 'the Dexterity table is gone from rules/abilities.md'
    dex = {r[0].strip(): r[1].strip() for r in t['rows']}
    assert dex['18'] == '+3', dex['18']
    assert dex['4'] == '-2', dex['4']
    for score in ('10', '11', '12', '13', '14'):
        assert dex[score] == '0', (score, dex[score])


# ------------------------------------------ one file, and only one

def test_no_other_markdown_file_states_a_lost_segment_FIGURE():
    """`rules/exploration.md` is where the wrong sentence lived for nine
    expeditions. It now points here and carries no number of its own."""
    pat = re.compile(r'lose[sd]?\s+1\s+segment|loses?\s+one\s+segment', re.I)
    for sub in ('rules', 'campaign', '.'):
        d = os.path.join(ROOT, sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.md') or fn == 'combat.md':
                continue
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            body = open(p, encoding='utf-8').read()
            for m in pat.finditer(body):
                line = body[:m.start()].count('\n') + 1
                ctx = body[max(0, m.start() - 200):m.start() + 120]
                assert '>' in ctx and 'used to read' in ctx, (
                    '%s:%d restates the surprise figure. It belongs in '
                    'rules/combat.md alone -- this is the sentence that was '
                    'wrong for nine expeditions.' % (os.path.join(sub, fn),
                                                     line))


def test_exploration_points_at_combat_instead_of_paraphrasing():
    body = open(os.path.join(ROOT, 'rules', 'exploration.md'),
                encoding='utf-8').read()
    i = body.find('## Surprise')
    assert i > 0
    section = body[i:i + 900]
    assert 'rules/combat.md' in section, (
        'the exploration.md surprise section must POINT at the full procedure, '
        'not summarise it')
