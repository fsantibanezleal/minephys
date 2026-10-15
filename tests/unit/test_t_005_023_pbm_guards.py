"""T-005-023 (FR-005-15, FR-005-18): PBM and Austin guards.

Public API under test (`minephys.comminution`): `pbm_batch_grinding(mass, selection, breakage, times)`,
`pbm_continuous_mill(feed, selection, breakage, residence_time, n_tanks=1)`, `austin_selection(sizes, a, alpha, mu,
lam, x0=None)`, `austin_breakage(sizes, phi, gamma, beta)`.

Expected errors (`minephys.InputError`, with the `argument` attribute naming the offending argument; for structural
errors, one of the arguments involved): shapes that disagree, fewer than 2 or more than 200 classes, NaN, +-inf or
negative entries, a breakage matrix that is not strictly lower triangular, a column j with S_j > 0 that does not sum to 1
within 1e-12, a non-zero selection of the last (sink) class, a negative time, tau <= 0, `n_tanks` not an integer >= 1;
for the Austin forms sizes that are not positive and strictly decreasing, phi outside (0, 1], non-positive exponents,
a < 0, mu <= 0, lam < 0 and non-finite values. `minephys.InputTypeError` for non-numeric arguments (FR-000-11).

Oracle: the hostile classes written in FR-005-15 and FR-005-18.
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


S3 = np.array([0.5, 0.3, 0.0]) / 60.0
B3 = np.array([[0.0, 0.0, 0.0], [0.6, 0.0, 0.0], [0.4, 1.0, 0.0]])
M3 = np.array([1.0, 0.0, 0.0])
T3 = np.array([60.0, 120.0])


def _batch(**over: Any) -> Any:
    kw: dict[str, Any] = {"mass": M3, "selection": S3, "breakage": B3, "times": T3}
    kw.update(over)
    return _c().pbm_batch_grinding(**kw)


def _cont(**over: Any) -> Any:
    kw: dict[str, Any] = {"feed": M3, "selection": S3, "breakage": B3, "residence_time": 120.0, "n_tanks": 2}
    kw.update(over)
    return _c().pbm_continuous_mill(**kw)


MILLS = [("batch", _batch, "mass"), ("continuous", _cont, "feed")]


def _structure(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A valid n-class mill: sink S_n = 0, columns of B sum to 1."""
    s = np.full(n, 0.01)
    s[-1] = 0.0
    b = np.zeros((n, n))
    for j in range(n - 1):
        b[j + 1 :, j] = 1.0 / (n - 1 - j)
    return np.ones(n), s, b


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_valid_reference_calls_work(label: str, call: Any, mass_name: str) -> None:
    out = call()
    assert np.all(np.isfinite(out)) and out.dtype == np.float64


