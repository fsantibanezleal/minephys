"""Input-validation helpers (spec 000 FR-000-07, FR-000-10 to FR-000-16).

Validation runs once per call at the function boundary; model code then receives float64 arrays that are finite and
in-domain. Every message names the argument; array messages carry the flat index of the first offending element.
"""

from __future__ import annotations

import numbers
import warnings
from collections.abc import Iterable
from typing import Any

import numpy as np
import numpy.typing as npt

from ._errors import InputError, InputTypeError, ValidityWarning

FloatArray = npt.NDArray[np.float64]

__all__ = [
    "as_float_array",
    "broadcast_all",
    "check_bool",
    "check_domain",
    "check_finite",
    "check_option",
    "check_rank",
    "check_size",
    "finalize",
    "warn_validity",
]

_REAL_KINDS = "iuf"


def _type_error(name: str, value: object) -> InputTypeError:
    return InputTypeError(
        f"argument '{name}' must be a real number or an array of real numbers, got {type(value).__name__}",
        argument=name,
    )


def as_float_array(value: Any, name: str) -> FloatArray:
    """Convert a real scalar or array to float64 (0-d for a scalar); anything else is an InputTypeError."""
    if isinstance(value, bool | np.bool_ | str | bytes | complex | np.complexfloating) or value is None:
        raise _type_error(name, value)
    if isinstance(value, np.ndarray | np.generic):
        arr = np.asarray(value)
        if arr.dtype.kind not in _REAL_KINDS:
            raise _type_error(name, value)
        return np.asarray(arr, dtype=np.float64)
    if isinstance(value, numbers.Real):
        try:
            return np.asarray(float(value), dtype=np.float64)
        except OverflowError:
            raise InputError(f"argument '{name}' is too large to be a float64 number", argument=name) from None
    if isinstance(value, list | tuple):
        try:
            arr = np.asarray(value)
        except (ValueError, TypeError):
            raise _type_error(name, value) from None
        if arr.dtype.kind not in _REAL_KINDS:
            raise _type_error(name, value)
        return np.asarray(arr, dtype=np.float64)
    raise _type_error(name, value)


def _first(mask: npt.NDArray[np.bool_]) -> int:
    return int(np.argmax(mask.ravel()))


def check_finite(arr: FloatArray, name: str, *, allow_posinf: bool = False) -> FloatArray:
    """Raise InputError for NaN, -inf and (unless allowed) +inf; arrays report the first flat index."""
    ok = np.isfinite(arr)
    if allow_posinf:
        ok = ok | (arr == np.inf)
    if ok.all():
        return arr
    idx = _first(~ok)
    value = float(arr.ravel()[idx])
    where = f" at flat index {idx}" if arr.ndim else ""
    allowed = "finite or +inf" if allow_posinf else "finite"
    raise InputError(f"argument '{name}' must be {allowed}, got {value!r}{where}", argument=name)


def _domain_error(arr: FloatArray, name: str, bad: npt.NDArray[np.bool_], rule: str) -> InputError:
    idx = _first(bad)
    value = float(arr.ravel()[idx])
    where = f" at flat index {idx}" if arr.ndim else ""
    return InputError(f"argument '{name}' must be {rule}, got {value!r}{where}", argument=name)


def check_domain(
    arr: FloatArray,
    name: str,
    *,
    lo: float | None = None,
    hi: float | None = None,
    lo_open: bool = False,
    hi_open: bool = False,
) -> FloatArray:
    """Raise InputError when an element violates the stated bound; the message names bound and value."""
    if lo is not None:
        low = (arr <= lo) if lo_open else (arr < lo)
        if low.any():
            raise _domain_error(arr, name, low, f"{'>' if lo_open else '>='} {lo!r}")
    if hi is not None:
        high = (arr >= hi) if hi_open else (arr > hi)
        if high.any():
            raise _domain_error(arr, name, high, f"{'<' if hi_open else '<='} {hi!r}")
    return arr


def check_option(value: Any, name: str, allowed: Iterable[str]) -> str:
    """Exact, case-sensitive match against the allowed strings; InputError lists the allowed values."""
    options = tuple(allowed)
    if type(value) is str and value in options:
        return value
    listed = ", ".join(repr(o) for o in options)
    raise InputError(f"argument '{name}' must be one of {listed}, got {value!r}", argument=name)


def check_bool(value: Any, name: str) -> Any:
    """A flag or mask must be a bool, a NumPy bool or a boolean array; anything else is an InputTypeError."""
    if isinstance(value, bool | np.bool_):
        return value
    if isinstance(value, np.ndarray) and value.dtype == np.bool_:
        return value
    raise InputTypeError(f"argument '{name}' must be boolean, got {type(value).__name__}", argument=name)


def check_rank(arr: FloatArray, name: str, ndim: int) -> FloatArray:
    """Raise InputError naming the shape when the array does not have the required rank."""
    if arr.ndim != ndim:
        raise InputError(
            f"argument '{name}' must be a {ndim}-D array, got shape {tuple(arr.shape)} ({arr.ndim}-D)", argument=name
        )
    return arr


def check_size(arr: FloatArray, name: str, *, min_size: int | None = None, max_size: int | None = None) -> FloatArray:
    """Aggregate size bounds: InputError names the received size and the violated bound."""
    size = int(arr.size)
    if min_size is not None and size < min_size:
        raise InputError(f"argument '{name}' needs at least {min_size} elements, got {size}", argument=name)
    if max_size is not None and size > max_size:
        raise InputError(f"argument '{name}' allows at most {max_size} elements, got {size}", argument=name)
    return arr


def broadcast_all(**named: FloatArray) -> tuple[FloatArray, ...]:
    """Broadcast the named arrays together (keyword order); InputError names the arguments and their shapes."""
    arrays = [np.asarray(a) for a in named.values()]
    try:
        out = np.broadcast_arrays(*arrays)
    except ValueError:
        shapes = ", ".join(f"{k} has shape {tuple(a.shape)}" for k, a in zip(named, arrays, strict=True))
        raise InputError(
            f"arguments {', '.join(named)} cannot be broadcast together: {shapes}", argument=", ".join(named)
        ) from None
    return tuple(out)


def finalize(result: Any, *inputs: Any) -> Any:
    """numpy.float64 when every input is 0-d, else a float64 ndarray of the broadcast shape."""
    res = np.asarray(result, dtype=np.float64)
    if res.ndim == 0 and all(np.ndim(i) == 0 for i in inputs):
        return np.float64(res[()])
    return res


def warn_validity(arr: FloatArray, name: str, lo: float, hi: float, row: str) -> None:
    """Emit ValidityWarning when any element lies outside [lo, hi]; execution continues."""
    if arr.size == 0:
        return
    outside = (arr < lo) | (arr > hi)
    if not outside.any():
        return
    low, high = float(arr[outside].min()), float(arr[outside].max())
    received = repr(low) if low == high else f"{low!r} to {high!r}"
    warnings.warn(
        ValidityWarning(
            f"argument '{name}' received {received}, outside the validity range [{lo!r}, {hi!r}] ({row})",
            argument=name,
            bounds=(lo, hi),
            row=row,
        ),
        stacklevel=3,
    )
