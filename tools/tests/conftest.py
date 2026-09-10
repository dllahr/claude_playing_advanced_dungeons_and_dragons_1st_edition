"""Keep the test suite out of the campaign's own records.

**This exists because `pytest` was appending 31 rows to `campaign/rolls.tsv` on
every single run**, and had been doing it for as long as those tests have existed.

`dice.roll()` takes `log=True` by DEFAULT — which is right for play, because
`CLAUDE.md` treats `campaign/rolls.tsv` as the evidence and a roll that never got
written down is a roll that can be argued about later. But it means any test that
exercises `combat.py`, `clock.py` or `dice.py` through their real code paths writes
into the live audit trail. Found 2026-09-10 while checking whether the log was
current before a compact: the tail of the campaign's die log held rolls for a giant
centipede and an orc that no character had ever met.

**The fix belongs here and not in the individual tests.** Thirty-odd tests call into
those modules and any one of them added later would re-open the hole. Redirecting
the module-level path once, for the whole session, cannot be forgotten.

The redirect points at a real temporary file rather than at nothing, so the logging
code paths still execute and still get tested — a test that asserted "this rolls and
records" keeps working. It just records somewhere that isn't the campaign.
"""
import os
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import dice                                                      # noqa: E402


@pytest.fixture(scope='session', autouse=True)
def _never_write_to_the_campaign_roll_log():
    """Point dice.ROLLS at a scratch file for the whole test session."""
    real = dice.ROLLS
    fd, tmp = tempfile.mkstemp(prefix='rolls-under-test-', suffix='.tsv')
    os.close(fd)
    # dice._log() skips silently if the file is absent, so give it a header row
    # to write under -- that keeps the logging branch live and under test.
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write('# scratch roll log for the test suite. Not the campaign.\n')
        fh.write('when\texped\tturn\tnotation\tdice\tmodifier\ttotal\thidden\treason\n')
    dice.ROLLS = tmp
    try:
        yield tmp
    finally:
        dice.ROLLS = real
        try:
            os.unlink(tmp)
        except OSError:
            pass
