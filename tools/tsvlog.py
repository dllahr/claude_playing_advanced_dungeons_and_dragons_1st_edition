#!/usr/bin/env python3
"""Reading and appending the campaign's tab-separated logs.

Every bookkeeping file in `campaign/` has the same shape: a comment header, a
single header row, and one row per event. This module is the one place that
knows how to read and extend them, because two implementations that have to
agree is the failure mode this project keeps rediscovering.

The convention these files share, and the reason for it:

  * **Append only.** A row is an event, never a running total. `tools/xp.py`
    recomputes experience from `encounters.tsv` on every invocation, and
    `tools/world.py` recomputes the state of the dungeon from
    `world_changes.tsv` the same way. A stored total goes stale silently -- the
    roster's XP line was last correct on day 2 of expedition 1 and was quoted
    as authoritative for weeks afterwards, and the equipment list told the DM
    the party's iron spikes were wedged in a door they had already pulled them
    out of.

  * **Comments are data too.** Lines beginning `#` carry the provenance of the
    rows under them and are preserved by every writer here.
"""
import datetime
import os


def read_tsv(path, missing_ok=False):
    """Rows of a campaign TSV as dicts, comments and blank lines dropped."""
    if missing_ok and not os.path.exists(path):
        return []
    rows, header = [], None
    with open(path) as fh:
        for line in fh:
            line = line.rstrip('\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            f = [c.strip() for c in line.split('\t')]
            if header is None:
                header = f
                continue
            # Short rows are padded rather than rejected: a hand-edited line
            # with the trailing note left off is still a usable event.
            f += [''] * (len(header) - len(f))
            rows.append(dict(zip(header, f)))
    return rows


def header_of(path):
    """The column names, so an appender writes fields in the file's own order."""
    with open(path) as fh:
        for line in fh:
            if line.strip() and not line.lstrip().startswith('#'):
                return [c.strip() for c in line.rstrip('\n').split('\t')]
    return []


def append(path, row):
    """Append one row, ordered by the file's own header. Returns the line."""
    cols = header_of(path)
    if not cols:
        raise ValueError('%s has no header row' % path)
    unknown = set(row) - set(cols)
    if unknown:
        raise ValueError('%s has no column(s) %s' % (path, sorted(unknown)))
    line = '\t'.join(str(row.get(c, '')) for c in cols)
    with open(path, 'a') as fh:
        fh.write(line + '\n')
    return line


def today():
    return datetime.date.today().isoformat()
