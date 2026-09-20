"""The figure-checker must catch every number the DM has actually got wrong --
and must stay silent on correct text.

**The second half is the harder requirement and the more important one.** A
checker that cries wolf gets ignored, and an ignored checker is prose again,
which is the failure this whole project exists to remove. So there are as many
tests here for silence as for catching.

THE SEVEN REAL ERRORS, all player-caught, all of them plain arithmetic:

    funds 595 gp            -> 1,072      spikes 3 in the hill  -> 9
    Tristle 641 xp          -> 712        19 oil flasks         -> 18
    2 ropes                 -> 8          171 tests             -> 198
    Yrtone 6/7              -> 7/7

None of them needed a language model, which is why this half is deterministic
and the agent (`.claude/agents/auditor.md`) is left the claims that need reading.

AND THE BUG THESE TESTS WERE WRITTEN AGAINST: the first implementation compared
every figure in a sentence against every anchor in it. *"19 sealed flasks and 2
ropes"* reported the rope count as a bad flask count, and *"Dave is at 9/9 and
Yrtone is 6 of 7"* produced four findings from two facts, two of them wrong.
`_nearest()` binds each figure to its closest anchor instead. See
`test_two_quantities_in_one_sentence_do_not_cross_contaminate`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import audit                                                     # noqa: E402

# Fixed truths, so these tests do not move when the campaign does. The point
# under test is the MATCHING, not today's gold.
TR = {
    'funds': (1072.1, 'gp', 'campaign/inventory.tsv'),
    'spikes_emplaced': (9, 'spikes', 'tools/world.py deployed'),
    'ropes': (8, 'ropes', 'campaign/inventory.tsv'),
    'oil_sealed': (18, 'flasks', 'tools/light.py oilstate'),
    'tests': (198, 'tests', 'pytest --collect-only'),
    'day': (77, 'day', 'campaign/days.tsv'),
}
CHARS = {'Dave': {}, 'Yrtone': {}, 'Tristle': {}}
HP = {'Dave': (9, 9), 'Yrtone': (7, 7), 'Tristle': (3, 3)}
XP = {'Dave': 744, 'Yrtone': 660, 'Tristle': 712}


def run(text):
    return audit.audit(text, tr=TR, chars=CHARS, hpnow=HP, xpnow=XP)


def verdicts(text):
    findings, _ = run(text)
    return [(f[0], f[1]) for f in findings]


def mismatches(text):
    return [f[1] for f in run(text)[0] if f[0] == 'MISMATCH']


# ---------------------------------------------------------------- catching

def test_it_catches_the_funds_error():
    assert 'funds' in mismatches('The party has 595 gp in funds.')


def test_it_catches_the_spike_error():
    assert 'spikes_emplaced' in mismatches('There are 3 spikes in the hill.')


def test_it_catches_the_xp_error():
    assert 'xp:Tristle' in mismatches('Tristle has 641 xp.')


def test_it_catches_the_hp_error():
    assert 'hp:Yrtone' in mismatches('Yrtone is at 6 of 7.')


def test_it_catches_the_oil_and_rope_errors():
    m = mismatches('We hold 19 sealed flasks. There are 2 ropes.')
    assert 'oil_sealed' in m and 'ropes' in m


def test_it_catches_the_test_count():
    assert 'tests' in mismatches('171 tests pass.')


def test_all_seven_historical_errors_in_one_block():
    """The exact shape of the real failures, in one paragraph."""
    text = ('The party has 595 gp in funds. There are 3 spikes in the hill. '
            'Tristle has 641 xp. Yrtone is 6 of 7. We have 19 sealed flasks '
            'and 2 ropes. 171 tests pass.')
    assert len(mismatches(text)) == 7


# ---------------------------------------------------------------- silence

def test_correct_text_produces_nothing():
    text = ('The party has 1,072 gp in funds. Tristle has 712 xp and Dave is '
            'at 9/9. 18 sealed flasks. 198 tests pass. It is campaign day 77.')
    assert mismatches(text) == []


def test_whole_gold_is_accepted_against_odd_silver():
    """1,072 gp 1 sp is 1072.1, and "1,072 gp" is a TRUE statement about it.

    Without a whole-gp tolerance the checker fires on a correct figure, which
    is the fastest possible way to teach the DM to ignore it.
    """
    assert mismatches('funds stand at 1,072 gp') == []


def test_two_quantities_in_one_sentence_do_not_cross_contaminate():
    """THE REGRESSION. Each figure binds to its NEAREST anchor, not to all.

    Before `_nearest()`, this sentence reported the rope count as a bad flask
    count and vice versa -- two false positives from one true statement.
    """
    assert mismatches('We have 18 sealed flasks and 8 ropes.') == []


def test_two_characters_in_one_sentence_each_get_their_own_hp():
    """Before `_nearest()` this produced four findings from two facts."""
    v = verdicts('Dave is at 9/9 and Yrtone is 7/7.')
    assert sorted(v) == [('OK', 'hp:Dave'), ('OK', 'hp:Yrtone')]


def test_a_sentence_about_another_day_is_historical_and_skipped():
    """calendar.md is full of figures that were right on the day they were
    written. Checking those against today would be the tool crying wolf."""
    findings, stats = run('On day 39 the party had 595 gp and 3 spikes.')
    assert findings == []
    assert stats['historical'] > 0


def test_a_sentence_naming_the_CURRENT_day_is_still_checked():
    """Only OTHER days are historical. "On day 77 funds are 595" is a claim."""
    assert 'funds' in mismatches('On day 77 the funds are 595 gp.')


def test_a_bare_number_with_no_anchor_is_unchecked_not_guessed():
    findings, stats = run('He put twenty five gold on the bar, then 40 more.')
    assert findings == []
    assert stats['unchecked'] > 0


def test_a_figure_far_from_its_anchor_is_not_bound_to_it():
    """The window is 80 characters. Beyond it, no claim is inferred."""
    text = ('funds' + ' and so on' * 12 + ' 595')
    assert mismatches(text) == []


# ---------------------------------------------------------------- plumbing

def test_only_prose_is_audited():
    """AUDITING THE LOGS IS CIRCULAR and can only produce noise.

    The first time the hook ran against a real commit it BLOCKED one, and every
    finding was a false positive out of the new TSVs: `torch ... 100` was an
    asset name beside its unit WEIGHT; `rope, 50 ft ... 75` yielded "50" and
    "75"; and money.tsv's header comment, which lists the five historical
    errors by way of explaining itself, offered "357 gp of small goods" as a
    rope count.

    The logs are what the tools compute FROM. Checking them against the tools
    compares a figure with a copy of itself. Paraphrases live in prose, and so
    did all eight class-C errors.
    """
    assert audit.AUDIT_EXTENSIONS == ('.md',)


def test_the_staged_diff_skips_the_post_mortems():
    """`dlwork/` quotes the wrong numbers ON PURPOSE -- it is where the error
    post-mortems and this project's own plan live. Auditing it would flag a
    correct document for correctly reporting an incorrect number."""
    assert 'dlwork/' in audit.SKIP_PATHS
    assert 'deprecated/' in audit.SKIP_PATHS
    assert 'tools/tests/' in audit.SKIP_PATHS, (
        'this very file quotes every wrong figure in the campaign')


def test_every_anchor_names_a_known_quantity():
    """An anchor for a quantity nothing computes would silently never fire."""
    known = set(audit.truths(need=set()) ) | {'tests'}
    unknown = [k for k, _ in audit.ANCHORS if k not in known]
    assert not unknown, ('anchors with no truth behind them: %s' % unknown)


def test_show_lists_a_source_for_every_truth():
    """A figure with no named source cannot be argued with, only believed."""
    for key, (val, unit, src) in audit.truths(need=set()).items():
        assert src, 'truth %r has no source' % key
        assert unit, 'truth %r has no unit' % key


def test_the_real_truths_are_computable():
    """Smoke test against the live campaign: nothing raises, funds resolve.

    `_inventory_qty` read a column called `kind` when the column is `category`,
    and the failure mode was SILENT -- the tool reported no funds, no ropes and
    no torches, which looks exactly like a clean bill of health.
    """
    tr = audit.truths(need=set())
    assert 'funds' in tr and tr['funds'][0] > 0
    assert 'ropes' in tr
    assert 'spikes_emplaced' in tr
    assert 'day' in tr and tr['day'][0] >= 77


def test_the_auditor_agent_exists_and_forbids_the_dm_notes():
    """The agent's spoiler clause is not optional and not editable away."""
    path = os.path.join(ROOT, '.claude', 'agents', 'auditor.md')
    assert os.path.exists(path), 'the auditor agent has gone'
    text = open(path, encoding='utf-8').read()
    assert 'B1_DM_NOTES_DO_NOT_READ' in text
    assert 'Do not read them' in text
    for tier in ('1 — EVIDENCE', '3 — INDEX'):
        assert tier in text, (
            'the source-tier table has lost %r. Without it the auditor can '
            'contradict the DM out of npcs.md -- which is the very file that '
            'misleads him, and would be the error it exists to catch wearing '
            'a badge.' % tier)


