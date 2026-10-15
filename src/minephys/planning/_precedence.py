"""Precedence arcs of a regular block grid and the validation of arc arrays (spec 007 FR-007-03, FR-007-07)."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from .._errors import InputError, InputTypeError
from .._validate import check_option

MAX_BLOCKS = 100_000
MAX_ARCS = 2_000_000

__all__ = ["check_arcs", "regular_grid_precedence"]

_OFFSETS = {
    "1-5": ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)),
    "1-9": tuple((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)),
}


def check_arcs(arcs: Any, n: int) -> npt.NDArray[np.int64]:
    """Validate an (m, 2) integer arc array against n blocks and return it as int64 (a view when it already is)."""
    arr = np.asarray(arcs)
    if arr.dtype.kind not in "iu":
        raise InputTypeError(f"argument 'arcs' must be an integer array, got dtype {arr.dtype}", argument="arcs")
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise InputError(f"argument 'arcs' must have shape (m, 2), got {tuple(arr.shape)}", argument="arcs")
    if arr.shape[0] > MAX_ARCS:
        raise InputError(f"argument 'arcs' allows at most {MAX_ARCS:,} arcs, got {arr.shape[0]:,}", argument="arcs")
    if arr.size:
        low, high = int(arr.min()), int(arr.max())
        if low < 0 or high >= n:
            raise InputError(
                f"argument 'arcs' holds a block index outside [0, {n - 1}]: {low if low < 0 else high}", argument="arcs"
            )
        same = arr[:, 0] == arr[:, 1]
        if same.any():
            k = int(np.argmax(same))
            raise InputError(f"argument 'arcs' holds a self-arc at row {k}: block {int(arr[k, 0])}", argument="arcs")
    return arr.astype(np.int64, copy=False)


def regular_grid_precedence(shape: Any, pattern: str = "1-5") -> npt.NDArray[np.int64]:
    """Precedence arcs of an (nx, ny, nz) block grid in C order with level 0 at the top.

    Parameters
    ----------
    shape : tuple of int [blocks]
        Grid dimensions (nx, ny, nz), each >= 1, with nx ny nz <= 100,000.
    pattern : str [option]
        "1-5" (the block above and its four side neighbours) or "1-9" (the nine blocks one level up).

    Returns
    -------
    array of int64 [block index pairs, shape (m, 2)]
        Arcs (i, j), "mining block i requires block j"; index = (x ny + y) nz + z. The row order is not specified.

    Equation
    --------
    Arc count (nz - 1) [nx ny + 2 (nx - 1) ny + 2 nx (ny - 1)] for "1-5" and (nz - 1)(3 nx - 2)(3 ny - 2) for "1-9".

    Source
    ------
    picard1976closure (definition of the closure the arcs feed); the slope rule is a derived hand calculation, spec 007
    section 7.

    Validity
    --------
    At most 100,000 blocks and 2,000,000 arcs. "1-5" approximates a 45 degree wall on cubic blocks; domain-specific
    slope
    angles are the caller's arcs.

    Knowledge rows
    --------------
    none
    """
    try:
        dims = tuple(shape)
    except TypeError:
        raise InputTypeError("argument 'shape' must be a sequence of three integers", argument="shape") from None
    if len(dims) != 3:
        raise InputError(f"argument 'shape' must have three entries, got {len(dims)}", argument="shape")
    for d in dims:
        if isinstance(d, bool | np.bool_) or not isinstance(d, int | np.integer):
            raise InputTypeError(f"argument 'shape' must hold integers, got {d!r}", argument="shape")
    nx, ny, nz = (int(d) for d in dims)
    if min(nx, ny, nz) < 1:
        raise InputError(f"argument 'shape' must be positive in every dimension, got {(nx, ny, nz)}", argument="shape")
    if nx * ny * nz > MAX_BLOCKS:
        raise InputError(
            f"argument 'shape' allows at most {MAX_BLOCKS:,} blocks, got {nx * ny * nz:,}", argument="shape"
        )
    check_option(pattern, "pattern", tuple(_OFFSETS))
    if nz == 1:
        return np.empty((0, 2), dtype=np.int64)
    x = np.arange(nx, dtype=np.int64)[:, None]
    y = np.arange(ny, dtype=np.int64)[None, :]
    z = np.arange(1, nz, dtype=np.int64)
    parts = []
    for dx, dy in _OFFSETS[pattern]:
        ok = (x + dx >= 0) & (x + dx < nx) & (y + dy >= 0) & (y + dy < ny)
        xs, ys = np.nonzero(ok)
        base_i = (xs * ny + ys) * nz
        base_j = ((xs + dx) * ny + (ys + dy)) * nz
        i = (base_i[:, None] + z[None, :]).ravel()
        j = (base_j[:, None] + (z - 1)[None, :]).ravel()
        parts.append(np.stack([i, j], axis=1))
    return np.concatenate(parts, axis=0).astype(np.int64, copy=False)
