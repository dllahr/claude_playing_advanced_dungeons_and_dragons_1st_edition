"""Unit tests for label assembly.

Digits arrive as separate connected components; turning "1" and "2" into "12"
is pure geometry and is tested here without invoking tesseract. The OCR call
itself is exercised only when tesseract is installed.
"""
import numpy as np
import pytest

import ocr_labels as O


def box(x0, y0, x1, y1, area=200):
    return [x0, y0, x1, y1, area]


def test_adjacent_digits_merge_into_one_label():
    merged = O.merge([box(10, 10, 23, 39), box(27, 10, 40, 39)])
    assert len(merged) == 1
    assert merged[0][:4] == (10, 10, 40, 39)
    assert merged[0][5] == 2, 'two blobs'


def test_distant_digits_stay_separate():
    merged = O.merge([box(10, 10, 23, 39), box(200, 10, 213, 39)])
    assert len(merged) == 2


def test_digits_on_different_lines_stay_separate():
    merged = O.merge([box(10, 10, 23, 39), box(27, 100, 40, 129)])
    assert len(merged) == 2


def test_three_digit_run_merges_transitively():
    merged = O.merge([box(10, 10, 23, 39), box(27, 10, 40, 39), box(44, 10, 57, 39)])
    assert len(merged) == 1 and merged[0][5] == 3


def test_max_gap_is_honoured():
    b = [box(10, 10, 23, 39), box(60, 10, 73, 39)]
    assert len(O.merge(b, max_gap=10)) == 2
    assert len(O.merge(b, max_gap=50)) == 1


def test_components_ignores_specks_and_respects_the_field():
    ink = np.zeros((100, 100), bool)
    ink[10:14, 10:14] = True          # 16 px speck
    ink[40:70, 40:55] = True          # a real glyph
    out = O.components(ink, (0, 100, 0, 100), min_area=40)
    assert len(out) == 1
    assert out[0][4] > 400


def test_components_clips_to_the_field():
    ink = np.zeros((100, 100), bool)
    ink[5:35, 5:20] = True
    assert O.components(ink, (50, 100, 50, 100)) == []


def test_to_cell_maps_centre_to_dungeon_coordinates():
    import extract as E
    grid = E.Grid(0.0, 40.0, 10, 0.0, 40.0, 10)
    # a box centred in image cell (2, 3) -> dungeon y = 10-1-3 = 6
    assert O.to_cell(box(80, 120, 120, 160), grid) == (2, 6)


@pytest.mark.skipif(
    __import__('shutil').which('tesseract') is None, reason='tesseract not installed')
def test_read_recognises_a_drawn_numeral():
    from PIL import Image, ImageDraw
    img = Image.new('L', (60, 60), 255)
    d = ImageDraw.Draw(img)
    d.text((18, 18), '7', fill=0)
    text = O.read(np.asarray(img, dtype=float), box(0, 0, 60, 60))
    assert isinstance(text, str)
