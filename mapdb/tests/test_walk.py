"""`dmap.py walk` -- advance until there is something to stop for.

Built day 139 alongside `light`, to replace guessing a destination and
retrying against `party.py move`'s REFUSED errors, which is how tonight's
"advance until something changes" declarations kept eating three attempts
each. The stop conditions are the player's own list: a junction (a real
choice, so it stops and hands back rather than picking), a dead end, an
area-label change, or a feature already visible to the party -- and
deliberately NOT merely stepping onto ground nobody has walked before, since
a long plain corridor should not stop every ten feet.
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dmap                                                       # noqa: E402


def make_db(tmp_path, cells, edges, rooms=(), secrets_seen=()):
    """`cells`: {(x,y): terrain} or {(x,y): (terrain, room, feature)} or
    {(x,y): (terrain, room, feature, passage)}. `edges`: {(x,y,orient): kind}.
    `secrets_seen`: [(x,y,orient)] already found by the party."""
    schema = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'schema.sql')
    db = str(tmp_path / 'walk.sqlite')
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    con.execute('INSERT INTO levels (level,name) VALUES (1,?)', ('test',))
    for (x, y), v in cells.items():
        if isinstance(v, tuple):
            terrain, room, feature = v[0], v[1], v[2]
            passage = v[3] if len(v) > 3 else None
        else:
            terrain, room, feature, passage = v, None, None, None
        con.execute('INSERT INTO cells (level,x,y,terrain,room,feature,'
                    'passage,confidence) VALUES (1,?,?,?,?,?,?,10)',
                    (x, y, terrain, room, feature, passage))
    seen = set(secrets_seen)
    for (x, y, o), kind in edges.items():
        con.execute('INSERT INTO edges (level,x,y,orient,kind,seen,'
                    'confidence) VALUES (1,?,?,?,?,?,10)',
                    (x, y, o, kind, 1 if (x, y, o) in seen else 0))
    for number, name, ax, ay in rooms:
        con.execute('INSERT INTO rooms (level,number,name,anchor_x,anchor_y)'
                    ' VALUES (1,?,?,?,?)', (number, name, ax, ay))
    con.commit(); con.close()
    return db


def corridor(tmp_path, n, room_at=None):
    """A straight open corridor (0,0)..(n,0). `room_at` optionally maps
    x -> room number for some cells, everything else unlabeled."""
    room_at = room_at or {}
    cells = {(x, 0): ('open', room_at.get(x), None) for x in range(n + 1)}
    edges = {(x, 0, 'V'): 'open' for x in range(n)}
    return cells, edges


# ------------------------------------------------------- the plain case

def test_walks_a_featureless_corridor_to_its_dead_end(tmp_path):
    cells, edges = corridor(tmp_path, 5)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'][-1] == (5, 0)
    assert len(r['path']) == 6, 'every square walked, start included'


def test_does_not_stop_merely_for_new_ground(tmp_path):
    """The explicit non-requirement: a long plain corridor walks straight
    through to its real stop, not one square at a time."""
    cells, edges = corridor(tmp_path, 20)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E', max_squares=100)
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'][-1] == (20, 0)


def test_no_way_that_direction_is_a_dead_end_of_one(tmp_path):
    cells, edges = corridor(tmp_path, 3)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'N')
    assert r['stop'] == dmap.STOP_DEAD_END
    assert r['path'] == [(0, 0)]


# ------------------------------------------------------------- junctions

def test_a_three_way_junction_stops_and_names_both_new_directions(tmp_path):
    # a corridor east, with a branch north partway along
    cells, edges = corridor(tmp_path, 4)
    cells[(2, 1)] = ('open', None, None)
    edges[(2, 0, 'H')] = 'open'
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_JUNCTION
    assert r['path'][-1] == (2, 0)
    dirs = sorted(d for d, _ in r['options'])
    assert dirs == ['E', 'N']


def test_a_junction_does_not_count_the_way_just_walked(tmp_path):
    """Two exits at a cell, one of them being where the party came from,
    is a plain corridor continuing, not a junction."""
    cells, edges = corridor(tmp_path, 4)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END, (
        'every interior cell has a W exit back the way it came; that must '
        'not itself register as a second option')


# ------------------------------------------------------------ area boundaries

def test_stops_on_entering_a_labelled_room(tmp_path):
    cells, edges = corridor(tmp_path, 4, room_at={3: '12', 4: '12'})
    db = make_db(tmp_path, cells, edges, rooms=[('12', 'Library', 3, 0)])
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_AREA
    assert r['path'][-1] == (3, 0)


def test_stops_on_leaving_a_labelled_room_too(tmp_path):
    cells, edges = corridor(tmp_path, 4, room_at={0: '12', 1: '12'})
    db = make_db(tmp_path, cells, edges, rooms=[('12', 'Library', 0, 0)])
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_AREA
    assert r['path'][-1] == (2, 0), 'stops the instant it leaves room 12'


# ------------------------------------------------------------------- features

def test_stops_at_a_cell_feature(tmp_path):
    cells, edges = corridor(tmp_path, 4)
    cells[(3, 0)] = ('open', None, 'stairs')
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_FEATURE
    assert 'stairs' in r['why']
    assert r['path'][-1] == (3, 0)


def test_stops_at_a_found_secret_door_but_not_an_unfound_one(tmp_path):
    cells, edges = corridor(tmp_path, 4)
    edges[(3, 0, 'H')] = 'secret'
    db = make_db(tmp_path, cells, edges)  # not marked seen
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END, (
        'an unfound secret door is invisible to the party, same as it is '
        'to a passing glance -- it must not leak a stop')

    db2 = make_db(tmp_path, cells, edges, secrets_seen=[(3, 0, 'H')])
    r2 = dmap.walk_until(db2, 1, (0, 0), 'E')
    assert r2['stop'] == dmap.STOP_FEATURE
    assert 'secret' in r2['why']
    assert r2['path'][-1] == (3, 0)


# ------------------------------------------------------------------------ cap

def test_the_safety_cap_fires_before_a_pathological_walk_runs_forever(tmp_path):
    cells, edges = corridor(tmp_path, 50)
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'E', max_squares=10)
    assert r['stop'] == dmap.STOP_CAPPED
    assert len(r['path']) == 11


# ------------------------------------------------------- loops vs. real forks
#
# Built day 140 after B1 level 2's alcove at (6,8)-(10,8): two raw exits at a
# junction both looked like choices, but both only curled back through
# squares already `seen` before either reached anything new. A plain
# "does this branch ever reach unseen ground" check still isn't enough --
# walking EITHER way around a loop eventually reaches the loop's one real
# exit, so a per-branch check calls both of them real. `frontier_exits`
# floods the whole connected bubble of already-seen ground at once and
# reduces it to the distinct first steps that reach a NEW frontier, so two
# directions around the same loop collapse into the one real option.

def _loop_with_one_exit(tmp_path, exit_cell=None):
    """(0,0) --E-- (1,0), which forks N to (1,1) and E to (2,0); those
    rejoin via (1,1)-E-(2,1)-S-(2,0), a closed 4-cycle. `exit_cell`, if
    given, hangs one more cell off (2,0) to the south, left unseen -- the
    loop's only real way on. Everything in the loop itself is marked
    `seen`, standing in for ground the party mapped earlier."""
    cells = {(0, 0): 'open', (1, 0): 'open', (1, 1): 'open',
              (2, 1): 'open', (2, 0): 'open'}
    edges = {(0, 0, 'V'): 'open',   # (0,0)-E-(1,0)
             (1, 0, 'H'): 'open',   # (1,0)-N-(1,1)
             (1, 0, 'V'): 'open',   # (1,0)-E-(2,0)
             (1, 1, 'V'): 'open',   # (1,1)-E-(2,1)
             (2, 0, 'H'): 'open'}   # (2,0)-N-(2,1)
    if exit_cell:
        cells[exit_cell] = 'open'
        edges[(exit_cell[0], exit_cell[1], 'H')] = 'open'  # (2,0)-S-exit_cell
    db = make_db(tmp_path, cells, edges)
    dmap.mark_seen(db, 1, [(1, 1), (2, 1), (2, 0)])
    return db


def test_two_raw_ways_around_one_closed_loop_is_not_a_junction(tmp_path):
    db = _loop_with_one_exit(tmp_path)
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_CLOSED_LOOP, (
        'N and E out of (1,0) both only loop back into already-seen '
        'ground; neither is a real choice, and there is nothing unseen '
        'anywhere nearby')
    assert r['path'][-1] == (1, 0)


def test_a_loop_with_one_real_exit_is_walked_through_not_offered_as_a_fork(
        tmp_path):
    db = _loop_with_one_exit(tmp_path, exit_cell=(2, -1))
    r = dmap.walk_until(db, 1, (0, 0), 'E')
    assert r['stop'] == dmap.STOP_DEAD_END, (
        'the loop has exactly one real way on -- south off (2,0) -- so the '
        'walk should pass silently through the loop and stop at the real '
        'dead end, never pausing at (1,0) to offer N/E as if they led '
        'somewhere different')
    assert r['path'] == [(0, 0), (1, 0), (2, 0), (2, -1)]


def test_frontier_exits_collapses_a_loop_directly(tmp_path):
    db = _loop_with_one_exit(tmp_path, exit_cell=(2, -1))
    cells, edges = dmap.load(db, 1)
    seen = dmap.load_seen(db, 1)
    real = dmap.frontier_exits(cells, edges, seen, (1, 0), (0, 0))
    assert len(real) == 1, 'N and E both lead to the one exit -- one option'
    assert real[0][1] == (2, 0), 'the direction whose bubble found it first'


# ------------------------------------------------------ a fork needs structure
#
# Built day 140, the SAME session, on B1 level 2's (6,6): "south" and "west"
# both reached genuinely different unseen ground, so `frontier_exits` was
# right to call both real -- but the player asked whether anything actually
# separated them, and nothing did. The page render shows one winding cave
# passage, no wall anywhere in it. Two directions that eventually diverge are
# not yet a fork if nothing stands between them where they leave the cell.

def _widening_pocket(tmp_path):
    """(5,5) --S-- (5,4), an open pocket with two ways on: S to (5,3), W to
    (4,4). The corner between S and W (the pocket's SW corner) is open on
    every cell and edge that meets there -- nothing separates the two
    paths, matching (6,6)'s S/W corner on the real map."""
    cells = {(5, 5): 'open', (5, 4): 'open', (5, 3): 'open',
             (4, 4): 'open', (4, 3): 'open'}
    edges = {(5, 4, 'H'): 'open',   # (5,5)-S-(5,4)
             (5, 3, 'H'): 'open',   # (5,4)-S-(5,3)
             (4, 4, 'V'): 'open',   # (5,4)-W-(4,4)
             (4, 3, 'V'): 'open',   # corner: east side of (4,3)
             (4, 3, 'H'): 'open'}   # corner: north side of (4,3)
    return make_db(tmp_path, cells, edges)


def test_two_open_edges_of_one_pocket_are_not_a_fork(tmp_path):
    db = _widening_pocket(tmp_path)
    cells, edges = dmap.load(db, 1)
    edge_states = dmap.load_edge_states(db, 1)
    seen = dmap.load_seen(db, 1)
    real = dmap.frontier_exits(cells, edges, seen, (5, 4), (5, 5))
    assert sorted(d for d, _ in real) == ['S', 'W'], (
        'both S and W genuinely reach different unseen ground -- '
        'frontier_exits alone is right to call them both real')
    reduced = dmap.structural_options(cells, edges, edge_states, (5, 4),
                                       (5, 5), real)
    assert len(reduced) == 1, (
        'nothing separates them -- the corner between S and W is open, so '
        'this is one pocket widening, not a fork')


def test_walk_does_not_stop_at_a_widening_pocket(tmp_path):
    # capped short, before the pocket's edges loop back around to (5,4) --
    # this test is only about NOT stopping at (5,4) itself on the way in.
    db = _widening_pocket(tmp_path)
    r = dmap.walk_until(db, 1, (5, 5), 'S', max_squares=2)
    assert r['stop'] == dmap.STOP_CAPPED
    assert (5, 4) in r['path'][:-1], (
        'the pocket was walked through, not stopped at, on the way in')


def test_a_real_wall_between_two_directions_still_forks(tmp_path):
    """The control case: same shape, but the SW corner is now blocked by a
    solid cell at (4,3). S and W must stay two separate real options."""
    cells = {(5, 5): 'open', (5, 4): 'open', (5, 3): 'open', (4, 4): 'open',
             (4, 3): 'solid'}
    edges = {(5, 4, 'H'): 'open', (5, 3, 'H'): 'open', (4, 4, 'V'): 'open'}
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (5, 5), 'S')
    assert r['stop'] == dmap.STOP_JUNCTION
    assert r['path'][-1] == (5, 4)
    assert sorted(d for d, _ in r['options']) == ['S', 'W']