def test_the_pre_commit_hook_exists_and_is_executable():
    hook = os.path.join(ROOT, 'tools', 'hooks', 'pre-commit')
    assert os.path.exists(hook), 'the pre-commit hook has gone'
    assert os.access(hook, os.X_OK), '%s is not executable' % hook
    text = open(hook, encoding='utf-8').read()
    assert 'audit.py --staged' in text
    assert 'core.hooksPath' in text, 'the hook does not say how to enable it'


def test_party_has_no_dwarf_is_not_a_claim_about_the_purse():
    """*** IT CRIED WOLF ON 2026-09-14 AND BLOCKED A COMMIT. ***

    The `funds` anchor carried a bare `party (?:has|holds)`, so a DM note
    reading "The party has no dwarf. The one they took out of area 34..." was
    read as a statement about money. The checker then took the nearest number --
    the 6 in "2 in 6 chance" -- and reported "text says 6, tools say 1041.1 gp".

    CLAUDE.md: "If it ever cries wolf, LOOSEN THE CHECKER -- do not learn to
    pass --no-verify." So the phrase must now sit within thirty characters of an
    actual money word.
    """
    findings, _ = run('The party has no dwarf. Only a dwarf notices the '
                      'slant, 2 in 6.')
    assert not [f for f in findings if f[1] == 'funds'], findings


