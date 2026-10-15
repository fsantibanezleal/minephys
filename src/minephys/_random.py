"""Random-source helper (spec 000 FR-000-18): a seed or a Generator, never a default, never global state."""

from __future__ import annotations

from typing import Any

import numpy as np

from ._errors import InputError, InputTypeError

__all__ = ["as_generator"]

_MAX_SEED = 2**32 - 1


def as_generator(rng: Any) -> np.random.Generator:
    """Return `rng` when it is a Generator, else `numpy.random.default_rng(rng)` for a seed in [0, 2**32 - 1]."""
    if isinstance(rng, np.random.Generator):
        return rng
    if isinstance(rng, bool | np.bool_) or not isinstance(rng, int | np.integer):
        raise InputTypeError(
            f"argument 'rng' must be a numpy.random.Generator or an integer seed, got {type(rng).__name__}",
            argument="rng",
        )
    seed = int(rng)
    if not 0 <= seed <= _MAX_SEED:
        raise InputError(f"argument 'rng' seed must lie in [0, {_MAX_SEED}], got {seed}", argument="rng")
    return np.random.default_rng(seed)
