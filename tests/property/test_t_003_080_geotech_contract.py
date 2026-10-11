# ruff: noqa: E501
"""T-003-080 (FR-003-20, FR-003-21, FR-003-23, FR-003-24, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12,
FR-000-13, FR-000-18, P-000-01..04).

Domain table of spec 003 section 7.2 (`InputError` naming the argument), unit tripwires of section 7.3
(`ValidityWarning` naming the argument and the row, result still returned), the option errors of FR-003-24 and
the constructed-input errors of FR-003-23, and the foundation contract suite (`tests/_contract_suite.py`,
T-000-010) on EVERY `minephys.geotech` function: purity, dtype invariance, elementwise = scalar evaluation,
the hostile battery, shape and empty-array handling, seeded reproducibility of the three sampling functions.
Plus the knowledge pin of the one verified row not covered by the unit tests (`gbsar_ku_band_wavelength`,
documented but never a default).

Conventions (stated so that the implementation can follow them): `ValidityWarning.row` is the row id of
section 7.3 and its message names the argument and the row; a tripwire fires strictly outside its limit
(exactly 1e5 Pa and 1e9 Pa, 1000 N/m^3, 100 Pa, 1.2 rad, 1e-2 m/s, 1e-4 m and 1 m are silent; a cohesion of
exactly 0 is silent); the scalar-only arguments (everything that is not an array of slices, samples, times,
positions or phases) raise an `InputError` naming the argument when given an array; an array argument with a
NaN or infinity names the argument and the index of the first offender in its message; per-slice arrays of
unequal length are an `InputError` naming at least one of them; empty slice, time or sample arrays are an
`InputError`; `required_samples` returns numpy int64 (array or scalar); the result of `inverse_velocity_ttf`
has the attributes failure_time, slope, intercept, r_squared, accelerating, n_used and that of `bayesian_ttf`
posterior_mean, posterior_cov, failure_time_median, failure_time_lower, failure_time_upper,
fraction_not_accelerating (see their unit tests); the result of `circular_slices` has width, weight,
base_angle, base_length, pore_pressure.

Oracle: analytical (the tables are the specification) and the foundation contract suite.
"""

from __future__ import annotations

import inspect
import math
import re
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import _contract_suite as cs
import numpy as np
import pytest
from _table_helpers_a import rows_by_id
from hypothesis import given, reject, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

import minephys
from minephys import geotech as G

INF = math.inf
HALF_PI = math.pi / 2.0
TWO_THIRDS = 2.0 / 3.0
FT = 0.3048
LBF = 0.45359237 * 9.80665
GAMMA_FK = 120.0 * LBF / FT**3
T5 = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
Y5 = np.array([1000.0, 820.0, 610.0, 430.0, 210.0])
V5 = 1.0 / Y5
MB, S, A = 1.676772, 3.86592e-3, 0.505734  # GSI = 50, mi = 10, D = 0 (spec 003 7.4)

BASE: dict[str, dict[str, Any]] = {
    "hoek_brown_parameters": {"gsi": 50.0, "mi": 10.0, "disturbance": 0.0},
    "hoek_brown_sigma1": {"sigma3": 1.0e6, "sigma_ci": 50.0e6, "mb": MB, "s": S, "a": A},
    "hoek_brown_uniaxial_strength": {"sigma_ci": 50.0e6, "s": S, "a": A},
    "hoek_brown_tensile_strength": {"sigma_ci": 50.0e6, "mb": MB, "s": S},
    "hoek_brown_rock_mass_strength": {"sigma_ci": 50.0e6, "mb": MB, "s": S, "a": A},
    "equivalent_mohr_coulomb": {"sigma_ci": 50.0e6, "mb": MB, "s": S, "a": A, "sigma3_max": 2.0e6},
    "sigma3_max": {"sigma_cm": 3.0e6, "unit_weight": 27000.0, "height": 100.0, "application": "slope"},
    "circular_slices": {
        "surface_x": np.array([0.0, 60.0, 140.0, 180.0]) * FT,
        "surface_z": np.array([60.0, 60.0, 20.0, 20.0]) * FT,
        "center_x": 120.0 * FT,
        "center_z": 90.0 * FT,
        "radius": 80.0 * FT,
        "n_slices": 20,
        "unit_weight": GAMMA_FK,
        "pore_pressure_ratio": 0.0,
    },
    "bishop_simplified_fos": {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.zeros(3),
        "cohesion": 5000.0,
        "friction_angle": math.radians(25.0),
    },
    "spencer_fos": {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.zeros(3),
        "cohesion": 5000.0,
        "friction_angle": math.radians(25.0),
    },
    "monte_carlo_fos": {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.zeros(3),
        "cohesion_mean": 5000.0,
        "cohesion_sd": 500.0,
        "friction_mean": math.radians(25.0),
        "friction_sd": math.radians(1.0),
        "n_samples": 50,
        "rng": 1,
        "method": "bishop",
    },
    "probability_of_failure": {"fos_samples": np.array([0.8, 1.1, 1.5, 2.0]), "threshold": 1.0},
    "required_samples": {"pof": 0.05, "relative_error": 0.1},
    "voight_creep_series": {"t": np.array([0.0, 1.0e5, 2.0e5]), "failure_time": 1.0e6, "a": 2.0, "alpha": 2.5},
    "inverse_velocity_ttf": {"t": T5, "velocity": V5},
    "bayesian_ttf": {"t": T5, "velocity": V5, "rng": 1, "noise_sd": 20.0, "n_draws": 200, "credible": 0.9},
    "slope_radar_los": {
        "displacement": np.array([-0.01, 0.01, 0.0]),
        "radar_position": np.zeros(3),
        "target_position": np.array([1000.0, 0.0, 0.0]),
    },
    "los_phase": {"los_displacement": 0.002, "wavelength": 0.0175, "rng": 1},
    "wrap_phase": {"phase": 4.0},
    "los_from_phase": {"phase": 1.0, "wavelength": 0.0175},
    "max_unambiguous_los_step": {"wavelength": 0.0175},
}
ELEMENTWISE = [
    "hoek_brown_parameters",
    "hoek_brown_sigma1",
    "hoek_brown_uniaxial_strength",
    "hoek_brown_tensile_strength",
    "hoek_brown_rock_mass_strength",
    "equivalent_mohr_coulomb",
    "sigma3_max",
    "required_samples",
    "los_phase",
    "wrap_phase",
    "los_from_phase",
    "max_unambiguous_los_step",
]
AGGREGATE = sorted(set(BASE) - set(ELEMENTWISE))
TUPLE_SIZE = {"hoek_brown_parameters": 3, "equivalent_mohr_coulomb": 2}
INTEGER_RESULT = {"required_samples"}
NON_NUMERIC = {"method", "application", "rng"}
FIELDS = {
    "circular_slices": ("width", "weight", "base_angle", "base_length", "pore_pressure"),
    "inverse_velocity_ttf": ("failure_time", "slope", "intercept", "r_squared", "accelerating", "n_used"),
    "bayesian_ttf": (
        "posterior_mean",
        "posterior_cov",
        "failure_time_median",
        "failure_time_lower",
        "failure_time_upper",
        "fraction_not_accelerating",
    ),
}

