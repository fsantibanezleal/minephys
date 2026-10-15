"""T-001-080 (FR-001-22, FR-001-23, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, P-000-01..03).

Domain table of spec 001 section 7.2 (violations raise `InputError` naming the argument), tripwire table of
section 7.3 (`ValidityWarning` naming the argument and the row id, the result is still returned), and the
foundation contract suite (`tests/_contract_suite.py`, T-000-010: purity, elementwise = scalar evaluation,
float32 and integer operands, hostile inputs, shape mismatch) on EVERY `minephys.haulage` function.

Conventions used here (stated so that the implementation can follow them):
* `ValidityWarning.row` equals the tripwire row id of section 7.3 (for example `tripwire_grade_abs_max`);
* a tripwire fires strictly outside its limit (`|grade| > 0.30`; exactly 0.30 is silent), for scalars and for
any element
  of an array;
* integral floats such as 6.0 are accepted as counts, non-integral ones (2.5) are `InputError`; booleans and
strings are
  `InputTypeError`;
* `speed` of `required_force` is >= 0 (its default is 0); `speed` of `segment_travel_time` is > 0;
* the function `loading_passes` returns int64, so the float64 clause of FR-000-07 is not applied to it (its own
  elementwise check is written here); named results of the queue functions are flattened to float arrays for the
  purity checks;
* a shape mismatch ((3,) against (4,)) is an `InputError` whose message names both arguments and both shapes; the
  mismatching arrays are filled with the base values of the call, which are inside every domain;
* optional arguments whose `None` is legal (`effective_mass`, `air_density`, `emission_factor`) get a hostile battery
  without `None`.

Oracle: analytical (the domain and tripwire tables are the specification) and the foundation contract suite.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import _contract_suite as cs
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

import minephys
from minephys import haulage as H

INF = math.inf
CFG = settings(deadline=None)

# ------------------------------------------------------------------ valid base calls (spec 001 section 7.4)

MASS_A = np.array([400000.0, 180000.0, 400000.0])
LEN_A = np.array([3000.0, 3000.0, 1000.0])
RR_A = np.array([0.02, 0.02, 0.03])
GR_A = np.array([0.10, -0.10, 0.0])

BASE: dict[str, dict[str, Any]] = {
    "grade_resistance": {"grade": 0.1},
    "total_resistance": {"rolling_resistance": 0.02, "grade": 0.1},
    "required_force": {
        "mass": 4e5,
        "total_resistance": 0.12,
        "acceleration": 0.1,
        "effective_mass": 4.2e5,
        "drag_area": 45.0,
        "air_density": 1.2,
        "speed": 5.0,
        "g": 9.80665,
    },
    "rimpull_limited_speed": {
        "power": 1.8e6,
        "mass": 4e5,
        "total_resistance": 0.12,
        "efficiency": 0.9,
        "traction_limit": 1e9,
        "speed_limit": 50.0,
        "drag_area": 45.0,
        "air_density": 1.2,
        "g": 9.80665,
    },
    "retarder_limited_speed": {
        "retarder_power": 2.5e6,
        "mass": 4e5,
        "rolling_resistance": 0.02,
        "grade": -0.1,
        "speed_limit": 40.0,
        "g": 9.80665,
    },
    "loose_density": {"bank_density": 2700.0, "swell": 0.35},
    "loading_passes": {"target_payload": 216000.0, "bucket_volume": 40.0, "fill_factor": 0.9, "loose_density": 2000.0},
    "segment_travel_time": {"length": 3000.0, "speed": 4.0},
    "cycle_time": {
        "spot_load": 60.0,
        "load": 240.0,
        "haul_travel": 900.0,
        "spot_dump": 90.0,
        "dump": 45.0,
        "return_travel": 600.0,
        "queue_load": 30.0,
        "queue_dump": 15.0,
    },
    "segment_energy": {
        "mass": 4e5,
        "length": 3000.0,
        "rolling_resistance": 0.02,
        "grade": 0.1,
        "efficiency": 0.35,
        "regen_efficiency": 0.6,
        "g": 9.80665,
    },
    "cycle_energy": {
        "mass": MASS_A,
        "length": LEN_A,
        "rolling_resistance": RR_A,
        "grade": GR_A,
        "efficiency": 0.35,
        "regen_efficiency": 0.6,
        "g": 9.80665,
    },
    "bev_cycle_energy": {
        "mass": MASS_A,
        "length": LEN_A,
        "rolling_resistance": RR_A,
        "grade": GR_A,
        "drive_efficiency": 0.85,
        "regen_efficiency": 0.6,
        "g": 9.80665,
    },
    "trolley_cycle_energy": {
        "mass": MASS_A,
        "length": LEN_A,
        "rolling_resistance": RR_A,
        "grade": GR_A,
        "on_trolley": np.array([True, False, False]),
        "diesel_efficiency": 0.35,
        "electric_efficiency": 0.9,
        "g": 9.80665,
    },
    "fuel_use": {"source_energy": 4e9, "fuel_energy_density": 36e9},
    "co2_from_diesel": {"fuel_volume": 0.112, "emission_factor": 2700.0},
    "co2_from_electricity": {"energy": 1.5e9, "grid_intensity": 1e-7},
    "match_factor": {"n_trucks": 6, "n_loaders": 1, "load_time": 240.0, "cycle_time": 1440.0},
    "mmc_queue": {"arrival_rate": 24 / 3600, "service_rate": 15 / 3600, "servers": 2},
    "finite_source_queue": {"n_trucks": 5, "travel_rate": 3 / 3600, "service_rate": 15 / 3600},
}
AGGREGATE = {"cycle_energy", "bev_cycle_energy", "trolley_cycle_energy"}
SCALAR_ONLY = {"mmc_queue", "finite_source_queue"}
ELEMENTWISE = sorted(set(BASE) - AGGREGATE - SCALAR_ONLY)

# ------------------------------------------------------------------ domain table (section 7.2)
# kind -> (invalid values, valid boundary values)
POS = ([0.0, -1.0, -1e-300, -INF], [])  # > 0
NONNEG = ([-1e-9, -1.0, -1e300], [0.0])  # >= 0
FINITE: tuple[list[float], list[float]] = ([], [-1.0, 0.0, 1.0])  # finite only (the NaN/inf battery covers the rest)
EFF = ([0.0, -0.1, 1.0000001, 1.5, 100.0], [1.0, 0.5])  # (0, 1]
FRAC = ([-0.1, 1.0000001, 2.0], [0.0, 1.0])  # [0, 1]
RRDOM = ([-0.01, 1.0, 1.5, 20.0], [0.0, 0.999])  # [0, 1)
FILL = ([0.0, -0.5, 2.0000001, 10.0], [2.0, 1.0])  # (0, 2]
LIMIT = ([0.0, -1.0, -INF], [INF])  # > 0, +inf allowed
COUNT = ([0, -1, 2.5, 100_001, 10**9], [1, 100_000])  # integer 1..100,000

DOMAIN: dict[str, dict[str, tuple[list[float], list[float]]]] = {
    "grade_resistance": {"grade": FINITE},
    "total_resistance": {"rolling_resistance": RRDOM, "grade": FINITE},
    "required_force": {
        "mass": POS,
        "total_resistance": FINITE,
        "acceleration": FINITE,
        "effective_mass": POS,
        "drag_area": NONNEG,
        "air_density": POS,
        "speed": NONNEG,
        "g": POS,
    },
    "rimpull_limited_speed": {
        "power": POS,
        "mass": POS,
        "total_resistance": FINITE,
        "efficiency": EFF,
        "traction_limit": LIMIT,
        "speed_limit": LIMIT,
        "drag_area": NONNEG,
        "air_density": POS,
        "g": POS,
    },
    "retarder_limited_speed": {
        "retarder_power": POS,
        "mass": POS,
        "rolling_resistance": RRDOM,
        "grade": FINITE,
        "speed_limit": LIMIT,
        "g": POS,
    },
    "loose_density": {"bank_density": POS, "swell": NONNEG},
    "loading_passes": {"target_payload": POS, "bucket_volume": POS, "fill_factor": FILL, "loose_density": POS},
    "segment_travel_time": {"length": NONNEG, "speed": POS},
    "cycle_time": {k: NONNEG for k in BASE["cycle_time"]},
    "segment_energy": {
        "mass": POS,
        "length": NONNEG,
        "rolling_resistance": RRDOM,
        "grade": FINITE,
        "efficiency": EFF,
        "regen_efficiency": FRAC,
        "g": POS,
    },
    "cycle_energy": {
        "mass": POS,
        "length": NONNEG,
        "rolling_resistance": RRDOM,
        "grade": FINITE,
        "efficiency": EFF,
        "regen_efficiency": FRAC,
        "g": POS,
    },
    "bev_cycle_energy": {
        "mass": POS,
        "length": NONNEG,
        "rolling_resistance": RRDOM,
        "grade": FINITE,
        "drive_efficiency": EFF,
        "regen_efficiency": FRAC,
        "g": POS,
    },
    "trolley_cycle_energy": {
        "mass": POS,
        "length": NONNEG,
        "rolling_resistance": RRDOM,
        "grade": FINITE,
        "diesel_efficiency": EFF,
        "electric_efficiency": EFF,
        "g": POS,
    },
    "fuel_use": {"source_energy": NONNEG, "fuel_energy_density": POS},
    "co2_from_diesel": {"fuel_volume": NONNEG, "emission_factor": POS},
    "co2_from_electricity": {"energy": NONNEG, "grid_intensity": NONNEG},
    "match_factor": {
        "n_trucks": COUNT,
        "n_loaders": ([0, -1, 2.5], [1, 3]),
        "load_time": POS,
        "cycle_time": POS,
    },
    "mmc_queue": {
        "arrival_rate": POS,
        "service_rate": POS,
        "servers": ([0, -1, 2.5, 10_001, 10**9], [10_000]),
    },
    "finite_source_queue": {"n_trucks": COUNT, "travel_rate": POS, "service_rate": POS},
}

CASES = [(fn, arg, bad) for fn, args in DOMAIN.items() for arg, (invalid, _) in args.items() for bad in invalid]
BOUNDARIES = [(fn, arg, ok) for fn, args in DOMAIN.items() for arg, (_, valid) in args.items() for ok in valid]


def call(fn: str, kwargs: dict[str, Any]) -> Any:
    return getattr(H, fn)(**kwargs)


def with_value(fn: str, arg: str, value: Any) -> dict[str, Any]:
    """Base kwargs with `arg` replaced; for the array-based functions the bad value sits at element 1."""
    kwargs = dict(BASE[fn])
    if fn in AGGREGATE and isinstance(kwargs[arg], np.ndarray):
        arr = kwargs[arg].copy()
        arr[1] = value
        kwargs[arg] = arr
    else:
        kwargs[arg] = value
    return kwargs


def id_of(case: tuple) -> str:
    return "-".join(str(c) for c in case)


# ------------------------------------------------------------------ FR-001-22: domain


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle(
    "analytical", "spec 001 7.2: a value outside the physical domain is an InputError naming the argument"
)
@pytest.mark.parametrize(("fn", "arg", "bad"), CASES, ids=[id_of(c) for c in CASES])
def test_domain_violation_is_an_input_error(fn: str, arg: str, bad: Any) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(fn, with_value(fn, arg, bad))
    assert ei.value.argument == arg


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle("analytical", "spec 001 7.2: the closed ends of every interval are accepted")
@pytest.mark.parametrize(("fn", "arg", "ok"), BOUNDARIES, ids=[id_of(c) for c in BOUNDARIES])
def test_domain_boundary_is_accepted(fn: str, arg: str, ok: Any) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = call(fn, with_value(fn, arg, ok))
    assert result is not None


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle("analytical", "spec 001 7.2: air_density is required when drag_area > 0")
@pytest.mark.parametrize("fn", ["required_force", "rimpull_limited_speed"])
def test_air_density_required_with_drag(fn: str) -> None:
    kwargs = dict(BASE[fn])
    del kwargs["air_density"]
    with pytest.raises(minephys.InputError) as ei:
        call(fn, kwargs)
    assert ei.value.argument == "air_density"
    kwargs["drag_area"] = 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert call(fn, kwargs) is not None  # no drag: no density needed


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle("analytical", "spec 001 7.2: load_time < cycle_time for the match factor")
@pytest.mark.parametrize(("load", "cycle"), [(1440.0, 1440.0), (1500.0, 1440.0), (2000.0, 100.0)])
def test_load_time_must_be_below_the_cycle_time(load: float, cycle: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        H.match_factor(6, 1, load, cycle)
    assert ei.value.argument in {"load_time", "cycle_time"}
    assert H.match_factor(6, 1, 1439.9999, 1440.0) > 0.0


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle(
    "analytical", "spec 001 7.2: only traction_limit and speed_limit accept +inf; every other argument rejects it"
)
@pytest.mark.parametrize("fn", sorted(DOMAIN))
def test_infinity_is_rejected_except_for_the_two_limits(fn: str) -> None:
    for arg in DOMAIN[fn]:
        if arg in {"traction_limit", "speed_limit"}:
            continue
        with pytest.raises(minephys.InputError) as ei:
            call(fn, with_value(fn, arg, INF))
        assert ei.value.argument == arg
    for arg in ("traction_limit", "speed_limit"):
        if arg in DOMAIN[fn]:
            with pytest.raises(minephys.InputError):
                call(fn, with_value(fn, arg, -INF))
            with pytest.raises(minephys.InputError):
                call(fn, with_value(fn, arg, math.nan))


@pytest.mark.req("FR-001-22")
@pytest.mark.oracle(
    "analytical", "spec 001 7.2: caps are inclusive (10,000 servers, 100,000 trucks) and exceeded caps are errors"
)
def test_caps_of_the_queue_models() -> None:
    assert math.isfinite(H.mmc_queue(1.0, 1.0, 10_000).mean_wait)
    with pytest.raises(minephys.InputError) as ei:
        H.mmc_queue(1.0, 1.0, 10_001)
    assert ei.value.argument == "servers"
    assert math.isfinite(H.finite_source_queue(100_000, 1e-3, 1.0).throughput)
    with pytest.raises(minephys.InputError) as ei2:
        H.finite_source_queue(100_001, 1e-3, 1.0)
    assert ei2.value.argument == "n_trucks"
    assert H.match_factor(100_000, 1, 10.0, 100.0) > 0.0
    with pytest.raises(minephys.InputError):
        H.match_factor(100_001, 1, 10.0, 100.0)


# ------------------------------------------------------------------ FR-001-23: tripwires (section 7.3)


@dataclass(frozen=True)
class Tripwire:
    row: str
    arg: str
    functions: tuple[str, ...]
    loud: tuple[float, ...]  # values that must warn
    quiet: tuple[float, ...]  # values that must not warn
    extra: dict[str, Any] = field(default_factory=dict)


TRIPWIRES = [
    Tripwire(
        "tripwire_grade_abs_max",
        "grade",
        ("grade_resistance", "total_resistance", "retarder_limited_speed", "segment_energy", "cycle_energy"),
        (0.3000001, -0.31, 30.0, -100.0),
        (0.3, -0.3, 0.0, 0.1),
    ),
    Tripwire(
        "tripwire_rolling_resistance_max",
        "rolling_resistance",
        ("total_resistance", "retarder_limited_speed", "segment_energy", "cycle_energy"),
        (0.2000001, 0.5, 0.99),
        (0.2, 0.0, 0.05),
    ),
    Tripwire(
        "tripwire_truck_mass_min",
        "mass",
        ("required_force", "rimpull_limited_speed", "retarder_limited_speed", "segment_energy", "cycle_energy"),
        (999.99, 400.0, 1.0),
        (1000.0, 4e5),
    ),
    Tripwire(
        "tripwire_truck_mass_max",
        "mass",
        ("required_force", "rimpull_limited_speed", "retarder_limited_speed", "segment_energy", "cycle_energy"),
        (2000001.0, 4e8, 4e9),
        (2000000.0, 4e5),
    ),
    Tripwire("tripwire_swell_max", "swell", ("loose_density",), (1.0000001, 35.0), (1.0, 0.0, 0.35)),
    Tripwire("tripwire_bank_density_min", "bank_density", ("loose_density",), (499.99, 2.7, 1.0), (500.0, 2700.0)),
    Tripwire(
        "tripwire_fuel_energy_density_min", "fuel_energy_density", ("fuel_use",), (9.99e8, 36.0, 3.6e7), (1e9, 36e9)
    ),
    Tripwire(
        "tripwire_grid_intensity_max",
        "grid_intensity",
        ("co2_from_electricity",),
        (1.0000001e-6, 0.4, 0.0005),
        (1e-6, 1e-7, 0.0),
    ),
]
TRIP_CASES = [(t.row, fn, v) for t in TRIPWIRES for fn in t.functions for v in t.loud]
QUIET_CASES = [(t.row, fn, v) for t in TRIPWIRES for fn in t.functions for v in t.quiet]
TRIP_BY_ROW = {t.row: t for t in TRIPWIRES}


def validity_warnings(fn: str, kwargs: dict[str, Any]) -> tuple[Any, list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        result = call(fn, kwargs)
    return result, [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]


@pytest.mark.req("FR-001-23")
@pytest.mark.oracle(
    "analytical", "spec 001 7.3: each unit tripwire warns, naming the argument and the row, and still returns"
)
@pytest.mark.parametrize(("row", "fn", "value"), TRIP_CASES, ids=[id_of(c) for c in TRIP_CASES])
def test_tripwire_warns_and_still_returns(row: str, fn: str, value: float) -> None:
    t = TRIP_BY_ROW[row]
    result, found = validity_warnings(fn, with_value(fn, t.arg, value))
    assert result is not None
    assert [w for w in found if w.message.row == row], f"no {row} warning in {[str(w.message) for w in found]}"
    w = next(w for w in found if w.message.row == row).message
    assert w.argument == t.arg
    assert row in str(w)
    assert t.arg in str(w)


@pytest.mark.req("FR-001-23")
@pytest.mark.oracle("analytical", "spec 001 7.3: values inside the limits (and exactly on them) stay silent")
@pytest.mark.parametrize(("row", "fn", "value"), QUIET_CASES, ids=[id_of(c) for c in QUIET_CASES])
def test_values_inside_the_tripwire_are_silent(row: str, fn: str, value: float) -> None:
    t = TRIP_BY_ROW[row]
    _, found = validity_warnings(fn, with_value(fn, t.arg, value))
    assert [w for w in found if w.message.row == row] == []


@pytest.mark.req("FR-001-23")
@pytest.mark.oracle("analytical", "an array warns if any one element trips the wire")
def test_one_element_of_an_array_is_enough() -> None:
    grades = np.array([0.05, 0.1, 25.0])
    _, found = validity_warnings("segment_energy", {**BASE["segment_energy"], "grade": grades})
    assert any(w.message.row == "tripwire_grade_abs_max" for w in found)
    _, none = validity_warnings("segment_energy", {**BASE["segment_energy"], "grade": np.array([0.05, 0.1, 0.2])})
    assert none == []


@pytest.mark.req("FR-001-23")
@pytest.mark.oracle("analytical", "the baseline calls of section 7.4 trip no wire at all")
@pytest.mark.parametrize("fn", sorted(BASE))
def test_the_worked_examples_are_silent(fn: str) -> None:
    _, found = validity_warnings(fn, dict(BASE[fn]))
    assert found == []


# ------------------------------------------------------------------ foundation contract suite on every function


def f32(lo: float, hi: float) -> st.SearchStrategy[float]:
    # bounds rounded to the nearest float32 (Hypothesis requires representable bounds at width 32)
    # (+ 0.0 turns -0.0 into 0.0: the integer variant of a negative zero would differ in its sign bit)
    return st.floats(float(np.float32(lo)), float(np.float32(hi)), width=32).map(lambda x: x + 0.0)


@dataclass(frozen=True)
class Op:
    """Hypothesis operand description of one function."""

    strategies: dict[str, st.SearchStrategy[Any]]
    fixed: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    posinf: tuple[str, ...] = ()


def counts(lo: int, hi: int) -> st.SearchStrategy[float]:
    return st.integers(lo, hi).map(float)


OPS: dict[str, Op] = {
    "grade_resistance": Op({"grade": f32(-1.0, 1.0)}, {"small_angle": False}, ("small_angle",)),
    "total_resistance": Op(
        {"rolling_resistance": f32(0.0, 0.2), "grade": f32(-0.3, 0.3)}, {"small_angle": True}, ("small_angle",)
    ),
    "required_force": Op(
        {
            "mass": f32(2e4, 7e5),
            "total_resistance": f32(-0.1, 0.3),
            "acceleration": f32(-3.0, 3.0),
            "effective_mass": f32(2e4, 7e5),
            "drag_area": f32(1.0, 100.0),
            "air_density": f32(0.5, 2.0),
            "speed": f32(0.0, 40.0),
            "g": f32(9.0, 10.0),
        }
    ),
    "rimpull_limited_speed": Op(
        {
            "power": f32(1e5, 5e6),
            "mass": f32(2e4, 7e5),
            "total_resistance": f32(0.01, 0.3),
            "efficiency": f32(0.1, 1.0),
            "traction_limit": f32(1e5, 1e8),
            "speed_limit": f32(1.0, 100.0),
            "drag_area": f32(1.0, 100.0),
            "air_density": f32(0.5, 2.0),
            "g": f32(9.0, 10.0),
        },
        posinf=("traction_limit", "speed_limit"),
    ),
    "retarder_limited_speed": Op(
        {
            "retarder_power": f32(1e5, 5e6),
            "mass": f32(2e4, 7e5),
            "rolling_resistance": f32(0.0, 0.05),
            "grade": f32(-0.3, -0.1),
            "speed_limit": f32(1.0, 100.0),
            "g": f32(9.0, 10.0),
        },
        {"small_angle": False},
        ("small_angle",),
        ("speed_limit",),
    ),
    "loose_density": Op({"bank_density": f32(1000.0, 5000.0), "swell": f32(0.0, 1.0)}),
    "loading_passes": Op(
        {
            "target_payload": f32(1e3, 6e5),
            "bucket_volume": f32(1.0, 60.0),
            "fill_factor": f32(0.5, 1.2),
            "loose_density": f32(1000.0, 3000.0),
        }
    ),
    "segment_travel_time": Op({"length": f32(0.0, 1e5), "speed": f32(0.5, 40.0)}),
    "cycle_time": Op({k: f32(0.0, 3600.0) for k in BASE["cycle_time"]}),
    "segment_energy": Op(
        {
            "mass": f32(2e4, 7e5),
            "length": f32(0.0, 5000.0),
            "rolling_resistance": f32(0.0, 0.1),
            "grade": f32(-0.3, 0.3),
            "efficiency": f32(0.1, 1.0),
            "regen_efficiency": f32(0.0, 1.0),
            "g": f32(9.0, 10.0),
        },
        {"small_angle": False},
        ("small_angle",),
    ),
    "fuel_use": Op({"source_energy": f32(0.0, 1e11), "fuel_energy_density": f32(1.1e9, 5e10)}),
    "co2_from_diesel": Op({"fuel_volume": f32(0.0, 100.0), "emission_factor": f32(1000.0, 4000.0)}),
    "co2_from_electricity": Op({"energy": f32(0.0, 1e10), "grid_intensity": f32(0.0, 1e-6)}),
    "match_factor": Op(
        {
            "n_trucks": counts(1, 200),
            "n_loaders": counts(1, 20),
            "load_time": f32(10.0, 100.0),
            "cycle_time": f32(200.0, 2000.0),
        }
    ),
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
            kwargs[name] = np.array(
                draw(st.lists(strat, min_size=int(np.prod(shp)), max_size=int(np.prod(shp)))), dtype=np.float64
            ).reshape(shp)
    return kwargs


def float_wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Cast integer-valued results to float64 so the float suite can compare them (loading_passes)."""

    def wrapped(**kw: Any) -> Any:
        out = fn(**kw)
        return np.float64(out) if np.ndim(out) == 0 else np.asarray(out, dtype=np.float64)

    return wrapped


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.req("P-000-03")
@pytest.mark.req("FR-000-07")
@pytest.mark.req("P-000-01")
@pytest.mark.oracle(
    "analytical", "foundation contract suite: purity, float32 and int operands, elementwise = scalar evaluation"
)
@pytest.mark.parametrize("name", ELEMENTWISE)
@settings(deadline=None)
@given(data=st.data())
def test_contract_suite_on_elementwise_functions(name: str, data: st.DataObject) -> None:
    kwargs = data.draw(operands(OPS[name]))
    fn = getattr(H, name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_purity(fn, kwargs)
        cs.check_dtype_invariance(fn if name != "loading_passes" else float_wrapper(fn), kwargs)
        if name == "loading_passes":
            out = fn(**kwargs)
            assert out.dtype == np.int64 if np.ndim(out) else type(out) is np.int64
            cs.check_elementwise(float_wrapper(fn), kwargs)
        else:
            cs.check_elementwise(fn, kwargs)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle(
    "analytical", "foundation hostile battery: NaN, inf, wrong types name the argument (except legal None)"
)
@pytest.mark.parametrize(
    ("name", "arg"),
    [
        (n, a)
        for n in ELEMENTWISE
        for a in OPS[n].strategies
        if a not in {"effective_mass", "air_density", "emission_factor"} and a not in OPS[n].posinf
    ],
    ids=lambda v: str(v),
)
def test_hostile_battery_on_numeric_arguments(name: str, arg: str) -> None:
    kwargs = dict(BASE[name])
    fn = getattr(H, name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(fn, kwargs, arg)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "the two limits accept +inf, nothing else; the battery honours allow_posinf")
@pytest.mark.parametrize(
    ("name", "arg"),
    [
        ("rimpull_limited_speed", "traction_limit"),
        ("rimpull_limited_speed", "speed_limit"),
        ("retarder_limited_speed", "speed_limit"),
    ],
)
def test_hostile_battery_on_the_infinite_limits(name: str, arg: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(getattr(H, name), dict(BASE[name]), arg, allow_posinf=True)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle(
    "analytical", "optional arguments whose None is legal: NaN/inf are InputError, wrong types InputTypeError"
)
@pytest.mark.parametrize(
    ("name", "arg"),
    [
        ("required_force", "effective_mass"),
        ("required_force", "air_density"),
        ("rimpull_limited_speed", "air_density"),
        ("co2_from_diesel", "emission_factor"),
    ],
)
def test_hostile_values_for_optional_arguments(name: str, arg: str) -> None:
    fn = getattr(H, name)
    for bad in (math.nan, INF, -INF):
        with pytest.raises(minephys.InputError) as ei:
            fn(**{**BASE[name], arg: bad})
        assert ei.value.argument == arg
        with pytest.raises(minephys.InputError) as ei2:
            fn(**{**BASE[name], arg: np.array([BASE[name][arg], bad])})
        assert ei2.value.argument == arg
    for bad in ("1.0", b"1", 1 + 1j, True, object(), np.datetime64("2026-01-01")):
        with pytest.raises(minephys.InputTypeError) as ei3:
            fn(**{**BASE[name], arg: bad})
        assert ei3.value.argument == arg


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "declared boolean flags must be boolean")
@pytest.mark.parametrize(
    ("name", "flag"),
    [(n, f) for n in ELEMENTWISE for f in OPS[n].flags],
)
def test_boolean_flags(name: str, flag: str) -> None:
    kwargs = {**BASE[name], flag: True}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_hostile(getattr(H, name), kwargs, flag, boolean=True)


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("analytical", "arrays of shapes (3,) and (4,) cannot broadcast: InputError naming both arguments")
@pytest.mark.parametrize("name", [n for n in ELEMENTWISE if len(OPS[n].strategies) >= 2])
def test_shape_mismatch(name: str) -> None:
    # written here instead of cs.check_shape_hostile: that helper fills the arrays with ones, which lie outside the
    # domain of some arguments (rolling_resistance < 1), so a domain error could mask the shape error.
    first, second = list(OPS[name].strategies)[:2]
    kwargs = dict(BASE[name])
    kwargs[first] = np.full(3, float(kwargs[first]))
    kwargs[second] = np.full(4, float(kwargs[second]))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(minephys.InputError) as ei:
            getattr(H, name)(**kwargs)
    msg = str(ei.value)
    assert first in msg
    assert second in msg
    assert "(3,)" in msg
    assert "(4,)" in msg


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle(
    "analytical", "an elementwise function given empty arrays returns an empty float64 array (int64 for passes)"
)
@pytest.mark.parametrize("name", ELEMENTWISE)
def test_empty_arrays(name: str) -> None:
    arg = next(iter(OPS[name].strategies))
    kwargs = {**BASE[name], arg: np.empty(0)}
    out = getattr(H, name)(**kwargs)
    assert out.shape == (0,)
    assert out.dtype == (np.int64 if name == "loading_passes" else np.float64)


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle(
    "analytical", "aggregate and queue functions: two calls are bitwise identical and the inputs untouched"
)
@pytest.mark.parametrize("name", sorted(AGGREGATE | SCALAR_ONLY))
def test_purity_of_aggregate_and_queue_functions(name: str) -> None:
    fn = getattr(H, name)
    kwargs = dict(BASE[name])

    def flat(**kw: Any) -> np.ndarray:
        out = fn(**kw)
        parts = list(out) if isinstance(out, tuple) else [out]
        return np.array([float(p) for p in parts], dtype=np.float64)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_purity(flat, {k: v for k, v in kwargs.items()})
        before = {k: v.copy() for k, v in kwargs.items() if isinstance(v, np.ndarray)}
        fn(**kwargs)
        for k, v in before.items():
            assert np.array_equal(kwargs[k], v), k


@pytest.mark.req("P-000-03")
@pytest.mark.oracle("analytical", "float32 and int32 per-segment operands give bitwise the float64 result (aggregates)")
@pytest.mark.parametrize("name", ["cycle_energy", "bev_cycle_energy"])
@settings(deadline=None)
@given(
    n=st.integers(1, 12),
    data=st.data(),
)
def test_dtype_invariance_of_the_segment_aggregates(name: str, n: int, data: st.DataObject) -> None:
    def arr(lo: float, hi: float) -> np.ndarray:
        return np.array(data.draw(st.lists(f32(lo, hi), min_size=n, max_size=n)), dtype=np.float64)

    kwargs = {
        "mass": arr(2e4, 7e5),
        "length": arr(0.0, 5000.0),
        "rolling_resistance": arr(0.0, 0.1),
        "grade": arr(-0.3, 0.3),
    }
    kwargs.update(
        {"efficiency": 0.5, "regen_efficiency": 0.25}
        if name == "cycle_energy"
        else {"drive_efficiency": 0.5, "regen_efficiency": 0.25}
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cs.check_dtype_invariance(getattr(H, name), kwargs)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.req("FR-000-12")
@pytest.mark.oracle(
    "analytical", "scalar-only queue functions: hostile scalars name the argument; arrays are rank errors"
)
@pytest.mark.parametrize("name", sorted(SCALAR_ONLY))
def test_hostile_battery_and_rank_of_the_queue_functions(name: str) -> None:
    kwargs = dict(BASE[name])
    fn = getattr(H, name)
    for arg, value in kwargs.items():
        for bad in (math.nan, INF, -INF):
            with pytest.raises(minephys.InputError) as ei:
                fn(**{**kwargs, arg: bad})
            assert ei.value.argument == arg
        for bad in ("1", b"1", None, 1 + 1j, True, object()):
            with pytest.raises(minephys.InputTypeError) as ei2:
                fn(**{**kwargs, arg: bad})
            assert ei2.value.argument == arg
        with pytest.raises(minephys.InputError) as ei3:
            fn(**{**kwargs, arg: np.array([value, value])})
        assert ei3.value.argument == arg, "scalar-only: a rank-1 array is a rank error"