@pytest.mark.req("FR-005-15")
@pytest.mark.oracle("hand-calculation", "FR-005-15 hostile classes")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), -1.0])
def test_fr_005_15_non_finite_or_negative_entries(label: str, call: Any, mass_name: str, bad: float) -> None:
    input_error, _ = _errors()
    mass, selection, breakage = M3.copy(), S3.copy(), B3.copy()
    mass[0] = bad
    selection[0] = bad
    breakage[1, 0] = bad  # an entry inside the strictly lower triangle
    for name, arr in ((mass_name, mass), ("selection", selection), ("breakage", breakage)):
        with pytest.raises(input_error) as exc:
            call(**{name: arr})
        assert exc.value.argument == name


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_shape_mismatches(label: str, call: Any, mass_name: str) -> None:
    input_error, _ = _errors()
    involved = {mass_name, "selection", "breakage"}
    for over in (
        {"selection": S3[:2]},
        {mass_name: M3[:2]},
        {"breakage": B3[:2, :2]},
        {"breakage": np.zeros((3, 4))},
        {"breakage": B3.ravel()},
        {mass_name: np.ones((3, 1))},
        {"selection": S3.reshape(1, 3)},
    ):
        with pytest.raises(input_error) as exc:
            call(**over)
        assert exc.value.argument in involved


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_class_count_bounds(label: str, call: Any, mass_name: str) -> None:
    input_error, _ = _errors()
    involved = {mass_name, "selection", "breakage"}
    for n in (1, 201, 250):
        m, s, b = _structure(n) if n > 1 else (np.ones(1), np.zeros(1), np.zeros((1, 1)))
        with pytest.raises(input_error) as exc:
            call(**{mass_name: m, "selection": s, "breakage": b})
        assert exc.value.argument in involved
    m, s, b = _structure(200)  # the cap itself is valid
    assert call(**{mass_name: m, "selection": s, "breakage": b}).shape[-1] == 200
    m, s, b = _structure(2)  # and so is the minimum
    assert call(**{mass_name: m, "selection": s, "breakage": b}).shape[-1] == 2


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_breakage_must_be_strictly_lower_triangular(label: str, call: Any, mass_name: str) -> None:
    input_error, _ = _errors()
    diagonal = B3.copy()
    diagonal[1, 1] = 0.1
    upper = B3.copy()
    upper[0, 2] = 0.1
    for bad in (diagonal, upper, B3.T.copy()):
        with pytest.raises(input_error) as exc:
            call(breakage=bad)
        assert exc.value.argument == "breakage"


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_breakage_columns_must_sum_to_one_where_selection_is_positive(
    label: str, call: Any, mass_name: str
) -> None:
    input_error, _ = _errors()
    for scale in (0.5, 0.999999, 1.000001, 2.0):
        bad = B3.copy()
        bad[:, 0] *= scale  # column 0 has S_0 > 0
        with pytest.raises(input_error) as exc:
            call(breakage=bad)
        assert exc.value.argument == "breakage"
    bad = B3.copy()
    bad[:, 1] = [0.0, 0.0, 0.9]  # column 1 sums to 0.9, S_1 > 0
    with pytest.raises(input_error):
        call(breakage=bad)


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
def test_fr_005_15_the_last_class_is_a_sink(label: str, call: Any, mass_name: str) -> None:
    input_error, _ = _errors()
    for s_last in (1e-12, 0.01, 1.0):
        sel = S3.copy()
        sel[-1] = s_last
        with pytest.raises(input_error) as exc:
            call(selection=sel)
        assert exc.value.argument == "selection"


@pytest.mark.req("FR-005-15")
def test_fr_005_15_batch_times() -> None:
    input_error, _ = _errors()
    for bad in ([-1.0], [0.0, -1e-9, 5.0], [float("nan")], [float("inf")], [float("-inf")]):
        with pytest.raises(input_error) as exc:
            _batch(times=np.array(bad))
        assert exc.value.argument == "times"
    assert _batch(times=np.array([0.0])).shape == (1, 3)  # zero is a valid time


@pytest.mark.req("FR-005-15")
def test_fr_005_15_continuous_residence_time_and_tank_count() -> None:
    input_error, _ = _errors()
    for bad in (0.0, -1.0, float("nan"), float("inf"), float("-inf")):
        with pytest.raises(input_error) as exc:
            _cont(residence_time=bad)
        assert exc.value.argument == "residence_time"
    for bad in (0, -1, 2.5, 1.5, 0.5, float("nan"), float("inf")):
        with pytest.raises(input_error) as exc:
            _cont(n_tanks=bad)
        assert exc.value.argument == "n_tanks"
    assert _cont(n_tanks=1).shape == (3,)
    assert _cont(n_tanks=np.int64(3)).shape == (3,)  # NumPy integers are integers


@pytest.mark.req("FR-005-15")
@pytest.mark.parametrize(("label", "call", "mass_name"), MILLS)
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, b"1", object()], ids=lambda v: type(v).__name__)
def test_fr_005_15_non_numeric_arguments(label: str, call: Any, mass_name: str, bad: Any) -> None:
    _, input_type_error = _errors()
    for name in (mass_name, "selection", "breakage"):
        with pytest.raises(input_type_error) as exc:
            call(**{name: bad})
        assert exc.value.argument == name
    with pytest.raises(input_type_error):
        _batch(times=bad)
    with pytest.raises(input_type_error):
        _cont(residence_time=bad)


# ------------------------------------------------------------------ Austin forms (FR-005-18)

SIZES = np.array([2e-3, 1e-3, 5e-4, 2.5e-4])


