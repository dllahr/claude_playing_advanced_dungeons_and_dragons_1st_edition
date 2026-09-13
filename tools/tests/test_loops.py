"""A loop cannot be closed without citing the thing that closed it.

**This file is the machine behind four errors of one shape.** A forward-looking
note was written, the thing it predicted happened, and nobody closed the note:

  * `articles.md` art. 11 warned that Wace's receipt would reach Wend before she
    had seen the letter. **True on day 55, fired on day 65, quoted as live on
    DAY 77** -- eleven days late.
  * `npcs.md` said of Ancel *"Unanswered. He will not sit in the square
    forever."* **Answered on day 34, quoted as live on day 77 -- 43 DAYS.**
  * `CHECKLIST` section 11 was headed "day 39" while play stood at day 77 --
    and warned in its own second paragraph that snapshots rot.
  * "Rowe stays until his foot heals", long after he went south with Halm.

A stale total looks like a number and can be checked against a tool. **A stale
warning looks exactly like a live one.** So warnings become rows.

WHAT THIS ENFORCES

  1. `campaign/loops.tsv` is a LOG, not a table with a mutable `closed` cell.
     Every verb must be one this tool understands, so a typo'd verb cannot
     silently leave a loop open for ever.
  2. **Every `close` cites evidence** -- in the file, and refused at the CLI.
     That is the step that was skipped on art. 11: had closing required naming
     day 65, the DM would have had to go and FIND day 65, which was the whole of
     the omission.
  3. Nothing is closed twice, because a second close hides which event really
     closed it.
  4. Both worked examples stay in the seeded log. They are the two errors this
     mechanism exists for, and a regression that quietly dropped them would
     remove the only test data that proves the shape.
  5. `days.tsv` yields a current day, because the briefing and every "overdue"
     judgment are computed off it.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import loops                                                     # noqa: E402
from tsvlog import read_tsv                                      # noqa: E402

LOG = os.path.join(ROOT, 'campaign', 'loops.tsv')
DAYS = os.path.join(ROOT, 'campaign', 'days.tsv')


def rows():
    return read_tsv(LOG, missing_ok=True)


def test_every_verb_is_one_the_tool_understands():
    """A typo'd verb would leave a loop open for ever and look deliberate."""
    bad = [(r.get('loop'), r.get('verb')) for r in rows()
           if r.get('verb', '').strip() not in loops.VERBS]
    assert not bad, ('unknown verb(s) in campaign/loops.tsv: %s. Known: %s'
                     % (bad, list(loops.VERBS)))


def test_every_close_cites_evidence():
    """THE RULE. A loop closed with a flag is a loop nobody had to verify."""
    naked = [r.get('loop') for r in rows()
             if r.get('verb', '').strip() == 'close'
             and not r.get('evidence', '').strip()]
    assert not naked, (
        'loop(s) %s were CLOSED WITHOUT EVIDENCE.\n'
        '\n'
        'Closing means CITING THE THING THAT CLOSED IT -- a day:seq, a '
        'file:line, a log row. This is the exact step skipped on articles.md '
        'art. 11, which then sat open for ELEVEN DAYS after it had fired and '
        'was quoted as live on day 77.\n'
        '\n'
        'WHY THIS PARTICULAR RULE NEEDS A MACHINE: a stale total looks like a '
        'number and can be checked against a tool. A STALE WARNING LOOKS LIKE '
        'A WARNING. Nothing on its face says it has already fired, so it reads '
        'as live for ever and gets quoted as live for ever. The prose files '
        'are an index, and AN INDEX OF THE FUTURE GOES OUT OF DATE FASTER '
        'THAN AN INDEX OF THE PAST.\n'
        '\n'
        'And when you close one in a prose file, close it by REWRITING the '
        'box -- a tick, what actually happened, and the fact that it was true '
        'when written. Deleting it orphans the citation; see '
        'deprecated/README.md for the same principle.'
        % naked)


def test_nothing_is_closed_twice():
    seen, twice = set(), []
    for r in rows():
        if r.get('verb', '').strip() != 'close':
            continue
        lid = r.get('loop', '').strip()
        if lid in seen:
            twice.append(lid)
        seen.add(lid)
    assert not twice, (
        'loop(s) %s carry two close rows. The second hides which event '
        'actually closed it, which is the one fact a close exists to record.'
        % twice)


def test_no_close_without_an_open():
    latest_verbs = {}
    for r in rows():
        latest_verbs.setdefault(r.get('loop', '').strip(), []).append(
            r.get('verb', '').strip())
    orphans = [lid for lid, vs in latest_verbs.items()
               if 'open' not in vs and lid]
    assert not orphans, ('loop(s) %s have events but were never opened'
                         % orphans)


