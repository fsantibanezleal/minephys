"""T-005-064 (FR-000-05, FR-000-07, FR-000-10 to FR-000-13, P-000-01, P-000-02, P-000-03): the foundation cross-cutting
contract checks on every elementwise function of `minephys.comminution`.

The shared contract suite of foundation task T-000-010 (`tests/_contract_suite.py`) is not available in this red phase, so
the same checks are written here against the functions of this module (the registry below lists each function with a
generator of valid arguments in SI units; arguments are drawn from a Hypothesis seed):
- P-000-01: for broadcastable valid inputs of rank 0 to 2, f(arrays)[i] equals f evaluated on the scalars at index i
  (TC-6: rtol 1e-14, atol 1e-14 x max|f| over the batch);
- P-000-02 and FR-000-05: two calls give bitwise-identical results and leave every input array unchanged;
- P-000-03: float32 inputs, and integer inputs for the index arguments, give bitwise the same result as the same values cast to
  float64 first;
- FR-000-07: scalars give `numpy.float64`, arrays a float64 array of the broadcast shape; FR-000-13: empty arrays give an empty
  float64 array of the broadcast shape;
- FR-000-10, FR-000-11, FR-000-12: a NaN or +-inf argument raises `InputError` naming it, a string argument raises
  `InputTypeError` naming it, unbroadcastable arrays raise `InputError`.
`two_product_recovery` returns a pair and is checked component by component.
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


def _c():
    return importlib.import_module("minephys.comminution")


def _u(rng: np.random.Generator, lo: float, hi: float, k: int) -> np.ndarray:
    return rng.uniform(lo, hi, k)


# name -> (generator of float64 argument arrays of length k, fixed non-array keyword arguments, integer-capable arguments)
def _bond(rng, k):
    p = _u(rng, 1e-4, 1e-3, k)
    return {"work_index": _u(rng, 3.6e3, 3.6e5, k), "f80": p * _u(rng, 1.5, 30.0, k), "p80": p}


def _bond_io(rng, k):
    p = _u(rng, 1e-4, 1e-3, k)
    return {"specific_energy": _u(rng, 3.6e3, 3.6e5, k), "f80": p * _u(rng, 1.5, 30.0, k), "p80": p}


def _bond_bm(rng, k):
    p = _u(rng, 1e-4, 5e-4, k)
    return {
        "closing_screen": _u(rng, 5e-5, 5e-4, k),
        "grindability": _u(rng, 5e-4, 3e-3, k),
        "f80": p * _u(rng, 2.0, 40.0, k),
        "p80": p,
    }


def _mor(rng, k):
    x2 = _u(rng, 1e-4, 1e-2, k)
    return {"m_index": _u(rng, 3.6e3, 3.6e5, k), "x1": x2 * _u(rng, 1.5, 30.0, k), "x2": x2}


def _mor_coarse(rng, k):
    return {"mia": _u(rng, 3.6e3, 3.6e5, k), "x1": _u(rng, 1e-3, 0.2, k)}


def _mor_fine(rng, k):
    return {"mib": _u(rng, 3.6e3, 3.6e5, k), "p80": _u(rng, 5e-5, 7e-4, k)}


def _mor_crusher(rng, k):
    x2 = _u(rng, 1e-3, 3e-2, k)
    return {"mic": _u(rng, 3.6e3, 3.6e5, k), "x1": x2 * _u(rng, 1.5, 5.0, k), "x2": x2}


def _mor_hpgr(rng, k):
    x2 = _u(rng, 1e-3, 1e-2, k)
    return {"mih": _u(rng, 3.6e3, 3.6e5, k), "x1": x2 * _u(rng, 2.0, 8.0, k), "x2": x2}


def _mor_ws(rng, k):
    x2 = _u(rng, 1e-3, 2e-2, k)
    return {"mia": _u(rng, 3.6e3, 3.6e5, k), "x1": x2 * _u(rng, 2.0, 10.0, k), "x2": x2}


def _mor_mib(rng, k):
    p = _u(rng, 1e-4, 5e-4, k)
    return {
        "closing_screen": _u(rng, 5e-5, 5e-4, k),
        "grindability": _u(rng, 5e-4, 3e-3, k),
        "f80": p * _u(rng, 2.0, 40.0, k),
        "p80": p,
    }


def _flo(rng, k):
    return {"r_inf": _u(rng, 0.1, 1.0, k), "k": _u(rng, 1e-3, 0.1, k), "t": _u(rng, 1.0, 500.0, k)}


def _cell(rng, k):
    return {"r_inf": _u(rng, 0.1, 1.0, k), "k": _u(rng, 1e-3, 0.1, k), "tau": _u(rng, 1.0, 500.0, k)}


def _whiten(rng, k):
    return {"sizes": _u(rng, 1e-3, 0.2, k)}


def _two(rng, k):
    t = _u(rng, 0.0, 0.01, k)
    f = t + _u(rng, 0.005, 0.05, k)
    return {"feed_grade": f, "concentrate_grade": f + _u(rng, 0.05, 0.5, k), "tail_grade": t}


REGISTRY: dict[str, tuple[Callable[..., dict[str, np.ndarray]], dict[str, Any], tuple[str, ...]]] = {
    "bond_energy": (_bond, {}, ("work_index",)),
    "bond_operating_work_index": (_bond_io, {}, ("specific_energy",)),
    "bond_ball_mill_work_index": (_bond_bm, {}, ()),
    "morrell_energy": (_mor, {}, ("m_index",)),
    "morrell_tumbling_coarse": (_mor_coarse, {"pebble_crusher": True}, ("mia",)),
    "morrell_tumbling_fine": (_mor_fine, {}, ("mib",)),
    "morrell_crusher": (_mor_crusher, {"closed_circuit": True, "stage": "secondary"}, ("mic",)),
    "morrell_hpgr": (_mor_hpgr, {"closed_circuit": False}, ("mih",)),
    "morrell_size_distribution_correction": (_mor_ws, {}, ("mia",)),
    "morrell_mib": (_mor_mib, {}, ()),
    "flotation_first_order": (_flo, {}, ()),
    "klimpel_recovery": (_flo, {}, ()),
    "flotation_cell_recovery": (_cell, {"n_cells": 3}, ()),
    "whiten_classification": (_whiten, {"k1": 0.02, "k2": 0.1, "k3": 2.0}, ()),
    "two_product_recovery": (_two, {}, ()),
}
NAMES = list(REGISTRY)
SEEDS = st.integers(0, 2**32 - 1)


def _call(name: str, args: dict[str, Any]) -> tuple[np.ndarray, ...]:
    out = getattr(_c(), name)(**args, **REGISTRY[name][1])
    return tuple(out) if isinstance(out, tuple) else (out,)


def _args(name: str, seed: int, k: int) -> dict[str, np.ndarray]:
    return REGISTRY[name][0](np.random.default_rng(seed), k)


@pytest.mark.req("P-000-01")
@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("analytical", "vectorised evaluation equals element-by-element scalar evaluation")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(1, 16), shape_choice=st.integers(0, 2))
def test_p_000_01_vectorised_equals_scalar(name: str, seed: int, k: int, shape_choice: int) -> None:
    args = _args(name, seed, k)
    if shape_choice == 1 and k >= 4:  # rank 2
        r = k // 2
        args = {a: v[: 2 * r].reshape(2, r) for a, v in args.items()}
    vec = _call(name, args)
    for part, out in enumerate(vec):
        assert isinstance(out, np.ndarray) and out.dtype == np.float64 and out.shape == next(iter(args.values())).shape
        flat = {a: v.ravel() for a, v in args.items()}
        scale = float(np.max(np.abs(out))) if out.size else 0.0
        for i in range(out.size):
            scalars = {a: float(v[i]) for a, v in flat.items()}
            one = _call(name, scalars)[part]
            assert isinstance(one, np.float64)
            np.testing.assert_allclose(out.ravel()[i], one, rtol=1e-14, atol=1e-14 * scale)


# an argument without ordering constraints, used as the Python scalar that broadcasts against the others
FREE = {
    "bond_energy": ("work_index", None),
    "bond_operating_work_index": ("specific_energy", None),
    "bond_ball_mill_work_index": ("grindability", None),
    "morrell_energy": ("m_index", None),
    "morrell_tumbling_coarse": ("mia", None),
    "morrell_tumbling_fine": ("mib", None),
    "morrell_crusher": ("mic", None),
    "morrell_hpgr": ("mih", None),
    "morrell_size_distribution_correction": ("mia", None),
    "morrell_mib": ("grindability", None),
    "flotation_first_order": ("r_inf", None),
    "klimpel_recovery": ("r_inf", None),
    "flotation_cell_recovery": ("r_inf", None),
    "two_product_recovery": ("tail_grade", 0.0),  # a zero tail grade is below every generated feed grade
}


@pytest.mark.req("P-000-01")
@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", list(FREE))
@CI
@given(seed=SEEDS, k=st.integers(2, 12))
def test_p_000_01_scalar_arguments_broadcast_against_arrays(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    arg, forced = FREE[name]
    value = float(args[arg][0]) if forced is None else forced
    mixed = dict(args, **{arg: value})  # a Python scalar against arrays
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
        assert np.array_equal(x, y) and x.tobytes() == y.tobytes()
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
def test_fr_000_07_python_numpy_scalars_and_dtypes_are_accepted(name: str) -> None:
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
    importlib.import_module("minephys.comminution")
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
