#!/usr/bin/env python3
"""The dungeon clock and the wandering-monster checks that hang off it.

    python tools/clock.py start --exped 4
    python tools/clock.py advance --rounds 10 --why "moved 90 ft, mapping"
    python tools/clock.py status
    python tools/clock.py extra --why "hammering spikes"
    python tools/clock.py cost --action search        # what an action costs

This state used to live only in the DM's head, which meant a cleared context
lost the round count, the anchor positions and the pre-rolled jitter all at
once. It is a file now.

THE PROCEDURE (rules/exploration.md, adopted 2026-08-18)
--------------------------------------------------------
Time is tracked in ROUNDS; 10 rounds is a turn. Checks anchor at every multiple
of 30 rounds and each fires at its anchor **+ (1d6 - 1)**, so the average
spacing is exactly the module's rate while the moment is unpredictable.

**THE INTERVAL WAS 20 AND THAT WAS WRONG.** B1 p.4: *"Every third turn of
adventuring, the DM should take a die roll for the possible appearance of
wandering monsters."* Every THIRD turn is 30 rounds, not two turns and not 20.
The old value ran the whole campaign at 1.5x the module's encounter rate --
about one encounter every 2 hours of dungeon time instead of every 3. Found
2026-08-30 when the player asked why two encounters had come back to back;
corrected against a 200 dpi render of the page. Per the standing precedent,
encounters already generated STAND and the procedure is fixed going forward.

**The jitter is rolled in advance and kept hidden.** `start` rolls the whole
series up front and writes it to the log, because rolling it lazily at each
anchor is the same thing as not rolling it in advance.

**THE CHECKS THEMSELVES ARE QUIET.** Every check, its jitter, its d6 and its
result go to `campaign/clock.tsv`; nothing reaches the table unless a monster
actually turns up. Asked for by the player 2026-08-26 -- announcing "the
round-40 check fired, d6 = 6, nothing" tells them the corridor is safe for the
next twenty rounds, which is information their characters do not have. A silent
check that comes up empty is indistinguishable from no check at all, which is
the point. Pass `--show-checks` to audit them, and the log always has every one.

This is a deliberate exception to the campaign's roll-in-the-open rule; it does
not extend to anything else. Combat, saves, morale and searches stay open.

**The die says WHAT, never WHERE.** If the rolled creature could not physically
have reached the party -- a sealed room, a corridor they have bottled -- relocate
it to a plausible approach or void it. Verify with:

    python mapdb/dmap.py at mapdb/output/b1/b1.sqlite 1 <x> <y>

Never invent geography to justify a roll.
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dice import roll                                           # noqa: E402
from tsvlog import append, read_tsv, today                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'clock.tsv')
TABLES = os.path.join(ROOT, 'modules', 'private', 'b1_wandering.tsv')

ANCHOR = 30            # B1 p.4: a check every THIRD turn. See the header.
CHANCE_IN_6 = 1        # 1 in 6
HORIZON = 60           # anchors pre-rolled at the start of an expedition

# What actions cost, from rules/exploration.md. Kept here as a convenience
# lookup only; the table in the markdown is the source.
# THREE speeds, not two (PHB p.102). The middle one was missing until
# 2026-08-27 and known-route movement was run 4-5x too slow for a whole
# expedition. For a 9" party: 90 ft per turn exploring, per 2 rounds on a known
# route, per round fleeing or in combat.
COSTS = {
    'explore90': (10, 'move 90 ft at 9", exploring and MAPPING (1" = 10 ft/turn)'),
    'known90': (2, 'move 90 ft at 9" on a KNOWN route — 5x faster, PHB p.102'),
    'flee90': (1, 'move 90 ft at 9" fleeing or in combat — 10x faster'),
    'move90': (10, 'deprecated alias for explore90'),
    'search': (10, 'search a 10x10 area'),
    'listen': (1, 'listen at a door'),
    'door': (1, 'open, force or spike a door'),
    'lock': (1, 'pick a lock'),
    'combat': (1, 'one round of combat'),
    'oil': (5, 'oiling hinges and letting it soak'),
    'loot': (3, 'looting bodies / recovering ammunition (2-5)'),
}


def load(path=None):
    return read_tsv(path or LOG, missing_ok=True)


def state(rows=None):
    """(exped, round, {anchor: jitter}, {anchors already fired})."""
    rows = load() if rows is None else rows
    exped, rnd, jitter, fired = None, 0, {}, set()
    for r in rows:
        kind = r.get('kind', '')
        if kind == 'start':
            exped, rnd, jitter, fired = r.get('exped'), 0, {}, set()
            continue
        if kind == 'jitter':
            for pair in (r.get('detail') or '').split(','):
                if ':' in pair:
                    a, _, j = pair.partition(':')
                    try:
                        jitter[int(a)] = int(j)
                    except ValueError:
                        pass
            continue
        # A `correct` row SETS the round outright, and is the ONLY thing that
        # may move it backwards. Same shape as the day-39 XP anchor and the
        # money anchor: the past is fixed by APPENDING a row that overrides,
        # never by rewriting one. It exists because on 2026-09-13 the DM
        # charged a round for a step through a wall that is not on the printed
        # map, appended `advance --rounds -1` to give it back, and the tool
        # silently ignored it -- max() below saw a smaller number and kept the
        # larger one. A log row that says one thing while the tool does another
        # is the exact failure this repo is built against, so the honest fix
        # was to give the clock a way to be corrected rather than to leave a
        # dead row in the log.
        if kind == 'correct':
            try:
                rnd = int(r.get('round'))
            except (TypeError, ValueError):
                pass
            continue
        # Otherwise the round counter only ever moves FORWARD within an
        # expedition, so take the maximum rather than the last value written. A
        # check fires partway through an advance and is logged at the round it
        # fired -- round 21 inside a move that ended at 23 -- and because it is
        # written last, reading the last value silently rewound the clock two
        # rounds.
        try:
            rnd = max(rnd, int(r.get('round') or rnd))
        except ValueError:
            pass
        if kind == 'check':
            try:
                fired.add(int(r.get('anchor') or 0))
            except ValueError:
                pass
    return exped, rnd, jitter, fired


def encounter_table(level=1, path=None):
    rows = read_tsv(path or TABLES, missing_ok=True)
    return {int(r['roll']): r['entry'] for r in rows
            if str(r.get('level')) == str(level)}


def check_due(rnd_from, rnd_to, jitter, fired):
    """Anchors whose check falls in (rnd_from, rnd_to] and has not yet fired."""
    due = []
    for anchor, j in sorted(jitter.items()):
        if anchor in fired:
            continue
        at = anchor + j
        if rnd_from < at <= rnd_to:
            due.append((anchor, j, at))
    return due


def fire_check(anchor, jitter_val, at, level, exped, rng=random, log_file=None):
    """Roll one wandering check. Returns (lines, encountered_entry_or_None).

    `anchor` is normally the round number the check hangs off, but `extra`
    passes the literal string 'extra' for a noise-triggered check outside the
    schedule -- so it is formatted as text, not as a number. It was formatted
    with %d and every extra check crashed.
    """
    if isinstance(anchor, int):
        head = ('--- wandering check: anchor %d fired at round %d (jitter +%d) ---'
                % (anchor, at, jitter_val))
    else:
        head = '--- EXTRA wandering check (%s) at round %d ---' % (anchor, at)
    lines = [head]
    d = roll('d6', reason='wandering check, anchor %s' % anchor, rng=rng)
    lines.append('    d6 = %d   (%d in 6 means an encounter)' % (d.total, CHANCE_IN_6))
    entry = None
    if d.total <= CHANCE_IN_6:
        t = encounter_table(level)
        if not t:
            lines.append('    ENCOUNTER, but no table for level %d -- see '
                         'modules/private/b1_wandering.tsv' % level)
        else:
            e = roll('d6', reason='wandering table, level %d' % level, rng=rng)
            entry = t.get(e.total, '(no entry %d)' % e.total)
            lines.append('    d6 = %d on the level %d table' % (e.total, level))
            lines.append('    -> %s' % entry)
            lines.append('    RESOLVE IT AT ROUND %d, WHERE THE PARTY IS NOW.'
                         % at)
            lines.append('    Do NOT bank it for later. If it cannot reach them')
            lines.append('    at this round, the check is SPENT and they never')
            lines.append('    knew it was there. Parking a monster in a corridor')
            lines.append('    for the party to walk into converts one check into')
            lines.append('    an encounter at a time of the DM\'s choosing, and')
            lines.append('    lands it next to the following check.')
            lines.append('    THE DIE SAYS WHAT, NOT WHERE. Verify an approach '
                         'exists:')
            lines.append('       python mapdb/dmap.py at '
                         'mapdb/output/b1/b1.sqlite %d <x> <y>' % level)
    else:
        lines.append('    no encounter')
    append(log_file or LOG, dict(when=today(), exped=exped, round=at,
                                 kind='check', anchor=anchor,
                                 detail='d6=%d%s' % (d.total,
                                                     ' -> ' + entry if entry else ''),
                                 note=('anchor %d + %d' % (anchor, jitter_val)
                                       if isinstance(anchor, int) else str(anchor))))
    return lines, entry


def build_parser():
    p = argparse.ArgumentParser(
        prog='clock.py',
        description='Dungeon time and wandering-monster checks.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--log-file', default=LOG)
    p.add_argument('--level', type=int, default=1, help='dungeon level')
    sub = p.add_subparsers(dest='cmd', required=True)

    ra = sub.add_parser('reanchor', help='retire every FUTURE anchor and roll a '
                                        'fresh hidden series at the current '
                                        'ANCHOR interval')
    ra.add_argument('--why', required=True,
                    help='why the schedule is being changed. Required -- a '
                         'silently re-rolled wandering schedule is exactly the '
                         'thing this tool exists to prevent')

    ex = sub.add_parser('extend', help='pre-roll more jitter anchors; the '
                                      'clock REFUSES to advance past the last one')
    ex.add_argument('--to', type=int, required=True,
                    help='extend the schedule to at least this round')

    st = sub.add_parser('start', help='begin an expedition and pre-roll the jitter')
    st.add_argument('--exped', required=True)
    st.add_argument('--note', default='entered the dungeon')

    ad = sub.add_parser('advance', help='advance the clock and fire any checks due')
    ad.add_argument('--rounds', type=int, help='rounds elapsed')
    ad.add_argument('--action', choices=sorted(COSTS),
                    help='use the standard cost of an action instead')
    ad.add_argument('--why', default='')
    ad.add_argument('--show-checks', action='store_true',
                    help='print every check, including the empty ones. Off by '
                         'default: an empty check announced at the table tells '
                         'the player the next twenty rounds are safe, which '
                         'their characters do not know. The log has them all.')

    co = sub.add_parser('correct', help='SET the round outright -- the only '
                                       'thing that may move the clock back')
    co.add_argument('--to', type=int, required=True, help='the true round')
    co.add_argument('--why', required=True,
                    help='what was charged that did not happen, or what was '
                         'not charged that did. Required: an unexplained jump '
                         'in the clock is indistinguishable from a bug')

    sub.add_parser('status', help='where the clock stands')

    ex = sub.add_parser('extra', help='one extra check for a genuinely loud event')
    ex.add_argument('--why', required=True)
    ex.add_argument('--show-checks', action='store_true',
                    help='print it even when nothing turns up')

    rs = sub.add_parser('rest', help='camp in the dungeon for several hours')
    rs.add_argument('--hours', type=float, required=True)
    rs.add_argument('--checks', type=int, default=3,
                    help='wandering checks for the whole rest. rules/exploration.md: '
                         'THREE per night if the party camps inside — not the '
                         'normal one-per-twenty-rounds schedule')
    rs.add_argument('--why', default='resting')
    rs.add_argument('--show-checks', action='store_true')

    co = sub.add_parser('cost', help='what a standard action costs in rounds')
    co.add_argument('--action', choices=sorted(COSTS))
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    rows = load(a.log_file)
    exped, rnd, jitter, fired = state(rows)

    if a.cmd == 'cost':
        if a.action:
            n, why = COSTS[a.action]
            print('%s: %d round(s)' % (why, n))
        else:
            for k in sorted(COSTS):
                print('%-9s %2d  %s' % (k, COSTS[k][0], COSTS[k][1]))
        return 0

    if a.cmd == 'start':
        append(a.log_file, dict(when=today(), exped=a.exped, round=0,
                                kind='start', anchor='', detail='',
                                note=a.note))
        # Pre-roll the whole series now. Rolling it lazily at each anchor is
        # the same as not rolling it in advance, and the point of the jitter is
        # that it is fixed before the party's choices can interact with it.
        pairs = []
        for k in range(1, HORIZON + 1):
            j = roll('d6', reason='wandering jitter, anchor %d' % (k * ANCHOR),
                     hidden=True).total - 1
            pairs.append('%d:%d' % (k * ANCHOR, j))
        append(a.log_file, dict(when=today(), exped=a.exped, round=0,
                                kind='jitter', anchor='',
                                detail=','.join(pairs),
                                note='rolled in advance and HIDDEN; each is '
                                     'reported when its check fires'))
        print('expedition %s started at round 0.' % a.exped)
        print('%d anchors pre-rolled (to round %d). The jitter is in the log '
              'and stays unreported until each check fires.'
              % (HORIZON, HORIZON * ANCHOR))
        return 0

    if a.cmd == 'status':
        if exped is None:
            print('no expedition started; run `clock.py start --exped N`')
            return 0
        nxt = [(k + j) for k, j in sorted(jitter.items())
               if k not in fired and k + j > rnd]
        print('expedition %s   round %d   (turn %d, %d rounds into it)'
              % (exped, rnd, rnd // 10 + 1, rnd % 10))
        print('checks fired: %d' % len(fired))
        if nxt:
            print('next check falls between round %d and %d -- the exact round '
                  'is in the log and stays hidden until it fires'
                  % (((rnd // ANCHOR) + 1) * ANCHOR,
                     ((rnd // ANCHOR) + 1) * ANCHOR + 5))
        return 0

    if a.cmd == 'extra':
        # The module sanctions extra checks for genuinely loud events. ONE
        # extra, not one per action -- an audit once found checks being rolled
        # at 2-5x the correct rate.
        lines, entry = fire_check('extra', 0, rnd, a.level, exped,
                                  log_file=a.log_file)
        # Quiet unless something turns up, exactly like a scheduled check.
        if entry or a.show_checks:
            print('extra check: %s' % a.why)
            print('\n'.join(lines))
        if entry:
            print()
            print('*** WANDERING MONSTER -- resolve it before narrating on ***')
        return 0

    if a.cmd == 'rest':
        if exped is None:
            print('no expedition started')
            return 1
        # A long rest is NOT the normal schedule. Firing every scheduled anchor
        # across eight hours would be 24 checks; the module gives three per
        # night camped inside. So the intervening anchors are marked fired
        # without rolling, and exactly --checks are rolled instead, spread
        # across the rest.
        rounds = int(a.hours * 60)
        new = rnd + rounds
        append(a.log_file, dict(when=today(), exped=exped, round=new,
                                kind='advance', anchor='', detail=str(rounds),
                                note='REST %.1f h — %s' % (a.hours, a.why)))
        skipped = [k for k in sorted(jitter)
                   if k not in fired and rnd < k + jitter[k] <= new]
        for k in skipped:
            append(a.log_file, dict(
                when=today(), exped=exped, round=k + jitter[k], kind='check',
                anchor=k, detail='not rolled',
                note='inside a long rest; the module gives %d checks per night '
                     'instead of the normal schedule' % a.checks))
        out, encountered = [], False
        for i in range(max(0, a.checks)):
            at = rnd + int(rounds * (i + 1) / (a.checks + 1))
            lines, entry = fire_check('rest watch %d' % (i + 1), 0, at,
                                      a.level, exped, log_file=a.log_file)
            if entry:
                encountered = True
            if entry or a.show_checks:
                out += lines
        print('rested %.1f hours: round %d -> %d   (%s)'
              % (a.hours, rnd, new, a.why))
        print('%d scheduled anchor(s) inside the rest were NOT rolled; '
              '%d rest checks rolled instead' % (len(skipped), a.checks))
        if out:
            print()
            print('\n'.join(out))
        if encountered:
            print()
            print('*** SOMETHING FOUND THE CAMP -- resolve it ***')
        return 0

    if a.cmd == 'reanchor':
        # CHANGING THE INTERVAL IS NOT JUST CHANGING ANCHOR.
        #
        # The jitter series lives in the LOG, not in the code -- `check_due`
        # walks whatever anchors have been written. So editing ANCHOR alone
        # leaves the old, wrongly-spaced anchors in place and they go on firing
        # forever. They have to be retired explicitly, and the replacements
        # rolled in advance and hidden like any other jitter.
        #
        # Retiring is done by writing a `check` row for each stale anchor, which
        # puts it in `fired` and takes it permanently out of play. Nothing is
        # deleted; the log stays append-only and the whole change is auditable.
        if exped is None:
            print('no expedition started')
            return 1
        horizon = max(jitter) if jitter else 0
        stale = [k for k in sorted(jitter) if k not in fired and k + jitter[k] > rnd]
        for k in stale:
            append(a.log_file, dict(
                when=today(), exped=exped, round=rnd, kind='check', anchor=k,
                detail='not rolled',
                note='RETIRED unfired at round %d, interval changed to %d: %s'
                     % (rnd, ANCHOR, a.why)))
        first = ((rnd // ANCHOR) + 1) * ANCHOR
        pairs = []
        for anchor in range(first, horizon + ANCHOR, ANCHOR):
            j = roll('d6', reason='wandering jitter, anchor %d' % anchor,
                     hidden=True).total - 1
            pairs.append('%d:%d' % (anchor, j))
        if pairs:
            append(a.log_file, dict(when=today(), exped=exped, round=rnd,
                                    kind='jitter', anchor='',
                                    detail=','.join(pairs),
                                    note='RE-ANCHORED at interval %d; rolled in '
                                         'advance and HIDDEN. %s'
                                         % (ANCHOR, a.why)))
        print('retired %d unfired anchor(s) after round %d' % (len(stale), rnd))
        print('rolled %d new anchor(s) at interval %d, rounds %d..%d (hidden)'
              % (len(pairs), ANCHOR, first, horizon))
        print('reason logged: %s' % a.why)
        return 0

    if a.cmd == 'extend':
        if exped is None:
            print('no expedition started')
            return 1
        horizon = max(jitter) if jitter else 0
        target = ((a.to + ANCHOR - 1) // ANCHOR) * ANCHOR
        if target <= horizon:
            print('jitter already runs to round %d; nothing to do' % horizon)
            return 0
        pairs = []
        for anchor in range(horizon + ANCHOR, target + ANCHOR, ANCHOR):
            j = roll('d6', reason='wandering jitter, anchor %d' % anchor,
                     hidden=True).total - 1
            pairs.append('%d:%d' % (anchor, j))
        append(a.log_file, dict(when=today(), exped=exped, round=rnd,
                                kind='jitter', anchor='',
                                detail=','.join(pairs),
                                note='EXTENDED past the original horizon; '
                                     'rolled in advance and HIDDEN'))
        print('jitter extended from round %d to %d (%d new anchors, hidden).'
              % (horizon, target, len(pairs)))
        return 0

    if a.cmd == 'correct':
        if exped is None:
            print('no expedition started; run `clock.py start --exped N`')
            return 1
        append(a.log_file, dict(when=today(), exped=exped, round=a.to,
                                kind='correct', anchor='',
                                detail='%+d' % (a.to - rnd), note=a.why))
        print('round %d -> %d   CORRECTED   (%s)' % (rnd, a.to, a.why))
        # Deliberately fires no checks. A correction is a statement about what
        # the clock SHOULD have read, not time passing, and a correction that
        # rolled for wandering monsters would be inventing an encounter out of
        # a bookkeeping fix.
        return 0

    if a.cmd == 'advance':
        if exped is None:
            print('no expedition started; run `clock.py start --exped N`')
            return 1
        n = a.rounds if a.rounds is not None else (
            COSTS[a.action][0] if a.action else None)
        if n is None:
            print('give --rounds N or --action NAME')
            return 1
        why = a.why or (COSTS[a.action][1] if a.action else '')
        new = rnd + n

        # THE JITTER HAS A HORIZON AND RUNNING OFF THE END IS SILENT.
        #
        # `start` pre-rolls HORIZON anchors -- 60 * ANCHOR rounds. Past the
        # last anchor `check_due` simply finds nothing and returns an empty
        # list, so the clock keeps advancing and the wandering checks quietly
        # STOP. Expedition 4 ran from round 1200 to 1325 with no check at all
        # before anyone noticed, which is 6 free checks in the party's favour.
        #
        # A wandering clock that stops without saying so is worse than no
        # wandering clock, because the DM goes on believing it is running. So
        # refuse to advance past the horizon instead of coasting past it.
        horizon = max(jitter) if jitter else 0
        if new > horizon:
            print('REFUSED: the pre-rolled jitter ends at round %d and this '
                  'advance would reach %d.' % (horizon, new))
            print('  Past the last anchor NO WANDERING CHECKS FIRE, silently.')
            print('  Extend it first:  python tools/clock.py extend --to %d'
                  % (((new // ANCHOR) + 4) * ANCHOR))
            return 1
        append(a.log_file, dict(when=today(), exped=exped, round=new,
                                kind='advance', anchor='', detail=str(n),
                                note=why))
        print('round %d -> %d   (%s)' % (rnd, new, why or '%d rounds' % n))
        # Checks are QUIET unless something turns up. Every one is written to
        # campaign/clock.tsv either way -- see the module docstring.
        out, encountered = [], False
        for anchor, j, at in check_due(rnd, new, jitter, fired):
            lines, entry = fire_check(anchor, j, at, a.level, exped,
                                      log_file=a.log_file)
            if entry:
                encountered = True
            if entry or a.show_checks:
                out += lines
        if out:
            print()
            print('\n'.join(out))
        elif a.show_checks:
            print('no wandering check due.')
        if encountered:
            print()
            print('*** WANDERING MONSTER -- resolve it before narrating on ***')
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
