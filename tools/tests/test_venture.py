"""The venture -- what it holds, what it owes, who owns it.

Day 103. The player asked for this alongside carry.tsv: an inventory of what
the wool/cloth venture holds, and a cap table for its shares. Scope is
DELIBERATELY (a) physical holdings and (b) money position -- never (c)
valuation, which the player said to figure out only when needed.

Split into two ventures the same day, at the player's correction:
`wool-venture-1` (the 14-share day 12-27 deal, CLOSED) and `ongoing-venture`
(everything since, party capital only, no cap table).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import venture                                                   # noqa: E402


def _log(*rows):
    return [dict(zip(('when', 'day', 'venture', 'asset', 'verb', 'qty',
                      'unit', 'holder', 'evidence', 'note'), r))
            for r in rows]


def _slog(*rows):
    return [dict(zip(('when', 'day', 'who', 'verb', 'shares', 'note'), r))
            for r in rows]


def test_shares_sum_per_holder():
    st = venture.shares(_slog(
        ('d', '16', 'Dave', 'anchor', '1', ''),
        ('d', '16', 'wend', 'anchor', '1', '')))
    assert st['Dave'] == 1
    assert st['wend'] == 1


def test_an_anchor_sets_outright_and_a_move_adds():
    st = venture.shares(_slog(
        ('d', '16', 'Dave', 'anchor', '1', ''),
        ('d', '50', 'Dave', 'move', '-1', 'sold to Torsat'),
        ('d', '50', 'Torsat', 'move', '1', 'bought from Dave')))
    assert st['Dave'] == 0
    assert st['Torsat'] == 1


def test_the_live_cap_table_totals_fourteen():
    """wool_venture.md: 6 PCs at 1 + Hask/Dellie at 1/2 + Wend 1 + holders 6."""
    assert sum(venture.shares().values()) == 14


def test_a_share_is_not_capital_and_this_module_prices_nothing():
    """The player's scope, verbatim: (a) and (b), never (c) valuation."""
    src = open(os.path.join(TOOLS, 'venture.py'), encoding='utf-8').read()
    assert 'valuation' in src.lower()
    for banned in ('def price', 'def value', 'def worth', 'gp_per_share'):
        assert banned not in src


def test_holdings_excludes_the_position_assets():
    """venture_capital and venture_payable_holders are (b), not (a)."""
    h = venture.holdings(_log(
        ('d', '103', 'ongoing-venture', 'wool', 'anchor', '36', 'tod', 'wend',
         '', ''),
        ('d', '103', 'ongoing-venture', 'venture_capital', 'anchor', '288',
         'gp', 'party', '', '')))
    assets_seen = {row[1] for row in h}
    assert 'wool' in assets_seen
    assert 'venture_capital' not in assets_seen


def test_position_only_returns_the_position_assets():
    p = venture.position(_log(
        ('d', '103', 'ongoing-venture', 'wool', 'anchor', '36', 'tod', 'wend',
         '', ''),
        ('d', '103', 'ongoing-venture', 'venture_capital', 'anchor', '288',
         'gp', 'party', '', '')))
    assert [row[1] for row in p] == ['venture_capital']


def test_a_venture_filter_returns_just_that_ventures_rows():
    log = _log(
        ('d', '103', 'ongoing-venture', 'wool', 'anchor', '36', 'tod',
         'wend', '', ''),
        ('d', '103', 'wool-venture-1', 'venture_payable_holders', 'anchor',
         '229', 'gp', 'holders_six', '', ''))
    assert [row[1] for row in venture.holdings(log, 'ongoing-venture')] \
        == ['wool']
    assert venture.holdings(log, 'wool-venture-1') == []
    assert [row[1] for row in venture.position(log, 'wool-venture-1')] \
        == ['venture_payable_holders']


def test_an_unrecognised_venture_fails():
    problems = venture.check(_log(
        ('d', '103', 'not-a-real-venture', 'wool', 'anchor', '1', 'tod',
         'wend', '', '')))
    assert any('is not one of' in m for _s, m in problems), problems


def test_the_live_venture_log_reconciles():
    assert [m for s, m in venture.check() if s == 'FAIL'] == []


def test_a_free_typed_holder_is_refused():
    problems = venture.check(_log(
        ('d', '103', 'ongoing-venture', 'wool', 'anchor', '1', 'tod',
         'somebody made up', '', '')))
    assert any('is not a character' in m for _s, m in problems), problems


def test_holders_six_is_the_one_allowed_bucket():
    """Not a real person -- documented in venture_shares.tsv's own header,
    because the record never named the other two of six holders."""
    problems = venture.check(_log(
        ('d', '103', 'wool-venture-1', 'venture_payable_holders', 'anchor',
         '229', 'gp', 'holders_six', '', '')))
    assert problems == []


def test_a_venture_holding_never_appears_in_the_party_inventory():
    """The venture is NOT the party's property (wool_venture.md). Wool bought
    on the venture's own money (book=art7) must not also be an
    inventory_log.tsv row, or the same fact has two homes."""
    import inventory
    assert 'wool' not in inventory.state()


def test_the_live_split_matches_the_players_correction():
    """wool-venture-1 is closed except one flagged open tail; ongoing-venture
    holds the wool and owes only the party."""
    h1 = venture.holdings(venture='wool-venture-1')
    p1 = venture.position(venture='wool-venture-1')
    assert h1 == [], 'wool-venture-1 holds no physical stock any more'
    assert [row[1] for row in p1] == ['venture_payable_holders']

    h2 = venture.holdings(venture='ongoing-venture')
    p2 = venture.position(venture='ongoing-venture')
    assert [row[1] for row in h2] == ['wool']
    assert [row[1] for row in p2] == ['venture_capital']


def test_negative_shares_fail():
    problems = venture.check(slog=_slog(
        ('d', '16', 'Dave', 'anchor', '1', ''),
        ('d', '50', 'Dave', 'move', '-2', 'oversold')))
    assert any('negative shares' in m for _s, m in problems), problems
