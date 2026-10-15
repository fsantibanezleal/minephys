# ruff: noqa: E501
"""T-004-080 (FR-004-10, FR-004-11, FR-004-12, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, P-000-01..03).

Domain table of spec 004 section 7.2 (`InputError` naming the argument), unit tripwires of section 7.3
(`ValidityWarning` naming the argument and the row, result still returned), the blending and sampling errors
of FR-004-12 and the foundation contract suite (`tests/_contract_suite.py`, T-000-010) on EVERY
`minephys.bulk` function (all ten are elementwise); the UnverifiedParameterWarning matrix of section 7.6 (only
`beverloo_discharge` and `cema_effective_tension` warn); plus the knowledge pin of the verified row
`beverloo_discharge_coefficient_dem` (documented, never a default).

Conventions (stated so that the implementation can follow them): `ValidityWarning.row` is the row id of
section 7.3 and its message names the argument and the row; a tripwire fires strictly outside its limit
(exactly 10 m, 1 m, 100 kg/m^3, 1.05 rad, 15 m/s, 100 kg/m^3 and 0.5 m are silent); `n_layers` accepts
integer-valued floats and NumPy integers but not 2.5; `end_cones` is a boolean flag (InputTypeError
otherwise); the domain error of `orifice_diameter <= annulus_coefficient * particle_diameter` and of
`sample_mass > lot_mass` is tested in the unit files of T-004-010 and T-004-030.

Oracle: analytical (the tables are the specification) and the foundation contract suite.
"""

from __future__ import annotations

import inspect
import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import _contract_suite as cs
import numpy as np
import pytest
from _table_helpers_a import rows_by_id
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp
from minephys.knowledge import UnverifiedParameterWarning

import minephys
from minephys import bulk as B

INF = math.inf
HALF_PI = math.pi / 2.0
PHI37 = math.radians(37.0)

BASE: dict[str, dict[str, Any]] = {
    "beverloo_discharge": {
        "orifice_diameter": 0.3,
        "particle_diameter": 0.02,
        "bulk_density": 1600.0,
        "discharge_coefficient": 0.56,
        "annulus_coefficient": 1.5,
        "g": 9.80665,
    },
    "repose_cone_height": {"base_radius": 30.0, "repose_angle": PHI37},
    "repose_cone_volume": {"base_radius": 30.0, "repose_angle": PHI37},
    "repose_ridge_volume": {"base_half_width": 30.0, "repose_angle": PHI37, "length": 100.0, "end_cones": False},
    "conveyor_capacity": {"load_area": 0.25, "belt_speed": 4.0, "bulk_density": 1600.0},
    "cema_effective_tension": {
        "length": 1000.0,
        "lift": 30.0,
        "belt_weight": 300.0,
        "material_weight": 1362.0347,
        "kt": 1.0,
        "kx": 10.0,
        "ky": 0.03,
        "pulley_tension": 0.0,
        "acceleration_tension": 0.0,
        "accessory_tension": 0.0,
    },
    "conveyor_power": {"effective_tension": 105_222.08, "belt_speed": 4.0, "drive_efficiency": 0.9},
    "gy_fundamental_sampling_error": {
        "sample_mass": 1.0,
        "lot_mass": 1000.0,
        "top_size": 0.01,
        "mineralogical_factor": 1.0e4,
        "shape_factor": 0.5,
        "granulometric_factor": 0.25,
        "liberation_factor": 0.1,
    },
    "gy_blending_variance": {"input_variance": 1.0, "n_layers": 100, "lag1_correlation": 0.9},
    "variance_reduction_ratio": {"n_layers": 100, "lag1_correlation": 0.9},
}
ELEMENTWISE = sorted(BASE)
UNVERIFIED_WARNERS = {"beverloo_discharge", "cema_effective_tension"}  # spec 7.6

