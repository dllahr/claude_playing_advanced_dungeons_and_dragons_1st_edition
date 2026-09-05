#!/usr/bin/env python3
"""The campaign's own Monster Manual, built up as creatures are encountered.

    python tools/bestiary.py --list
    python tools/bestiary.py troglodyte
    python tools/bestiary.py troglodyte --field "Surprises On"

`bestiary/` holds one markdown file per creature in exactly the format of
`rules/*.md`, so this module is `tools/rules.py` pointed at another directory
rather than a second parser.

Why it exists
-------------
Every stat block here was read off a Monster Manual page render, which costs a
page search, a render and a read each time. Before this file that work was
thrown away after every fight and done again at the next one -- and worse, the
numbers in between lived only in the DM's memory. Two encounters were run with
the wrong troglodyte surprise range for exactly that reason.

What each file must carry, beyond the stat block:

  * **Surprises On / Surprised On.** The default 1-2 is wrong often enough that
    it belongs in data. Troglodytes surprise on 1-4.
  * **Special attacks and defences as rows**, with trigger, save and duration --
    a paragraph is not something you can read mid-round.
  * **The module conversion.** B1 is statted for Basic D&D and disagrees with
    the MM; keeping both, side by side, is how you can see which book a number
    came from.
  * **The play record.** What it actually did to this party.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules                                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BESTIARY = os.path.join(ROOT, 'bestiary')


def creatures():
    """{name: filename} for everything in the bestiary."""
    return {fn[:-3].replace('-', ' '): fn
            for fn in sorted(os.listdir(BESTIARY))
            if fn.endswith('.md') and fn != 'README.md'}


def stats(name):
    """The creature's stat block as {field: value}. Raises if it is unknown."""
    key = name.strip().lower().replace('-', ' ')
    known = creatures()
    if key not in known:
        raise KeyError('no bestiary entry for %r; have: %s'
                       % (name, ', '.join(sorted(known))))
    tables = rules.load([known[key]], directory=BESTIARY)
    for k, t in tables.items():
        if 'stat block' in k.lower():
            return rules.as_dict(t), t['source']
    raise KeyError('%s has no "... stat block" table' % known[key])


def tables(name):
    """Every table in the creature's file, for the sections beyond the block."""
    key = name.strip().lower().replace('-', ' ')
    return rules.load([creatures()[key]], directory=BESTIARY)


def field(name, which, default=None):
    d, _ = stats(name)
    for k, v in d.items():
        if k.lower() == which.lower():
            return v['Value']
    if default is not None:
        return default
    raise KeyError('%s has no field %r' % (name, which))


def build_parser():
    p = argparse.ArgumentParser(
        prog='bestiary.py', description="The campaign's own Monster Manual.")
    p.add_argument('creature', nargs='?', help='which creature')
    p.add_argument('--list', action='store_true', help='list every entry')
    p.add_argument('--field', help='print one field of the stat block')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.list or not a.creature:
        for name in sorted(creatures()):
            try:
                d, _ = stats(name)
                print('%-14s AC %-4s HD %-16s %s'
                      % (name, d.get('Armor Class', {}).get('Value', '?'),
                         d.get('Hit Dice', {}).get('Value', '?'),
                         d.get('Damage', {}).get('Value', '?')))
            except KeyError as e:
                print('%-14s (unreadable: %s)' % (name, e))
        return 0
    if a.field:
        print(field(a.creature, a.field))
        return 0
    d, src = stats(a.creature)
    print(a.creature.upper())
    for k, v in d.items():
        print('  %-20s %s' % (k, v['Value']))
    print('  %s' % (src or '(no source line)'))
    for key, t in sorted(tables(a.creature).items()):
        head = key.split(':: ')[-1]
        if 'stat block' in head.lower() or not t['rows']:
            continue
        print('\n%s' % head)
        print('  ' + ' | '.join(t['columns']))
        for r in t['rows']:
            print('  ' + ' | '.join(r))
    return 0


if __name__ == '__main__':
    sys.exit(main())