@pytest.mark.req("FR-005-18")
@pytest.mark.oracle("hand-calculation", "FR-005-18 hostile classes")
@pytest.mark.parametrize(
    "bad_sizes",
    [
        np.array([1e-3, 2e-3, 3e-3]),  # increasing
        np.array([2e-3, 1e-3, 1e-3]),  # not strictly decreasing
        np.array([2e-3, 0.0, -1e-3]),
        np.array([2e-3, float("nan"), 1e-4]),
        np.array([float("inf"), 1e-3, 1e-4]),
        np.array([2e-3, -1e-3]),
        np.array([2e-3, 1e-3, 5e-4]).reshape(1, 3),
    ],
    ids=["increasing", "tie", "non-positive", "nan", "inf", "negative", "2-D"],
)
def test_fr_005_18_sizes_must_be_positive_and_strictly_decreasing(bad_sizes: np.ndarray) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        c.austin_selection(bad_sizes, 0.5, 1.2, 1.5e-3, 3.0, x0=1e-3)
    assert exc.value.argument == "sizes"
    with pytest.raises(input_error) as exc:
        c.austin_breakage(bad_sizes, 0.4, 0.8, 3.0)
    assert exc.value.argument == "sizes"


@pytest.mark.req("FR-005-18")
@pytest.mark.parametrize(
    ("name", "bad"),
    [
        ("a", -1e-9),
        ("a", float("nan")),
        ("a", float("inf")),
        ("alpha", 0.0),
        ("alpha", -1.0),
        ("alpha", float("nan")),
        ("mu", 0.0),
        ("mu", -1e-3),
        ("mu", float("inf")),
        ("lam", -0.5),
        ("lam", float("nan")),
        ("lam", float("-inf")),
        ("x0", 0.0),
        ("x0", -1e-3),
        ("x0", float("nan")),
    ],
)
def test_fr_005_18_selection_parameters(name: str, bad: float) -> None:
    c = _c()
    input_error, _ = _errors()
    kw: dict[str, Any] = {"sizes": SIZES, "a": 0.5, "alpha": 1.2, "mu": 1.5e-3, "lam": 3.0, "x0": 1e-3}
    kw[name] = bad
    with pytest.raises(input_error) as exc:
        c.austin_selection(**kw)
    assert exc.value.argument == name


@pytest.mark.req("FR-005-18")
@pytest.mark.parametrize(
    ("name", "bad"),
    [
        ("phi", 0.0),
        ("phi", -0.1),
        ("phi", 1.0000001),
        ("phi", 2.0),
        ("phi", float("nan")),
        ("gamma", 0.0),
        ("gamma", -1.0),
        ("gamma", float("inf")),
        ("beta", 0.0),
        ("beta", -2.0),
        ("beta", float("nan")),
    ],
)
def test_fr_005_18_breakage_parameters(name: str, bad: float) -> None:
    c = _c()
    input_error, _ = _errors()
    kw: dict[str, Any] = {"sizes": SIZES, "phi": 0.4, "gamma": 0.8, "beta": 3.0}
    kw[name] = bad
    with pytest.raises(input_error) as exc:
        c.austin_breakage(**kw)
    assert exc.value.argument == name


@pytest.mark.req("FR-005-18")
def test_fr_005_18_phi_equal_to_one_and_lam_equal_to_zero_are_valid() -> None:
    c = _c()
    assert c.austin_breakage(SIZES, 1.0, 0.8, 3.0).shape == (4, 4)
    assert c.austin_selection(SIZES, 0.5, 1.2, 1.5e-3, 0.0, x0=1e-3).shape == (4,)


@pytest.mark.req("FR-005-18")
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, True, b"1"], ids=lambda v: type(v).__name__)
def test_fr_005_18_non_numeric_arguments(bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    for name in ("sizes", "a", "alpha", "mu", "lam", "x0"):
        if name == "x0" and bad is None:
            continue  # None is the documented default of x0 (the knowledge row), not a bad value
        kw: dict[str, Any] = {"sizes": SIZES, "a": 0.5, "alpha": 1.2, "mu": 1.5e-3, "lam": 3.0, "x0": 1e-3}
        kw[name] = bad
        with pytest.raises(input_type_error) as exc:
            c.austin_selection(**kw)
        assert exc.value.argument == name
    for name in ("sizes", "phi", "gamma", "beta"):
        kw = {"sizes": SIZES, "phi": 0.4, "gamma": 0.8, "beta": 3.0}
        kw[name] = bad
        with pytest.raises(input_type_error) as exc:
            c.austin_breakage(**kw)
        assert exc.value.argument == name
