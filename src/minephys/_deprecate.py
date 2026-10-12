"""Deprecation helper (spec 000 FR-000-29): one DeprecationWarning per call site, naming replacement and removal."""

from __future__ import annotations

import functools
import re
import warnings
from collections.abc import Callable
from typing import Any, TypeVar

from ._errors import InputError

__all__ = ["deprecated", "warn_deprecated_parameter"]

_F = TypeVar("_F", bound=Callable[..., Any])
_VERSION = re.compile(r"^(\d+)\.(\d{2})\.(\d{3})$")


def _parse(value: str, argument: str) -> tuple[int, int, int]:
    match = _VERSION.match(value) if isinstance(value, str) else None
    if match is None:
        raise InputError(f"argument '{argument}' must be an X.YY.ZZZ version, got {value!r}", argument=argument)
    x, y, z = match.groups()
    return int(x), int(y), int(z)


def deprecated(*, since: str, removal: str, replacement: str) -> Callable[[_F], _F]:
    """Decorator: calls warn once per call site and the wrapper records `__minephys_deprecated__`."""
    if _parse(removal, "removal") <= _parse(since, "since"):
        raise InputError(f"argument 'removal' ({removal}) must be later than 'since' ({since})", argument="removal")
    info = {"since": since, "removal": removal, "replacement": replacement}

    def decorate(function: _F) -> _F:
        message = (
            f"{function.__name__}() is deprecated since {since} and will be removed in {removal}; "
            f"use {replacement}"
        )

        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return function(*args, **kwargs)

        wrapper.__minephys_deprecated__ = info  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorate


def warn_deprecated_parameter(function: str, parameter: str, *, since: str, removal: str, replacement: str) -> None:
    """Warn that `parameter` (or its default) of `function` is deprecated, attributed to the caller of `function`."""
    warnings.warn(
        f"parameter '{parameter}' of {function}() is deprecated since {since} and will be removed in {removal}; "
        f"use {replacement}",
        DeprecationWarning,
        stacklevel=3,
    )