POS = ([0.0, -1.0, -1e-300, -INF], [])  # > 0
NONNEG = ([-1e-9, -1.0, -1e300], [0.0])  # >= 0
FINITE: tuple[list[float], list[float]] = ([], [-1e6, -1.0, 0.0, 1.0, 1e6])  # finite, negative allowed
ANGLE = ([0.0, -0.1, HALF_PI, 2.0, 90.0, -HALF_PI], [1e-9, 0.5, 1.5])  # (0, pi/2)
EFF = ([0.0, -0.1, 1.0000001, 1.5, 100.0], [1.0, 0.5, 1e-9])  # (0, 1]
LAYERS = ([0, -1, -100, 10**7 + 1, 10**9, 2.5, 0.5], [1, 2, 10**7])  # integer 1..1e7
RHO = ([-1.0, 1.0, 1.5, -1.0000001, 100.0, math.nextafter(1.0, 2.0)], [0.0, 0.5, -0.999999999, 0.999999999])  # (-1, 1)
DOMAIN: dict[str, dict[str, tuple[list[float], list[float]]]] = {
    "beverloo_discharge": {
        "orifice_diameter": POS,
        "particle_diameter": POS,
        "bulk_density": POS,
        "discharge_coefficient": POS,
        "annulus_coefficient": NONNEG,
        "g": POS,
    },
    "repose_cone_height": {"base_radius": POS, "repose_angle": ANGLE},
    "repose_cone_volume": {"base_radius": POS, "repose_angle": ANGLE},
    "repose_ridge_volume": {"base_half_width": POS, "repose_angle": ANGLE, "length": NONNEG},
    "conveyor_capacity": {"load_area": POS, "belt_speed": POS, "bulk_density": POS},
    "cema_effective_tension": {
        "length": NONNEG,
        "lift": FINITE,
        "belt_weight": NONNEG,
        "material_weight": NONNEG,
        "kt": NONNEG,
        "kx": NONNEG,
        "ky": NONNEG,
        "pulley_tension": NONNEG,
        "acceleration_tension": NONNEG,
        "accessory_tension": NONNEG,
    },
    "conveyor_power": {"effective_tension": FINITE, "belt_speed": POS, "drive_efficiency": EFF},
    "gy_fundamental_sampling_error": {
        "sample_mass": POS,
        "lot_mass": POS,
        "top_size": POS,
        "mineralogical_factor": POS,
        "shape_factor": EFF,
        "granulometric_factor": EFF,
        "liberation_factor": EFF,
    },
    "gy_blending_variance": {"input_variance": NONNEG, "n_layers": LAYERS, "lag1_correlation": RHO},
    "variance_reduction_ratio": {"n_layers": LAYERS, "lag1_correlation": RHO},
}
CASES = [(fn, arg, bad) for fn, args in DOMAIN.items() for arg, (invalid, _) in args.items() for bad in invalid]
BOUNDARIES = [(fn, arg, ok) for fn, args in DOMAIN.items() for arg, (_, valid) in args.items() for ok in valid]


def call(fn: str, kwargs: dict[str, Any]) -> Any:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return getattr(B, fn)(**kwargs)


def id_of(case: tuple) -> str:
    return "-".join(str(c) for c in case)


# ------------------------------------------------------------------ FR-004-10 and FR-004-12: domain


@pytest.mark.req("FR-004-10")
@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "analytical", "spec 004 7.2: a value outside the physical domain is an InputError naming the argument"
)
@pytest.mark.parametrize(("fn", "arg", "bad"), CASES, ids=[id_of(c) for c in CASES])
def test_domain_violation_is_an_input_error(fn: str, arg: str, bad: Any) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-004-10")
@pytest.mark.oracle(
    "analytical", "spec 004 7.2: the closed ends of every interval, and negative lift and tension, are accepted"
)
@pytest.mark.parametrize(("fn", "arg", "ok"), BOUNDARIES, ids=[id_of(c) for c in BOUNDARIES])
def test_domain_boundary_is_accepted(fn: str, arg: str, ok: Any) -> None:
    assert call(fn, {**BASE[fn], arg: ok}) is not None


@pytest.mark.req("FR-004-10")
@pytest.mark.oracle("analytical", "spec 004 7.2: NaN and infinity are not a value anywhere in this module")
@pytest.mark.parametrize("fn", sorted(DOMAIN))
def test_non_finite_is_rejected_everywhere(fn: str) -> None:
    for arg in DOMAIN[fn]:
        for bad in (INF, -INF, math.nan):
            with pytest.raises(minephys.InputError) as ei:
                call(fn, {**BASE[fn], arg: bad})
            assert ei.value.argument == arg


