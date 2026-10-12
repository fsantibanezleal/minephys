"""Voight creep series, the inverse-velocity forecast and the conjugate Bayesian time of failure (spec 003 FR-003-14
to FR-003-17, FR-003-21, FR-003-23)."""

from __future__ import annotations

import math
from typing import Any, NamedTuple

import numpy as np

from .. import _tripwire as tw
from .._errors import InputError
from .._random import as_generator
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

_MAX_SAMPLES = 10**6
_MIN_USED = 3
_MIN_DRAWS = 100
_SYMMETRY_RTOL = 1e-9


def voight_creep_series(t: Any, failure_time: Any, a: Any, alpha: Any) -> tuple[FloatArray, FloatArray]:
    """Velocity and displacement of Voight's accelerating-creep law.

    Parameters
    ----------
    t : array_like [s]
        Times, 1-D, at least one, every t < failure_time (negative times are allowed).
    failure_time : float [s]
        Failure time t_f, > 0.
    a : float [(m/s)^(1-alpha)/s]
        Voight constant A, > 0 (1/m for alpha = 2).
    alpha : float [1]
        Voight exponent, > 1.

    Returns
    -------
    tuple of ndarray [m/s]
        (velocity [m/s], displacement [m]) shaped like t; the displacement accumulates from t[0].

    Equation
    --------
    v = [A (alpha - 1) (t_f - t)]^(1/(1 - alpha)); displacement = [A (alpha - 1)]^p ((t_f - t0)^q - (t_f - t)^q) / q
    with p = 1/(1 - alpha), q = p + 1, and (1/A) ln((t_f - t0) / (t_f - t)) for alpha = 2.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-14; the solution of the ODE, no empirical constant)

    Validity
    --------
    The terminal accelerating stage; v blows up at t_f.

    Knowledge rows
    --------------
    none
    """
    tf = as_scalar(as_checked(failure_time, "failure_time", lo=0, lo_open=True), "failure_time")
    rate = as_scalar(as_checked(a, "a", lo=0, lo_open=True), "a")
    exponent = as_scalar(as_checked(alpha, "alpha", lo=1, lo_open=True), "alpha")
    times = as_float_array(t, "t")
    check_rank(times, "t", 1)
    check_finite(times, "t")
    check_size(times, "t", min_size=1)
    if np.any(times >= tf):
        raise InputError("every time t must lie before the failure time", argument="t")
    p = 1 / (1 - exponent)
    q = p + 1
    base = rate * (exponent - 1)
    remaining = tf - times
    velocity = (base * remaining) ** p
    span = np.log((tf - times[0]) / remaining)  # ln((t_f - t0) / (t_f - t)) >= 0 when the times increase
    x = -q * span
    with np.errstate(invalid="ignore", divide="ignore"):
        shape = np.where(x == 0, 1, np.expm1(x) / np.where(x == 0, 1, x))
    displacement = base**p * (tf - times[0]) ** q * span * shape
    return velocity, displacement


class _Series(NamedTuple):
    t: FloatArray
    y: FloatArray


def _series(t: Any, velocity: Any, window: Any) -> _Series:
    """Validated times and inverse velocities of the used samples (the last `window`, or all)."""
    times = as_float_array(t, "t")
    v = as_float_array(velocity, "velocity")
    check_rank(times, "t", 1)
    check_rank(v, "velocity", 1)
    check_finite(times, "t")
    check_finite(v, "velocity")
    check_size(times, "t", max_size=_MAX_SAMPLES)
    if times.size != v.size:
        raise InputError(f"t has {times.size} samples but velocity has {v.size}", argument="velocity")
    check_size(times, "t", min_size=_MIN_USED)
    as_checked(v, "velocity", lo=0, lo_open=True)
    keep = None if window is None else int(as_scalar(as_count(window, "window", lo=_MIN_USED, hi=_MAX_SAMPLES), "window"))
    if np.any(np.diff(times) <= 0):
        raise InputError("argument 't' must be strictly increasing", argument="t")
    tw.warn_max(v, "velocity", "tripwire_slope_velocity_max")
    if keep is not None:
        times, v = times[-keep:], v[-keep:]
    return _Series(times, 1 / v)


