#!/usr/bin/env python3
"""Replay what the party has done to the dungeon onto the map database.

    python tools/world.py replay --db mapdb/output/b1/b1.sqlite --level 1
    python tools/world.py state --level 1
    python tools/world.py deployed
    python tools/world.py log --scope edge --target 17,13,V --change spiked_open \
        --exped 3 --turn 58 --who Tristle --item "iron spike" --qty 2 \
        --note "two at the bottom, quietly"
    python tools/world.py check --db mapdb/output/b1/b1.sqlite --level 1

`campaign/world_changes.tsv` is the source of record; the database is a cache
rebuilt from the scanned page, and a rebuild wipes every change the party has
made along with `cells.seen`. RUN `replay` AFTER EVERY REBUILD.

Why a log and not columns edited in place
-----------------------------------------
The database is derived. `mapdb/build.py` deletes and recreates it from the
PDF, so a state written straight into SQLite survives exactly until the next
classifier tweak. Worse, it survives *silently*: nothing announces that the
spiked door has quietly become unspiked again.

Replay is IDEMPOTENT, unlike `mapdb/markers.py --apply`, which mutates a
database in place and gives different answers on a second run. This one always
starts from whatever the build produced and applies the entire log, so running
it twice is the same as running it once.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, read_tsv, today                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'world_changes.tsv')
INVENTORY_LOG = os.path.join(ROOT, 'campaign', 'inventory_log.tsv')

# This log names gear in prose ("iron spike"); the inventory log names it by
# asset id. One small map rather than a fuzzy stem match, because a guess
# cannot be a constraint.
ITEM_TO_ASSET = {'iron spike': 'iron_spike', 'wooden spike': 'wooden_spike',
                 'rope, 50 ft': 'rope_50ft', 'ten-foot pole': 'ten_foot_pole',
                 'laboratory glass, bulky': 'lab_glass_bulky'}

SCOPES = ('edge', 'cell', 'area', 'seen')

# Known states per scope. These are WARNINGS, not constraints -- see the
# comment on `edges.state` in mapdb/schema.sql. An unanticipated state at the
# table must not raise; the game does not stop because a verb is new.
KNOWN = {
    'edge': ('spiked_open', 'spiked_shut', 'wedged', 'broken', 'barred',
             'locked', 'unlocked', 'stuck', 'open', 'closed', 'oiled'),
    'cell': ('burned', 'flooded', 'blocked', 'pit_sprung', 'searched',
             'cleared'),
    'area': ('cleared', 'looted', 'occupied', 'burned'),
    'seen': ('yes', 'no'),
}
REVERT = 'revert'

# Which states make a boundary passable regardless of what the map draws.
# A door spiked open cannot be closed by anything that lacks hands and a
# crowbar, and that is the whole reason the party spends spikes on it.
FORCED_OPEN = ('spiked_open', 'broken', 'open')
FORCED_SHUT = ('spiked_shut', 'barred', 'stuck', 'closed')


# ------------------------------------------------------------------ parsing

def parse_target(scope, target):
    """('edge','17,13,V') -> (17, 13, 'V'). Raises ValueError on nonsense."""
    t = target.strip()
    if scope == 'edge':
        f = t.split(',')
        if len(f) != 3 or f[2].strip().upper() not in ('V', 'H'):
            raise ValueError('edge target must be "x,y,V" or "x,y,H", got %r' % t)
        return int(f[0]), int(f[1]), f[2].strip().upper()
    if scope == 'cell':
        f = t.split(',')
        if len(f) != 2:
            raise ValueError('cell target must be "x,y", got %r' % t)
        return int(f[0]), int(f[1])
    if scope == 'area':
        return t
    if scope == 'seen':
        if t.startswith('area:'):
            return ('area', t[5:])
        f = t.split(',')
        if len(f) != 2:
            raise ValueError('seen target must be "x,y" or "area:N", got %r' % t)
        return ('cell', (int(f[0]), int(f[1])))
    raise ValueError('unknown scope %r' % scope)


def _order(pair):
    """Sort key putting the log in GAME order: expedition, then turn.

    File order is not good enough. The log is append-only, so a row backfilled
    later lands at the bottom -- and the expedition-1 spiking of the pair-2 door
    was written after the expedition-3 row that reopened it, which under file
    order made the party's oldest action supersede its newest and left the door
    shut.

    A blank turn sorts LAST within its expedition, because a row logged without
    one is almost always "at some point during that trip" and in practice has
    meant the end of it. Ties fall back to file order.
    """
    i, r = pair

    def num(key, default):
        v = (r.get(key) or '').strip()
        try:
            return float(v)
        except ValueError:
            return default

    return (num('exped', float('inf')), num('turn', float('inf')), i)


def load(path=None, map_name=None, level=None):
    """Log rows for one map and level, in game order.

    BOTH filters are needed. Filtering on `level` alone replayed every one of
    Quasqueton's changes onto the DMG sample dungeon -- they are both level 1 --
    and reported 73 successful updates while doing it. A silent success is the
    worst failure mode this project has.
    """
    rows = read_tsv(path or LOG, missing_ok=True)
    if map_name is not None:
        rows = [r for r in rows
                if (r.get('map') or '').strip().lower() == map_name.lower()]
    if level is not None:
        rows = [r for r in rows if str(r.get('level', '')).strip() == str(level)]
    return [r for _, r in sorted(enumerate(rows), key=_order)]


def map_of(db):
    """Infer the map name from the database path, e.g. .../b1/b1.sqlite -> b1."""
    return os.path.splitext(os.path.basename(db))[0].split('_')[0].lower()


def validate(rows):
    """Warnings, never exceptions. Returns a list of strings."""
    warn = []
    for i, r in enumerate(rows, start=1):
        scope, change = r.get('scope', ''), r.get('change', '')
        if scope not in SCOPES:
            warn.append('row %d: unknown scope %r (expected one of %s)'
                        % (i, scope, '/'.join(SCOPES)))
            continue
        if change != REVERT and change not in KNOWN[scope]:
            warn.append('row %d: %s state %r is not one of the documented '
                        'values %s -- applying it anyway'
                        % (i, scope, change, ', '.join(KNOWN[scope])))
        try:
            parse_target(scope, r.get('target', ''))
        except (ValueError, IndexError) as e:
            warn.append('row %d: %s' % (i, e))
        q = (r.get('qty') or '').strip()
        if q:
            try:
                int(q)
            except ValueError:
                warn.append('row %d: qty %r is not a whole number' % (i, q))
    return warn


# ------------------------------------------------------------------- state

def current(rows):
    """Fold the log down to what is true now.

    Later rows supersede earlier ones on the same target -- that is the whole
    mechanism by which a change is undone. Returns
    {scope: {target: (change, row)}} with reverted targets dropped.
    """
    state = {s: {} for s in SCOPES}
    for r in rows:
        scope = r.get('scope', '')
        if scope not in state:
            continue
        try:
            key = parse_target(scope, r.get('target', ''))
        except (ValueError, IndexError):
            continue
        change = r.get('change', '')
        if change == REVERT or (scope == 'seen' and change == 'no'):
            state[scope].pop(key, None)
        else:
            state[scope][key] = (change, r)
    return state


def deployed(rows):
    """Gear currently left in the world, netted per item.

    This is the counterpart to campaign/inventory_log.tsv, which holds what is
    OWNED -- so CARRIED = owned - emplaced, derived, and the two can never
    drift. Keeping emplaced gear in a prose note on an inventory line is
    what once had the DM tell the player their spikes were unavailable when
    they had been recovered two expeditions earlier.
    """
    net, where = {}, {}
    for r in rows:
        item = (r.get('item') or '').strip()
        qty = (r.get('qty') or '').strip()
        if not item or not qty:
            continue
        try:
            n = int(qty)
        except ValueError:
            continue
        net[item] = net.get(item, 0) + n
        where.setdefault(item, []).append(
            (n, r.get('scope', ''), r.get('target', ''), r.get('exped', ''),
             r.get('note', '')))
    return {k: v for k, v in net.items() if v}, where


# ------------------------------------------------------------------ replay

def replay(db, level, rows=None, quiet=False):
    """Apply the log to the database. Returns (applied, problems)."""
    rows = load(map_name=map_of(db), level=level) if rows is None else rows
    st = current(rows)
    con = sqlite3.connect(db)
    applied, problems = 0, []

    def run(sql, args, what):
        cur = con.execute(sql, args)
        if cur.rowcount == 0:
            problems.append('matched nothing in the map: %s' % what)
        return cur.rowcount

    # Clear first, so replay is idempotent and a removed log row really does
    # disappear rather than lingering from an earlier run.
    con.execute('UPDATE cells SET state=NULL, state_note=NULL, seen=0'
                ' WHERE level=?', (level,))
    con.execute('UPDATE edges SET state=NULL, state_note=NULL WHERE level=?',
                (level,))
    con.execute('UPDATE rooms SET state=NULL, state_note=NULL WHERE level=?',
                (level,))

    for (x, y, o), (change, r) in st['edge'].items():
        applied += run(
            'UPDATE edges SET state=?, state_note=? WHERE level=? AND x=? AND'
            ' y=? AND orient=?', (change, _note(r), level, x, y, o),
            'edge %d,%d,%s' % (x, y, o))
    for (x, y), (change, r) in st['cell'].items():
        applied += run(
            'UPDATE cells SET state=?, state_note=? WHERE level=? AND x=? AND y=?',
            (change, _note(r), level, x, y), 'cell %d,%d' % (x, y))
    for num, (change, r) in st['area'].items():
        applied += run(
            'UPDATE rooms SET state=?, state_note=? WHERE level=? AND number=?',
            (change, _note(r), level, num), 'area %s' % num)
    for key, (_, r) in st['seen'].items():
        if key[0] == 'area':
            applied += run(
                'UPDATE cells SET seen=1 WHERE level=? AND room=?',
                (level, key[1]), 'seen area %s' % key[1])
        else:
            x, y = key[1]
            applied += run('UPDATE cells SET seen=1 WHERE level=? AND x=? AND y=?',
                           (level, x, y), 'seen cell %d,%d' % (x, y))
    con.commit()
    con.close()
    if not quiet:
        for w in validate(rows):
            print('  WARNING ' + w)
        for p in problems:
            print('  PROBLEM ' + p)
    return applied, problems


def _note(r):
    """The audit trail that lands in the database beside the state."""
    bits = []
    if r.get('exped'):
        bits.append('exp.%s' % r['exped'])
    if r.get('turn'):
        bits.append('turn %s' % r['turn'])
    if r.get('who'):
        bits.append(r['who'])
    head = ' '.join(bits)
    note = (r.get('note') or '').strip()
    item = (r.get('item') or '').strip()
    if item and (r.get('qty') or '').strip():
        note = ('%s x%s emplaced' % (item, r['qty'])
                + ('; ' + note if note else ''))
    return ('%s: %s' % (head, note)).strip(': ').strip() or head


# --------------------------------------------------------------- reporting

def report_state(rows, map_name, level):
    out = ['what the party has done to %s, level %s' % (map_name, level), '']
    st = current(rows)
    for scope in ('edge', 'cell', 'area'):
        items = sorted(st[scope].items(), key=lambda kv: str(kv[0]))
        if not items:
            continue
        out.append('%s:' % scope)
        for key, (change, r) in items:
            out.append('  %-12s %-12s %s' % (key if scope == 'area'
                                             else ','.join(map(str, key)),
                                             change, _note(r)))
        out.append('')
    n = len(st['seen'])
    out.append('seen: %d target(s) marked verified' % n)
    if not any(st[s] for s in ('edge', 'cell', 'area')):
        out.append('(no changes logged for this level)')
    return '\n'.join(out)


def report_deployed(rows):
    net, where = deployed(rows)
    if not net:
        return 'nothing of the party\'s is left in the dungeon.'
    out = ['gear currently emplaced in the dungeon',
           '(tools/inventory.py holds what is OWNED; carried = owned - this)', '']
    for item, n in sorted(net.items()):
        out.append('  %-16s %d' % (item, n))
        for q, scope, target, exped, note in where[item]:
            out.append('      %+d  %s %s  exp.%s  %s'
                       % (q, scope, target, exped, note))
    return '\n'.join(out)


def check(db, level, rows=None):
    """Cross-checks that have each already failed once in play."""
    rows = load(map_name=map_of(db) if db else None,
                level=level) if rows is None else rows
    out = []
    out += ['  ' + w for w in validate(rows)]

    # 1. Emplaced gear described in inventory prose instead of logged here.
    #    The old inventory.tsv once carried "TWO ARE IN THE PAIR-2 DOOR holding
    #    it open" as a free-text note, which nothing recomputed and which was
    #    wrong by two expeditions. The check now reads the inventory LOG's note
    #    column, which is where such a sentence would land today.
    net, _ = deployed(rows)
    for r in read_tsv(INVENTORY_LOG, missing_ok=True):
        note = (r.get('note') or '').lower()
        # A note that points AT this log is the fix, not the fault.
        if 'world_changes' in note or 'world.py' in note:
            continue
        if any(w in note for w in ('in the door', 'holding it open',
                                   'spiked open', 'spiked shut', 'wedged in')):
            out.append('  inventory_log.tsv row for %r describes gear left in '
                       'the world in prose: %r -- log it here instead'
                       % (r.get('asset'), r.get('note')))

    # 2. A state applied to a boundary the map does not have.
    if db and os.path.exists(db):
        con = sqlite3.connect(db)
        st = current(rows)
        for (x, y, o) in st['edge']:
            row = con.execute('SELECT kind FROM edges WHERE level=? AND x=? AND'
                              ' y=? AND orient=?', (level, x, y, o)).fetchone()
            if row is None:
                out.append('  edge %d,%d,%s is not in the map at all' % (x, y, o))
            elif row[0] == 'wall' and st['edge'][(x, y, o)][0] in FORCED_OPEN:
                out.append('  edge %d,%d,%s is spiked/broken OPEN but the map '
                           'calls it a plain wall -- if the party went through '
                           'it, the map is wrong and needs a correction, not a '
                           'world change' % (x, y, o))
        con.close()

    # 3. Emplaced gear, and what that leaves carried.
    #    This used to WARN that a thing was "also still counted as carried",
    #    which was right when inventory.tsv stored a carried figure by hand.
    #    It no longer does: tools/inventory.py holds the total OWNED and derives
    #    carried as owned minus emplaced, so the two cannot disagree. The note
    #    survives because restocking in town should still count both.
    if net:
        import inventory as invmod
        owned = invmod.state()
        for item, n in net.items():
            asset = ITEM_TO_ASSET.get(item)
            if asset and asset in owned:
                total = sum(v[0] for v in owned[asset].values())
                out.append('  note: %r -- %g owned, %d emplaced in the dungeon, '
                           '%g carried. Restocking in town should count both.'
                           % (item, total, n, total - n))
    return out or ['  all checks pass']


# --------------------------------------------------------------------- CLI

def build_parser():
    p = argparse.ArgumentParser(
        prog='world.py',
        description='Replay what the party has done to the dungeon onto the '
                    'map database.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='campaign/world_changes.tsv is the source of record; the map '
               'database is a cache. Run `replay` after every rebuild.')
    p.add_argument('--log-file', default=LOG, help='the event log to read')
    sub = p.add_subparsers(dest='cmd', required=True)

    def with_db(sp, required=True):
        sp.add_argument('--db', required=required,
                        help='map database to write to')
        sp.add_argument('--level', type=int, default=1, help='dungeon level')
        return sp

    with_db(sub.add_parser('replay', help='apply the log to the database'))
    r = sub.add_parser('state', help='what is currently changed')
    r.add_argument('--map', default='b1', help='which dungeon')
    r.add_argument('--level', type=int, default=1, help='dungeon level')
    d = sub.add_parser('deployed', help='gear currently left in the dungeon')
    d.add_argument('--map', default=None,
                   help='restrict to one dungeon; default is all of them')
    c = with_db(sub.add_parser('check', help='cross-checks against inventory '
                                             'and the map'), required=False)
    c.set_defaults(db=None)

    lg = sub.add_parser('log', help='append one event',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    lg.add_argument('--scope', required=True, choices=SCOPES)
    lg.add_argument('--target', required=True,
                    help='"x,y,V" for an edge, "x,y" for a cell, "N" for an '
                         'area, "x,y" or "area:N" for seen')
    lg.add_argument('--change', required=True,
                    help='the new state, or "revert" to clear it')
    lg.add_argument('--map', default='b1', help='which dungeon')
    lg.add_argument('--level', type=int, default=1)
    lg.add_argument('--exped', default='', help='expedition number')
    lg.add_argument('--turn', default='', help='elapsed turn, from clock.py')
    lg.add_argument('--who', default='', help='which character did it')
    lg.add_argument('--item', default='', help='gear left behind or recovered')
    lg.add_argument('--qty', default='',
                    help='positive to emplace, NEGATIVE to take back')
    lg.add_argument('--note', default='')
    lg.add_argument('--when', default=None, help='date; defaults to today')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.cmd == 'replay':
        m = map_of(a.db)
        rows = load(a.log_file, m, a.level)
        n, problems = replay(a.db, a.level, rows=rows)
        print('applied %d world change(s) from %d log row(s) to map %r level %d'
              ' of %s' % (n, len(rows), m, a.level, a.db))
        return 1 if problems else 0
    if a.cmd == 'state':
        print(report_state(load(a.log_file, a.map, a.level), a.map, a.level))
        return 0
    if a.cmd == 'deployed':
        print(report_deployed(load(a.log_file, a.map)))
        return 0
    if a.cmd == 'check':
        m = map_of(a.db) if a.db else None
        print('\n'.join(check(a.db, a.level, load(a.log_file, m, a.level))))
        return 0
    if a.cmd == 'log':
        try:
            parse_target(a.scope, a.target)
        except (ValueError, IndexError) as e:
            print('bad target: %s' % e)
            return 1
        for w in validate([dict(scope=a.scope, target=a.target,
                                change=a.change, qty=a.qty)]):
            print('WARNING ' + w)
        line = append(a.log_file, dict(
            when=a.when or today(), map=a.map, exped=a.exped, turn=a.turn,
            level=a.level, scope=a.scope, target=a.target, change=a.change,
            item=a.item, qty=a.qty, who=a.who, note=a.note))
        print('appended to %s:\n  %s' % (a.log_file, line))
        print('\nnow run:  python tools/world.py replay '
              '--db mapdb/output/%s/%s.sqlite --level %d'
              % (a.map, a.map, a.level))
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
