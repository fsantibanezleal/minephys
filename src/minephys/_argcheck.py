"""Shared argument checks of the model modules (comminution, environment): finite, domain, flag, count, size."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from . import knowledge
from ._errors import InputError
from ._validate import as_float_array, check_bool, check_domain, check_finite, check_rank

FloatArray = npt.NDArray[np.float64]


def row(row_id: str) -> float:
    """The value of a knowledge row, read at call time so that a replaced row changes the result."""
    return float(knowledge.get_value(row_id))  # type: ignore[arg-type]


def positive(value: Any, name: str) -> FloatArray:
    """A finite real number or array, strictly greater than zero."""
    return check_domain(check_finite(as_float_array(value, name), name), name, lo=0, lo_open=True)


def non_negative(value: Any, name: str) -> FloatArray:
    """A finite real number or array, zero or greater."""
    return check_domain(check_finite(as_float_array(value, name), name), name, lo=0)


def unit_interval(value: Any, name: str, *, lo_open: bool = False) -> FloatArray:
    """A finite real number or array in [0, 1] (or (0, 1] with `lo_open`)."""
    return check_domain(check_finite(as_float_array(value, name), name), name, lo=0, hi=1, lo_open=lo_open)


def flag(value: Any, name: str) -> bool:
    """A boolean flag (Python or NumPy bool); anything else is an InputTypeError."""
    checked = check_bool(value, name)
    if np.ndim(checked) != 0:
        raise InputError(f"argument '{name}' must be a single boolean, got shape {np.shape(checked)}", argument=name)
    return bool(checked)


def finer_than(product: FloatArray, feed: FloatArray, product_name: str, feed_name: str) -> None:
    """Raise InputError unless every product size is strictly finer than the feed size."""
    bad = ~(product < feed)
    if bad.any():
        k = int(np.argmax(bad.ravel()))
        raise InputError(
            f"argument '{product_name}' must be finer than '{feed_name}', got {float(np.ravel(product)[k])!r} "
            f"against {float(np.ravel(feed)[k])!r}",
            argument=product_name,
        )


def vector(value: Any, name: str, *, min_size: int = 1, max_size: int | None = None) -> FloatArray:
    """A finite 1-D float array with a size window (InputError names the argument, the size and the bound)."""
    arr = check_finite(as_float_array(value, name), name)
    check_rank(arr, name, 1)
    if arr.size < min_size:
        raise InputError(f"argument '{name}' needs at least {min_size} elements, got {arr.size}", argument=name)
    if max_size is not None and arr.size > max_size:
        raise InputError(f"argument '{name}' allows at most {max_size} elements, got {arr.size}", argument=name)
    return arr


def scalar(value: Any, name: str, *, lo: float | None = None, lo_open: bool = False, hi: float | None = None) -> float:
    """A finite real scalar with an optional lower and upper bound."""
    arr = check_domain(check_finite(as_float_array(value, name), name), name, lo=lo, hi=hi, lo_open=lo_open)
    if arr.ndim != 0:
        raise InputError(f"argument '{name}' must be a scalar, got shape {tuple(arr.shape)}", argument=name)
    return float(arr)


def count(value: Any, name: str, *, minimum: int = 1) -> int:
    """An integer count of at least `minimum` (Python or NumPy integers, or integral floats)."""
    arr = check_finite(as_float_array(value, name), name)
    if arr.ndim != 0 or arr != np.floor(arr) or arr < minimum:
        raise InputError(f"argument '{name}' must be an integer >= {minimum}, got {value!r}", argument=name)
    return int(arr)