def test_a_direction_that_merges_with_came_from_is_dropped_not_kept(tmp_path):
    """The case a working run against the real map found that neither
    earlier fix caught: a direction can be transitively one pocket with
    `came_from` ITSELF, not just with a sibling option. B1 level 2's
    (3,9) -- entered from the south -- had "north" (genuinely separate)
    and "west" (which corner-connects back to south, the way the party
    just came from) both reported as real. West isn't a second choice;
    it's the same pocket the party is standing in. Only north should
    survive, not two options with west picked as an arbitrary stand-in
    for "the pocket you're already in."""
    cells = {(0, 0): 'open', (0, -1): 'open', (-1, -1): 'open',
             (-1, 0): 'open', (0, 1): 'open'}
    edges = {(0, -1, 'H'): 'open',    # (0,0)-S-(0,-1), the way in
             (-1, 0, 'V'): 'open',    # (0,0)-W-(-1,0)
             (0, 0, 'H'): 'open',     # (0,0)-N-(0,1)
             (-1, -1, 'V'): 'open',   # SW corner: east side of (-1,-1)
             (-1, -1, 'H'): 'open'}   # SW corner: north side of (-1,-1)
    db = make_db(tmp_path, cells, edges)
    cells_, edges_ = dmap.load(db, 1)
    edge_states = dmap.load_edge_states(db, 1)
    seen = dmap.load_seen(db, 1)
    real = dmap.frontier_exits(cells_, edges_, seen, (0, 0), (0, -1))
    assert sorted(d for d, _ in real) == ['N', 'W']
    reduced = dmap.structural_options(cells_, edges_, edge_states, (0, 0),
                                       (0, -1), real)
    assert reduced == [('N', (0, 1))], (
        '"west" corner-connects to south (came_from) -- it must be '
        'dropped entirely, not offered as a second real choice')


