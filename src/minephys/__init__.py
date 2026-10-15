"""minephys: sourced, tested reference implementations of mining-engineering models.

The package exports the error classes (spec 000 FR-000-32), `__version__` and the public subpackages; subpackages are
imported on first access so that `import minephys` stays cheap and reads no data file (FR-000-06).
"""

from __future__ import annotations

import importlib
import importlib.metadata
from typing import Any

from ._errors import ConvergenceError, InputError, InputTypeError, ValidityWarning

__all__ = [
    "ConvergenceError",
    "InputError",
    "InputTypeError",
    "ValidityWarning",
    "__version__",
    "blasting",
    "bulk",
    "comminution",
    "environment",
    "geotech",
    "haulage",
    "knowledge",
    "planning",
    "units",
]


def _display_version() -> str:
    """The distribution version in the display form X.YY.ZZZ (the metadata carries the normalised X.Y.Z)."""
    try:
        x, y, z = (int(p) for p in importlib.metadata.version("minephys").split(".")[:3])
    except importlib.metadata.PackageNotFoundError:  # a source tree without installed metadata
        return "0.00.000"
    return f"{x}.{y:02d}.{z:03d}"


__version__: str = _display_version()


def __getattr__(name: str) -> Any:
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
