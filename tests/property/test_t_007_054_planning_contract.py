"""T-007-054 (FR-000-05, FR-000-07, FR-000-10 to FR-000-13, P-000-01, P-000-02, P-000-03): the foundation cross-cutting contract
checks on `minephys.planning`.

The shared contract suite of foundation task T-000-010 (`tests/_contract_suite.py`) is not available in this red phase, so the same
checks are written here against the functions of this module.
- Elementwise functions (`block_economic_value` -> `.value` float64 and `.processed` bool, `breakeven_cutoff_grade`): P-000-01
  (vectorised equals scalar, TC-6: rtol 1e-14, atol 1e-14 x max|f|), P-000-03 (float32 and integer inputs equal their float64 cast,
  bitwise), FR-000-07 (scalars give `numpy.float64`, arrays the broadcast float64 array), FR-000-13 (empty arrays give empty arrays),
  FR-000-10 / 11 / 12 (NaN or inf and strings name the argument, unbroadcastable arrays name the arguments).
- Every function (P-000-02, FR-000-05): two calls give bitwise-identical results and leave every input array unchanged.
Oracle: the contract itself (invariants), no expected numbers.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)


def _p():
    return importlib.import_module("minephys.planning")


def _bv_args(rng: np.random.Generator, k: int) -> dict[str, np.ndarray]:
    price = rng.uniform(5.0, 50.0, k)
    return {
        "tonnage": rng.uniform(1e3, 1e8, k),
        "grade": rng.uniform(0.0, 0.1, k),
        "price": price,
        "selling_cost": price * rng.uniform(0.05, 0.4, k),
        "recovery": rng.uniform(0.3, 1.0, k),
        "processing_cost": rng.uniform(1e-4, 5e-2, k),
        "mining_cost": rng.uniform(1e-4, 5e-2, k),
    }


def _be_args(rng: np.random.Generator, k: int) -> dict[str, np.ndarray]:
    price = rng.uniform(5.0, 50.0, k)
    return {
        "processing_cost": rng.uniform(1e-4, 5e-2, k),
        "price": price,
        "selling_cost": price * rng.uniform(0.05, 0.4, k),
        "recovery": rng.uniform(0.3, 1.0, k),
    }


REGISTRY = {"block_economic_value": _bv_args, "breakeven_cutoff_grade": _be_args}
FREE = {"block_economic_value": "tonnage", "breakeven_cutoff_grade": "processing_cost"}
INT_CAPABLE = {"block_economic_value": ("tonnage",), "breakeven_cutoff_grade": ()}
NAMES = list(REGISTRY)


def _outputs(name: str, args: dict[str, Any]) -> tuple[Any, ...]:
    out = getattr(_p(), name)(**args)
    return (out.value, out.processed) if name == "block_economic_value" else (out,)


def _args(name: str, seed: int, k: int) -> dict[str, np.ndarray]:
    return REGISTRY[name](np.random.default_rng(seed), k)


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
    shape = next(iter(args.values())).shape
    outs = _outputs(name, args)
    for part, out in enumerate(outs):
        assert isinstance(out, np.ndarray) and out.shape == shape
        flat = {a: v.ravel() for a, v in args.items()}
        for i in range(out.size):
            one = _outputs(name, {a: float(v[i]) for a, v in flat.items()})[part]
            if out.dtype == np.bool_:
                assert bool(one) == bool(out.ravel()[i])
            else:
                assert out.dtype == np.float64 and isinstance(one, np.float64)
                scale = float(np.max(np.abs(out)))
                np.testing.assert_allclose(out.ravel()[i], one, rtol=1e-14, atol=1e-14 * scale)


@pytest.mark.req("P-000-01")
@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(2, 12))
def test_p_000_01_scalar_arguments_broadcast_against_arrays(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    arg = FREE[name]
    value = float(args[arg][0])
    mixed = dict(args, **{arg: value})
    ref = dict(args, **{arg: np.full(k, value)})
    for g, w in zip(_outputs(name, mixed), _outputs(name, ref), strict=True):
        assert isinstance(g, np.ndarray) and g.shape == (k,)
        np.testing.assert_array_equal(g, w) if g.dtype == np.bool_ else np.testing.assert_allclose(g, w, rtol=1e-14, atol=0)


@pytest.mark.req("P-000-02")
@pytest.mark.req("FR-000-05")
@pytest.mark.parametrize("name", NAMES)
@CI
@given(seed=SEEDS, k=st.integers(1, 16))
def test_p_000_02_elementwise_functions_are_pure(name: str, seed: int, k: int) -> None:
    args = _args(name, seed, k)
    before = {a: v.copy() for a, v in args.items()}
    first, second = _outputs(name, args), _outputs(name, args)
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
    for x, y in zip(_outputs(name, a32), _outputs(name, a64), strict=True):
        assert x.tobytes() == y.tobytes()


@pytest.mark.req("P-000-03")
@CI
@given(seed=SEEDS, k=st.integers(1, 16))
def test_p_000_03_integer_tonnage_equals_its_float64_cast(seed: int, k: int) -> None:
    args = _args("block_economic_value", seed, k)
    ints = dict(args, tonnage=np.round(args["tonnage"]).astype(np.int64))
    floats = dict(ints, tonnage=ints["tonnage"].astype(np.float64))
    for x, y in zip(_outputs("block_economic_value", ints), _outputs("block_economic_value", floats), strict=True):
        assert x.tobytes() == y.tobytes()


@pytest.mark.req("FR-000-13")
@pytest.mark.req("FR-000-07")
@pytest.mark.parametrize("name", NAMES)
def test_fr_000_13_empty_arrays_give_empty_arrays(name: str) -> None:
    args = {a: np.empty(0) for a in _args(name, 0, 1)}
    for out in _outputs(name, args):
        assert isinstance(out, np.ndarray) and out.shape == (0,)
    assert _outputs(name, args)[0].dtype == np.float64


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.req("FR-000-12")
@pytest.mark.parametrize("name", NAMES)
def test_fr_000_10_11_12_hostile_arguments_name_the_argument(name: str) -> None:
    importlib.import_module("minephys.planning")
    import minephys

    base = {a: float(v[0]) for a, v in _args(name, 5, 1).items()}
    for arg in base:
        for bad in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(minephys.InputError) as exc:
                _outputs(name, dict(base, **{arg: bad}))
            assert exc.value.argument == arg
        with pytest.raises(minephys.InputTypeError) as exc2:
            _outputs(name, dict(base, **{arg: "text"}))
        assert exc2.value.argument == arg
    first, second = ("tonnage", "grade") if name == "block_economic_value" else ("processing_cost", "recovery")
    with pytest.raises(minephys.InputError) as exc3:
        _outputs(name, dict(base, **{first: np.full(3, base[first]), second: np.full(2, base[second])}))
    assert first in str(exc3.value) and second in str(exc3.value)


@pytest.mark.req("P-000-02")
@pytest.mark.req("FR-000-05")
@pytest.mark.oracle("hand-calculation", "purity: identical results and unmodified inputs for every aggregate function")
def test_fr_000_05_every_other_function_is_pure() -> None:
    p = _p()
    arcs = np.array([[3, 0], [3, 1], [3, 2]], dtype=np.int64)
    values = np.array([-1.0, -1.0, -1.0, 5.0])
    cases = {
        "ultimate_pit_mincut": (values, arcs),
        "strip_ratio": (np.array([True, True, False, True]), np.array([1.0, 2.0, 3.0, 4.0]), np.array([False, True, False, True])),
        "npv": (np.array([-5.0, 3.0, 4.0]), 0.1),
        "schedule_npv": (np.array([0, 1, -1, 1]), np.array([5.0, 6.0, 7.0, 8.0]), 0.1),
        "regular_grid_precedence": ((3, 3, 2), "1-5"),
    }
    def parts(result: Any) -> list[np.ndarray]:
        return [np.asarray(x) for x in result] if hasattr(result, "_fields") else [np.asarray(result)]

    for name, args in cases.items():
        copies = [a.copy() if isinstance(a, np.ndarray) else a for a in args]
        r1, r2 = getattr(p, name)(*args), getattr(p, name)(*args)
        for x, y in zip(parts(r1), parts(r2), strict=True):
            assert x.tobytes() == y.tobytes(), name
        for a, c in zip(args, copies, strict=True):
            if isinstance(a, np.ndarray):
                assert np.array_equal(a, c), name