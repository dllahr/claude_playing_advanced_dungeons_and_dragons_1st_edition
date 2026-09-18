"""The drawn map must obey the same two rules as the text one, and one more.

`tools/mapimg.py` is now **the only thing that draws this campaign's overland
map**. An ASCII renderer lived in `overland.py` for a day and was removed on
2026-09-12: the player asked whether it was actually easier to READ than the
data behind it, and it was not. This holds no places of its own either -- it
draws `places.tsv` and `knowledge.tsv` and nothing else.

WHAT THE PIXELS BUY, and it is the reason this file exists at all:

    the aspect is simply TRUE      the text map carried a 2:1 character hack
                                   and had to announce it in its own header
    labels are sub-pixel and can   the terminal had to give up and SAY so
    run on a LEADER LINE
    *** A VAGUE POSITION IS A      in text, Quasqueton's uncertainty is a
        DRAWN CIRCLE ***           footnote saying "~ within 1,000 ft". Here it
                                   is a ring you can SEE, and at the crag it is
                                   bigger than the hill

AND THE RULE THAT ONLY MATTERS IN A PICTURE: *** A RING IS DRAWN TO SCALE OR NOT
AT ALL. *** Inflating one so it is visible at a coarse zoom would be drawing a
bigger doubt than the party actually has -- which is the single thing a map of
KNOWLEDGE must never do. Below three pixels it is dropped and the `~` beside the
glyph carries it instead.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import mapimg                                                     # noqa: E402
import overland as land                                           # noqa: E402


def rings(out):
    """Every dashed uncertainty circle, as (cx, cy, r)."""
    return [tuple(float(v) for v in m)
            for m in re.findall(
                r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)" '
                r'fill="#c84422"', out)]


# ------------------------------------------------------- the same two layers

def test_a_place_only_heard_of_is_not_drawn():
    """*** A MAP IS THE EASIEST WAY TO LEAK A POSITION, and a PICTURE of one is
    easier still, because nobody reads a picture sceptically. ***"""
    assert land.level_of('hobbs_lane') == land.HEARD
    party = mapimg.svg()
    assert "Hobb's Lane" not in party
    assert "Hobb's Lane" in mapimg.svg(true=True)
    # Wraye WAS the example here until 2026-09-12, when it went
    # from `heard` to `vague`: they know it is reachable by road
    # out of Ludbury, so they can point at a region. A vague place
    # IS drawn -- with its doubt around it.
    assert 'Wraye' in party


def test_the_default_is_the_partys_map():
    assert mapimg.svg() == mapimg.svg(true=False)
    assert mapimg.svg(true=True) != mapimg.svg(true=False)


def test_the_page_names_heard_of_places_without_placing_them():
    """The margin is where a name with no position belongs -- on the page as
    well as on the terminal."""
    page = mapimg.html()
    assert 'Heard of and not placed' in page
    assert "Hobb's Lane" in page
    assert "Hobb's Lane" not in page.split('</svg>')[0], (
        "Hobb's Lane is drawn and nobody has been there")


def test_the_dm_page_is_marked_as_the_dms():
    assert 'DM ONLY' in mapimg.svg(true=True)
    assert 'DM ONLY' in mapimg.html(true=True)
    assert 'DM ONLY' not in mapimg.svg()


# ------------------------------------------- the rule that only exists here

def test_a_ring_is_drawn_to_scale():
    """Quasqueton is vague to 1,000 ft. At 260 px/mile that is ~49 px."""
    near = land.crop(land.points(), 'crag_turning', 4)
    out = mapimg.svg(near, px_per_mile=260)
    rr = rings(out)
    assert rr, 'no uncertainty ring drawn at a zoom where it is 49 px across'
    r = max(x[2] for x in rr)
    want = 1000 * 260 / land.MILE
    assert abs(r - want) < 2, (r, want)


def test_a_ring_too_small_to_draw_is_DROPPED_and_not_inflated():
    """*** THE ONE THING A MAP OF KNOWLEDGE MUST NOT DO. ***

    At the whole-world zoom, 1,000 ft is under two pixels. Drawing it at a
    visible minimum would show a bigger doubt than the party has.
    """
    wide = mapimg.svg(px_per_mile=9)
    # Wraye's thirty-mile doubt IS big enough to draw at this zoom; Quasqueton's
    # thousand feet is not, and must be dropped rather than inflated.
    small = [r for r in rings(wide) if r[2] < 3]
    assert small == [], (
        'a ring was drawn smaller than three pixels, where it cannot be to '
        'scale. It must be DROPPED -- the "~" beside the glyph carries it. '
        'Inflating it to a visible minimum would draw a bigger doubt than the '
        'party actually has.')
    assert '~' in wide, 'and the ~ must then be there'
    assert any(r[2] > 20 for r in rings(wide)), (
        "Wraye's thirty miles is big enough to draw at this zoom and should be")


def test_the_ring_scales_with_the_zoom_and_nothing_else():
    a = rings(mapimg.svg(land.crop(land.points(), 'crag_turning', 4),
                         px_per_mile=200))
    b = rings(mapimg.svg(land.crop(land.points(), 'crag_turning', 4),
                         px_per_mile=400))
    assert a and b
    assert abs(max(x[2] for x in b) / max(x[2] for x in a) - 2) < 0.05


# ---------------------------------------------------------- it is real SVG

def test_it_is_well_formed_and_self_contained():
    import xml.etree.ElementTree as ET
    for out in (mapimg.svg(), mapimg.svg(true=True)):
        ET.fromstring(out)                       # raises if malformed
        assert 'http' not in out.replace('http://www.w3.org/2000/svg', ''), (
            'the SVG reaches outside itself')


def test_north_is_up():
    """SVG's y grows DOWN and the world's grows north. Getting that backwards
    would flip the map and look entirely plausible.

    Measured off the GLYPHS, not the labels -- a label can sit on either side
    of its place and one of them is on a leader line.
    """
    pts = land.points()
    out = mapimg.svg()
    glyphs = [(float(x), float(y)) for x, y in re.findall(
        r'<circle cx="([\d.]+)" cy="([\d.]+)" r="[\d.]+" fill="#[0-9a-f]{6}" '
        r'stroke="#f6f1e4"', out)]
    assert len(glyphs) >= 8, len(glyphs)
    north = [g for g in glyphs if g[1] == min(y for _x, y in glyphs)][0]
    south = [g for g in glyphs if g[1] == max(y for _x, y in glyphs)][0]
    # the northernmost drawn thing is the crag; the southernmost is Ludbury
    assert land.miles('wethersby', 'crag_turning') > 0
    scale = (south[1] - north[1])
    assert scale > 0
    assert 'N</text>' in out


def test_the_scale_bar_is_in_real_units_at_the_real_scale():
    for ppm, unit in ((9, 'miles'), (260, 'mile')):
        out = mapimg.svg(land.crop(land.points(), 'crag_turning', 4)
                         if ppm > 50 else None, px_per_mile=ppm)
        m = re.search(r'>(\d+) (mile s?|miles|mile)<', out)
        assert m, out[-400:]
        step = int(m.group(1))
        line = re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)" '
                          r'x2="([\d.]+)"', out)
        px = max(float(c) - float(a) for a, _b, c in line)
        assert abs(px - step * ppm) < 2, (px, step * ppm)


def test_the_output_is_gitignored_because_it_is_derived():
    ignore = open(os.path.join(ROOT, '.gitignore'), encoding='utf-8').read()
    assert 'campaign/output/' in ignore
    assert mapimg.OUTDIR.endswith(os.path.join('campaign', 'output'))


def test_the_drawing_shows_exactly_who_the_data_says_it_should():
    """They hold no data of their own, so they cannot disagree -- and this
    says so out loud, because 'two views of one source' is only a virtue while
    somebody is checking."""
    import entities
    pic = mapimg.svg()
    for pid, r in entities.places().items():
        if (r.get('kind') or '') in ('region', 'hundred'):
            continue
        if land.level_of(pid) in (land.KNOWN, land.VAGUE):
            assert r['name'] in pic, (
                '%s is on the text map and NOT on the drawn one. The drawn map '
                'dropped a label in silence once -- the crag turning, hemmed in '
                'by the basecamp and the cave mouth -- which is worse than the '
                'terminal, which at least reports what it could not fit. '
                'Leader lines and a NO ROOM note are the fix.' % pid)


# ===================================================================== wobble
# *** A WAY THAT BENDS IS TRUER THAN A WAY DRAWN WITH A RULER, AND THE ONLY
# *** REASON THAT IS SAFE IS THAT THE BENDING NEVER TOUCHES A PLACE.
#
# Added 2026-09-17 at the player's request: "the roads are probably not
# perfectly straight, and the side paths almost certainly are not." The risk it
# introduces is obvious and these tests are the whole of the answer to it -- a
# prettifying pass on a map that gets READ FOR POSITIONS could quietly move a
# place, and nothing else in this repository would notice.

def _chord_distance(p, a, b):
    """How far p sits off the straight line a->b, in px."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-9:
        return ((p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2) ** 0.5
    return abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / length


def test_every_named_stop_survives_the_wobble_EXACTLY():
    """*** THE ONE THAT MATTERS. *** The ink may wander; a place may not."""
    stops = [(10.0, 10.0), (300.0, 120.0), (420.0, 500.0)]
    for kind in ('road', 'track', 'path'):
        got = mapimg._wander('north_road', stops, kind)
        for s in stops:
            assert s in got, (
                '%s: the stop %r is no longer among the drawn points -- the '
                'wobble has MOVED A PLACE, which is the one thing it may never '
                'do' % (kind, s))
        assert got[0] == stops[0] and got[-1] == stops[-1]


def test_the_wobble_is_deterministic_so_the_svg_still_diffs():
    """Hashed, not random. A rebuild that looks like a change is a broken tool.

    The output of this file is gitignored but it is READ side by side with an
    older copy, and `overland check` compares drawings. A random wobble would
    make every single re-render differ from the last for no reason.
    """
    stops = [(0.0, 0.0), (250.0, 90.0)]
    a = mapimg._wander('lyde_track', stops, 'track')
    b = mapimg._wander('lyde_track', stops, 'track')
    assert a == b
    # and a DIFFERENT way bends differently, or every road is the same squiggle
    assert a != mapimg._wander('fenns_track', stops, 'track')


def test_a_path_wanders_more_than_a_track_and_a_track_more_than_a_road():
    """*** THE AMPLITUDE IS THE CLAIM: who built it, and how well. ***

    A made road kept up by somebody with authority over more than one hundred
    only sags. A path is a line worn by feet and goes where the feet went.
    """
    stops = [(0.0, 0.0), (600.0, 0.0)]
    off = {k: max(abs(p[1]) for p in mapimg._wander('x', stops, k))
           for k in ('road', 'track', 'path')}
    assert off['road'] < off['track'] < off['path'], off
    assert off['road'] > 0, 'even a made road is not a ruler line'


def test_the_wobble_is_capped_so_a_long_leg_cannot_wander_miles_off():
    """Ludbury to Wraye is 396,000 ft. A percentage alone would be absurd."""
    stops = [(0.0, 0.0), (4000.0, 0.0)]
    for kind, (_frac, cap) in mapimg.WOBBLE.items():
        for p in mapimg._wander('x', stops, kind):
            assert _chord_distance(p, stops[0], stops[1]) <= cap + 0.51, (
                '%s wandered past its own cap of %.1f px' % (kind, cap))


def test_the_curve_passes_through_the_points_it_is_given():
    """Catmull-Rom INTERPOLATES. A Bezier that merely approximates its control
    points would pull the line off every named stop -- which is the same failure
    as moving the stop, arriving by a different route."""
    d = mapimg._smooth([(0.0, 0.0), (10.0, 5.0), (20.0, 0.0), (30.0, 9.0)])
    assert d.startswith('M0.0,0.0')
    assert d.rstrip().endswith('30.0,9.0')
    for x, y in ((10.0, 5.0), (20.0, 0.0)):
        assert '%.1f,%.1f' % (x, y) in d


def test_no_label_is_drawn_off_the_edge_of_the_canvas():
    """A clipped label is a label LOST, and it reads as a rendering glitch
    rather than as the map running out of room. `free()` treats outside-the-
    canvas as occupied so the leader-line search moves on instead."""
    for kw in ({}, dict(true=True), dict(px_per_mile=90.0)):
        s = mapimg.svg(**kw)
        w = float(re.search(r'width="([\d.]+)"', s).group(1))
        h = float(re.search(r'height="([\d.]+)"', s).group(1))
        for m in re.finditer(r'<text x="([-\d.]+)" y="([-\d.]+)"', s):
            x, y = float(m.group(1)), float(m.group(2))
            assert -2 <= x <= w + 2 and -2 <= y <= h + 2, \
                'a label sits at %.1f,%.1f outside a %.0fx%.0f canvas' % (
                    x, y, w, h)


def test_the_ways_round_the_crag_exist_at_all():
    """*** THEY WERE MISSING FROM roads.tsv ENTIRELY UNTIL DAY 96. ***

    Coll's trail has been walked every expedition since day 20 and the outcrop
    above it eleven times, and neither was in the data -- so `road_between` said
    there was no way from the north road to the cave the party lives out of.
    """
    rd = land.roads()
    assert 'crag_trail' in rd and rd['crag_trail']['kind'] == 'track'
    # A CART NEVER REACHES THE DOOR, and the drawing has to agree with the
    # sentence places.tsv has carried since it was corrected.
    assert rd['outcrop_path']['kind'] == 'path', (
        'the outcrop is feet and hooves only; calling it a track would make '
        'it cart-passable at 15 miles a day')
    assert land.road_between('basecamp', 'watercourse') is not None
