"""The DM may not roll for a character who has not said what they are doing.

**This is the day-70 error made impossible.** At round 285, on the loaded walk
out of the pocket, the DM resolved the party's round without asking: he decided
Yrtone swapped sling for flail, decided which four engaged, decided nobody fired
a missile, cast, dropped a load or withdrew. **Four attack rolls were voided.**
The player: *"Please stop right now."*

`CHECKLIST.md` gained a ⚠⚠ heading and a six-step procedure that day. **This
file is that rule stopping being a sentence.** `combat.py round` refuses to roll
for anyone without a `declare` row in the current round of
`campaign/encounter.tsv`.

IT IS A SPEED BUMP AND NOT A WALL, and that is said plainly in the tool: the DM
could type a declaration the player never made, exactly as he could log a move
`party.py` never routed. That tool has held for two expeditions anyway, because
the friction arrives at the instant of the error rather than in a file read at
the start of a session.

AND A HOLD IS A DECLARATION. Day 70 had two of them -- Blartho and Dellie held,
ready to close or cast -- and a gate that treated "held" as "said nothing" would
refuse the one round the DM got right.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import combat                                                     # noqa: E402
import encounter                                                  # noqa: E402
from tsvlog import read_tsv                                       # noqa: E402

LOG = os.path.join(ROOT, 'campaign', 'encounter.tsv')


@pytest.fixture
def fight(tmp_path, monkeypatch):
    """A scratch encounter log, pointed at by the module the gate reads."""
    p = tmp_path / 'encounter.tsv'
    p.write_text(open(LOG, encoding='utf-8').read())
    monkeypatch.setattr(encounter, 'LOG', str(p))
    encounter.main(['--log-file', str(p), 'start', '--detail',
                    'the y=21 corridor, one troglodyte', '--exped', '9',
                    '--day', '79'])
    return str(p)


def declare(p, who, what):
    encounter.main(['--log-file', p, 'declare', who, what])


# ------------------------------------------------------------- the gate

def test_it_refuses_when_no_fight_is_logged(monkeypatch, capsys):
    monkeypatch.setattr(encounter, 'current', lambda *a, **k: None)
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword']) == 1
    assert 'REFUSED' in capsys.readouterr().err


def test_the_rule_itself_is_stated_where_it_fires(fight, capsys):
    """A test may only replace prose if its message says what the prose said.

    The CHECKLIST section this replaced listed what the DM silently decided on
    day 70: that Yrtone swapped her sling for a flail, which four characters
    engaged and which five did not, that nobody fired a missile, that nobody
    cast -- Frython's sleep and nine memorised cleric spells went unmentioned --
    and that nobody dropped a load, withdrew, closed a door or ran.

    **A MONSTER'S ACTIONS ARE THE DM'S. A CHARACTER'S ACTIONS ARE NEVER THE
    DM'S** -- not the six PCs, and not Hask, Dellie or Ista, who are 1st-level
    characters on characters.tsv that the player plays.
    """
    combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                 '--attack', 'Dave:long sword'])
    err = capsys.readouterr().err
    assert 'ASK THE PLAYER' in err
    assert 'day-70' in err or 'day 70' in err


def test_it_refuses_when_nobody_has_declared(fight, capsys):
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword',
                        'Torsat:long sword']) == 1
    err = capsys.readouterr().err
    assert 'REFUSED' in err
    assert 'Dave' in err and 'Torsat' in err


def test_it_names_exactly_who_is_missing(fight, capsys):
    """Naming them is the difference between a gate and an obstacle."""
    declare(fight, 'Dave', 'swings at the trog with his long sword')
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword',
                        'Torsat:long sword']) == 1
    err = capsys.readouterr().err
    assert 'Torsat' in err
    assert 'Dave,' not in err and 'Dave ' not in err.split('REFUSED:')[1][:40]


def test_it_passes_once_everyone_has_declared(fight, capsys):
    declare(fight, 'Dave', 'swings at the trog')
    declare(fight, 'Torsat', 'steps up and swings')
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword',
                        'Torsat:long sword']) == 0
    assert 'total damage' in capsys.readouterr().out


def test_a_HOLD_counts_as_a_declaration(fight, capsys):
    """Day 70 had two held actions. A gate that refused them would be wrong."""
    encounter.main(['--log-file', fight, 'hold', 'Blartho', '--detail',
                    'ready to close or cast'])
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', "Blartho:footman's flail"]) == 0


def test_the_override_exists_and_is_documented_as_a_last_resort(fight):
    """--declared is for a roll outside any encounter, not for skipping the ask."""
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword', '--declared']) == 0
    # argparse does not fold subparser options into the top-level help, so
    # reach for the `round` subparser itself.
    sub = [a for a in combat.build_parser()._actions
           if hasattr(a, 'choices') and a.choices and 'round' in a.choices][0]
    help_text = sub.choices['round'].format_help()
    assert '--declared' in help_text
    assert 'never to skip asking the player' in help_text


def test_a_declaration_does_not_carry_into_the_next_round(fight, capsys):
    """THE SUBTLE ONE. Actions are declared EVERY round, not once per fight."""
    declare(fight, 'Dave', 'swings')
    encounter.main(['--log-file', fight, 'next'])
    assert combat.main(['round', '--target', 'troglodyte AC 5 HD 2',
                        '--attack', 'Dave:long sword']) == 1
    assert 'Dave' in capsys.readouterr().err


# ------------------------------------------------------- the derived state

def test_the_fight_state_is_computed_not_remembered(fight):
    declare(fight, 'Dave', 'swings')
    encounter.main(['--log-file', fight, 'damage', 'trog1', '6',
                    '--detail', 'Torsat, 16 for 8'])
    st = encounter.current(encounter.rows(fight))
    assert st['round'] == 1
    assert st['declared']['Dave'] == 'swings'
    assert st['damage']['trog1'] == 6


def test_end_closes_the_fight_so_the_next_one_is_separate(fight):
    encounter.main(['--log-file', fight, 'end', '--detail', 'the trog is dead'])
    assert encounter.current(encounter.rows(fight)) is None


def test_two_fights_are_not_read_as_one(fight):
    encounter.main(['--log-file', fight, 'end', '--detail', 'over'])
    encounter.main(['--log-file', fight, 'start', '--detail', 'a second fight',
                    '--exped', '9', '--day', '79'])
    st = encounter.current(encounter.rows(fight))
    assert st['detail'] == 'a second fight'
    assert st['round'] == 1
    assert st['declared'] == {}


def test_starting_a_fight_inside_a_fight_is_refused(fight):
    assert encounter.main(['--log-file', fight, 'start',
                           '--detail', 'another', '--exped', '9']) == 1


def test_the_committed_log_holds_NO_STALE_FIGHT():
    """*** THIS TEST USED TO PIN TODAY'S STATE AND WENT RED THE MOMENT A FIGHT
    STARTED. *** It read `current(...) is None` with a docstring saying "play is
    paused at day 77", and on 2026-09-13 the troglodytes at (24,37) turned it
    red for the one reason that is not a bug: a fight was in progress, correctly.

    A test that fails when the campaign advances is a test of the calendar, not
    of the code -- the same defect as the three tests that pinned the purse and
    the party's position on day 79. So it now asserts the INVARIANT it was
    always reaching for: the live log never carries a fight somebody forgot to
    `end`. Either no fight is running, or exactly one is, and it belongs to the
    expedition that is actually out.
    """
    log = read_tsv(LOG, missing_ok=True)
    starts = [r for r in log if (r.get('verb') or '').strip() == 'start']
    ends = [r for r in log if (r.get('verb') or '').strip() == 'end']
    assert len(ends) in (len(starts), len(starts) - 1), (
        '%d start rows and %d end rows -- a fight was left dangling, which is '
        'how encounter.py comes to report a round number from a fight that '
        'finished two expeditions ago' % (len(starts), len(ends)))

    live = encounter.current(log)
    if live is None:
        return
    assert len(ends) == len(starts) - 1
    exped = {(r.get('exped') or '').strip() for r in starts[-1:]}
    assert exped, 'a live fight with no expedition on its start row'


def test_monster_damage_is_hidden_unless_asked_for():
    """Monster hit points are the one number the player must never be handed."""
    log = [dict(verb='start', round='1', detail='x', exped='9', day='79'),
           dict(verb='damage', round='1', target='trog1', qty='6', actor='')]
    assert 'trog1' not in encounter.report(log)
    assert 'trog1' in encounter.report(log, hidden=True)


# ------------------------------------------ the other door on the roll log

def test_dice_honours_the_roll_log_override():
    """The pytest conftest closed this for PYTEST ONLY, and a shell was the
    other door: driving combat.py by hand to check the declaration gate put
    three real d20s into campaign/rolls.tsv within a minute of the gate being
    written. They are voided in the log by an appended row; the hole is shut by
    `dice.ROLLS` honouring $DND_ROLL_LOG.

    *** RUN IN A SUBPROCESS ON PURPOSE. ***

    The first version of this test did `importlib.reload(dice)` -- which RESET
    dice.ROLLS to the module default and so UNDID the session fixture in
    conftest.py, and the suite immediately wrote 28 rows into the campaign roll
    log. A test for a leak that opens the leak. Anything that mutates a module
    the conftest has patched must happen in a child process.
    """
    import subprocess
    out = subprocess.run(
        [sys.executable, '-c',
         'import sys; sys.path.insert(0, %r); import dice; print(dice.ROLLS)'
         % TOOLS],
        env=dict(os.environ, DND_ROLL_LOG='/tmp/does-not-matter.tsv'),
        capture_output=True, text=True, cwd=ROOT)
    assert out.stdout.strip() == '/tmp/does-not-matter.tsv', out.stderr