def test_the_two_worked_examples_survive():
    """The 43-day loop and the 11-day loop are the test data. Keep them.

    L001 is Ancel -- *"Unanswered. He will not sit in the square forever"* --
    answered on day 34 and quoted as live on day 77. L002 is Wace's receipt,
    fired on day 65 and quoted as live on day 77. **Both are seeded CLOSED, with
    evidence, as the demonstration of the shape this file prevents.**
    """
    latest, _ = loops.state(rows())
    for lid, subject in (('L001', 'ancel'), ('L002', 'wace')):
        assert lid in latest, (
            '%s has gone from campaign/loops.tsv. It is one of the two worked '
            'examples this mechanism was built for and it is the only proof in '
            'the repo that a closed loop can be represented at all.' % lid)
        assert latest[lid]['verb'] == 'close'
        assert latest[lid]['subject'] == subject
        assert latest[lid]['evidence'].strip()


def test_open_loops_excludes_the_closed_ones():
    ids = [r['loop'] for r in loops.open_loops(rows())]
    assert 'L001' not in ids and 'L002' not in ids
    assert ids, 'no open loops at all -- the seed has been lost'


def test_a_note_does_not_close_a_loop():
    """`note` records movement on something still open. It must not close it."""
    log = [
        dict(loop='L900', verb='open', subject='x', what='a', evidence='e',
             day='1', expected_day='', when=''),
        dict(loop='L900', verb='note', subject='x', what='moved', evidence='',
             day='2', expected_day='', when=''),
    ]
    assert [r['loop'] for r in loops.open_loops(log)] == ['L900']
    latest, _ = loops.state(log)
    assert latest['L900']['verb'] == 'open'


def test_close_inherits_the_subject_and_text_it_does_not_restate():
    log = [
        dict(loop='L901', verb='open', subject='wend', what='the thing',
             evidence='e1', day='1', expected_day='9', when=''),
        dict(loop='L901', verb='close', subject='', what='', evidence='e2',
             day='5', expected_day='', when=''),
    ]
    latest, _ = loops.state(log)
    assert latest['L901']['verb'] == 'close'
    assert latest['L901']['subject'] == 'wend'
    assert latest['L901']['what'] == 'the thing'
    assert latest['L901']['evidence'] == 'e2'
    assert loops.open_loops(log) == []


def test_next_id_does_not_collide():
    nid = loops.next_id(rows())
    latest, _ = loops.state(rows())
    assert nid not in latest


@pytest.mark.parametrize('argv', [
    ['close', 'L001', '--evidence', 'x'],          # already closed
    ['close', 'L999', '--evidence', 'x'],          # no such loop
])
def test_the_cli_refuses_a_bad_close(argv, tmp_path):
    """Refusal is the point. A tool that shrugs is a sentence again."""
    scratch = tmp_path / 'loops.tsv'
    scratch.write_text(open(LOG).read())
    # --log-file is a top-level option and must precede the subcommand, the
    # same shape as hp.py and world.py.
    assert loops.main(['--log-file', str(scratch)] + argv) == 1
    assert scratch.read_text() == open(LOG).read(), 'it wrote anyway'


def test_a_good_close_is_appended_and_removes_it_from_open(tmp_path):
    """*** THIS NAMED L018 AND WENT RED WHEN THE PARTY CLOSED IT. ***

    On day 80 Dave answered Wend's whose-money question, L018 closed, and a
    test about the CLOSE MECHANISM failed because the fixture had hard-coded
    one live loop id as a stand-in for "an open loop". Fifth time this shape has
    appeared -- the purse, the party's position, the encounter fixture, the
    spike count, and now this. A test that names today's data is a test of
    today.

    It now takes whatever is open, so it tests the mechanism and nothing else.
    """
    scratch = tmp_path / 'loops.tsv'
    scratch.write_text(open(LOG).read())
    rows = read_tsv(str(scratch))
    still_open = loops.open_loops(rows)
    assert still_open, 'no open loops at all -- pick a different fixture'
    victim = still_open[0]['loop']
    before = len(rows)
    assert loops.main(['--log-file', str(scratch), 'close', victim,
                       '--evidence', '79:2', '--day', '79']) == 0
    after = read_tsv(str(scratch))
    assert len(after) == before + 1
    assert victim not in [r['loop'] for r in loops.open_loops(after)]


def test_days_tsv_gives_a_current_day():
    """The most frequently needed fact in the campaign, and it drifted once."""
    day = loops.current_day(DAYS)
    assert day is not None, 'campaign/days.tsv yields no current day'
    assert day >= 77, (
        'current day computed as %s. It was 77 when days.tsv was seeded and '
        'the day count only goes up -- a lower number means rows were lost.'
        % day)
