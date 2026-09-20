"""The view is DERIVED, its keys are real, and staleness is a comparison.

**The database is not a second store.** The TSVs are the source of record; this
is a materialised view rebuilt from them and gitignored -- the pattern `mapdb/`
has used since the beginning, whose own help says *"world_changes.tsv is the
source of record; the map database is a cache."*

So there is no diff check between two copies. There are two different things,
and conflating them was a mistake in the first draft of the plan:

    STALENESS  was the view rebuilt from the current logs?  -> a WATERMARK
    VALIDITY   does every name resolve, does every close cite evidence?
               -> the log validated against ITSELF

WHAT THE KEYS MAKE UNREPRESENTABLE -- all four of these actually happened:

    the spike phantom negative   two labels for one door, (14,29,H) and
                                 (14,28,H), the ledger holding +2 at one and
                                 -2 at the other; two correcting rows were
                                 needed and the first over-corrected to 7
    wrought hanging iron -1      an orphan: minus one object in a corridor
    area 9's glass               a row whose referent had moved
    Wetherby / Wethersby         two towns where there is one

AND THE BUILD FAILS ON A VIOLATION rather than dropping the row. That caught two
dangling citations within a minute of the schema existing: `money.tsv` cited
scene `62:2`, which had never been logged, and `71:4`, which was a typo for
`71:1`. **A view that quietly loses the rows it cannot join looks complete,
which is the worst thing a view can look.**
"""
import os
import sqlite3
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import build_campaign_db as dbmod                                 # noqa: E402
from tsvlog import read_tsv                                       # noqa: E402


@pytest.fixture(scope='module')
def db(tmp_path_factory):
    return dbmod.build(str(tmp_path_factory.mktemp('db') / 'campaign.sqlite'),
                       quiet=True)


def q(db, sql, *args):
    con = dbmod.connect(db)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


# ------------------------------------------------------- it builds at all

def test_the_live_data_builds_without_a_foreign_key_violation(db):
    """If this fails, a row in a TSV cites something that does not exist."""
    assert q(db, 'PRAGMA foreign_key_check') == []


def test_the_tables_that_matter_are_populated(db):
    for table, least in (('people', 40), ('places', 10), ('interactions', 40),
                         ('interaction_person', 90), ('money', 10),
                         ('inventory', 50), ('loop_events', 30),
                         ('hp_log', 40), ('assets', 50)):
        n = q(db, 'SELECT count(*) FROM "%s"' % table)[0][0]
        assert n >= least, '%s has only %d rows' % (table, n)


# ------------------------------------------------------------- the keys

def test_a_scene_naming_an_unknown_person_cannot_be_inserted(db, tmp_path):
    """The interaction_person key is what stops a scene inventing a person."""
    scratch = str(tmp_path / 'x.sqlite')
    dbmod.build(scratch, quiet=True)
    con = sqlite3.connect(scratch)
    con.execute('PRAGMA foreign_keys = ON')
    with pytest.raises(sqlite3.IntegrityError):
        con.execute('INSERT INTO interaction_person VALUES (?,?)',
                    ('77:3', 'wendel'))
    con.close()


def absent_scene_id():
    """A scene citation that CANNOT exist, derived instead of guessed.

    *** BOTH CALLERS USED A HARDCODED ID AND THE CAMPAIGN WALKED INTO IT. ***
    On 2026-09-18, in-game day 99, scene 99 colon 9 was logged -- and two tests
    that had been green for a fortnight went red together. Neither had found a
    bug: they had asserted A FACT ABOUT TODAY'S DATA ("that scene does not
    exist") while claiming to test AN INVARIANT ("a citation to nothing is
    refused").

    This repository has been bitten by pinned game state repeatedly -- see
    test_inventory.py, which carries a comment telling the reader not to pin
    quantities four lines above a pinned quantity. A hardcoded id is the same
    mistake in a different hat: THE CAMPAIGN IS A CLOCK, and any literal drawn
    from its range eventually becomes true.

    So: MAX LOGGED DAY + 1000, read off interactions.tsv at test time. It cannot
    collide unless somebody plays three more years in a single session, and if
    they do, this returns a still-absent id rather than a stale one.
    """
    rows = read_tsv(os.path.join(ROOT, 'campaign', 'interactions.tsv'))
    days = [int(r['day']) for r in rows if (r.get('day') or '').isdigit()]
    return '%d:1' % (max(days, default=0) + 1000)


