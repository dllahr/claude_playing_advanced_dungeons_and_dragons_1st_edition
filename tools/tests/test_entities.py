"""Every name must resolve, and what CHANGES must not live in a reference file.

**This is the largest error class in the campaign getting a mechanism.** Social
events lived only in prose -- three thousand lines of it in one file -- so every
one of these was a question that could not be asked of anything:

    how Kell died            narrated backwards
    Sim's two years          wrong
    Cuddy toward Yrtone      called cold; the prose said the opposite
    Ista's grievance         extended to a cart trip it never covered
    the barrel "never moved"  world_changes.tsv:419 says otherwise
    "the plan was the 51st"  the DM's own calendar row, read back as theirs
    Meg and Tibb             a mother and her grown son, written as two families
    "you nearly forgot Wend"  they had been the ones reminding him

TWO RULES ARE UNDER TEST HERE.

**1. IDENTITY IS REFERENCE; CONDITION IS AN EVENT.** `people.tsv` holds only
what is stable. *"Cuddy is frail"* is not a property of Cuddy -- it became true
on day 76 and was rolled for. **Filing that sort of thing as a property is
exactly how the old prose came to say of Ancel "Unanswered. He will not sit in
the square forever": true for two days, answered completely on day 34, and still
quoted as live on DAY 77. Forty-three days.**

**2. A NAME MUST RESOLVE.** *Wetherby* and *Wethersby* are both in this
repository, some typed by the player. *"Rell's brother"* and *Gyll* are one man
whose name nobody in the hundred used for two years. A fuzzy match is a guess,
and **a guess cannot be a constraint** -- an alias table can.
"""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import entities                                                   # noqa: E402

CAMPAIGN = os.path.join(ROOT, 'campaign')
SESSIONS = os.path.join(CAMPAIGN, 'sessions')


# ------------------------------------------------------ names must resolve

def test_the_live_data_passes_its_own_validator():
    assert [m for s, m in entities.check() if s == 'FAIL'] == []


def test_the_wethersby_spelling_that_has_been_wrong_both_ways():
    """Both spellings are in this repo and some of them are the player's."""
    assert entities.resolve('Wetherby', entities.places()) == 'wethersby'
    assert entities.resolve('Wethersby', entities.places()) == 'wethersby'


def test_rells_brother_and_gyll_are_one_man():
    """Nobody in the hundred used his name for two years, and the file used
    both. He paid restitution in the square on day 35 under one of them."""
    assert entities.resolve("Rell's brother") == 'gyll'
    assert entities.resolve('Gyll') == 'gyll'


def test_titles_resolve_to_the_person():
    for name in ('Cuddy', 'Father Cuddy', 'Ottir', 'Reeve Ottir',
                 'Wace', 'Master Wace', 'Doule', 'Father Doule'):
        assert entities.resolve(name) is not None, name


def test_check_refuses_a_scene_naming_somebody_who_does_not_exist(monkeypatch):
    monkeypatch.setattr(entities, 'scenes', lambda *a, **k: [
        dict(day='1', seq='1', place='wethersby', people='Wend, Wendel',
             kind='counsel', evidence='x')])
    fails = [m for s, m in entities.check() if s == 'FAIL']
    assert any('Wendel' in m for m in fails)
    assert any('Did you mean' in m for m in fails), (
        'a refusal that does not suggest the near miss is an obstacle, '
        'not a gate')


def test_check_refuses_an_unknown_place_and_an_unknown_kind(monkeypatch):
    monkeypatch.setattr(entities, 'scenes', lambda *a, **k: [
        dict(day='1', seq='1', place='atlantis', people='Wend',
             kind='gossiping', evidence='x')])
    fails = [m for s, m in entities.check() if s == 'FAIL']
    assert any('atlantis' in m for m in fails)
    assert any('gossiping' in m for m in fails)


def test_day_and_seq_are_unique_because_other_files_point_at_them(monkeypatch):
    """money.tsv and loops.tsv cite scenes as "77:3". That must mean one thing."""
    monkeypatch.setattr(entities, 'scenes', lambda *a, **k: [
        dict(day='77', seq='3', place='wethersby', people='Wend',
             kind='counsel', evidence='x'),
        dict(day='77', seq='3', place='wethersby', people='Dave',
             kind='counsel', evidence='y')])
    fails = [m for s, m in entities.check() if s == 'FAIL']
    assert any('77:3' in m for m in fails)


# -------------------------------------------- identity vs condition

def test_people_tsv_carries_no_status_or_condition_column():
    """Those CHANGE, so they are events with dates and belong in a log.

    A `status` column here would be the Ancel defect rebuilt: a cell that was
    true once, has no date on it, and reads as current for ever.
    """
    header = [c.strip() for c in
              open(os.path.join(CAMPAIGN, 'people.tsv'), encoding='utf-8')
              .read().split('\n')[-1:][0].split('\t')] if False else None
    with open(os.path.join(CAMPAIGN, 'people.tsv'), encoding='utf-8') as fh:
        for line in fh:
            if line.strip() and not line.startswith('#'):
                header = [c.strip() for c in line.rstrip('\n').split('\t')]
                break
    for banned in ('status', 'condition', 'current', 'hp', 'reaction'):
        assert banned not in header, (
            'people.tsv has a %r column. That CHANGES, so it is an event with '
            'a date and belongs in interactions.tsv, loops.tsv or '
            'availability.tsv -- not in a reference file where it reads as '
            'current for ever.' % banned)


