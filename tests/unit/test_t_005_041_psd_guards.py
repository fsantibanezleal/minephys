"""T-005-041 (FR-005-26): the size-distribution helpers reject hostile inputs.

Public API under test (`minephys.comminution`): `passing_size(sizes, passing, fraction=0.8)`,
`class_masses(sizes, passing)`, `cumulative_passing(masses)`.
Expected: `minephys.InputError` naming the argument for sizes that are not strictly monotone and positive, passing values
outside [0, 1] or not monotone in size, mismatched lengths, fewer than 2 or more than 10,000 points, NaN or inf, and a
`fraction` outside the range spanned by the curve; `minephys.InputTypeError` for non-numeric arguments.
(Negative class masses in `cumulative_passing` are rejected under FR-000-14: a negative mass is outside the physical domain.)

Oracle: the hostile classes written in FR-005-26.
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
    importlib.import_module("minephys.comminution")
    import minephys

    return minephys.InputError, minephys.InputTypeError


SIZES = np.array([0.4, 0.2, 0.1, 0.05])
PASSING = np.array([1.0, 0.75, 0.4, 0.15])
NAN, INF = float("nan"), float("inf")
BAD_SIZES = {
    "not_monotone": np.array([0.4, 0.1, 0.2, 0.05]),
    "tie": np.array([0.4, 0.2, 0.2, 0.05]),
    "zero": np.array([0.4, 0.2, 0.1, 0.0]),
    "negative": np.array([0.4, 0.2, 0.1, -0.05]),
    "nan": np.array([0.4, NAN, 0.1, 0.05]),
    "inf": np.array([INF, 0.2, 0.1, 0.05]),
    "two_d": np.tile(SIZES, (2, 1)),
}
BAD_PASSING = {
    "above_one": np.array([1.2, 0.75, 0.4, 0.15]),
    "below_zero": np.array([1.0, 0.75, 0.4, -0.01]),
    "not_monotone": np.array([1.0, 0.4, 0.75, 0.15]),
    "nan": np.array([1.0, NAN, 0.4, 0.15]),
    "inf": np.array([1.0, 0.75, 0.4, INF]),
    "reversed": PASSING[::-1].copy(),  # passing increasing as the size decreases
}
NON_NUMERIC: list[Any] = ["abc", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a", "b"])]
FUNCS = ["passing_size", "class_masses"]


@pytest.mark.req("FR-005-26")
@pytest.mark.oracle("hand-calculation", "FR-005-26 hostile classes")
@pytest.mark.parametrize("fn", FUNCS)
@pytest.mark.parametrize("label", list(BAD_SIZES))
def test_fr_005_26_bad_sizes(fn: str, label: str) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(BAD_SIZES[label], PASSING)
    assert exc.value.argument == "sizes"


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize("fn", FUNCS)
@pytest.mark.parametrize("label", list(BAD_PASSING))
def test_fr_005_26_bad_passing(fn: str, label: str) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(SIZES, BAD_PASSING[label])
    assert exc.value.argument == "passing"


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize("fn", FUNCS)
def test_fr_005_26_mismatched_lengths_and_point_counts(fn: str) -> None:
    c = _c()
    input_error, _ = _errors()
    for sizes, passing in (
        (SIZES, PASSING[:3]),
        (SIZES[:3], PASSING),
        (SIZES[:1], PASSING[:1]),  # fewer than 2 points
        (SIZES[:0], PASSING[:0]),
    ):
        with pytest.raises(input_error) as exc:
            getattr(c, fn)(sizes, passing)
        assert exc.value.argument in {"sizes", "passing"}
    big = np.geomspace(1.0, 1e-6, 10_001)  # more than 10,000 points
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(big, np.linspace(1.0, 0.01, big.size))
    assert exc.value.argument in {"sizes", "passing"}
    ok = np.geomspace(1.0, 1e-6, 10_000)  # the cap itself is accepted
    assert np.all(np.isfinite(getattr(c, fn)(ok, np.linspace(1.0, 0.01, ok.size))))


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize("fn", FUNCS)
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_26_non_numeric(fn: str, bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    for name, args in (("sizes", (bad, PASSING)), ("passing", (SIZES, bad))):
        with pytest.raises(input_type_error) as exc:
            getattr(c, fn)(*args)
        assert exc.value.argument == name


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize("fraction", [0.0, -0.1, 0.1, 0.14999, 1.0001, 1.5, NAN, INF, -INF])
def test_fr_005_26_fraction_outside_the_curve_range(fraction: float) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        c.passing_size(SIZES, PASSING, fraction)  # the curve spans [0.15, 1.0]
    assert exc.value.argument == "fraction"


@pytest.mark.req("FR-005-26")
def test_fr_005_26_fraction_type_and_range_boundaries() -> None:
    c = _c()
    _, input_type_error = _errors()
    for bad in ("0.8", None, 1 + 0j, True):
        with pytest.raises(input_type_error) as exc:
            c.passing_size(SIZES, PASSING, bad)
        assert exc.value.argument == "fraction"
    assert c.passing_size(SIZES, PASSING, 0.15) == pytest.approx(0.05, rel=1e-13)  # curve ends are valid
    assert c.passing_size(SIZES, PASSING, 1.0) == pytest.approx(0.4, rel=1e-13)


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize(
    ("masses", "ok"),
    [
        (np.array([0.25, 0.35, 0.25, 0.15]), True),
        (np.array([0.25, -0.01, 0.25, 0.15]), False),
        (np.array([0.25, NAN, 0.25, 0.15]), False),
        (np.array([INF, 0.1]), False),
        (np.array([0.5]), False),  # fewer than 2 points
        (np.array([]), False),
        (np.full(10_001, 1e-5), False),  # more than 10,000 points
        (np.full(10_000, 1e-5), True),
        (np.array([[0.2, 0.3], [0.1, 0.4]]), False),  # 2-D
    ],
    ids=["valid", "negative", "nan", "inf", "single", "empty", "too_many", "cap", "two_d"],
)
def test_fr_005_26_cumulative_passing(masses: np.ndarray, ok: bool) -> None:
    c = _c()
    input_error, _ = _errors()
    if ok:
        out = c.cumulative_passing(masses)
        assert out.shape == masses.shape and np.all(np.isfinite(out))
    else:
        with pytest.raises(input_error) as exc:
            c.cumulative_passing(masses)
        assert exc.value.argument == "masses"


@pytest.mark.req("FR-005-26")
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_26_cumulative_passing_non_numeric(bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        c.cumulative_passing(bad)
    assert exc.value.argument == "masses"
