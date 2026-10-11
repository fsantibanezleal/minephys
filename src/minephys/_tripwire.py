"""Unit tripwires (spec 000 FR-000-16): warn when an input is outside a limit read from a `limit` knowledge row.

A tripwire fires strictly outside its limit, for scalars and for any element of an array, names the argument and the
row id in a `ValidityWarning`, and never stops the computation.
"""

from __future__ import annotations

import math

from . import knowledge
from ._validate import FloatArray, warn_validity

__all__: list[str] = []


def limit(row: str) -> float:
    """The value of a tripwire row (role `limit`: reading it never warns about verification)."""
    return float(knowledge.get_value(row))  # type: ignore[arg-type]


def warn_abs_max(arr: FloatArray, name: str, row: str) -> None:
    """Warn when |arr| exceeds the limit of `row`."""
    bound = limit(row)
    warn_validity(arr, name, -bound, bound, row, stacklevel=4)


def warn_max(arr: FloatArray, name: str, row: str) -> None:
    """Warn when `arr` exceeds the limit of `row`."""
    warn_validity(arr, name, -math.inf, limit(row), row, stacklevel=4)


def warn_min(arr: FloatArray, name: str, row: str) -> None:
    """Warn when `arr` lies below the limit of `row`."""
    warn_validity(arr, name, limit(row), math.inf, row, stacklevel=4)