class InverseVelocityResult(NamedTuple):
    """Least-squares fit of the inverse velocity and the failure time it implies."""

    failure_time: np.float64
    slope: np.float64
    intercept: np.float64
    r_squared: np.float64
    accelerating: bool
    n_used: int


def inverse_velocity_ttf(t: Any, velocity: Any, window: Any = None) -> InverseVelocityResult:
    """Time of failure by Fukuzono's inverse-velocity method.

    Parameters
    ----------
    t : array_like [s]
        Sample times, 1-D, strictly increasing; 3 to 1,000,000 samples.
    velocity : array_like [m/s]
        Velocities, 1-D, > 0, same length as t.
    window : int [count]
        Use only the last `window` samples (an integer >= 3); None uses all.

    Returns
    -------
    InverseVelocityResult [s]
        Named result: failure_time [s] (+inf while not accelerating), slope [1/m], intercept [s/m], r_squared [1],
        accelerating [bool] and n_used [count].

    Equation
    --------
    Ordinary least squares of 1/v = b0 + b1 t on the used samples; t_f = -b0 / b1 when b1 < 0.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-15; the linear inverse-velocity relation of the alpha = 2 law)

    Validity
    --------
    Assumes the terminal accelerating stage with alpha near 2; velocity above tripwire_slope_velocity_max (mm/day
    passed as m/s) emits a ValidityWarning; a constant series has r_squared 0.

    Knowledge rows
    --------------
    tripwire_slope_velocity_max
    """
    used = _series(t, velocity, window)
    n = used.t.size
    t_mean, y_mean = float(np.mean(used.t)), float(np.mean(used.y))
    centred = used.t - t_mean
    dy = used.y - y_mean
    sxx, sxy, syy = float(np.sum(centred * centred)), float(np.sum(centred * dy)), float(np.sum(dy * dy))
    slope = sxy / sxx
    accelerating = slope < 0
    failure = t_mean - y_mean / slope if accelerating else math.inf
    r2 = sxy * sxy / (sxx * syy) if syy > 0 else 0.0
    return InverseVelocityResult(
        np.float64(failure), np.float64(slope), np.float64(y_mean - slope * t_mean), np.float64(r2), accelerating, n
    )


class BayesianTTF(NamedTuple):
    """Gaussian posterior of the inverse-velocity line and the failure time it implies."""

    posterior_mean: FloatArray
    posterior_cov: FloatArray
    failure_time_median: float
    failure_time_lower: float
    failure_time_upper: float
    fraction_not_accelerating: float


def _vector(value: Any, name: str, shape: tuple[int, ...]) -> FloatArray:
    arr = as_float_array(value, name)
    if arr.shape != shape:
        raise InputError(f"argument '{name}' must have shape {shape}, got {tuple(arr.shape)}", argument=name)
    return check_finite(arr, name)