POS = ([0.0, -1.0, -1e-300, -INF], [])  # > 0
NONNEG = ([-1e-9, -1.0, -1e300], [0.0])  # >= 0
FINITE: tuple[list[float], list[float]] = ([], [-1.0, 0.0, 1.0])
OPEN01 = ([0.0, 1.0, -0.1, 1.5, 100.0], [0.5])  # (0, 1)
S_DOM = ([0.0, -1.0, 1.0000001, 2.0], [1.0, 1e-9])  # (0, 1]
A_DOM = ([0.4999999, 0.0, 0.6666667, 1.0, -0.5], [0.5, TWO_THIRDS])  # [1/2, 2/3]
FRICTION = ([-1e-9, -0.1, HALF_PI, 2.0, 90.0], [0.0])  # [0, pi/2)
SLICE_ANGLE = ([-HALF_PI, HALF_PI, 1.6, -1.6, 4.0, 100.0], [0.0])  # (-pi/2, pi/2)
GSI = ([0.0, -1.0, 100.0001, 101.0, 1e6], [100.0, 1e-9, 0.5])  # (0, 100]
D_DOM = ([-1e-9, -0.01, 1.0000001, 2.0], [0.0, 1.0])  # [0, 1]
COUNT_SLICES = ([0, 1, -1, 10_001, 10**9, 2.5], [2, 10_000])
COUNT_ITER = ([0, -1, 10_001, 10**6, 2.5], [200, 10_000])
COUNT_SAMPLES = ([0, -1, 10**6 + 1, 2**40, 2.5], [1, 100])
COUNT_DRAWS = ([0, 1, 99, 10**6 + 1, 100.5, -1], [100, 500])
COUNT_WINDOW = ([0, 1, 2, -1, 2.5], [3, 5])
SLICES = {"width": POS, "weight": NONNEG, "base_angle": SLICE_ANGLE, "pore_pressure": NONNEG}
DOMAIN: dict[str, dict[str, tuple[list[float], list[float]]]] = {
    "hoek_brown_parameters": {"gsi": GSI, "mi": POS, "disturbance": D_DOM},
    "hoek_brown_sigma1": {
        "sigma3": ([-1e6, -2e5, -1e9], [0.0, -1e5]),
        "sigma_ci": POS,
        "mb": POS,
        "s": S_DOM,
        "a": A_DOM,
    },
    "hoek_brown_uniaxial_strength": {"sigma_ci": POS, "s": S_DOM, "a": A_DOM},
    "hoek_brown_tensile_strength": {"sigma_ci": POS, "mb": POS, "s": S_DOM},
    "hoek_brown_rock_mass_strength": {"sigma_ci": POS, "mb": POS, "s": S_DOM, "a": A_DOM},
    "equivalent_mohr_coulomb": {"sigma_ci": POS, "mb": POS, "s": S_DOM, "a": A_DOM, "sigma3_max": NONNEG},
    "sigma3_max": {"sigma_cm": POS, "unit_weight": POS, "height": POS},
    "circular_slices": {
        "radius": ([0.0, -1.0, -1e-300, -INF], []),
        "unit_weight": POS,
        "pore_pressure_ratio": ([-1e-9, -0.1, 1.0, 1.5, 100.0], [0.0, 0.5, 0.999]),
        "n_slices": COUNT_SLICES,
    },
    "bishop_simplified_fos": {
        **SLICES,
        "cohesion": NONNEG,
        "friction_angle": FRICTION,
        "max_iter": COUNT_ITER,
    },
    "spencer_fos": {**SLICES, "cohesion": NONNEG, "friction_angle": FRICTION, "max_iter": COUNT_ITER},
    "monte_carlo_fos": {
        **SLICES,
        "cohesion_mean": NONNEG,
        "cohesion_sd": NONNEG,
        "friction_mean": FRICTION,
        "friction_sd": NONNEG,
        "n_samples": COUNT_SAMPLES,
    },
    "required_samples": {"pof": OPEN01, "relative_error": POS},
    "voight_creep_series": {
        "failure_time": POS,
        "a": POS,
        "alpha": ([1.0, 0.5, 0.0, -2.0, -INF], [1.5, 2.0]),
    },
    "inverse_velocity_ttf": {"velocity": POS, "window": COUNT_WINDOW},
    "bayesian_ttf": {
        "velocity": POS,
        "noise_sd": ([-1e-12, -0.1, -5.0], [20.0, 1e-3]),
        "credible": OPEN01,
        "n_draws": COUNT_DRAWS,
        "window": COUNT_WINDOW,
    },
    "los_phase": {"wavelength": POS, "noise_sd": ([-1e-12, -1.0], [0.0])},
    "los_from_phase": {"wavelength": POS},
    "max_unambiguous_los_step": {"wavelength": POS},
}
CASES = [(fn, arg, bad) for fn, args in DOMAIN.items() for arg, (invalid, _) in args.items() for bad in invalid]
BOUNDARIES = [(fn, arg, ok) for fn, args in DOMAIN.items() for arg, (_, valid) in args.items() for ok in valid]


