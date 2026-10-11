"""Exceptions and the validity warning of the library (spec 000 FR-000-32, data model section 4)."""

from __future__ import annotations

__all__ = ["ConvergenceError", "InputError", "InputTypeError", "ValidityWarning"]


class InputError(ValueError):
    """A value, shape, size, domain or option error in an argument; `argument` names the argument."""

    def __init__(self, message: str, *, argument: str) -> None:
        super().__init__(message)
        self.argument = argument


class InputTypeError(TypeError):
    """An argument that is not real-numeric (or not boolean where a flag is required)."""

    def __init__(self, message: str, *, argument: str) -> None:
        super().__init__(message)
        self.argument = argument


class ValidityWarning(UserWarning):
    """An input outside the validity range of the source of a model, or a unit tripwire."""

    def __init__(self, message: str, *, argument: str, bounds: tuple[float, float], row: str) -> None:
        super().__init__(message)
        self.argument = argument
        self.bounds = bounds
        self.row = row


class ConvergenceError(RuntimeError):
    """An iterative solver that did not meet its tolerance within its iteration cap."""

    def __init__(self, message: str, *, last_iterate: float, residual: float, iterations: int) -> None:
        super().__init__(message)
        self.argument = None
        self.last_iterate = last_iterate
        self.residual = residual
        self.iterations = iterations