def test_a_door_is_real_structure_even_though_its_walkable(tmp_path):
    """A door blocks light (unless recorded open), so it blocks the corner
    check too even though a party can walk through it. Same
    widening-pocket shape, but the S edge out of (5,4) is now a shut door
    instead of open floor -- S and W must stay separate choices."""
    cells = {(5, 5): 'open', (5, 4): 'open', (5, 3): 'open', (4, 4): 'open',
             (4, 3): 'open'}
    edges = {(5, 4, 'H'): 'open', (5, 3, 'H'): 'door', (4, 4, 'V'): 'open',
             (4, 3, 'V'): 'open', (4, 3, 'H'): 'open'}
    db = make_db(tmp_path, cells, edges)
    cells_, edges_ = dmap.load(db, 1)
    edge_states = dmap.load_edge_states(db, 1)
    seen = dmap.load_seen(db, 1)
    real = dmap.frontier_exits(cells_, edges_, seen, (5, 4), (5, 5))
    reduced = dmap.structural_options(cells_, edges_, edge_states, (5, 4),
                                       (5, 5), real)
    assert len(reduced) == 2, (
        'the shut door to the south is real structure -- S and W must '
        'stay separate choices even though the door is walkable')


def test_opposite_directions_merge_transitively_through_came_from(tmp_path):
    """The case the first corner-only attempt missed: N/S and E/W share no
    single lattice corner, so a pairwise check between just the two of
    them never catches this. But B1 level 2's (5,4) is exactly this shape
    -- "east" and "west", entered from the north -- and it needed fixing
    too. E and W each corner-connect to N (the direction just walked, not
    itself offered) via a diagonal cell open on both sides, so they merge
    transitively through it. No cell south of the junction is defined, so
    S is never a raw option at all -- only E and W are on offer."""
    cells = {(5, 6): 'open', (5, 5): 'open', (6, 5): 'open',
             (4, 5): 'open', (6, 6): 'open', (4, 6): 'open'}
    edges = {(5, 5, 'H'): 'open',   # (5,6)-S-(5,5), the way in
             (5, 5, 'V'): 'open',   # (5,5)-E-(6,5)
             (4, 5, 'V'): 'open',   # (5,5)-W-(4,5)
             (5, 6, 'V'): 'open',   # NE corner: (5,6)-E-(6,6)
             (6, 5, 'H'): 'open',   # NE corner: (6,5)-N-(6,6)
             (4, 6, 'V'): 'open',   # NW corner: (4,6)-E-(5,6)
             (4, 5, 'H'): 'open'}   # NW corner: (4,5)-N-(4,6)
    db = make_db(tmp_path, cells, edges)
    cells_, edges_ = dmap.load(db, 1)
    edge_states = dmap.load_edge_states(db, 1)
    seen = dmap.load_seen(db, 1)
    real = dmap.frontier_exits(cells_, edges_, seen, (5, 5), (5, 6))
    assert sorted(d for d, _ in real) == ['E', 'W']
    reduced = dmap.structural_options(cells_, edges_, edge_states, (5, 5),
                                       (5, 6), real)
    assert len(reduced) == 1, (
        'E and W are opposite, not adjacent, but both corner-connect to '
        'N (came_from) through this open 3x3 block -- one pocket, not a '
        'fork')


