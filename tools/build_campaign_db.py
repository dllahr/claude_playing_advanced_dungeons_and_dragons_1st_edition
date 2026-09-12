#!/usr/bin/env python3
"""Build campaign/output/campaign.sqlite from the TSVs. A VIEW, not a store.

    python tools/build_campaign_db.py
    python tools/build_campaign_db.py --check      # is it stale? exit 1 if so
    python tools/build_campaign_db.py --query "SELECT ..."

THE TSVs ARE THE SOURCE OF RECORD. This database is a MATERIALISED VIEW of them,
rebuilt by this script and gitignored -- exactly the pattern `mapdb/` has used
since the beginning, whose own help says *"world_changes.tsv is the source of
record; the map database is a cache."*

So there is no redundancy and no diff check between two copies. There are two
different things, and conflating them was a mistake in the first draft of the
plan:

    STALENESS  was the view rebuilt from the current logs?  -> a WATERMARK
    VALIDITY   does every name resolve, does every close cite evidence?
               -> the log validated against ITSELF, not compared to a copy

*** WHY FOREIGN KEYS, CONCRETELY. *** Four errors that actually happened in this
campaign become unrepresentable:

    the spike phantom negative   TWO LABELS FOR ONE DOOR -- (14,29,H) and
                                 (14,28,H), the ledger holding +2 at one name
                                 and -2 at the other. Needed two correcting
                                 rows, the first of which over-corrected to 7
    wrought hanging iron -1      an orphan: minus one object in a corridor
    area 9's glass               a row whose referent had moved, with nothing
                                 linking the two
    Wetherby / Wethersby         two towns where there is one

`PRAGMA foreign_keys` is ON and a violation FAILS THE BUILD. A view that quietly
drops the rows it cannot join is worse than no view, because it looks complete.

READS ARE ANYTHING, INCLUDING AD-HOC SQL -- that is where a database earns its
keep, on joins that cannot be run against flat files. WRITES GO THROUGH
`tools/log.py` AND NOWHERE ELSE, and every other consumer opens this file
READ-ONLY, so a stray UPDATE raises instead of silently rewriting the past.
"""
import argparse
import hashlib
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import entities as entmod                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPAIGN = os.path.join(ROOT, 'campaign')
OUTDIR = os.path.join(CAMPAIGN, 'output')
DB = os.path.join(OUTDIR, 'campaign.sqlite')
MAPDB = os.path.join(ROOT, 'mapdb', 'output', 'b1', 'b1.sqlite')

# Every TSV that feeds the view, and therefore every watermark.
SOURCES = ('people', 'places', 'assets', 'interactions', 'money',
           'inventory_log', 'loops', 'days', 'availability', 'hp_log',
           'encounters', 'rolls', 'clock', 'light', 'spells', 'party',
           'world_changes', 'encounter', 'characters')

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE places (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT,
    parent_id TEXT REFERENCES places(id),
    days_from_wethersby REAL, notes TEXT);

CREATE TABLE place_alias (
    alias TEXT PRIMARY KEY,
    place_id TEXT NOT NULL REFERENCES places(id));

CREATE TABLE people (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT, first_day INTEGER,
    place_id TEXT REFERENCES places(id), notes TEXT);

CREATE TABLE person_alias (
    alias TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES people(id));

CREATE TABLE assets (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT,
    weight REAL, weight_unit TEXT, notes TEXT);

CREATE TABLE interactions (
    id TEXT PRIMARY KEY,             -- "day:seq", which other files cite
    day INTEGER NOT NULL, seq INTEGER NOT NULL,
    place_id TEXT REFERENCES places(id),
    kind TEXT NOT NULL, reaction TEXT, d6s TEXT, summary TEXT, evidence TEXT,
    UNIQUE (day, seq));

CREATE TABLE interaction_person (
    interaction_id TEXT NOT NULL REFERENCES interactions(id),
    person_id TEXT NOT NULL REFERENCES people(id),
    PRIMARY KEY (interaction_id, person_id));

CREATE TABLE money (
    id INTEGER PRIMARY KEY, day INTEGER, delta REAL NOT NULL, unit TEXT,
    asset_id TEXT NOT NULL,          -- 'anchor' is a verb, so no REFERENCES
    qty TEXT, counterparty_id TEXT REFERENCES people(id),
    interaction_id TEXT REFERENCES interactions(id), reason TEXT);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY, day INTEGER,
    asset_id TEXT NOT NULL REFERENCES assets(id),
    verb TEXT NOT NULL, qty REAL, unit TEXT, condition TEXT,
    holder TEXT, evidence TEXT, note TEXT);

CREATE TABLE loop_events (
    id INTEGER PRIMARY KEY, day INTEGER, loop_id TEXT NOT NULL,
    verb TEXT NOT NULL, subject_person_id TEXT REFERENCES people(id),
    expected_day INTEGER, evidence TEXT, what TEXT,
    CHECK (verb <> 'close' OR (evidence IS NOT NULL AND evidence <> '')));

