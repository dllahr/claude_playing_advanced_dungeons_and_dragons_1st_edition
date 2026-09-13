"""Two layers: the world, which is exact, and what the party knows, which is not.

**The player's distinction, and it is better than the DM's first attempt.** That
draft put a `precision_ft` on every place -- which was really measuring the DM's
own doubt about his reading of the narrative, *a property of neither the world
nor the party*. The player split it:

    THE TRUE MAP      exact. Wethersby does not move. Distance is FIXED and only
                      TIME varies -- cart, ride, walk, load, weather
    THE PARTY'S MAP   where the uncertainty lives: known, vague, heard, unknown

And the campaign already had that shape one level down: `mapdb` separates what a
square IS from `cells.seen`, what the party has looked at.

*** AND THE SCALE CAME OUT OF THE BOOK, WHICH CHANGED IT. *** The first map used
a DM-reasoned **18 miles per CART-day**, taken off *"fifteen to twenty miles
laden"* -- a **WALKING** figure applied to carts. `rules/overland.md`, DMG p.58,
gives a cart **25 on a road**. Marchford moved 54 -> 75 miles and Ludbury 90 ->
125. **Every travel TIME in the narrative is unchanged**, because the times are
what was played; only the mileage moved, and it moved onto the book.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import overland                                                   # noqa: E402
import entities                                                   # noqa: E402


def map_body(out):
    """The grid only -- between the scale bar and the legend.

    Splitting on a blank line does NOT work: the grid has blank ROWS in it, and
    a render whose first row happened to be empty measured as two lines tall.
    """
    lines = out.split('\n')
    start = next(i for i, l in enumerate(lines) if l.startswith('|-')) + 1
    end = next(i for i, l in enumerate(lines) if l.lstrip().startswith('place'))
    return [l for l in lines[start:end - 1]]


# ------------------------------------------------------- the true map

def test_the_live_map_agrees_with_every_stated_travel_time():
    """If this fails, the map and the fiction have come apart. FICTION WINS."""
    assert [m for s, m in overland.check() if s == 'FAIL'] == []


def test_the_scale_is_the_books_and_not_the_dms():
    """DMG p.58: cart 25 on a road, laden walk 20, medium mount 40.

    The DM's invented 18 was a walking figure applied to carts, and looking the
    table up is what caught it.
    """
    assert overland.PACE['cart'] == 25
    assert overland.PACE['walk'] == 20
    assert overland.PACE['ride'] == 40
    assert overland.PACE['walk_rough'] == 10
    rules = open(os.path.join(ROOT, 'rules', 'overland.md'),
                 encoding='utf-8').read()
    assert 'DMG p. 58' in rules
    for row in ('| light | 30 | 20 | 10 |', '| cart | 25 | 15 | — |'):
        assert row in rules, row


def test_the_world_carries_no_uncertainty_column():
    """Uncertainty is a property of KNOWLEDGE. It does not belong here."""
    with open(os.path.join(ROOT, 'campaign', 'places.tsv'),
              encoding='utf-8') as fh:
        for line in fh:
            if line.strip() and not line.startswith('#'):
                header = line.split('\t')
                break
    for banned in ('precision_ft', 'precision', 'uncertainty'):
        assert banned not in [c.strip() for c in header], (
            'places.tsv has a %r column. The world is where it is; what is '
            'uncertain is what the PARTY knows, and that is knowledge.tsv.'
            % banned)


def test_positions_are_in_feet_so_the_dungeon_shares_the_frame():
    pts = overland.points()
    assert overland.MILE == 5280
    assert abs(overland.feet('wethersby', 'marchford') - 75 * 5280) < 5280
    assert pts['marchford'][1] == -396000


def test_distances_are_fixed_and_times_are_ranges():
    """A distance is one number. A journey is not, and the tool says so."""
    m = overland.miles('wethersby', 'marchford')
    lo, hi = overland.days_range(m, 'cart')
    assert lo < 3 < hi, (lo, hi)
    assert lo < overland.days(m, 'cart') < hi
    assert overland.days_range(m, 'ride')[0] < lo


def test_the_two_distances_that_were_got_wrong_in_play():
    fe = overland.miles('fenns', 'edes')
    assert 6.5 <= fe <= 9.5, fe
    assert overland.days_range(fe, 'cart')[1] < 0.6, (
        'Ede\'s is "a couple of hours, not a day" and the DM said "a day" twice')
    assert overland.miles('crag_turning', 'cave_mouth') < 4, (
        'A CART NEVER REACHES THE DOOR')


def test_the_bearings_the_record_states_in_words():
    for a, b, want in (('wethersby', 'draycot', 'south-west'),
                       ('wethersby', 'marchford', 'south'),
                       ('wethersby', 'ludbury', 'south'),
                       ('wethersby', 'crag_turning', 'north'),
                       ('ludbury', 'wraye', 'east')):
        assert overland.bearing(a, b) == want, (a, b, overland.bearing(a, b))


def test_wrayes_claim_lives_on_the_LEG_and_not_on_the_radius():
    """"Three days EAST OF LUDBURY" -- its eight days from Wethersby go south
    and THEN east, so a straight line cuts the corner. The check fired on that,
    correctly, and the claim moved to the leg where it belongs."""
    assert ('ludbury', 'wraye', 3, 'cart') in overland.LEGS
    assert not (entities.places()['wraye'].get('attested_days') or '').strip()


def test_check_fails_when_the_map_stops_matching_the_fiction():
    pts = dict(overland.points())
    x, y, r = pts['marchford']
    pts['marchford'] = (x, y + 40 * overland.MILE, r)
    fails = [m for s, m in overland.check(pts) if s == 'FAIL']
    assert any('marchford' in m and 'NARRATIVE WINS' in m for m in fails)


# --------------------------------------------------- the party's map

def test_a_place_only_heard_of_carries_that_level():
    """Nan named Hobb's Lane and Wettleford and NOBODY HAS BEEN to
    either; that is ALL they have of them. Whether it gets DRAWN is
    tools/mapimg.py's problem now; the LEVEL is decided here."""
    assert overland.level_of('hobbs_lane') == overland.HEARD
    assert overland.level_of('wettleford') == overland.HEARD
    assert overland.level_of('marchford') == overland.KNOWN


