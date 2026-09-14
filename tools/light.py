#!/usr/bin/env python3
"""Lantern oil and torch stubs, computed from campaign/light.tsv.

    python tools/light.py                                  # every source
    python tools/light.py remaining                         # the party's total
    python tools/light.py lit lantern-torsat --why "into the east corridor"
    python tools/light.py hooded lantern-torsat --why "listening at the door"
    python tools/light.py out lantern-torsat --why "camping"
    python tools/light.py refill lantern-torsat --who Frython
    python tools/light.py new torch-1 --what Torch --who Tristle
    python tools/light.py anchor lantern-yrtone --fuel 12 --why "DM ruling"
    python tools/light.py sources                           # the rules table

Why this exists
---------------
Hit points, experience, the dungeon clock, the state of the dungeon and the
party's position are all computed from append-only logs. Lantern oil was not
tracked at all, which meant the party had **infinite light**: 1,146 rounds of
expedition 4 — 114 turns, nineteen hours of dungeon time — were run without a
single flask being charged against anything. A resource that is never spent is
not a resource, and in a module whose whole tension is how long you can stay
down there, that is the wrong thing to be silently generous about.

So fuel is DATA now, and current fuel is never stored. Every report replays
`campaign/light.tsv` from the beginning, exactly the way `tools/hp.py` replays
wounds. A written-down "18 turns left" is correct for one round and wrong
afterwards, and this campaign has already been burnt twice by a stored total
that went stale (the roster's XP line, and the iron spikes it claimed were in a
door the party had already pulled them out of).

Why a separate tool rather than `clock.py light ...`
----------------------------------------------------
`clock.py` OWNS dungeon time — it is the only thing that writes the round
counter and the wandering jitter. This module is a CONSUMER of that counter, in
the same way `hp.py`, `xp.py`, `world.py` and `party.py` each own one derived
thing and read what they need from the others. Folding fuel into clock.py would
make one module both the authority on time and a reader of it, and would put a
second write-path into `campaign/clock.tsv`, which a live session is appending
to right now. One log, one owner.

WHERE THE NUMBERS COME FROM
---------------------------
`rules/exploration.md`, "Light sources (PHB p. 102, verified)", through
`tools/rules.py`. **No burn time appears in this file.** Not 24, not 6. The
campaign's standing rule is that no rules table is written twice, because the
second copy is the one nobody re-checks against the book.

The table is read literally, wording and all:

  * "24 turns **per pint of oil**"  -> 24 turns, and the word *per* names a fuel
    separate from the fitting, so the source is REFILLABLE.
  * "6 turns (1 hour)"              -> 6 turns, no fuel named, so a torch is a
    CONSUMED ITEM and `refill` on one raises.
  * "infinite"                      -> a magic sword never burns down.

HOODING DOES NOT STOP THE BURN
------------------------------
`rules/exploration.md` is not silent on this and does not have to be guessed at:
*"A hooded lantern can be fully shuttered — lit inside, showing no light"*, and
*"a burning lamp is a heat source whether or not light escapes"*. The flame is
behind the shutter, not out. So `hooded` here changes what the dungeon can see
and NOTHING about what the wick consumes — it deliberately does not touch the
`burning` flag. Only `out` stops the fuel clock.

That is also the conservative reading, which is the one to take when a DM ruling
could go either way: a party that thinks hooding is free will hood the lamp for
eight hours of rest and wake up with oil it has not got.

**Log `out` before a rest.** `clock.py rest --hours 8` advances 480 rounds, and
480 rounds of an un-extinguished lantern is two flasks. The fuel does not know
the party was asleep.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clock                                                    # noqa: E402
import rules                                                    # noqa: E402
from tsvlog import append, read_tsv, today                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'light.tsv')

TABLE = 'Light sources'          # the heading in rules/exploration.md
ROUNDS_PER_TURN = 10             # rules/exploration.md, Time: 1 turn = 10 rounds
WARN_TURNS = 5                   # "close to running out", in turns

# Every kind a row may carry, and what it does. `hooded`/`unhooded` are absent
# from the burn side of this on purpose -- see the module docstring.
KINDS = ('anchor', 'new', 'lit', 'hooded', 'unhooded', 'out', 'refill',
         'spent', 'lost', 'oil', 'draw')

_TURNS = re.compile(r'(\d+)\s*turns?', re.I)
_PER = re.compile(r'\bper\b', re.I)
_LEADING_NUM = re.compile(r'(\d+)')

# Inventory wording -> the row it is priced from in the rules table. This maps
# NAMES ONLY and holds no numbers: every burn time still comes out of
# rules/exploration.md. Anything not listed is reported as unpriced rather than
# guessed at, which is why candles show up in the report as an open question
# instead of quietly counting for zero.
INVENTORY_FUEL = {
    'torch': ('Torch', 'whole'),                 # each torch is one whole burn
    'oil flask': ('Lantern (hooded)', 'fill'),   # one pint = one lantern fill
}


# ------------------------------------------------------------ the rules table

def catalogue(tables=None):
    """{name: what the book says about it}, straight off rules/exploration.md.

    Nothing is interpreted beyond the wording of the Burning time column, and
    the source line travels with it so a report can cite the page.
    """
    t = rules.find(TABLE, tables)
    out = {}
    for row in t['rows']:
        if not row or not row[0].strip():
            continue
        name, radius, burn = row[0].strip(), row[1].strip(), row[2].strip()
        m = _TURNS.search(burn)
        turns = int(m.group(1)) if m else None
        out[name] = dict(
            name=name,
            radius=radius,
            text=burn,
            source=t['source'],
            infinite='infinite' in burn.lower(),
            burn_turns=turns,
            burn_rounds=None if turns is None else turns * ROUNDS_PER_TURN,
            # "24 turns PER PINT of oil" names a fuel; "6 turns (1 hour)" does
            # not. That single word is the whole refillable test, and it is the
            # book's word, not ours.
            refillable=bool(_PER.search(burn)),
        )
    return out


def resolve(name, cat=None):
    """The one catalogue row `name` means. Ambiguity raises, like rules.find.

    "lantern" is allowed to mean "Lantern (hooded)" because typing the
    parenthesis at the table is friction, but "lant" matching two rows must be
    an error rather than a coin toss -- picking the first plausible match is the
    exact failure the rules cache exists to prevent.
    """
    cat = cat if cat is not None else catalogue()
    n = (name or '').strip()
    if not n:
        raise KeyError('no light source named; --what is required')
    for k in cat:
        if k.lower() == n.lower():
            return k
    hits = [k for k in cat if n.lower() in k.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise KeyError('no light source %r in rules/exploration.md (%s)'
                       % (name, ', '.join(sorted(cat))))
    raise KeyError('%r matches %d light sources: %s'
                   % (name, len(hits), ', '.join(sorted(hits))))


# ------------------------------------------------------------ the log

def _num(text, default=None):
    """Parse a numeric log field, tolerating anything the callers actually pass.

    Fields arrive as strings when replayed from the TSV but as ints/floats when
    they come straight off argparse, and the first version assumed a string --
    `light.py anchor ... --fuel 23` crashed with
    `'int' object has no attribute 'strip'` the first time a real figure was
    logged. Coerce first, strip second.
    """
    if text is None:
        return default
    if isinstance(text, (int, float)):
        return float(text)
    t = str(text).strip()
    if not t:
        return default
    try:
        return float(t)
    except ValueError:
        return default


def _order(pair):
    """Game order: expedition, then round, then file position.

    Copied deliberately from tools/world.py -- the log is append-only, so a row
    backfilled later lands at the bottom of the file, and under file order a
    refill remembered after the fact would put the oil in before it was burnt.
    A blank round sorts LAST within its expedition, the same convention
    world_changes.tsv uses for a blank turn.
    """
    i, r = pair
    return (_num(r.get('exped'), float('inf')),
            _num(r.get('round'), float('inf')), i)


def load(path=None):
    """Every row of the log, in GAME order."""
    rows = read_tsv(path or LOG, missing_ok=True)
    return [r for _, r in sorted(enumerate(rows), key=_order)]


def now(clock_log=None):
    """(expedition, round) off the dungeon clock. Fuel burns against THIS.

    Not wall time, and not the last round in the light log: a lantern left
    burning while the clock advances for other reasons is still burning.
    """
    exped, rnd, _, _ = clock.state(clock.load(clock_log))
    return exped, rnd


def what_of(rows, cat=None):
    """{source id: the catalogue row that prices it}, from ANY row naming it.

    Not from the FIRST row in game order, which is what this originally did and
    which the order-independence test caught immediately. The log is
    append-only: a row backfilled a session later sorts by its expedition and
    round, so the earliest event for a source is frequently not the one that
    was written first, and it may well be a bare `out` with no `what` on it.
    Making the replay depend on which row happens to sort first would make
    correctness depend on exactly the file order this module refuses to trust.

    A source logged under two different rules-table rows raises. One physical
    light source is priced from one line of PHB p. 102.
    """
    cat = cat if cat is not None else catalogue()
    out = {}
    for r in rows:
        sid = (r.get('source') or '').strip()
        what = (r.get('what') or '').strip()
        if not sid or not what:
            continue
        name = resolve(what, cat)
        if sid in out and out[sid] != name:
            raise ValueError('%s is logged as both %r and %r — one light '
                             'source, one line of the rules table'
                             % (sid, out[sid], name))
        out[sid] = name
    return out


def _fresh(sid, what, cat, at):
    entry = cat[what]
    return dict(id=sid, what=what, who='', burning=False, hooded=False,
                infinite=entry['infinite'], refillable=entry['refillable'],
                capacity=entry['burn_rounds'], radius=entry['radius'],
                fuel=None, known=False, certain=True, at=at, burned=0,
                guttered_at=None, gone=False, fills=0, events=0, exped=None)


def _burn_to(s, rnd):
    """Advance one source's fuel clock to `rnd`. The whole model is here.

    Fuel is consumed ONLY while `burning`. Hooding does not clear that flag, so
    a shuttered lamp keeps drinking oil; `out` does clear it, so a party that
    puts the lamp out to sleep spends nothing. That asymmetry is the ruling in
    rules/exploration.md and it is the only place it is enforced.
    """
    dt = rnd - s['at']
    if dt <= 0:
        return
    if not s['burning'] or s['infinite'] or s['gone']:
        s['at'] = rnd
        return
    s['burned'] += dt
    if s['fuel'] is None:                  # unknown stays unknown, never zero
        s['at'] = rnd
        return
    if s['fuel'] <= dt:
        # It guttered partway through. Record WHEN, because "the lamp went out
        # at some point in the last hour" is not something a party can plan
        # around and the round is the only useful form of the answer.
        s['guttered_at'] = s['at'] + s['fuel']
        s['burning'] = False
        s['fuel'] = 0
    else:
        s['fuel'] -= dt
    s['at'] = rnd


def _oil_fresh():
    """The party's oil, as a pool, in ROUNDS -- not a count of flasks.

    A lantern holds a pint and a pint is one flask, so topping up a lamp that
    still has fuel in it does NOT spend a whole flask: it draws only what the
    reservoir can take and leaves the rest IN THE FLASK. That remainder is
    `broached`, and before this existed it was silently thrown away twice over
    -- once out of the lamp and once off the flask count.

    `known` stays False until an `oil` row says how many flasks the party has.
    An untracked pool is reported as untracked, never as empty and never as
    generous: same rule as an `anchor` with no fuel figure.
    """
    return dict(known=False, sealed=0, broached=0.0, opened=0,
                drawn=0.0, short=0.0, untracked=0.0)


def _draw_oil(pool, need, capacity):
    """Take `need` rounds of oil out of the pool. Returns what it could give.

    Broach a sealed flask only when the open one runs dry, which is the whole
    point: a part-used flask is finished before another is opened.
    """
    if need <= 1e-9:
        return 0.0
    pool['drawn'] += need
    if not pool['known']:
        pool['untracked'] += need
        return need
    got = 0.0
    while need > 1e-9:
        if pool['broached'] <= 1e-9:
            if pool['sealed'] <= 0:
                pool['short'] += need
                break
            pool['sealed'] -= 1
            pool['opened'] += 1
            pool['broached'] = float(capacity)
        take = min(need, pool['broached'])
        pool['broached'] -= take
        need -= take
        got += take
    return got


def _apply(s, kind, row, cat, pool=None):
    """One event onto one source, after its fuel has been brought up to date."""
    entry = cat[s['what']]
    fuel_txt = (row.get('fuel') or '').strip()

    if kind in ('anchor', 'new', 'refill', 'spent'):
        if kind == 'refill' and not s['refillable']:
            # The book's own wording decides this: "6 turns (1 hour)" names no
            # fuel. A torch is burnt, not refuelled, and letting one be topped
            # up would hand the party unlimited light through the back door.
            raise ValueError(
                '%s is a %s -- rules/exploration.md prices it at "%s", which '
                'names no fuel, so it is a consumed item and cannot be '
                'refilled. Log a `new` source instead.'
                % (s['id'], s['what'], entry['text']))
        def _pour(want):
            # THE DRAW. Filling a reservoir that is not empty costs only the
            # DIFFERENCE, and the difference is what comes out of a flask; the
            # remainder stays IN the flask. If the party has run out of oil the
            # lamp gets what there was, NOT a full pint.
            before = s['fuel'] if s['fuel'] is not None else 0.0
            if pool is not None and s['refillable'] and want is not None:
                got = _draw_oil(pool, max(0.0, want - before), s['capacity'])
                s['fuel'] = min(want, before + got)
            else:
                s['fuel'] = want
            s['known'] = want is not None

        if kind == 'spent':
            s['fuel'], s['known'] = 0, True
        elif fuel_txt == '?':
            s['fuel'], s['known'] = None, False    # UNKNOWN, said out loud
        elif kind == 'refill':
            # A REFILL IS A POUR AND ALWAYS COSTS OIL. An explicit --fuel names
            # the level the lamp is brought UP TO; it does not make the oil
            # free. Letting a figure skip the draw would hand the party
            # unlimited light through exactly the back door the torch rule
            # above was written to close.
            _pour(int(round(float(fuel_txt) * ROUNDS_PER_TURN))
                  if fuel_txt else s['capacity'])
        elif fuel_txt:
            # `new` or `anchor` with a figure: an ASSERTION about the source --
            # a lamp found with oil in it, a torch, a correction. It states
            # what is there and moves none of the party's own oil.
            s['fuel'], s['known'] = (
                int(round(float(fuel_txt) * ROUNDS_PER_TURN)), True)
        elif kind == 'anchor':
            # An anchor with no fuel figure is not "full", it is a row nobody
            # finished writing. Treat it as unknown rather than generous.
            s['fuel'], s['known'] = None, False
        else:
            _pour(s['capacity'])       # `new` with no figure: filled from ours
        s['burned'] = 0
        s['guttered_at'] = None
        if kind == 'refill':
            s['fills'] += 1
        if kind == 'spent':
            s['burning'] = False
    elif kind == 'lit':
        s['burning'], s['gone'] = True, False
        if s['fuel'] == 0:
            s['guttered_at'] = None
    elif kind == 'hooded':
        # Shutter closed. `burning` is NOT touched -- see the module docstring.
        s['hooded'] = True
    elif kind == 'unhooded':
        s['hooded'] = False
    elif kind == 'out':
        s['burning'], s['hooded'] = False, False
    elif kind == 'lost':
        s['gone'], s['burning'] = True, False
    else:
        raise ValueError('unknown kind %r in the light log; known kinds: %s'
                         % (kind, ', '.join(KINDS)))

    if (row.get('who') or '').strip():
        s['who'] = row['who'].strip()
    if (row.get('certainty') or '').strip().lower() == 'uncertain':
        s['certain'] = False
    elif kind == 'anchor':
        # A `known` anchor is how uncertainty is retired: rule the level once,
        # log it, and every report downstream stops hedging.
        s['certain'] = True
    s['events'] += 1


def _replay(rows=None, at_round=None, cat=None, path=None, clock_log=None):
    """(sources, oil pool) replayed from the log.

    `at_round` defaults to the live dungeon clock. Pass it explicitly in tests
    and anywhere the answer must not move under you.
    """
    cat = cat if cat is not None else catalogue()
    rows = load(path) if rows is None else rows
    whats = what_of(rows, cat)
    src = {}
    pool = _oil_fresh()
    for r in rows:
        sid = (r.get('source') or '').strip()
        if not sid:
            continue
        kind = (r.get('kind') or '').strip().lower()
        rnd = int(_num(r.get('round'), 0))
        # An `oil` row is about the PARTY'S SUPPLY, not about a light source,
        # so it never touches the source machinery -- it has no `what`, no
        # burn time and nothing to bring up to date.
        if kind == 'oil':
            pool['known'] = True
            pool['sealed'] += int(_num(r.get('fuel'), 0) or 0)
            continue
        # A `draw` is oil used for something that is NOT filling a lamp --
        # oiling hinges, soaking a rag, dressing a lock. It comes out of the
        # same pool and out of the BROACHED flask first, because that is what a
        # part-used flask is for. `--fuel` is in TURNS, not flasks: the
        # expedition-4 precedent for oiling a door is "roughly 2 turns' worth
        # off a broached flask, NOT a whole flask".
        if kind == 'draw':
            cap = cat['Lantern (hooded)']['burn_rounds']
            _draw_oil(pool,
                      float(_num(r.get('fuel'), 0) or 0) * ROUNDS_PER_TURN,
                      cap)
            continue
        if sid not in src:
            if sid not in whats:
                raise ValueError(
                    'no row for %r names a `what`, so there is no way to know '
                    'which line of rules/exploration.md prices it' % sid)
            src[sid] = _fresh(sid, whats[sid], cat, rnd)
        s = src[sid]
        # THE ROUND COUNTER RESTARTS AT 0 EVERY EXPEDITION.  Carrying a fuel
        # clock across that boundary is not a rewind to be guarded against, it
        # is a different clock -- and the "never rewind" guard below turns it
        # into INFINITE LIGHT, because max(164, 2263) is 2263 and the lamp has
        # already burned to it.  Expedition 5 ran 164 rounds on a lantern that
        # charged nothing.  This is the second time this tool has produced
        # infinite light; see the header.
        ex = _num(r.get('exped'), None)
        if ex is not None and ex != s['exped']:
            s['exped'] = ex
            s['at'] = rnd            # new clock, no burn across the gap
        else:
            _burn_to(s, rnd)
        _apply(s, kind, r, cat, pool)
    # An explicit at_round means the CALLER has named the moment -- tests, and
    # anywhere the answer must not move. Burn to it and do not second-guess
    # which expedition it belongs to.
    explicit = at_round is not None
    live_exped = None
    if not explicit:
        live_exped, at_round = now(clock_log)
        live_exped = _num(live_exped, None)
    for s in src.values():
        # Never rewind WITHIN an expedition: a row logged ahead of the clock is
        # a row about the future, not a reason to un-burn oil already spent.
        # Against the LIVE clock, only burn a source whose last event is in the
        # live expedition -- otherwise its rounds belong to a different clock
        # and max() turns the guard into infinite light.
        if explicit or s['exped'] is None or live_exped is None \
                or s['exped'] == live_exped:
            _burn_to(s, max(at_round, s['at']))
    return src, pool


def state(rows=None, at_round=None, cat=None, path=None, clock_log=None):
    """{source id: its state now}, replayed from the log.

    `at_round` defaults to the live dungeon clock. Pass it explicitly in tests
    and anywhere the answer must not move under you.
    """
    return _replay(rows, at_round, cat, path, clock_log)[0]


def oil_state(rows=None, at_round=None, cat=None, path=None, clock_log=None):
    """The party's oil as a pool: sealed flasks, and the broached one."""
    return _replay(rows, at_round, cat, path, clock_log)[1]