def test_the_ancel_answer_is_a_scene_and_not_a_sentence():
    """THE WORKED EXAMPLE, and the reason this whole file exists.

    He asked on day 32 who to speak to about next summer's wool. It was
    answered completely on DAY 34 -- introduced to Wend as factor at 127,
    brokered to Marrow at 114, four buyers named. The prose said "Unanswered"
    until day 77. As a scene it is a row, with a day on it, that a query
    returns.
    """
    pid = entities.resolve('Ancel')
    mine = [s for s in entities.scenes()
            if pid in [entities.resolve(n) for n in
                       entities.split_people(s.get('people'))]]
    days = sorted(int(s['day']) for s in mine)
    assert 32 in days and 34 in days, days
    answer = [s for s in mine if s['day'] == '34'][0]
    assert answer['kind'] == 'negotiation'
    assert answer['reaction'] == '127'


def test_who_returns_the_scenes_and_points_at_recall_for_the_rest():
    out = entities.who('Ancel')
    assert 'day 34' in out
    assert 'recall.py' in out, (
        'the scene log is not the whole record -- wounds, rolls, money and '
        'gear are elsewhere, and a tool that implies otherwise is worse than '
        'one that says where to look')


# --------------------------------------------------- the prose split

def test_the_narrative_moved_out_of_npcs_and_nothing_was_lost():
    """npcs.md is REFERENCE now. The write-ups are archived, not deleted."""
    npcs = os.path.join(CAMPAIGN, 'npcs.md')
    assert os.path.exists(npcs)
    assert len(open(npcs, encoding='utf-8').read().split('\n')) < 700, (
        'npcs.md has grown back into a narrative. It is the roster; the '
        'write-ups live in campaign/sessions/')
    files = sorted(f for f in os.listdir(SESSIONS) if f.startswith('day-'))
    assert len(files) >= 24, files


def test_every_session_file_says_it_is_an_archive():
    """So nobody -- including the DM -- reads one to answer a question."""
    for fn in sorted(os.listdir(SESSIONS)):
        if not fn.endswith('.md'):
            continue
        head = open(os.path.join(SESSIONS, fn), encoding='utf-8').read(400)
        assert 'ARCHIVE' in head, fn
        assert 'NEVER to answer a question' in head, fn


def test_every_scene_cites_evidence_that_exists():
    """A citation is a file under campaign/, or ANOTHER SCENE.

    The scene-id form was accepted by log.check_evidence from 2026-09-14 and
    rejected here on the same day, because the two checkers were written at
    different times and only one of them knew about it. A scene citing a scene
    is the natural way to say "this corrects the one above" -- 83:5 does exactly
    that -- so it is legal, AND THE SCENE IT NAMES MUST EXIST.
    """
    ids = {'%s:%s' % (s.get('day'), s.get('seq')) for s in entities.scenes()}
    missing = []
    for s in entities.scenes():
        ev = (s.get('evidence') or '').strip()
        if not ev:
            missing.append('%s:%s has no evidence' % (s.get('day'), s.get('seq')))
            continue
        head = ev.split(':')[0].split('#')[0].strip()
        if head.isdigit():
            if ev.split('#')[0].strip() not in ids:
                missing.append('%s:%s cites SCENE %r, which does not exist'
                               % (s.get('day'), s.get('seq'), ev))
            continue
        if not os.path.exists(os.path.join(CAMPAIGN, head)):
            missing.append('%s:%s cites %r, which does not exist'
                           % (s.get('day'), s.get('seq'), ev))
    assert not missing, missing


def test_the_two_evidence_CHECKERS_agree():
    """log.check_evidence runs on write; the test above runs on the committed
    data. They disagreed on day 81 -- log.py took a scene id and this file
    rejected it -- which means a row could be written and then fail the suite.
    Whatever one accepts, the other must."""
    import log
    for ev in ('articles.md', 'articles.md:913', 'sessions/day-077.md:12', '83:4'):
        log.check_evidence(ev)                      # must not raise
    with pytest.raises(log.Refused):
        log.check_evidence('not a citation at all')


def test_the_session_files_carry_the_days_the_calendar_knows_about():
    """A day with a write-up must be a day the campaign agrees happened."""
    import loops
    days = {int(re.search(r'day-(\d+)', f).group(1))
            for f in os.listdir(SESSIONS) if f.startswith('day-')}
    assert max(days) <= loops.current_day(), (
        'a session file is dated past the current campaign day')


def test_log_py_REFUSES_evidence_that_is_a_sentence_not_a_citation():
    import log
    with pytest.raises(log.Refused) as e:
        log.check_evidence('articles.md art.7, the sellable-before-shearing clause')
    assert 'does not resolve' in str(e.value)
    assert 'NOT A CITATION' in str(e.value)


def test_log_py_ACCEPTS_the_three_shapes_that_ARE_citations():
    """A bare file, a file:line, and a scene id. None of these may raise."""
    import log
    for ev in ('articles.md', 'articles.md:913', 'sessions/day-077.md:12',
               '77:1', ''):
        log.check_evidence(ev)


def test_the_checker_is_PURE_and_writes_nothing():
    """The first version of this test called do_interaction and put a probe row
    into campaign/interactions.tsv -- the exact leak conftest.py exists to
    prevent, reintroduced by a test written to prevent a different one."""
    import log
    before = open(os.path.join(CAMPAIGN, 'interactions.tsv'),
                  encoding='utf-8').read()
    try:
        log.check_evidence('not a citation at all')
    except log.Refused:
        pass
    log.check_evidence('articles.md')
    after = open(os.path.join(CAMPAIGN, 'interactions.tsv'),
                 encoding='utf-8').read()
    assert before == after, 'the evidence checker wrote to the campaign log'
