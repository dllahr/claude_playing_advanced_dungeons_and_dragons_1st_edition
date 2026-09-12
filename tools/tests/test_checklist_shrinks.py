"""`CHECKLIST.md` may not grow while the test suite does. The ratchet.

**Every enforceable line that becomes a test must be DELETED from the prose.**
Not because the knowledge is unwanted -- because of where it needs to live.

    the instruction   "remember to apply the -4 only in melee"   -> DELETED
    the reason and    "this failed on these three dates, and     -> KEPT, in the
    the history        here is the wording that misled"             test's
                                                                    docstring and
                                                                    assertion

An assertion message is read **at the instant of the offence**. A paragraph in a
1,400-line file is read at the start of a session and then not again. That is the
whole difference, and it is why `test_lane_rule.py` has held where three prose
warnings failed.

*** WHY THIS TEST EXISTS AT ALL. ***

The plan (`dlwork/tooling_plan.md`, phase 6) marked the deleting half NOT
OPTIONAL, because the DM had done the fun half twice and never the deleting:
`test_lane_rule.py` shipped and the lane-rule section stayed; the roll-log
conftest shipped and its section stayed; the reaction-table discipline got a rule
and kept every earlier paragraph. **So the file only ever grew -- to 1,598 lines,
with its own section 11 thirty-eight in-game days out of date while warning in
that same section's second paragraph that snapshots rot.**

An unread instruction is worse than an absent one, because it looks like cover.

THE GATE, which this test cannot check and a human must:

    Delete the prose ONLY when the test covers the same ground AND its failure
    message says everything the prose said.

What this test CAN check is that the trade only ever goes one way.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)

CHECKLIST = os.path.join(ROOT, 'CHECKLIST.md')

# The high-water mark, set when the ratchet was installed. It may come DOWN and
# never up. Lower it whenever a section is genuinely absorbed by a machine.
CEILING = 1407


def lines(path):
    return len(open(path, encoding='utf-8').read().split('\n'))


def test_the_checklist_is_at_or_under_its_ceiling():
    n = lines(CHECKLIST)
    assert n <= CEILING, (
        'CHECKLIST.md is %d lines, over its ceiling of %d.\n'
        '\n'
        'THE RATCHET ONLY TURNS ONE WAY. If a rule has just been given a test '
        'or a tool, DELETE THE INSTRUCTION HERE and keep the reason inside the '
        'test docstring and its assertion message -- that message is read at '
        'the instant of the offence, and a paragraph in this file is read at '
        'the start of a session and then not again.\n'
        '\n'
        'If the new prose is genuinely NOT mechanisable -- tone, spoiler '
        'judgment, whether a scene is any good -- then something else in this '
        'file has become mechanisable and should go. The DM shipped three '
        'mechanisms without deleting a line of the prose they replaced, which '
        'is how this file reached 1,598 lines with a section in it 38 in-game '
        'days out of date.\n'
        '\n'
        'Lowering CEILING in this file is the ONLY legitimate way to change '
        'it, and it should be lowered whenever a section is absorbed.'
        % (n, CEILING))


def test_the_ceiling_is_not_far_above_the_file():
    """A ceiling with slack in it is not a ratchet, it is a suggestion."""
    n = lines(CHECKLIST)
    assert CEILING - n <= 60, (
        'CHECKLIST.md is %d lines and the ceiling is %d -- %d lines of slack. '
        'Lower CEILING to about %d. A ratchet with room in it lets the file '
        'grow back without ever failing, which is precisely the failure mode.'
        % (n, CEILING, CEILING - n, n + 10))


def test_the_sections_that_became_machines_are_gone_from_the_prose():
    """Named individually, so a merge cannot quietly restore one."""
    text = open(CHECKLIST, encoding='utf-8').read()
    gone = {
        'THE PROCEDURE, and there is no version of it that skips a step':
            'the six-step declaration procedure -- combat.py round now '
            'refuses an undeclared attack, and test_encounter.py holds the '
            'day-70 incident',
        'A TRADE GOOD WITH NO ROW STOPS EXISTING':
            'log.py refuses a money row with no asset and ledger.py check '
            'warns on a good with no inventory row',
        'HAS ITS OWN TEST NOW, BECAUSE PROSE FAILED THREE TIMES':
            'test_lane_rule.py -- the pointer replaced the retelling',
        '## 10. The map extraction pipeline\n\n**`mapdb/`':
            'moved to mapdb/README.md, where tool documentation belongs',
    }
    back = [why for marker, why in gone.items() if marker in text]
    assert not back, (
        'prose that a machine had absorbed has come back: %s' % back)


def test_the_deleted_rules_still_exist_somewhere_that_fires():
    """THE OTHER HALF OF THE GATE. Deleting must not lose the knowledge.

    Each of these strings was carried by a CHECKLIST section that is now gone.
    It must survive in the place that is read at the moment it matters.
    """
    def read(*parts):
        return open(os.path.join(ROOT, *parts), encoding='utf-8').read()

    survives = [
        (read('tools', 'tests', 'test_lane_rule.py'), 'on a miss',
         'the lane rule\'s second condition'),
        (read('tools', 'tests', 'test_encounter.py'), 'Yrtone swapped',
         'what the DM silently decided on day 70'),
        (read('tools', 'tests', 'test_encounter.py'),
         "A CHARACTER'S ACTIONS ARE NEVER THE", 'the rule itself'),
        (read('tools', 'tests', 'test_loops.py'), 'A STALE WARNING LOOKS LIKE',
         'why a warning needs a machine'),
        (read('tools', 'tests', 'test_ledger.py'), 'two carts',
         'the five purchases that got no row'),
        (read('mapdb', 'README.md'), 'moved out of `CHECKLIST.md`',
         'the map pipeline'),
    ]
    missing = ['%s (%s)' % (why, needle)
               for text, needle, why in survives if needle not in text]
    assert not missing, (
        'DELETED FROM THE CHECKLIST AND NOT KEPT ANYWHERE THAT FIRES: %s.\n'
        'The gate is that a test may replace prose only when its message says '
        'what the prose said. Restore it or restore the section.' % missing)


def test_the_suite_is_still_growing_while_the_prose_is_not():
    """The ratchet is a RATIO, not a line count. Both halves must hold."""
    p = subprocess.run([sys.executable, '-m', 'pytest', HERE,
                        '--collect-only', '-q'],
                       cwd=ROOT, capture_output=True, text=True)
    import re
    m = re.search(r'(\d+)\s+tests? collected', p.stdout)
    assert m, p.stdout[-400:]
    n = int(m.group(1))
    assert n >= 300, (
        'the suite has %d tests. It had 300 when the ratchet was installed, '
        'and CHECKLIST.md was allowed to shrink on the strength of that. '
        'Losing tests while keeping the deletions would leave the rules '
        'enforced by nothing at all.' % n)