# ------------------------------------------------------------ reporting

def turns(rounds):
    """Rounds as turns, to one decimal. Turns are what a DM plans in."""
    return rounds / float(ROUNDS_PER_TURN)


def describe(s, at_round):
    """(state word, fuel text, gutter text, warning or '') for one source."""
    if s['gone']:
        word = 'GONE'
    elif s['infinite']:
        word = 'lit (magical)' if s['burning'] else 'dark'
    elif s['burning']:
        word = 'BURNING (hooded)' if s['hooded'] else 'BURNING'
    elif s['guttered_at'] is not None:
        word = 'GUTTERED'
    else:
        word = 'out'

    if s['infinite']:
        return word, 'infinite', '-', ''
    if s['fuel'] is None:
        warn = ('fuel UNKNOWN — %.1f turns burned since the last row that '
                'named a figure' % turns(s['burned']))
        return word, '?', 'UNKNOWN', warn
    left = turns(s['fuel'])
    fuel = '%.1f turns' % left
    if s['guttered_at'] is not None:
        return word, '0.0 turns', 'went out at round %d' % s['guttered_at'], \
            'OUT OF FUEL since round %d' % s['guttered_at']
    if not s['burning']:
        return word, fuel, '-', ''
    gutter = 'round %d' % (at_round + s['fuel'])
    warn = ''
    if left <= WARN_TURNS:
        warn = ('LOW — %.1f turns left, gutters at round %d'
                % (left, at_round + s['fuel']))
    return word, fuel, gutter, warn


