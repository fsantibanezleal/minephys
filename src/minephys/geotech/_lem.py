"""Limit equilibrium of circular slip surfaces on slice data: Bishop's simplified method and Spencer's method (spec 003
FR-003-09 to FR-003-11, FR-003-20 to FR-003-22)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import _tripwire as tw
from .._errors import ConvergenceError, InputError
from .._validate import (
    FloatArray,
    as_checked,
    as_count,
    as_float_array,
    as_scalar,
    check_finite,
    check_rank,
    check_size,
)

_MAX_SLICES = 10_000
_MAX_ITER = 10_000
_HALF_PI = math.pi / 2
_FD_STEP = 1e-6  # relative step of the finite-difference Jacobian of Spencer's Newton iteration
_BACKTRACKS = 40


def slice_arrays(
    width: Any,
    weight: Any,
    base_angle: Any,
    pore_pressure: Any,
    *,
    min_slices: int = 1,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Validated per-slice arrays (1-D, same length, min_slices to 10,000 slices, positive driving moment)."""
    arrays = {
        "width": as_float_array(width, "width"),
        "weight": as_float_array(weight, "weight"),
        "base_angle": as_float_array(base_angle, "base_angle"),
        "pore_pressure": as_float_array(pore_pressure, "pore_pressure"),
    }
    for name, arr in arrays.items():
        check_rank(arr, name, 1)
        check_finite(arr, name)
        check_size(arr, name, min_size=min_slices, max_size=_MAX_SLICES)
    sizes = {name: arr.size for name, arr in arrays.items()}
    if len(set(sizes.values())) != 1:
        raise InputError(
            "the per-slice arrays must have the same length, got "
            + ", ".join(f"{name} {size}" for name, size in sizes.items()),
            argument="width",
        )
    b = as_checked(arrays["width"], "width", lo=0, lo_open=True)
    w = as_checked(arrays["weight"], "weight", lo=0)
    alpha = as_checked(arrays["base_angle"], "base_angle", lo=-_HALF_PI, hi=_HALF_PI, lo_open=True, hi_open=True)
    u = as_checked(arrays["pore_pressure"], "pore_pressure", lo=0)
    if float(np.sum(w * np.sin(alpha))) <= 0:
        raise InputError("the driving moment sum(W sin(alpha)) must be positive", argument="base_angle")
    return b, w, alpha, u


def strengths(
    cohesion: Any, friction_angle: Any, size: int, *, cohesion_name: str = "cohesion", friction_name: str = "friction_angle"
) -> tuple[FloatArray, FloatArray]:
    """Per-slice cohesion and friction angle (scalars broadcast); emits the tripwires of section 7.3."""
    c = as_checked(cohesion, cohesion_name, lo=0)
    phi = as_checked(friction_angle, friction_name, lo=0, hi=_HALF_PI, hi_open=True)
    for name, arr in ((cohesion_name, c), (friction_name, phi)):
        if arr.ndim > 1:
            check_rank(arr, name, 1)
        if arr.ndim == 1 and arr.size != size:
            raise InputError(f"argument '{name}' has {arr.size} entries for {size} slices", argument=name)
    warn_strengths(c, phi, cohesion_name, friction_name)
    return np.broadcast_to(c, (size,)).astype(np.float64), np.broadcast_to(phi, (size,)).astype(np.float64)


def warn_strengths(c: FloatArray, phi: FloatArray, cohesion_name: str, friction_name: str) -> None:
    """Tripwires: 0 < cohesion < tripwire_cohesion_min (kPa passed as Pa) and friction above tripwire_friction_angle_max."""
    limit = tw.limit("tripwire_cohesion_min")
    tw.warn_min(np.where(c > 0, c, limit), cohesion_name, "tripwire_cohesion_min")
    tw.warn_max(phi, friction_name, "tripwire_friction_angle_max")


def iteration_controls(tol: Any, max_iter: Any) -> tuple[float, int]:
    t = as_scalar(as_checked(tol, "tol", lo=0, lo_open=True), "tol")
    n = int(as_scalar(as_count(max_iter, "max_iter", lo=1, hi=_MAX_ITER), "max_iter"))
    return t, n