@pytest.mark.req("FR-004-10")
@pytest.mark.oracle("analytical", "an out-of-domain element of an array raises, naming the argument")
@pytest.mark.parametrize(
    ("fn", "arg", "bad"),
    [
        ("beverloo_discharge", "bulk_density", -5.0),
        ("repose_cone_volume", "repose_angle", HALF_PI),
        ("conveyor_power", "drive_efficiency", 1.1),
        ("gy_blending_variance", "lag1_correlation", 1.0),
        ("variance_reduction_ratio", "n_layers", 0),
        ("conveyor_capacity", "load_area", 0.0),
    ],
)
def test_bad_element_in_an_array(fn: str, arg: str, bad: float) -> None:
    base = BASE[fn][arg]
    arr = np.array([base, bad, base], dtype=float)
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: arr})
    assert ei.value.argument == arg


@pytest.mark.req("FR-004-10")
@pytest.mark.oracle("analytical", "g defaults to g0 but is validated when given (> 0)")
def test_g_is_optional_and_validated() -> None:
    assert inspect.signature(B.beverloo_discharge).parameters["g"].default == 9.80665
    assert call("beverloo_discharge", {**BASE["beverloo_discharge"], "g": 9.81}) is not None


# ------------------------------------------------------------------ FR-004-11: tripwires


@dataclass(frozen=True)
class Wire:
    row: str
    args: dict[str, str]  # function -> the argument it watches
    loud: tuple[float, ...]
    quiet: tuple[float, ...]
    extra: dict[str, dict[str, Any]] = field(default_factory=dict)  # function -> kwargs keeping the call valid


WIRES = [
    Wire(
        "tripwire_orifice_diameter_max",
        {"beverloo_discharge": "orifice_diameter"},
        (10.0000001, 50.0, 1e3),
        (10.0, 5.0, 0.3),
    ),
    Wire(
        "tripwire_particle_diameter_max",
        {"beverloo_discharge": "particle_diameter"},
        (1.0000001, 2.0, 5.0),
        (1.0, 0.5, 0.02),
        {"beverloo_discharge": {"orifice_diameter": 9.9}},
    ),
    Wire(
        "tripwire_bulk_density_min",
        {"beverloo_discharge": "bulk_density", "conveyor_capacity": "bulk_density"},
        (99.99, 1.6, 1e-3),
        (100.0, 1600.0),
    ),
    Wire(
        "tripwire_repose_angle_max",
        {
            "repose_cone_height": "repose_angle",
            "repose_cone_volume": "repose_angle",
            "repose_ridge_volume": "repose_angle",
        },
        (1.0500001, 1.2, 1.5),
        (1.05, 0.6, 0.01),
    ),
    Wire(
        "tripwire_belt_speed_max",
        {"conveyor_capacity": "belt_speed", "conveyor_power": "belt_speed"},
        (15.0000001, 20.0, 1e3),
        (15.0, 4.0, 0.5),
    ),
    Wire(
        "tripwire_mineralogical_factor_min",
        {"gy_fundamental_sampling_error": "mineralogical_factor"},
        (99.99, 10.0, 1e-3),
        (100.0, 1e4),
    ),
    Wire("tripwire_top_size_max", {"gy_fundamental_sampling_error": "top_size"}, (0.5000001, 1.0, 10.0), (0.5, 0.01)),
]
WIRE_BY_ROW = {w.row: w for w in WIRES}
LOUD = [(w.row, fn, v) for w in WIRES for fn in w.args for v in w.loud]
QUIET = [(w.row, fn, v) for w in WIRES for fn in w.args for v in w.quiet]


def wire_kwargs(row: str, fn: str, value: float) -> dict[str, Any]:
    w = WIRE_BY_ROW[row]
    return {**BASE[fn], **w.extra.get(fn, {}), w.args[fn]: value}