def report(src, at_round):
    out = ['round %d' % at_round, '']
    out.append('%-16s %-19s %-9s %-17s %-11s %s'
               % ('source', 'what', 'carried by', 'state', 'fuel', 'gutters'))
    warnings, uncertain = [], []
    for sid in sorted(src):
        s = src[sid]
        word, fuel, gutter, warn = describe(s, at_round)
        out.append('%-16s %-19s %-9s %-17s %-11s %s'
                   % (sid, s['what'], s['who'] or '-', word, fuel, gutter))
        if warn:
            warnings.append('%-16s %s' % (sid, warn))
        if not s['certain']:
            uncertain.append(sid)
    if not src:
        out.append('(no light sources logged)')
    if warnings:
        out += ['', 'WARNINGS'] + ['  ' + w for w in warnings]
    if uncertain:
        out += ['',
                'UNCERTAIN: %s. These carry a reconstruction or an assumption, '
                'not a recorded fact.' % ', '.join(uncertain),
                '  Rule the level once and log it — '
                '`light.py anchor <source> --fuel N --why "..."` — and the '
                'hedging goes away for good.']
    return '\n'.join(out)


# The asset ids in campaign/assets.tsv that this module prices, and the rules
# table heading each one burns under.
_ASSET_FUEL = {'torch': 'Torch', 'oil_flask': 'Lantern (hooded)'}
_ASSET_UNPRICED = ('candle', 'lantern', 'tinder_box')