def test_this_tool_no_longer_draws_anything():
    """*** THE ASCII MAP WAS REMOVED, 2026-09-12, AND THAT IS THE POINT. ***

    It lived for a day. The player asked whether it was actually easier to
    READ than the data behind it, and the answer was no: taking "which town
    lies north-west of Wethersby" off a character grid means reconstructing
    coordinates from column positions, which is harder than reading the
    coordinates. Every question the DM asks has a better answer in a query.

    And A PASTED MAP IS A STALE MAP -- correct when made and never again --
    so reading a position back off one in scrollback is narrating from a
    summary instead of from the log, which is the largest error class in this
    campaign. Render for the player (mapimg.py); query here."""
    assert not hasattr(overland, 'render')
    assert not hasattr(overland, 'ASPECT')
    assert not hasattr(overland, 'GLYPH')
    src = open(os.path.join(TOOLS, 'overland.py'), encoding='utf-8').read()
    assert 'NO LONGER DRAWS A MAP' in src
    assert 'def crop(' in src, 'crop stays -- tools/mapimg.py uses it'
    assert 'def ways(' in src, 'the ways stay -- mapimg draws them'
    assert 'ROADS = {' not in src, (
        'the roads moved to campaign/roads.tsv on 2026-09-12; a dict of '
        'them in a tool is data in code')


def test_the_third_case_is_represented():
    """Somewhere they have BEEN and still could not place.

    Quasqueton: eight expeditions inside, and `mapdb` holds level 1 to ten feet
    -- but where the hill SITS relative to the road is still "about an hour off
    the turning, up the outcrop". Nobody has surveyed the outside.
    """
    assert overland.level_of('quasqueton') == overland.VAGUE
    kn = overland.knowledge()
    assert kn['quasqueton']['precision_ft'].strip() == '1000'


def test_only_a_vague_place_carries_a_precision():
    warns = [m for s, m in overland.check() if s == 'WARN']
    assert not [m for m in warns if 'carries a precision_ft' in m]
    assert not [m for m in warns if 'VAGUE with no precision_ft' in m]


def test_every_knowledge_level_is_one_of_the_four():
    bad = [(p, r.get('level')) for p, r in overland.knowledge().items()
           if (r.get('level') or '').strip() not in overland.LEVELS]
    assert not bad, bad


def test_check_flags_a_place_they_spent_a_day_at_with_nothing_logged():
    """The cross-check that catches the DM forgetting to say what they learnt."""
    kn = dict(overland.knowledge())
    kn.pop('marchford', None)
    warns = [m for s, m in overland.check(kn=kn) if s == 'WARN']
    assert any('marchford' in m and 'days.tsv' in m for m in warns)


# ------------------------------------------------- one coordinate system

def test_a_dungeon_square_resolves_into_the_world_frame():
    """`mapdb` keeps its own 10-ft grid and its own tests. ONE ROW says where."""
    x, y = overland.to_overland('b1_level1', 16, 1)
    cave = overland.points()['cave_mouth']
    assert abs(x - cave[0]) < 2000 and abs(y - cave[1]) < 2000, (
        'the level-1 grid should sit under the cave mouth')


def test_the_frame_records_a_rotation_even_though_it_is_zero():
    """A printed map's north arrow need not be the world's, and pretending it
    is would be exactly the quiet assumption this project keeps finding."""
    f = overland.frames()['b1_level1']
    assert float(f['rotation_deg']) == 0
    assert float(f['unit_ft']) == 10


def test_every_frame_sits_at_a_place_that_exists():
    assert [m for s, m in overland.check() if 'frame' in m and s == 'FAIL'] == []

# ------------------------------------------------------------- the ways

