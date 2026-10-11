"""T-007-020 (FR-007-03): regular-grid precedence arcs and their counts.

Expected public API (`minephys.planning`):
    regular_grid_precedence(shape, pattern="1-5") -> int64 array of shape (m, 2) of arcs (i, j), "mining block i requires block j"
for an (nx, ny, nz) grid whose blocks are numbered in C order, index = (x * ny + y) * nz + z, with level 0 at the top: each block
below the top level (z >= 1) is linked to the in-grid blocks one level up (z - 1) at the offsets {(0, 0), (+-1, 0), (0, +-1)} for
"1-5" or |dx|, |dy| <= 1 for "1-9". The number of arcs is (nz - 1) [nx ny + 2 (nx - 1) ny + 2 nx (ny - 1)] for "1-5" and
(nz - 1) (3 nx - 2)(3 ny - 2) for "1-9". The order of the rows is not specified (the tests compare sets).

Oracles
- hand counts (plan 007): a 3 x 3 x 2 grid has 33 "1-5" arcs and 49 "1-9" arcs;
- the explicit arc list of a 2 x 2 x 2 grid written out by hand below (index = 4 x + 2 y + z);
- the arc-count formulas on a range of shapes, and a brute-force enumeration of the offsets written in the test.
"""

from __future__ import annotations

import importlib
import itertools

import numpy as np
import pytest


def _f():
    return importlib.import_module("minephys.planning").regular_grid_precedence


def brute(nx: int, ny: int, nz: int, pattern: str) -> set[tuple[int, int]]:
    offsets = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)] if pattern == "1-5" else list(itertools.product((-1, 0, 1), repeat=2))
    idx = lambda x, y, z: (x * ny + y) * nz + z  # noqa: E731
    arcs = set()
    for x, y, z in itertools.product(range(nx), range(ny), range(nz)):
        if z == 0:
            continue
        for dx, dy in offsets:
            if 0 <= x + dx < nx and 0 <= y + dy < ny:
                arcs.add((idx(x, y, z), idx(x + dx, y + dy, z - 1)))
    return arcs


def as_set(arcs: np.ndarray) -> set[tuple[int, int]]:
    return {(int(i), int(j)) for i, j in arcs}


@pytest.mark.req("FR-007-03")
@pytest.mark.oracle("hand-calculation", "plan 007: 3 x 3 x 2 grid -> 33 arcs ('1-5'), 49 arcs ('1-9')")
def test_fr_007_03_hand_counts() -> None:
    f = _f()
    a5, a9 = f((3, 3, 2), "1-5"), f((3, 3, 2), "1-9")
    assert a5.shape == (33, 2) and a9.shape == (49, 2)
    assert a5.dtype == np.int64 and a9.dtype == np.int64
    assert f((3, 3, 2)).shape == (33, 2)  # "1-5" is the default pattern
    assert len(as_set(a5)) == 33 and len(as_set(a9)) == 49  # no duplicates


@pytest.mark.req("FR-007-03")
@pytest.mark.oracle("hand-calculation", "explicit arc list of a 2 x 2 x 2 grid, index = 4x + 2y + z")
def test_fr_007_03_explicit_two_by_two_by_two() -> None:
    f = _f()
    # level-1 blocks: (0,0,1)=1, (0,1,1)=3, (1,0,1)=5, (1,1,1)=7; level-0 blocks: (0,0,0)=0, (0,1,0)=2, (1,0,0)=4, (1,1,0)=6
    expected_15 = {
        (1, 0), (1, 4), (1, 2),  # block 1 requires 0 (above), 4 (x + 1), 2 (y + 1)
        (3, 2), (3, 6), (3, 0),
        (5, 4), (5, 0), (5, 6),
        (7, 6), (7, 2), (7, 4),
    }
    assert as_set(f((2, 2, 2), "1-5")) == expected_15
    expected_19 = {(i, j) for i in (1, 3, 5, 7) for j in (0, 2, 4, 6)}  # a 2 x 2 level: every block sees all four above
    assert as_set(f((2, 2, 2), "1-9")) == expected_19 and len(expected_19) == 16


@pytest.mark.req("FR-007-03")
@pytest.mark.oracle("analytical", "arc-count formulas of FR-007-03 and a brute-force enumeration of the offsets")
@pytest.mark.parametrize("shape", [(1, 1, 1), (1, 1, 5), (2, 1, 3), (1, 4, 2), (3, 3, 2), (4, 5, 3), (6, 6, 6), (2, 7, 4), (5, 2, 9)])
def test_fr_007_03_counts_and_enumeration(shape: tuple[int, int, int]) -> None:
    f = _f()
    nx, ny, nz = shape
    a5, a9 = f(shape, "1-5"), f(shape, "1-9")
    assert a5.shape[0] == (nz - 1) * (nx * ny + 2 * (nx - 1) * ny + 2 * nx * (ny - 1))
    assert a9.shape[0] == (nz - 1) * (3 * nx - 2) * (3 * ny - 2)
    assert as_set(a5) == brute(nx, ny, nz, "1-5") and as_set(a9) == brute(nx, ny, nz, "1-9")
    assert a5.shape[1] == 2 and a5.dtype == np.int64


@pytest.mark.req("FR-007-03")
def test_fr_007_03_a_single_level_has_no_arcs_and_arcs_point_one_level_up() -> None:
    f = _f()
    flat = f((4, 4, 1))
    assert flat.shape == (0, 2) and flat.dtype == np.int64
    arcs = f((5, 4, 6), "1-9")
    z = lambda i: i % 6  # noqa: E731  level = z for index = (x * ny + y) * nz + z
    assert np.all(z(arcs[:, 0]) == z(arcs[:, 1]) + 1)
    assert arcs.min() >= 0 and arcs.max() < 5 * 4 * 6
    assert np.all(arcs[:, 0] != arcs[:, 1])  # no self-arcs


@pytest.mark.req("FR-007-03")
def test_fr_007_03_the_largest_regular_grid_is_available() -> None:
    f = _f()
    arcs = f((100, 100, 10), "1-5")  # 100,000 blocks, the size cap
    assert arcs.shape[0] == 9 * (100 * 100 + 2 * 99 * 100 + 2 * 100 * 99)
    assert arcs.dtype == np.int64 and arcs.max() < 100_000
