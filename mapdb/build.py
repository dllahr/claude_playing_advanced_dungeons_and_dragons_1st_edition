#!/usr/bin/env python3
"""Extract a scanned dungeon map into a SQLite grid.

Replaces the earlier build_dmg.py / run_extract.py pair, which duplicated the
whole render -> fit -> classify path between them.

    conda activate advanced_dnd_1e
    python build.py --key dmg_key --db dmg.sqlite
    python build.py --key dmg_key --plots            # also write diagnostics

The key module (--key) supplies the hand-verified labels and the node graph
read from the module text. It is imported by name, so a new map means a new
`<name>_key.py` and no change here.
"""
import argparse
import importlib
import os
import sqlite3
import sys

import extract as E


# ----------------------------------------------------------------- pipeline

def extract_map(pdf, page, dpi, t_solid, t_open, stair_slots, rooms=None,
                channel='mean', deskew=True, t_thick=4.5, t_gap=0.25,
                boxr=0.42):
    """Render a page and classify every cell and boundary.

    Returns a dict with the grid, the masks, and the per-cell / per-edge stats,
    each already carrying its class and confidence.
    """
    grey, rgb = E.render(pdf, page, dpi, channel=channel)
    skew = 0.0
    if deskew:
        grey, rgb, skew = E.auto_deskew(grey, rgb)
    field = E.find_field(grey)
    grid = E.fit_grid(grey, field)
    rot = E.rotation_check(grey, field, grid.px)
    protect = E.label_boxes(rooms, grid) if rooms else ()   # rooms = cell list
    rock, ink = E.rock_mask(grey, protect=protect)

    cells = E.cell_stats(grey, rock, ink, grid)
    terrain = {}
    for s in cells:
        s['klass'] = E.classify(s, t_solid=t_solid, t_open=t_open)
        s['conf'] = E.cell_confidence(s, s['klass'])
        s['feature'] = 'stairs' if s['slots'] >= stair_slots else None
        s['passage'] = E.passage_kind(s, s['klass'])
        terrain[(s['x'], s['y'])] = s['klass']

    # scenery outside the drawn map frame is not dungeon
    outside = E.outside_cells(terrain, grid.nx, grid.ny)
    for s in cells:
        if (s['x'], s['y']) in outside:
            s['feature'] = 'outside'

    edges = E.edge_stats(rock, grid, boxr=boxr)
    for e in edges:
        e['kind'], e['conf'] = E.classify_edge(e, terrain, grid.nx, grid.ny,
                                               t_thick=t_thick, t_gap=t_gap)

    return dict(grey=grey, rgb=rgb, field=field, grid=grid, rot=rot, skew=skew,
                outside=outside, pdf=pdf, page=page, dpi=dpi, channel=channel,
                rock=rock, ink=ink, cells=cells, edges=edges, terrain=terrain)


def label_cells(key):
    """Every square any area label occupies, from the key module."""
    if key is None:
        return None
    rooms = getattr(key, 'ROOMS', None)
    if not rooms:
        return None
    out = []
    for v in rooms.values():
        out.extend(v if isinstance(v, list) else [v])
    return out


def anchors_of(key):
    """One canonical square per area."""
    rooms = getattr(key, 'ROOMS', {}) or {}
    return {k: (v[0] if isinstance(v, list) else v) for k, v in rooms.items() if v}


# ----------------------------------------------------------------- database