def reserves(cat=None, path=None, inv_state=None, pool=None):
    """Unburnt fuel the party is CARRYING, priced off the rules table.

    *** THE OIL FLASK COUNT COMES FROM THE OIL POOL, NOT FROM AN INVENTORY
    CELL. *** It used to come from the old campaign inventory file, so the fact
    lived in two files -- and they drifted apart TWICE, both times caught only
    by the disagreement warning this function used to feed. `light.tsv` knows
    which flasks have been broached, so `sealed` is DERIVED there and there is
    now nothing left to disagree with.

    Everything else comes from campaign/inventory_log.tsv via tools/inventory.py.
    Items the rules table does not price (candles, the spare lantern, the tinder
    box) are returned separately rather than counted as nothing.
    """
    import inventory as invmod
    cat = cat if cat is not None else catalogue()
    st = inv_state if inv_state is not None else invmod.state()
    pool = pool if pool is not None else oil_state()
    priced, unpriced = [], []

    n = pool['sealed'] if pool.get('known') else 0
    entry = cat['Lantern (hooded)']
    priced.append(dict(item='oil flask', qty=n, what='Lantern (hooded)',
                       each_rounds=entry['burn_rounds'],
                       rounds=n * (entry['burn_rounds'] or 0),
                       text=entry['text']))

    for asset, what in sorted(_ASSET_FUEL.items()):
        if asset == 'oil_flask':
            continue
        n = sum(v[0] for v in st.get(asset, {}).values())
        entry = cat[what]
        priced.append(dict(item=asset, qty=int(n), what=what,
                           each_rounds=entry['burn_rounds'],
                           rounds=int(n) * (entry['burn_rounds'] or 0),
                           text=entry['text']))
    for asset in _ASSET_UNPRICED:
        # inventory.state() is keyed (condition, unit) since 2026-09-14 -- the
        # unit had to join the key or an anchor in one unit wiped another.
        for (cond, _unit), v in sorted(st.get(asset, {}).items()):
            if v[0]:
                unpriced.append(('%s%s' % (asset, (' (%s)' % cond) if cond
                                           else ''), '%g' % v[0]))
    return priced, unpriced


