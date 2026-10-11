"""T-005-032 (FR-005-23): flotation and two-product guards.

Public API under test (`minephys.comminution`): `flotation_first_order(r_inf, k, t)`, `klimpel_recovery(r_inf, k, t)`,
`flotation_cell_recovery(r_inf, k, tau, n_cells=1)`, `two_product_recovery(feed_grade, concentrate_grade, tail_grade)`.

Expected errors: `minephys.InputError` (`argument` names the offending argument) when R_inf is outside (0, 1], k <= 0,
t < 0, tau <= 0, `n_cells` is not an integer >= 1, a value is non-finite, or the grades do not satisfy 0 <= tail < feed <
concentrate; `minephys.InputTypeError` for non-numeric arguments (FR-000-11).

Oracle: the hostile classes written in FR-005-23.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


def _errors():
    importlib.import_module("minephys.comminution")
    import minephys

    return minephys.InputError, minephys.InputTypeError


NAN, INF = float("nan"), float("inf")
BASE_KINETIC = {"r_inf": 0.9, "k": 0.02, "t": 100.0}
BASE_CELL = {"r_inf": 0.9, "k": 0.02, "tau": 100.0, "n_cells": 3}
BASE_TWO = {"feed_grade": 0.01, "concentrate_grade": 0.25, "tail_grade": 0.001}

# (function, base arguments, argument, bad values)
KINETIC_BAD = {
    "r_inf": [0.0, -0.1, 1.0000001, 2.0, NAN, INF, -INF],
    "k": [0.0, -1e-9, NAN, INF, -INF],
    "t": [-1e-9, -5.0, NAN, INF, -INF],
}
CELL_BAD = {
    "r_inf": KINETIC_BAD["r_inf"],
    "k": KINETIC_BAD["k"],
    "tau": [0.0, -1.0, NAN, INF, -INF],
    "n_cells": [0, -1, 2.5, 1.5, 0.5, NAN, INF],
}
TWO_BAD = {
    "feed_grade": [0.001, 0.0, 0.25, 0.3, -0.01, NAN, INF],  # <= tail, = 0 (not > t), >= concentrate, ...
    "concentrate_grade": [0.01, 0.005, 0.0, -0.1, NAN, INF],
    "tail_grade": [0.01, 0.02, 0.25, -1e-9, NAN, INF, -INF],
}
NON_NUMERIC: list[Any] = ["0.5", None, 1 + 2j, True, b"1", object(), np.array(["a"]), np.datetime64("2020-01-01")]


def _sweep() -> list[tuple[str, dict[str, Any], str, float]]:
    out = []
    for fn, base, bad in (
        ("flotation_first_order", BASE_KINETIC, KINETIC_BAD),
        ("klimpel_recovery", BASE_KINETIC, KINETIC_BAD),
        ("flotation_cell_recovery", BASE_CELL, CELL_BAD),
        ("two_product_recovery", BASE_TWO, TWO_BAD),
    ):
        for arg, values in bad.items():
            out.extend((fn, base, arg, v) for v in values)
    return out


@pytest.mark.req("FR-005-23")
@pytest.mark.oracle("hand-calculation", "FR-005-23 hostile classes")
@pytest.mark.parametrize(("fn", "base", "arg", "bad"), _sweep())
def test_fr_005_23_hostile_values_raise_input_error(fn: str, base: dict[str, Any], arg: str, bad: float) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(**dict(base, **{arg: bad}))
    if fn == "two_product_recovery":
        assert exc.value.argument in {"feed_grade", "concentrate_grade", "tail_grade"}  # ordering errors involve all three
    else:
        assert exc.value.argument == arg


@pytest.mark.req("FR-005-23")
@pytest.mark.parametrize(
    ("fn", "base", "arg"),
    [
        (fn, base, arg)
        for fn, base in (
            ("flotation_first_order", BASE_KINETIC),
            ("klimpel_recovery", BASE_KINETIC),
            ("flotation_cell_recovery", BASE_CELL),
            ("two_product_recovery", BASE_TWO),
        )
        for arg in base
        if arg != "n_cells"
    ],
)
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_23_non_numeric_arguments_raise_input_type_error(fn: str, base: dict[str, Any], arg: str, bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        getattr(c, fn)(**dict(base, **{arg: bad}))
    assert exc.value.argument == arg


@pytest.mark.req("FR-005-23")
def test_fr_005_23_two_product_grade_order_names_the_arguments() -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        c.two_product_recovery(0.01, 0.25, 0.01)  # tail = feed
    assert exc.value.argument in {"feed_grade", "tail_grade"}
    with pytest.raises(input_error) as exc:
        c.two_product_recovery(0.25, 0.25, 0.001)  # feed = concentrate
    assert exc.value.argument in {"feed_grade", "concentrate_grade"}
    with pytest.raises(input_error):
        c.two_product_recovery(0.5, 0.25, 0.001)  # feed above concentrate (sampling error): rejected, not extrapolated
    # arrays: one unordered element is enough
    with pytest.raises(input_error):
        c.two_product_recovery(np.array([0.01, 0.30]), 0.25, 0.001)


@pytest.mark.req("FR-005-23")
@pytest.mark.parametrize("fn", ["flotation_first_order", "klimpel_recovery"])
def test_fr_005_23_arrays_with_one_bad_element_and_unbroadcastable_shapes(fn: str) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(0.9, 0.02, np.array([10.0, -1.0, 30.0]))
    assert exc.value.argument == "t"
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(0.9, np.array([0.01, 0.02, 0.03]), np.array([1.0, 2.0]))
    msg = str(exc.value)
    assert "3" in msg and "2" in msg  # FR-000-12: the shapes are named


@pytest.mark.req("FR-005-23")
def test_fr_005_23_boundaries_that_are_valid() -> None:
    c = _c()
    assert c.flotation_first_order(1.0, 0.01, 0.0) == 0.0  # R_inf = 1 and t = 0 are inside the domain
    assert c.klimpel_recovery(1.0, 0.01, 0.0) == 0.0
    assert c.flotation_cell_recovery(1.0, 0.01, 1e-9, 1) > 0.0
    y, r = c.two_product_recovery(0.01, 0.25, 0.0)  # tail grade 0 is allowed
    assert 0.0 < y < 1.0 and r == pytest.approx(1.0)
    assert c.flotation_cell_recovery(0.9, 0.02, 50.0, n_cells=np.int64(4)) > 0.0