def write_db(db, run, key, level, name, source, schema='schema.sql'):
    """Create the database from scratch and load the extraction plus the key."""
    parent = os.path.dirname(db)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(open(schema).read())
    grid, rot = run['grid'], run['rot']
    con.execute("INSERT INTO levels (level,name,source,pdf,page,dpi,channel,"
                "deskew_deg,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                (level, name, source, run.get('pdf'), run.get('page'),
                 run.get('dpi'), run.get('channel'), run.get('skew', 0.0),
                 'grid %s; residual %+.3f deg' % (grid, rot['angle_deg'])))
    con.executemany(
        "INSERT INTO cells (level,x,y,terrain,feature,passage,notes,confidence)"
        " VALUES (?,?,?,?,?,?,?,?)",
        [(level, s['x'], s['y'], s['klass'], s['feature'], s['passage'],
          'open=%.2f ink=%.3f sides=%s' % (s['open_frac'], s['ink_frac'],
                                           s['rock_sides']), s['conf'])
         for s in run['cells']])
    con.executemany(
        "INSERT INTO edges (level,x,y,orient,kind,notes,confidence)"
        " VALUES (?,?,?,?,?,?,?)",
        [(level, e['x'], e['y'], e['orient'], e['kind'],
          'thick=%.0f hole=%d' % (e['thick'], e['hole']), e['conf'])
         for e in run['edges']])

    if key is None:
        con.commit(); con.close()
        return
    anchors = anchors_of(key)
    names = getattr(key, 'NAMES', {}) or {}
    con.executemany(
        "INSERT INTO rooms (level,number,name,anchor_x,anchor_y,text_ref,"
        "confidence) VALUES (?,?,?,?,?,?,?)",
        [(level, n, names.get(n), x, y, getattr(key, 'TEXT_REF', ''), 9)
         for n, (x, y) in anchors.items()])
    for n, v in key.ROOMS.items():
        for (x, y) in (v if isinstance(v, list) else [v]):
            con.execute("INSERT OR REPLACE INTO room_labels"
                        " (level,number,x,y,source,confidence)"
                        " VALUES (?,?,?,?,'human',10)", (level, n, x, y))
            con.execute("UPDATE cells SET room=? WHERE level=? AND x=? AND y=?",
                        (n, level, x, y))
    for x, y in getattr(key, 'STREAM', []):
        con.execute("UPDATE cells SET feature='stream', confidence=9,"
                    " notes=notes||' | stream (DMG key text)'"
                    " WHERE level=? AND x=? AND y=?", (level, x, y))
    for (x, y), feat in getattr(key, 'FEATURES', {}).items():
        con.execute("UPDATE cells SET feature=?, confidence=9,"
                    " notes=notes||' | '||?||' (module text)'"
                    " WHERE level=? AND x=? AND y=?", (feat, feat, level, x, y))
    for (x, y), note in getattr(key, 'MARKERS', {}).items():
        con.execute("UPDATE cells SET feature=COALESCE(feature||'+','')||'secret_marker',"
                    " notes=notes||' | '||? WHERE level=? AND x=? AND y=?",
                    (note, level, x, y))
    for x, y, o, kind, note in getattr(key, 'SECRET_EDGES', []):
        con.execute("UPDATE edges SET kind=?, notes=notes||' | '||?, confidence=9"
                    " WHERE level=? AND x=? AND y=? AND orient=?",
                    (kind, note, level, x, y, o))
    con.executemany(
        "INSERT OR REPLACE INTO connections"
        " (level,from_room,to_room,kind,source,notes,confidence)"
        " VALUES (?,?,?,?,?,?,?)",
        [(level, a, b, k, 'text', note, 8)
         for a, b, k, note in getattr(key, 'CONNECTIONS', [])])
    con.commit()
    con.close()


PLAY_OVERRIDE_MARKER = (
    '*** PLAY OVERRIDE -- NOT ON THE PRINTED PAGE. A page-render check should '
    'SKIP this cell/edge, not flag it as a mismatch. ***')


