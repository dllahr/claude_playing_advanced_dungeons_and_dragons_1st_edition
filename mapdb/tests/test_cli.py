"""Functional tests: the command-line tools, driven as a user would drive them."""
import os
import sqlite3
import subprocess
import sys

import pytest

import build
import dmap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, script)] + list(args),
                       capture_output=True, text=True, cwd=ROOT)
    return p


@pytest.mark.parametrize('script', ['build.py', 'dmap.py', 'review.py'])
def test_help_works_and_documents_options(script):
    p = run(script, '--help')
    assert p.returncode == 0
    assert 'usage:' in p.stdout
    assert len(p.stdout) > 300, 'options should carry real help text'


def test_dmap_subcommands_are_all_documented():
    p = run('dmap.py', '--help')
    for cmd in ('render', 'stats', 'lowconf', 'check', 'reach'):
        assert cmd in p.stdout


def test_dmap_requires_a_subcommand():
    assert run('dmap.py').returncode != 0


def test_build_rejects_unknown_option():
    assert run('build.py', '--nonsense').returncode != 0


def test_build_parser_defaults_are_sane():
    args = build.build_parser().parse_args([])
    assert args.dpi == 200
    assert args.t_solid < args.t_open
    assert args.t_solid <= 0.1, 'a quarter-open diagonal square must not be solid'


def test_build_parser_accepts_threshold_overrides():
    args = build.build_parser().parse_args(['--t-solid', '0.2', '--t-open', '0.6'])
    assert (args.t_solid, args.t_open) == (0.2, 0.6)


def test_render_window_is_respected(dmg_db):
    full = dmap.render(dmg_db, 1)
    win = dmap.render(dmg_db, 1, (7, 38, 23, 45))
    assert len(win) < len(full)
    assert win.count('\n') < full.count('\n')
    # the ruler should start at the window's first column
    assert win.splitlines()[0].split()[0] == '7'


def test_render_marks_the_three_terrain_classes(dmg_db):
    art = dmap.render(dmg_db, 1)
    assert '#' in art and ':' in art


def test_stats_reports_totals(dmg_db):
    out = dmap.stats(dmg_db, 1)
    assert 'cells  total=1680' in out
    assert 'edges  total=3360' in out


def test_lowconf_respects_max_conf(dmg_db):
    strict = dmap.lowconf(dmg_db, 1, limit=500, max_conf=3)
    loose = dmap.lowconf(dmg_db, 1, limit=500, max_conf=8)
    assert len(loose.splitlines()) > len(strict.splitlines())


def test_lowconf_respects_limit(dmg_db):
    assert len(dmap.lowconf(dmg_db, 1, limit=5).splitlines()) == 6  # + header


def test_check_reports_no_contradictions(dmg_db):
    assert 'no contradictions found' in dmap.check(dmg_db, 1)


def test_reach_runs_and_reports_a_count(dmg_db):
    out = dmap.reachable(dmg_db, 1, from_room='1')
    assert 'walkable' in out[0] and 'UNREACHED' in out[0]


def test_review_sheet_is_written(tmp_path, dmg_db, dmg_pdf):
    import review
    png = str(tmp_path / 'sheet.png')
    idx = str(tmp_path / 'index.txt')
    n, index = review.sheet(dmg_db, 1, dmg_pdf, 95, 200, 3, 200, 4, png, idx)
    assert os.path.exists(png) and os.path.exists(idx)
    assert n > 0 and len(index) > 0
    assert all(line.startswith('#') for line in index)


def test_review_clusters_group_adjacent_cells():
    import review
    g = review.clusters([(1, 1), (1, 2), (5, 5)], 10, 10)
    assert [len(c) for c in g] == [2, 1]


def test_review_clusters_ignore_out_of_range():
    import review
    assert review.clusters([(99, 99)], 10, 10) == []