def bayesian_ttf(
    t: Any,
    velocity: Any,
    rng: Any,
    noise_sd: Any = None,
    prior_mean: Any = None,
    prior_cov: Any = None,
    n_draws: Any = 10_000,
    credible: Any = 0.9,
    window: Any = None,
) -> BayesianTTF:
    """Conjugate Gaussian posterior of the failure time of an accelerating slope.

    Parameters
    ----------
    t : array_like [s]
        Sample times, 1-D, strictly increasing; 3 to 1,000,000 samples.
    velocity : array_like [m/s]
        Velocities, 1-D, > 0, same length as t.
    rng : numpy.random.Generator or int
        Random source (no default): a Generator or an integer seed.
    noise_sd : float [s/m]
        Standard deviation of the noise of 1/v, > 0; None estimates it from the least-squares residuals.
    prior_mean : array_like [s/m]
        Prior mean of (b0, b1), length 2; used only together with prior_cov (otherwise the prior is flat).
    prior_cov : array_like [1]
        Prior covariance of (b0, b1), a symmetric positive-definite 2 x 2 matrix; None gives a flat prior.
    n_draws : int [count]
        Number of posterior draws, an integer from 100 to 1,000,000.
    credible : float [1]
        Credible mass of the equal-tailed interval, 0 < q < 1.
    window : int [count]
        Use only the last `window` samples (an integer >= 3); None uses all.

    Returns
    -------
    BayesianTTF [s]
        Named result: posterior_mean [s/m] (2,), posterior_cov (2, 2), failure_time_median [s],
        failure_time_lower [s], failure_time_upper [s] (over the draws with b1 < 0, +inf when there is none) and
        fraction_not_accelerating [1] (the fraction of draws with b1 >= 0).

    Equation
    --------
    Sigma_N = (Sigma0^-1 + X'X / sigma^2)^-1, mu_N = Sigma_N (Sigma0^-1 mu0 + X'y / sigma^2) for y = 1/v and
    X = [1, t]; t_f = -b0 / b1 on the draws.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-17; a conjugate linear-Gaussian update, no empirical constant)

    Validity
    --------
    Known or estimated noise of 1/v that is independent between samples; velocity above tripwire_slope_velocity_max
    emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_slope_velocity_max
    """
    used = _series(t, velocity, window)
    sigma = None if noise_sd is None else as_scalar(as_checked(noise_sd, "noise_sd", lo=0, lo_open=True), "noise_sd")
    mu0 = None if prior_mean is None else _vector(prior_mean, "prior_mean", (2,))
    cov0 = None if prior_cov is None else _vector(prior_cov, "prior_cov", (2, 2))
    if cov0 is not None:
        if mu0 is None:
            raise InputError("argument 'prior_mean' is required together with prior_cov", argument="prior_mean")
        if not np.allclose(cov0, cov0.T, rtol=_SYMMETRY_RTOL, atol=0) or float(np.linalg.eigvalsh((cov0 + cov0.T) / 2)[0]) <= 0:
            raise InputError("argument 'prior_cov' must be a symmetric positive-definite 2 x 2 matrix", argument="prior_cov")
    draws = int(as_scalar(as_count(n_draws, "n_draws", lo=_MIN_DRAWS, hi=_MAX_SAMPLES), "n_draws"))
    level = as_scalar(as_checked(credible, "credible", lo=0, hi=1, lo_open=True, hi_open=True), "credible")
    generator = as_generator(rng)

    n = used.t.size
    t_mean = float(np.mean(used.t))
    s = used.t - t_mean
    sxx = float(np.sum(s * s))
    y = used.y
    if sigma is None:
        slope = float(np.sum(s * (y - np.mean(y)))) / sxx
        resid = y - np.mean(y) - slope * s
        variance = float(np.sum(resid * resid)) / (n - 2)
        if variance <= 0:
            raise InputError("the residuals are zero: pass noise_sd", argument="noise_sd")
        sigma = math.sqrt(variance)
    # centred coordinates: b0' = b0 + b1 t_mean, so X' = [1, t - t_mean] and X'X is diagonal
    shift = np.array([[1.0, t_mean], [0.0, 1.0]])
    precision = np.diag([n, sxx]) / (sigma * sigma)
    rhs = np.array([float(np.sum(y)), float(np.sum(s * y))]) / (sigma * sigma)
    if cov0 is not None and mu0 is not None:
        cov0c = shift @ cov0 @ shift.T
        prior_precision = np.linalg.inv(cov0c)
        precision = precision + prior_precision
        rhs = rhs + prior_precision @ (shift @ mu0)
    cov_c = np.linalg.inv(precision)
    mean_c = cov_c @ rhs
    back = np.array([[1.0, -t_mean], [0.0, 1.0]])
    cov = back @ cov_c @ back.T
    cov = (cov + cov.T) / 2
    mean = back @ mean_c

    chol = np.linalg.cholesky(cov)
    sample = mean + generator.standard_normal((draws, 2)) @ chol.T
    accelerating = sample[:, 1] < 0
    fraction = float(np.count_nonzero(~accelerating)) / draws
    if np.any(accelerating):
        tf = -sample[accelerating, 0] / sample[accelerating, 1]
        lower, median, upper = (float(v) for v in np.quantile(tf, [(1 - level) / 2, 1 / 2, (1 + level) / 2]))
    else:
        lower = median = upper = math.inf
    return BayesianTTF(mean, cov, median, lower, upper, fraction)