def apply_corrections(db, path, level, quiet=False):
    """Overlay human corrections. Applied last, so they always win.

    The build recreates the database from scratch, so a correction made
    directly in SQLite dies at the next run. Recording it here makes it durable
    and doubles as a regression set: after a threshold change, re-run and check
    that none of these had to move.

    *** TWO KINDS OF ROW, AND THEY ARE NOT THE SAME CLAIM. *** Most corrections
    fix a MISREAD of the printed page -- the classifier saw a numeral as rock,
    the S-glyph as furniture. An eighth column, `provenance`, marks the other
    kind: `play` means the party and the DM agreed to put something on the map
    that the PAGE DOES NOT SHOW AT ALL -- day 99's opening at (4,15,H), added
    because six orcs needed somewhere to have gone, with the player's own
    permission on record and connectivity checked before it was applied.
    Omit the column, or write `extraction`, for the ordinary kind.

    A `play` row gets `PLAY_OVERRIDE_MARKER` prefixed onto its note, so it is
    greppable, so a future page-render verification pass knows to SKIP it
    instead of reporting a correct correction as a mismatch against a page it
    was never trying to match.

    Returns (applied, problems).
    """
    if not path or not os.path.exists(path):
        return 0, []
    con = sqlite3.connect(db)
    applied, problems = 0, []
    for ln, raw in enumerate(open(path), start=1):
        line = raw.split('#')[0].strip()
        if not line:
            continue
        f = [c.strip() for c in line.split('\t') if c.strip()]
        if len(f) < 5:
            problems.append('%s:%d malformed: %r' % (path, ln, raw.strip()))
            continue
        what, orient, value = f[0], f[3], f[4]
        try:
            x, y = int(f[1]), int(f[2])
        except ValueError:
            problems.append('%s:%d non-integer coordinate: %r' % (path, ln, line))
            continue
        who = f[5] if len(f) > 5 else '?'
        note = f[6] if len(f) > 6 else ''
        provenance = f[7] if len(f) > 7 else 'extraction'
        if provenance not in ('extraction', 'play'):
            problems.append('%s:%d provenance %r is neither extraction nor '
                            'play: %r' % (path, ln, provenance, raw.strip()))
            continue
        if provenance == 'play':
            note = (PLAY_OVERRIDE_MARKER + ' ' + note) if note \
                else PLAY_OVERRIDE_MARKER
        if what == 'cell':
            cur = con.execute(
                "UPDATE cells SET terrain=?, confidence=10,"
                " notes=notes||' | CORRECTED by '||?||': '||?"
                " WHERE level=? AND x=? AND y=?", (value, who, note, level, x, y))
        elif what == 'edge':
            cur = con.execute(
                "UPDATE edges SET kind=?, confidence=10,"
                " notes=notes||' | CORRECTED by '||?||': '||?"
                " WHERE level=? AND x=? AND y=? AND orient=?",
                (value, who, note, level, x, y, orient))
        elif what == 'feature':
            # Override a cell FEATURE -- 'stairs', 'pit', and so on. Use "none"
            # to clear one.
            #
            # The stair detector counts thin parallel slots in a square, because
            # that is what a flight of treads looks like. Furniture drawn as two
            # or three parallel rectangles -- chests side by side, a rack, a
            # bench -- looks identical, and B1 draws a great deal of furniture.
            # Area 34's south-west corner holds two locked chests and came out
            # flagged `stairs` at exactly the threshold (slots = 5 of 5).
            #
            # A false `stairs` is dangerous rather than untidy: it invents a way
            # off the level, and `dmap.py describe` prints it, which is how a
            # room label leaked into narration once already.
            cur = con.execute(
                "UPDATE cells SET feature=?, confidence=10,"
                " notes=notes||' | FEATURE SET by '||?||': '||?"
                " WHERE level=? AND x=? AND y=?",
                (None if value.lower() == 'none' else value, who, note, level, x, y))
        elif what == 'member':
            # Assign a single square to a room BY HAND.
            #
            # `extents.py` derives room membership by flooding across open
            # boundaries, which works everywhere the walls run along grid lines
            # and fails completely where they do not. B1's north-east quadrant
            # is built on 45-degree walls: the rock sits INSIDE the squares, so
            # every boundary measures thin and open and the flood runs straight
            # through what is plainly a wall on the page. Area 34 came out as 41
            # squares with the Room of Pools' own markers inside it.
            #
            # A diagonal wall cannot be expressed as an edge correction -- there
            # is no edge to correct -- so membership has to be stateable
            # directly. See mapdb/lab_notebook.md, "DIAGONAL WALLS defeat a
            # boundary-based model".
            #
            # NOTE: extents.py clears cells.room, so these must be applied
            # AFTER it. rebuild.sh does exactly that.
            # "none" CLEARS membership. extents.py over-assigns as readily as it
            # under-assigns -- it gave the barracks three squares on the far
            # side of the room's north wall -- and a correction file that can
            # only add is only half a correction file.
            cur = con.execute(
                "UPDATE cells SET room=?, confidence=10,"
                " notes=notes||' | ROOM SET by '||?||': '||?"
                " WHERE level=? AND x=? AND y=?",
                (None if value.lower() == 'none' else value,
                 who, note, level, x, y))
        elif what == 'room':
            cur = con.execute(
                "INSERT OR REPLACE INTO rooms"
                " (level,number,anchor_x,anchor_y,notes,confidence)"
                " VALUES (?,?,?,?,?,10)", (level, value, x, y, note))
        else:
            problems.append('%s:%d unknown kind %r' % (path, ln, what))
            continue
        if cur.rowcount == 0:
            problems.append('%s:%d matched nothing: %r' % (path, ln, line))
        applied += cur.rowcount
    con.commit()
    con.close()
    if not quiet:
        for p in problems:
            print('  ' + p)
    return applied, problems