def bishop_core(
    b: FloatArray,
    w: FloatArray,
    alpha: FloatArray,
    u: FloatArray,
    c: FloatArray,
    phi: FloatArray,
    tol: float,
    max_iter: int,
) -> FloatArray:
    """Bishop's fixed point for each row of the (samples, slices) arrays c and phi (b, w, alpha, u are per slice)."""
    cos_a, tan_a = np.cos(alpha), np.tan(alpha)
    sin_a = np.sin(alpha)
    drive = float(np.sum(w * sin_a))
    tan_phi = np.tan(phi)
    resisting = c * b + (w - u * b) * tan_phi  # (samples, slices)
    shear = tan_phi * sin_a  # m_alpha = cos_a + shear / F
    if phi.shape[1] == 1:  # one friction angle per sample: the extremes of tan(alpha) bound every slice
        critical = np.maximum(-tan_phi[:, 0] * tan_a.min(), -tan_phi[:, 0] * tan_a.max())
    else:
        critical = np.max(-shear / cos_a, axis=1)
    # m_alpha > 0 for every slice exactly when F > critical
    f = np.ones(c.shape[0])
    active = np.arange(c.shape[0])
    res_a, shear_a, crit_a = resisting, shear, critical
    for iteration in range(1, max_iter + 1):
        f_a = f[active]
        if np.any(f_a <= crit_a):
            m = cos_a + shear_a / f_a[:, None]
            if np.any(m <= 0):
                slice_index = int(np.argmax((m <= 0).any(axis=0)))
                raise ConvergenceError(
                    f"m_alpha <= 0 at slice {slice_index} during iteration {iteration}: no factor of safety",
                    last_iterate=float(f_a[0]),
                    residual=math.inf,
                    iterations=iteration,
                )
        m = shear_a / f_a[:, None]
        m += cos_a
        np.divide(res_a, m, out=m)
        new = m.sum(axis=1) / drive
        step = np.abs(new - f_a)
        f[active] = new
        done = step <= tol * np.abs(new)
        if done.all():
            return f
        if done.any():
            keep = ~done
            active = active[keep]
            res_a, shear_a, crit_a = res_a[keep], shear_a[keep], crit_a[keep]
    raise ConvergenceError(
        f"no convergence to tol={tol!r} in {max_iter} iterations",
        last_iterate=float(f[active[0]]),
        residual=float(np.max(step[~done])),
        iterations=max_iter,
    )


def bishop_simplified_fos(
    width: Any,
    weight: Any,
    base_angle: Any,
    pore_pressure: Any,
    cohesion: Any,
    friction_angle: Any,
    tol: Any = 1e-12,
    max_iter: Any = 200,
) -> Any:
    """Factor of safety of a circular slip surface by Bishop's simplified method.

    Parameters
    ----------
    width : array_like [m]
        Slice widths, 1-D, > 0; 1 to 10,000 slices.
    weight : array_like [N/m]
        Slice weights per metre of slope, >= 0.
    base_angle : array_like [rad]
        Slice base inclinations, -pi/2 < alpha < pi/2; the driving moment sum(W sin alpha) must be positive.
    pore_pressure : array_like [Pa]
        Pore pressures at the slice bases, >= 0.
    cohesion : float or array_like [Pa]
        Effective cohesion, >= 0; a scalar or one value per slice.
    friction_angle : float or array_like [rad]
        Effective friction angle, 0 <= phi' < pi/2; a scalar or one value per slice.
    tol : float [1]
        Relative step at which the iteration stops, > 0.
    max_iter : int [count]
        Iteration cap, an integer from 1 to 10,000.

    Returns
    -------
    numpy.float64 [1]
        Factor of safety F.

    Equation
    --------
    F = sum[(c' b + (W - u b) tan(phi')) / m_alpha] / sum[W sin(alpha)] with m_alpha = cos(alpha) (1 + tan(alpha)
    tan(phi') / F), iterated from F = 1.

    Source
    ------
    rocscience2020slide, eq. 4 to 6, p. 3

    Validity
    --------
    A non-positive m_alpha or no convergence within max_iter raises ConvergenceError; cohesion between 0 and
    tripwire_cohesion_min and a friction angle above tripwire_friction_angle_max emit a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_cohesion_min, tripwire_friction_angle_max
    """
    b, w, alpha, u = slice_arrays(width, weight, base_angle, pore_pressure)
    c, phi = strengths(cohesion, friction_angle, b.size)
    t, n = iteration_controls(tol, max_iter)
    return np.float64(bishop_core(b, w, alpha, u, c[None, :], phi[None, :], t, n)[0])


def _spencer_terms(
    f: float, theta: float, ell: FloatArray, w: FloatArray, alpha: FloatArray, u: FloatArray, c: FloatArray, tan_phi: FloatArray
) -> FloatArray:
    """Interslice terms Q_i of Spencer's method for (F, theta); a non-positive denominator names the first slice."""
    den = np.cos(alpha - theta) + np.sin(alpha - theta) * tan_phi / f
    if np.any(den <= 0):
        raise _Breakdown(int(np.argmax(den <= 0)))
    return (c * ell / f + (w * np.cos(alpha) - u * ell) * tan_phi / f - w * np.sin(alpha)) / den


class _Breakdown(Exception):
    """A trial point where Spencer's denominator is not positive (a damped Newton step backs off from it)."""

    def __init__(self, index: int) -> None:
        super().__init__(index)
        self.index = index


def _residuals(f: float, theta: float, *args: Any) -> tuple[float, float, float]:
    q = _spencer_terms(f, theta, *args)
    alpha = args[2]
    scale = float(np.sum(np.abs(q))) or 1.0
    return float(np.sum(q)), float(np.sum(q * np.cos(alpha - theta))), scale