def test_b1_level_2_54_east_west_is_not_a_fork(tmp_path):
    """The actual regression: B1 level 2's (5,4). "East" (to (6,4)) and
    "west" (to (4,4)) both looked like a real fork -- frontier_exits is
    right that they reach different unseen ground -- but the player asked
    whether anything separated them, and the page render confirmed no:
    one open pocket, no wall in it anywhere. The walk should pass straight
    through (5,4) rather than stopping there. Where it eventually DOES
    stop is not pinned here -- it already moved once when a separate bug
    (a false 'outside'/frame-scenery tag nearby) got corrected, and a
    direction's exact far endpoint isn't the thing this regression is
    about."""
    db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'output', 'b1', 'b1.sqlite')
    if not os.path.exists(db):
        pytest.skip('map not built')
    r = dmap.walk_until(db, 2, (6, 7), 'S')
    assert (5, 4) in r['path'][:-1], (
        '(5,4) must be walked through, not stopped at -- there is no wall '
        'between its east and west')


def test_b1_level_2_2_9_is_not_tagged_outside(tmp_path):
    """Day 140: (2,9) carried a false `feature='outside'` -- the extractor's
    frame-scenery sweep catches anything non-'open' within 2 columns of the
    sheet's edge, and (2,9) is 'mixed' terrain there, not 'open'. The DM read
    the tag mid-session and narrated an invented second cave mouth from a
    data-pipeline housekeeping marker. Confirmed against the page render:
    real connected cave floor. Corrected in `b1_lv2_corrections.tsv`, along
    with the 25 other 'outside'+'mixed' cells reachable from the explored
    interior the same way; 24 more are NOT reachable and were left alone."""
    db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'output', 'b1', 'b1.sqlite')
    if not os.path.exists(db):
        pytest.skip('map not built')
    cells, _ = dmap.load(db, 2)
    assert cells[(2, 9)][2] is None, (
        '(2,9) must not carry the outside/frame-scenery tag -- it is real '
        'cave floor, confirmed against the page render')


