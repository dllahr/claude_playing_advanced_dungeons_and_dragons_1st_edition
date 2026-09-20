"""Experience totals — and a 0-level character, who has no next level.

Brand was given a stat line mid-session on day 99 and `characters.tsv` carried
`-` in next_level, because 1e has NO 0-level-to-1st progression: 1st level
begins at 0 xp and the gate is capacity, not points (rules/zero-level.md).

`int('-')` crashed characters(), which crashed totals(), which crashed audit.py,
which BLOCKED THE COMMIT. The pre-commit hook caught it and nothing else would
have — the crash was three layers below the thing being committed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import xp                                                        # noqa: E402


def test_a_dash_next_level_parses_as_none_not_a_crash():
    assert xp._threshold('-') is None
    assert xp._threshold('') is None
    assert xp._threshold(None) is None
    assert xp._threshold('  ') is None
    assert xp._threshold('2000') == 2000
    assert xp._threshold(' 1251 ') == 1251


def test_the_live_roster_loads_with_a_zero_level_character_in_it():
    chars = xp.characters()
    assert chars, 'the real characters.tsv must parse'
    thresholdless = [n for n, c in chars.items() if c['next_level'] is None]
    for n in thresholdless:
        assert chars[n]['cls'].lower() in ('normal man', 'normal men'), (
            '%s has no next_level but is class %r -- only a 0-level normal man '
            'may lack one' % (n, chars[n]['cls']))


def test_every_classed_character_still_has_a_threshold():
    """The fix must not let a real class quietly lose its next level."""
    for n, c in xp.characters().items():
        if c['cls'].lower() in ('normal man', 'normal men'):
            continue
        assert isinstance(c['next_level'], int) and c['next_level'] > 0, n


def test_totals_still_compute_with_a_thresholdless_character():
    """The crash was in characters(), so every xp figure went down with it."""
    tot, detail = xp.totals()
    assert tot, 'totals must not be empty'
    assert all(v >= 0 for v in tot.values())
    assert detail


def test_a_zero_level_character_starts_at_zero_experience():
    """He is present and in the marching order; he has simply earned nothing.

    B1 pays only on a living exit, so the gnoll and the four orcs are both
    still outstanding when this runs.
    """
    tot, _ = xp.totals()
    zero = [n for n, c in xp.characters().items() if c['next_level'] is None]
    for n in zero:
        assert n in tot, '%s must appear in the totals, not be skipped' % n
