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

def test_a_place_only_heard_of_is_not_on_the_partys_map():
    """*** SPOILER DISCIPLINE, AND A MAP IS THE EASIEST WAY TO LEAK. ***

    They know Wraye is "three days east of Ludbury and it has a library". They
    have never been. Their map must not carry a dot at its exact coordinates.
    """
    assert overland.level_of('wraye') == overland.HEARD
    party = overland.render(true=False)
    assert 'HEARD OF, AND NOT PLACED' in party
    assert 'Wraye' in party            # named in the margin
    lines = party.split('HEARD OF')[0]
    assert 'Wraye' not in lines, 'Wraye is plotted on the party map'
    assert 'Wraye' in overland.render(true=True)


def test_the_default_render_is_the_partys_and_not_the_dms():
    assert overland.render() == overland.render(true=False)
    assert overland.render(true=True) != overland.render(true=False)


def test_the_third_case_is_represented():
    """Somewhere they have BEEN and still could not place.

    Quasqueton: eight expeditions inside, and `mapdb` holds level 1 to ten feet
    -- but where the hill SITS relative to the road is still "about an hour off
    the turning, up the outcrop". Nobody has surveyed the outside.
    """
    assert overland.level_of('quasqueton') == overland.VAGUE
    kn = overland.knowledge()
    assert kn['quasqueton']['precision_ft'].strip()
    assert '~ within' in overland.render()


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
