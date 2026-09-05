"""Shared fixtures.

The real-PDF fixtures are session-scoped because rendering and masking the DMG
page takes a couple of seconds and every integration test wants the same one.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

DMG_PDF = os.path.join(
    ROOT, '..', 'manuals',
    "tsr02011 - Advanced Dungeons & Dragons (Ad&D) 1St Ed - Dungeon Master'S Guide.pdf")
DMG_PAGE = 95

needs_pdf = pytest.mark.skipif(
    not os.path.exists(DMG_PDF), reason='DMG pdf not available')


@pytest.fixture(scope='session')
def repo_root():
    return ROOT


@pytest.fixture(scope='session')
def dmg_pdf():
    if not os.path.exists(DMG_PDF):
        pytest.skip('DMG pdf not available')
    return DMG_PDF


@pytest.fixture(scope='session')
def dmg_render(dmg_pdf):
    import extract as E
    grey, rgb = E.render(dmg_pdf, DMG_PAGE, 200)
    return grey, rgb


@pytest.fixture(scope='session')
def dmg_grid(dmg_render):
    import extract as E
    grey, _ = dmg_render
    field = E.find_field(grey)
    return field, E.fit_grid(grey, field)


@pytest.fixture(scope='session')
def dmg_masks(dmg_render):
    import extract as E
    grey, _ = dmg_render
    return E.rock_mask(grey)


@pytest.fixture(scope='session')
def dmg_db(tmp_path_factory, dmg_pdf):
    """Build a database from the real page once, in a temp dir."""
    import build
    d = tmp_path_factory.mktemp('dmgdb')
    db = str(d / 'dmg.sqlite')
    build.main(['--pdf', dmg_pdf, '--page', str(DMG_PAGE), '--db', db,
                '--schema', os.path.join(ROOT, 'schema.sql'),
                '--key', 'dmg_key',
                '--corrections', os.path.join(ROOT, 'corrections.tsv'),
                '--images', str(d / 'images'), '--quiet'])
    return db


@pytest.fixture
def synth():
    import synth as S
    return S


@pytest.fixture
def simple(synth):
    m = synth.simple_map()
    return m, m.render(), m.truth()