# -------------------------------------------------------- diagonal corner-steps
#
# Found day 140 at B1 level 2's (7,18): orthogonally walled on N, E and W,
# it reported a dead end. `reachable()` has known about diagonal corner-steps
# between two 'diagonal'/'diagonal_half'-passage cells since day 139 -- a
# half-width 45-degree corridor connects only at the corner, no floor at all
# on the squares that would bridge it orthogonally -- but `exits()`, the
# primitive under frontier_exits/walk_until/structural_options AND
# party.py's find_path, never implemented it. Checked against the real map:
# (7,18) itself isn't diagonal-tagged (its own rock touches three sides, not
# the two-ADJACENT-sides pattern the classifier requires), so this specific
# dead end holds up -- but 38 OTHER cells on level 2 had a diagonal-only
# neighbour the old exits() could never see, including (6,7), right where
# today's exploration started.

def test_exits_adds_no_diagonal_step_without_cells(tmp_path):
    """Backward compatible: omitting `cells` is the pre-existing contract
    (several callers still rely on it), and must not change."""
    cells = {(0, 0): ('mixed', None, None, 'diagonal'),
             (1, 1): ('mixed', None, None, 'diagonal')}
    db = make_db(tmp_path, cells, {})
    cells_, edges_ = dmap.load(db, 1)
    assert dmap.exits((0, 0), edges_) == []