def with_value(fn: str, arg: str, value: Any) -> dict[str, Any]:
    kwargs = dict(BASE[fn])
    cur = kwargs.get(arg)
    if isinstance(cur, np.ndarray) and cur.ndim == 1 and cur.size > 1 and np.ndim(value) == 0:
        arr = cur.astype(float).copy()
        arr[1] = value  # one bad element in the middle of the array
        kwargs[arg] = arr
    else:
        kwargs[arg] = value
    return kwargs


def call(fn: str, kwargs: dict[str, Any]) -> Any:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return getattr(G, fn)(**kwargs)


def id_of(case: tuple) -> str:
    return "-".join(str(c) for c in case)


# ------------------------------------------------------------------ FR-003-20: domain


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "spec 003 7.2: a value outside the physical domain is an InputError naming the argument"
)
@pytest.mark.parametrize(("fn", "arg", "bad"), CASES, ids=[id_of(c) for c in CASES])
def test_domain_violation_is_an_input_error(fn: str, arg: str, bad: Any) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(fn, with_value(fn, arg, bad))
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: the closed ends of every interval are accepted")
@pytest.mark.parametrize(("fn", "arg", "ok"), BOUNDARIES, ids=[id_of(c) for c in BOUNDARIES])
def test_domain_boundary_is_accepted(fn: str, arg: str, ok: Any) -> None:
    assert call(fn, with_value(fn, arg, ok)) is not None


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: NaN and infinity are not a value anywhere in this module")
@pytest.mark.parametrize("fn", sorted(DOMAIN))
def test_non_finite_is_rejected_everywhere(fn: str) -> None:
    for arg in DOMAIN[fn]:
        for bad in (INF, -INF, math.nan):
            with pytest.raises(minephys.InputError) as ei:
                call(fn, with_value(fn, arg, bad))
            assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "an out-of-domain element of an elementwise array raises, naming the argument")
@pytest.mark.parametrize(
    ("fn", "arg", "bad"),
    [
        ("hoek_brown_parameters", "gsi", 0.0),
        ("hoek_brown_tensile_strength", "s", 1.5),
        ("sigma3_max", "height", -1.0),
        ("required_samples", "pof", 1.0),
        ("los_from_phase", "wavelength", 0.0),
        ("max_unambiguous_los_step", "wavelength", -0.5),
    ],
)
def test_bad_element_in_an_array(fn: str, arg: str, bad: float) -> None:
    base = float(BASE[fn][arg])
    arr = np.array([base, bad, base])
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: arr})
    assert ei.value.argument == arg


# ------------------------------------------------------------------ FR-003-21: tripwires


@dataclass(frozen=True)
class Wire:
    row: str
    args: dict[str, str]  # function -> the argument it watches
    loud: tuple[float, ...]
    quiet: tuple[float, ...]
    extra: dict[str, Any] = field(default_factory=dict)


SIGMA_CI_FUNCTIONS = {
    f: "sigma_ci"
    for f in (
        "hoek_brown_sigma1",
        "hoek_brown_uniaxial_strength",
        "hoek_brown_tensile_strength",
        "hoek_brown_rock_mass_strength",
        "equivalent_mohr_coulomb",
    )
}
WIRES = [
    Wire("tripwire_sigma_ci_min", SIGMA_CI_FUNCTIONS, (99_999.0, 5e4, 1e3, 1.0), (1e5, 5e7)),
    Wire("tripwire_sigma_ci_max", SIGMA_CI_FUNCTIONS, (1_000_000_001.0, 5e10, 1e12), (1e9, 5e8)),
    Wire(
        "tripwire_cohesion_min",
        {"bishop_simplified_fos": "cohesion", "spencer_fos": "cohesion", "monte_carlo_fos": "cohesion_mean"},
        (99.99, 50.0, 1e-3, 1e-9),
        (100.0, 5000.0, 0.0),
    ),
    Wire(
        "tripwire_unit_weight_min",
        {"sigma3_max": "unit_weight", "circular_slices": "unit_weight"},
        (999.9, 10.0, 1e-3),
        (1000.0, 27000.0),
    ),
    Wire(
        "tripwire_friction_angle_max",
        {
            "bishop_simplified_fos": "friction_angle",
            "spencer_fos": "friction_angle",
            "monte_carlo_fos": "friction_mean",
        },
        (1.2000001, 1.25, 1.3),
        (1.2, 0.5, 0.0),
    ),
    Wire(
        "tripwire_slope_velocity_max",
        {"inverse_velocity_ttf": "velocity", "bayesian_ttf": "velocity"},
        (0.0100001, 0.02, 1.0, 50.0),
        (0.01, 1e-3, 1e-9),
    ),
    Wire(
        "tripwire_wavelength_range",
        {"los_phase": "wavelength", "los_from_phase": "wavelength", "max_unambiguous_los_step": "wavelength"},
        (9.9999e-5, 1e-6, 1.0000001, 10.0),
        (1e-4, 1.0, 0.0175),
    ),
]
WIRE_BY_ROW = {w.row: w for w in WIRES}
LOUD = [(w.row, fn, v) for w in WIRES for fn in w.args for v in w.loud]
QUIET = [(w.row, fn, v) for w in WIRES for fn in w.args for v in w.quiet]


