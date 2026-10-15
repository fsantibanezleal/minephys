# ruff: noqa: E501
"""T-002-080 (FR-002-16, FR-002-17, FR-002-18, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, P-000-01..03).

Domain table of spec 002 section 7.2 (`InputError` naming the argument), validity ranges and tripwires of
section 7.3 (`ValidityWarning` naming the argument and the row, result still returned), the option errors of
FR-002-18 and the foundation contract suite (`tests/_contract_suite.py`, T-000-010) on EVERY
`minephys.blasting` function; plus the knowledge pins of the verified rows not covered by the unit tests
(Cunningham's uniformity constants, the Rosin-Rammler median constant, the rock-factor validity limits and the
two flyrock parameter rows).

Conventions (stated so that the implementation can follow them): `ValidityWarning.row` is the row id of
section 7.3 and its message names the argument and the row; a limit fires strictly outside (A < 0.8 or A > 22
for `rock_factor`; exactly 0.8 and 22 are silent); `launch_angle` of `flyrock_range_no_drag` is in [0, pi/2]
and that of `flyrock_trajectory` in [-pi/2, pi/2]; `time_step` is in (0, 0.1]; for the uniformity typical
range the warning carries the row id of `kuzram_uniformity_typical_min` or `_max` (its `argument` is not
tested: the checked quantity is the result); `flyrock_trajectory` takes scalars only (an array is a rank
`InputError`); a shape mismatch ((3,) against (4,)) is an `InputError` naming both arguments and shapes, the
mismatching arrays being filled with the base values of the call.

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
from minephys import blasting as B

INF = math.inf
HALF_PI = math.pi / 2.0

BASE: dict[str, dict[str, Any]] = {
    "charge_per_hole": {"explosive_density": 850.0, "hole_diameter": 0.25, "charge_length": 7.2},
    "powder_factor": {"charge": 300.4, "burden": 6.0, "spacing": 7.0, "bench_height": 12.0},
    "kuznetsov_x50": {
        "rock_factor": 7.0,
        "powder_factor": 0.596,
        "charge": 300.4,
        "rws": 100.0,
        "variant": "cunningham2005",
    },
    "rock_factor": {"rmd": 50.0, "rdi": 17.5, "hf": 10.0},
    "hardness_factor": {"youngs_modulus": 30e9, "ucs": 150e6},
    "rock_density_influence": {"density": 2700.0},
    "uniformity_index": {
        "burden": 6.0,
        "spacing": 7.0,
        "hole_diameter": 0.25,
        "drilling_deviation": 0.3,
        "charge_length": 7.2,
        "bench_height": 12.0,
    },
    "rosin_rammler_passing": {"size": 0.5, "x50": 0.3, "n": 1.1},
    "rosin_rammler_size": {"passing": 0.8, "x50": 0.3, "n": 1.1},
    "swebrec_passing": {"size": 0.5, "x50": 0.3, "xmax": 1.5, "b": 2.5},
    "swebrec_size": {"passing": 0.8, "x50": 0.3, "xmax": 1.5, "b": 2.5},
    "kco_undulation": {"n": 1.1, "x50": 0.3, "xmax": 1.5},
    "kco_distribution": {"size": 0.5, "x50": 0.3, "xmax": 1.5, "n": 1.1},
    "scaled_distance": {"distance": 300.0, "charge_per_delay": 150.0},
    "ppv_scaled_distance": {"distance": 300.0, "charge_per_delay": 150.0, "k_site": 1.0, "beta": 1.6},
    "ppv_limit": {"distance": 304.8},
    "max_charge_per_delay": {"distance": 304.8},
    "flyrock_range_no_drag": {"launch_speed": 40.0, "launch_angle": math.pi / 4.0, "g": 9.80665},
    "flyrock_range_lundborg": {"hole_diameter": 0.127},
    "flyrock_trajectory": {
        "launch_speed": 40.0,
        "launch_angle": math.pi / 4.0,
        "diameter": 0.1,
        "rock_density": 2650.0,
        "drag_coefficient": 0.47,
        "air_density": 1.2,
        "launch_height": 10.0,
        "time_step": 1e-2,
        "max_time": 600.0,
        "g": 9.80665,
    },
}
SCALAR_ONLY = {"flyrock_trajectory"}
ELEMENTWISE = sorted(set(BASE) - SCALAR_ONLY)
SILENT = {"rock_density_influence", "flyrock_range_lundborg"}  # always warn about their UNVERIFIED rows

POS = ([0.0, -1.0, -1e-300, -INF], [])
NONNEG = ([-1e-9, -1.0, -1e300], [0.0])
FINITE: tuple[list[float], list[float]] = ([], [-1.0, 0.0, 1.0])
OPEN01 = ([0.0, 1.0, -0.1, 1.5, 100.0], [0.5])
ANGLE_RANGE = ([-0.01, HALF_PI + 0.01, 2.0, -HALF_PI], [0.0, HALF_PI])  # flyrock_range_no_drag: [0, pi/2]
ANGLE_TRAJ = ([HALF_PI + 0.01, -HALF_PI - 0.01, 2.0, 4.0], [-HALF_PI, 0.0, HALF_PI, -0.5])  # [-pi/2, pi/2]
TIME_STEP = ([0.0, -1e-3, 0.1000001, 0.2, 1.0], [0.1, 0.05])
DOMAIN: dict[str, dict[str, tuple[list[float], list[float]]]] = {
    "charge_per_hole": {"explosive_density": POS, "hole_diameter": POS, "charge_length": POS},
    "powder_factor": {"charge": POS, "burden": POS, "spacing": POS, "bench_height": POS},
    "kuznetsov_x50": {"rock_factor": POS, "powder_factor": POS, "charge": POS, "rws": POS},
    "rock_factor": {"rmd": FINITE, "rdi": FINITE, "hf": FINITE},
    "hardness_factor": {"youngs_modulus": POS, "ucs": POS},
    "rock_density_influence": {"density": POS},
    "uniformity_index": {
        "burden": POS,
        "spacing": POS,
        "hole_diameter": POS,
        "drilling_deviation": NONNEG,
        "charge_length": POS,
        "bench_height": POS,
    },
    "rosin_rammler_passing": {"size": POS, "x50": POS, "n": POS},
    "rosin_rammler_size": {"passing": OPEN01, "x50": POS, "n": POS},
    "swebrec_passing": {"size": POS, "x50": POS, "xmax": POS, "b": POS},
    "swebrec_size": {"passing": OPEN01, "x50": POS, "xmax": POS, "b": POS},
    "kco_undulation": {"n": POS, "x50": POS, "xmax": POS},
    "kco_distribution": {"size": POS, "x50": POS, "xmax": POS, "n": POS},
    "scaled_distance": {"distance": POS, "charge_per_delay": POS},
    "ppv_scaled_distance": {"distance": POS, "charge_per_delay": POS, "k_site": POS, "beta": POS},
    "ppv_limit": {"distance": POS},
    "max_charge_per_delay": {"distance": POS},
    "flyrock_range_no_drag": {"launch_speed": POS, "launch_angle": ANGLE_RANGE, "g": POS},
    "flyrock_range_lundborg": {"hole_diameter": POS},
    "flyrock_trajectory": {
        "launch_speed": POS,
        "launch_angle": ANGLE_TRAJ,
        "diameter": POS,
        "rock_density": POS,
        "drag_coefficient": ([-1e-9, -1.0], [0.0, 1.8]),
        "air_density": ([-1e-9, -1.0], [0.0, 1.2]),
        "launch_height": ([-1e-9, -1.0], [0.0, 25.0]),
        "time_step": TIME_STEP,
        "max_time": ([0.0, -1.0, -INF], []),
        "g": POS,
    },
}
CASES = [(fn, arg, bad) for fn, args in DOMAIN.items() for arg, (invalid, _) in args.items() for bad in invalid]
BOUNDARIES = [(fn, arg, ok) for fn, args in DOMAIN.items() for arg, (_, valid) in args.items() for ok in valid]


def call(fn: str, kwargs: dict[str, Any]) -> Any:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return getattr(B, fn)(**kwargs)


def id_of(case: tuple) -> str:
    return "-".join(str(c) for c in case)


# ------------------------------------------------------------------ FR-002-16: domain


@pytest.mark.req("FR-002-16")
@pytest.mark.oracle(
    "analytical", "spec 002 7.2: a value outside the physical domain is an InputError naming the argument"
)
@pytest.mark.parametrize(("fn", "arg", "bad"), CASES, ids=[id_of(c) for c in CASES])
def test_domain_violation_is_an_input_error(fn: str, arg: str, bad: Any) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-002-16")
@pytest.mark.oracle("analytical", "spec 002 7.2: the closed ends of every interval are accepted")
@pytest.mark.parametrize(("fn", "arg", "ok"), BOUNDARIES, ids=[id_of(c) for c in BOUNDARIES])
def test_domain_boundary_is_accepted(fn: str, arg: str, ok: Any) -> None:
    assert call(fn, {**BASE[fn], arg: ok}) is not None


@pytest.mark.req("FR-002-16")
@pytest.mark.oracle("analytical", "spec 002 7.2: infinity is not a value anywhere in this module")
@pytest.mark.parametrize("fn", sorted(DOMAIN))
def test_infinity_is_rejected_everywhere(fn: str) -> None:
    for arg in DOMAIN[fn]:
        for bad in (INF, -INF, math.nan):
            with pytest.raises(minephys.InputError) as ei:
                call(fn, {**BASE[fn], arg: bad})
            assert ei.value.argument == arg


@pytest.mark.req("FR-002-16")
@pytest.mark.oracle("analytical", "an out-of-domain element of an array raises, naming the argument")
@pytest.mark.parametrize(
    ("fn", "arg", "bad"),
    [
        ("charge_per_hole", "hole_diameter", -0.1),
        ("ppv_limit", "distance", 0.0),
        ("swebrec_size", "passing", 1.0),
        ("hardness_factor", "ucs", -5.0),
    ],
)
def test_bad_element_in_an_array(fn: str, arg: str, bad: float) -> None:
    arr = np.array([BASE[fn][arg], bad, BASE[fn][arg]])
    with pytest.raises(minephys.InputError) as ei:
        call(fn, {**BASE[fn], arg: arr})
    assert ei.value.argument == arg


# ------------------------------------------------------------------ FR-002-17: validity ranges and tripwires


@dataclass(frozen=True)
class Wire:
    row: str
    arg: str
    functions: tuple[str, ...]
    loud: tuple[float, ...]
    quiet: tuple[float, ...]
    extra: dict[str, Any] = field(default_factory=dict)


WIRES = [
    Wire("kuzram_rock_factor_min", "rock_factor", ("kuznetsov_x50",), (0.7999999, 0.1, 0.0001), (0.8, 5.0)),
    Wire("kuzram_rock_factor_max", "rock_factor", ("kuznetsov_x50",), (22.0000001, 50.0, 1000.0), (22.0, 15.0)),
    Wire("tripwire_powder_factor_max", "powder_factor", ("kuznetsov_x50",), (5.0000001, 600.0, 1e6), (5.0, 0.6)),
    Wire("tripwire_rws_min", "rws", ("kuznetsov_x50",), (19.9999, 1.0, 0.85), (20.0, 100.0)),
    Wire(
        "tripwire_hole_diameter_max",
        "hole_diameter",
        ("charge_per_hole", "uniformity_index", "flyrock_range_lundborg"),
        (1.0000001, 250.0, 311.0),
        (1.0, 0.25),
    ),
    Wire("tripwire_k_site_max", "k_site", ("ppv_scaled_distance",), (100.0001, 1700.0, 1e5), (100.0, 1.0)),
    Wire(
        "tripwire_launch_speed_max",
        "launch_speed",
        ("flyrock_range_no_drag", "flyrock_trajectory"),
        (500.0001, 1800.0),
        (500.0, 40.0),
    ),
    Wire("tripwire_air_density_max", "air_density", ("flyrock_trajectory",), (2.0000001, 1200.0), (2.0, 1.2)),
]
WIRE_BY_ROW = {w.row: w for w in WIRES}
LOUD = [(w.row, fn, v) for w in WIRES for fn in w.functions for v in w.loud]
QUIET = [(w.row, fn, v) for w in WIRES for fn in w.functions for v in w.quiet]


def validity(fn: str, kwargs: dict[str, Any]) -> tuple[Any, list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        result = getattr(B, fn)(**kwargs)
    return result, [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]


def wire_kwargs(fn: str, arg: str, value: float) -> dict[str, Any]:
    kwargs = {**BASE[fn], arg: value}
    if fn == "flyrock_trajectory" and arg == "launch_speed" and value > 100.0:
        kwargs["time_step"] = 5e-2  # keep the integration short; the flight of a very fast rock is long
    return kwargs


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle(
    "analytical",
    "spec 002 7.3: each validity limit and unit tripwire warns, naming the argument and the row, and still returns",
)
@pytest.mark.parametrize(("row", "fn", "value"), LOUD, ids=[id_of(c) for c in LOUD])
def test_wire_warns_and_still_returns(row: str, fn: str, value: float) -> None:
    w = WIRE_BY_ROW[row]
    result, found = validity(fn, wire_kwargs(fn, w.arg, value))
    assert result is not None
    hits = [x for x in found if x.message.row == row]
    assert hits, f"no {row} warning in {[str(x.message) for x in found]}"
    msg = hits[0].message
    assert msg.argument == w.arg
    assert row in str(msg)
    assert w.arg in str(msg)


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle("analytical", "spec 002 7.3: values inside the limits, and exactly on them, stay silent")
@pytest.mark.parametrize(("row", "fn", "value"), QUIET, ids=[id_of(c) for c in QUIET])
def test_values_inside_the_wires_are_silent(row: str, fn: str, value: float) -> None:
    w = WIRE_BY_ROW[row]
    _, found = validity(fn, wire_kwargs(fn, w.arg, value))
    assert [x for x in found if x.message.row == row] == []


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle(
    "analytical", "spec 002 7.3: the uniformity index outside 0.8 to 1.5 warns with the kuzram_uniformity_typical rows"
)
def test_uniformity_outside_the_typical_range() -> None:
    base = BASE["uniformity_index"]
    n_ok, quiet = validity("uniformity_index", base)
    assert 0.8 <= float(n_ok) <= 1.5  # 1.1164546
    assert [w for w in quiet if w.message.row.startswith("kuzram_uniformity_typical")] == []
    low, found_low = validity("uniformity_index", {**base, "charge_length": 3.0})  # n ~ 0.46
    assert float(low) < 0.8
    assert any(w.message.row == "kuzram_uniformity_typical_min" for w in found_low)
    high, found_high = validity("uniformity_index", {**base, "charge_length": 12.0})  # n ~ 1.86
    assert float(high) > 1.5
    assert any(w.message.row == "kuzram_uniformity_typical_max" for w in found_high)


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle("analytical", "an array warns if any one element trips the wire")
def test_one_element_of_an_array_is_enough() -> None:
    _, found = validity("charge_per_hole", {**BASE["charge_per_hole"], "hole_diameter": np.array([0.2, 0.3, 250.0])})
    assert any(w.message.row == "tripwire_hole_diameter_max" for w in found)
    _, none = validity("charge_per_hole", {**BASE["charge_per_hole"], "hole_diameter": np.array([0.2, 0.3, 0.4])})
    assert none == []


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle("analytical", "the baseline calls of section 7.4 trip no wire at all")
@pytest.mark.parametrize("fn", sorted(BASE))
def test_the_worked_examples_are_silent(fn: str) -> None:
    _, found = validity(fn, dict(BASE[fn]))
    assert found == []


@pytest.mark.req("FR-002-17")
@pytest.mark.oracle(
    "analytical", "FR-008-12 + spec 002 7.6: only the three documented functions warn about UNVERIFIED rows"
)
def test_unverified_row_warnings_come_only_from_the_documented_functions() -> None:
    for fn in sorted(BASE):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            getattr(B, fn)(**BASE[fn])
        got = [w for w in rec if issubclass(w.category, UnverifiedParameterWarning)]
        if fn in SILENT:
            assert got, f"{fn} reads UNVERIFIED model constants and must warn"
        else:
            assert got == [], f"{fn} must not warn about UNVERIFIED rows (variant cunningham2005 is verified)"
    with pytest.warns(UnverifiedParameterWarning):
        B.kuznetsov_x50(7.0, 0.596, 300.4, 100.0)  # the default variant uses the UNVERIFIED 19/30


# ------------------------------------------------------------------ FR-002-18: options


@pytest.mark.req("FR-002-18")
@pytest.mark.oracle("analytical", "options are exact strings; the error lists the allowed values")
def test_option_errors() -> None:
    with pytest.raises(minephys.InputError) as ei:
        call("kuznetsov_x50", {**BASE["kuznetsov_x50"], "variant": "kuz-ram"})
    assert ei.value.argument == "variant"
    assert "cunningham1983" in str(ei.value)
    assert "cunningham2005" in str(ei.value)
    for fn in ("ppv_limit", "max_charge_per_delay"):
        with pytest.raises(minephys.InputError) as ei2:
            call(fn, {**BASE[fn], "standard": "usbm"})
        assert ei2.value.argument == "standard"
        assert "30cfr816.67" in str(ei2.value)


# ------------------------------------------------------------------ foundation contract suite


def f32(lo: float, hi: float) -> st.SearchStrategy[float]:
    # bounds rounded to the nearest float32; "+ 0.0" turns -0.0 into 0.0 (its integer variant would differ in the sign bit)
    return st.floats(float(np.float32(lo)), float(np.float32(hi)), width=32).map(lambda x: x + 0.0)


@dataclass(frozen=True)
class Op:
    strategies: dict[str, st.SearchStrategy[Any]]
    fixed: dict[str, Any] = field(default_factory=dict)


SIZE = f32(0.001, 10.0)
X50 = f32(0.01, 0.2)
XMAX = f32(0.5, 5.0)
OPS: dict[str, Op] = {
    "charge_per_hole": Op(
        {"explosive_density": f32(700.0, 1400.0), "hole_diameter": f32(0.05, 0.4), "charge_length": f32(0.5, 20.0)}
    ),
    "powder_factor": Op(
        {
            "charge": f32(1.0, 1000.0),
            "burden": f32(1.0, 12.0),
            "spacing": f32(1.0, 15.0),
            "bench_height": f32(2.0, 30.0),
        }
    ),
    "kuznetsov_x50": Op(
        {
            "rock_factor": f32(0.8, 22.0),
            "powder_factor": f32(0.1, 3.0),
            "charge": f32(1.0, 3000.0),
            "rws": f32(50.0, 200.0),
        },
        {"variant": "cunningham2005"},
    ),
    "rock_factor": Op({"rmd": f32(0.0, 100.0), "rdi": f32(-30.0, 30.0), "hf": f32(0.0, 60.0)}),
    "hardness_factor": Op({"youngs_modulus": f32(1e9, 1e11), "ucs": f32(1e7, 4e8)}),
    "rock_density_influence": Op({"density": f32(1500.0, 4000.0)}),
    "uniformity_index": Op(
        {
            "burden": f32(2.0, 10.0),
            "spacing": f32(2.0, 12.0),
            "hole_diameter": f32(0.1, 0.3),
            "drilling_deviation": f32(0.0, 1.0),
            "charge_length": f32(3.0, 10.0),
            "bench_height": f32(8.0, 20.0),
        }
    ),
    "rosin_rammler_passing": Op({"size": SIZE, "x50": f32(0.01, 1.0), "n": f32(0.5, 4.0)}),
    "rosin_rammler_size": Op({"passing": f32(0.01, 0.99), "x50": f32(0.01, 1.0), "n": f32(0.5, 4.0)}),
    "swebrec_passing": Op({"size": SIZE, "x50": X50, "xmax": XMAX, "b": f32(0.5, 4.0)}),
    "swebrec_size": Op({"passing": f32(0.01, 0.99), "x50": X50, "xmax": XMAX, "b": f32(0.5, 4.0)}),
    "kco_undulation": Op({"n": f32(0.5, 3.0), "x50": X50, "xmax": XMAX}),
    "kco_distribution": Op({"size": SIZE, "x50": X50, "xmax": XMAX, "n": f32(0.5, 3.0)}),
    "scaled_distance": Op({"distance": f32(10.0, 1e4), "charge_per_delay": f32(1.0, 5e3)}),
    "ppv_scaled_distance": Op(
        {
            "distance": f32(10.0, 1e4),
            "charge_per_delay": f32(1.0, 5e3),
            "k_site": f32(0.01, 50.0),
            "beta": f32(1.0, 2.5),
        }
    ),
    "ppv_limit": Op({"distance": f32(1.0, 1e4)}, {"standard": "30cfr816.67"}),
    "max_charge_per_delay": Op({"distance": f32(1.0, 1e4)}, {"standard": "30cfr816.67"}),
    "flyrock_range_no_drag": Op({"launch_speed": f32(1.0, 300.0), "launch_angle": f32(0.0, 1.5), "g": f32(1.0, 25.0)}),
    "flyrock_range_lundborg": Op({"hole_diameter": f32(0.02, 0.5)}),
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


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-01")
@pytest.mark.req("P-000-02")
@pytest.mark.req("P-000-03")
@pytest.mark.req("FR-000-07")
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
    ("name", "arg"), [(n, a) for n in ELEMENTWISE for a in OPS[n].strategies], ids=lambda v: str(v)
)
def test_hostile_battery(name: str, arg: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(getattr(B, name), dict(BASE[name]), arg)


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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(minephys.InputError) as ei:
            getattr(B, name)(**kwargs)
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


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle("analytical", "flyrock_trajectory is pure: bitwise-identical results on two calls")
def test_trajectory_purity() -> None:
    def flat(**kw: Any) -> np.ndarray:
        r = B.flyrock_trajectory(**kw)
        return np.concatenate([r.t, r.x, r.z, r.vx, r.vz, [r.range, r.flight_time, r.apex_height]])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_purity(flat, dict(BASE["flyrock_trajectory"]))


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.req("FR-000-12")
@pytest.mark.oracle(
    "analytical", "scalar-only flyrock_trajectory: hostile scalars name the argument; arrays are rank errors"
)
def test_trajectory_hostile_battery_and_rank() -> None:
    kwargs = dict(BASE["flyrock_trajectory"])
    for arg, value in kwargs.items():
        for bad in (math.nan, INF, -INF):
            with pytest.raises(minephys.InputError) as ei:
                B.flyrock_trajectory(**{**kwargs, arg: bad})
            assert ei.value.argument == arg
        for bad in ("1", b"1", None, 1 + 1j, True, object()):
            with pytest.raises(minephys.InputTypeError) as ei2:
                B.flyrock_trajectory(**{**kwargs, arg: bad})
            assert ei2.value.argument == arg
        with pytest.raises(minephys.InputError) as ei3:
            B.flyrock_trajectory(**{**kwargs, arg: np.array([value, value])})
        assert ei3.value.argument == arg


# ------------------------------------------------------------------ knowledge pins of the remaining verified rows


def uniformity_from_rows(c0: float, c1: float, c2: float, c3: float) -> float:
    b, s, d_mm, w, length, h = 6.0, 7.0, 250.0, 0.3, 7.2, 12.0
    return (c0 - c1 * b / d_mm) * math.sqrt((1 + s / b) / 2) * (1 - w / b) * (1.0 + c2) ** c3 * length / h


@pytest.mark.req("FR-002-04")
@pytest.mark.knowledge("cunningham_n_constant")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 202: n = (2.2 - 14 B/d) ..., the constant 2.2 of eq. 3")
def test_row_cunningham_n_constant() -> None:
    row = rows_by_id("blasting")["cunningham_n_constant"]
    assert row["value"] == 2.2
    assert float(call("uniformity_index", dict(BASE["uniformity_index"]))) == pytest.approx(
        uniformity_from_rows(row["value"], 14.0, 0.1, 0.1), rel=1e-12
    )


@pytest.mark.req("FR-002-04")
@pytest.mark.knowledge("cunningham_n_burden_coefficient")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 202: the coefficient 14 of B/d (d in mm)")
def test_row_cunningham_n_burden_coefficient() -> None:
    row = rows_by_id("blasting")["cunningham_n_burden_coefficient"]
    assert row["value"] == 14
    assert float(call("uniformity_index", dict(BASE["uniformity_index"]))) == pytest.approx(
        uniformity_from_rows(2.2, row["value"], 0.1, 0.1), rel=1e-12
    )


@pytest.mark.req("FR-002-04")
@pytest.mark.knowledge("cunningham_n_charge_offset")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 202: the offset 0.1 added to |BCL - CCL| / L")
def test_row_cunningham_n_charge_offset() -> None:
    row = rows_by_id("blasting")["cunningham_n_charge_offset"]
    assert row["value"] == 0.1
    assert float(call("uniformity_index", dict(BASE["uniformity_index"]))) == pytest.approx(
        uniformity_from_rows(2.2, 14.0, row["value"], 0.1), rel=1e-12
    )


@pytest.mark.req("FR-002-04")
@pytest.mark.knowledge("cunningham_n_charge_exponent")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 202: the exponent 0.1 of the charge-length term")
def test_row_cunningham_n_charge_exponent() -> None:
    row = rows_by_id("blasting")["cunningham_n_charge_exponent"]
    assert row["value"] == 0.1
    assert float(call("uniformity_index", dict(BASE["uniformity_index"]))) == pytest.approx(
        uniformity_from_rows(2.2, 14.0, 0.1, row["value"]), rel=1e-12
    )


@pytest.mark.req("FR-002-05")
@pytest.mark.knowledge("rosin_rammler_median_constant")
@pytest.mark.oracle(
    "worked-example", "cunningham2005 p. 202: 0.693 printed, implemented as ln 2 so that x50 is exactly the median"
)
def test_row_rosin_rammler_median_constant() -> None:
    row = rows_by_id("blasting")["rosin_rammler_median_constant"]
    assert row["value"] == 0.693
    assert abs(row["value"] - math.log(2.0)) / math.log(2.0) == pytest.approx(2.1e-4, abs=1e-5)
    p = float(call("rosin_rammler_passing", {"size": 0.3, "x50": 0.3, "n": 1.1}))
    assert abs(p - 0.5) < 1e-15, "the median is exact only with ln 2; 0.693 would give 0.49997"


@pytest.mark.req("FR-002-17")
@pytest.mark.knowledge("kuzram_rock_factor_min")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 201: the rock factor varies between 0.8 and 22 (lower end)")
def test_row_rock_factor_min() -> None:
    row = rows_by_id("blasting")["kuzram_rock_factor_min"]
    assert row["value"] == 0.8
    _, below = validity("kuznetsov_x50", {**BASE["kuznetsov_x50"], "rock_factor": row["value"] * (1 - 1e-6)})
    assert any(w.message.row == "kuzram_rock_factor_min" for w in below)


@pytest.mark.req("FR-002-17")
@pytest.mark.knowledge("kuzram_rock_factor_max")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 201: the rock factor varies between 0.8 and 22 (upper end)")
def test_row_rock_factor_max() -> None:
    row = rows_by_id("blasting")["kuzram_rock_factor_max"]
    assert row["value"] == 22
    _, above = validity("kuznetsov_x50", {**BASE["kuznetsov_x50"], "rock_factor": row["value"] * (1 + 1e-6)})
    assert any(w.message.row == "kuzram_rock_factor_max" for w in above)


@pytest.mark.req("FR-002-12")
@pytest.mark.knowledge("flyrock_drag_coefficient_range")
@pytest.mark.oracle(
    "worked-example", "szendrei2022 p. 728: drag coefficients of 0.6 to 1.8, documented but never a default"
)
def test_row_flyrock_drag_coefficient_range() -> None:
    row = rows_by_id("blasting")["flyrock_drag_coefficient_range"]
    assert row["range"] == {"min": 0.6, "max": 1.8}
    params = inspect.signature(B.flyrock_trajectory).parameters
    assert params["drag_coefficient"].default is inspect.Parameter.empty, "a documented range is not a default"
    with pytest.raises(TypeError):
        B.flyrock_trajectory(40.0, 0.7, 0.1, 2650.0)  # type: ignore[call-arg]


@pytest.mark.req("FR-002-12")
@pytest.mark.knowledge("flyrock_air_density_reference")
@pytest.mark.oracle(
    "worked-example", "szendrei2022 p. 728: reference air density 1.24 kg/m^3, documented but never a default"
)
def test_row_flyrock_air_density_reference() -> None:
    row = rows_by_id("blasting")["flyrock_air_density_reference"]
    assert row["value"] == 1.24
    assert inspect.signature(B.flyrock_trajectory).parameters["air_density"].default is inspect.Parameter.empty
