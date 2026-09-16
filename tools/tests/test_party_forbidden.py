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
    """A refusal that has already moved the party is not a refusal.

    *** IT PUTS THE PARTY AT THE ALCOVE FIRST, rather than using wherever
    they happen to be. *** The first version walked from their LIVE position
    and passed only while that position was (17,13); an hour of play later
    they were at (14,29), from which (16,19) does not cross the forbidden
    corridor at all, and the test failed having tested nothing. A test that
    depends on today's game state is the same defect as one that pins today's
    gold.
    """
    log = tmp_path / 'party.tsv'
    log.write_text(open(os.path.join(ROOT, 'campaign', 'party.tsv'),
                        encoding='utf-8').read())
    party.place('17,13', why='fixture: the alcove, where the route to the\n                four-way crosses the ruled-out corridor',
                path=str(log))
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


# ---------------------------------------------- ONE list, read by BOTH tools
# Added day 95, when the player asked "do you have a tool for the route that
# avoids the magic mouths?" There was HALF of one, and the halves disagreed:
#
#   party.py     knew six edges, hardcoded in a dict in the source, and REFUSED
#                them -- so a named route still had to be walked leg by leg.
#   dmap path    knew nothing at all and cheerfully printed the forbidden route.
#   NEITHER      knew about (17,21), KELL'S GRAVE -- the OTHER square a route
#                was hand-corrected away from, on expedition 5 round 34.
#
# The squares now live in campaign/avoid.tsv, one copy, and party.py DERIVES its
# edges from them. The repo's own rule: no rules table is written twice.

def test_party_py_holds_NO_hardcoded_forbidden_table():
    """The dict is gone and must stay gone. A second copy of a rule is the
    thing this whole repo is arranged against."""
    src = open(os.path.join(TOOLS, 'party.py'), encoding='utf-8').read()
    assert 'FORBIDDEN = {' not in src, (
        'party.py has grown a hardcoded forbidden table again. The squares '
        'belong in campaign/avoid.tsv, which dmap.py also reads.')
    assert 'avoid_set' in src, 'party.py no longer reads campaign/avoid.tsv'


def test_both_documented_hand_corrections_are_in_the_file():
    """Each row exists because a route was auto-picked wrong and caught by
    hand. If either disappears, the bug that was paid for twice is back."""
    import dmap
    cells = dmap.avoid_set(1)
    assert (16, 17) in cells, 'the magic mouths, exp.7 round 784'
    assert (17, 21) in cells, (
        "Kell's grave, exp.5 round 34 -- the one party.py NEVER knew about")
    for y in range(14, 19):
        assert (16, y) in cells, (
            'the mouth corridor is avoided AS A RUN, %d missing' % y)
    for junction in ((16, 13), (16, 19)):
        assert junction not in cells, (
            '%s is a JUNCTION the correct route uses; avoiding it would break '
            'the detour it exists to allow' % (junction,))


def test_the_router_now_produces_the_HAND_CORRECTED_route():
    """*** THE POINT OF THE WHOLE EXERCISE. *** The day-46 correction row says
    the right way round is the alcove-pair-2 one-way slab at (17,13,V) and that
    it costs "~60 ft longer, no mouths". The router, given only the avoided
    squares, must arrive at that independently -- same slab, same 60 feet."""
    import dmap
    db = os.path.join(ROOT, 'mapdb', 'output', 'b1', 'b1.sqlite')
    if not os.path.exists(db):
        import pytest
        pytest.skip('b1.sqlite not built')
    good, crossed = dmap.find_path(db, 1, (16, 1), (14, 39), dmap.avoid_set(1))
    naive, _ = dmap.find_path(db, 1, (16, 1), (14, 39))
    assert good and naive
    assert not (set(good) & {(16, y) for y in range(14, 19)}), (
        'the router still walks the mouth corridor')
    assert (17, 13, 'V') in [e for _, e in crossed], (
        'the detour must go through the alcove-pair-2 one-way slab')
    assert (len(good) - len(naive)) * 10 == 60, (
        'the detour costs %d ft; the hand-written correction from day 46 says '
        '~60' % ((len(good) - len(naive)) * 10))


def test_going_in_deliberately_is_still_possible_and_must_be_SAID():
    """A rule that cannot be overridden gets worked around instead. Walking
    into the mouths' alcove is a legal choice -- it just has to be declared."""
    import dmap
    allowed = dmap.avoid_set(1, allow=[(16, 17)])
    assert (16, 17) not in allowed
    assert (17, 21) in allowed, '--through must free ONE square, not all of them'
