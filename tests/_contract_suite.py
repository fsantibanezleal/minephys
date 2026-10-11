"""Shared contract suite of the foundation (T-000-010; spec 000 FR-000-05, FR-000-07, FR-000-10 to FR-000-12, FR-000-18,
P-000-01 to P-000-04).

Every module spec runs these checks on its own functions. Each check raises `AssertionError` when the function under
test violates the property and returns `None` otherwise. `kwargs` maps argument names to values: `numpy.ndarray`
values are the broadcastable operands, every other value (bool, str, None, int options, NumPy scalars) is passed
through unchanged. Nothing here is an oracle for a model value.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

__all__ = [
    "check_dtype_invariance",
    "check_elementwise",
    "check_hostile",
    "check_purity",
    "check_seeded",
    "check_shape_hostile",
]

Fn = Callable[..., Any]

_SEEDS = (20261011, 20261012)


def _fingerprint(value: Any) -> Any:
    """Type, dtype, shape and bytes of a result, recursively for tuples, lists and named results."""
    if isinstance(value, np.ndarray):
        return ("ndarray", str(value.dtype), value.shape, value.tobytes())
    if isinstance(value, np.generic):
        return (type(value).__name__, str(value.dtype), value.tobytes())
    if isinstance(value, tuple | list):
        return (type(value).__name__, tuple(_fingerprint(v) for v in value))
    if hasattr(value, "__dataclass_fields__"):
        return (type(value).__name__, tuple((f, _fingerprint(getattr(value, f))) for f in value.__dataclass_fields__))
    return (type(value).__name__, repr(value))


def _components(value: Any) -> list[Any]:
    if isinstance(value, tuple | list):
        return [c for v in value for c in _components(v)]
    return [value]


def check_purity(fn: Fn, kwargs: dict[str, Any]) -> None:
    """P-000-02, FR-000-05: two calls are bitwise identical and no ndarray argument is modified."""
    before = {k: v.copy() for k, v in kwargs.items() if isinstance(v, np.ndarray)}
    first = fn(**kwargs)
    second = fn(**kwargs)
    for name, original in before.items():
        assert kwargs[name].dtype == original.dtype, f"{name}: dtype changed"
        assert kwargs[name].tobytes() == original.tobytes(), f"argument {name} was modified in place"
    assert _fingerprint(first) == _fingerprint(second), "two calls with identical arguments differ"


def _operand_shape(kwargs: dict[str, Any]) -> tuple[int, ...]:
    shapes = [np.shape(v) for v in kwargs.values() if isinstance(v, np.ndarray)]
    return np.broadcast_shapes(*shapes) if shapes else ()


def check_elementwise(fn: Fn, kwargs: dict[str, Any]) -> None:
    """P-000-01, FR-000-07: array evaluation equals scalar evaluation at each index; result types are fixed."""
    shape = _operand_shape(kwargs)
    out = fn(**kwargs)
    scalar_inputs = all(np.ndim(v) == 0 for v in kwargs.values() if isinstance(v, np.ndarray | np.generic | float))
    for part in _components(out):
        if scalar_inputs:
            assert type(part) is np.float64, f"all-scalar inputs must give numpy.float64, got {type(part).__name__}"
        else:
            assert isinstance(part, np.ndarray), f"array inputs must give an ndarray, got {type(part).__name__}"
            assert part.dtype == np.float64, f"result dtype {part.dtype} is not float64"
            assert part.shape == shape, f"result shape {part.shape} is not the broadcast shape {shape}"
    if not shape or int(np.prod(shape)) == 0:
        return
    arrays = {k: np.broadcast_to(v, shape) for k, v in kwargs.items() if isinstance(v, np.ndarray)}
    parts = _components(out)
    for index in np.ndindex(*shape):
        scalar_kwargs = {k: (np.float64(arrays[k][index]) if k in arrays else v) for k, v in kwargs.items()}
        expected = _components(fn(**scalar_kwargs))
        assert len(expected) == len(parts), "the number of result components depends on the operand shape"
        for got, want in zip(parts, expected, strict=True):
            scale = float(np.max(np.abs(got))) if got.size else 0.0
            np.testing.assert_allclose(
                got[index],
                want,
                rtol=1e-14,
                atol=1e-14 * scale,
                err_msg=f"array result differs from the scalar result at index {index}",
            )


def _float32_exact(arr: np.ndarray) -> bool:
    return bool(np.all(np.isfinite(arr)) and np.array_equal(arr.astype(np.float32).astype(np.float64), arr))


def _int32_exact(arr: np.ndarray) -> bool:
    negative_zero = bool(np.any(np.signbit(arr) & (arr == 0)))  # an integer cannot carry the sign of zero
    return bool(
        np.all(np.isfinite(arr))
        and np.all(np.abs(arr) < 2**31)
        and np.array_equal(arr, np.trunc(arr))
        and arr.size > 0
        and not negative_zero
    )


def check_dtype_invariance(fn: Fn, kwargs: dict[str, Any]) -> None:
    """P-000-03: float32 and int32 operands give bitwise the result of the float64 operands."""
    reference = _fingerprint(fn(**kwargs))
    variants: dict[str, dict[str, Any]] = {"float32": {}, "int32": {}}
    for name, value in kwargs.items():
        if isinstance(value, np.ndarray) and value.dtype == np.float64:
            if _float32_exact(value):
                variants["float32"][name] = value.astype(np.float32)
            if _int32_exact(value):
                variants["int32"][name] = value.astype(np.int32)
        elif isinstance(value, np.float64) and _float32_exact(np.asarray(value)):
            variants["float32"][name] = np.float32(value)
    for label, changes in variants.items():
        if not changes:
            continue
        got = _fingerprint(fn(**{**kwargs, **changes}))
        assert got == reference, f"{label} operands {sorted(changes)} give a different result than float64 operands"


def check_seeded(fn: Fn, kwargs: dict[str, Any], rng_name: str = "rng") -> None:
    """P-000-04, FR-000-18: same seed (or default_rng(seed)) gives identical output; different seeds differ."""
    seed, other = _SEEDS
    a = fn(**{**kwargs, rng_name: seed})
    b = fn(**{**kwargs, rng_name: seed})
    c = fn(**{**kwargs, rng_name: np.random.default_rng(seed)})
    assert _fingerprint(a) == _fingerprint(b), "the same integer seed gives different output"
    assert _fingerprint(a) == _fingerprint(c), "default_rng(seed) differs from the integer seed"
    d = fn(**{**kwargs, rng_name: other})
    assert _fingerprint(a) != _fingerprint(d), "two different seeds give identical output"


def _expect(fn: Fn, kwargs: dict[str, Any], argument: str, error: type[Exception], what: str) -> Exception:
    try:
        fn(**kwargs)
    except error as err:
        assert getattr(err, "argument", None) == argument, f"{what}: argument attribute is {err.argument!r}"
        return err
    except Exception as err:
        raise AssertionError(f"{what}: raised {type(err).__name__} instead of {error.__name__}: {err}") from err
    raise AssertionError(f"{what}: no {error.__name__} raised")


_BAD_TYPES: tuple[Any, ...] = (
    "1.0",
    b"1",
    None,
    1 + 2j,
    True,
    object(),
    np.datetime64("2026-10-11"),
    np.timedelta64(5, "s"),
)


def check_hostile(
    fn: Fn, kwargs: dict[str, Any], argument: str, *, allow_posinf: bool = False, boolean: bool = False
) -> None:
    """FR-000-10, FR-000-11: hostile values of one argument raise the stated error naming it."""
    base = kwargs[argument]
    if boolean:
        for bad in (0, 1, 1.0, "yes"):
            _expect(fn, {**kwargs, argument: bad}, argument, _types(), f"{argument}={bad!r} for a flag")
        return
    others_are_arrays = any(isinstance(v, np.ndarray) for k, v in kwargs.items() if k != argument)
    bad_values = [np.nan, -np.inf] + ([] if allow_posinf else [np.inf])
    for bad in bad_values:
        _expect(fn, {**kwargs, argument: bad}, argument, _input(), f"{argument}={bad}")
        if isinstance(base, np.ndarray) and base.size:
            arr = np.array(base, dtype=np.float64, copy=True)
            arr.flat[arr.size - 1] = bad
            err = _expect(fn, {**kwargs, argument: arr}, argument, _input(), f"{argument}[-1]={bad}")
            assert str(arr.size - 1) in str(err), f"the message does not carry the flat index {arr.size - 1}: {err}"
        else:
            arr = np.array([bad]) if others_are_arrays else np.array([float(base), bad])
            err = _expect(fn, {**kwargs, argument: arr}, argument, _input(), f"{argument} array with {bad}")
            assert str(arr.size - 1) in str(err), f"the message does not carry the flat index: {err}"
    if allow_posinf:
        fn(**{**kwargs, argument: np.inf})
    for bad in _BAD_TYPES:
        _expect(fn, {**kwargs, argument: bad}, argument, _types(), f"{argument}={bad!r}")
    shape = base.shape if isinstance(base, np.ndarray) else (1,)
    typed_arrays = (
        np.ones(shape, dtype=bool),
        np.ones(shape, dtype=complex),
        np.full(shape, "a"),
        np.full(shape, None, dtype=object),
        np.full(shape, np.datetime64("2026-10-11")),
    )
    for arr in typed_arrays:
        _expect(fn, {**kwargs, argument: arr}, argument, _types(), f"{argument} array of dtype {arr.dtype}")


def _input() -> type[Exception]:
    from minephys import InputError

    return InputError


def _types() -> type[Exception]:
    from minephys import InputTypeError

    return InputTypeError


def check_shape_hostile(fn: Fn, kwargs: dict[str, Any], first: str, second: str) -> None:
    """FR-000-12: operands of shapes (3,) and (4,) cannot broadcast; the error names both arguments and shapes."""
    bad = {**kwargs, first: np.ones(3), second: np.ones(4)}
    try:
        fn(**bad)
    except _input() as err:
        message = str(err)
        for token in (first, second, "(3,)", "(4,)"):
            assert token in message, f"the message does not name {token!r}: {message}"
        return
    except Exception as err:
        raise AssertionError(f"raised {type(err).__name__} instead of InputError: {err}") from err
    raise AssertionError("arguments of shapes (3,) and (4,) were accepted")
