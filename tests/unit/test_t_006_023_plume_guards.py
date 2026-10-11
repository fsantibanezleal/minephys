"""T-006-023 (FR-006-14): dispersion and plume guards.

Public API under test (`minephys.environment`): `pasquill_sigmas(x, stability_class, terrain="rural")`,
`gaussian_plume(q, u, y, z, h, sigma_y, sigma_z, mixing_height=None)`, `line_source_plume(q_line, u, z, h, sigma_z)`,
`finite_line_source_plume(q_line, u, y, z, h, y1, y2, sigma_y, sigma_z)`, `line_emission_rate(emission_factor,
vehicles_per_second)` (signatures as in tests/unit/test_t_006_020_sigmas.py, test_t_006_021_plume.py,
test_t_006_022_line_source.py).
Expected: `minephys.InputError` naming the argument for NaN or +-inf, x <= 0, a stability class that is not exactly "A" to "F" or
a terrain that is not exactly "rural" or "urban", u <= 0, sigma <= 0, z < 0, h < 0, a negative emission or vehicle rate, y1 >= y2,
a mixing height <= 0 and unbroadcastable arrays (the message names the arguments and their shapes);
`minephys.InputTypeError` for non-numeric numerical arguments. The crosswind coordinate y may be negative.

Oracle: the hostile classes written in FR-006-14.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

NAN, INF = float("nan"), float("inf")


def _e():
    return importlib.import_module("minephys.environment")


def _errors():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.InputError, minephys.InputTypeError


POS = [0.0, -1.0, NAN, INF, -INF]  # strictly positive quantities
NONNEG = [-1e-9, -1.0, NAN, INF, -INF]  # non-negative quantities
FREE = [NAN, INF, -INF]  # quantities of any sign

CASES: dict[str, tuple[dict[str, Any], dict[str, list[Any]]]] = {
    "pasquill_sigmas": (
        {"x": 500.0, "stability_class": "D", "terrain": "rural"},
        {"x": POS, "stability_class": ["a", "G", "", "AB", "d", " D", "D ", "E1"], "terrain": ["Rural", "URBAN", "", "suburban", "rural "]},
    ),
    "gaussian_plume": (
        {"q": 1e-3, "u": 3.0, "y": 5.0, "z": 2.0, "h": 4.0, "sigma_y": 36.0, "sigma_z": 20.0, "mixing_height": 500.0},
        {
            "q": NONNEG,
            "u": POS,
            "y": FREE,
            "z": NONNEG,
            "h": NONNEG,
            "sigma_y": POS,
            "sigma_z": POS,
            "mixing_height": [0.0, -1.0, NAN, INF, -INF],
        },
    ),
    "line_source_plume": (
        {"q_line": 5e-6, "u": 3.0, "z": 2.0, "h": 4.0, "sigma_z": 20.0},
        {"q_line": NONNEG, "u": POS, "z": NONNEG, "h": NONNEG, "sigma_z": POS},
    ),
    "finite_line_source_plume": (
        {"q_line": 5e-6, "u": 3.0, "y": 5.0, "z": 2.0, "h": 4.0, "y1": -30.0, "y2": 30.0, "sigma_y": 36.0, "sigma_z": 20.0},
        {
            "q_line": NONNEG,
            "u": POS,
            "y": FREE,
            "z": NONNEG,
            "h": NONNEG,
            "y1": FREE,
            "y2": FREE,
            "sigma_y": POS,
            "sigma_z": POS,
        },
    ),
    "line_emission_rate": (
        {"emission_factor": 2.8e-3, "vehicles_per_second": 0.0023},
        {"emission_factor": NONNEG, "vehicles_per_second": NONNEG},
    ),
}
NON_NUMERIC: list[Any] = ["abc", "１.０", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a"])]
NUMERIC_NAMES = {fn: [a for a in base if a not in ("stability_class", "terrain")] for fn, (base, _) in CASES.items()}
OPTIONAL = {("gaussian_plume", "mixing_height"), ("pasquill_sigmas", "terrain")}


def _call(fn: str, kwargs: dict[str, Any]) -> Any:
    return getattr(_e(), fn)(**kwargs)


def _bad_values() -> list[Any]:
    return [
        pytest.param(fn, arg, bad, id=f"{fn}-{arg}-{bad!r}")
        for fn, (_, bads) in CASES.items()
        for arg, values in bads.items()
        for bad in values
    ]


def _non_numeric() -> list[Any]:
    return [
        pytest.param(fn, arg, bad, id=f"{fn}-{arg}-{type(bad).__name__}")
        for fn, names in NUMERIC_NAMES.items()
        for arg in names
        for bad in NON_NUMERIC
        if not (bad is None and (fn, arg) in OPTIONAL)
    ]


@pytest.mark.req("FR-006-14")
def test_fr_006_14_reference_calls_are_valid() -> None:
    for fn, (base, _) in CASES.items():
        assert _call(fn, base) is not None


@pytest.mark.req("FR-006-14")
@pytest.mark.oracle("hand-calculation", "FR-006-14 hostile classes")
@pytest.mark.parametrize(("fn", "arg", "bad"), _bad_values())
def test_fr_006_14_hostile_values_raise_input_error(fn: str, arg: str, bad: Any) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-14")
@pytest.mark.parametrize(("fn", "arg", "bad"), _non_numeric())
def test_fr_006_14_non_numeric_arguments_raise_input_type_error(fn: str, arg: str, bad: Any) -> None:
    _e()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-14")
@pytest.mark.parametrize(("y1", "y2"), [(30.0, 30.0), (40.0, -40.0), (1e-9, 0.0)])
def test_fr_006_14_segment_ends_must_be_ordered(y1: float, y2: float) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call("finite_line_source_plume", {**CASES["finite_line_source_plume"][0], "y1": y1, "y2": y2})
    assert exc.value.argument in {"y1", "y2"}
    with pytest.raises(input_error):  # one unordered element of an array of segments
        _call("finite_line_source_plume", {**CASES["finite_line_source_plume"][0], "y1": np.array([-30.0, 50.0]), "y2": 30.0})


@pytest.mark.req("FR-006-14")
@pytest.mark.parametrize("fn", ["gaussian_plume", "line_source_plume", "finite_line_source_plume"])
def test_fr_006_14_unbroadcastable_arrays_name_the_arguments_and_shapes(fn: str) -> None:
    _e()
    input_error, _ = _errors()
    base = dict(CASES[fn][0])
    first, second = ("z", "h") if fn != "gaussian_plume" else ("y", "z")
    with pytest.raises(input_error) as exc:
        _call(fn, {**base, first: np.full(3, 2.0), second: np.full(2, 4.0)})
    msg = str(exc.value)
    assert first in msg and second in msg and "3" in msg and "2" in msg


@pytest.mark.req("FR-006-14")
def test_fr_006_14_array_with_one_bad_element_and_the_valid_edge_values() -> None:
    e = _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        e.gaussian_plume(1e-3, 3.0, 0.0, np.array([1.0, -2.0]), 4.0, 36.0, 20.0)
    assert exc.value.argument == "z"
    # valid edge values: zero emission, z = h = 0, negative y, a zero vehicle rate
    assert e.gaussian_plume(0.0, 3.0, -10.0, 0.0, 0.0, 36.0, 20.0) == 0.0
    assert e.line_emission_rate(2.8e-3, 0.0) == 0.0
    assert e.line_source_plume(0.0, 3.0, 0.0, 0.0, 20.0) == 0.0
    sy, sz = e.pasquill_sigmas(np.array([10.0, 1e5]), "F", terrain="rural")
    assert sy.shape == (2,) and np.all(np.isfinite(sz))
