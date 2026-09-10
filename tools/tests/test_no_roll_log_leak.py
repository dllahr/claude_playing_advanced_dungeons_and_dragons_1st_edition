"""The regression for the roll-log leak. Lives here because pytest does not
collect test functions out of conftest.py -- which the DM discovered by noticing
the test count had not moved after adding one.

THE BUG: `pytest` appended 31 rows to `campaign/rolls.tsv` on every run, for as
long as those tests had existed. `dice.roll()` logs by DEFAULT, which is correct
for play -- CLAUDE.md treats that file as the evidence -- so any test exercising
combat.py, clock.py or dice.py through their real paths wrote into the campaign's
audit trail. Found 2026-09-10 while checking the log was current before a compact:
its tail held attack rolls for a giant centipede and an orc that no character had
ever met.

The fix is the session fixture in conftest.py. This is the alarm on it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import dice                                                      # noqa: E402

CAMPAIGN_LOG = os.path.join(os.path.dirname(TOOLS), 'campaign', 'rolls.tsv')


def test_dice_is_not_pointed_at_the_campaign_log_during_tests():
    assert os.path.abspath(dice.ROLLS) != os.path.abspath(CAMPAIGN_LOG), (
        'dice.ROLLS points at the real campaign roll log during tests. Every '
        'pytest run will append to the audit trail CLAUDE.md treats as evidence. '
        'The session fixture in conftest.py is missing or broken.')


def test_a_logged_roll_does_not_reach_the_campaign_log():
    """Stronger than checking the path: actually roll and measure the file."""
    before = os.path.getsize(CAMPAIGN_LOG)
    dice.roll('d20', reason='leak check -- must not reach campaign/rolls.tsv')
    assert os.path.getsize(CAMPAIGN_LOG) == before, (
        'a logged roll reached campaign/rolls.tsv from inside the test suite')
