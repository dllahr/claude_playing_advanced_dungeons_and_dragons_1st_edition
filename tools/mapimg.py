#!/usr/bin/env python3
"""The overland map as SVG. Same data, a medium that can actually draw it.

    python tools/mapimg.py                      # the party's map -> SVG
    python tools/mapimg.py --true               # the DM's. NOT FOR THE TABLE
    python tools/mapimg.py --around wethersby --miles 25
    python tools/mapimg.py --html               # a page with both legends

**This does not replace `overland.py`'s ASCII.** They have different readers:
the text map is read inline, in the middle of narrating, and can be quoted; this
one is for looking at properly. Both are rendered from `campaign/places.tsv` and
`campaign/knowledge.tsv`, so neither can drift from the other.

WHAT THE PIXELS BUY, and it is not just tidiness:

  * **the aspect is simply true.** The ASCII map carries a 2:1 character hack
    and has to say so in its own header;
  * **labels have sub-pixel positions**, so nothing has to be dropped for want
    of a free cell -- which the text renderer had to do until it learned to
    reserve margin;
  * **A VAGUE POSITION CAN BE DRAWN AS A CIRCLE.** In text, Quasqueton's
    uncertainty is a footnote reading "~ within 1,000 ft". Here it is a dashed
    ring you can see, and the knowledge layer stops being a column and becomes
    the picture.

SVG rather than PNG on purpose: it is text, so it diffs and greps, it needs no
library at all, and it scales without being re-rendered. Output lands in
`campaign/output/`, which is gitignored -- **it is derived, like every other
view in this project.**

⚠ `--true` DRAWS PLACES THE PARTY HAS NEVER HEARD OF. It is a DM artifact and
writes to a file named so, and `CHECKLIST` section 8 applies to a picture at
least as hard as to a sentence.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overland as land                                          # noqa: E402
import entities as entmod                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'campaign', 'output')

PX_PER_MILE = 9.0          # the whole world is then about 1,000 px tall
PAD = 90

STYLE = {
    'city':     dict(r=8.5, fill='#1b1b1b'),
    'town':     dict(r=6.5, fill='#2f2f2f'),
    'hall':     dict(r=6.5, fill='#6b3f14'),
    'village':  dict(r=4.5, fill='#4a4a4a'),
    'holding':  dict(r=4.0, fill='#4f6b2a'),
    'hamlet':   dict(r=3.0, fill='#777'),
    'camp':     dict(r=3.5, fill='#8a6d1f'),
    'landmark': dict(r=3.5, fill='#5b5b8a'),
    'dungeon':  dict(r=5.0, fill='#7a1f1f'),
}


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def _bounds(pts):
    xs = [v[0] for v in pts.values()]
    ys = [v[1] for v in pts.values()]
    return min(xs), max(xs), min(ys), max(ys)


def svg(pts=None, kn=None, true=False, px_per_mile=PX_PER_MILE):
    pts = pts if pts is not None else land.points()
    all_pts = land.points()
    kn = kn if kn is not None else land.knowledge()
    real = {k: v for k, v in pts.items()
            if (v[2].get('kind') or '') not in ('region', 'hundred')}
    if not true:
        real = {k: v for k, v in real.items()
                if land.level_of(k, kn) in (land.KNOWN, land.VAGUE)}
    if not real:
        return '<svg xmlns="http://www.w3.org/2000/svg"/>'

    k = px_per_mile / land.MILE          # feet -> px
    x0, x1, y0, y1 = _bounds(real)
    w = (x1 - x0) * k + PAD * 2
    h = (y1 - y0) * k + PAD * 2

    def X(fx):
        return (fx - x0) * k + PAD

    def Y(fy):
        return h - PAD - (fy - y0) * k      # SVG y grows DOWN; north is up

    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
         'viewBox="0 0 %.0f %.0f" font-family="Georgia,serif">' % (w, h, w, h),
         '<rect width="100%%" height="100%%" fill="#f6f1e4"/>']

    # roads under everything
    shown_ways = land.ways(kn, true=true)
    for r in sorted(land.roads().values(),
                    key=lambda r: r.get('kind') != 'road'):
        stops = land.stops_of(r)
        name, kind = r['name'], (r.get('kind') or 'road')
        if name not in shown_ways:
            continue        # a road they have not heard of
        seq = [s for s in stops if s in real]
        if len(seq) < 2:
            continue
        d = ' '.join('%s%.1f,%.1f' % ('M' if i == 0 else 'L',
                                      X(pts[s][0]), Y(pts[s][1]))
                     for i, s in enumerate(seq))
        # A TRACK IS NOT A ROAD and the drawing says so: rugged terrain for a
        # vehicle, so fifteen miles a day for a cart rather than twenty-five.
        if kind == 'road':
            o.append('<path d="%s" fill="none" stroke="#b9a77e" '
                     'stroke-width="5" stroke-linecap="round"/>' % d)
            o.append('<path d="%s" fill="none" stroke="#8d7b52" '
                     'stroke-width="1.2" stroke-dasharray="7 5"/>' % d)
        else:
            o.append('<path d="%s" fill="none" stroke="#b9a77e" '
                     'stroke-width="2" stroke-linecap="round" '
                     'stroke-dasharray="6 4"/>' % d)
        mid = seq[len(seq) // 2]
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8d7b52" '
                 'font-style="italic">%s</text>'
                 % (X(pts[mid][0]) + 9, Y(pts[mid][1]) - 8, esc(name)))

    # *** the knowledge layer, drawn rather than footnoted ***
    for pid, (fx, fy, r) in sorted(real.items()):
        if land.level_of(pid, kn) != land.VAGUE:
            continue
        p_ft = (kn.get(pid, {}).get('precision_ft') or '').strip()
        if not p_ft:
            continue
        rad = float(p_ft) * k
        if rad < 3:
            # Drawn to scale or not at all. Inflating it so it can be SEEN
            # would be drawing a bigger doubt than the party actually has,
            # which is the one thing a map of knowledge must not do. The '~'
            # beside the glyph carries it instead.
            continue
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#c84422" '
                 'fill-opacity="0.10" stroke="#c84422" stroke-opacity="0.65" '
                 'stroke-width="1.2" stroke-dasharray="5 4"/>'
                 % (X(fx), Y(fy), rad))

    placed, unlabelled = [], []       # (x, y, w, h) of labels already written

    def free(bx, by, bw, bh):
        for (ax, ay, aw, ah) in placed:
            if not (bx + bw < ax or ax + aw < bx or
                    by + bh < ay or ay + ah < by):
                return False
        return True

    for pid, (fx, fy, r) in sorted(real.items(), key=lambda kv: -kv[1][1]):
        st = STYLE.get(r.get('kind') or '', dict(r=4, fill='#555'))
        cx, cy = X(fx), Y(fy)
        lv = land.level_of(pid, kn)
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" '
                 'stroke="#f6f1e4" stroke-width="1.5"/>'
                 % (cx, cy, st['r'], st['fill']))

        text = r['name'] + ('' if not true or r.get('fix') == 'attested'
                            else ' †')
        fs = 13 if (r.get('kind') or '') in ('city', 'town', 'hall') else 11
        tw, th = len(text) * fs * 0.55, fs + 3

        # Close in first, then further out ON A LEADER LINE. *** The ASCII
        # renderer has to give up and SAY it gave up; this one does not, and
        # that is most of what a drawing buys. The crag turning, the basecamp
        # and the cave mouth sit within two miles of each other and the first
        # version of this file dropped one of the three labels in silence,
        # which is worse than the terminal's honest failure. ***
        spots = [(st['r'] + 6, 4, 'start', False),
                 (-st['r'] - 6, 4, 'end', False),
                 (0, -st['r'] - 6, 'middle', False),
                 (0, st['r'] + fs + 3, 'middle', False),
                 (st['r'] + 6, -10, 'start', False),
                 (-st['r'] - 6, 16, 'end', False)]
        for reach in (26, 40, 58, 80):
            spots += [(reach, -reach * 0.45, 'start', True),
                      (-reach, -reach * 0.45, 'end', True),
                      (reach, reach * 0.55, 'start', True),
                      (-reach, reach * 0.55, 'end', True)]
        for dx, dy, anchor, lead in spots:
            bx = cx + dx - (tw if anchor == 'end' else
                            tw / 2 if anchor == 'middle' else 0)
            by = cy + dy - th
            if free(bx, by, tw, th):
                placed.append((bx, by, tw, th))
                if lead:
                    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                             'stroke="#999" stroke-width="0.8"/>'
                             % (cx, cy, cx + dx * 0.88, cy + dy - 3))
                o.append('<text x="%.1f" y="%.1f" font-size="%d" '
                         'text-anchor="%s" fill="#222">%s</text>'
                         % (cx + dx, cy + dy, fs, anchor, esc(text)))
                break
        else:
            unlabelled.append(r['name'])
        if lv == land.VAGUE:
            o.append('<text x="%.1f" y="%.1f" font-size="14" fill="#c84422" '
                     'font-weight="bold">~</text>'
                     % (cx - st['r'] - 9, cy - st['r'] - 1))

    # scale bar, in real units, at the real scale
    for step in (100, 50, 20, 10, 5, 2, 1):
        if step * px_per_mile <= (w - PAD * 2) * 0.35:
            break
    bx, by = PAD, h - PAD * 0.45
    o += ['<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" '
          'stroke-width="2"/>' % (bx, by, bx + step * px_per_mile, by),
          '<text x="%.1f" y="%.1f" font-size="11" fill="#333">%d mile%s</text>'
          % (bx, by - 6, step, '' if step == 1 else 's')]
    # north arrow
    nx, ny = w - PAD * 0.55, h - PAD * 0.95
    o += ['<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" '
          'stroke-width="2"/>' % (nx, ny + 26, nx, ny - 4),
          '<path d="M%.1f,%.1f l-5,9 l10,0 z" fill="#333"/>' % (nx, ny - 8),
          '<text x="%.1f" y="%.1f" font-size="12" text-anchor="middle" '
          'fill="#333">N</text>' % (nx, ny + 42)]

    title = ('THE TRUE MAP — DM ONLY' if true else "THE PARTY'S MAP")
    sub = ['computed from places.tsv and knowledge.tsv',
           'a dashed ring is how far out the party would be']
    if unlabelled:
        # Say so, exactly as the terminal renderer does. A drawing that loses a
        # name in silence is worse than a terminal that admits it.
        sub.append('NO ROOM FOR A LABEL: ' + ', '.join(unlabelled))
    o += ['<rect x="4" y="4" width="%.0f" height="%.0f" fill="none" '
          'stroke="#ddd0b0" stroke-width="2"/>' % (w - 8, h - 8),
          '<text x="%.1f" y="%.1f" font-size="17" fill="#222">%s</text>'
          % (PAD * 0.6, PAD * 0.6, title)]
    for i, line in enumerate(sub):
        o.append('<text x="%.1f" y="%.1f" font-size="10" fill="#777">%s</text>'
                 % (PAD * 0.6, PAD * 0.6 + 14 + i * 12, esc(line)))
    o.append('</svg>')
    return '\n'.join(o)


def html(pts=None, kn=None, true=False, px_per_mile=PX_PER_MILE):
    kn = kn if kn is not None else land.knowledge()
    pc = entmod.places()
    heard = sorted(k for k in pc if land.level_of(k, kn) == land.HEARD)
    body = svg(pts, kn, true, px_per_mile)
    rows = []
    for pid in sorted(pc):
        if (pc[pid].get('kind') or '') in ('region', 'hundred'):
            continue
        lv = land.level_of(pid, kn)
        if not true and lv == land.UNKNOWN:
            continue
        rows.append('<tr><td>%s</td><td>%s</td><td class=%s>%s</td>'
                    '<td>%s</td></tr>'
                    % (esc(pc[pid]['name']), esc(pc[pid].get('kind', '')),
                       lv, lv, esc((kn.get(pid, {}).get('how') or '')[:90])))
    return '''<title>%s</title>
<style>
 body{font:15px/1.5 Georgia,serif;max-width:100%%;margin:0;padding:1.5rem;
      background:#fbf8f0;color:#222}
 svg{max-width:100%%;height:auto;border:1px solid #ddd0b0;background:#f6f1e4}
 table{border-collapse:collapse;margin-top:1.2rem;font-size:13px}
 td,th{border-bottom:1px solid #e5dcc4;padding:.3rem .7rem;text-align:left}
 .known{color:#2c6e2c}.vague{color:#c84422}.heard{color:#8d7b52}
 .note{color:#666;font-size:13px;max-width:60em}
</style>
<h2>%s</h2>
%s
<p class=note><b>Known</b> &mdash; been there and attended.
<b class=vague>Vague</b> &mdash; been there in a hurry, or hearsay with a
direction; the dashed ring is how far out they would be.
<b class=heard>Heard of</b> &mdash; named, no position, <em>not drawn</em>.</p>
%s
<table><tr><th>place<th>kind<th>they<th>how</tr>%s</table>
''' % (esc('The true map' if true else "The party's map"),
       esc('THE TRUE MAP — DM ONLY' if true else "THE PARTY'S MAP"),
       body,
       ('<p class=note><b>Heard of and not placed:</b> ' +
        ', '.join(esc(pc[k]['name']) for k in heard) +
        ' &mdash; they could not put these on a map, and this page does not '
        'pretend otherwise.</p>') if heard and not true else '',
       ''.join(rows))


def build_parser():
    p = argparse.ArgumentParser(
        prog='mapimg.py', description="The overland map as SVG or a page.")
    p.add_argument('--true', action='store_true',
                   help='THE DM MAP. Draws places the party has never heard of')
    p.add_argument('--html', action='store_true', help='a page, not a bare SVG')
    p.add_argument('--around')
    p.add_argument('--miles', type=float, default=30)
    p.add_argument('--px-per-mile', type=float, default=PX_PER_MILE)
    p.add_argument('-o', '--out')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    pts = land.points()
    if a.around:
        cid = entmod.resolve(a.around, entmod.places())
        if cid is None:
            print('no place %r' % a.around, file=sys.stderr)
            return 1
        pts = land.crop(pts, cid, a.miles)
    text = (html if a.html else svg)(pts, true=a.true,
                                     px_per_mile=a.px_per_mile)
    os.makedirs(OUTDIR, exist_ok=True)
    name = a.out or os.path.join(
        OUTDIR, '%s_map%s.%s' % ('DM_TRUE' if a.true else 'party',
                                 ('_' + a.around.lower().replace(' ', '_'))
                                 if a.around else '',
                                 'html' if a.html else 'svg'))
    with open(name, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print('wrote %s  (%d bytes)' % (os.path.relpath(name, ROOT), len(text)))
    if a.true:
        print('  *** DM ARTIFACT. It draws places the party has never heard '
              'of. CHECKLIST section 8 applies to a picture at least as hard '
              'as to a sentence.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