def test_the_funds_anchor_still_catches_a_real_purse_claim():
    """Loosening must not blind it."""
    for text in ('the party has 3 gp on hand',
                 'the purse is 12 gp',
                 'party funds stand at 7 gp'):
        findings, _ = run(text)
        assert [f for f in findings if f[1] == 'funds'], (text, findings)


# ------------------- a transcribed book table is not a paraphrase. Day 99.
# Completing DMG Appendix O in rules/equipment.md blocked a commit with three
# findings, every one the same mistake the TSV case made a month earlier:
#
#     ropes    text says 50   tools say 10   <- "| Rope, 50' | 75 |"
#     torches  text says 25   tools say 8    <- "| Torch | 25 |"
#     funds    text says 1    tools say 1025 <- "| Purse | 1 |"
#
# Those are encumbrance figures out of the Dungeon Masters Guide.

def test_a_book_table_row_in_rules_is_not_audited():
    import audit
    assert 'rules/' in audit.BOOK_TABLE_PATHS
    assert 'bestiary/' in audit.BOOK_TABLE_PATHS


def test_prose_is_still_audited_everywhere():
    """The loosening must not become an exemption for whole files.

    Only PIPE-TABLE ROWS are skipped, and only in the two directories that hold
    transcribed book data. A sentence in rules/ that restates a running total is
    exactly the class-C error this hook exists to catch.
    """
    import audit
    findings, stats = audit.audit('The party has 50 ropes and 25 torches.')
    names = {f[0] if isinstance(f, (list, tuple)) else str(f) for f in findings}
    assert findings, 'a prose claim about ropes and torches must still be caught'
    assert stats['checked'] >= 2


def test_the_skip_is_rows_only_and_not_the_whole_directory():
    """Guards the shape of the fix rather than its effect.

    If somebody ever widens this to `SKIP_PATHS += ('rules/',)` the hook stops
    reading the rules cache's prose entirely, and that prose is where the
    campaign's rulings live.
    """
    import audit
    assert not any(p.startswith('rules') for p in audit.SKIP_PATHS), (
        'rules/ must NOT be in SKIP_PATHS -- only its table ROWS are skipped')
    assert not any(p.startswith('bestiary') for p in audit.SKIP_PATHS)


# ------------------------- a hard-wrapped line is not a sentence. Day 101.
# sentences() split on EVERY newline, so markdown prose wrapped at ~79 columns
# was chopped mid-clause. That breaks the checker both ways: a "day N" marker
# wrapped away from its sentence never reaches historical(), and a figure
# belonging to one noun gets bound to an anchor that happens to survive the cut.
#
# The live case: "...ON THREE HORSES. On day\n101 that is 196 spikes, 20 lb of
# nails, and every sealed flask..." -- the wrap hid "day 101" AND bound the 20
# from the NAILS to the "sealed flask" anchor. One line break, one false
# positive, out of two unrelated true statements.

def test_wrapped_prose_is_rejoined_before_it_is_split():
    import audit
    got = list(audit.sentences('the party carried on day\n101 eight flasks.'))
    assert got == ['the party carried on day 101 eight flasks.'], got


def test_a_blockquote_is_prose_and_joins_to_itself():
    """This repo puts its load-bearing paragraphs in `>` boxes."""
    import audit
    got = list(audit.sentences('> a sentence that runs on\n> to the next line.'))
    assert got == ['> a sentence that runs on to the next line.'], got


def test_a_blockquote_never_joins_to_the_paragraph_outside_it():
    import audit
    got = list(audit.sentences('plain prose running on\n> quoted prose'))
    assert len(got) == 2, got


def test_table_rows_and_list_items_are_never_joined():
    """There a line really IS the unit, and joining them invents sentences."""
    import audit
    assert len(list(audit.sentences('| a | 1 |\n| b | 2 |'))) == 2
    assert len(list(audit.sentences('- one thing\n- another'))) == 2
    assert len(list(audit.sentences('# heading\nprose under it'))) == 2
    assert len(list(audit.sentences('| a | 1 |\n> quoted'))) == 2


def test_a_blank_line_still_separates_paragraphs():
    import audit
    got = list(audit.sentences('first para runs on\n\nsecond para'))
    assert got == ['first para runs on', 'second para'], got


def test_a_finished_sentence_does_not_swallow_the_next_line():
    import audit
    got = list(audit.sentences('It ended here.\nA new one began.'))
    assert got == ['It ended here.', 'A new one began.'], got
