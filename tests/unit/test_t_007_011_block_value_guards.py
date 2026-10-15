"""T-007-011 (FR-007-08): block-value guards.

Public API under test (`minephys.planning`): `block_economic_value(tonnage, grade, price, selling_cost, recovery,
processing_cost, mining_cost)` and `breakeven_cutoff_grade(processing_cost, price, selling_cost, recovery)`.
Expected: `minephys.InputError` naming the argument for NaN or +-inf, a negative tonnage or cost, a grade outside [0, 1], a
recovery outside (0, 1] and a price that is not greater than the selling cost (the error names `price` or `selling_cost`);
`minephys.InputTypeError` for non-numeric arguments.

Oracle: the hostile classes written in FR-007-08.
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


BV_BASE = {
    "tonnage": 1e6,
    "grade": 0.01,
    "price": 10.0,
    "selling_cost": 2.0,
    "recovery": 0.85,
    "processing_cost": 0.01,
    "mining_cost": 0.002,
}
BE_BASE = {"processing_cost": 0.01, "price": 10.0, "selling_cost": 2.0, "recovery": 0.85}
NONNEG = [-1e-9, -1.0, NAN, INF, -INF]
BAD = {
    "tonnage": NONNEG,
    "grade": [-1e-9, 1.0000001, 2.0, NAN, INF, -INF],
    "price": [NAN, INF, -INF],
    "selling_cost": [-1e-9, -1.0, NAN, INF, -INF],
    "recovery": [0.0, -0.1, 1.0000001, 2.0, NAN, INF],
    "processing_cost": NONNEG,
    "mining_cost": NONNEG,
}
NON_NUMERIC: list[Any] = ["abc", "１.０", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a"])]


def _cases() -> list[Any]:
    out = []
    for fn, base in (("block_economic_value", BV_BASE), ("breakeven_cutoff_grade", BE_BASE)):
        for arg in base:
            for bad in BAD[arg]:
                out.append(pytest.param(fn, base, arg, bad, id=f"{fn}-{arg}-{bad!r}"))
    return out


@pytest.mark.req("FR-007-08")
@pytest.mark.oracle("hand-calculation", "FR-007-08 hostile classes")
@pytest.mark.parametrize(("fn", "base", "arg", "bad"), _cases())
def test_fr_007_08_out_of_domain_and_non_finite_values(fn: str, base: dict[str, Any], arg: str, bad: float) -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(p, fn)(**{**base, arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-007-08")
@pytest.mark.parametrize("fn", ["block_economic_value", "breakeven_cutoff_grade"])
@pytest.mark.parametrize(("price", "selling"), [(2.0, 2.0), (2.0, 3.0), (0.0, 0.0), (-1.0, -2.0)])
def test_fr_007_08_price_must_exceed_the_selling_cost(fn: str, price: float, selling: float) -> None:
    p = _p()
    input_error, _ = _errors()
    base = BV_BASE if fn == "block_economic_value" else BE_BASE
    with pytest.raises(input_error) as exc:
        getattr(p, fn)(**{**base, "price": price, "selling_cost": selling})
    assert exc.value.argument in {"price", "selling_cost"}


@pytest.mark.req("FR-007-08")
@pytest.mark.parametrize("fn", ["block_economic_value", "breakeven_cutoff_grade"])
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_007_08_non_numeric_arguments(fn: str, bad: Any) -> None:
    p = _p()
    _, input_type_error = _errors()
    base = BV_BASE if fn == "block_economic_value" else BE_BASE
    for arg in base:
        with pytest.raises(input_type_error) as exc:
            getattr(p, fn)(**{**base, arg: bad})
        assert exc.value.argument == arg


@pytest.mark.req("FR-007-08")
def test_fr_007_08_arrays_with_one_bad_element_and_valid_boundaries() -> None:
    p = _p()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        p.block_economic_value(np.array([1e6, -5.0]), 0.01, 10.0, 2.0, 0.85, 0.01, 0.002)
    assert exc.value.argument == "tonnage"
    with pytest.raises(input_error) as exc:
        p.block_economic_value(1e6, np.array([0.01, 1.2]), 10.0, 2.0, 0.85, 0.01, 0.002)
    assert exc.value.argument == "grade"
    with pytest.raises(input_error) as exc:  # unbroadcastable shapes name the arguments
        p.block_economic_value(np.ones(3), np.full(2, 0.01), 10.0, 2.0, 0.85, 0.01, 0.002)
    assert "tonnage" in str(exc.value) and "grade" in str(exc.value)
    # the boundaries of the domain are valid: zero costs, grade 0 and 1, recovery 1, zero selling cost
    out = p.block_economic_value(1.0, 1.0, 10.0, 0.0, 1.0, 0.0, 0.0)
    assert out.value == pytest.approx(10.0)
    assert p.block_economic_value(1.0, 0.0, 10.0, 0.0, 1.0, 0.0, 0.0).value == 0.0
    assert p.breakeven_cutoff_grade(0.0, 10.0, 0.0, 1.0) == 0.0
