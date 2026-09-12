#!/usr/bin/env python3
"""The session briefing -- one command instead of reading four prose files.

    python tools/brief.py
    python tools/brief.py --day 79
    python tools/brief.py --touching "Wend, Osk"     # scene-scoped loops too

RUN THIS AT THE START OF EVERY SESSION AND AFTER EVERY COMPACT.

WHY IT EXISTS. Orientation used to mean opening `calendar.md`, `npcs.md`,
`party_roster.md` and `CHECKLIST` section 11 and reading a snapshot out of each
-- and three of those four were stale the last time it was done. Section 11 was
headed "day 39" while play stood at day 77; it carried funds of 595 gp against
an actual 1,072, spikes 3 against 9, and Tristle's XP 641 against 712. Every
number in this briefing is COMPUTED FRESH by the tool that owns it, so there is
nothing here that can be 38 in-game days out of date.

WHAT THIS IS NOT. It is the BROAD, SHALLOW view -- the thing needed when
context has just been lost. Two other shapes of "state on hand" exist and want
their own tools, and conflating them was a mistake in the first draft of the
plan (`dlwork/tooling_plan.md`, section 1.4):

    briefing   broad, shallow, at session start      <- this file
    scene      narrow and deep, about one person     <- recall.py
    encounter  small, fast, rewritten every round    <- encounter.tsv, phase 3

DESIGN NOTE: this tool SHELLS OUT to the others rather than importing them. It
has exactly one job -- composition -- and if `light.py` changes its internals
the briefing keeps working and shows you `light.py`'s own words. A briefing that
reimplemented any of these would be the second copy this whole project exists to
remove.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import read_tsv                                     # noqa: E402
import loops as loopmod                                         # noqa: E402
import ledger as ledgermod                                      # noqa: E402
import inventory as invmod                                      # noqa: E402
import entities as entmod                                       # noqa: E402
import build_campaign_db as dbmod                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DAYS = os.path.join(ROOT, 'campaign', 'days.tsv')
AVAIL = os.path.join(ROOT, 'campaign', 'availability.tsv')
WORLD_LOG = os.path.join(ROOT, 'campaign', 'world_changes.tsv')
MAPDB = os.path.join(ROOT, 'mapdb', 'output', 'b1', 'b1.sqlite')

RULE = '=' * 78


def run(args):
    """One tool's own output, or its error. Never reimplement, never guess."""
    try:
        p = subprocess.run([sys.executable] + args, cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
    except Exception as exc:                       # pragma: no cover
        return '(could not run %s: %s)' % (' '.join(args), exc)
    out = (p.stdout or '').rstrip()
    err = (p.stderr or '').strip()
    if err and not out:
        return '(%s failed: %s)' % (args[0], err.splitlines()[-1])
    if err:
        out += '\n(stderr: %s)' % err.splitlines()[-1]
    return out or '(no output)'


def day_row(day=None, path=None):
    rows = [r for r in read_tsv(path or DAYS, missing_ok=True)
            if r.get('day', '').strip().isdigit()]
    if not rows:
        return None
    if day is None:
        return max(rows, key=lambda r: int(r['day']))
    at = [r for r in rows if int(r['day']) <= day]
    return max(at, key=lambda r: int(r['day'])) if at else None


def availability(path=None):
    """Latest row per character wins. No row at all means present."""
    out = {}
    for r in read_tsv(path or AVAIL, missing_ok=True):
        who = r.get('who', '').strip()
        if who:
            out[who] = r
    return out


def avail_report(path=None):
    av = availability(path)
    here = sorted(n for n, r in av.items() if r.get('status') == 'present')
    gone = [(n, r) for n, r in sorted(av.items())
            if r.get('status') != 'present']
    lines = ['AVAILABLE (%d): %s' % (len(here), ', '.join(here) or '--')]
    for n, r in gone:
        until = r.get('until_day', '').strip()
        lines.append('  %-8s %-8s %s %s'
                     % (n, r.get('status', ''),
                        ('back ~day %s' % until) if until else '',
                        r.get('why', '')))
    return '\n'.join(lines)


def stale_report():
    """Are the derived views current with the logs they are built from?

    `campaign.sqlite` carries a real watermark -- a `build_meta` row per source
    TSV with its row count and a sha256 -- so staleness is a COMPARISON and not
    a judgment. The map cache still only gets a modification-time check, which
    is a weak proxy: it cannot say HOW far behind. It is honest about the
    direction, and the direction is the part that kept being missed.
    """
    out = []
    for name, why in dbmod.stale():
        out.append('*** campaign.sqlite: %s %s -- run '
                   'python tools/build_campaign_db.py' % (name, why))
    if not os.path.exists(MAPDB):
        out.append('mapdb/output/b1/b1.sqlite ABSENT -- run mapdb/rebuild.sh')
    elif os.path.getmtime(MAPDB) < os.path.getmtime(WORLD_LOG):
        out.append('*** b1.sqlite IS OLDER THAN world_changes.tsv. '
                   'Run: python tools/world.py replay '
                   '--db mapdb/output/b1/b1.sqlite --level 1')
    return '\n'.join(out) or 'nothing stale'


def brief(day=None, touching=None):
    d = day_row(day)
    today_n = int(d['day']) if d else None
    parts = []

    head = 'CAMPAIGN DAY %s' % (today_n if today_n is not None else '?')
    if d:
        head += '  --  %s' % d.get('where', '')
        if d.get('summary'):
            head += '\n%s' % d['summary']
    parts.append(head)

    parts.append(RULE + '\n' + avail_report())
    purse = [RULE, 'THE PURSE', ledgermod.report()]
    problems = ledgermod.check()
    if problems:
        purse.append('')
        purse += ['%-5s %s' % (sev, msg) for sev, msg in problems]
    parts.append('\n'.join(purse))

    gear = [RULE, 'WHAT THE PARTY OWNS  (computed; carried spikes = owned - '
                  'emplaced)', run(['tools/inventory.py'])]
    bad = invmod.check()
    if bad:
        gear.append('')
        gear += ['%-5s %s' % (sev, msg) for sev, msg in bad]
    parts.append('\n'.join(gear))

    parts.append(RULE + '\nHIT POINTS\n' + run(['tools/hp.py']))
    parts.append(RULE + '\nEXPERIENCE\n' + run(['tools/xp.py']))
    parts.append(RULE + '\nLIGHT AND OIL\n' + run(['tools/light.py', 'oilstate']))
    # world.py deployed prints one summary line per item and then an indented
    # provenance row for every change ever made -- hundreds of them. The
    # briefing wants the totals only; `world.py deployed` itself is the place
    # to go for the history.
    gear = [ln for ln in run(['tools/world.py', 'deployed']).splitlines()
            if ln.startswith('  ') and not ln.startswith('      ')]
    parts.append(RULE + '\nGEAR LEFT IN THE DUNGEON\n'
                 + ('\n'.join(gear) or '  nothing emplaced'))
    parts.append(RULE + '\nDUNGEON POSITION  (this tool knows NOTHING about '
                        'overland travel)\n'
                 + '\n'.join(run(['tools/party.py', 'where']).splitlines()[:2]))
    parts.append(RULE + '\nCLOCK  (reports the LAST expedition until a new one '
                        'starts -- there is no `close`)\n'
                 + run(['tools/clock.py', 'status']))
    parts.append(RULE + '\n' + loopmod.report(day=today_n))
    if touching:
        parts.append(RULE + '\nLOOPS TOUCHING %s\n%s'
                     % (touching, loopmod.report(touching=touching,
                                                 day=today_n)))
        for name in [n.strip() for n in touching.split(',') if n.strip()]:
            parts.append(RULE + '\n' + entmod.who(name))
    bad = entmod.check()
    if bad:
        parts.append(RULE + '\nENTITIES\n'
                     + '\n'.join('%-5s %s' % x for x in bad))
    parts.append(RULE + '\nSTALE?\n' + stale_report())
    return '\n\n'.join(parts)


def build_parser():
    p = argparse.ArgumentParser(
        prog='brief.py', description='The session briefing, computed fresh.')
    p.add_argument('--day', type=int, help='brief as of this campaign day')
    p.add_argument('--touching',
                   help='comma-separated names; adds a scene-scoped loop list')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    print(brief(day=a.day, touching=a.touching))
    return 0


if __name__ == '__main__':
    sys.exit(main())