def oil_report(pool, cat=None, inventory=None):
    """The oil supply in words, and a cross-check against the inventory."""
    cat = cat if cat is not None else catalogue()
    cap = cat['Lantern (hooded)']['burn_rounds']
    out = []
    if not pool['known']:
        out.append('OIL SUPPLY NOT TRACKED. %.1f turns have been drawn into '
                   'lamps with no pool to draw them from.'
                   % turns(pool['drawn']))
        out.append('  Log `light.py oil <id> --fuel <flasks>` to start '
                   'counting. Until then NOTHING records the flasks -- the '
                   'inventory cell that used to is retired -- and a top-up '
                   'silently costs a whole flask.')
        return '\n'.join(out)
    held = pool['sealed'] * cap + pool['broached']
    out.append('oil: %d sealed flask(s)%s  = %.1f turns'
               % (pool['sealed'],
                  ('  + 1 BROACHED with %.1f turns' % turns(pool['broached']))
                  if pool['broached'] > 1e-9 else '',
                  turns(held)))
    out.append('  %d flask(s) opened so far; %.1f turns poured into lamps'
               % (pool['opened'], turns(pool['drawn'])))
    if pool['untracked'] > 1e-9:
        out.append('  (%.1f turns were drawn BEFORE tracking began and are '
                   'not debited against the pool)' % turns(pool['untracked']))
    if pool['short'] > 1e-9:
        out.append('  *** RAN DRY: %.1f turns could not be supplied. A lamp '
                   'was filled short, not full.' % turns(pool['short']))
    # The disagreement warning that used to live here is GONE, and its absence
    # is the point: the flask count had two homes -- this log and an
    # inventory cell -- and they drifted apart twice. `reserves()` now takes
    # the count from this pool, so there is nothing left to disagree with.
    return '\n'.join(out)


