"""Solver helpers with an honest failure mode (spec 000 FR-000-17): never an unconverged value."""

from __future__ import annotations

import math
from collections.abc import Callable

from ._errors import ConvergenceError, InputError

__all__ = ["bracketed_root", "fixed_point"]

_EPS = 2.0**-52
_TINY = 1e-300


def _check_controls(rtol: float, max_iter: int) -> None:
    if not (isinstance(rtol, int | float) and math.isfinite(rtol) and rtol > 0):
        raise InputError(f"argument 'rtol' must be a positive finite number, got {rtol!r}", argument="rtol")
    if not (isinstance(max_iter, int) and not isinstance(max_iter, bool) and max_iter >= 1):
        raise InputError(f"argument 'max_iter' must be an integer >= 1, got {max_iter!r}", argument="max_iter")


def bracketed_root(
    f: Callable[[float], float], lo: float, hi: float, *, rtol: float = 1e-12, max_iter: int = 200
) -> float:
    """Root of the scalar function `f` in the sign-changing bracket [lo, hi] (Brent's method).

    Raises InputError when the bracket is not finite or does not change sign and ConvergenceError when the
    relative step or bracket width does not reach `rtol` within `max_iter` iterations.
    """
    _check_controls(rtol, max_iter)
    for label, end in (("lo", lo), ("hi", hi)):
        if not math.isfinite(end):
            raise InputError(f"argument '{label}' must be finite, got {end!r}", argument=label)
    a, b = float(lo), float(hi)
    fa, fb = float(f(a)), float(f(b))
    if fa == 0:
        return a
    if fb == 0:
        return b
    if (fa > 0) == (fb > 0):
        raise InputError(
            f"the bracket [{lo!r}, {hi!r}] does not change sign (f(lo)={fa!r}, f(hi)={fb!r})", argument="bracket"
        )
    c, fc = a, fa
    d = e = b - a
    for k in range(1, max_iter + 1):
        if (fb > 0) == (fc > 0):
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb
        tol = 2 * _EPS * abs(b) + rtol * abs(b) / 2 + _TINY
        xm = (c - b) / 2
        if abs(xm) <= tol or fb == 0:
            return b
        if abs(e) >= tol and abs(fa) > abs(fb):
            s = fb / fa
            if a == c:
                p, q = 2 * xm * s, 1 - s
            else:
                q = fa / fc
                r = fb / fc
                p = s * (2 * xm * q * (q - r) - (b - a) * (r - 1))
                q = (q - 1) * (r - 1) * (s - 1)
            if p > 0:
                q = -q
            p = abs(p)
            if 2 * p < min(3 * xm * q - abs(tol * q), abs(e * q)):
                e, d = d, p / q
            else:
                d = e = xm
        else:
            d = e = xm
        a, fa = b, fb
        b += d if abs(d) > tol else math.copysign(tol, xm)
        fb = float(f(b))
        if not math.isfinite(fb):
            raise ConvergenceError(
                f"the function is not finite at {b!r}", last_iterate=b, residual=abs(fb), iterations=k
            )
    raise ConvergenceError(
        f"no convergence to rtol={rtol!r} in {max_iter} iterations",
        last_iterate=b,
        residual=abs(fb),
        iterations=max_iter,
    )


def fixed_point(g: Callable[[float], float], x0: float, *, rtol: float = 1e-12, max_iter: int = 200) -> float:
    """Iterate x <- g(x) from `x0` until |g(x) - x| <= rtol * max(|x|, 1) (the iterate x_k is returned)."""
    _check_controls(rtol, max_iter)
    if not math.isfinite(x0):
        raise InputError(f"argument 'x0' must be finite, got {x0!r}", argument="x0")
    x = float(x0)
    for k in range(1, max_iter + 1):
        try:
            nxt = float(g(x))
        except (OverflowError, FloatingPointError):
            nxt = math.inf
        if not math.isfinite(nxt):
            raise ConvergenceError(
                f"the iteration left the finite numbers after {k} applications",
                last_iterate=x,
                residual=math.inf,
                iterations=k,
            )
        step = abs(nxt - x)
        scale = max(abs(x), 1)
        x = nxt
        if step <= rtol * scale:
            return x
    try:
        residual = abs(float(g(x)) - x)
    except (OverflowError, FloatingPointError):
        residual = math.inf
    raise ConvergenceError(
        f"no convergence to rtol={rtol!r} in {max_iter} iterations",
        last_iterate=x,
        residual=residual,
        iterations=max_iter,
    )
