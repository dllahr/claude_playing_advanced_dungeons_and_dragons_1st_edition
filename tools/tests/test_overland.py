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


def _superseded_test_the_route_to_lyde_is_VAGUE_to_the_party():
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

# ------------------------------------------- Draycot is not a cul-de-sac

def test_draycot_has_more_than_one_way_out():
    """*** INFERRED FROM THE RECORD, NOT INVENTED. ***
    district.md: "Sir Aymer's clip has gone [to Ludbury] these two summers", and
    Wethersby was never told where the staple went because "his clip goes to
    Ludbury EITHER WAY". *** If it went through Wethersby the town would have
    watched it go, every summer, and the whole mystery would never have
    existed. *** So Draycot has its own way south.
    """
    out = [r['id'] for r in overland.roads().values()
           if 'draycot' in overland.stops_of(r)]
    assert len(out) >= 3, out
    assert 'draycot_south' in out
    assert 'ludbury' in overland.stops_of(overland.roads()['draycot_south'])


def test_the_south_road_does_not_pass_through_wethersby():
    """The whole point of it. If it did, the staple would not have been
    a mystery to a market town that watches every cart on its own road."""
    assert 'wethersby' not in overland.stops_of(
        overland.roads()['draycot_south'])


def test_the_party_does_not_know_the_south_road_and_it_is_not_drawn():
    """*** A ROAD IS A SPOILER TOO. *** They have never
    asked where Sir Aymer's clip goes. Drawing the answer on their map would
    hand it to them in a picture, which is harder to un-see than a sentence.
    """
    import mapimg
    assert overland.level_of('draycot_south') == overland.UNKNOWN
    name = overland.roads()['draycot_south']['name']
    assert name not in overland.ways(true=False)
    assert name in overland.ways(true=True)
    assert name not in mapimg.svg()
    assert name in mapimg.svg(true=True)


def test_the_draycot_road_runs_ON_and_the_party_came_up_it():
    """district.md: "Where the PCs came from -- d8 = 6 -- the SOUTH-WEST,
    on the Draycot road, before expedition 1." So the road does not stop at the
    hall, and they know that because they walked it."""
    assert 'sw_way' in overland.points()
    assert 'draycot_road_on' in overland.roads()
    assert overland.bearing('draycot', 'sw_way') == 'south-west'
    assert overland.level_of('sw_way') == overland.VAGUE
    assert overland.level_of('draycot_road_on') == overland.VAGUE


# ---------------------------------------------- knowledge covers the ways

def test_every_way_has_a_knowledge_row():
    """Explicitly, because a default would be a guess about what the
    party has actually travelled."""
    kn = overland.knowledge()
    missing = [rid for rid in overland.roads() if rid not in kn]
    assert not missing, missing


def test_a_road_does_not_carry_a_precision():
    """A precision is a radius around a POINT. You know where a road
    goes, or you do not quite."""
    warns = [m for s, m in overland.check() if s == 'WARN']
    assert not [m for m in warns if 'is a ROAD and carries a precision' in m]


def test_the_lyde_turning_is_KNOWN_because_dave_rode_it():
    """*** CORRECTED 2026-09-12, PLAYER-CAUGHT. *** It was
    logged VAGUE on the reasoning that nobody had surveyed which milestone the
    turning is at. But DAVE RODE TO LYDE AND HOME AGAIN on day 62, and Wat
    before him -- and a man who has ridden to a place and back knows where he
    turned off. The route belongs on the party's map.
    """
    assert overland.level_of('lyde_turning') == overland.KNOWN
    assert overland.level_of('lyde_track') == overland.KNOWN
    import mapimg
    assert 'the Lyde track' in overland.ways(true=False)
    assert 'the Lyde turning' in mapimg.svg()


# ------------------------------------- what a casualty costs on the road
# Added 2026-09-13. The DM ruled mid-scene that an invalid under DMG p.82 drops
# the party to the heavy-burden row and so made a 22-mile walk take two days.
# The player said the campaign had never done that, and he was right: expedition
# 7 came out on day 46 and was in Wethersby LATE AFTERNOON ON DAY 47 with Ista
# invalid and ~250 gp of laboratory glass carried. One day, twenty-two miles.
#
# A rule reasoned from a table that contradicts attested play loses to the play.

def test_an_invalid_does_NOT_slow_the_party():
    import rules
    t = rules.find('Wounded, invalid and carried')
    assert t, 'the casualty table is gone from rules/overland.md'
    rows = {r[0]: r[1] for r in t['rows']}
    inval = [v for k, v in rows.items() if 'INVALID' in k]
    assert inval, rows
    assert '20 miles' in inval[0], (
        'an invalid walks the normal laden day. Attested day 46-47: Ista '
        'invalid, 22 miles, one day, arrived late afternoon.')


def test_someone_who_cannot_walk_DOES_slow_the_party():
    import rules
    rows = {r[0]: r[1] for r in rules.find('Wounded, invalid and carried')['rows']}
    cant = [v for k, v in rows.items() if 'CANNOT WALK' in k]
    assert cant and '10 miles' in cant[0], rows


def test_the_precedents_are_quoted_not_just_cited():
    """Both rows were settled against the record, and the record must sit
    beside them -- otherwise the next DM re-derives from the burden table and
    gets the same wrong answer."""
    body = open(os.path.join(ROOT, 'rules', 'overland.md'),
                encoding='utf-8').read()
    # normalised: the file is hard-wrapped, and a quotation must not have to be
    # kept on one line to stay findable
    flat = ' '.join(body.split())
    assert 'BACK IN WETHERSBY, late afternoon' in flat
    assert 'litter of two poles and the bearskin' in flat
    assert 'A LITTER IS NOT FASTER THAN A MAN WHO CAN WALK' in flat


def test_a_short_leg_warns_that_a_DAILY_rate_is_not_an_HOURLY_pace():
    """*** PLAYER-CAUGHT, DAY 98, AND THE TOOL INVITED THE ERROR. ***

    Basecamp to the dry watercourse is 2 miles. `off the road` divides DMG
    p.58's 10 mi/day and prints "0.2 - 0.3 days", which the DM read as two and a
    half hours and narrated an afternoon around. The player:

        "If we took 2 hours to go those 2 miles, which would be very, very
         slow, we would be there at 1 PM."

    He is right. A daily rate already carries rests, obstacles and the fact that
    nobody marches ten hours at one pace, so dividing it is correct at the scale
    it was written for -- Wethersby to Ludbury -- and absurd below a few miles.

    The FIGURES are not changed; they are the book's. The warning is what is
    added, because the failure was in the reading.
    """
    short = land.how_long(2.0)
    assert any('SHORT LEG' in line for line in short), \
        'a 2-mile leg printed daily-rate divisions with no caveat'
    assert any('mi/hour' in line for line in short), \
        'the caveat must give an actual pace to use instead'


def test_a_DAY_SCALE_leg_does_NOT_carry_the_warning():
    """The caveat must not become noise on the legs the model is right for.

    Wethersby to Ludbury is 125 miles and "4.7 - 7.0 days by cart" is exactly
    what DMG p.58 is for. A warning printed on every answer is a warning nobody
    reads.
    """
    assert not any('SHORT LEG' in line for line in land.how_long(125.0))
    assert land.SHORT_LEG_MI < 20, 'the threshold has grown into the day scale'
