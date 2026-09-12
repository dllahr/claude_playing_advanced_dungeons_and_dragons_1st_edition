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


# ----------------------------------------------------------- the renderer

def test_it_fills_the_requested_width():
    """The ask was ~120 columns, so an UNCONSTRAINED render fills the width.

    Give it a height as well and the aspect binds instead: this world is about
    38 miles wide and 146 tall, so boxing it into a screen makes it narrow and
    tall -- which is the honest shape and not a bug. That is what
    `test_a_height_boxes_it_instead` is for.
    """
    for w in (80, 120, 160):
        out = overland.render(width=w)
        # The MAP body only. The legend and the heard-of notes are prose and
        # wrap where the terminal wraps them; the grid is what has a width.
        body = map_body(out)
        widest = max((len(l) for l in body), default=0)
        assert widest <= w, ('render(width=%d) drew %d columns' % (w, widest))
        assert widest >= w * 0.8, (
            'render(width=%d) drew only %d columns -- with no height cap it is '
            'meant to FILL the width, and room reserved for labels is not an '
            'excuse for a fifth of it' % (w, widest))


def test_a_height_boxes_it_instead():
    """And then the aspect binds, which is the honest shape of a long world."""
    rows = map_body(overland.render(width=120, height=46))
    assert len(rows) <= 48, len(rows)
    assert len(map_body(overland.render(width=120))) > len(rows), (
        'without a height cap the map should run deeper, not the same')


def test_the_aspect_is_honest_and_says_so():
    """A row must cover TWICE the miles of a column, because a terminal
    character is about twice as tall as it is wide. Stretching one axis to make
    a long world look compact would be the most convincing kind of lie a map
    can tell."""
    assert overland.ASPECT == 2.0
    out = overland.render(width=120, height=46)
    assert 'THE ASPECT IS HONEST' in out
    head = [l for l in out.split('\n') if 'miles a column' in l][0]
    import re
    col = float(re.search(r'([\d.]+) miles a column', head).group(1))
    row = float(re.search(r'([\d.]+) a row', head).group(1))
    assert abs(row - col * overland.ASPECT) < 0.02, (col, row)


def test_every_place_shown_gets_a_label():
    """The renderer reserves room for the longest NAME before choosing a scale.

    Without that, a place at the eastern edge has nowhere to put its label and
    the map has to report that it gave up -- which it did, for Marrow's holding
    and Ede's cottage, until the margin was reserved.
    """
    out = overland.render(width=120, height=46)
    assert 'no room for a label' not in out
    for name in ("Marrow's holding", "Ede's cottage", 'Wethersby', 'Ludbury'):
        assert name in out.split('    place')[0], name


def test_the_scale_bar_adapts_to_the_zoom():
    """A fixed "10 miles" ran off the edge at the crag, where a column is fifty
    feet, and would have been one character at the whole-world zoom."""
    wide = overland.render(width=120, height=46)
    close = overland.render(pts=overland.crop(overland.points(),
                                              'crag_turning', 4), width=120)
    def bar(out):
        return [l for l in out.split('\n') if l.startswith('|-')][0]
    assert bar(wide) != bar(close)
    assert len(bar(wide)) < 120 and len(bar(close)) < 130


def test_crop_is_the_zoom_and_keeps_distances_from_wethersby():
    """A 4-mile crop of the crag does NOT contain Wethersby, and the legend
    still has to measure from it -- which it got wrong the first time and
    crashed on."""
    near = overland.crop(overland.points(), 'crag_turning', 4)
    assert 'wethersby' not in near
    assert {'crag_turning', 'basecamp', 'cave_mouth'} <= set(near)
    out = overland.render(pts=near, width=120)
    assert 'the crag turning' in out
    assert '20  north' in out or ' 20 ' in out      # still measured from town


def test_crop_respects_the_party_layer():
    """Cropping must not become a back door onto places they have not been."""
    around = overland.crop(overland.points(), 'ludbury', 90)
    assert 'wraye' in around
    assert 'Wraye' not in overland.render(pts=around, width=120).split(
        'HEARD OF')[0]