def test_money_cannot_cite_a_scene_that_does_not_exist(db, tmp_path):
    """THE ONE THAT FIRED IMMEDIATELY.

    Within a minute of this schema existing it caught `money.tsv` citing scene
    62:2, which had never been logged, and 71:4, which was a typo for 71:1.
    """
    scratch = str(tmp_path / 'y.sqlite')
    dbmod.build(scratch, quiet=True)
    con = sqlite3.connect(scratch)
    con.execute('PRAGMA foreign_keys = ON')
    with pytest.raises(sqlite3.IntegrityError):
        con.execute('INSERT INTO money (day,delta,asset_id,interaction_id) '
                    'VALUES (?,?,?,?)', (77, -1, 'coin', absent_scene_id()))
    con.close()


def test_a_loop_cannot_be_closed_without_evidence(db, tmp_path):
    """The CHECK constraint, not a convention. Closing means CITING.

    This is the step skipped on articles.md art. 11, which then sat open for
    eleven days after it had fired and was quoted as live.
    """
    scratch = str(tmp_path / 'z.sqlite')
    dbmod.build(scratch, quiet=True)
    con = sqlite3.connect(scratch)
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO loop_events (day,loop_id,verb,evidence) "
                    "VALUES (77,'L999','close','')")
    con.close()


def test_day_and_seq_are_unique(db, tmp_path):
    """Other files cite scenes as "77:3" and that must mean one thing."""
    scratch = str(tmp_path / 'u.sqlite')
    dbmod.build(scratch, quiet=True)
    con = sqlite3.connect(scratch)
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO interactions (id,day,seq,kind) "
                    "VALUES ('dup',77,3,'counsel')")
    con.close()


def test_wetherby_and_wethersby_are_one_place(db):
    rows = q(db, "SELECT place_id FROM place_alias WHERE alias IN "
                 "('wetherby','wethersby')")
    assert {r[0] for r in rows} == {'wethersby'}


def test_rells_brother_and_gyll_are_one_person(db):
    rows = q(db, "SELECT person_id FROM person_alias WHERE alias IN "
                 "(\"rell's brother\",'gyll')")
    assert {r[0] for r in rows} == {'gyll'}


# --------------------------------------------------- the joins it exists for

def test_every_reaction_ever_rolled_for_one_person(db):
    """Impossible against flat files, and it is how the p.63 misuse was found:
    a reaction roll at somebody with a prior logged encounter."""
    rows = q(db, """SELECT i.day, i.reaction FROM interactions i
                    JOIN interaction_person ip ON ip.interaction_id = i.id
                    WHERE ip.person_id = 'cuddy' AND i.reaction <> ''
                    ORDER BY i.day""")
    assert len(rows) >= 3


def test_the_ancel_answer_is_reachable_by_join(db):
    """The 43-day error, as a query.

    "Unanswered. He will not sit in the square forever" sat in prose until day
    77. It was answered on day 34 at reaction 127.
    """
    rows = q(db, """SELECT i.day, i.kind, i.reaction FROM interactions i
                    JOIN interaction_person ip ON ip.interaction_id = i.id
                    WHERE ip.person_id = 'ancel' ORDER BY i.day""")
    assert (34, 'negotiation', '127') in rows


def test_open_loops_by_person_is_one_join(db):
    rows = q(db, """SELECT p.name, count(*) FROM loop_events le
                    JOIN people p ON p.id = le.subject_person_id
                    WHERE le.verb='open' AND le.loop_id NOT IN
                          (SELECT loop_id FROM loop_events WHERE verb='close')
                    GROUP BY p.name""")
    assert dict(rows).get('Father Cuddy', 0) >= 3