def spencer_core(
    b: FloatArray, w: FloatArray, alpha: FloatArray, u: FloatArray, c: FloatArray, phi: FloatArray, tol: float, max_iter: int
) -> tuple[float, float]:
    """Spencer's (F, theta) by a damped Newton iteration on the force and moment equations."""
    ell = b / np.cos(alpha)
    tan_phi = np.tan(phi)
    args = (ell, w, alpha, u, c, tan_phi)
    try:
        f = float(bishop_core(b, w, alpha, u, c[None, :], phi[None, :], 1e-6, _MAX_ITER)[0])
    except ConvergenceError:
        f = 1.0
    theta = 0.0
    last = math.inf
    for iteration in range(1, max_iter + 1):
        try:
            force, moment, scale = _residuals(f, theta, *args)
        except _Breakdown as err:
            raise ConvergenceError(
                f"the Spencer denominator is not positive at slice {err.index}",
                last_iterate=f,
                residual=math.inf,
                iterations=iteration,
            ) from None
        last = max(abs(force), abs(moment)) / scale
        if last <= tol:
            return f, theta
        hf, ht = _FD_STEP * max(abs(f), 1), _FD_STEP
        try:
            fp = _residuals(f + hf, theta, *args)
            fm = _residuals(f - hf, theta, *args)
            tp = _residuals(f, theta + ht, *args)
            tm = _residuals(f, theta - ht, *args)
        except _Breakdown as err:
            raise ConvergenceError(
                f"the Spencer denominator is not positive at slice {err.index}",
                last_iterate=f,
                residual=last,
                iterations=iteration,
            ) from None
        jac = np.array(
            [
                [(fp[0] - fm[0]) / (2 * hf), (tp[0] - tm[0]) / (2 * ht)],
                [(fp[1] - fm[1]) / (2 * hf), (tp[1] - tm[1]) / (2 * ht)],
            ]
        )
        try:
            step = np.linalg.solve(jac, -np.array([force, moment]))
        except np.linalg.LinAlgError:
            raise ConvergenceError(
                "the Jacobian of Spencer's equations is singular", last_iterate=f, residual=last, iterations=iteration
            ) from None
        damping = 1.0
        for _ in range(_BACKTRACKS):
            f_new, t_new = f + damping * float(step[0]), theta + damping * float(step[1])
            if f_new > 0:
                try:
                    f_force, f_moment, f_scale = _residuals(f_new, t_new, *args)
                except _Breakdown:
                    pass
                else:
                    if max(abs(f_force), abs(f_moment)) / f_scale < last or damping < 2 * _FD_STEP:
                        break
            damping /= 2
        f, theta = f_new, t_new
    raise ConvergenceError(
        f"no convergence to tol={tol!r} in {max_iter} iterations", last_iterate=f, residual=last, iterations=max_iter
    )


def spencer_fos(
    width: Any,
    weight: Any,
    base_angle: Any,
    pore_pressure: Any,
    cohesion: Any,
    friction_angle: Any,
    tol: Any = 1e-12,
    max_iter: Any = 200,
) -> tuple[Any, Any]:
    """Factor of safety of a circular slip surface by Spencer's method.

    Parameters
    ----------
    width : array_like [m]
        Slice widths, 1-D, > 0; 2 to 10,000 slices.
    weight : array_like [N/m]
        Slice weights per metre of slope, >= 0.
    base_angle : array_like [rad]
        Slice base inclinations, -pi/2 < alpha < pi/2; the driving moment sum(W sin alpha) must be positive.
    pore_pressure : array_like [Pa]
        Pore pressures at the slice bases, >= 0.
    cohesion : float or array_like [Pa]
        Effective cohesion, >= 0; a scalar or one value per slice.
    friction_angle : float or array_like [rad]
        Effective friction angle, 0 <= phi' < pi/2; a scalar or one value per slice.
    tol : float [1]
        Relative residual of the force and moment equations at which the iteration stops, > 0.
    max_iter : int [count]
        Iteration cap, an integer from 1 to 10,000.

    Returns
    -------
    tuple of numpy.float64 [1]
        (fos [1], theta [rad]): the factor of safety and the inclination of the interslice resultant.

    Equation
    --------
    Q_i = [c' l_i / F + (W_i cos(alpha_i) - u_i l_i) tan(phi') / F - W_i sin(alpha_i)] / [cos(alpha_i - theta) +
    sin(alpha_i - theta) tan(phi') / F]; both sum(Q_i) = 0 and sum(Q_i cos(alpha_i - theta)) = 0 hold.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-10; the slice equation was not read on a primary source)

    Validity
    --------
    A non-positive denominator or no convergence within max_iter raises ConvergenceError; tripwires as in
    bishop_simplified_fos.

    Knowledge rows
    --------------
    tripwire_cohesion_min, tripwire_friction_angle_max
    """
    b, w, alpha, u = slice_arrays(width, weight, base_angle, pore_pressure, min_slices=2)
    c, phi = strengths(cohesion, friction_angle, b.size)
    t, n = iteration_controls(tol, max_iter)
    fos, theta = spencer_core(b, w, alpha, u, c, phi, t, n)
    return np.float64(fos), np.float64(theta)

