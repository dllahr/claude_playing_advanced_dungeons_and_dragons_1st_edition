"""tools/account.py: the Holt account is a sum of rows, never a stored figure."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import account                                                    # noqa: E402

HEADER = 'date\tday\taccount\tdelta\tkind\tnote\n'


def write(tmp_path, body):
    p = tmp_path / 'accounts.tsv'
    p.write_text('# c\n' + HEADER + body)
    return str(p)


def test_a_debt_falls_as_coin_tab_and_credit_come_off(tmp_path):
    p = write(tmp_path,
              'x\t135\tholt\t448.6\tdebt\tgoods and the old ale\n'
              'x\t135\tholt\t-50\tcoin\tin the till\n'
              'x\t135\tholt\t-1\tcredit\tthe keg\n'
              'x\t135\tholt\t-3\ttab\ta night at the Inn\n')
    assert account.balance('holt', p) == 394.6


def test_accounts_are_kept_apart(tmp_path):
    p = write(tmp_path, 'x\t1\tholt\t10\tdebt\t\nx\t1\tlyde\t-6\tdebt\t\n')
    assert account.balances(p) == {'holt': 10.0, 'lyde': -6.0}


def test_the_live_holt_account_reconciles():
    """Goods 420.6 plus the 28 gp of old ale, less the coin and the keg."""
    assert account.balance('holt') < 448.6
