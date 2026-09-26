"""tools/offscreen.py: NPC agendas that keep moving whether or not the party asks.

The player's spec, day 135: weekly cadence, every roll recorded, NOTHING shown
until the party meets the person, and it must catch up on its own however long
the party has been away.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import offscreen as off                                           # noqa: E402
from tsvlog import read_tsv                                       # noqa: E402

AGENDA_HEADER = 'day\tid\taction\twho\tloop\tcadence\tceiling\ttask\ttable\tnote\n'
TICK_HEADER = 'day\tagenda\ttick\taction\troll\tkind\tnews\tdelivered_day\n'

TABLE = 'd6|1-2=progress:it moved|3-5=hold:nothing yet|6=resolve:done'


@pytest.fixture
def files(tmp_path):
    a = tmp_path / 'agendas.tsv'
    t = tmp_path / 'offscreen.tsv'
    a.write_text('# comment\n' + AGENDA_HEADER)
    t.write_text('# comment\n' + TICK_HEADER)
    return str(a), str(t)


def open_agenda(path, aid='A001', day=100, cadence=7, ceiling=8,
                who='wend', table=TABLE):
    with open(path, 'a') as fh:
        fh.write('\t'.join([str(day), aid, 'open', who, 'L043', str(cadence),
                            str(ceiling), 'the letters', table, '']) + '\n')


def rolls(*seq):
    it = iter(seq)
    return lambda notation, reason: next(it)


def test_a_tick_falls_due_one_cadence_after_it_opens(files):
    a, t = files
    open_agenda(a, day=100)
    assert off.tick(106, rolls(3), a, t) == 0
    assert off.tick(107, rolls(3), a, t) == 1
    row = read_tsv(t)[0]
    assert (row['day'], row['tick'], row['kind']) == ('107', '1', 'hold')


def test_it_is_idempotent(files):
    a, t = files
    open_agenda(a, day=100)
    off.tick(110, rolls(3), a, t)
    assert off.tick(110, rolls(3), a, t) == 0
    assert len(read_tsv(t)) == 1


def test_it_catches_up_across_a_long_absence(files):
    """The party was away three weeks: three ticks, each on its own due day."""
    a, t = files
    open_agenda(a, day=100)
    assert off.tick(121, rolls(3, 2, 4), a, t) == 3
    days = [r['day'] for r in read_tsv(t)]
    assert days == ['107', '114', '121']


def test_resolve_closes_the_agenda_and_stops_further_ticks(files):
    a, t = files
    open_agenda(a, day=100)
    assert off.tick(140, rolls(1, 6, 1, 1), a, t) == 2
    ag = off.agendas(path=a)['A001']
    assert ag['action'] == 'close'
    assert not off.is_active(ag)


def test_the_ceiling_is_a_hard_stop(files):
    a, t = files
    open_agenda(a, day=100, ceiling=2)
    assert off.tick(200, rolls(3, 3, 3, 3), a, t) == 2


def test_a_paused_agenda_does_not_tick(files):
    a, t = files
    open_agenda(a, day=100)
    with open(a, 'a') as fh:
        fh.write('105\tA001\tpause\t\t\t\t\t\t\twaiting on the party\n')
    assert off.tick(140, rolls(3), a, t) == 0


def test_an_auto_table_needs_no_die(files):
    a, t = files
    open_agenda(a, day=100, cadence=30, table='auto|due:Holt pays 40 gp')
    assert off.tick(131, None, a, t) == 1
    assert read_tsv(t)[0]['roll'] == ''


def test_news_is_held_until_delivered(files):
    a, t = files
    open_agenda(a, day=100)
    open_agenda(a, aid='A002', day=100, who='coll')
    off.tick(107, rolls(1, 2), a, t)
    assert len(off.waiting('wend', tick_path=t, agenda_path=a)) == 1
    assert len(off.waiting('Coll', tick_path=t, agenda_path=a)) == 1
    assert off.deliver('wend', day=108, tick_path=t, agenda_path=a) == 1
    assert off.waiting('wend', tick_path=t, agenda_path=a) == []
    assert len(off.waiting('coll', tick_path=t, agenda_path=a)) == 1


def test_the_table_must_cover_every_face_exactly():
    with pytest.raises(ValueError):
        off.parse_table('d6|1-2=progress:a|4-6=hold:b')
    with pytest.raises(ValueError):
        off.parse_table('d6|1-4=progress:a|4-6=hold:b')
    with pytest.raises(ValueError):
        off.parse_table('d6|1-6=maybe:a')
    off.parse_table(TABLE)


def test_the_die_is_told_the_declared_table(files):
    """The reason handed to dice.py carries the table written first."""
    a, t = files
    open_agenda(a, day=100)
    seen = []

    def spy(notation, reason):
        seen.append((notation, reason))
        return 3
    off.tick(107, spy, a, t)
    assert seen[0][0] == 'd6'
    assert 'DECLARED FIRST' in seen[0][1] and 'it moved' in seen[0][1]


def test_the_live_agendas_are_well_formed():
    assert off.check() == []
