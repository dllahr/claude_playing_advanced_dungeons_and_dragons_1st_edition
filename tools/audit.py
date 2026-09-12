#!/usr/bin/env python3
"""The deterministic half of the auditor: checks FIGURES against the tools.

    python tools/audit.py --text "the party has 595 gp and 3 spikes in the hill"
    python tools/audit.py somefile.md
    cat draft.md | python tools/audit.py -
    python tools/audit.py --staged        # what is about to be committed
    python tools/audit.py --show          # every truth it knows, and its source

WHY A DETERMINISTIC HALF EXISTS AT ALL. Roughly a third of the errors in this
campaign were plain numbers, and not one of them needed a language model:

    funds 595 gp                 -> 1,072
    3 spikes in the hill         -> 9
    Tristle 641 xp               -> 712
    19 oil flasks                -> 18
    2 ropes                      -> 8
    thief find traps 30%         -> 25%
    171 tests                    -> 185

So: the tool checks arithmetic, and the LLM auditor (`.claude/agents/auditor.md`)
is left for claims that need reading comprehension -- *"Cuddy was cold to
Yrtone"*, *"the barrel was never moved"*. Free, exact, instant, and it runs in a
pre-commit hook, so it is the one part of the auditor that CANNOT BE FORGOTTEN.

THE DESIGN CONSTRAINT THAT MATTERS MORE THAN COVERAGE: **it must not cry wolf.**
A checker that fires on historical figures would train me to ignore it, and then
it is prose again -- which is the whole failure this project is about. So:

  * a figure is only checked when an ANCHOR PHRASE for that quantity appears in
    the same sentence. Bare numbers are counted as UNCHECKED, never guessed at;
  * a sentence naming a campaign day OTHER than the current one is treated as
    HISTORICAL and skipped, because `calendar.md` is full of figures that were
    right on the day they were written and are not right now;
  * the report always prints how many figures went unchecked, so the coverage is
    visible instead of implied.

WHAT IT DOES NOT DO: tone, plausibility, whether a scene is any good, or whether
a claim about the past is true. Those are the LLM auditor's, and two of them are
nobody's.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                      # noqa: E402
import hp as hpmod                                               # noqa: E402
import xp as xpmod                                               # noqa: E402
import light as lightmod                                         # noqa: E402
import world as worldmod                                         # noqa: E402
import loops as loopmod                                          # noqa: E402
import ledger as ledgermod                                       # noqa: E402
import inventory as invmod                                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AVAIL = os.path.join(ROOT, 'campaign', 'availability.tsv')
TESTDIR = os.path.join(HERE, 'tests')

NUM = r'\d[\d,]*(?:\.\d+)?'


# --------------------------------------------------------------------------
# the truths, each computed by the tool that owns it
# --------------------------------------------------------------------------



def truths(need=None):
    """{name: (value, unit, source)}. Everything computed fresh, every call.

    `need` limits the expensive ones. Counting tests means asking pytest to
    collect, which is a second of work nobody wants in a hook that fires on
    every commit.
    """
    t = {}

    # The purse is COMPUTED from campaign/money.tsv, not read off the
    # inventory cell. That cell is materialised state; ledger.check() is what
    # notices when it drifts, and this checker must not check a figure against
    # a copy of itself.
    t['funds'] = (ledgermod.total(), 'gp', 'tools/ledger.py')

    spikes_in, _ = worldmod.deployed(worldmod.load())
    t['spikes_emplaced'] = (spikes_in.get('iron spike', 0), 'spikes',
                            'tools/world.py deployed')
    t['spikes_carried'] = (invmod.carried_spikes(), 'spikes',
                           'tools/inventory.py carried')
    t['ropes'] = (invmod.qty('rope_50ft'), 'ropes', 'tools/inventory.py')
    t['torches'] = (invmod.qty('torch'), 'torches', 'tools/inventory.py')

    oil = lightmod.oil_state()
    t['oil_sealed'] = (oil['sealed'], 'flasks', 'tools/light.py oilstate')
    t['oil_turns'] = (round((oil['sealed'] * 196 + oil['broached']) / 10.0, 1),
                      'turns', 'tools/light.py oilstate')

    day = loopmod.current_day()
    if day is not None:
        t['day'] = (day, 'day', 'campaign/days.tsv')

    if need is None or 'tests' in need:
        t['tests'] = (_count_tests(), 'tests', 'pytest --collect-only')
    t['open_loops'] = (len(loopmod.open_loops()), 'loops',
                       'tools/loops.py')

    av = _availability()
    t['available'] = (sum(1 for s in av.values() if s == 'present'),
                      'characters', 'campaign/availability.tsv')
    t['characters'] = (len(hpmod.characters()), 'characters',
                       'campaign/characters.tsv')
    return t


def _availability():
    out = {}
    for r in read_tsv(AVAIL, missing_ok=True):
        if r.get('who'):
            out[r['who']] = r.get('status', '')
    for name in hpmod.characters():
        out.setdefault(name, 'present')
    return out


def _count_tests():
    """Collected test CASES, not `def test_` lines.

    Those differ -- 160 functions expand to 198 cases through
    `@pytest.mark.parametrize` -- and the number quoted in prose and in commit
    messages has always been the collected one. Counting definitions would make
    this checker disagree with `pytest -q` and cry wolf on a true statement.
    """
    p = subprocess.run([sys.executable, '-m', 'pytest', TESTDIR,
                        '--collect-only', '-q'],
                       cwd=ROOT, capture_output=True, text=True)
    m = re.search(r'(\d+)\s+tests? collected', p.stdout)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# anchors -- a figure is checked ONLY when its anchor is in the same sentence
# --------------------------------------------------------------------------

ANCHORS = (
    ('funds',           r'\bfunds?\b|\bpurse\b|\bin the purse\b|'
                        r'party (?:has|holds)\b|\bon hand\b'),
    ('spikes_emplaced', r'spikes?[^.]{0,40}(?:emplaced|in the hill|'
                        r'left in the dungeon|still (?:in|there))|'
                        r'(?:emplaced|deployed)[^.]{0,20}spikes?'),
    ('spikes_carried',  r'spikes?[^.]{0,30}carried|carr(?:y|ies|ied)'
                        r'[^.]{0,20}spikes?'),
    ('ropes',           r'\bropes?\b'),
    ('torches',         r'\btorch(?:es)?\b'),
    ('oil_sealed',      r'sealed[^.]{0,20}flasks?|flasks?[^.]{0,20}sealed'),
    ('oil_turns',       r'turns of oil|oil[^.]{0,20}turns'),
    ('day',             r'campaign day|\bit is day\b|\btoday is day\b'),
    ('tests',           r'\btests?\b[^.]{0,20}(?:pass|passing|in `?tools)|'
                        r'\d[\d,]*\s+tests?\b'),
    ('open_loops',      r'open loops?'),
    ('available',       r'available\b|\bgo(?:ing)? up\b'),
)

# Per-character hp, written "9/9", "9 of 9", "6 of 7".
HP_PAT = re.compile(r'\b(%s)\s*(?:/|\s+of\s+)\s*(%s)\b' % (NUM, NUM))
XP_PAT = re.compile(r'\b(%s)\s*(?:xp|experience)\b' % NUM, re.I)


def sentences(text):
    for raw in re.split(r'(?<=[.!?:;])\s+|\n', text):
        s = raw.strip()
        if s:
            yield s


def historical(sentence, current_day):
    """A sentence about another day is not a claim about now.

    `calendar.md` is full of figures that were exactly right on the day they
    were written. Checking them against today would be the tool crying wolf,
    and a tool that cries wolf gets ignored the way the prose did.
    """
    days = [int(d.replace(',', '')) for d in re.findall(r'day\s+(\d[\d,]*)',
                                                        sentence, re.I)]
    return bool(days) and current_day is not None and all(
        d != current_day for d in days)


def _fmt(v):
    return ('%d' % v) if float(v) == int(v) else ('%g' % v)


WINDOW = 80          # characters. How close a figure must be to its anchor.

# How close counts as right. Funds carry odd silver -- 1,072 gp 1 sp is 1072.1
# -- and "1,072 gp" is a TRUE statement about it, so a whole-gp tolerance is
# required or the checker fires on a correct figure. Everything else is exact.
TOLERANCE = {'funds': 1.0, 'oil_turns': 1.0}


def _nearest(spans, at, window=WINDOW):
    """The span closest to `at`, or None if nothing is within `window`.

    THIS FUNCTION IS THE WHOLE DIFFERENCE BETWEEN A USEFUL TOOL AND ONE I WOULD
    LEARN TO IGNORE. The first version compared every figure in a sentence
    against every anchor in it, so *"19 sealed flasks and 2 ropes"* reported the
    rope count as a bad flask count, and *"Dave is at 9/9 and Yrtone is 6 of 7"*
    produced four findings from two facts, two of them wrong. Binding each
    figure to the nearest anchor instead is what keeps the false-positive rate
    at zero -- and a checker that cries wolf is prose again.
    """
    best, bestd = None, window + 1
    for sp in spans:
        d = 0 if sp[0] <= at <= sp[1] else min(abs(sp[0] - at), abs(sp[1] - at))
        if d < bestd:
            best, bestd = sp, d
    return best


def audit(text, tr=None, chars=None, hpnow=None, xpnow=None):
    tr = tr if tr is not None else truths(need=_needed(text))
    chars = chars if chars is not None else hpmod.characters()
    hpnow = hpnow if hpnow is not None else hpmod.current()
    xpnow = xpnow if xpnow is not None else xpmod.totals()[0]
    cur_day = tr.get('day', (None,))[0]

    findings, checked, unchecked, skipped = [], 0, 0, 0

    for s in sentences(text):
        numspans = [(m.start(), m.end(), m.group())
                    for m in re.finditer(NUM, s)]
        if not numspans:
            continue
        if historical(s, cur_day):
            skipped += len(numspans)
            continue
        used = set()

        for key, pat in ANCHORS:
            if key not in tr or tr[key][0] is None:
                continue
            for am in re.finditer(pat, s, re.I):
                n = _nearest(numspans, (am.start() + am.end()) // 2)
                if n is None:
                    continue
                want, unit, src = tr[key]
                got = float(n[2].replace(',', ''))
                ok = abs(got - want) < TOLERANCE.get(key, 1e-9)
                findings.append(('OK' if ok else 'MISMATCH', key, _fmt(got),
                                 '%s %s' % (_fmt(want), unit), src))
                checked += 1
                used.add(n[:2])
                break

        namespans = []
        for name in chars:
            for m in re.finditer(r'\b%s\b' % re.escape(name), s, re.I):
                namespans.append((m.start(), m.end(), name))

        for m in HP_PAT.finditer(s):
            owner = _nearest(namespans, m.start())
            if owner is None:
                continue
            cur, mx = hpnow.get(owner[2], (None, None))
            if cur is None:
                continue
            said = '%s/%s' % (m.group(1), m.group(2))
            ok = (float(m.group(1)), float(m.group(2))) == (float(cur), float(mx))
            findings.append(('OK' if ok else 'MISMATCH', 'hp:' + owner[2], said,
                             '%d/%d' % (cur, mx), 'tools/hp.py'))
            checked += 1
            used.add((m.start(1), m.end(1)))
            used.add((m.start(2), m.end(2)))

        for m in XP_PAT.finditer(s):
            owner = _nearest(namespans, m.start())
            if owner is None or owner[2] not in xpnow:
                continue
            want = xpnow[owner[2]]
            got = float(m.group(1).replace(',', ''))
            ok = abs(got - want) < 1
            findings.append(('OK' if ok else 'MISMATCH', 'xp:' + owner[2],
                             _fmt(got), '%d' % want, 'tools/xp.py'))
            checked += 1
            used.add((m.start(1), m.end(1)))

        unchecked += sum(1 for n in numspans if n[:2] not in used)

    return findings, dict(checked=checked, unchecked=unchecked,
                          historical=skipped)


def _needed(text):
    """Which expensive truths this text could possibly be talking about."""
    need = set()
    for key, pat in ANCHORS:
        if re.search(pat, text, re.I):
            need.add(key)
    return need


def report(findings, stats, quiet_ok=True):
    bad = [f for f in findings if f[0] == 'MISMATCH']
    lines = []
    for verdict, key, said, truth, src in findings:
        if verdict == 'OK' and quiet_ok:
            continue
        lines.append('%-9s %-18s text says %-14s tools say %-16s [%s]'
                     % (verdict, key, said, truth, src))
    if not lines:
        lines.append('no mismatches')
    lines.append('')
    lines.append('%d figure(s) checked, %d MISMATCHED, %d unchecked '
                 '(no checker), %d skipped as historical'
                 % (stats['checked'], len(bad), stats['unchecked'],
                    stats['historical']))
    if stats['unchecked']:
        lines.append('*** "unchecked" is coverage, not a clean bill. The '
                     'deterministic half only knows the quantities listed by '
                     '`--show`; everything else is the LLM auditor\'s job.')
    return '\n'.join(lines)


# Paths whose whole job is to discuss the errors, so they QUOTE the wrong
# figures on purpose. `dlwork/` holds the post-mortems and this very plan;
# `deprecated/` is retired by definition. Auditing them would be the tool
# flagging a correct document for correctly reporting an incorrect number.
SKIP_PATHS = ('dlwork/', 'deprecated/', 'tools/tests/', 'tools/audit.py')

# Any line may opt out. Use it for a figure deliberately quoted as it stood.
SKIP_MARK = 'audit-skip'

# *** ONLY PROSE IS AUDITED. ***
#
# The first time this hook ran against a real commit it blocked one, and every
# finding was a false positive out of the new TSVs: `torch ... 100` was an asset
# name beside its unit WEIGHT; `rope, 50 ft ... 75` gave "50" and "75"; and the
# header comment of money.tsv, which lists the five historical errors by way of
# explaining itself, offered up "357 gp of small goods" as a rope count.
#
# The diagnosis is not that the anchors were sloppy. It is that AUDITING THE
# LOGS IS CIRCULAR: they are what the tools compute FROM, so checking them
# against the tools compares a figure with a copy of itself, and the only thing
# such a check can ever produce is noise. Paraphrases live in prose. That is
# where the eight class-C errors lived, every one of them.
#
# The hook's own header says: if it cries wolf, LOOSEN THE CHECKER, do not learn
# to pass --no-verify. This is that, on the first occasion, by design.
AUDIT_EXTENSIONS = ('.md',)


def staged_text():
    """Added lines from the staged diff -- what is about to be committed.

    Tracks which file each hunk belongs to so SKIP_PATHS can be honoured. A
    single blob of every added line in the commit would audit the post-mortems
    along with the play, and the post-mortems are full of the wrong numbers on
    purpose.
    """
    p = subprocess.run(['git', 'diff', '--cached', '--unified=0'],
                       cwd=ROOT, capture_output=True, text=True)
    out, path = [], ''
    for ln in p.stdout.splitlines():
        if ln.startswith('+++ b/'):
            path = ln[6:]
            continue
        if ln.startswith(('---', '+++', '@@', 'diff ', 'index ')):
            continue
        if not ln.startswith('+'):
            continue
        if not path.endswith(AUDIT_EXTENSIONS):
            continue
        if any(path.startswith(sk) for sk in SKIP_PATHS):
            continue
        if SKIP_MARK in ln:
            continue
        out.append(ln[1:])
    return '\n'.join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog='audit.py',
        description='Check the figures in a block of text against the tools.')
    p.add_argument('path', nargs='?', help='a file, or - for stdin')
    p.add_argument('--text', help='audit this string')
    p.add_argument('--staged', action='store_true',
                   help='audit the added lines of the staged diff')
    p.add_argument('--show', action='store_true',
                   help='print every truth this tool knows, and its source')
    p.add_argument('--all', action='store_true', help='include OK lines')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.show:
        print('%-18s %-14s %s' % ('quantity', 'value', 'source'))
        for k, (v, unit, src) in sorted(truths().items()):
            print('%-18s %-14s %s' % (k, '%s %s' % (_fmt(v), unit), src))
        return 0

    if a.text is not None:
        text = a.text
    elif a.staged:
        text = staged_text()
    elif a.path in (None, '-'):
        text = sys.stdin.read()
    else:
        text = open(os.path.join(ROOT, a.path) if not os.path.isabs(a.path)
                    else a.path).read()

    if not text.strip():
        print('nothing to audit')
        return 0
    findings, stats = audit(text)
    print(report(findings, stats, quiet_ok=not a.all))
    return 1 if any(f[0] == 'MISMATCH' for f in findings) else 0


if __name__ == '__main__':
    sys.exit(main())
