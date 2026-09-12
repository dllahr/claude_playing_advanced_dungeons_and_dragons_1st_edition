"""The grid must keep agreeing with the travel times the fiction already used.

**A map is the most convincing thing in a campaign and the easiest to get
wrong**, because once something is drawn it looks surveyed. So this one is data:
coordinates in `campaign/places.tsv`, every distance recomputed from them, and a
check that FAILS when the grid stops reproducing a travel time the narrative has
already spent.

THE DISTANCES IT EXISTS TO PROTECT, both of which were got wrong in play:

    Fenn's -> Ede's       EIGHT MILES, "a couple of hours, not a day".
                          The DM said "a day" TWICE before the player caught it
    the cave mouth        A CART NEVER REACHES THE DOOR. The graded trail stops
                          at the basecamp, half an hour short, and Halm's
                          objection to the rope plan collapsed when that was
                          finally said correctly

*** AND `fix` IS THE COLUMN THAT MATTERS MOST. *** Ten of sixteen places have
both bearing and distance in the record. The rest are DM calls, and the map says
so in its own legend -- because a schematic flattens the difference between a
fact and a guess far more thoroughly than prose does. **A call is not canon.**

THE FIRST THING `check` CAUGHT WAS THIS FILE'S OWN AUTHOR: Draycot is "a long
day's RIDE; the walk is two days", and its 1 was being compared against CART
speed. **A day is not a distance.** `places.tsv` now carries `day_mode` beside
every figure, for exactly the reason every quantity in this campaign carries its
unit.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import overland                                                   # noqa: E402
import entities                                                   # noqa: E402


def test_the_live_grid_agrees_with_every_stated_travel_time():
    """If this fails, the map and the fiction have come apart. FICTION WINS."""
    assert [m for s, m in overland.check() if s == 'FAIL'] == []


def test_the_scale_is_the_attested_one():
    """15-20 miles laden is the crag turning, one day's walk. Not invented."""
    assert overland.MILES_PER_DAY == 18
    assert 15 <= overland.MILES_PER_DAY <= 20


def test_a_day_is_not_a_distance():
    """cart, ride and walk are different speeds and the column says which.

    Draycot's "1 day" is a RIDING day. Checking it against cart speed was the
    first thing `check` caught, in its own author.
    """
    assert overland.PACE['ride'] > overland.PACE['cart'] > overland.PACE['walk']
    draycot = entities.places()['draycot']
    assert draycot['day_mode'] == 'ride'
    assert 'RIDE' in draycot['notes'].upper()


def test_fenns_to_edes_is_eight_miles_and_not_a_day():
    """THE ERROR THIS MAP EXISTS FOR. The DM said "a day" twice."""
    m = overland.miles('fenns', 'edes')
    assert 6 <= m <= 10, m
    assert overland.days(m) < 0.6, (
        '%.1f miles computes to %.1f days. It is "a couple of hours, not a '
        'day" -- a cart out of Fenn\'s is at Ede\'s door before dinner.'
        % (m, overland.days(m)))


def test_a_cart_never_reaches_the_cave_door():
    """The graded trail stops at the basecamp, half an hour short."""
    assert overland.miles('crag_turning', 'basecamp') < 4
    assert overland.miles('crag_turning', 'cave_mouth') < 6
    assert overland.miles('basecamp', 'cave_mouth') <= 2


def test_the_bearings_the_record_states_in_words():
    for a, b, want in (('wethersby', 'draycot', 'south-west'),
                       ('wethersby', 'marchford', 'south'),
                       ('wethersby', 'ludbury', 'south'),
                       ('wethersby', 'crag_turning', 'north'),
                       ('ludbury', 'wraye', 'east')):
        assert overland.bearing(a, b) == want, (a, b, overland.bearing(a, b))


def test_ludbury_is_two_days_beyond_marchford():
    """"Five days south -- three to Marchford, two beyond it.\""""
    assert abs(overland.days(overland.miles('marchford', 'ludbury')) - 2) < 0.45


def test_check_fails_when_the_grid_stops_matching_the_fiction():
    """The mechanism, not the data. Move a town and the check must notice."""
    pts = dict(overland.points())
    x, y, r = pts['marchford']
    pts['marchford'] = (x, y + 30, r)          # drag it a day and a half north
    fails = [m for s, m in overland.check(pts) if s == 'FAIL']
    assert any('marchford' in m for m in fails)
    assert any('NARRATIVE WINS' in m for m in fails)


def test_every_place_declares_how_it_got_where_it_is():
    """A map flattens fact and guess together. This column un-flattens them."""
    bad = [pid for pid, (x, y, r) in overland.points().items()
           if (r.get('fix') or '') not in ('attested', 'part', 'call', 'region')]
    assert not bad, bad


def test_the_calls_are_visible_in_the_render_and_not_disguised():
    out = overland.render()
    assert '<- call' in out
    assert 'A call is not canon' in out
    for name in ("Marrow's holding", "Hobb's Lane", 'Wettleford', 'Lyde'):
        assert name in out


def test_the_attested_places_are_not_marked_as_calls():
    """If Wethersby or Marchford ever shows "<- call", something has been lost."""
    pts = overland.points()
    for pid in ('wethersby', 'marchford', 'ludbury', 'draycot', 'wraye',
                'crag_turning', 'fenns'):
        assert pts[pid][2]['fix'] == 'attested', pid


def test_the_render_does_not_lose_a_place_behind_a_label():
    """The first renderer wrote labels onto the grid and they collided --
    Wettleford over Marrow's, both over WETHERSBY, and the origin of the whole
    map vanished under somebody's holding. The legend cannot do that."""
    out = overland.render()
    for pid, (x, y, r) in overland.points().items():
        if (r.get('kind') or '') in ('region', 'hundred'):
            continue
        assert r['name'] in out, '%s is not in the render at all' % pid


def test_distances_are_reported_as_a_floor_not_a_quote():
    """Straight-line understates any journey that follows a road."""
    out = overland.from_report('Wethersby')
    assert 'FLOOR' in out
    assert 'follows a road' in out
