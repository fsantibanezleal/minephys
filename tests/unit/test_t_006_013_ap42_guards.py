"""T-006-013 (FR-006-07): AP-42 guards.

Public API under test (`minephys.environment`): `ap42_unpaved_emission_factor`, `ap42_unpaved_validity`,
`fleet_mean_vehicle_weight(weights, traffic_fractions)`, `precipitation_correction(emission_factor, wet_days)`,
`watering_control_efficiency(moisture_ratio)`, `controlled_emission_factor(emission_factor, control_efficiency)`
(signatures as in tests/unit/test_t_006_010_ap42.py and test_t_006_012_ap42_corrections.py).
Expected: `minephys.InputError` naming the argument for NaN or +-inf, a silt fraction <= 0 or > 1, a weight, speed or wheel count
<= 0, a moisture fraction outside [0, 1], an unknown `size_class` (exact, case-sensitive), negative or all-zero traffic fractions,
mismatched lengths, `wet_days` outside [0, 365], a moisture ratio outside [0, 5], a control efficiency outside [0, 1] and a
negative emission factor; `minephys.InputTypeError` for non-numeric arguments and a non-boolean `strict`.

Oracle: the hostile classes written in FR-006-07.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

ST = 907.18474
NAN, INF = float("nan"), float("inf")


def _e():
    return importlib.import_module("minephys.environment")


def _errors():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.InputError, minephys.InputTypeError


EF_BASE = {"silt_fraction": 0.10, "mean_weight": 100.0 * ST, "size_class": "PM10"}
EF_OPT = {"mean_speed": 10.0, "mean_wheels": 6, "moisture_fraction": 0.02}

# function -> (valid keyword arguments, {argument: [bad values]})
CASES: dict[str, tuple[dict[str, Any], dict[str, list[Any]]]] = {
    "ap42_unpaved_emission_factor": (
        {**EF_BASE, **EF_OPT},
        {
            "silt_fraction": [0.0, -0.1, 1.0000001, 2.0, NAN, INF, -INF],
            "mean_weight": [0.0, -1.0, NAN, INF, -INF],
            "mean_speed": [0.0, -1.0, NAN, INF],
            "mean_wheels": [0, -4, NAN, INF],
            "moisture_fraction": [-1e-9, 1.0000001, 5.0, NAN, INF],
        },
    ),
    "ap42_unpaved_validity": (
        {**EF_BASE, **EF_OPT, "size_class": None},
        {
            "silt_fraction": [0.0, -0.1, 1.0000001, NAN, INF],
            "mean_weight": [0.0, -1.0, NAN, INF],
            "mean_speed": [0.0, -1.0, NAN],
            "mean_wheels": [0, -4, NAN],
            "moisture_fraction": [-1e-9, 1.0000001, NAN],
        },
    ),
    "precipitation_correction": (
        {"emission_factor": 2.0e-3, "wet_days": 120},
        {"emission_factor": [-1e-12, -1.0, NAN, INF, -INF], "wet_days": [-1, -1e-9, 365.0001, 400, NAN, INF, -INF]},
    ),
    "watering_control_efficiency": (
        {"moisture_ratio": 2.5},
        {"moisture_ratio": [-1e-9, -1.0, 5.0000001, 6.0, NAN, INF, -INF]},
    ),
    "controlled_emission_factor": (
        {"emission_factor": 2.0e-3, "control_efficiency": 0.5},
        {"emission_factor": [-1e-12, -1.0, NAN, INF], "control_efficiency": [-1e-9, 1.0000001, 2.0, NAN, INF, -INF]},
    ),
}
NON_NUMERIC: list[Any] = ["abc", "１.０", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a"])]


def _call(fn: str, kwargs: dict[str, Any]) -> Any:
    kwargs = {k: v for k, v in kwargs.items() if not (k == "size_class" and v is None and fn == "ap42_unpaved_validity")}
    return getattr(_e(), fn)(**kwargs)


# None means "not given" for the optional arguments, so it is not a bad value there
OPTIONAL = {"mean_speed", "mean_wheels", "moisture_fraction"}


def _non_numeric_sweep() -> list[Any]:
    return [
        pytest.param(fn, arg, bad, id=f"{fn}-{arg}-{type(bad).__name__}")
        for fn, (_, bad_values) in CASES.items()
        for arg in bad_values
        for bad in NON_NUMERIC
        if not (bad is None and arg in OPTIONAL)
    ]


def _sweep(which: str) -> list[tuple[str, str, Any]]:
    out = []
    for fn, (_, bad) in CASES.items():
        for arg, values in bad.items():
            out.extend((fn, arg, v) for v in values) if which == "bad" else out.append((fn, arg, None))
    return out


@pytest.mark.req("FR-006-07")
def test_fr_006_07_reference_calls_are_valid() -> None:
    for fn, (base, _) in CASES.items():
        out = _call(fn, base)
        assert out is not None


@pytest.mark.req("FR-006-07")
@pytest.mark.oracle("hand-calculation", "FR-006-07 hostile classes")
@pytest.mark.parametrize(("fn", "arg", "bad"), _sweep("bad"))
def test_fr_006_07_out_of_domain_and_non_finite_values(fn: str, arg: str, bad: Any) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-07")
@pytest.mark.parametrize(("fn", "arg", "bad"), _non_numeric_sweep())
def test_fr_006_07_non_numeric_arguments(fn: str, arg: str, bad: Any) -> None:
    _e()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-07")
@pytest.mark.parametrize("arg_value", [np.array([0.1, 0.2, np.nan]), np.array([0.1, 0.2, -0.5]), np.array([0.1, 1.5])])
def test_fr_006_07_arrays_with_a_bad_element_are_rejected(arg_value: Any) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call("ap42_unpaved_emission_factor", {**CASES["ap42_unpaved_emission_factor"][0], "silt_fraction": arg_value})
    assert exc.value.argument == "silt_fraction"

@pytest.mark.req("FR-006-07")
@pytest.mark.parametrize("name", ["pm10", "PM 10", "PM2_5", "PM25", "PM2.50", "Pm10", "", " PM10", "PM10 ", "PM100", "TSP", "µ"])
def test_fr_006_07_unknown_size_class(name: str) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call("ap42_unpaved_emission_factor", {**CASES["ap42_unpaved_emission_factor"][0], "size_class": name})
    assert exc.value.argument == "size_class"
    assert "PM2.5" in str(exc.value) and "PM30" in str(exc.value)  # the allowed values are listed (FR-000-15)


@pytest.mark.req("FR-006-07")
def test_fr_006_07_valid_boundaries_are_accepted() -> None:
    e = _e()
    assert e.ap42_unpaved_emission_factor(1.0, 1.0, "PM30") > 0.0  # silt = 100 % is the upper limit of the domain
    assert e.precipitation_correction(0.0, 0) == 0.0  # a zero emission factor is not negative
    assert e.precipitation_correction(1.0, 365) == 0.0 and e.precipitation_correction(1.0, 0) == 1.0
    assert e.watering_control_efficiency(0.0) == 0.0 and e.watering_control_efficiency(5.0) == pytest.approx(0.95)
    assert e.controlled_emission_factor(2.0, 0.0) == 2.0 and e.controlled_emission_factor(2.0, 1.0) == 0.0
    assert e.ap42_unpaved_emission_factor(0.1, 1e5, "PM10", moisture_fraction=0.0) > 0.0
    assert e.ap42_unpaved_emission_factor(0.1, 1e5, "PM10", moisture_fraction=1.0) > 0.0


@pytest.mark.req("FR-006-07")
def test_fr_006_07_strict_must_be_boolean() -> None:
    _e()
    _, input_type_error = _errors()
    for bad in (1, 0, "yes", None, 1.0):
        with pytest.raises(input_type_error) as exc:
            _call("ap42_unpaved_emission_factor", {**CASES["ap42_unpaved_emission_factor"][0], "strict": bad})
        assert exc.value.argument == "strict"


@pytest.mark.req("FR-006-07")
def test_fr_006_07_fleet_mean_weight_guards() -> None:
    e = _e()
    input_error, input_type_error = _errors()
    w, f = np.array([20_000.0, 60_000.0]), np.array([0.7, 0.3])
    for weights, fractions, arg in (
        (np.array([20_000.0, 0.0]), f, "weights"),
        (np.array([20_000.0, -5.0]), f, "weights"),
        (np.array([20_000.0, NAN]), f, "weights"),
        (np.array([20_000.0, INF]), f, "weights"),
        (w, np.array([0.7, -0.1]), "traffic_fractions"),
        (w, np.array([0.0, 0.0]), "traffic_fractions"),  # all-zero traffic
        (w, np.array([0.7, NAN]), "traffic_fractions"),
        (w, np.array([0.7, INF]), "traffic_fractions"),
        (w, np.array([0.7]), "traffic_fractions"),  # mismatched lengths
        (np.array([20_000.0]), f, "weights"),
    ):
        with pytest.raises(input_error) as exc:
            e.fleet_mean_vehicle_weight(weights, fractions)
        assert exc.value.argument in {arg, "weights", "traffic_fractions"}, (weights, fractions)
        if len(weights) == len(fractions):
            assert exc.value.argument == arg
    for bad in ("abc", None, 1 + 2j, True, np.array(["a", "b"])):
        with pytest.raises(input_type_error) as exc:
            e.fleet_mean_vehicle_weight(bad, f)
        assert exc.value.argument == "weights"
        with pytest.raises(input_type_error) as exc:
            e.fleet_mean_vehicle_weight(w, bad)
        assert exc.value.argument == "traffic_fractions"
    assert e.fleet_mean_vehicle_weight(w, np.array([0.0, 1.0])) == pytest.approx(60_000.0)  # one zero fraction is fine
