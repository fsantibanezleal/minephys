"""T-005-043 (FR-005-29): crusher guards.

Public API under test (`minephys.comminution`): `crusher_matrix_model(feed, classification, breakage)` and
`whiten_classification(sizes, k1, k2, k3)`.
Expected: `minephys.InputError` naming the argument for mismatched shapes, a classification outside [0, 1], a breakage that
is not strictly lower triangular or whose column j with c_j > 0 does not sum to 1 within 1e-12, a finest class with
c_n > 0, negative or non-finite values; for `whiten_classification`: k1 >= k2, k3 <= 0 and non-finite values.
`minephys.InputTypeError` for non-numeric arguments.

Oracle: the hostile classes written in FR-005-29.
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


F3 = np.array([0.6, 0.3, 0.1])
C3 = np.array([0.8, 0.4, 0.0])
B3 = np.array([[0.0, 0.0, 0.0], [0.7, 0.0, 0.0], [0.3, 1.0, 0.0]])
NAN, INF = float("nan"), float("inf")
NON_NUMERIC: list[Any] = ["abc", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a"])]


def _crush(**over: Any) -> Any:
    kw: dict[str, Any] = {"feed": F3, "classification": C3, "breakage": B3}
    kw.update(over)
    return _c().crusher_matrix_model(**kw)


@pytest.mark.req("FR-005-29")
def test_fr_005_29_reference_call_is_valid() -> None:
    assert _crush().shape == (3,)


@pytest.mark.req("FR-005-29")
@pytest.mark.oracle("hand-calculation", "FR-005-29 hostile classes")
@pytest.mark.parametrize("bad", [NAN, INF, -INF, -0.1])
def test_fr_005_29_non_finite_or_negative_entries(bad: float) -> None:
    input_error, _ = _errors()
    feed, cl, br = F3.copy(), C3.copy(), B3.copy()
    feed[1] = bad
    cl[1] = bad
    br[1, 0] = bad
    for name, arr in (("feed", feed), ("classification", cl), ("breakage", br)):
        with pytest.raises(input_error) as exc:
            _crush(**{name: arr})
        assert exc.value.argument == name


@pytest.mark.req("FR-005-29")
def test_fr_005_29_classification_outside_unit_interval() -> None:
    input_error, _ = _errors()
    for bad in (1.0000001, 1.5, -1e-9):
        cl = C3.copy()
        cl[0] = bad
        with pytest.raises(input_error) as exc:
            _crush(classification=cl)
        assert exc.value.argument == "classification"
    assert _crush(classification=np.array([1.0, 0.0, 0.0])).shape == (3,)  # the bounds are valid


@pytest.mark.req("FR-005-29")
def test_fr_005_29_shape_mismatches() -> None:
    input_error, _ = _errors()
    involved = {"feed", "classification", "breakage"}
    for over in (
        {"feed": F3[:2]},
        {"classification": C3[:2]},
        {"breakage": B3[:2, :2]},
        {"breakage": np.zeros((3, 4))},
        {"breakage": B3.ravel()},
        {"feed": F3.reshape(3, 1)},
        {"classification": C3.reshape(1, 3)},
    ):
        with pytest.raises(input_error) as exc:
            _crush(**over)
        assert exc.value.argument in involved


@pytest.mark.req("FR-005-29")
def test_fr_005_29_breakage_must_be_strictly_lower_triangular() -> None:
    input_error, _ = _errors()
    diag, upper = B3.copy(), B3.copy()
    diag[1, 1] = 0.2
    upper[0, 2] = 0.2
    for bad in (diag, upper, B3.T.copy()):
        with pytest.raises(input_error) as exc:
            _crush(breakage=bad)
        assert exc.value.argument == "breakage"


@pytest.mark.req("FR-005-29")
def test_fr_005_29_breakage_columns_must_sum_to_one_where_the_class_is_broken() -> None:
    input_error, _ = _errors()
    for scale in (0.5, 0.999999, 1.000001, 2.0):
        bad = B3.copy()
        bad[:, 0] *= scale  # c_0 = 0.8 > 0
        with pytest.raises(input_error) as exc:
            _crush(breakage=bad)
        assert exc.value.argument == "breakage"
    bad = B3.copy()
    bad[:, 1] = [0.0, 0.0, 0.5]
    with pytest.raises(input_error):
        _crush(breakage=bad)


@pytest.mark.req("FR-005-29")
def test_fr_005_29_the_finest_class_cannot_be_broken() -> None:
    input_error, _ = _errors()
    for c_last in (1e-9, 0.3, 1.0):
        cl = C3.copy()
        cl[-1] = c_last
        with pytest.raises(input_error) as exc:
            _crush(classification=cl)
        assert exc.value.argument == "classification"


@pytest.mark.req("FR-005-29")
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_29_non_numeric_arguments(bad: Any) -> None:
    _, input_type_error = _errors()
    for name in ("feed", "classification", "breakage"):
        with pytest.raises(input_type_error) as exc:
            _crush(**{name: bad})
        assert exc.value.argument == name


WHITEN_BASE = {"sizes": np.array([0.01, 0.05, 0.2]), "k1": 0.02, "k2": 0.1, "k3": 2.0}


@pytest.mark.req("FR-005-29")
@pytest.mark.parametrize(
    ("name", "bad"),
    [
        ("k1", 0.1),  # k1 = k2
        ("k1", 0.2),  # k1 > k2
        ("k2", 0.02),
        ("k2", 0.01),
        ("k3", 0.0),
        ("k3", -1.0),
        ("k1", NAN),
        ("k2", INF),
        ("k3", NAN),
        ("k3", INF),
        ("k1", -INF),
        ("sizes", np.array([0.01, NAN])),
        ("sizes", np.array([0.01, INF])),
    ],
)
def test_fr_005_29_whiten_parameter_errors(name: str, bad: Any) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        c.whiten_classification(**dict(WHITEN_BASE, **{name: bad}))
    assert exc.value.argument in ({name} | ({"k1", "k2"} if name in {"k1", "k2"} else set()))


@pytest.mark.req("FR-005-29")
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_29_whiten_non_numeric(bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    for name in ("sizes", "k1", "k2", "k3"):
        with pytest.raises(input_type_error) as exc:
            c.whiten_classification(**dict(WHITEN_BASE, **{name: bad}))
        assert exc.value.argument == name
