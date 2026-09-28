#!/usr/bin/env python3
"""WHO IS CARRYING WHAT, and what it does to their movement rate.

COMMANDS
    python tools/carry.py                       # (no subcommand) the whole
                                                  # manifest, per person, plus
                                                  # the shared-kit apportionment
    python tools/carry.py person Dave            # one person's load, gp-weight,
                                                  # and their encumbrance band
    python tools/carry.py roster                 # every person's kit, itemised
    python tools/carry.py pack [--target BAND]   # fill the strongest bearers
                                                  # first, up to BAND (default
                                                  # 'heavy'); reports what is
                                                  # left unpacked
    python tools/carry.py check                  # reconcile this manifest
                                                  # against what the party OWNS;
                                                  # exit 1 on any FAIL

Global options (before the subcommand):
    --log-file PATH   override campaign/carry.tsv (tests use this)
    --bearers "Dave,Ista,..."   who is actually on THIS trip. Shared `party`
                      kit is apportioned across these people, not the whole
                      roster. Applies to the default report, `person` and
                      `pack`; `check` and `roster` ignore it.

INPUT FILES (read-only -- this module has no write path of its own)
    campaign/carry.tsv           the manifest itself: who/what/verb/qty/unit
    campaign/characters.tsv      the six PCs plus henchmen, for `person` and
                                  Strength-based encumbrance allowances
    campaign/people.tsv          non-PC `who` ids (NPCs), for the closed
                                  who-vocabulary `check` enforces
    campaign/places.tsv          place `who` ids (Wethersby, Wend's barn, the
                                  basecamp, ...), same vocabulary
    campaign/inventory_log.tsv   what the party OWNS, via tools/inventory.py --
                                  `check` reconciles carried against this
    campaign/assets.tsv          asset identities, via tools/inventory.py
    campaign/world_changes.tsv   iron_spike's emplaced-in-doors count, via
                                  tools/world.py -- `check` subtracts it before
                                  comparing carried against owned
    rules/exploration.md         the Strength encumbrance-allowance table, via
                                  tools/rules.py

    A `FOREIGN` asset (oil_flask, coin, wool -- see tools/inventory.py's
    FOREIGN dict) is never reconciled against inventory_log.tsv here, because
    a DIFFERENT log owns its total (light.tsv, money.tsv, venture.tsv). A row
    naming one is a location note about part of that total, not a claim
    `check` verifies in full.

*** WHY THIS IS A SEPARATE LOG FROM inventory_log.tsv. ***

The player asked, on day 102, what data structure recorded per-person kit. There
wasn't one. It was the free-text `holder` column, one string per row, holding
things like "WORN: Dave, Torsat, Yrtone, Blartho" and "ONE EACH: Dave, Torsat,
Tristle, Frython, Hask, Ista -- 2 spare". Thirty-three distinct hand-typed
strings were in use, `--held-by Dave` was a substring match that returned the
group total, and the tidy per-person table the DM had presented was assembled BY
HAND out of that prose.

Adding `holder` to inventory's cell key was tried first. It fragmented the
ownership history -- inconsistent historical strings split every asset's running
total, and iron_spike computed to -13 for one string and +13 for another.

L052 had named both options on day 95: "Either inventory_log grows a notion of a
packed load, or the outfitting step starts producing a manifest." This is the
manifest, and the split is right on its merits: OWNERSHIP AND CARRIAGE ARE
DIFFERENT QUESTIONS. The party owns a kettle it is not carrying and carries
Ista's own hand axe it does not own.

WHAT THIS COMPUTES THAT NOTHING COULD BEFORE
--------------------------------------------
Per-person load in gp weight, against that person's own encumbrance bands --
because PHB p.101's bands are modified by the STRENGTH TABLE II allowance, which
differs by eleven hundred gp weight across this party. Dave carries 1,000 more
than Tristle before either notices.

*** AND IT APPORTIONS THE SHARED KIT, WHICH IS THE PART EVERY HAND-CALCULATION
GOT WRONG. *** `party` rows are real weight carried by real people; ignoring
them flatters every load, and the rope, rations, sacks and torches are most of
what the party is actually lifting.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import inventory as invmod                                       # noqa: E402
import rules as rulesmod                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, 'campaign', 'carry.tsv')
CHARS = os.path.join(ROOT, 'campaign', 'characters.tsv')
PEOPLE = os.path.join(ROOT, 'campaign', 'people.tsv')
PLACES = os.path.join(ROOT, 'campaign', 'places.tsv')
EXEMPT = os.path.join(ROOT, 'campaign', 'carry_exempt.tsv')

SHARED = 'party'


def characters():
    return {r['name']: r for r in read_tsv(CHARS)}


def non_pc_people():
    """{id: row} for people.tsv, EXCLUDING kind=pc -- those come from
    characters.tsv under their Title-Case `name` and stay there, so `Dave`
    (the character) and `dave` (the identity row) do not become two entries
    for one person."""
    return {r['id']: r for r in read_tsv(PEOPLE)
            if (r.get('kind') or '').strip() != 'pc'}


def places():
    return {r['id']: r for r in read_tsv(PLACES)}


def rows(path=None):
    return read_tsv(path or LOG)


def who_vocabulary():
    """The closed set: a character (by name), a place or person id, or `party`.

    *** EXTENDED DAY 103. *** carry.tsv started as WHO IS CARRYING WHAT, closed
    to the party's own characters. The player then asked for it to become the
    single "where is everything" log, which means it has to be able to say a
    thing is at Wend's barn or with Toller, not just in a character's hands.
    Extending the vocabulary rather than inventing a second closed list keeps
    the same guarantee: a free-typed holder is how this went wrong, so nothing
    outside `characters.tsv`, `people.tsv` (id) or `places.tsv` (id) is legal.
    """
    return set(characters()) | set(non_pc_people()) | set(places()) | {SHARED}


def standing_exempt(path=None):
    """{who} currently EXEMPT from the shared kit, from campaign/carry_exempt.tsv
    (append-only; the latest `exempt`/`resume` row per name wins)."""
    cur = {}
    for r in read_tsv(path or EXEMPT, missing_ok=True):
        who = (r.get('who') or '').strip()
        if who:
            cur[who] = (r.get('action') or '').strip().lower() == 'exempt'
    return {w for w, on in cur.items() if on}


def default_bearers(log=None):
    """Who shares the `party` kit when nobody has said otherwise: everyone
    carrying anything, minus the standing exemptions. None when nobody is
    exempt, which means "everyone", exactly as before."""
    ex = standing_exempt()
    if not ex:
        return None
    chars = characters()
    st = state(log)
    return [n for n in chars if n in st and n not in ex]


def state(log=None):
    """{who: {(asset, unit): qty}}. Anchors set outright; moves add."""
    out = {}
    for r in (log if log is not None else rows()):
        who = (r.get('who') or '').strip()
        asset = (r.get('asset') or '').strip()
        if not who or not asset:
            continue
        unit = (r.get('unit') or 'each').strip()
        try:
            q = float(r.get('qty') or 0)
        except ValueError:
            continue
        cell = out.setdefault(who, {})
        if (r.get('verb') or '').strip() == 'anchor':
            cell[(asset, unit)] = q
        else:
            cell[(asset, unit)] = cell.get((asset, unit), 0.0) + q
    return out


# --------------------------------------------------------------------------
# encumbrance
# --------------------------------------------------------------------------

def _table(heading):
    return rulesmod.find(heading)


def _allowance_table():
    """{STR spec: gp-weight allowance}, parsed from rules/exploration.md.

    *** THREE THINGS IN THIS TABLE BREAK A NAIVE PARSER AND ALL THREE DID. ***

    1. It is printed as TWO COLUMN-PAIRS WITH A BLANK SPACER between them,
       exactly as the PHB sets it -- "| 3 | -350 | | 14-15 | +200 |" -- so the
       right-hand pair is cells 3 and 4, not 2 and 3. Pairing by stride of two
       read the spacer as a key and returned +0 for every high Strength.
    2. THE MINUS SIGN IS U+2212, not an ASCII hyphen, and the ranges use an
       EN-DASH. A `[+-]` character class matches neither, so every penalty
       parsed as zero -- including STR 3's -350.
    3. Two values are the WORD "normal", one of them as "normal (no penalty)".

    The first version of this function returned +0 for STR 18/26 and for STR 3
    alike, which would have let Dave carry what Dellie carries.
    """
    import re
    txt = open(os.path.join(ROOT, 'rules', 'exploration.md'),
               encoding='utf-8').read()
    m = re.search(r'\| STR \| Weight allowance \|.*?\n\n', txt, re.S)
    if not m:
        raise ValueError('the Strength allowance table is not in '
                         'rules/exploration.md under its expected heading')
    table = {}
    for line in m.group(0).splitlines():
        if line.strip().startswith('|---'):
            continue
        cells = [c.strip().strip('*').strip()
                 for c in line.strip().strip('|').split('|')]
        cells = [c for c in cells if c]              # drop the spacer
        for i in range(0, len(cells) - 1, 2):
            key, val = cells[i], cells[i + 1]
            if not re.match(r'^\d', key):
                continue
            key = key.replace(' ', '').replace('\u2013', '-').replace('\u2014', '-')
            if 'normal' in val.lower():
                table[key] = 0
                continue
            mv = re.search(r'([+\u2212-])\s*([\d,]+)', val)
            if mv:
                sign = -1 if mv.group(1) in ('-', '\u2212') else 1
                table[key] = sign * int(mv.group(2).replace(',', ''))
    if not table:
        raise ValueError('parsed no rows out of the Strength allowance table')
    return table


def _allowance_lookup(score):
    return _match_band(str(score).strip(), _allowance_table())


def _match_band(score, table):
    import re
    if score in table:
        return table[score]
    # exceptional strength: "18/26" falls in the 18/01-50 band
    if '/' in score:
        base, pct = score.split('/', 1)
        try:
            pct = int(pct)
        except ValueError:
            pct = 0
        for key, val in table.items():
            mm = re.match(r'^18/(\d+)[-–](\d+)$', key)
            if mm and int(mm.group(1)) <= pct <= int(mm.group(2)):
                return val
        return table.get('18', 0)
    try:
        n = int(score)
    except ValueError:
        return 0
    for key, val in table.items():
        mm = re.match(r'^(\d+)[-–](\d+)$', key)
        if mm and int(mm.group(1)) <= n <= int(mm.group(2)):
            return val
    return table.get(score, 0)


# PHB pp.101-102 bands, in gp weight, BEFORE the Strength allowance is added.
BANDS = (('normal', 350, '12"'),
         ('heavy', 700, '9"'),
         ('very heavy', 1050, '6"'),
         ('encumbered', None, '3"-4"'))


def band_for(gp, allowance):
    """(band name, movement) for a load, with the allowance added to each band."""
    for name, ceiling, move in BANDS:
        if ceiling is None or gp <= ceiling + allowance:
            return name, move
    return BANDS[-1][0], BANDS[-1][2]


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def person_load(name, log=None, share=None):
    """(gp carried, [(asset, qty, unit, gp, why)], shared gp apportioned)."""
    st = state(log)
    ass = invmod.ledgermod.assets()
    lines, tot = [], 0.0
    for (asset, unit), qty in sorted(st.get(name, {}).items()):
        if not qty:
            continue
        gp, why = invmod.gp_weight(asset, qty, ass)
        if gp:
            tot += gp
        lines.append((asset, qty, unit, gp, why))
    return tot, lines, (share or 0.0)


def shared_total(log=None):
    """(gp, [(asset, qty, unit, gp, why)]) for the `party` rows."""
    st = state(log)
    ass = invmod.ledgermod.assets()
    lines, tot = [], 0.0
    for (asset, unit), qty in sorted(st.get(SHARED, {}).items()):
        if not qty:
            continue
        gp, why = invmod.gp_weight(asset, qty, ass)
        if gp:
            tot += gp
        lines.append((asset, qty, unit, gp, why))
    return tot, lines


def report(log=None, bearers=None):
    """The whole manifest, per person, with bands.

    `bearers` is who is actually on the trip, and it matters: the shared kit is
    divided among THEM, not among everybody on the roster. Ten people sharing
    the rope carry less each than seven do.
    """
    chars = characters()
    st = state(log)
    people = [n for n in chars if n in st or n in (bearers or [])]
    bearers = bearers or people
    shared_gp, shared_lines = shared_total(log)
    per_head = shared_gp / len(bearers) if bearers else 0.0

    out = []
    out.append('SHARED KIT -- carried by somebody, bearer not tracked')
    for asset, qty, unit, gp, why in sorted(shared_lines,
                                            key=lambda r: -(r[3] or 0)):
        out.append('   %-18s %8s %-12s %8s %7s  %s'
                   % (asset, invmod._fmt(qty), unit,
                      ('%.0f' % gp) if gp is not None else '?',
                      ('%.1f' % (gp / 10)) if gp is not None else '?', why))
    out.append('   %-18s %38s %7.1f lb' % ('TOTAL SHARED',
                                           '%.0f gp-wt' % shared_gp,
                                           shared_gp / 10))
    out.append('   divided among %d bearers = %.0f gp-wt (%.1f lb) each'
               % (len(bearers), per_head, per_head / 10))
    out.append('')
    out.append('%-9s %8s %8s %9s %9s %-11s %s'
               % ('', 'own', '+share', 'TOTAL', 'allowance', 'band', 'move'))
    grand = 0.0
    for name in sorted(people, key=lambda n: -person_load(n, log)[0]):
        own, lines, _ = person_load(name, log)
        share = per_head if name in bearers else 0.0
        total = own + share
        grand += own
        alw = _allowance_lookup(chars[name].get('str', '') or '0')
        bname, move = band_for(total, alw)
        out.append('%-9s %8.0f %8.0f %9.0f %+9d %-11s %s'
                   % (name, own, share, total, alw, bname, move))
    out.append('')
    out.append('   personal kit %.0f gp-wt + shared %.0f = %.0f gp-wt, %.0f lb'
               % (grand, shared_gp, grand + shared_gp,
                  (grand + shared_gp) / 10))
    out.append('   columns are GP WEIGHT, ten to the pound (DMG Appendix O)')
    return '\n'.join(out)


def roster(log=None, bearers=None):
    """Every person's kit, itemised, with their band. THE DESCRIPTIVE LIST.

    A standing script rather than something typed out once, because a pasted
    list is stale the instant a lantern changes hands -- which is exactly what
    happened on day 103, one message after the list was given.
    """
    chars = characters()
    st = state(log)
    people = [n for n in chars if n in st or n in (bearers or [])]
    order = sorted(people, key=lambda n: -person_load(n, log)[0])
    shared_gp, _ = shared_total(log)
    bearers = bearers or people
    per_head = shared_gp / len(bearers) if bearers else 0.0
    ass = invmod.ledgermod.assets()

    out = []
    for name in order:
        own, lines, _ = person_load(name, log)
        share = per_head if name in bearers else 0.0
        total = own + share
        alw = _allowance_lookup(chars[name].get('str', '') or '0')
        bname, move = band_for(total, alw)
        out.append('%s -- STR %s, allowance %+d, AC %s'
                   % (name, chars[name].get('str', '?'), alw,
                      chars[name].get('ac', '?')))
        for asset, qty, unit, gp, why in sorted(lines,
                                                key=lambda r: -(r[3] or 0)):
            nm = (ass.get(asset) or {}).get('name', asset)
            out.append('   %-18s %7s %-11s %7s %6s  %s'
                       % (asset, invmod._fmt(qty), unit,
                          ('%.0f' % gp) if gp is not None else '?',
                          ('%.1f' % (gp / 10)) if gp is not None else '?',
                          ('' if gp is not None else 'UNWEIGHED -- ') + nm[:30]))
        if not lines:
            out.append('   (nothing of his own)')
        out.append('   own %.0f + %.0f share = %.0f gp-wt (%.1f lb)  %s, %s'
                   % (own, share, total, total / 10, bname, move))
        out.append('')
    return '\n'.join(out).rstrip()


def everywhere(log=None):
    """Every non-character holder's contents, itemised. THE "WHERE IS X" LIST.

    `roster` answers what each character carries; the default report answers
    what the party's shared kit holds. Neither answers "what's at the
    basecamp" or "what's at Wend's barn" -- this does, by listing every `who`
    in carry.tsv that ISN'T a character or the shared `party` bucket, i.e.
    every place and non-PC person state() tracks a balance for.

    Added day 139, at the player's word, after a hand-rolled one-off script
    got a location total wrong by not respecting anchor-sets-outright
    semantics -- state() already gets that right, so this is a thin wrapper
    round it rather than a second implementation of the same arithmetic.
    """
    chars = characters()
    st = state(log)
    ass = invmod.ledgermod.assets()
    locations = sorted(w for w in st if w not in chars and w != SHARED)
    out = []
    for loc in locations:
        items = {k: q for k, q in st[loc].items() if abs(q) > 1e-9}
        if not items:
            continue
        out.append(loc + ':')
        for (asset, unit), qty in sorted(items.items(),
                                          key=lambda kv: -abs(kv[1])):
            nm = (ass.get(asset) or {}).get('name', asset)
            out.append('   %-18s %8s %-12s  %s'
                       % (asset, invmod._fmt(qty), unit, nm[:40]))
        out.append('')
    return '\n'.join(out).rstrip()


def pack(log=None, bearers=None, target='heavy'):
    """Fill the STRONGEST first, up to `target`, then the next strongest.

    The player's rule, day 103: "start with the strongest, give him shared
    weight until he is just within the 9-inch movement band. Then repeat for the
    subsequently lower strength party members. Then let's see how much weight is
    left over."

    *** WHY IT IS THE RIGHT RULE AND NOT JUST A TIDY ONE. *** An even split is
    what the party has been doing implicitly, and it is the worst possible
    division here, because the allowance spans ELEVEN HUNDRED gp-weight. Dividing
    348 lb ten ways puts 35 lb on a man with a +1,000 allowance and the same 35
    lb on a man with none. Filling by strength converts Dave's slack into
    somebody else's movement.

    Returns (assignments, leftover, rows) -- leftover is what nobody can take
    without dropping below the target band, and it is the number that decides
    whether the party needs a mule.
    """
    chars = characters()
    st = state(log)
    people = bearers or [n for n in chars if n in st]
    shared_gp, _ = shared_total(log)

    ceiling = dict((n, c) for n, c, _m in BANDS)[target]
    def _raw(score):
        """18/26 sorts above 18, which sorts above 17."""
        score = (score or '0').strip()
        if '/' in score:
            b, p = score.split('/', 1)
            try:
                return (int(b), int(p))
            except ValueError:
                return (0, 0)
        try:
            return (int(score), 0)
        except ValueError:
            return (0, 0)

    # Allowance first, THEN raw Strength as the tie-break. Without the second
    # key, Hask and Dellie at STR 11 were ordered BEHIND Frython at STR 8,
    # because all three share a +0 allowance -- and the player's rule is
    # "start with the strongest, then the subsequently lower strength members".
    ranked = sorted(people,
                    key=lambda n: (-_allowance_lookup(chars[n].get('str') or '0'),
                                   tuple(-x for x in _raw(chars[n].get('str')))))

    left = shared_gp
    overage = 0.0
    rows_ = []
    for name in ranked:
        own, _lines, _ = person_load(name, log)
        alw = _allowance_lookup(chars[name].get('str', '') or '0')
        room = max(0.0, (ceiling + alw) - own)
        # Day 120: a bearer whose OWN kit already exceeds the band's ceiling has
        # room 0, but the old code then reported "EVERY MEMBER IS WITHIN <band>"
        # -- Blartho at 745 of personal kit was called 'normal' (12") when his
        # ceiling is 550. The overage is weight that cannot be carried at this
        # band, so it counts as left over.
        overage += max(0.0, own - (ceiling + alw))
        take = min(room, left)
        left -= take
        rows_.append((name, chars[name].get('str', '?'), alw, own, room, take,
                      own + take))
    # Personal kit above a bearer's own ceiling cannot be handed on by this
    # routine (it is armour, weapons, worn gear); it counts as weight that cannot
    # be carried at this band.
    left += overage
    return rows_, left, shared_gp


def pack_report(log=None, bearers=None, target='heavy'):
    band_move = dict((n, m) for n, _c, m in BANDS)[target]
    rows_, left, shared_gp = pack(log, bearers, target)
    out = []
    out.append('FILL THE STRONGEST FIRST, up to the %r band (%s)'
               % (target, band_move))
    out.append('%-9s %6s %8s %7s %7s %7s %8s'
               % ('', 'STR', 'allowance', 'own', 'room', 'takes', 'TOTAL'))
    for name, strs, alw, own, room, take, tot in rows_:
        out.append('%-9s %6s %+8d %7.0f %7.0f %7.0f %8.0f'
                   % (name, strs, alw, own, room, take, tot))
    taken = sum(r[5] for r in rows_)
    out.append('')
    out.append('   shared kit to place   %7.0f gp-wt  (%.1f lb)'
               % (shared_gp, shared_gp / 10))
    out.append('   placed                %7.0f gp-wt  (%.1f lb)'
               % (taken, taken / 10))
    out.append('   LEFT OVER             %7.0f gp-wt  (%.1f lb)'
               % (left, left / 10))
    if left <= 0:
        spare = sum(r[4] for r in rows_) - taken
        out.append('   -> IT ALL FITS, and there is %.0f gp-wt (%.1f lb) of '
                   'room still unused.' % (spare, spare / 10))
        out.append('      EVERY MEMBER IS WITHIN %s, so THE PARTY MOVES AT %s.'
                   % (target, band_move))
    else:
        out.append('   -> %.1f lb CANNOT BE CARRIED at this band by anybody. '
                   'It goes on a mule, stays behind, or the party accepts a '
                   'slower rate.' % (left / 10))
    return '\n'.join(out)


def check(log=None):
    """[(severity, message)]. Reconcile the manifest against what is OWNED.

    *** TIGHTENED DAY 103: located == owned, not located <= owned. ***
    carry.tsv is now the single "where is everything" log, so an owned thing
    with nowhere logged for it is exactly the bug this file exists to catch --
    the same shape as the headboard and the diary, which went SEVENTY DAYS with
    an inventory row and no location anywhere. `debt` assets (Fenn's and Dill's
    loans) are excluded: they are not physical goods with a location, they are
    money owed, and belong to inventory_log.tsv alone.
    """
    log = log if log is not None else rows()
    st = state(log)
    vocab = who_vocabulary()
    owned = invmod.state()
    ass = invmod.ledgermod.assets()
    out = []

    for r in log:
        who = (r.get('who') or '').strip()
        if who and who not in vocab:
            out.append(('FAIL', 'who=%r is not a character, a place/person id,'
                        ' or %r. THE VOCABULARY IS CLOSED -- a free-typed '
                        'holder is how this went wrong in the first place.'
                        % (who, SHARED)))
        a = (r.get('asset') or '').strip()
        if a and a not in ass:
            out.append(('FAIL', 'asset %r is not in campaign/assets.tsv' % a))
        v = (r.get('verb') or '').strip()
        if v not in ('anchor', 'move'):
            out.append(('FAIL', 'verb %r is not anchor or move' % v))

    for who, cells in st.items():
        for (a, unit), q in cells.items():
            if q < 0:
                out.append(('FAIL', '%s carries %g %s -- a negative is not a '
                            'thing' % (who, q, a)))

    carried = {}
    for who, cells in st.items():
        for (a, unit), q in cells.items():
            carried[(a, unit)] = carried.get((a, unit), 0.0) + q

    owned_by_unit = {}
    for a, cells in owned.items():
        if ass.get(a, {}).get('kind') == 'debt':
            continue
        if a in invmod.FOREIGN:
            continue
        for (cond, unit), (n, u, h, note) in cells.items():
            if not n:
                continue
            owned_by_unit[(a, unit)] = owned_by_unit.get((a, unit), 0.0) + n

    # iron_spike is a SPECIAL CASE, the same one inventory.py's own
    # carried_spikes() carves out: some of what the party owns is emplaced in
    # Quasqueton doors, and world_changes.tsv owns that fact, not carry.tsv or
    # inventory_log.tsv. "Located" here means located BY THIS MANIFEST, which
    # only ever covers what is carried -- so the comparison is against
    # owned MINUS emplaced, exactly as inventory.py already computes it.
    if ('iron_spike', 'each') in owned_by_unit:
        emplaced, _ = invmod.worldmod.deployed(invmod.worldmod.load())
        owned_by_unit[('iron_spike', 'each')] -= emplaced.get('iron spike', 0)

    keys = set(carried) | set(owned_by_unit)
    for a, unit in sorted(keys):
        if a in invmod.FOREIGN:
            # A FOREIGN asset's total is owned by another log (see
            # inventory.py's FOREIGN dict), so it was never added to
            # owned_by_unit above -- but if a row here still NAMES it (e.g.
            # noting which of the party's oil flasks are physically in the
            # dungeon vs. at Wend's barn), that is a location note about part
            # of a total this file does not track, not a claim to reconcile
            # against `have=0`. Skip it entirely rather than FAIL a carried
            # amount against an ownership figure this file was never going
            # to have.
            continue
        q = carried.get((a, unit), 0.0)
        have = owned_by_unit.get((a, unit), 0.0)
        if q > have + 1e-9:
            out.append(('FAIL', 'the manifest carries %g %s of %s but the '
                        'party owns %g -- carriage may not exceed ownership'
                        % (q, unit, a, have)))
        elif q < have - 1e-9:
            out.append(('FAIL', 'the party owns %g %s of %s but the manifest '
                        'places only %g -- located must equal owned, or the '
                        'rest has no home logged anywhere' % (have, unit, a, q)))

    return out


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog='carry.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Who is carrying what, and what it does to their '
                     'movement rate.',
        epilog='No subcommand prints the full manifest (same as `roster` '
               'plus the shared-kit apportionment). Reads campaign/carry.tsv '
               '(its own log), campaign/characters.tsv, people.tsv and '
               'places.tsv (the who-vocabulary), and -- via tools/inventory.py '
               '-- campaign/inventory_log.tsv and assets.tsv for `check`, plus '
               'campaign/world_changes.tsv (iron_spike emplaced) and '
               'rules/exploration.md (Strength allowances). It never writes; '
               'append rows to carry.tsv directly. See the module docstring '
               '(head -60 tools/carry.py) for the full file-by-file '
               'breakdown, including which assets (oil_flask, coin, wool) are '
               "FOREIGN and skipped by `check` because another log owns them.")
    p.add_argument('--log-file', default=LOG,
                    help='override campaign/carry.tsv (tests use this)')
    p.add_argument('--bearers', help='comma-separated; who is actually on the '
                   'trip. The shared `party` kit is divided among THEM, not '
                   'the whole roster. Used by the default report, `person` '
                   'and `pack`; ignored by `check` and `roster`')
    sub = p.add_subparsers(dest='cmd',
                            metavar='{person,roster,where,pack,check}',
                            help='omit for the full manifest')
    q = sub.add_parser('person', help="one person's load in gp-weight and "
                        'their encumbrance band (reads characters.tsv for '
                        'Strength; --bearers sets who shares the party kit)')
    q.add_argument('name', help='a character name from campaign/characters.tsv')
    sub.add_parser('roster', help="every person's kit, itemised (ignores "
                    '--bearers)')
    sub.add_parser('where', help='every place and non-PC holder\'s contents, '
                    "itemised -- what's at the basecamp, at Wend's barn, "
                    'with Holt, and so on. The complement of `roster`')
    pk = sub.add_parser('pack', help='fill the strongest bearers first, up '
                        'to --target; report what is left over unpacked')
    pk.add_argument('--target', default='heavy',
                    choices=[n for n, _c, _m in BANDS],
                    help='the encumbrance band to fill each person up to '
                         '(default: heavy)')
    sub.add_parser('check', help='reconcile this manifest against what the '
                    'party OWNS (inventory_log.tsv via tools/inventory.py); '
                    'prints FAIL/OK lines and exits 1 on any FAIL')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    log = rows(a.log_file)
    bearers = [b.strip() for b in a.bearers.split(',')] if a.bearers else None
    if bearers is None and a.log_file == LOG:
        bearers = default_bearers(log)     # standing exemptions, campaign/carry_exempt.tsv

    if a.cmd == 'roster':
        print(roster(log, bearers))
        return 0

    if a.cmd == 'where':
        print(everywhere(log))
        return 0

    if a.cmd == 'pack':
        print(pack_report(log, bearers, a.target))
        return 0

    if a.cmd == 'check':
        problems = check(log)
        for sev, msg in problems:
            print('%-5s %s' % (sev, msg))
        if not problems:
            print('carry OK: every bearer is in the vocabulary, every asset '
                  'resolves, nothing is negative, and nothing is carried in '
                  'greater quantity than the party owns.')
        return 1 if any(s == 'FAIL' for s, _ in problems) else 0

    if a.cmd == 'person':
        chars = characters()
        if a.name not in chars:
            print('%r is not in campaign/characters.tsv. Known: %s'
                  % (a.name, ', '.join(sorted(chars))))
            return 1
        shared_gp, _ = shared_total(log)
        people = bearers or [n for n in chars if n in state(log)]
        share = (shared_gp / len(people)
                 if people and a.name in people else 0.0)
        own, lines, _ = person_load(a.name, log, share)
        alw = _allowance_lookup(chars[a.name].get('str', '') or '0')
        print('%s -- STR %s, allowance %+d gp-weight'
              % (a.name, chars[a.name].get('str', '?'), alw))
        for asset, qty, unit, gp, why in sorted(lines,
                                                key=lambda r: -(r[3] or 0)):
            print('   %-18s %8s %-12s %8s %7s  %s'
                  % (asset, invmod._fmt(qty), unit,
                     ('%.0f' % gp) if gp is not None else '?',
                     ('%.1f' % (gp / 10)) if gp is not None else '?', why))
        total = own + share
        print('   own %.0f gp-wt + %.0f share of the common kit = %.0f gp-wt '
              '(%.1f lb)' % (own, share, total, total / 10))
        bname, move = band_for(total, alw)
        print('   band: %s -- movement %s' % (bname, move))
        return 0

    print(report(log, bearers))
    return 0


if __name__ == '__main__':
    sys.exit(main())
