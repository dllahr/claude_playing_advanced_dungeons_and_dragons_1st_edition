"""`recall.py` -- and the specific error it was built to prevent.

The load-bearing test here is `test_ista_was_healed_before_blartho_bled_again`.
On 2026-09-06 the DM narrated Ista going under twice in the pool with nobody
noticing, and the player caught it: `hp_log.tsv` says she was pulled out and
given the party's FIRST cure light wounds, and that Blartho bled an extra round
after that. The fabricated version was the exact opposite of the record.

That test reads the real campaign log rather than a fixture, deliberately. It
asserts an ORDER that actually happened at the table, so if a future edit ever
reverses those rows -- or `gather()` stops preserving append order -- it fails
loudly instead of letting the wrong story be told twice.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
CAMPAIGN = os.path.join(os.path.dirname(TOOLS), 'campaign')
sys.path.insert(0, TOOLS)

import recall                                                   # noqa: E402


@pytest.fixture
def logs(tmp_path):
    """A miniature campaign directory with two of the real schemas."""
    (tmp_path / 'hp_log.tsv').write_text(
        '# Hit points. APPEND ONLY.\n'
        'when\texped\tturn\twho\tkind\tdelta\treason\n'
        '2026-01-01\t6\t\tIsta\tdamage\t-4\tthe fall\n'
        '2026-01-01\t6\t\tIsta\theal\t4\tYrtone at the pool edge\n'
        '2026-01-01\t6\t\tBlartho\tdamage\t-1\tbleeding, hauled clear after\n'
        '2026-01-01\t5\t10\tIsta\tdamage\t-1\tan earlier expedition\n')
    (tmp_path / 'encounters.tsv').write_text(
        '# Encounters. APPEND ONLY.\n'
        'exped\tkind\tencounter\txp\tearned_by\tsource\tnotes\n'
        '6\tmonster\torc\t54\tall\tMM\tnobody named, everybody paid\n'
        '6\tmonster\trat\t10\tTristle,Dellie\tMM\tshe was not on this one\n')
    (tmp_path / 'rolls.tsv').write_text(
        '# Rolls.\n'
        'when\texped\tturn\tnotation\tdice\tmodifier\ttotal\thidden\treason\n'
        '2026-01-01\t6\t5\td20\t11\t0\t11\t\tIsta attacks the rat\n')
    return str(tmp_path)


def test_finds_rows_that_name_the_character(logs):
    rows = recall.gather('Ista', campaign=logs)
    kinds = [r['kind'] for r in rows]
    assert 'hp' in kinds and 'roll' in kinds


def test_expedition_filter(logs):
    assert all(r['exped'] == '6' for r in recall.gather('Ista', campaign=logs, exped=6))
    assert recall.gather('Ista', campaign=logs, exped=5)


def test_an_all_row_is_marked_not_silently_claimed(logs):
    """`earned_by=all` concerns her, but it does not NAME her -- say which."""
    hows = {r['how'] for r in recall.gather('Ista', campaign=logs) if r['kind'] == 'xp'}
    assert hows == {'all'}
    assert not recall.gather('Ista', campaign=logs, kinds=['xp'], include_all=False)


def test_a_named_column_does_not_match_a_bare_substring(logs):
    """`earned_by=Tristle,Dellie` must not be read as an Ista row.

    The comma list is matched element by element. A substring search would be
    the same class of bug as the one this tool exists to stop.
    """
    xp = [r for r in recall.gather('Dellie', campaign=logs) if r['kind'] == 'xp']
    assert sorted(r['how'] for r in xp) == ['all', 'named']
    named = [r for r in xp if r['how'] == 'named']
    assert dict(named[0]['show'])['encounter'] == 'rat'

    # And the converse: Ista is NOT in that comma list and must not appear.
    ista_xp = [r for r in recall.gather('Ista', campaign=logs) if r['kind'] == 'xp']
    assert all(r['how'] != 'named' for r in ista_xp)


def test_free_text_mention_is_distinguished_from_being_named(logs):
    """Blartho's row mentions nobody else; Ista's roll names her in free text."""
    roll = [r for r in recall.gather('Ista', campaign=logs) if r['kind'] == 'roll']
    assert roll and roll[0]['how'] == 'text'


def test_rows_without_a_clock_report_unknown_not_the_row_above(logs):
    """Ordering may guess. The PRINTED turn may not -- that is how facts get invented."""
    text = recall.render('Ista', recall.gather('Ista', campaign=logs))
    assert '?' in text
    assert 'the fall' in text


def test_ista_was_healed_before_blartho_bled_again():
    """THE REGRESSION. Reads the real log, because the real log is the point.

    Order in `campaign/hp_log.tsv`: Ista takes 4 (on a 4-hp maximum, so she is
    at ZERO), Ista is healed at the pool edge, and only THEN does Blartho lose
    another point bleeding. She was got out first and given the first spell.
    """
    rows = recall.gather('Ista', campaign=CAMPAIGN, exped=6, kinds=['hp'])
    reasons = [dict(r['show']).get('reason', '') for r in rows]
    fall = next(i for i, s in enumerate(reasons) if '40-ft fall' in s)
    cure = next(i for i, s in enumerate(reasons) if 'pool edge' in s)
    assert fall < cure, 'Ista was healed at the pool edge AFTER the fall'

    blartho = recall.gather('Blartho', campaign=CAMPAIGN, exped=6, kinds=['hp'])
    bled = [dict(r['show']).get('reason', '') for r in blartho]
    assert any('bleeding out at -2' in s for s in bled), (
        'the row that proves Blartho bled an extra round has gone')