def test_the_roads_are_DATA_and_not_a_dict_in_a_tool():
    """`ROADS` was hard-coded in overland.py, which is the one thing
    CLAUDE.md is most insistent about. It is campaign/roads.tsv now."""
    assert os.path.exists(os.path.join(ROOT, 'campaign', 'roads.tsv'))
    src = open(os.path.join(TOOLS, 'overland.py'), encoding='utf-8').read()
    assert 'ROADS = {' not in src
    assert len(overland.roads()) >= 6


def test_every_road_ends_where_a_place_is():
    """A route to nowhere is not a route."""
    ids = set(entities.places())
    for r in overland.roads().values():
        for stop in overland.stops_of(r):
            assert stop in ids, '%s stops at %r' % (r['id'], stop)


def test_a_track_is_slower_than_a_road_and_that_is_the_book():
    """DMG p.58: normal terrain for a VEHICLE means roadways; rugged
    means "roadways through such terrain OR TRACKS/PATHS through normal
    terrain". So `kind` changes how long a journey takes and is not a label.
    """
    assert overland.WAY_PACE['track']['cart'] < overland.WAY_PACE['road']['cart']
    assert overland.WAY_PACE['path']['cart'] is None, (
        'a path is not cart-passable at all')


def test_lyde_is_reached_by_a_TURNING_off_the_north_road():
    """DM call: not via Draycot, not via Marchford. A turning about two
    days south, then west by track -- which is what makes the attested "a day
    off the road each way" true at TRACK pace rather than road pace."""
    north = overland.stops_of(overland.roads()['north_road'])
    assert 'lyde_turning' in north
    assert 'lyde' not in north, 'Lyde is not ON the north road'
    assert overland.roads()['lyde_track']['kind'] == 'track'
    m = overland.miles('lyde_turning', 'lyde')
    d = m / overland.WAY_PACE['track']['ride']
    assert 0.6 <= d <= 1.4, (m, d)
    assert overland.bearing('lyde_turning', 'lyde') == 'west'
    assert overland.road_between('draycot', 'lyde') is None
    assert overland.road_between('marchford', 'lyde') is None


def test_the_route_to_lyde_is_VAGUE_to_the_party():
    """They got there twice and could still not say which milestone the
    turning is at. Lyde itself they have stood in."""
    assert overland.level_of('lyde_turning') == overland.VAGUE
    assert overland.level_of('lyde') == overland.KNOWN
    assert overland.knowledge()['lyde_turning']['precision_ft'].strip()


def test_fenns_is_four_miles_east_of_the_road_by_track():
    m = overland.miles('fenns_turning', 'fenns')
    assert abs(m - 4) < 1, m
    assert overland.bearing('fenns_turning', 'fenns') == 'east'
    assert overland.roads()['fenns_track']['kind'] == 'track'
    assert 'fenns_turning' in overland.stops_of(overland.roads()['north_road'])


def test_edes_is_reached_THROUGH_FENNS_AND_NOT_FROM_THE_ROAD():
    """DM call, and it explains the record: the party went that way both
    times, and it makes Fenn's yard the gateway to her."""
    assert overland.road_between('fenns', 'edes') is not None
    for other in ('fenns_turning', 'marchford', 'ludbury', 'wethersby'):
        assert overland.road_between(other, 'edes') is None, (
            'a direct way to Ede\'s from %s would make Fenn\'s yard '
            'unnecessary, and the party has gone through it twice' % other)


def test_a_turning_sits_ON_the_road_it_turns_off():
    """A junction that is not on the road is not a junction."""
    pts = overland.points()
    for t in ('lyde_turning', 'fenns_turning'):
        assert abs(pts[t][0] - pts['wethersby'][0]) < 2000, t


# ----------------------------------------------------------------- Wraye

def test_wraye_is_VAGUE_now_and_not_merely_heard_of():
    """They know it exists and is reachable by road out of Ludbury, so
    they could put a finger on a REGION -- more than nothing, less than a
    position.

    *** The record says three days east of LUDBURY, not Marchford:
    calendar.md:103, the distance table. ***
    """
    assert overland.level_of('wraye') == overland.VAGUE
    r = overland.knowledge()['wraye']
    rad = float(r['precision_ft']) / overland.MILE
    assert 20 <= rad <= 45, (
        'the radius is %g miles. "East" is one of eight compass points, a '
        '45-degree wedge, and at 75 miles that is about 30 wide.' % rad)
    assert 'LUDBURY' in r['how']
    assert 'ludbury' in overland.stops_of(overland.roads()['ludbury_east'])


def test_wraye_is_now_drawn_but_with_its_doubt_around_it():
    import mapimg
    out = mapimg.svg(mapimg.land.crop(overland.points(), 'ludbury', 90),
                     px_per_mile=6)
    assert 'Wraye' in out, 'a vague place is DRAWN; only a heard-of one is not'
    rings = out.count('stroke-dasharray="5 4"')
    assert rings >= 1, 'and its uncertainty must be drawn with it'
