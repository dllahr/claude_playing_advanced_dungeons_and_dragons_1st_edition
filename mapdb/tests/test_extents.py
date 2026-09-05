"""Room-versus-corridor separation, and the size cross-check.

Nothing in the image says where a room ends and a corridor begins -- both are
plain white. The separating property is that a corridor never contains a 2x2
block of open floor and a room does, which is exact on a grid and needs no
threshold.
"""
import pytest

import extents as X


def opener(open_edges):
    """is_open() over an explicit set of open boundaries."""
    return X.opener({e: 'open' for e in open_edges})


def grid_open(cells):
    """Every boundary between orthogonally adjacent cells is open."""
    edges = set()
    for (x, y) in cells:
        if (x + 1, y) in cells:
            edges.add((x, y, 'V'))
        if (x, y + 1) in cells:
            edges.add((x, y, 'H'))
    return opener(edges)


def test_a_one_wide_corridor_has_no_wide_squares():
    walk = {(x, 0) for x in range(6)}
    assert X.wide_cells(walk, grid_open(walk)) == set()


def test_a_two_by_two_room_is_entirely_wide():
    walk = {(0, 0), (1, 0), (0, 1), (1, 1)}
    assert X.wide_cells(walk, grid_open(walk)) == walk


def test_a_corridor_junction_is_still_narrow():
    """A T of 1-wide corridors gives cells three open neighbours but no block."""
    walk = {(x, 0) for x in range(5)} | {(2, 1), (2, 2)}
    assert X.wide_cells(walk, grid_open(walk)) == set()


def test_a_room_with_a_corridor_attached_splits():
    room = {(x, y) for x in range(3) for y in range(3)}
    corridor = {(3, 1), (4, 1), (5, 1)}
    walk = room | corridor
    wide = X.wide_cells(walk, grid_open(walk))
    assert wide == room
    assert not (wide & corridor)


def test_a_wall_inside_the_block_prevents_it():
    """Two rooms touching across a wall must not merge into one wide area."""
    walk = {(0, 0), (1, 0), (0, 1), (1, 1)}
    is_open = opener({(0, 0, 'H'), (1, 0, 'H'), (0, 1, 'V')})   # (0,0)-(1,0) closed
    assert X.wide_cells(walk, is_open) == set()


def test_a_door_does_not_let_a_room_grow_through_it():
    """Doors are ways through, but they are also boundaries between spaces."""
    is_open = X.opener({(0, 0, 'V'): 'door'})
    assert not is_open((0, 0), (1, 0))


def test_growth_splits_a_shared_area_between_its_seeds():
    walk = {(x, y) for x in range(6) for y in range(2)}
    is_open = grid_open(walk)
    wide = X.wide_cells(walk, is_open)
    ext, spare = X.grow(walk, wide, {'1': {(0, 0)}, '2': {(5, 0)}}, is_open)
    assert spare == set()
    assert len(ext['1']) == len(ext['2']) == 6
    assert (0, 1) in ext['1'] and (5, 1) in ext['2']


def test_a_label_in_a_narrow_alcove_keeps_its_own_square():
    walk = {(x, 0) for x in range(4)}
    is_open = grid_open(walk)
    ext, spare = X.grow(walk, X.wide_cells(walk, is_open), {'7': {(2, 0)}}, is_open)
    assert ext['7'] == {(2, 0)}


def test_wide_areas_with_no_label_are_reported_not_claimed():
    walk = {(0, 0), (1, 0), (0, 1), (1, 1)}
    is_open = grid_open(walk)
    ext, spare = X.grow(walk, X.wide_cells(walk, is_open), {}, is_open)
    assert ext == {} and spare == walk


@pytest.mark.parametrize('number,expect', [
    ('12', '12'), ('1', '1'), ('1A', '1'), ('2B', '2'), ('C', 'C')])
def test_sub_locations_fold_into_their_area(number, expect):
    assert X.base_area(number) == expect


def test_stated_squares_reads_a_room_dimension():
    assert X.stated_squares("This 20' by 20' room is used for storage") == 4
    assert X.stated_squares("a damp and vaulted chamber 30' square") == 9
    assert X.stated_squares("The room is 50' by 30' overall") == 15


def test_stated_squares_ignores_the_size_of_the_furniture():
    """B1 sizes area 37's floor mats before it ever sizes the room."""
    text = ("five heavy woven mats lying atop each other to form a sort of "
            "floor cushion measuring 20' by 20'.")
    assert X.stated_squares(text) is None


def test_stated_squares_is_none_when_no_size_is_given():
    assert X.stated_squares('There are several iron bars here.') is None
    assert X.stated_squares('') is None
    assert X.stated_squares(None) is None


def test_check_dimensions_flags_only_real_disagreement():
    ext = {'17': {(0, 0), (1, 0)}, '18': {(0, 0)} | {(i, 1) for i in range(3)}}
    rows = X.check_dimensions(ext, {'17': 4, '18': 4}, tol=0.35)
    got = {a: ok for a, _, _, ok in rows}
    assert got['17'] is False, '2 squares against a stated 4 is a disagreement'
    assert got['18'] is True, '4 squares against a stated 4 agrees'