def total(src, at_round, cat=None, inventory=None, pool=None):
    """The answer to "how many turns of light have we got left, all in?"."""
    cat = cat if cat is not None else catalogue()
    in_hand = sum(s['fuel'] for s in src.values()
                  if not s['gone'] and not s['infinite'] and s['fuel'])
    unknown = [sid for sid, s in sorted(src.items())
               if not s['gone'] and not s['infinite'] and s['fuel'] is None]
    priced, unpriced = reserves(cat, inventory)
    carried = sum(p['rounds'] for p in priced)
    # A TRACKED pool beats the hand-kept flask count, and replaces the oil part
    # of it rather than adding to it -- otherwise the broached flask is counted
    # twice, which is the bug this whole mechanism exists to kill.
    if pool is not None and pool['known']:
        cap = cat['Lantern (hooded)']['burn_rounds']
        carried -= sum(p['rounds'] for p in priced if 'oil' in p['item'].lower())
        carried += pool['sealed'] * cap + pool['broached']
    return dict(in_sources=in_hand, reserves=carried,
                grand=in_hand + carried, unknown=unknown,
                priced=priced, unpriced=unpriced, pool=pool)


def remaining_report(src, at_round, cat=None, inventory=None, pool=None):
    t = total(src, at_round, cat, inventory, pool)
    out = ['round %d' % at_round, '']
    out.append('in the lamps and torches in hand   %8.1f turns'
               % turns(t['in_sources']))
    for p in t['priced']:
        out.append('  %-22s %3d x %4.1f turns  %8.1f turns'
                   % (p['item'], p['qty'], turns(p['each_rounds']),
                      turns(p['rounds'])))
    out.append('carried in reserve                 %8.1f turns'
               % turns(t['reserves']))
    if pool is not None:
        out += ['', oil_report(pool, cat, inventory)]
    out.append('%s' % ('-' * 52))
    out.append('TOTAL, of what can be counted      %8.1f turns  (%.1f hours '
               'of dungeon time)'
               % (turns(t['grand']), turns(t['grand']) / 6.0))
    if t['unknown']:
        out += ['',
                'NOT COUNTED — fuel unknown in: %s' % ', '.join(t['unknown']),
                '  Up to %.1f turns each could be sitting in those, or none. '
                'The total above is a FLOOR, not the answer.'
                % turns(cat['Lantern (hooded)']['burn_rounds'])]
    if t['unpriced']:
        out += ['',
                'NOT PRICED — rules/exploration.md has no burn time for: %s'
                % ', '.join('%s (%s)' % (i, q) for i, q in t['unpriced'])]
    return '\n'.join(out)


