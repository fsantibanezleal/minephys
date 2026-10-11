"""T-007-032 (FR-007-13, FR-007-14): infeasible schedules and NPV guards.

Public API under test (`minephys.planning`): `schedule_npv(periods, block_values, rate, arcs=None, tonnage=None,
capacities=None)` and `npv(cash_flows, rate, timing="end")` (see tests/unit/test_t_007_030_npv.py and
test_t_007_031_schedule_npv.py).
Expected
- FR-007-13: `minephys.InputError` naming the first violated arc (a block mined in a period earlier than a block it requires, or
  requiring a block that is not mined) or the first violated period (the mined tonnage exceeds its capacity); the message contains
  the indices of the arc or the period;
- FR-007-14: `minephys.InputError` naming the argument for NaN or +-inf, a rate <= -1, an empty cash-flow series, an unknown
  `timing` (exact, case-sensitive), period indices below -1 or non-integer, and mismatched lengths; `minephys.InputTypeError` for
  non-numeric arguments (non-integer periods may raise either class: the conventions call them type errors, FR-007-14 lists them
  with the domain errors).

Oracle: the hostile classes written in FR-007-13 and FR-007-14.
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


PERIODS = np.array([0, 0, 1, 1, 2, -1])
VALUES = np.array([10.0, 20.0, 30.0, -5.0, 40.0, 100.0])


@pytest.mark.req("FR-007-13")
@pytest.mark.oracle("hand-calculation", "FR-007-13: arc (i, j) is violated when i is mined earlier than j, or j is not mined")
@pytest.mark.parametrize(
    ("arcs", "first"),
    [
        (np.array([[0, 2]], dtype=np.int64), (0, 2)),  # block 0 (period 0) requires block 2 (period 1)
        (np.array([[4, 5]], dtype=np.int64), (4, 5)),  # block 4 (period 2) requires block 5 (not mined)
        (np.array([[2, 0], [1, 4], [0, 3]], dtype=np.int64), (1, 4)),  # the first violated arc in the array is reported
        (np.array([[3, 2], [3, 1], [3, 4]], dtype=np.int64), (3, 4)),  # block 3 (period 1) requires block 4 (period 2)
    ],
)
def test_fr_007_13_precedence_violations(arcs: np.ndarray, first: tuple[int, int]) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _p().schedule_npv(PERIODS, VALUES, 0.1, arcs=arcs)
    assert exc.value.argument == "arcs"
    message = str(exc.value)
    assert str(first[0]) in message and str(first[1]) in message


@pytest.mark.req("FR-007-13")
@pytest.mark.parametrize(
    ("capacities", "period"),
    [
        (np.array([1.0, 2.0, 1.0]), 0),  # period 0 mines 2 kg
        (np.array([2.0, 1.0, 1.0]), 1),  # period 1 mines 2 kg
        (np.array([2.0, 2.0, 0.5]), 2),  # period 2 mines 1 kg
        (np.array([1.0, 1.0, 0.5]), 0),  # the first violated period is reported
    ],
)
def test_fr_007_13_capacity_violations(capacities: np.ndarray, period: int) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _p().schedule_npv(PERIODS, VALUES, 0.1, tonnage=np.ones(6), capacities=capacities)
    assert exc.value.argument in {"capacities", "tonnage", "periods"}
    assert str(period) in str(exc.value)


@pytest.mark.req("FR-007-13")
def test_fr_007_13_unmined_blocks_do_not_count_against_capacity_and_the_cap_is_inclusive() -> None:
    p = _p()
    tonnage = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1e12])  # the huge block 5 is not mined
    res = p.schedule_npv(PERIODS, VALUES, 0.1, tonnage=tonnage, capacities=np.array([2.0, 2.0, 1.0]))  # equal to the capacity: fine
    assert res.npv > 0.0


@pytest.mark.req("FR-007-14")
@pytest.mark.oracle("hand-calculation", "FR-007-14 hostile classes")
@pytest.mark.parametrize("bad", [NAN, INF, -INF])
def test_fr_007_14_non_finite_values(bad: float) -> None:
    p = _p()
    input_error, _ = _errors()
    cf = np.array([10.0, bad, 5.0])
    with pytest.raises(input_error) as exc:
        p.npv(cf, 0.1)
    assert exc.value.argument == "cash_flows"
    with pytest.raises(input_error) as exc:
        p.npv(np.array([1.0, 2.0]), bad)
    assert exc.value.argument == "rate"
    values = VALUES.copy()
    values[2] = bad
    with pytest.raises(input_error) as exc:
        p.schedule_npv(PERIODS, values, 0.1)
    assert exc.value.argument == "block_values"
    with pytest.raises(input_error) as exc:
        p.schedule_npv(PERIODS, VALUES, bad)
    assert exc.value.argument == "rate"


@pytest.mark.req("FR-007-14")
@pytest.mark.parametrize("rate", [-1.0, -1.0000001, -2.0, -100.0])
def test_fr_007_14_rates_at_or_below_minus_one(rate: float) -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        p.npv(np.array([1.0, 2.0]), rate)
    assert exc.value.argument == "rate"
    with pytest.raises(input_error) as exc:
        p.schedule_npv(PERIODS, VALUES, rate)
    assert exc.value.argument == "rate"


@pytest.mark.req("FR-007-14")
def test_fr_007_14_empty_series_and_unknown_timing() -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        p.npv(np.array([]), 0.1)
    assert exc.value.argument == "cash_flows"
    for timing in ("middle", "End", "START", "", "end ", "mid"):
        with pytest.raises(input_error) as exc:
            p.npv(np.array([1.0, 2.0]), 0.1, timing=timing)
        assert exc.value.argument == "timing"
        assert "end" in str(exc.value) and "start" in str(exc.value)  # the allowed values are listed (FR-000-15)


@pytest.mark.req("FR-007-14")
@pytest.mark.parametrize("bad_period", [-2, -100])
def test_fr_007_14_periods_below_minus_one(bad_period: int) -> None:
    input_error, _ = _errors()
    periods = PERIODS.copy()
    periods[1] = bad_period
    with pytest.raises(input_error) as exc:
        _p().schedule_npv(periods, VALUES, 0.1)
    assert exc.value.argument == "periods"


@pytest.mark.req("FR-007-14")
@pytest.mark.parametrize("periods", [np.array([0.0, 0.0, 1.0, 1.0, 2.0, -1.0]), np.array([0.5, 0, 1, 1, 2, -1]), np.array(["0", "1", "1", "1", "2", "-1"]), np.array([True, False, True, True, False, False])], ids=["float", "fraction", "str", "bool"])
def test_fr_007_14_non_integer_periods(periods: np.ndarray) -> None:
    input_error, input_type_error = _errors()
    with pytest.raises((input_error, input_type_error)) as exc:
        _p().schedule_npv(periods, VALUES, 0.1)
    assert exc.value.argument == "periods"


@pytest.mark.req("FR-007-14")
def test_fr_007_14_mismatched_lengths() -> None:
    p = _p()
    input_error, _ = _errors()
    for periods, values in ((PERIODS[:5], VALUES), (PERIODS, VALUES[:5])):
        with pytest.raises(input_error) as exc:
            p.schedule_npv(periods, values, 0.1)
        assert exc.value.argument in {"periods", "block_values"}
    with pytest.raises(input_error) as exc:
        p.schedule_npv(PERIODS, VALUES, 0.1, tonnage=np.ones(5), capacities=np.array([5.0, 5.0, 5.0]))
    assert exc.value.argument in {"tonnage", "periods"}
    with pytest.raises(input_error) as exc:
        p.npv(np.ones((2, 2)), 0.1)  # a 2-D series is not a cash-flow vector
    assert exc.value.argument == "cash_flows"


@pytest.mark.req("FR-007-14")
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a", "b"])], ids=lambda v: type(v).__name__)
def test_fr_007_14_non_numeric_arguments(bad: Any) -> None:
    p = _p()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        p.npv(bad, 0.1)
    assert exc.value.argument == "cash_flows"
    with pytest.raises(input_type_error) as exc:
        p.npv(np.array([1.0, 2.0]), bad)
    assert exc.value.argument == "rate"
    with pytest.raises(input_type_error) as exc:
        p.schedule_npv(PERIODS, bad, 0.1)
    assert exc.value.argument == "block_values"