def test_exits_steps_corner_to_corner_between_two_diagonal_cells(tmp_path):
    cells = {(0, 0): ('mixed', None, None, 'diagonal'),
             (1, 1): ('mixed', None, None, 'diagonal')}
    db = make_db(tmp_path, cells, {})
    cells_, edges_ = dmap.load(db, 1)
    assert dmap.exits((0, 0), edges_, cells=cells_) == [('NE', (1, 1))]
    assert dmap.exits((1, 1), edges_, cells=cells_) == [('SW', (0, 0))]


def test_exits_does_not_step_unless_both_cells_are_diagonal(tmp_path):
    """One cell carrying the tag is not enough -- B1's (7,18) is the real
    example: its SE neighbour (8,17) is diagonal-tagged, but (7,18) itself
    is not, so nothing connects them this way."""
    cells = {(0, 0): ('mixed', None, None, None),
             (1, 1): ('mixed', None, None, 'diagonal')}
    db = make_db(tmp_path, cells, {})
    cells_, edges_ = dmap.load(db, 1)
    assert dmap.exits((0, 0), edges_, cells=cells_) == []


def test_walk_until_takes_a_diagonal_step_instead_of_stopping_short(tmp_path):
    """The actual shape of the bug: a cell walled on every orthogonal side
    but one -- the one behind the party -- with its only way on a diagonal
    corner-step. Without `cells` wired through, the walk stopped dead at
    (0,-1) and called it STOP_DEAD_END; the diagonal cell one step further,
    (1,-2), was invisible to it. (1,-2) genuinely has no exits of its own
    in this tiny test map, so the walk still ends in a dead end -- the
    fix is that it gets there, rather than stopping one square short."""
    cells = {(0, 0): 'open', (0, -1): ('mixed', None, None, 'diagonal'),
             (1, -2): ('mixed', None, None, 'diagonal')}
    edges = {(0, -1, 'H'): 'open'}   # (0,0)-S-(0,-1), the only orthogonal way
    db = make_db(tmp_path, cells, edges)
    r = dmap.walk_until(db, 1, (0, 0), 'S')
    assert r['path'] == [(0, 0), (0, -1), (1, -2)], (
        'the diagonal step to (1,-2) must be taken, not missed')
    assert r['stop'] == dmap.STOP_DEAD_END, '(1,-2) genuinely has no exits'


def test_b1_level_2_exits_matches_reachable_across_the_whole_level(tmp_path):
    """Cross-check against the independently-built, already-validated
    `reachable()` (used for the day-139 audit): now that `exits()` knows
    about diagonal corner-steps too, a plain BFS with it should reach
    EXACTLY the same walkable cells `reachable()` does, from the same
    start. Agreement here is the strongest evidence the fix is complete,
    not just correct on the one cell that found it."""
    import collections
    db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'output', 'b1', 'b1.sqlite')
    if not os.path.exists(db):
        pytest.skip('map not built')
    cells, edges = dmap.load(db, 2)
    start = (21, 10)
    walk = {k for k, v in cells.items()
            if v[0] in dmap.WALKABLE and (v[2] or '') not in ('stream', 'outside')}
    seen = {start}
    q = collections.deque([start])
    while q:
        cur = q.popleft()
        for _, n in dmap.exits(cur, edges, cells=cells):
            if n in seen or n not in walk:
                continue
            seen.add(n); q.append(n)
    reachable_report = dmap.reachable(db, 2, start=start)[0]
    assert ('reached %d' % len(seen)) in reachable_report
    assert 'UNREACHED 0' in reachable_report