# ------------------------------------------------------------ CLI

def build_parser():
    p = argparse.ArgumentParser(
        prog='light.py',
        description='Light-source fuel, computed from campaign/light.tsv.',
        epilog='Burn times come from rules/exploration.md via tools/rules.py; '
               'none is written here. Hooding does NOT stop the burn — log '
               '`out` before a rest.')
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--clock-file', default=None,
                   help='the dungeon clock fuel is charged against')
    p.add_argument('--at-round', type=int, default=None,
                   help='report as of this round instead of the clock')
    p.add_argument('--log', action='store_true', help='every row in game order')
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('show', help='the state of every light source (default)')
    sub.add_parser('remaining', help='how many turns of light the party has')
    sub.add_parser('sources', help='the rules table, as parsed')
    sub.add_parser('oilstate', help="the party's oil pool: sealed "
                                    'flasks and the broached one')

    for kind, helptext in (
            ('new', 'a source enters play, fuel full'),
            ('lit', 'it is burning'),
            ('hooded', 'shutter closed — STILL BURNING'),
            ('unhooded', 'shutter open — also still burning'),
            ('out', 'extinguished; this is what stops the fuel clock'),
            ('refill', 'a fresh pint of oil. Raises on a torch'),
            ('spent', 'fuel written down to nothing by hand'),
            ('lost', 'dropped, left behind, or taken away'),
            ('anchor', 'set fuel outright; supersedes everything above'),
            ('oil', 'flasks ADDED to the party\'s oil pool; --fuel is a '
                    'FLASK COUNT, negative for loss'),
            ('draw', 'oil used for something OTHER than filling a lamp -- '
                     'oiling hinges, a soaked rag. --fuel is in TURNS')):
        s = sub.add_parser(kind, help=helptext)
        s.add_argument('source', help='the id, e.g. lantern-torsat, torch-3')
        s.add_argument('--what', default='',
                       help='the row in rules/exploration.md it is priced '
                            'from, e.g. "lantern" or "torch". Required the '
                            'first time a source is seen')
        s.add_argument('--who', default='', help='who is carrying it')
        s.add_argument('--fuel', default='',
                       help='TURNS, on new/anchor/refill. Blank means full; '
                            '"?" means UNKNOWN and is reported as unknown')
        s.add_argument('--exped', default='')
        s.add_argument('--round', '--turn', dest='round', default='',
                       help='the clock round. Defaults to the current one. '
                            '(--turn is accepted as an alias, because the '
                            'other campaign logs spell it that way and their '
                            'values are rounds too)')
        s.add_argument('--note', '--why', dest='note', default='')
        s.add_argument('--certainty', choices=('known', 'uncertain'),
                       default='known')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    cat = catalogue()
    exped, rnd = now(a.clock_file)
    at = a.at_round if a.at_round is not None else rnd

    if a.cmd in KINDS:
        what = ''
        rows = load(a.log_file)
        # An `oil` row is about the party's SUPPLY, not a light source: it has
        # no burn time, so it needs no `what` and prices off nothing.
        if a.cmd in ('oil', 'draw'):
            row = dict(when=today(), exped=a.exped or (exped or ''),
                       round=a.round or at, source=a.source, kind=a.cmd,
                       what='', who=a.who, fuel=a.fuel,
                       certainty=a.certainty, note=a.note)
            if not (a.fuel or '').strip():
                print('REFUSED: --fuel must give the number of %s'
                      % ('FLASKS (negative to record loss)' if a.cmd == 'oil'
                         else 'TURNS of oil used'))
                return 1
            append(a.log_file, row)
            print(oil_report(oil_state(None, at_round=at, cat=cat,
                                       path=a.log_file), cat))
            return 0
        if a.what:
            what = resolve(a.what, cat)
        elif a.source not in what_of(rows, cat):
            print('REFUSED: %r is new, so --what must say which line of '
                  'rules/exploration.md prices it (%s)'
                  % (a.source, ', '.join(sorted(cat))))
            return 1
        row = dict(when=today(), exped=a.exped or (exped or ''),
                   round=a.round or at, source=a.source, kind=a.cmd,
                   what=what, who=a.who, fuel=a.fuel,
                   certainty=a.certainty, note=a.note)
        # Replay the log WITH the new row before writing it. A refill on a
        # torch has to be refused at the table, not discovered later by a
        # report that raises -- by then the row is in an append-only file and
        # can only be undone by another row.
        try:
            state(rows + [row], at_round=at, cat=cat)
        except (ValueError, KeyError) as e:
            print('REFUSED: %s' % e)
            return 1
        append(a.log_file, row)
        src, pool = _replay(None, at_round=at, cat=cat, path=a.log_file)
        if a.cmd in ('refill', 'new'):
            print(oil_report(pool, cat))
        word, fuel, gutter, warn = describe(src[a.source], at)
        print('%s %s at round %s — %s, %s, gutters %s'
              % (a.source, a.cmd, row['round'], word, fuel, gutter))
        if warn:
            print('  *** %s' % warn)
        return 0

    if a.cmd == 'sources':
        t = rules.find(TABLE)
        print('%-22s %-8s %-10s %-12s %s'
              % ('source', 'radius', 'burn', 'refillable', 'as printed'))
        for k in sorted(cat):
            e = cat[k]
            print('%-22s %-8s %-10s %-12s %s'
                  % (k, e['radius'],
                     'infinite' if e['infinite'] else '%d turns' % e['burn_turns'],
                     'yes' if e['refillable'] else 'no', e['text']))
        print()
        print(t['source'] or '(no source line -- treat as unverified)')
        return 0

    rows = load(a.log_file)
    if a.log:
        for r in rows:
            print('exp %-3s round %-6s %-16s %-9s %-6s %s'
                  % (r.get('exped', ''), r.get('round', ''),
                     r.get('source', ''), r.get('kind', ''),
                     r.get('fuel', ''), r.get('note', '')))
        print()
    src, pool = _replay(rows, at_round=at, cat=cat)

    if a.cmd == 'remaining':
        print(remaining_report(src, at, cat, pool=pool))
        return 0
    if a.cmd == 'oilstate':
        print(oil_report(pool, cat))
        return 0
    print(report(src, at))
    return 0


if __name__ == '__main__':
    sys.exit(main())
