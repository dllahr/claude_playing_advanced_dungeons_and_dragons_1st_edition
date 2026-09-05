#!/usr/bin/env python3
"""Read the verified rules cache in `rules/*.md` as data.

    python tools/rules.py --list                       # every table found
    python tools/rules.py --show "To-hit, monsters"    # print one
    python tools/rules.py --cite "Weapon damage"       # its provenance line

Why parse markdown instead of writing the tables in Python
----------------------------------------------------------
Because then there would be two of them. `rules/*.md` is the verified cache:
every table in it was transcribed from a page render and carries a `*source:*`
line naming the book and page. That citation is the reason the PDFs are kept at
all, and it has to sit next to the numbers the dice are actually compared
against -- otherwise the markdown drifts into being documentation of a Python
table nobody re-checks, and "cite book and page" becomes a fiction.

So this module is deliberately thin: find the pipe-tables under each heading,
return them as rows of strings, and carry the source line along. Interpretation
belongs to the caller.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(ROOT, 'rules')

_BOLD = re.compile(r'\*+([^*]*)\*+')
_DASH = re.compile(r'[‐-―−]')       # en/em dash, minus sign


def clean(cell):
    """Strip markdown emphasis and normalise the dashes OCR and typography mix.

    A minus sign, a hyphen and an en dash all appear in these tables and all
    mean the same thing in "1-8" or "-3". Leaving them distinct makes int()
    fail on values that look perfectly correct on screen.
    """
    return _DASH.sub('-', _BOLD.sub(r'\1', cell)).strip()


def parse_file(path):
    """{heading: {'columns': [...], 'rows': [[...]], 'source': str}}.

    Tables are keyed by the nearest preceding heading, so renaming a heading in
    the markdown breaks the lookup loudly rather than silently returning the
    wrong table.
    """
    tables, heading, pending = {}, None, None
    for raw in open(path):
        line = raw.rstrip('\n')
        s = line.strip()
        if s.startswith('#'):
            heading = s.lstrip('#').strip()
            pending = None
            continue
        if s.startswith('|') and s.endswith('|'):
            cells = [clean(c) for c in s.strip('|').split('|')]
            if all(set(c) <= set('-: ') and c for c in cells):
                continue                       # the |---| separator row
            if pending is None:
                pending = {'columns': cells, 'rows': [], 'source': None,
                           'file': os.path.basename(path)}
                # A heading may carry more than one table; keep the first and
                # suffix the rest, rather than silently overwriting.
                key = heading or os.path.basename(path)
                n = 2
                while key in tables:
                    key = '%s (%d)' % (heading, n)
                    n += 1
                tables[key] = pending
                pending['key'] = key
            else:
                pending['rows'].append(cells)
            continue
        if pending is not None and s.startswith('*source:'):
            pending['source'] = clean(s)
        if not s:
            continue
        if pending is not None and not s.startswith('*'):
            pending = None                     # prose ends the table
    return tables


def load(names=None, directory=None):
    """Every table in a cache directory, keyed 'file.md :: Heading'.

    `directory` defaults to rules/; bestiary/ uses the identical format, so
    tools/bestiary.py is this function pointed somewhere else rather than a
    second parser.
    """
    directory = directory or RULES
    out = {}
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith('.md') or (names and fn not in names):
            continue
        for key, t in parse_file(os.path.join(directory, fn)).items():
            out['%s :: %s' % (fn, key)] = t
    return out


def find(fragment, tables=None):
    """The one table whose key contains `fragment`. Ambiguity is an error.

    Returning "the first match" would make a typo in a heading select a
    plausible-looking wrong table, which is the failure this whole cache exists
    to prevent.
    """
    tables = tables if tables is not None else load()
    hits = [k for k in tables if fragment.lower() in k.lower()]
    if not hits:
        raise KeyError('no rules table matching %r; --list shows them all'
                       % fragment)
    if len(hits) > 1:
        exact = [k for k in hits if k.split(':: ')[-1].lower() == fragment.lower()]
        if len(exact) != 1:
            raise KeyError('%r matches %d tables: %s'
                           % (fragment, len(hits), ', '.join(sorted(hits))))
        hits = exact
    return tables[hits[0]]


def as_dict(table, key_col=0):
    """{first column: {column name: value}} for row lookups by name."""
    cols = table['columns']
    return {r[key_col]: dict(zip(cols, r)) for r in table['rows'] if r}


def lookup(table, row_key, column):
    """One cell, by row label and column label. Raises with the options listed."""
    d = as_dict(table)
    if row_key not in d:
        raise KeyError('no row %r in %s (rows: %s)'
                       % (row_key, table.get('key'), ', '.join(sorted(d))))
    if column not in table['columns']:
        raise KeyError('no column %r in %s (columns: %s)'
                       % (column, table.get('key'), ', '.join(table['columns'])))
    return d[row_key][column]


def build_parser():
    p = argparse.ArgumentParser(
        prog='rules.py',
        description='Read the verified rules cache in rules/*.md as data.')
    p.add_argument('--list', action='store_true', help='list every table found')
    p.add_argument('--show', metavar='FRAGMENT', help='print one table')
    p.add_argument('--cite', metavar='FRAGMENT', help='print its source line')
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    tables = load()
    if a.list or not (a.show or a.cite):
        for k in sorted(tables):
            t = tables[k]
            print('%-58s %2d cols x %3d rows  %s'
                  % (k, len(t['columns']), len(t['rows']),
                     'cited' if t['source'] else 'NO SOURCE LINE'))
        return 0
    t = find(a.cite or a.show, tables)
    if a.cite:
        print(t['source'] or '(no source line -- treat as unverified)')
        return 0
    print(' | '.join(t['columns']))
    for r in t['rows']:
        print(' | '.join(r))
    print()
    print(t['source'] or '(no source line -- treat as unverified)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
