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
    assert land.level_of('wraye') == land.HEARD
    party = mapimg.svg()
    assert 'Wraye' not in party
    assert 'Wraye' in mapimg.svg(true=True)


def test_the_default_is_the_partys_map():
    assert mapimg.svg() == mapimg.svg(true=False)
    assert mapimg.svg(true=True) != mapimg.svg(true=False)


def test_the_page_names_heard_of_places_without_placing_them():
    """The margin is where a name with no position belongs -- on the page as
    well as on the terminal."""
    page = mapimg.html()
    assert 'Heard of and not placed' in page
    assert 'Wraye' in page
    assert 'Wraye' not in page.split('</svg>')[0], 'Wraye is drawn'


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
    assert rings(wide) == [], (
        'a ring was drawn at a zoom where it cannot be to scale. It must be '
        'dropped -- the "~" beside the glyph carries it instead.')
    assert '~' in wide, 'and the ~ must then be there'


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
