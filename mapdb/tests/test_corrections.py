"""Functional tests for the human-correction overlay.

The build recreates the database from scratch, so a correction made directly in
SQLite dies at the next run. These tests pin down that corrections survive a
rebuild, win over the classifier, and fail loudly rather than silently when
they no longer match anything.
"""
import os
import sqlite3

import pytest

import build

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'schema.sql')


def tiny_db(path):
    con = sqlite3.connect(path)
    con.executescript(open(SCHEMA).read())
    con.execute("INSERT INTO levels (level,name) VALUES (1,'t')")
    con.execute("INSERT INTO cells (level,x,y,terrain,notes,confidence)"
                " VALUES (1,4,5,'mixed','open=0.40',3)")
    con.execute("INSERT INTO edges (level,x,y,orient,kind,notes,confidence)"
                " VALUES (1,4,5,'H','wall','thick=9',8)")
    con.commit(); con.close()
    return path


def write(path, *rows):
    with open(path, 'w') as fh:
        fh.write('# comment line\n\n')
        for r in rows:
            fh.write('\t'.join(r) + '\n')
    return str(path)


def test_cell_correction_overrides_the_classifier(tmp_path):
    db = tiny_db(str(tmp_path / 'a.sqlite'))
    tsv = write(tmp_path / 'c.tsv',
                ('cell', '4', '5', '-', 'open', 'dl', 'the "32" numeral, not rock'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert (n, problems) == (1, [])
    con = sqlite3.connect(db)
    terrain, conf, notes = con.execute(
        'SELECT terrain,confidence,notes FROM cells WHERE x=4 AND y=5').fetchone()
    con.close()
    assert terrain == 'open'
    assert conf == 10, 'a human looked at the page'
    assert 'CORRECTED by dl' in notes and 'numeral' in notes


def test_edge_correction_applies_to_the_right_orientation(tmp_path):
    db = tiny_db(str(tmp_path / 'b.sqlite'))
    tsv = write(tmp_path / 'c.tsv',
                ('edge', '4', '5', 'H', 'secret', 'dl', 'S marker south wall'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 1 and problems == []
    con = sqlite3.connect(db)
    assert con.execute("SELECT kind FROM edges WHERE x=4 AND y=5 AND orient='H'"
                       ).fetchone()[0] == 'secret'
    con.close()


def test_correction_that_matches_nothing_is_reported(tmp_path):
    """A stale correction must be loud, not silent -- the map may have moved."""
    db = tiny_db(str(tmp_path / 'c.sqlite'))
    tsv = write(tmp_path / 'c.tsv', ('cell', '99', '99', '-', 'open', 'dl', 'stale'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 0
    assert problems and 'matched nothing' in problems[0]


def test_malformed_row_is_reported_and_skipped(tmp_path):
    db = tiny_db(str(tmp_path / 'd.sqlite'))
    tsv = write(tmp_path / 'c.tsv', ('cell', '4'), ('cell', '4', '5', '-', 'open', 'dl'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 1, 'the good row still applies'
    assert any('malformed' in p for p in problems)


def test_non_integer_coordinate_is_reported(tmp_path):
    db = tiny_db(str(tmp_path / 'e.sqlite'))
    tsv = write(tmp_path / 'c.tsv', ('cell', 'x', '5', '-', 'open', 'dl', 'bad'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 0 and any('non-integer' in p for p in problems)


def test_unknown_kind_is_reported(tmp_path):
    db = tiny_db(str(tmp_path / 'f.sqlite'))
    tsv = write(tmp_path / 'c.tsv', ('sofa', '4', '5', '-', 'open', 'dl', ''))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 0 and any('unknown kind' in p for p in problems)


def test_comments_and_blank_lines_are_ignored(tmp_path):
    db = tiny_db(str(tmp_path / 'g.sqlite'))
    tsv = str(tmp_path / 'c.tsv')
    with open(tsv, 'w') as fh:
        fh.write('# header\n\n   \n')
    assert build.apply_corrections(db, tsv, 1, quiet=True) == (0, [])


def test_missing_file_is_not_an_error(tmp_path):
    db = tiny_db(str(tmp_path / 'h.sqlite'))
    assert build.apply_corrections(db, str(tmp_path / 'nope.tsv'), 1, quiet=True) \
        == (0, [])


def test_corrections_are_reapplied_after_a_rebuild(tmp_path):
    """The regression property: rebuild, and the human's calls are still there."""
    db = str(tmp_path / 'i.sqlite')
    tsv = write(tmp_path / 'c.tsv', ('cell', '4', '5', '-', 'open', 'dl', 'n'))
    for _ in range(2):
        if os.path.exists(db):
            os.remove(db)
        tiny_db(db)
        con = sqlite3.connect(db)
        assert con.execute('SELECT terrain FROM cells WHERE x=4').fetchone()[0] == 'mixed'
        con.close()
        build.apply_corrections(db, tsv, 1, quiet=True)
        con = sqlite3.connect(db)
        assert con.execute('SELECT terrain FROM cells WHERE x=4').fetchone()[0] == 'open'
        con.close()


def test_shipped_corrections_file_still_matches(dmg_db):
    """Every row in the real corrections.tsv must still find its target."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tsv = os.path.join(root, 'corrections.tsv')
    if not os.path.exists(tsv):
        pytest.skip('no corrections file')
    n, problems = build.apply_corrections(dmg_db, tsv, 1, quiet=True)
    assert problems == [], 'a correction went stale: %s' % problems
    assert n > 0


def test_member_correction_assigns_a_square_to_a_room(tmp_path):
    """`member` states room membership by hand, for diagonal-walled rooms.

    `extents.py` derives membership by flooding across open boundaries. That
    works wherever walls run along grid lines and fails completely where they do
    not: B1's north-east quadrant is built on 45-degree walls, so the rock sits
    INSIDE the squares, every boundary measures thin and open, and the flood ran
    straight through. Area 34 came out as 41 squares with the Room of Pools'
    own markers inside it, and the party was standing in it at the time.

    A diagonal wall cannot be expressed as an edge correction -- there is no
    edge to correct -- so membership has to be stateable directly.
    """
    db = tiny_db(str(tmp_path / 'm.sqlite'))
    tsv = write(tmp_path / 'm.tsv',
                ('member', '4', '5', '-', '34', 'dl', 'player-documented outline'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert (n, problems) == (1, [])
    con = sqlite3.connect(db)
    room, conf, notes = con.execute(
        'SELECT room,confidence,notes FROM cells WHERE x=4 AND y=5').fetchone()
    con.close()
    assert room == '34'
    assert conf == 10, 'a human read it off the printed map'
    assert 'ROOM SET by dl' in notes


def test_member_correction_that_matches_no_square_is_reported(tmp_path):
    """Silence on a stale correction is the failure mode this file exists for."""
    db = tiny_db(str(tmp_path / 'n.sqlite'))
    tsv = write(tmp_path / 'n.tsv',
                ('member', '99', '99', '-', '34', 'dl', 'off the map'))
    n, problems = build.apply_corrections(db, tsv, 1, quiet=True)
    assert n == 0
    assert len(problems) == 1 and 'matched nothing' in problems[0]
