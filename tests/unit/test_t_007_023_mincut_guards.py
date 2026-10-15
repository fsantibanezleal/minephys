"""T-007-023 (FR-007-07): min-cut, nested-pit and precedence guards.

Public API under test (`minephys.planning`): `ultimate_pit_mincut(values, arcs)`, `nested_pits(tonnage, grade, price,
selling_cost, recovery, processing_cost, mining_cost, arcs, revenue_factors)`, `regular_grid_precedence(shape, pattern="1-5")`.
Expected: `minephys.InputError` naming the argument for NaN or +-inf values, arcs that are not an (m, 2) array, an arc index out of
range, a self-arc, more than 100,000 blocks, more than 2,000,000 arcs, an empty block set, an unknown `pattern`, a non-positive
grid dimension, and revenue factors that are negative or non-finite; `minephys.InputTypeError` for non-numeric values and for
non-integer arcs (spec 007 conventions: "non-integer arcs or periods" are type errors).

Oracle: the hostile classes written in FR-007-07.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

NAN, INF = float("nan"), float("inf")


def _p():
    return importlib.import_module("minephys.planning")


def _errors():
    importlib.import_module("minephys.planning")
    import minephys

    return minephys.InputError, minephys.InputTypeError


VALUES = np.array([-1.0, -1.0, -1.0, 5.0])
ARCS = np.array([[3, 0], [3, 1], [3, 2]], dtype=np.int64)
NO_ARCS = np.empty((0, 2), dtype=np.int64)
NESTED = dict(
    tonnage=np.ones(4),
    grade=np.array([0.0, 0.0, 0.0, 1.0]),
    price=7.0,
    selling_cost=1.0,
    recovery=1.0,
    processing_cost=0.0,
    mining_cost=1.0,
    arcs=ARCS,
    revenue_factors=np.array([0.5, 1.0]),
)


@pytest.mark.req("FR-007-07")
def test_fr_007_07_reference_calls_are_valid() -> None:
    p = _p()
    assert np.asarray(p.ultimate_pit_mincut(VALUES, ARCS).mask).shape == (4,)
    assert len(list(p.nested_pits(**NESTED))) == 2
    assert p.regular_grid_precedence((3, 3, 2)).shape == (33, 2)


@pytest.mark.req("FR-007-07")
@pytest.mark.oracle("hand-calculation", "FR-007-07 hostile classes")
@pytest.mark.parametrize("bad", [NAN, INF, -INF])
def test_fr_007_07_non_finite_values(bad: float) -> None:
    p = _p()
    input_error, _ = _errors()
    values = VALUES.copy()
    values[1] = bad
    with pytest.raises(input_error) as exc:
        p.ultimate_pit_mincut(values, ARCS)
    assert exc.value.argument == "values"
    for name in ("tonnage", "grade"):
        arr = NESTED[name].copy()
        arr[1] = bad
        with pytest.raises(input_error) as exc:
            p.nested_pits(**{**NESTED, name: arr})
        assert exc.value.argument == name


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize(
    "arcs",
    [
        np.array([3, 0, 3, 1]),  # 1-D
        np.array([[3, 0, 1], [3, 1, 1]]),  # three columns
        np.array([[[3, 0]]]),  # 3-D
        np.array([[4, 0]]),  # index equal to n
        np.array([[3, 17]]),  # index beyond n
        np.array([[-1, 0]]),  # negative index
        np.array([[3, -2]]),
        np.array([[2, 2]]),  # self-arc
        np.array([[3, 0], [1, 1]]),  # one self-arc among valid arcs
    ],
    ids=["1d", "3cols", "3d", "idx-n", "idx-big", "neg-first", "neg-second", "self", "self-among"],
)
def test_fr_007_07_bad_arcs(arcs: np.ndarray) -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        p.ultimate_pit_mincut(VALUES, arcs)
    assert exc.value.argument == "arcs"
    with pytest.raises(input_error) as exc:
        p.nested_pits(**{**NESTED, "arcs": arcs})
    assert exc.value.argument == "arcs"


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize("arcs", [np.array([[3.0, 0.0]]), np.array([[3.5, 0.0]]), np.array([["3", "0"]]), np.array([[True, False]])], ids=["float", "fraction", "str", "bool"])
def test_fr_007_07_non_integer_arcs_are_rejected(arcs: np.ndarray) -> None:
    """FR-007-07 calls them "not an (m, 2) integer array" (InputError); the spec conventions call non-integer arcs a type error."""
    input_error, input_type_error = _errors()
    with pytest.raises((input_error, input_type_error)) as exc:
        _p().ultimate_pit_mincut(VALUES, arcs)
    assert exc.value.argument == "arcs"


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a", "b"])], ids=lambda v: type(v).__name__)
def test_fr_007_07_non_numeric_values(bad: Any) -> None:
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        _p().ultimate_pit_mincut(bad, ARCS)
    assert exc.value.argument == "values"


@pytest.mark.req("FR-007-07")
def test_fr_007_07_empty_and_oversized_block_sets() -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        p.ultimate_pit_mincut(np.empty(0), NO_ARCS)
    assert exc.value.argument == "values"
    with pytest.raises(input_error) as exc:
        p.ultimate_pit_mincut(np.zeros(100_001), NO_ARCS)
    assert exc.value.argument == "values"
    with pytest.raises(input_error):
        p.ultimate_pit_mincut(np.zeros((2, 2)), NO_ARCS)  # a 2-D value array is not a block list
    # the cap itself is valid
    res = p.ultimate_pit_mincut(np.r_[np.ones(50_000), -np.ones(50_000)], NO_ARCS)
    assert np.asarray(res.mask).shape == (100_000,) and float(res.value) == 50_000.0


@pytest.mark.req("FR-007-07")
def test_fr_007_07_too_many_arcs() -> None:
    p = _p()
    input_error, _ = _errors()
    arcs = np.tile(np.array([[1, 0]], dtype=np.int64), (2_000_001, 1))
    with pytest.raises(input_error) as exc:
        p.ultimate_pit_mincut(np.array([1.0, -1.0, 0.0]), arcs)
    assert exc.value.argument == "arcs"


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize("factors", [np.array([-1e-9, 1.0]), np.array([0.5, -2.0]), np.array([NAN]), np.array([0.5, INF]), np.array([-INF])])
def test_fr_007_07_bad_revenue_factors(factors: np.ndarray) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _p().nested_pits(**{**NESTED, "revenue_factors": factors})
    assert exc.value.argument == "revenue_factors"


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize("shape", [(0, 3, 3), (3, 0, 3), (3, 3, 0), (-1, 3, 3), (3, -2, 3), (3, 3, -5), (3, 3), (3, 3, 3, 3), ()])
def test_fr_007_07_bad_grid_shapes(shape: tuple[int, ...]) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _p().regular_grid_precedence(shape)
    assert exc.value.argument == "shape"


@pytest.mark.req("FR-007-07")
@pytest.mark.parametrize("pattern", ["1-3", "1-5 ", "1-9\n", "", "1_5", "15", "1-5-9", "5", "ONE-FIVE"])
def test_fr_007_07_unknown_pattern(pattern: str) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _p().regular_grid_precedence((3, 3, 2), pattern)
    assert exc.value.argument == "pattern"
    assert "1-5" in str(exc.value) and "1-9" in str(exc.value)  # the allowed values are listed (FR-000-15)


@pytest.mark.req("FR-007-07")
def test_fr_007_07_grids_over_the_block_cap() -> None:
    input_error, _ = _errors()
    for shape in ((101, 100, 10), (1000, 100, 2), (50, 50, 41), (400, 400, 1)):  # 101,000 / 200,000 / 102,500 / 160,000 blocks
        with pytest.raises(input_error) as exc:
            _p().regular_grid_precedence(shape)
        assert exc.value.argument == "shape"