def validity(fn: str, kwargs: dict[str, Any]) -> tuple[Any, list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        result = getattr(G, fn)(**kwargs)
    return result, [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical",
    "spec 003 7.3: each unit tripwire warns, naming the argument and the row, and still returns the result",
)
@pytest.mark.parametrize(("row", "fn", "value"), LOUD, ids=[id_of(c) for c in LOUD])
def test_wire_warns_and_still_returns(row: str, fn: str, value: float) -> None:
    arg = WIRE_BY_ROW[row].args[fn]
    result, found = validity(fn, with_value(fn, arg, value))
    assert result is not None
    hits = [x for x in found if x.message.row == row]
    assert hits, f"no {row} warning in {[str(x.message) for x in found]}"
    msg = hits[0].message
    assert msg.argument == arg
    assert row in str(msg)
    assert arg in str(msg)


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle("analytical", "spec 003 7.3: values inside the limits, and exactly on them, stay silent")
@pytest.mark.parametrize(("row", "fn", "value"), QUIET, ids=[id_of(c) for c in QUIET])
def test_values_inside_the_wires_are_silent(row: str, fn: str, value: float) -> None:
    arg = WIRE_BY_ROW[row].args[fn]
    _, found = validity(fn, with_value(fn, arg, value))
    assert [x for x in found if x.message.row == row] == []


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical", "an array warns if any one element trips the wire; an array within the limits is silent"
)
def test_one_element_of_an_array_is_enough() -> None:
    base = BASE["max_unambiguous_los_step"]
    _, found = validity("max_unambiguous_los_step", {**base, "wavelength": np.array([0.0175, 0.03, 5.0])})
    assert any(w.message.row == "tripwire_wavelength_range" for w in found)
    _, none = validity("max_unambiguous_los_step", {**base, "wavelength": np.array([0.0175, 0.03, 0.3])})
    assert none == []
    _, vel = validity(
        "inverse_velocity_ttf", {**BASE["inverse_velocity_ttf"], "velocity": np.array([1e-3, 1e-3, 0.5, 1e-3, 1e-3])}
    )
    assert any(w.message.row == "tripwire_slope_velocity_max" for w in vel)


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle("analytical", "the worked baseline calls of spec 003 7.4 trip no wire at all")
@pytest.mark.parametrize("fn", sorted(BASE))
def test_the_worked_examples_are_silent(fn: str) -> None:
    _, found = validity(fn, dict(BASE[fn]))
    assert found == []


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical", "the two sigma_ci rows are distinct: a value below 1e5 Pa names _min, above 1e9 Pa names _max"
)
def test_the_sigma_ci_rows_are_distinct() -> None:
    low = validity("hoek_brown_uniaxial_strength", with_value("hoek_brown_uniaxial_strength", "sigma_ci", 5e4))[1]
    high = validity("hoek_brown_uniaxial_strength", with_value("hoek_brown_uniaxial_strength", "sigma_ci", 5e10))[1]
    assert {w.message.row for w in low} == {"tripwire_sigma_ci_min"}
    assert {w.message.row for w in high} == {"tripwire_sigma_ci_max"}


# ------------------------------------------------------------------ FR-003-24: options


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "options are exact strings; the error lists the allowed values")
@pytest.mark.parametrize("bad", ["Bishop", "SPENCER", "janbu", "", " bishop", "bishop ", "bïshop"])
def test_method_option_errors(bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call("monte_carlo_fos", {**BASE["monte_carlo_fos"], "method": bad})
    assert ei.value.argument == "method"
    assert "bishop" in str(ei.value)
    assert "spencer" in str(ei.value)


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "application is exactly 'slope' or 'tunnel'; the error lists both values")
@pytest.mark.parametrize("bad", ["Slope", "TUNNEL", "road", "", " slope", "tunnel ", "tünnel"])
def test_application_option_errors(bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call("sigma3_max", {**BASE["sigma3_max"], "application": bad})
    assert ei.value.argument == "application"
    assert "slope" in str(ei.value)
    assert "tunnel" in str(ei.value)


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "a non-string option is an error naming the argument (type or value)")
@pytest.mark.parametrize(("fn", "arg"), [("monte_carlo_fos", "method"), ("sigma3_max", "application")])
@pytest.mark.parametrize("bad", [None, 1, 1.5, b"slope", ["slope"], object()])
def test_non_string_option(fn: str, arg: str, bad: Any) -> None:
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as ei:
        call(fn, {**BASE[fn], arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "the valid options are accepted")
def test_valid_options() -> None:
    for method in ("bishop", "spencer"):
        assert call("monte_carlo_fos", {**BASE["monte_carlo_fos"], "method": method, "n_samples": 5}).shape == (5,)
    for application in ("slope", "tunnel"):
        assert float(call("sigma3_max", {**BASE["sigma3_max"], "application": application})) > 0.0


# ------------------------------------------------------------------ FR-003-23: constructed-input errors


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle(
    "analytical", "noise_sd > 0 without rng, a bad prior, a non-increasing t, fewer than 3 samples, counts out of range"
)
def test_constructed_input_errors() -> None:
    def raises(fn: str, arg: str | tuple[str, ...], **over: Any) -> None:
        with pytest.raises(minephys.InputError) as ei:
            call(fn, {**BASE[fn], **over})
        names = (arg,) if isinstance(arg, str) else arg
        assert ei.value.argument in names

    raises("los_phase", "rng", noise_sd=0.1, rng=None)
    raises("bayesian_ttf", "prior_cov", prior_mean=[1000.0, -20.0], prior_cov=[[1.0, 2.0], [2.0, 1.0]])
    raises("bayesian_ttf", "prior_cov", prior_mean=[1000.0, -20.0], prior_cov=[[1.0, 0.5], [0.4, 1.0]])
    raises(
        "bayesian_ttf",
        "prior_cov",
        prior_mean=[1000.0, -20.0],
        prior_cov=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    raises("bayesian_ttf", "prior_mean", prior_mean=[1000.0], prior_cov=[[1.0, 0.0], [0.0, 1.0]])
    raises("inverse_velocity_ttf", "t", t=np.array([0.0, 10.0, 10.0, 30.0, 40.0]))
    raises("bayesian_ttf", "t", t=np.array([0.0, 20.0, 10.0, 30.0, 40.0]))
    raises("inverse_velocity_ttf", ("t", "velocity"), t=T5[:2], velocity=V5[:2])
    raises("bayesian_ttf", ("t", "velocity"), t=T5[:2], velocity=V5[:2])
    raises("inverse_velocity_ttf", "window", window=2)
    raises("monte_carlo_fos", "n_samples", n_samples=0)
    raises("monte_carlo_fos", "n_samples", n_samples=10**6 + 1)
    raises("bayesian_ttf", "n_draws", n_draws=99)
    raises("bayesian_ttf", "n_draws", n_draws=10**6 + 1)


# ------------------------------------------------------------------ rank and shape of aggregate functions

SCALAR_ONLY = {
    "circular_slices": ("center_x", "center_z", "radius", "n_slices", "unit_weight", "pore_pressure_ratio"),
    "monte_carlo_fos": ("cohesion_mean", "cohesion_sd", "friction_mean", "friction_sd", "n_samples"),
    "probability_of_failure": ("threshold",),
    "voight_creep_series": ("failure_time", "a", "alpha"),
    "bayesian_ttf": ("noise_sd", "n_draws", "credible"),
}
RANK_CASES = [(fn, arg) for fn, args in SCALAR_ONLY.items() for arg in args]


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("analytical", "scalar-only arguments given an array are an InputError naming the argument")
@pytest.mark.parametrize(("fn", "arg"), RANK_CASES, ids=[id_of(c) for c in RANK_CASES])
def test_scalar_only_arguments_reject_arrays(fn: str, arg: str) -> None:
    value = BASE[fn][arg]
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: np.array([value, value])})
    assert ei.value.argument == arg


