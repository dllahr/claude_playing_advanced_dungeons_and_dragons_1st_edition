"""The lane rule has ONE authority and every paraphrase of it must keep its trigger.

**This test exists because a warning failed three times.**

`rules/exploration.md` states it correctly and always has, including a row reading
*"allies merely standing in front are not a melee."* But the figure also got
paraphrased into `party_roster.md` and into `CHECKLIST.md`, and the paraphrases
dropped the "in melee" condition. The DM then quoted a paraphrase:

  - expedition 4, round ~1203: three darts resolved with NO penalty and no ally
    risk, and retracted;
  - 2026-09-06: the opposite error, penalty applied with nobody in contact;
  - 2026-09-08: the same error a THIRD time, in a marching-order note -- and
    `party_roster.md` was at that moment already carrying a warning that said
    *"this paraphrase used to omit that and misled the DM again on 2026-09-06."*

A note that has failed twice is not a mechanism. So: a test.

WHAT IT ENFORCES
  1. The authoritative row in `rules/exploration.md` keeps BOTH conditions --
     "into a melee" and "on a miss".
  2. The explicit no-melee row is still there.
  3. No markdown file outside `rules/` restates the ally-hit figure at all.
     Paraphrases lose conditions; the fix is to have no paraphrases with numbers
     in them. Point at the cache instead.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE)) if os.path.basename(
    os.path.dirname(HERE)) == 'tools' else os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(os.path.dirname(HERE))
AUTHORITY = os.path.join(ROOT, 'rules', 'exploration.md')

# The phrasing that has actually caused the misreadings, every time.
FIGURE = re.compile(r'50\s*%\s*chance of hitting the ally', re.I)

SKIP_DIRS = {'deprecated', '.git', 'manuals', 'modules', 'mapdb', 'dlwork',
             'session_exports', 'scratchpad'}


def _markdown_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.md'):
                yield os.path.join(dirpath, fn)


def test_the_authority_keeps_both_conditions():
    """rules/exploration.md is the only place the figure may live."""
    text = open(AUTHORITY, encoding='utf-8').read()
    rows = [ln for ln in text.splitlines() if FIGURE.search(ln)]
    assert rows, 'the lane-rule row has gone from rules/exploration.md'
    for row in rows:
        low = row.lower()
        assert 'melee' in low, (
            'THE TRIGGER IS GONE. The lane rule only applies when somebody is in '
            'contact, and this row no longer says so: %r' % row)
        assert 'on a miss' in low, (
            'THE SECOND CONDITION IS GONE. The ally is only at risk on a MISS: %r'
            % row)


def test_the_no_melee_row_survives():
    """The row that says allies merely standing in front are not a melee."""
    text = open(AUTHORITY, encoding='utf-8').read().lower()
    assert 'not a melee' in text, (
        'rules/exploration.md has lost the row stating that allies merely '
        'STANDING in front are not a melee. That row is the one the DM needed '
        'three separate times.')


def test_no_paraphrase_anywhere_else_carries_the_figure():
    """Paraphrases lose conditions. So no paraphrase gets the number."""
    offenders = []
    for path in _markdown_files():
        if os.path.abspath(path) == os.path.abspath(AUTHORITY):
            continue
        for n, line in enumerate(open(path, encoding='utf-8'), 1):
            if FIGURE.search(line):
                offenders.append('%s:%d' % (os.path.relpath(path, ROOT), n))
    assert not offenders, (
        'The lane-rule figure has been restated outside rules/exploration.md at '
        '%s. Every paraphrase of this rule in this repo has dropped a condition '
        'at least once, and the DM has quoted a paraphrase three times. State the '
        'TRIGGER in prose and point at rules/exploration.md for the numbers.'
        % ', '.join(offenders))