CREATE TABLE hp_log (
    id INTEGER PRIMARY KEY, exped TEXT, turn TEXT,
    person_id TEXT NOT NULL REFERENCES people(id),
    kind TEXT, delta INTEGER, reason TEXT);

CREATE TABLE days (
    day INTEGER PRIMARY KEY, when_ TEXT,
    place_id TEXT REFERENCES places(id), summary TEXT);

CREATE TABLE availability (
    id INTEGER PRIMARY KEY, day INTEGER,
    person_id TEXT NOT NULL REFERENCES people(id),
    status TEXT NOT NULL, until_day INTEGER, why TEXT);

CREATE TABLE build_meta (
    source TEXT PRIMARY KEY, rows INTEGER, last_day INTEGER,
    sha256 TEXT, built_at TEXT);
"""

# The append-only play logs go in verbatim, one table each, columns as written.
# They are queryable and joinable by hand without being modelled -- modelling
# every one of them would be a second schema nobody re-checks against the file.
RAW = ('encounters', 'rolls', 'clock', 'light', 'spells', 'party',
       'world_changes', 'encounter', 'characters')


def _path(name):
    return os.path.join(CAMPAIGN, name + '.tsv')


def watermark(name):
    """(rows, last_day, sha256). Staleness becomes a comparison, not a guess."""
    p = _path(name)
    if not os.path.exists(p):
        return (0, None, '')
    raw = open(p, 'rb').read()
    rows = read_tsv(p, missing_ok=True)
    days = [int(r['day']) for r in rows
            if (r.get('day') or '').strip().isdigit()]
    return (len(rows), max(days) if days else None,
            hashlib.sha256(raw).hexdigest())


def _i(v):
    v = (v or '').strip()
    return int(v) if v.lstrip('-').isdigit() else None


def _f(v):
    try:
        return float((v or '').strip())
    except ValueError:
        return None


def build(db_path=None, quiet=False):
    db_path = db_path or DB
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.unlink(db_path)
    con = sqlite3.connect(db_path)
    con.executescript(DDL)
    # Places point at parent places and rows arrive in file order, so a child
    # can land before its parent. DEFER rather than reorder: the constraint is
    # still enforced, just at COMMIT, and `PRAGMA foreign_key_check` below
    # fails the build on anything that survives.
    con.execute('PRAGMA defer_foreign_keys = ON')
    con.execute('BEGIN')

    pl, pc = entmod.people(), entmod.places()
    pidx, cidx = entmod.index(pl), entmod.index(pc)

    def person(v):
        return pidx.get((v or '').strip().lower())

    def place(v):
        return cidx.get((v or '').strip().lower())

    # places first -- people point at them
    for pid, r in pc.items():
        con.execute('INSERT INTO places VALUES (?,?,?,?,?,?)',
                    (pid, r['name'], r.get('kind'), place(r.get('parent')),
                     _f(r.get('days_from_wethersby')), r.get('notes')))
    for alias, pid in cidx.items():
        con.execute('INSERT OR IGNORE INTO place_alias VALUES (?,?)',
                    (alias, pid))

    for pid, r in pl.items():
        con.execute('INSERT INTO people VALUES (?,?,?,?,?,?)',
                    (pid, r['name'], r.get('kind'), _i(r.get('first_day')),
                     place(r.get('place')), r.get('notes')))
    for alias, pid in pidx.items():
        con.execute('INSERT OR IGNORE INTO person_alias VALUES (?,?)',
                    (alias, pid))

    for r in read_tsv(_path('assets'), missing_ok=True):
        con.execute('INSERT INTO assets VALUES (?,?,?,?,?,?)',
                    (r['id'], r['name'], r.get('kind'), _f(r.get('weight')),
                     r.get('weight_unit'), r.get('notes')))

    for r in entmod.scenes():
        sid = '%s:%s' % (r['day'], r['seq'])
        con.execute('INSERT INTO interactions VALUES (?,?,?,?,?,?,?,?,?)',
                    (sid, _i(r['day']), _i(r['seq']), place(r.get('place')),
                     r.get('kind'), r.get('reaction'), r.get('d6s'),
                     r.get('summary'), r.get('evidence')))
        for n in entmod.split_people(r.get('people')):
            con.execute('INSERT OR IGNORE INTO interaction_person VALUES (?,?)',
                        (sid, person(n)))

    for r in read_tsv(_path('money'), missing_ok=True):
        ix = (r.get('interaction') or '').strip()
        con.execute('INSERT INTO money (day,delta,unit,asset_id,qty,'
                    'counterparty_id,interaction_id,reason) '
                    'VALUES (?,?,?,?,?,?,?,?)',
                    (_i(r.get('day')), _f(r.get('delta')) or 0, r.get('unit'),
                     r['asset'], r.get('qty'), person(r.get('counterparty')),
                     ix if ':' in ix else None, r.get('reason')))

    for r in read_tsv(_path('inventory_log'), missing_ok=True):
        con.execute('INSERT INTO inventory (day,asset_id,verb,qty,unit,'
                    'condition,holder,evidence,note) VALUES (?,?,?,?,?,?,?,?,?)',
                    (_i(r.get('day')), r['asset'], r.get('verb'),
                     _f(r.get('qty')), r.get('unit'), r.get('condition'),
                     r.get('holder'), r.get('evidence'), r.get('note')))

    for r in read_tsv(_path('loops'), missing_ok=True):
        con.execute('INSERT INTO loop_events (day,loop_id,verb,'
                    'subject_person_id,expected_day,evidence,what) '
                    'VALUES (?,?,?,?,?,?,?)',
                    (_i(r.get('day')), r['loop'], r.get('verb'),
                     person(r.get('subject')), _i(r.get('expected_day')),
                     r.get('evidence'), r.get('what')))

    for r in read_tsv(_path('hp_log'), missing_ok=True):
        pid = person(r.get('who'))
        if pid:
            con.execute('INSERT INTO hp_log (exped,turn,person_id,kind,delta,'
                        'reason) VALUES (?,?,?,?,?,?)',
                        (r.get('exped'), r.get('turn'), pid, r.get('kind'),
                         _i(r.get('delta')), r.get('reason')))

    for r in read_tsv(_path('days'), missing_ok=True):
        con.execute('INSERT OR REPLACE INTO days VALUES (?,?,?,?)',
                    (_i(r['day']), r.get('when'), place(r.get('where')),
                     r.get('summary')))

    for r in read_tsv(_path('availability'), missing_ok=True):
        pid = person(r.get('who'))
        if pid:
            con.execute('INSERT INTO availability (day,person_id,status,'
                        'until_day,why) VALUES (?,?,?,?,?)',
                        (_i(r.get('day')), pid, r.get('status'),
                         _i(r.get('until_day')), r.get('why')))

    for name in RAW:
        rows = read_tsv(_path(name), missing_ok=True)
        if not rows:
            continue
        cols = list(rows[0])
        safe = ['"%s"' % c.replace('"', '') for c in cols]
        con.execute('CREATE TABLE "%s" (%s)'
                    % (name, ', '.join('%s TEXT' % c for c in safe)))
        con.executemany('INSERT INTO "%s" VALUES (%s)'
                        % (name, ','.join('?' * len(cols))),
                        [tuple(r.get(c, '') for c in cols) for r in rows])

    import datetime
    now = datetime.datetime.now().isoformat(timespec='seconds')
    for name in SOURCES:
        n, last, sha = watermark(name)
        con.execute('INSERT INTO build_meta VALUES (?,?,?,?,?)',
                    (name, n, last, sha, now))

    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        con.close()
        raise SystemExit(
            'FOREIGN KEY VIOLATIONS -- the build FAILS rather than dropping '
            'the rows it cannot join, because a view that quietly loses rows '
            'looks complete:\n  %s'
            % '\n  '.join(repr(b) for b in bad[:20]))
    con.commit()
    if not quiet:
        counts = {t: con.execute('SELECT count(*) FROM "%s"' % t).fetchone()[0]
                  for (t,) in con.execute(
                      "SELECT name FROM sqlite_master WHERE type='table' "
                      "ORDER BY name")}
        print('built %s' % os.path.relpath(db_path, ROOT))
        for t, n in counts.items():
            print('  %-22s %6d' % (t, n))
    con.close()
    return db_path


def stale(db_path=None):
    """[(source, why)] -- the watermark comparison. Empty means current."""
    db_path = db_path or DB
    if not os.path.exists(db_path):
        return [('(all)', 'campaign.sqlite does not exist -- run '
                          'tools/build_campaign_db.py')]
    con = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
    try:
        stored = {r[0]: r for r in con.execute(
            'SELECT source, rows, last_day, sha256 FROM build_meta')}
    except sqlite3.OperationalError:
        return [('(all)', 'no build_meta -- rebuilt with an older script')]
    finally:
        con.close()
    out = []
    for name in SOURCES:
        n, last, sha = watermark(name)
        s = stored.get(name)
        if s is None:
            out.append((name, 'not in build_meta at all'))
        elif s[3] != sha:
            out.append((name, 'has changed since the build '
                              '(%d rows then, %d now)' % (s[1], n)))
    return out


def connect(db_path=None):
    """READ-ONLY. Every consumer but the builder opens it this way."""
    return sqlite3.connect('file:%s?mode=ro' % (db_path or DB), uri=True)


def build_parser():
    p = argparse.ArgumentParser(
        prog='build_campaign_db.py',
        description='Build the derived view. The TSVs remain the record.')
    p.add_argument('--db', default=DB)
    p.add_argument('--check', action='store_true',
                   help='report staleness and exit 1 if stale')
    p.add_argument('--query', help='run one read-only SELECT against the view')
    p.add_argument('--quiet', action='store_true')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.check:
        bad = stale(a.db)
        for name, why in bad:
            print('STALE %-16s %s' % (name, why))
        if not bad:
            print('campaign.sqlite is current with every source TSV.')
        return 1 if bad else 0
    if a.query:
        con = connect(a.db)
        for row in con.execute(a.query):
            print('\t'.join('' if v is None else str(v) for v in row))
        con.close()
        return 0
    build(a.db, quiet=a.quiet)
    return 0


if __name__ == '__main__':
    sys.exit(main())