SLICE_FUNCTIONS = ["bishop_simplified_fos", "spencer_fos", "monte_carlo_fos"]


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("analytical", "per-slice arrays of unequal length are an InputError naming one of them")
@pytest.mark.parametrize("fn", SLICE_FUNCTIONS)
@pytest.mark.parametrize(
    ("first", "second"),
    [("width", "weight"), ("weight", "base_angle"), ("base_angle", "pore_pressure"), ("pore_pressure", "width")],
)
def test_unequal_slice_arrays(fn: str, first: str, second: str) -> None:
    kwargs = dict(BASE[fn])
    kwargs[second] = np.append(np.asarray(kwargs[second], dtype=float), kwargs[second][-1])  # one slice more
    with pytest.raises(minephys.InputError) as ei:
        call(fn, kwargs)
    assert ei.value.argument in {first, second, "width", "weight", "base_angle", "pore_pressure"}


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("analytical", "empty slice, time, sample and polyline arrays are an InputError naming the argument")
@pytest.mark.parametrize(
    ("fn", "arg"),
    [
        ("bishop_simplified_fos", "width"),
        ("spencer_fos", "width"),
        ("monte_carlo_fos", "width"),
        ("circular_slices", "surface_x"),
        ("probability_of_failure", "fos_samples"),
        ("voight_creep_series", "t"),
        ("inverse_velocity_ttf", "t"),
        ("bayesian_ttf", "t"),
    ],
)
def test_empty_arrays_are_errors_in_aggregates(fn: str, arg: str) -> None:
    kwargs = dict(BASE[fn])
    kwargs[arg] = np.empty(0)
    if fn in SLICE_FUNCTIONS:
        for other in ("weight", "base_angle", "pore_pressure"):
            kwargs[other] = np.empty(0)
    if fn in {"inverse_velocity_ttf", "bayesian_ttf"}:
        kwargs["velocity"] = np.empty(0)
    with pytest.raises(minephys.InputError) as ei:
        call(fn, kwargs)
    assert ei.value.argument in {arg, "surface_z", "width", "weight", "base_angle", "pore_pressure", "velocity", "t"}


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle(
    "analytical", "an elementwise function given empty arrays returns an empty float64 array (int64 for counts)"
)
@pytest.mark.parametrize("name", ELEMENTWISE)
def test_empty_arrays_in_elementwise_functions(name: str) -> None:
    arg = next(iter(BASE[name]))
    out = call(name, {**BASE[name], arg: np.empty(0)})
    parts = list(out) if isinstance(out, tuple) else [out]
    assert len(parts) == TUPLE_SIZE.get(name, 1)
    for part in parts:
        assert part.shape == (0,)
        assert part.dtype == (np.int64 if name in INTEGER_RESULT else np.float64)


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("analytical", "slope_radar_los given an empty leading shape returns an empty float64 array")
def test_empty_radar_input() -> None:
    out = call("slope_radar_los", {**BASE["slope_radar_los"], "displacement": np.empty((0, 3))})
    assert out.shape == (0,)
    assert out.dtype == np.float64


# ------------------------------------------------------------------ foundation contract suite: elementwise functions


def f32(lo: float, hi: float) -> st.SearchStrategy[float]:
    # bounds rounded to the nearest float32; "+ 0.0" turns -0.0 into 0.0 (its integer variant would differ in the sign bit)
    return st.floats(float(np.float32(lo)), float(np.float32(hi)), width=32).map(lambda x: x + 0.0)


@dataclass(frozen=True)
class Op:
    strategies: dict[str, st.SearchStrategy[Any]]
    fixed: dict[str, Any] = field(default_factory=dict)


SIGMA_CI = f32(2e6, 3e8)
MB_S = f32(0.1, 30.0)
S_S = f32(1e-6, 1.0)
A_S = f32(0.5, 0.66666)
OPS: dict[str, Op] = {
    "hoek_brown_parameters": Op({"gsi": f32(1.0, 100.0), "mi": f32(5.0, 35.0), "disturbance": f32(0.0, 1.0)}),
    "hoek_brown_sigma1": Op({"sigma3": f32(0.0, 2e7), "sigma_ci": SIGMA_CI, "mb": MB_S, "s": S_S, "a": A_S}),
    "hoek_brown_uniaxial_strength": Op({"sigma_ci": SIGMA_CI, "s": S_S, "a": A_S}),
    "hoek_brown_tensile_strength": Op({"sigma_ci": SIGMA_CI, "mb": MB_S, "s": S_S}),
    "hoek_brown_rock_mass_strength": Op({"sigma_ci": SIGMA_CI, "mb": MB_S, "s": S_S, "a": A_S}),
    "equivalent_mohr_coulomb": Op({"sigma_ci": SIGMA_CI, "mb": MB_S, "s": S_S, "a": A_S, "sigma3_max": f32(0.0, 2e7)}),
    "sigma3_max": Op(
        {"sigma_cm": f32(1e5, 1e9), "unit_weight": f32(1e4, 3e4), "height": f32(10.0, 500.0)}, {"application": "slope"}
    ),
    "required_samples": Op({"pof": f32(1e-3, 0.999), "relative_error": f32(0.01, 1.0)}),
    "los_phase": Op({"los_displacement": f32(-1.0, 1.0), "wavelength": f32(1e-3, 0.3)}),
    "wrap_phase": Op({"phase": f32(-1e3, 1e3)}),
    "los_from_phase": Op({"phase": f32(-1e3, 1e3), "wavelength": f32(1e-3, 0.3)}),
    "max_unambiguous_los_step": Op({"wavelength": f32(1e-3, 0.3)}),
}


