"""Integration tests against the real DMG sample-dungeon page.

These assert facts about the printed page that a human has verified by eye, not
whatever the code happened to produce. Where a number could drift with a
threshold change it is bounded rather than pinned.
"""
import sqlite3

import pytest

import extract as E

pytestmark = pytest.mark.integration


def test_grid_matches_five_squares_per_inch(dmg_grid):
    """0.2 inch per square at 200 dpi = 40 px. The sheet is graph paper."""
    _, grid = dmg_grid
    assert grid.px == pytest.approx(40.5, abs=0.6)
    assert grid.py == pytest.approx(40.6, abs=0.6)
    assert grid.nx == 35
    assert grid.ny == 48


def test_sheet_is_square_on_the_page(dmg_render, dmg_grid):
    grey, _ = dmg_render
    field, grid = dmg_grid
    rot = E.rotation_check(grey, field, grid.px)
    assert abs(rot['angle_deg']) < 0.1, 'DMG sheet is not skewed; B1 is'


def test_rock_is_most_of_the_page_and_ink_is_slight(dmg_masks):
    rock, ink = dmg_masks
    assert 0.5 < rock.mean() < 0.7
    assert 0.001 < ink.mean() < 0.02
    assert not (rock & ink).any()


def test_ink_layer_holds_the_room_numbers(dmg_render, dmg_masks, dmg_grid):
    """Numerals must not be counted as rock, or numbered rooms read as filled."""
    grey, _ = dmg_render
    _, ink = dmg_masks
    field, grid = dmg_grid
    import ocr_labels as O
    boxes = O.merge(O.components(ink, field))
    assert len(boxes) > 30, 'expected a label per keyed area'
    heights = [b[3] - b[1] for b in boxes]
    assert 20 < sum(heights) / len(heights) < 40, 'labels are ~29px at 200 dpi'


@pytest.mark.parametrize('x,y', [(9, 43), (13, 43), (12, 27), (8, 38)])
def test_verified_room_anchors_sit_on_open_floor(dmg_db, x, y):
    """Areas 4, 5, 3 and 2 are chambers; their label squares must be walkable."""
    con = sqlite3.connect(dmg_db)
    terrain = con.execute('SELECT terrain FROM cells WHERE level=1 AND x=? AND y=?',
                          (x, y)).fetchone()[0]
    con.close()
    assert terrain in ('open', 'mixed')


def test_area_3_has_a_secret_door_in_its_south_wall(dmg_db):
    """DMG p.94: area 3 'appears to be a dead end'; the S at (12,24) is the door."""
    con = sqlite3.connect(dmg_db)
    kind = con.execute("SELECT kind FROM edges WHERE level=1 AND x=12 AND y=24"
                       " AND orient='H'").fetchone()[0]
    con.close()
    assert kind == 'secret'


def test_staircase_between_areas_4_and_5_is_found(dmg_db):
    con = sqlite3.connect(dmg_db)
    n = con.execute("SELECT COUNT(*) FROM cells WHERE level=1 AND feature='stairs'"
                    " AND x=12 AND y BETWEEN 41 AND 43").fetchone()[0]
    con.close()
    assert n == 3


def test_class_counts_are_in_the_expected_range(dmg_db):
    con = sqlite3.connect(dmg_db)
    got = dict(con.execute('SELECT terrain, COUNT(*) FROM cells WHERE level=1'
                           ' GROUP BY terrain'))
    con.close()
    assert got['solid'] + got['open'] + got['mixed'] == 35 * 48
    assert 950 < got['solid'] < 1100
    assert 500 < got['open'] < 650
    assert 60 < got['mixed'] < 160


def test_doors_are_found_and_are_not_absurd(dmg_db):
    con = sqlite3.connect(dmg_db)
    n = con.execute("SELECT COUNT(*) FROM edges WHERE level=1 AND kind='door'"
                    ).fetchone()[0]
    con.close()
    assert 25 < n < 60


def test_no_passable_edge_leads_into_rock(dmg_db):
    import dmap
    assert 'no contradictions found' in dmap.check(dmg_db, 1)


def test_every_cell_and_edge_is_recorded_once(dmg_db):
    con = sqlite3.connect(dmg_db)
    cells = con.execute('SELECT COUNT(*), COUNT(DISTINCT x||","||y) FROM cells'
                        ' WHERE level=1').fetchone()
    edges = con.execute('SELECT COUNT(*), COUNT(DISTINCT x||","||y||orient)'
                        ' FROM edges WHERE level=1').fetchone()
    con.close()
    assert cells[0] == cells[1]
    assert edges[0] == edges[1]
    assert edges[0] == 2 * cells[0], 'one V and one H edge per cell'


def test_cell_edges_view_agrees_with_the_edges_table(dmg_db):
    con = sqlite3.connect(dmg_db)
    bad = con.execute(
        "SELECT COUNT(*) FROM cell_edges WHERE (orient='V' AND (bx<>ax+1 OR by<>ay))"
        " OR (orient='H' AND (bx<>ax OR by<>ay+1))").fetchone()[0]
    con.close()
    assert bad == 0
