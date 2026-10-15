"""T-006-054 (FR-000-05, FR-000-07, FR-000-10 to FR-000-13, P-000-01, P-000-02, P-000-03): the foundation cross-cutting contract
checks on every elementwise function of `minephys.environment`.

The shared contract suite of foundation task T-000-010 (`tests/_contract_suite.py`) is not available in this red phase, so the
same checks are written here against the functions of this module (registry below: each function with a generator of valid
SI arguments drawn from a Hypothesis seed):
- P-000-01: for broadcastable valid inputs of rank 0 to 2, f(arrays)[i] equals f on the scalars at index i (TC-6: rtol 1e-14,
  atol 1e-14 x max|f|);
- P-000-02 and FR-000-05: two calls give bitwise-identical results and leave every input array unchanged;
- P-000-03: float32 inputs, and integer inputs for the count-like arguments, give bitwise the same result as the same values cast
  to float64 first;
- FR-000-07 / FR-000-13: scalars give `numpy.float64`, arrays a float64 array of the broadcast shape, empty arrays an empty
  float64 array;
- FR-000-10, FR-000-11, FR-000-12: NaN or +-inf raises `InputError` naming the argument, a string raises `InputTypeError` naming
  it, unbroadcastable arrays raise `InputError` naming the arguments.
`pasquill_sigmas` and the pair-returning functions are checked component by component. Aggregate functions (`path_transmittance`,
`lidar_dust_return`, `fleet_mean_vehicle_weight`) and `ap42_unpaved_validity` are covered in their own unit tests.
Oracle: the contract itself (invariants), no expected numbers.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)
ST = 907.18474


def _e():
    return importlib.import_module("minephys.environment")


def _u(rng: np.random.Generator, lo: float, hi: float, k: int) -> np.ndarray:
    return rng.uniform(lo, hi, k)


def _ap42(rng, k):
    return {"silt_fraction": _u(rng, 0.02, 0.25, k), "mean_weight": _u(rng, 2000.0, 260_000.0, k)}


def _precip(rng, k):
    return {"emission_factor": _u(rng, 1e-6, 1e-2, k), "wet_days": _u(rng, 0.0, 365.0, k)}


def _water(rng, k):
    return {"moisture_ratio": _u(rng, 0.0, 5.0, k)}


def _controlled(rng, k):
    return {"emission_factor": _u(rng, 1e-6, 1e-2, k), "control_efficiency": _u(rng, 0.0, 1.0, k)}


def _line_rate(rng, k):
    return {"emission_factor": _u(rng, 1e-6, 1e-2, k), "vehicles_per_second": _u(rng, 0.0, 1.0, k)}


def _sigmas(rng, k):
    return {"x": _u(rng, 150.0, 1e5, k)}


def _plume(rng, k):
    return {
        "q": _u(rng, 1e-6, 1.0, k),
        "u": _u(rng, 0.5, 20.0, k),
        "y": _u(rng, -300.0, 300.0, k),
        "z": _u(rng, 0.0, 200.0, k),
        "h": _u(rng, 0.0, 200.0, k),
        "sigma_y": _u(rng, 1.0, 500.0, k),
        "sigma_z": _u(rng, 1.0, 500.0, k),
    }


def _line(rng, k):
    return {
        "q_line": _u(rng, 1e-9, 1e-3, k),
        "u": _u(rng, 0.5, 20.0, k),
        "z": _u(rng, 0.0, 200.0, k),
        "h": _u(rng, 0.0, 200.0, k),
        "sigma_z": _u(rng, 1.0, 500.0, k),
    }


def _finite(rng, k):
    a = _line(rng, k)
    a.update(
        {
            "y": _u(rng, -100.0, 100.0, k),
            "y1": _u(rng, -200.0, -10.0, k),
            "y2": _u(rng, 10.0, 200.0, k),
            "sigma_y": _u(rng, 5.0, 100.0, k),
        }
    )
    return a


def _kmass(rng, k):
    return {"diameter": _u(rng, 1e-6, 1e-3, k), "particle_density": _u(rng, 500.0, 8000.0, k)}


def _ext(rng, k):
    return {"mass_concentration": _u(rng, 1e-10, 1e-2, k), "mass_extinction": _u(rng, 1.0, 500.0, k)}


def _beer(rng, k):
    return {"extinction": _u(rng, 1e-8, 0.1, k), "path_length": _u(rng, 0.0, 500.0, k)}


# name -> (generator, fixed non-array keyword arguments, integer-capable arguments)
REGISTRY: dict[str, tuple[Callable[..., dict[str, np.ndarray]], dict[str, Any], tuple[str, ...]]] = {
    "ap42_unpaved_emission_factor": (_ap42, {"size_class": "PM10"}, ()),
    "precipitation_correction": (_precip, {}, ()),
    "watering_control_efficiency": (_water, {}, ()),
    "controlled_emission_factor": (_controlled, {}, ()),
    "line_emission_rate": (_line_rate, {}, ()),
    "pasquill_sigmas": (_sigmas, {"stability_class": "D"}, ()),
    "gaussian_plume": (_plume, {}, ()),
    "line_source_plume": (_line, {}, ()),
    "finite_line_source_plume": (_finite, {}, ()),
    "mass_extinction_coefficient": (_kmass, {"extinction_efficiency": 2.0}, ("particle_density",)),
    "extinction_coefficient": (_ext, {}, ("mass_extinction",)),
    "beer_lambert_transmittance": (_beer, {}, ()),
}
NAMES = list(REGISTRY)


def _call(name: str, args: dict[str, Any]) -> tuple[np.ndarray, ...]:
    out = getattr(_e(), name)(**args, **REGISTRY[name][1])
    return tuple(out) if isinstance(out, tuple) else (out,)


def _args(name: str, seed: int, k: int) -> dict[str, np.ndarray]:
    return REGISTRY[name][0](np.random.default_rng(seed), k)


@pytest.mark.req("P-000-01")
@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("analytical", "vectorised evaluation equals element-by-element scalar evaluation")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(1, 16), rank2=st.booleans())
def test_p_000_01_vectorised_equals_scalar(name: str, seed: int, k: int, rank2: bool) -> None:
    args = _args(name, seed, k)
    if rank2 and k >= 4:
        r = k // 2
        args = {a: v[: 2 * r].reshape(2, r) for a, v in args.items()}
    vec = _call(name, args)
    shape = next(iter(args.values())).shape
    for part, out in enumerate(vec):
        assert isinstance(out, np.ndarray) and out.dtype == np.float64 and out.shape == shape
        flat = {a: v.ravel() for a, v in args.items()}
        scale = float(np.max(np.abs(out))) if out.size else 0.0
        for i in range(out.size):
            one = _call(name, {a: float(v[i]) for a, v in flat.items()})[part]
            assert isinstance(one, np.float64)
            np.testing.assert_allclose(out.ravel()[i], one, rtol=1e-14, atol=1e-14 * scale)


# an argument without constraints against the others, passed as a Python scalar to test broadcasting
FREE = {
    "ap42_unpaved_emission_factor": "silt_fraction",
    "precipitation_correction": "emission_factor",
    "controlled_emission_factor": "emission_factor",
    "line_emission_rate": "emission_factor",
    "gaussian_plume": "q",
    "line_source_plume": "q_line",
    "finite_line_source_plume": "q_line",
    "mass_extinction_coefficient": "diameter",
    "extinction_coefficient": "mass_extinction",
    "beer_lambert_transmittance": "extinction",
}


@pytest.mark.req("P-000-01")
@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", list(FREE))
@CI
@given(seed=SEEDS, k=st.integers(2, 12))
def test_p_000_01_scalar_arguments_broadcast_against_arrays(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    arg = FREE[name]
    value = float(args[arg][0])
    mixed = dict(args, **{arg: value})
    ref = dict(args, **{arg: np.full(k, value)})
    for g, w in zip(_call(name, mixed), _call(name, ref), strict=True):
        assert isinstance(g, np.ndarray) and g.dtype == np.float64 and g.shape == (k,)
        np.testing.assert_allclose(g, w, rtol=1e-14, atol=0)


@pytest.mark.req("P-000-02")
@pytest.mark.req("FR-000-05")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(1, 16))
def test_p_000_02_pure_bitwise_deterministic_and_inputs_unchanged(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    before = {a: v.copy() for a, v in args.items()}
    first, second = _call(name, args), _call(name, args)
    for x, y in zip(first, second, strict=True):
        assert x.tobytes() == y.tobytes()
    for a, v in args.items():
        assert np.array_equal(v, before[a]) and v.dtype == before[a].dtype


@pytest.mark.req("P-000-03")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(1, 16))
def test_p_000_03_float32_inputs_equal_float64_casts(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    a32 = {a: v.astype(np.float32) for a, v in args.items()}
    a64 = {a: v.astype(np.float64) for a, v in a32.items()}
    for x, y in zip(_call(name, a32), _call(name, a64), strict=True):
        assert x.dtype == np.float64 and x.tobytes() == y.tobytes()


@pytest.mark.req("P-000-03")
@pytest.mark.parametrize("name", [n for n in NAMES if REGISTRY[n][2]])
@CI
@given(seed=SEEDS, k=st.integers(1, 16))
def test_p_000_03_integer_inputs_equal_float64_casts(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    ints = dict(args)
    for a in REGISTRY[name][2]:
        ints[a] = np.round(args[a]).astype(np.int64)
    floats = {a: v.astype(np.float64) for a, v in ints.items()}
    for x, y in zip(_call(name, ints), _call(name, floats), strict=True):
        assert x.tobytes() == y.tobytes()


@pytest.mark.req("FR-000-13")
@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", NAMES)
def test_fr_000_13_empty_arrays_give_an_empty_float64_array(name: str) -> None:
    args = {a: np.empty(0) for a in _args(name, 0, 1)}
    for out in _call(name, args):
        assert isinstance(out, np.ndarray) and out.dtype == np.float64 and out.shape == (0,)


@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", NAMES)
def test_fr_000_07_python_and_numpy_scalars_give_float64(name: str) -> None:
    args = {a: float(v[0]) for a, v in _args(name, 3, 1).items()}
    for out in _call(name, args):
        assert isinstance(out, np.float64)
    np_scalars = {a: np.float64(v) for a, v in args.items()}
    for x, y in zip(_call(name, args), _call(name, np_scalars), strict=True):
        assert x == y


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.req("FR-000-12")
@pytest.mark.parametrize("name", NAMES)
def test_fr_000_10_11_12_hostile_arguments_name_the_argument(name: str) -> None:
    importlib.import_module("minephys.environment")
    import minephys

    base = {a: float(v[0]) for a, v in _args(name, 5, 1).items()}
    for arg in base:
        for bad in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(minephys.InputError) as exc:
                _call(name, dict(base, **{arg: bad}))
            assert exc.value.argument == arg
        with pytest.raises(minephys.InputTypeError) as exc2:
            _call(name, dict(base, **{arg: "text"}))
        assert exc2.value.argument == arg
    if len(base) >= 2:
        first, second = list(base)[:2]
        with pytest.raises(minephys.InputError) as exc3:
            _call(name, dict(base, **{first: np.full(3, base[first]), second: np.full(2, base[second])}))
        assert first in str(exc3.value) and second in str(exc3.value)
