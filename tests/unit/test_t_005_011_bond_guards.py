"""T-005-011 (FR-005-04): the Bond functions reject hostile inputs and return no partial result.

Public API under test (`minephys.comminution`): `bond_energy(work_index, f80, p80)`,
`bond_operating_work_index(specific_energy, f80, p80)`, `bond_ball_mill_work_index(closing_screen, grindability,
f80, p80)`. Expected errors: `minephys.InputError` (a `ValueError`) whose `argument` attribute names the argument for
NaN, +-inf, zero, negative, unordered (p80 >= f80) and unbroadcastable inputs; `minephys.InputTypeError` (a
`TypeError`) for non-numeric arguments (FR-000-10, FR-000-11, FR-000-12, FR-000-14).

Oracle: hand-written hostile classes of spec 005 FR-005-04 (the expected exception class and argument are the
requirement itself).
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


def _errors():
    importlib.import_module("minephys.comminution")  # the module under test first, then the error classes
    import minephys

    return minephys.InputError, minephys.InputTypeError


# (function name, valid keyword arguments in SI)
CASES: list[tuple[str, dict[str, float]]] = [
    ("bond_energy", {"work_index": 5.4e4, "f80": 2.0e-3, "p80": 1.5e-4}),
    ("bond_operating_work_index", {"specific_energy": 3.0e4, "f80": 2.5e-3, "p80": 2.12e-4}),
    (
        "bond_ball_mill_work_index",
        {"closing_screen": 1.06e-4, "grindability": 1.825e-3, "f80": 2.7461e-3, "p80": 7.97e-5},
    ),
]
BAD_NUMBERS = [float("nan"), float("inf"), float("-inf"), 0.0, -1.0, -1e-12]
NON_NUMERIC: list[Any] = [
    "1.0",
    "１.０",  # full-width digits
    "µm",
    None,
    1 + 2j,
    True,
    b"1",
    object(),
    dt.datetime(2020, 1, 1),
    np.datetime64("2020-01-01"),
    np.timedelta64(1, "s"),
    np.array(["a", "b"]),
    np.array([1 + 1j]),
    np.array([True, False]),
]


def _sweep() -> list[tuple[str, dict[str, float], str]]:
    return [(fn, kw, arg) for fn, kw in CASES for arg in kw]


@pytest.mark.req("FR-005-04")
@pytest.mark.oracle("hand-calculation", "FR-005-04 hostile classes")
@pytest.mark.parametrize(("fn", "kw", "arg"), _sweep())
@pytest.mark.parametrize("bad", BAD_NUMBERS)
def test_fr_005_04_non_finite_and_non_positive_values_raise_input_error(
    fn: str, kw: dict[str, float], arg: str, bad: float
) -> None:
    c = _c()
    input_error, _ = _errors()
    call = dict(kw, **{arg: bad})
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(**call)
    assert exc.value.argument == arg
    assert isinstance(exc.value, ValueError)


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw", "arg"), _sweep())
def test_fr_005_04_array_with_one_bad_element_raises_naming_the_argument(
    fn: str, kw: dict[str, float], arg: str
) -> None:
    c = _c()
    input_error, _ = _errors()
    for bad in (float("nan"), float("inf"), -3.0, 0.0):
        arr = np.array([kw[arg], kw[arg], bad])
        with pytest.raises(input_error) as exc:
            getattr(c, fn)(**dict(kw, **{arg: arr}))
        assert exc.value.argument == arg


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw", "arg"), _sweep())
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_04_non_numeric_raises_input_type_error(fn: str, kw: dict[str, float], arg: str, bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        getattr(c, fn)(**dict(kw, **{arg: bad}))
    assert exc.value.argument == arg
    assert isinstance(exc.value, TypeError)


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw"), CASES)
def test_fr_005_04_product_not_finer_than_feed_raises(fn: str, kw: dict[str, float]) -> None:
    c = _c()
    input_error, _ = _errors()
    for p80 in (kw["f80"], kw["f80"] * 1.0000001, kw["f80"] * 10.0):
        with pytest.raises(input_error) as exc:
            getattr(c, fn)(**dict(kw, p80=p80))
        assert exc.value.argument in {"p80", "f80"}


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw"), CASES)
def test_fr_005_04_unordered_anywhere_in_an_array_raises(fn: str, kw: dict[str, float]) -> None:
    c = _c()
    input_error, _ = _errors()
    f80 = np.array([kw["f80"], kw["f80"] * 2.0, kw["p80"] * 0.5])  # last element: p80 >= f80
    with pytest.raises(input_error):
        getattr(c, fn)(**dict(kw, f80=f80))


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw"), CASES)
def test_fr_005_04_unbroadcastable_shapes_raise_and_name_both_arguments(fn: str, kw: dict[str, float]) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(**dict(kw, f80=np.full(3, kw["f80"]), p80=np.full(2, kw["p80"])))
    msg = str(exc.value)
    assert "f80" in msg and "p80" in msg  # FR-000-12: names the arguments (and their shapes)
    assert "3" in msg and "2" in msg


@pytest.mark.req("FR-005-04")
@pytest.mark.parametrize(("fn", "kw"), CASES)
def test_fr_005_04_valid_call_is_unaffected_and_inputs_are_not_modified(fn: str, kw: dict[str, float]) -> None:
    c = _c()
    f80 = np.full(4, kw["f80"])
    p80 = np.full(4, kw["p80"])
    f_before, p_before = f80.copy(), p80.copy()
    out = getattr(c, fn)(**dict(kw, f80=f80, p80=p80))
    assert out.shape == (4,) and np.all(np.isfinite(out)) and np.all(out > 0)
    assert np.array_equal(f80, f_before) and np.array_equal(p80, p_before)
