#!/usr/bin/env python3
"""THE ONLY WRITE PATH. It validates, then it appends. Never write by hand.

    python tools/log.py money --delta -12 --asset rations_iron --qty 3 \
        --reason "three person-weeks of iron rations for expedition 9"
    python tools/log.py money --delta +28 --asset ale_barrel_sd \
        --counterparty holt --reason "the second half of the cask, as drawn"
    python tools/log.py day --day 78 --where basecamp --summary "..."
    python tools/log.py available --who Hask --status present \
        --why "back off the wool road"
    python tools/log.py assets                 # what ids exist

WHY A SINGLE ENTRY POINT AT ALL. A foreign key in a database catches a bad row
when the database is next rebuilt -- a red build, afterwards. This tool catches
it AT THE MOMENT OF WRITING and refuses. That is the difference between the
three mechanisms in this repo with a perfect record and every prose warning in
it, which have all failed again:

    party.py move      cannot cross a wall
    tests/conftest.py  cannot write to the campaign roll log
    test_lane_rule.py  will not let a paraphrase carry the figure

VALIDATE ON WRITE, REBUILD ON READ. The TSVs stay the source of record --
append-only, greppable, fixable at the table -- and this tool is the gate.

WHAT IT REFUSES, and each refusal is an error that actually happened:

  * **a money row with no asset.** Five purchases in this campaign were recorded
    only as a sentence inside the notes column of the `funds` row, and the thing
    bought got no row anywhere: the two carts (forty days), the two mules, the
    small goods (357 gp, seventeen days), six ropes (eleven days, while the rope
    row still said 2), the dragon scales. **You cannot write down that money
    moved without writing down what it moved for.**
  * **an asset id that is not in `campaign/assets.tsv`.** A typo'd id is worse
    than a missing row, because it reconciles to nothing and looks deliberate.
  * **a short row.** `tsvlog.read_tsv` pads short rows on purpose, so a line
    missing a MIDDLE field is read silently with every later value shifted one
    column left. That happened twice within an hour of `money.tsv` being
    written: two rows lost their `interaction` field and their reason was read
    as an interaction id. This tool always writes the full width.
  * **a day that runs backwards** past the last one in `days.tsv`, which is how
    the campaign day drifted before the player caught it.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsvlog import append, header_of, read_tsv, today             # noqa: E402
import ledger as ledgermod                                        # noqa: E402
import loops as loopmod                                           # noqa: E402
import hp as hpmod                                                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONEY = os.path.join(ROOT, 'campaign', 'money.tsv')
DAYS = os.path.join(ROOT, 'campaign', 'days.tsv')
AVAIL = os.path.join(ROOT, 'campaign', 'availability.tsv')

STATUSES = ('present', 'away', 'invalid', 'dead')


class Refused(Exception):
    """Not an error in the tool. The tool working."""


def _write(path, row):
    """Append at the file's FULL WIDTH, so no field can shift left."""
    full = {c: row.get(c, '') for c in header_of(path)}
    return append(path, full)


def do_money(a):
    ass = ledgermod.assets()
    if not a.asset:
        raise Refused(
            'NO ASSET. Money cannot move for nothing -- that is the one rule '
            'this file has. Name what it was for; `python tools/log.py assets` '
            'lists the ids, and there are service ids (wages, lodging, '
            'licence, loan, kit, service) for money that does not buy a thing.')
    if a.asset != ledgermod.ANCHOR and a.asset not in ass:
        near = sorted(k for k in ass if a.asset.lower() in k.lower()
                      or k.lower() in a.asset.lower())
        raise Refused('asset %r is not in campaign/assets.tsv.%s'
                      % (a.asset,
                         ('\nDid you mean: %s' % ', '.join(near)) if near
                         else ' Add it there first -- a typo\'d id reconciles '
                              'to nothing and looks deliberate.'))
    if a.delta == 0:
        raise Refused('a delta of zero records nothing. Omit the row, or say '
                      'what actually moved.')
    day = a.day if a.day is not None else loopmod.current_day()
    line = _write(a.log_file or MONEY, dict(
        when=today(), day=day, delta=a.delta, asset=a.asset,
        qty=a.qty or '', counterparty=a.counterparty or '-',
        interaction=a.interaction or '-', reason=a.reason))
    print(line)
    print()
    print(ledgermod.report(ledgermod.rows(a.log_file or MONEY)))
    print()
    for sev, msg in ledgermod.check(ledgermod.rows(a.log_file or MONEY)):
        print('%-5s %s' % (sev, msg))
    return 0


def do_day(a):
    last = loopmod.current_day(a.log_file or DAYS)
    if last is not None and a.day < last:
        raise Refused(
            'day %d is BEHIND the last logged day (%d). The campaign day only '
            'goes forward; it drifted once when it was kept in the DM\'s head '
            'and the player caught it on Torsat\'s illness. If a past day '
            'genuinely needs a row, add it by hand and say in the summary why.'
            % (a.day, last))
    print(_write(a.log_file or DAYS, dict(
        day=a.day, when=today(), where=a.where or '', summary=a.summary or '')))
    return 0


def do_available(a):
    if a.who not in hpmod.characters():
        raise Refused('no character %r. This file covers the nine in '
                      'characters.tsv; NPC whereabouts are a different '
                      'question. Known: %s'
                      % (a.who, ', '.join(sorted(hpmod.characters()))))
    if a.status not in STATUSES:
        raise Refused('status %r is not one of %s'
                      % (a.status, ', '.join(STATUSES)))
    day = a.day if a.day is not None else loopmod.current_day()
    print(_write(a.log_file or AVAIL, dict(
        when=today(), day=day, who=a.who, status=a.status,
        until_day=a.until_day or '', why=a.why or '')))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog='log.py',
        description='The only write path. It validates, then it appends.')
    p.add_argument('--log-file', help='override the target file (for tests)')
    sub = p.add_subparsers(dest='cmd', required=True)

    m = sub.add_parser('money', help='a movement of coin. ASSET IS REQUIRED')
    m.add_argument('--delta', type=float, required=True,
                   help='gold pieces, decimal. 0.1 = 1 s.p. Negative is out')
    m.add_argument('--asset', required=True,
                   help='an id from campaign/assets.tsv. REQUIRED -- this is '
                        'the double entry')
    m.add_argument('--qty', help='how many units moved; negative if sold')
    m.add_argument('--counterparty', help='who the money came from or went to')
    m.add_argument('--interaction', help='day:seq of the scene, if there was one')
    m.add_argument('--reason', required=True)
    m.add_argument('--day', type=int)
    m.set_defaults(fn=do_money)

    d = sub.add_parser('day', help='open a new campaign day')
    d.add_argument('--day', type=int, required=True)
    d.add_argument('--where')
    d.add_argument('--summary')
    d.set_defaults(fn=do_day)

    v = sub.add_parser('available', help='a character\'s status changed')
    v.add_argument('--who', required=True)
    v.add_argument('--status', required=True,
                   help=' | '.join(STATUSES))
    v.add_argument('--until-day', help='a FORECAST. It does not close the row')
    v.add_argument('--why')
    v.add_argument('--day', type=int)
    v.set_defaults(fn=do_available)

    sub.add_parser('assets', help='list the asset ids').set_defaults(
        fn=lambda a: ledgermod.main(['assets']))
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        return a.fn(a)
    except Refused as exc:
        print('REFUSED: %s' % exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