def verify(db, key, level):
    """Cross-check the text-derived node graph against the extracted grid."""
    lines = []
    anchors = anchors_of(key)
    for a, b, kind, _ in getattr(key, 'CONNECTIONS', []):
        if kind == 'none':
            continue
        pa, pb = anchors.get(a), anchors.get(b)
        if not pa or not pb:
            lines.append('  %-4s -> %-4s  no anchor for one end' % (a, b))
            continue
        lines.append('  %-4s -> %-4s  %-7s anchors %s %s, %d cells apart'
                     % (a, b, kind, pa, pb,
                        abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])))
    return lines


# ----------------------------------------------------------------- cli

def build_parser():
    p = argparse.ArgumentParser(
        prog='build.py',
        description='Extract a scanned dungeon map into a SQLite grid database.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='Cells and edges are rebuilt from the image every run; anything a '
               'human decided belongs in the --key module or --corrections file.')
    src = p.add_argument_group('source')
    src.add_argument('--pdf', default="../manuals/tsr02011 - Advanced Dungeons & "
                                      "Dragons (Ad&D) 1St Ed - Dungeon Master'S Guide.pdf",
                     help='PDF holding the map')
    src.add_argument('--page', type=int, default=95,
                     help='0-based page index of the map')
    src.add_argument('--dpi', type=int, default=200,
                     help='render resolution; 200 gives ~40px per 10ft square')
    src.add_argument('--channel', default='mean', choices=list(E.CHANNELS),
                     help="how colour becomes grey. 'mean' for a black-printed "
                          "map; 'r' for a BLUE-printed one such as B1, where blue "
                          "ink absorbs red and the red channel roughly doubles "
                          "the ink/paper contrast")
    src.add_argument('--no-deskew', action='store_true',
                     help='skip rotation correction (it is measured either way)')

    out = p.add_argument_group('output')
    out.add_argument('--db', default='output/dmg/dmg.sqlite',
                     help='SQLite file to write; its directory is created')
    out.add_argument('--level', type=int, default=1, help='dungeon level number')
    out.add_argument('--name', default='DMG sample dungeon (practice)',
                     help='human-readable name for the level')
    out.add_argument('--schema', default='schema.sql', help='schema to create from')
    out.add_argument('--images', default='output/dmg/images',
                     help='directory for diagnostic images')

    hum = p.add_argument_group('human input')
    hum.add_argument('--key', default='dmg_key',
                     help='python module with ROOMS / MARKERS / SECRET_EDGES / '
                          'CONNECTIONS; use "none" to skip')
    hum.add_argument('--corrections', default='corrections.tsv',
                     help='TSV of human corrections, applied last')
    hum.add_argument('--no-corrections', action='store_true',
                     help='ignore the corrections file (to see raw classifier output)')

    tun = p.add_argument_group('classifier thresholds')
    tun.add_argument('--t-solid', type=float, default=0.05,
                     help='cells at or below this open fraction are solid rock. '
                          'Low by design: a diagonal corridor may leave only a '
                          'quarter of a square open and it is still walkable')
    tun.add_argument('--t-open', type=float, default=0.75,
                     help='cells at or above this open fraction are clear floor')
    tun.add_argument('--t-thick', type=float, default=4.5,
                     help='median rock thickness (px) at which a boundary counts '
                          'as a drawn wall rather than a printed ruling. This is '
                          'PRINT-SPECIFIC: the DMG separates at 4.5 (rulings 0-3, '
                          'walls 6+) but B1 is printed in a heavier blue line and '
                          'separates at 6 (rulings 0-3, walls 7+). Check the '
                          'histogram before trusting the default on a new map')
    tun.add_argument('--boxr', type=float, default=0.42,
                     help='half-size, in squares, of the box searched for a door '
                          'glyph on a boundary. Print-specific: B1 draws doors '
                          'about half again the size of the DMG and needs 0.55, '
                          'below which the glyph falls outside the box and the '
                          'door reads as a plain wall')
    tun.add_argument('--t-gap', type=float, default=0.25,
                     help='fraction of a boundary that must be clear of rock for '
                          'it to count as a way through between partial squares')
    tun.add_argument('--stair-slots', type=int, default=5,
                     help='rock/void alternations across a square to call it stairs')

    p.add_argument('--plots', action='store_true',
                   help='also write ECDF, bimodality and mask diagnostics')
    p.add_argument('-q', '--quiet', action='store_true', help='suppress progress output')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    key = None if args.key.lower() == 'none' else importlib.import_module(args.key)
    say = (lambda *a: None) if args.quiet else print

    run = extract_map(args.pdf, args.page, args.dpi,
                      args.t_solid, args.t_open, args.stair_slots,
                      rooms=label_cells(key),
                      channel=args.channel, deskew=not args.no_deskew,
                      t_thick=args.t_thick, t_gap=args.t_gap, boxr=args.boxr)
    say('grid     %s' % run['grid'])
    say('deskew   %+.3f deg applied; residual %+.3f (monotonic=%s)'
        % (run['skew'], run['rot']['angle_deg'], run['rot']['monotonic']))

    counts = {}
    for s in run['cells']:
        counts[s['klass']] = counts.get(s['klass'], 0) + 1
    ecounts = {}
    for e in run['edges']:
        ecounts[e['kind']] = ecounts.get(e['kind'], 0) + 1
    say('cells    %s' % counts)
    say('edges    %s' % ecounts)
    say('outside  %d squares of frame/scenery' % len(run['outside']))
    say('stairs   %d   diagonal %d'
        % (sum(1 for s in run['cells'] if s['feature'] == 'stairs'),
           sum(1 for s in run['cells'] if s['passage'] == 'diagonal')))

    source = '%s page %d, %d dpi' % (os.path.basename(args.pdf), args.page, args.dpi)
    write_db(args.db, run, key, args.level, args.name, source, args.schema)

    if not args.no_corrections:
        n, _ = apply_corrections(args.db, args.corrections, args.level, args.quiet)
        say('applied  %d correction(s) from %s' % (n, args.corrections))

    if key is not None:
        say('\n--- text vs grid ---')
        for line in verify(args.db, key, args.level):
            say(line)

    os.makedirs(args.images, exist_ok=True)
    E.overlay(run['rgb'], run['grid'], os.path.join(args.images, '08_final.png'),
              field=run['field'], cells=run['cells'])
    if args.plots:
        import pandas as pd
        import plots
        df = pd.DataFrame(run['cells'])
        plots.ecdf(df['open_frac'], os.path.join(args.images, '04_ecdf_white.png'),
                   args.t_solid, args.t_open)
        plots.bimodality(df, os.path.join(args.images, '05_bimodality.png'),
                         args.t_solid, args.t_open)
        plots.masks(run['rock'], run['ink'],
                    os.path.join(args.images, '07_rock_vs_ink.png'))
        df.to_csv(os.path.splitext(args.db)[0] + '_cells.csv', index=False)
    say('\nwrote %s' % args.db)
    return 0


if __name__ == '__main__':
    sys.exit(main())