# ------------------------------------------------------- the watermark

def test_the_freshly_built_view_is_not_stale(db):
    assert dbmod.stale(db) == []


def test_a_changed_source_makes_it_stale(db, tmp_path, monkeypatch):
    """Staleness is a COMPARISON, not a judgment -- which is the whole point.

    CHECKLIST section 11 was 38 in-game days out of date while warning in its
    own second paragraph that snapshots rot. A sha256 per source cannot do that.
    """
    real = dbmod.watermark

    def fake(name):
        n, last, sha = real(name)
        return (n, last, 'deadbeef') if name == 'loops' else (n, last, sha)

    monkeypatch.setattr(dbmod, 'watermark', fake)
    bad = dbmod.stale(db)
    assert [n for n, _ in bad] == ['loops']


def test_every_source_has_a_watermark_row(db):
    stored = {r[0] for r in q(db, 'SELECT source FROM build_meta')}
    assert set(dbmod.SOURCES) == stored


def test_a_missing_view_reports_itself_rather_than_pretending(tmp_path):
    assert dbmod.stale(str(tmp_path / 'nope.sqlite'))


# ------------------------------------------------- it is a view, not a store

def test_consumers_open_it_read_only(db):
    """A stray UPDATE must raise rather than silently rewrite the past."""
    con = dbmod.connect(db)
    with pytest.raises(sqlite3.OperationalError):
        con.execute("UPDATE people SET name='nope' WHERE id='wend'")
    con.close()


def test_log_refuses_a_dangling_scene_citation(tmp_path):
    """The same rule as the foreign key, arriving at the MOMENT of the error.

    A key catches this when the view is next built -- afterwards. `log.py`
    catches it on the way in. **A pointer to nothing looks CHECKED, which is
    worse than no pointer at all.**
    """
    import log as logmod
    scratch = tmp_path / 'money.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign', 'money.tsv'),
                            encoding='utf-8').read())
    before = scratch.read_text()
    assert logmod.main(['--log-file', str(scratch), 'money', '--delta', '-5',
                        '--asset', 'coin', '--interaction', absent_scene_id(),
                        '--reason', 'x']) == 1
    assert scratch.read_text() == before


def test_log_refuses_a_scene_naming_somebody_who_does_not_exist(tmp_path):
    import log as logmod
    scratch = tmp_path / 'interactions.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign', 'interactions.tsv'),
                            encoding='utf-8').read())
    before = scratch.read_text()
    assert logmod.main(['--log-file', str(scratch), 'interaction',
                        '--people', 'Wend, Wendel', '--kind', 'counsel',
                        '--summary', 'x']) == 1
    assert scratch.read_text() == before


def test_log_writes_a_scene_and_tells_you_how_to_cite_it(tmp_path, capsys):
    import log as logmod
    scratch = tmp_path / 'interactions.tsv'
    scratch.write_text(open(os.path.join(ROOT, 'campaign', 'interactions.tsv'),
                            encoding='utf-8').read())
    assert logmod.main(['--log-file', str(scratch), 'interaction',
                        '--people', "Rell's brother, Dave", '--kind', 'payment',
                        '--place', 'Wetherby', '--day', '77',
                        # --evidence is REQUIRED as of day 100: log.py used to
                        # accept a scene with no citation while the data test in
                        # test_entities.py demanded one, so a row could be
                        # written successfully and then fail the suite.
                        '--evidence', 'days.tsv',
                        '--summary', 'an alias on each side resolves']) == 0
    out = capsys.readouterr().out
    assert 'cite this scene as 77:' in out


def test_the_view_is_gitignored_because_it_is_derived():
    ignore = open(os.path.join(ROOT, '.gitignore'), encoding='utf-8').read()
    assert 'campaign/output/' in ignore, (
        'the derived view must not be tracked -- the TSVs are the record, and '
        'a committed cache is a second copy that diverges')