@st.composite
def operands(draw: Callable, op: Op) -> dict[str, Any]:
    shape = draw(hnp.array_shapes(min_dims=0, max_dims=2, min_side=0, max_side=4))
    kwargs: dict[str, Any] = dict(op.fixed)
    for name, strat in op.strategies.items():
        mode = draw(st.sampled_from(["scalar", "full", "row"])) if shape else "scalar"
        if mode == "scalar":
            kwargs[name] = np.float64(draw(strat))
        else:
            shp = shape if mode == "full" else shape[-1:]
            n = int(np.prod(shp))
            kwargs[name] = np.array(draw(st.lists(strat, min_size=n, max_size=n)), dtype=np.float64).reshape(shp)
    return kwargs


def parts_of(fn: Callable[..., Any], index: int | None, as_float: bool) -> Callable[..., Any]:
    """Wrap `fn` so that it returns one float64 output (the `index`-th of a tuple, int64 cast to float64 for counts)."""

    def wrapped(**kw: Any) -> Any:
        out = fn(**kw)
        if index is not None:
            out = out[index]
        if as_float:
            return np.float64(out) if np.ndim(out) == 0 else np.asarray(out, dtype=np.float64)
        return out

    return wrapped


@pytest.mark.req("FR-000-05")
@pytest.mark.req("FR-000-07")
@pytest.mark.req("P-000-01")
@pytest.mark.req("P-000-02")
@pytest.mark.req("P-000-03")
@pytest.mark.oracle(
    "analytical", "foundation contract suite: purity, float32 and int operands, elementwise = scalar evaluation"
)
@pytest.mark.parametrize("name", ELEMENTWISE)
@settings(deadline=None)
@given(data=st.data())
def test_contract_suite_on_elementwise_functions(name: str, data: st.DataObject) -> None:
    kwargs = data.draw(operands(OPS[name]))
    fn = getattr(G, name)
    as_float = name in INTEGER_RESULT
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for index in range(TUPLE_SIZE.get(name, 1)):
            wrapped = parts_of(fn, index if name in TUPLE_SIZE else None, as_float)
            cs.check_purity(wrapped, kwargs)
            cs.check_dtype_invariance(wrapped, kwargs)
            cs.check_elementwise(wrapped, kwargs)
        out = fn(**kwargs)
        for part in out if isinstance(out, tuple) else (out,):
            if as_float:
                assert (part.dtype == np.int64) if np.ndim(part) else (type(part) is np.int64)
            elif np.ndim(part) == 0:
                assert type(part) is np.float64
            else:
                assert part.dtype == np.float64


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "foundation hostile battery: NaN, inf, wrong types name the argument")
@pytest.mark.parametrize(
    ("name", "arg"), [(n, a) for n in ELEMENTWISE for a in OPS[n].strategies], ids=lambda v: str(v)
)
def test_hostile_battery_on_elementwise_functions(name: str, arg: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(getattr(G, name), dict(BASE[name]), arg)


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle(
    "analytical", "arrays of shapes (3,) and (4,) cannot broadcast: InputError naming both arguments and shapes"
)
@pytest.mark.parametrize("name", [n for n in ELEMENTWISE if len(OPS[n].strategies) >= 2])
def test_shape_mismatch(name: str) -> None:
    first, second = list(OPS[name].strategies)[:2]
    kwargs = dict(BASE[name])
    kwargs[first] = np.full(3, float(kwargs[first]))
    kwargs[second] = np.full(4, float(kwargs[second]))
    with pytest.raises(minephys.InputError) as ei:
        call(name, kwargs)
    msg = str(ei.value)
    assert first in msg
    assert second in msg
    assert "(3,)" in msg
    assert "(4,)" in msg


# ------------------------------------------------------------------ foundation contract suite: aggregate and sampling functions


def flat(name: str) -> Callable[..., np.ndarray]:
    """Call `name` and flatten its result (array, tuple or named record) into one float64 vector."""

    def go(**kw: Any) -> np.ndarray:
        out = getattr(G, name)(**kw)
        if name in FIELDS:
            parts = [getattr(out, f) for f in FIELDS[name]]
        elif isinstance(out, tuple):
            parts = list(out)
        else:
            parts = [out]
        return np.concatenate([np.ravel(np.asarray(p, dtype=np.float64)) for p in parts])

    return go


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle(
    "analytical", "every aggregate and sampling function is pure: bitwise-identical on two calls, inputs untouched"
)
@pytest.mark.parametrize("name", AGGREGATE)
def test_purity_of_aggregate_functions(name: str) -> None:
    kwargs = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in BASE[name].items()}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_purity(flat(name), kwargs)


@st.composite
def slice_arrays(draw: Callable, n_min: int = 3, n_max: int = 10) -> dict[str, np.ndarray]:
    n = draw(st.integers(n_min, n_max))

    def arr(lo: float, hi: float) -> np.ndarray:
        return np.array(draw(st.lists(f32(lo, hi), min_size=n, max_size=n)), dtype=np.float64)

    return {
        "width": arr(1.0, 5.0),
        "weight": arr(1e5, 1e6),
        "base_angle": arr(0.05, 0.9),
        "pore_pressure": arr(0.0, 5e4),
    }


