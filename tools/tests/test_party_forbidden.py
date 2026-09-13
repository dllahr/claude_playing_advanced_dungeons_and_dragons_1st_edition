"""The pathfinder may not use a route the campaign has ruled out.

`party.py move` has physically refused to cross a WALL since expedition 6, and
that has held: not one geometry error since. But "legal" meant "not a wall", and
the campaign has a rule the map knows nothing about --

    the x=16 corridor between y=13 and y=19 runs under the MAGIC MOUTHS.
    The party does not walk it. The way in and out is the alcove-pair-2
    one-way slab at (17,13,V).

*** ON DAY 79 THE PATHFINDER PROVED IT. *** Asked for the four-way at (16,19),
it went back out through the secret slab and straight up that corridor -- the
shortest legal path, and the one stretch of level 1 this party does not use. The
rule was in CHECKLIST.md, in prose, where no tool could read it. The player had
named the real route in the same breath and the tool ignored it.

IT REFUSES RATHER THAN REROUTING, on purpose. A silent detour would be the tool
choosing the party's path, which is the same family of error as choosing their
actions. Naming the waypoints is what the player already did.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import party                                                      # noqa: E402


def test_the_magic_mouth_corridor_is_ruled_out():
    for y in range(13, 19):
        assert party.forbidden('b1', 1, 16, y, 'H'), (16, y)
    assert 'MAGIC MOUTHS' in party.forbidden('b1', 1, 16, 13, 'H')


def test_the_way_in_is_not_ruled_out():
    """The slab at (17,13,V) is the route, not the thing forbidden."""
    assert party.forbidden('b1', 1, 17, 13, 'V') is None


def test_the_edge_between_two_squares_is_computed_the_map_way():
    """mapdb convention: V at (x,y) separates (x,y)/(x+1,y); H at (x,y)
    separates (x,y)/(x,y+1). Getting this backwards would make the guard miss
    every edge it exists to catch."""
    assert party.edge_between((16, 13), (16, 14)) == (16, 13, 'H')
    assert party.edge_between((16, 14), (16, 13)) == (16, 13, 'H')
    assert party.edge_between((17, 13), (18, 13)) == (17, 13, 'V')
    assert party.edge_between((18, 13), (17, 13)) == (17, 13, 'V')


def test_a_route_up_the_forbidden_corridor_is_reported():
    steps = [(16, 13), (16, 14), (16, 15), (16, 16)]
    bad = party.forbidden_on(steps, 'b1', 1)
    assert len(bad) == 3
    assert all('magic mouth' in w.lower() for _e, w in bad)


def test_the_named_route_east_of_the_slab_is_clean():
    """What the player actually described: east through the door, left at
    the first junction, north, and west along y=19 to the four-way."""
    steps = ([(17, 13), (18, 13), (19, 13)]
             + [(19, y) for y in range(14, 20)]
             + [(x, 19) for x in (18, 17, 16)])
    assert party.forbidden_on(steps, 'b1', 1) == []


def test_move_refuses_and_writes_nothing(tmp_path):
    """A refusal that has already moved the party is not a refusal."""
    log = tmp_path / 'party.tsv'
    log.write_text(open(os.path.join(ROOT, 'campaign', 'party.tsv'),
                        encoding='utf-8').read())
    before = log.read_text()
    try:
        party.move('16,19', path=str(log), rate='known', why='x')
        raise AssertionError('it did not refuse')
    except ValueError as exc:
        assert 'RULED OUT' in str(exc)
        assert 'magic mouth' in str(exc).lower()
    assert log.read_text() == before


def test_anyway_is_the_deliberate_override_and_is_documented():
    """The party may genuinely decide to use it one day. That decision is
    theirs and must be possible -- but it must be typed."""
    src = open(os.path.join(TOOLS, 'party.py'), encoding='utf-8').read()
    assert "--anyway" in src
    assert 'genuinely decided' in src
