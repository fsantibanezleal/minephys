"""T-007-042 (FR-007-17): Lane guards.

Public API under test (`minephys.planning`): `lane_cutoff_grades(grade_edges, tonnage, price, selling_cost, recovery,
processing_cost, mining_cost, fixed_cost, mine_capacity, plant_capacity, market_capacity, opportunity_cost=0)` (see
tests/unit/test_t_007_040_lane_cutoffs.py).
Expected: `minephys.InputError` naming the argument for grade edges that are not strictly increasing and non-negative, a negative
tonnage, an all-zero tonnage, a tonnage that does not match the bins (n edges give n - 1 bins), more than 100,000 bins, a capacity
<= 0, a recovery outside (0, 1], a negative cost (processing, mining, fixed, opportunity), a price not greater than the selling cost
and NaN or +-inf values; `minephys.InputTypeError` for non-numeric arguments.

Oracle: the hostile classes written in FR-007-17.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

NAN, INF = float("nan"), float("inf")


def _f():
    return importlib.import_module("minephys.planning").lane_cutoff_grades


def _errors():
    importlib.import_module("minephys.planning")
    import minephys

    return minephys.InputError, minephys.InputTypeError


BASE: dict[str, Any] = dict(
    grade_edges=np.array([0.0, 0.01, 0.02]),
    tonnage=np.array([1.0e6, 5.0e5]),
    price=10_000.0,
    selling_cost=2_000.0,
    recovery=0.9,
    processing_cost=2.0,
    mining_cost=0.5,
    fixed_cost=300.0,
    mine_capacity=100.0,
    plant_capacity=50.0,
    market_capacity=1.0,
    opportunity_cost=0.0,
)
POS = [0.0, -1.0, NAN, INF, -INF]
NONNEG = [-1e-9, -1.0, NAN, INF, -INF]
BAD_SCALARS: dict[str, list[float]] = {
    "price": [NAN, INF, -INF],
    "selling_cost": NONNEG,
    "recovery": [0.0, -0.1, 1.0000001, 2.0, NAN, INF],
    "processing_cost": NONNEG,
    "mining_cost": NONNEG,
    "fixed_cost": NONNEG,
    "mine_capacity": POS,
    "plant_capacity": POS,
    "market_capacity": POS,
    "opportunity_cost": NONNEG,
}
NON_NUMERIC: list[Any] = ["abc", "１.０", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a", "b"])]


def _call(**over: Any) -> Any:
    return _f()(**{**BASE, **over})


@pytest.mark.req("FR-007-17")
def test_fr_007_17_reference_call_is_valid() -> None:
    assert _call().optimum is not None


@pytest.mark.req("FR-007-17")
@pytest.mark.oracle("hand-calculation", "FR-007-17 hostile classes")
@pytest.mark.parametrize(("arg", "bad"), [(a, v) for a, vals in BAD_SCALARS.items() for v in vals], ids=lambda v: repr(v))
def test_fr_007_17_scalar_arguments(arg: str, bad: float) -> None:
    _f()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(**{arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-007-17")
@pytest.mark.parametrize(("price", "selling"), [(2000.0, 2000.0), (1000.0, 2000.0), (0.0, 0.0)])
def test_fr_007_17_price_must_exceed_the_selling_cost(price: float, selling: float) -> None:
    input_error, _ = _errors()
    _f()
    with pytest.raises(input_error) as exc:
        _call(price=price, selling_cost=selling)
    assert exc.value.argument in {"price", "selling_cost"}


@pytest.mark.req("FR-007-17")
@pytest.mark.parametrize(
    "edges",
    [
        np.array([0.0, 0.02, 0.01]),  # decreasing
        np.array([0.0, 0.01, 0.01]),  # tie
        np.array([-0.001, 0.01, 0.02]),  # negative
        np.array([0.0, NAN, 0.02]),
        np.array([0.0, 0.01, INF]),
        np.array([0.02, 0.01, 0.0]),
        np.array([0.0]),  # no bin
        np.array([]),
        np.array([[0.0, 0.01], [0.01, 0.02]]),  # 2-D
    ],
    ids=["decreasing", "tie", "negative", "nan", "inf", "reversed", "single-edge", "empty", "2d"],
)
def test_fr_007_17_grade_edges(edges: np.ndarray) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(grade_edges=edges, tonnage=np.array([1.0e6, 5.0e5]))
    assert exc.value.argument in {"grade_edges", "tonnage"}


@pytest.mark.req("FR-007-17")
@pytest.mark.parametrize(
    "tonnage",
    [
        np.array([1.0e6, -1.0]),
        np.array([-1e-9, 1.0e6]),
        np.array([0.0, 0.0]),  # all zero
        np.array([1.0e6]),  # fewer than the bins
        np.array([1.0e6, 5.0e5, 1.0]),  # more than the bins
        np.array([1.0e6, NAN]),
        np.array([1.0e6, INF]),
        np.array([]),
    ],
    ids=["negative", "tiny-negative", "all-zero", "short", "long", "nan", "inf", "empty"],
)
def test_fr_007_17_tonnage(tonnage: np.ndarray) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(tonnage=tonnage)
    assert exc.value.argument in {"tonnage", "grade_edges"}
    if tonnage.size == 2:
        assert exc.value.argument == "tonnage"


@pytest.mark.req("FR-007-17")
def test_fr_007_17_a_zero_tonnage_bin_is_allowed_but_not_all_zero() -> None:
    assert _call(tonnage=np.array([1.0e6, 0.0])).optimum is not None
    assert _call(tonnage=np.array([0.0, 1.0e6])).optimum is not None


@pytest.mark.req("FR-007-17")
def test_fr_007_17_more_than_100000_bins() -> None:
    input_error, _ = _errors()
    edges = np.linspace(0.0, 0.05, 100_002)  # 100,001 bins
    with pytest.raises(input_error) as exc:
        _call(grade_edges=edges, tonnage=np.ones(100_001))
    assert exc.value.argument in {"grade_edges", "tonnage"}
    ok = np.linspace(0.0, 0.05, 100_001)  # 100,000 bins: the cap itself is valid
    assert _call(grade_edges=ok, tonnage=np.ones(100_000)).optimum is not None


@pytest.mark.req("FR-007-17")
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_007_17_non_numeric_arguments(bad: Any) -> None:
    _f()
    _, input_type_error = _errors()
    for arg in BASE:
        with pytest.raises(input_type_error) as exc:
            _call(**{arg: bad})
        assert exc.value.argument == arg