@st.composite
def sorted_times(draw: Callable, n_min: int = 3, n_max: int = 12) -> np.ndarray:
    values = draw(st.lists(st.integers(0, 900_000), min_size=n_min, max_size=n_max, unique=True))
    return np.array(sorted(values), dtype=np.float64)


@st.composite
def aggregate_operands(draw: Callable, name: str) -> dict[str, Any]:
    if name in {"bishop_simplified_fos", "spencer_fos"}:
        return {
            **draw(slice_arrays()),
            "cohesion": np.float64(draw(f32(5e3, 5e4))),
            "friction_angle": np.float64(draw(f32(0.2, 0.7))),
        }
    if name == "monte_carlo_fos":
        return {
            **draw(slice_arrays()),
            "cohesion_mean": np.float64(draw(f32(5e3, 5e4))),
            "cohesion_sd": np.float64(draw(f32(0.0, 2e3))),
            "friction_mean": np.float64(draw(f32(0.3, 0.7))),
            "friction_sd": np.float64(draw(f32(0.0, 0.03))),
            "n_samples": 16,
            "rng": draw(st.integers(0, 2**32 - 1)),
            "method": draw(st.sampled_from(["bishop", "spencer"])),
        }
    if name == "circular_slices":
        return {
            "surface_x": np.array([0.0, 18.0, 42.0, 54.0]),
            "surface_z": np.array([18.0, 18.0, 6.0, 6.0]),
            "center_x": 30.0,
            "center_z": 30.0,
            "radius": 26.0,
            "n_slices": draw(st.integers(2, 40)),
            "unit_weight": 20000.0,
            "pore_pressure_ratio": draw(st.sampled_from([0.0, 0.25, 0.5])),
        }
    if name == "probability_of_failure":
        n = draw(st.integers(1, 30))
        return {
            "fos_samples": np.array(draw(st.lists(f32(0.1, 5.0), min_size=n, max_size=n)), dtype=np.float64),
            "threshold": np.float64(draw(f32(0.5, 2.0))),
        }
    if name == "voight_creep_series":
        return {
            "t": draw(sorted_times(1, 12)),
            "failure_time": 1.0e6,
            "a": np.float64(draw(f32(0.1, 10.0))),
            "alpha": np.float64(draw(f32(1.5, 4.0))),
        }
    if name in {"inverse_velocity_ttf", "bayesian_ttf"}:
        t = draw(sorted_times())
        n = t.size
        v = np.array(draw(st.lists(f32(1e-5, 5e-3), min_size=n, max_size=n)), dtype=np.float64)
        if name == "inverse_velocity_ttf":
            return {"t": t, "velocity": v}
        return {
            "t": t,
            "velocity": v,
            "rng": draw(st.integers(0, 2**32 - 1)),
            "noise_sd": np.float64(draw(f32(50.0, 500.0))),
            "n_draws": 100,
        }
    if name == "slope_radar_los":
        n = draw(st.integers(1, 6))

        def vec(lo: float, hi: float) -> np.ndarray:
            return np.array(draw(st.lists(f32(lo, hi), min_size=3 * n, max_size=3 * n)), dtype=np.float64).reshape(n, 3)

        return {
            "displacement": vec(-1.0, 1.0),
            "radar_position": vec(-50.0, 50.0),
            "target_position": vec(100.0, 900.0),
        }
    raise AssertionError(name)


@pytest.mark.req("FR-000-07")
@pytest.mark.req("P-000-03")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle(
    "analytical",
    "float32 and (where the values are integers) int32 array operands give the float64 result bitwise, for the aggregate functions",
)
@pytest.mark.parametrize("name", AGGREGATE)
@settings(deadline=None, max_examples=25)
@given(data=st.data())
def test_dtype_invariance_of_aggregate_functions(name: str, data: st.DataObject) -> None:
    kwargs = data.draw(aggregate_operands(name))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            cs.check_purity(flat(name), kwargs)
            cs.check_dtype_invariance(flat(name), kwargs)
        except minephys.ConvergenceError:
            reject()  # a draw the solver cannot converge on is not a dtype question