def validity(fn: str, kwargs: dict[str, Any]) -> tuple[Any, list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        result = getattr(B, fn)(**kwargs)
    return result, [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle(
    "analytical",
    "spec 004 7.3: each unit tripwire warns, naming the argument and the row, and still returns the result",
)
@pytest.mark.parametrize(("row", "fn", "value"), LOUD, ids=[id_of(c) for c in LOUD])
def test_wire_warns_and_still_returns(row: str, fn: str, value: float) -> None:
    arg = WIRE_BY_ROW[row].args[fn]
    result, found = validity(fn, wire_kwargs(row, fn, value))
    assert result is not None
    hits = [x for x in found if x.message.row == row]
    assert hits, f"no {row} warning in {[str(x.message) for x in found]}"
    msg = hits[0].message
    assert msg.argument == arg
    assert row in str(msg)
    assert arg in str(msg)


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle("analytical", "spec 004 7.3: values inside the limits, and exactly on them, stay silent")
@pytest.mark.parametrize(("row", "fn", "value"), QUIET, ids=[id_of(c) for c in QUIET])
def test_values_inside_the_wires_are_silent(row: str, fn: str, value: float) -> None:
    _, found = validity(fn, wire_kwargs(row, fn, value))
    assert [x for x in found if x.message.row == row] == []


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle(
    "analytical", "an array warns if any one element trips the wire; an array within the limits is silent"
)
def test_one_element_of_an_array_is_enough() -> None:
    _, found = validity("repose_cone_volume", {**BASE["repose_cone_volume"], "repose_angle": np.array([0.5, 0.9, 1.4])})
    assert any(w.message.row == "tripwire_repose_angle_max" for w in found)
    _, none = validity("repose_cone_volume", {**BASE["repose_cone_volume"], "repose_angle": np.array([0.5, 0.9, 1.0])})
    assert none == []


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle("analytical", "the baseline calls of spec 004 7.4 trip no wire at all")
@pytest.mark.parametrize("fn", sorted(BASE))
def test_the_worked_examples_are_silent(fn: str) -> None:
    _, found = validity(fn, dict(BASE[fn]))
    assert found == []


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle(
    "analytical",
    "the two bulk-density wires watch different functions but name the same row; a speed wire does not fire on a density",
)
def test_wires_do_not_cross() -> None:
    _, found = validity("conveyor_capacity", {**BASE["conveyor_capacity"], "bulk_density": 50.0})
    assert {w.message.row for w in found} == {"tripwire_bulk_density_min"}
    _, found2 = validity("conveyor_capacity", {**BASE["conveyor_capacity"], "belt_speed": 30.0})
    assert {w.message.row for w in found2} == {"tripwire_belt_speed_max"}


# ------------------------------------------------------------------ spec 004 section 7.6: UNVERIFIED rows


@pytest.mark.req("FR-004-11")
@pytest.mark.oracle(
    "analytical",
    "spec 004 7.6: only beverloo_discharge (beverloo_exponent) and cema_effective_tension (cema_return_belt_coefficient) warn about UNVERIFIED rows",
)
@pytest.mark.parametrize("fn", sorted(BASE))
def test_unverified_row_warnings(fn: str) -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        getattr(B, fn)(**BASE[fn])
    got = [w for w in rec if issubclass(w.category, UnverifiedParameterWarning)]
    if fn in UNVERIFIED_WARNERS:
        assert got, f"{fn} reads an UNVERIFIED model constant and must warn"
    else:
        assert got == [], f"{fn} reads no UNVERIFIED model constant and must not warn"


# ------------------------------------------------------------------ foundation contract suite: elementwise functions


def f32(lo: float, hi: float) -> st.SearchStrategy[float]:
    # bounds rounded to the nearest float32; "+ 0.0" turns -0.0 into 0.0 (its integer variant would differ in the sign bit)
    return st.floats(float(np.float32(lo)), float(np.float32(hi)), width=32).map(lambda x: x + 0.0)


def counts(lo: int, hi: int) -> st.SearchStrategy[float]:
    return st.integers(lo, hi).map(float)


@dataclass(frozen=True)
class Op:
    strategies: dict[str, st.SearchStrategy[Any]]
    fixed: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()


ANGLE_S = f32(0.05, 1.5)
RADIUS_S = f32(0.1, 500.0)
OPS: dict[str, Op] = {
    "beverloo_discharge": Op(
        {
            "orifice_diameter": f32(0.05, 2.0),
            "particle_diameter": f32(1e-4, 0.01),
            "bulk_density": f32(300.0, 4000.0),
            "discharge_coefficient": f32(0.4, 0.8),
            "annulus_coefficient": f32(0.0, 3.0),
            "g": f32(1.0, 25.0),
        }
    ),
    "repose_cone_height": Op({"base_radius": RADIUS_S, "repose_angle": ANGLE_S}),
    "repose_cone_volume": Op({"base_radius": RADIUS_S, "repose_angle": ANGLE_S}),
    "repose_ridge_volume": Op(
        {"base_half_width": RADIUS_S, "repose_angle": ANGLE_S, "length": f32(0.0, 1e4)},
        {"end_cones": True},
        ("end_cones",),
    ),
    "conveyor_capacity": Op(
        {"load_area": f32(0.01, 2.0), "belt_speed": f32(0.1, 12.0), "bulk_density": f32(300.0, 4000.0)}
    ),
    "cema_effective_tension": Op(
        {
            "length": f32(1.0, 2e4),
            "lift": f32(-500.0, 500.0),
            "belt_weight": f32(0.0, 300.0),
            "material_weight": f32(0.0, 5e3),
            "kt": f32(0.5, 2.0),
            "kx": f32(0.0, 50.0),
            "ky": f32(0.01, 0.05),
            "pulley_tension": f32(0.0, 1e4),
            "acceleration_tension": f32(0.0, 1e4),
            "accessory_tension": f32(0.0, 1e4),
        }
    ),
    "conveyor_power": Op(
        {"effective_tension": f32(-1e6, 1e6), "belt_speed": f32(0.1, 12.0), "drive_efficiency": f32(0.1, 1.0)}
    ),
    "gy_fundamental_sampling_error": Op(
        {
            "sample_mass": f32(1e-3, 1e3),
            "lot_mass": f32(1e3, 1e6),
            "top_size": f32(1e-5, 0.3),
            "mineralogical_factor": f32(100.0, 1e5),
            "shape_factor": f32(0.1, 1.0),
            "granulometric_factor": f32(0.05, 1.0),
            "liberation_factor": f32(0.01, 1.0),
        }
    ),
    "gy_blending_variance": Op(
        {"input_variance": f32(0.0, 1e6), "n_layers": counts(1, 10_000), "lag1_correlation": f32(-0.99, 0.99)}
    ),
    "variance_reduction_ratio": Op({"n_layers": counts(1, 10_000), "lag1_correlation": f32(-0.99, 0.99)}),
}


@st.composite
def operands(draw: Callable, op: Op) -> dict[str, Any]:
    """Broadcast-compatible operands: each argument is a scalar, a full array or a trailing-axis row."""
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
    if "lot_mass" in kwargs and "sample_mass" in kwargs:  # keep M_S <= M_L whatever the broadcast pairing
        kwargs["sample_mass"] = np.minimum(kwargs["sample_mass"], 1e3)
        kwargs["lot_mass"] = np.maximum(kwargs["lot_mass"], 1e3)
    return kwargs


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
    fn = getattr(B, name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_purity(fn, kwargs)
        cs.check_dtype_invariance(fn, kwargs)
        cs.check_elementwise(fn, kwargs)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "foundation hostile battery: NaN, inf, wrong types name the argument")
@pytest.mark.parametrize(
    ("name", "arg"),
    [(n, a) for n in ELEMENTWISE for a in OPS[n].strategies],
    ids=lambda v: str(v),
)
def test_hostile_battery(name: str, arg: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(getattr(B, name), dict(BASE[name]), arg)


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "the declared boolean flag must be boolean (foundation battery for flags)")
def test_boolean_flag() -> None:
    kwargs = {**BASE["repose_ridge_volume"], "end_cones": True}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(B.repose_ridge_volume, kwargs, "end_cones", boolean=True)


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


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("analytical", "an elementwise function given empty arrays returns an empty float64 array")
@pytest.mark.parametrize("name", ELEMENTWISE)
def test_empty_arrays(name: str) -> None:
    arg = next(iter(OPS[name].strategies))
    out = call(name, {**BASE[name], arg: np.empty(0)})
    assert out.shape == (0,)
    assert out.dtype == np.float64


# ------------------------------------------------------------------ knowledge pin of the verified row


@pytest.mark.req("FR-004-01")
@pytest.mark.knowledge("beverloo_discharge_coefficient_dem")
@pytest.mark.oracle(
    "worked-example",
    "dasilva2025 p. 9: C = 0.56 fitted with the particle density 3,000 kg/m3, documented but never a default and not interchangeable with the bulk-density C",
)
def test_row_beverloo_discharge_coefficient_dem() -> None:
    row = rows_by_id("bulk")["beverloo_discharge_coefficient_dem"]
    assert row["value"] == 0.56
    params = inspect.signature(B.beverloo_discharge).parameters
    assert params["discharge_coefficient"].default is inspect.Parameter.empty
    assert params["annulus_coefficient"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        B.beverloo_discharge(0.3, 0.02, 1600.0)  # type: ignore[call-arg]
    for name in ("kt", "kx", "ky"):
        assert inspect.signature(B.cema_effective_tension).parameters[name].default is inspect.Parameter.empty