HOSTILE_TYPES = ("1.0", b"1", None, 1 + 1j, True, object(), np.datetime64("2026-01-01"))
OPTIONAL_NONE = {"window", "noise_sd", "prior_mean", "prior_cov"}
BATTERY_CASES = [(fn, arg) for fn in AGGREGATE for arg in BASE[fn] if arg not in NON_NUMERIC]


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle(
    "analytical",
    "hostile battery on the aggregate functions: NaN and infinity (scalar, or the first element of an array whose index is named) are InputError, wrong types InputTypeError",
)
@pytest.mark.parametrize(("fn", "arg"), BATTERY_CASES, ids=id_of)
def test_hostile_battery_on_aggregate_functions(fn: str, arg: str) -> None:
    kwargs = dict(BASE[fn])
    ref = kwargs[arg]
    for bad in (math.nan, INF, -INF):
        probe = dict(kwargs)
        if isinstance(ref, np.ndarray):
            arr = ref.astype(float).copy()
            arr.ravel()[0] = bad
            probe[arg] = arr
        else:
            probe[arg] = bad
        with pytest.raises(minephys.InputError) as ei:
            call(fn, probe)
        assert ei.value.argument == arg
        if isinstance(ref, np.ndarray):
            assert re.search(r"\b0\b", str(ei.value)), "the message names the index of the first offender"
    for bad in HOSTILE_TYPES:
        if bad is None and arg in OPTIONAL_NONE:
            continue  # None is the documented 'estimate it' value of noise_sd
        with pytest.raises(minephys.InputTypeError) as ei2:
            call(fn, {**kwargs, arg: bad})
        assert ei2.value.argument == arg


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle(
    "analytical", "optional arguments whose None is legal: NaN/inf are InputError, wrong types InputTypeError"
)
@pytest.mark.parametrize(
    ("fn", "arg", "value"),
    [("inverse_velocity_ttf", "window", 3), ("bayesian_ttf", "window", 3)],
)
def test_hostile_values_for_optional_counts(fn: str, arg: str, value: int) -> None:
    for bad in (math.nan, INF, -INF):
        with pytest.raises(minephys.InputError) as ei:
            call(fn, {**BASE[fn], arg: bad})
        assert ei.value.argument == arg
    for bad in ("3", b"3", 1 + 1j, True, object()):
        with pytest.raises(minephys.InputTypeError) as ei2:
            call(fn, {**BASE[fn], arg: bad})
        assert ei2.value.argument == arg
    assert call(fn, {**BASE[fn], arg: None}) is not None
    assert call(fn, {**BASE[fn], arg: value}) is not None


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("analytical", "the iteration controls of the two slope methods are validated like any other number")
@pytest.mark.parametrize("fn", ["bishop_simplified_fos", "spencer_fos"])
def test_hostile_battery_on_the_iteration_controls(fn: str) -> None:
    for arg in ("tol", "max_iter"):
        for bad in (math.nan, INF, -INF):
            with pytest.raises(minephys.InputError) as ei:
                call(fn, {**BASE[fn], arg: bad})
            assert ei.value.argument == arg
        for bad in HOSTILE_TYPES:
            with pytest.raises(minephys.InputTypeError) as ei2:
                call(fn, {**BASE[fn], arg: bad})
            assert ei2.value.argument == arg


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle(
    "analytical",
    "slice cohesion and friction angle may be per-slice arrays: a NaN inside names the argument and the index",
)
@pytest.mark.parametrize("fn", SLICE_FUNCTIONS[:2])
@pytest.mark.parametrize("arg", ["cohesion", "friction_angle"])
def test_per_slice_strength_arrays(fn: str, arg: str) -> None:
    good = np.full(3, BASE[fn][arg])
    assert call(fn, {**BASE[fn], arg: good}) is not None
    bad = good.copy()
    bad[0] = math.nan
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: bad})
    assert ei.value.argument == arg
    assert re.search(r"\b0\b", str(ei.value))


# ------------------------------------------------------------------ FR-000-18: sampling functions


SAMPLERS = {
    "monte_carlo_fos": {**BASE["monte_carlo_fos"]},
    "bayesian_ttf": {**BASE["bayesian_ttf"], "noise_sd": 300.0},
    "los_phase": {"los_displacement": np.linspace(0.0, 0.01, 20), "wavelength": 0.0175, "noise_sd": 0.1, "rng": 1},
}


@pytest.mark.req("FR-000-18")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle(
    "analytical",
    "same integer seed or Generator made from it: bitwise-identical output; a different seed gives different output (foundation check_seeded)",
)
@pytest.mark.parametrize("name", sorted(SAMPLERS))
def test_seeded_reproducibility(name: str) -> None:
    kwargs = {k: v for k, v in SAMPLERS[name].items() if k != "rng"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_seeded(flat(name), kwargs, rng_name="rng")


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle(
    "analytical", "sampling draws only from rng: NumPy's legacy global state is untouched, and rng has no default"
)
@pytest.mark.parametrize("name", sorted(SAMPLERS))
def test_no_global_state_and_no_default_rng(name: str) -> None:
    kwargs = dict(SAMPLERS[name])
    state = np.random.get_state()[1].copy()  # noqa: NPY002 - the legacy global state is exactly what must stay untouched
    call(name, kwargs)
    assert np.array_equal(np.random.get_state()[1], state), "global random state was used"  # noqa: NPY002
    default = inspect.signature(getattr(G, name)).parameters["rng"].default
    assert default is inspect.Parameter.empty or (name == "los_phase" and default is None)


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("analytical", "monte_carlo_fos and bayesian_ttf cannot run without rng")
@pytest.mark.parametrize("name", ["monte_carlo_fos", "bayesian_ttf"])
def test_rng_is_required(name: str) -> None:
    kwargs = {k: v for k, v in BASE[name].items() if k != "rng"}
    with pytest.raises(TypeError):
        getattr(G, name)(**kwargs)


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("analytical", "rng must be a Generator or an integer seed in 0..2**32-1")
@pytest.mark.parametrize("name", sorted(SAMPLERS))
def test_rng_validation(name: str) -> None:
    for bad in (None, 1.5, "7", b"7", True, np.array([1, 2]), np.random.RandomState(1), object()):
        if name == "los_phase" and bad is None:
            continue  # None is the 'no rng' default of los_phase; it is an InputError for noise_sd > 0, tested above
        with pytest.raises((minephys.InputTypeError, minephys.InputError)) as ei:
            call(name, {**SAMPLERS[name], "rng": bad})
        assert ei.value.argument == "rng"
    for bad in (-1, 2**32, 2**64):
        with pytest.raises(minephys.InputError) as ei2:
            call(name, {**SAMPLERS[name], "rng": bad})
        assert ei2.value.argument == "rng"


# ------------------------------------------------------------------ knowledge pin of the remaining verified row


@pytest.mark.req("FR-003-19")
@pytest.mark.knowledge("gbsar_ku_band_wavelength")
@pytest.mark.oracle(
    "worked-example", "wolff2023 p. 8 (preprint): Ku-band wavelength 1.75 cm, documented but never a default"
)
def test_row_gbsar_ku_band_wavelength() -> None:
    row = rows_by_id("geotech")["gbsar_ku_band_wavelength"]
    assert row["value"] == 0.0175
    assert row["units"] == "m"
    for name in ("los_phase", "los_from_phase", "max_unambiguous_los_step"):
        default = inspect.signature(getattr(G, name)).parameters["wavelength"].default
        assert default is inspect.Parameter.empty, f"{name}: a documented wavelength is not a default"
        with pytest.raises(TypeError):
            getattr(G, name)(0.001) if name == "los_phase" else getattr(G, name)()
    assert float(G.max_unambiguous_los_step(row["value"])) == pytest.approx(0.004375, rel=1e-14)
