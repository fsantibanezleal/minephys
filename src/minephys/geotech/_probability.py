"""Monte-Carlo factor of safety and the probability-of-failure helpers (spec 003 FR-003-12, FR-003-13, FR-003-23,
FR-003-24)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .._errors import ConvergenceError, InputError
from .._random import as_generator
from .._validate import (
    FloatArray,
    as_checked,
    as_count,
    as_float_array,
    as_scalar,
    broadcast_all,
    check_finite,
    check_option,
    check_rank,
    check_size,
)
from ._lem import bishop_core, slice_arrays, spencer_core, warn_strengths

_METHODS = ("bishop", "spencer")
_MAX_SAMPLES = 10**6
_HALF_PI = math.pi / 2
_RESAMPLE_ROUNDS = 1000
_INTEGER_RULE = 1e-12
_TOL = 1e-12
_MAX_ITER = 200


def _truncated_normal(
    rng: np.random.Generator, mean: float, sd: float, n: int, lo: float, hi: float, name: str
) -> FloatArray:
    """Normal draws mean + sd z with the rejected ones (outside [lo, hi)) redrawn from `rng`, never clipped."""
    z = rng.standard_normal(n)
    x = mean + sd * z
    for _ in range(_RESAMPLE_ROUNDS):
        bad = (x < lo) | (x >= hi)
        count = int(np.count_nonzero(bad))
        if count == 0:
            return x
        z[bad] = rng.standard_normal(count)
        x = mean + sd * z
    raise ConvergenceError(
        f"the truncation to [{lo!r}, {hi!r}) rejects almost every draw of {name}",
        last_iterate=float(mean),
        residual=float(count) / n,
        iterations=_RESAMPLE_ROUNDS,
    )


def monte_carlo_fos(
    width: Any,
    weight: Any,
    base_angle: Any,
    pore_pressure: Any,
    cohesion_mean: Any,
    cohesion_sd: Any,
    friction_mean: Any,
    friction_sd: Any,
    n_samples: Any,
    rng: Any,
    method: str = "bishop",
) -> FloatArray:
    """Factors of safety of a fixed slip surface under normally distributed strength.

    Parameters
    ----------
    width : array_like [m]
        Slice widths, 1-D, > 0; 1 to 10,000 slices (2 or more for "spencer").
    weight : array_like [N/m]
        Slice weights per metre of slope, >= 0.
    base_angle : array_like [rad]
        Slice base inclinations, -pi/2 < alpha < pi/2; the driving moment must be positive.
    pore_pressure : array_like [Pa]
        Pore pressures at the slice bases, >= 0.
    cohesion_mean : float [Pa]
        Mean of the effective cohesion, >= 0.
    cohesion_sd : float [Pa]
        Standard deviation of the effective cohesion, >= 0.
    friction_mean : float [rad]
        Mean of the effective friction angle, 0 <= phi' < pi/2.
    friction_sd : float [rad]
        Standard deviation of the effective friction angle, >= 0.
    n_samples : int [count]
        Number of draws, an integer from 1 to 1,000,000.
    rng : numpy.random.Generator or int
        Random source (no default): a Generator or an integer seed.
    method : {"bishop", "spencer"}
        Limit-equilibrium method evaluated for each draw.

    Returns
    -------
    ndarray [1]
        The n_samples factors of safety (float64).

    Equation
    --------
    c' = mu_c + sd_c z and phi' = mu_phi + sd_phi z' with independent standard normal z, z', the draws outside c' >= 0
    and 0 <= phi' < pi/2 resampled; each draw is evaluated on the fixed slices.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-12; truncation by resampling, no empirical constant)

    Validity
    --------
    The slip surface stays fixed (this underestimates the probability of failure of a per-sample critical surface);
    tripwires as in bishop_simplified_fos apply to the means.

    Knowledge rows
    --------------
    tripwire_cohesion_min, tripwire_friction_angle_max
    """
    b, w, alpha, u = slice_arrays(width, weight, base_angle, pore_pressure, min_slices=2 if method == "spencer" else 1)
    c_mean = as_scalar(as_checked(cohesion_mean, "cohesion_mean", lo=0), "cohesion_mean")
    c_sd = as_scalar(as_checked(cohesion_sd, "cohesion_sd", lo=0), "cohesion_sd")
    f_mean = as_scalar(as_checked(friction_mean, "friction_mean", lo=0, hi=_HALF_PI, hi_open=True), "friction_mean")
    f_sd = as_scalar(as_checked(friction_sd, "friction_sd", lo=0), "friction_sd")
    n = int(as_scalar(as_count(n_samples, "n_samples", hi=_MAX_SAMPLES), "n_samples"))
    check_option(method, "method", _METHODS)
    generator = as_generator(rng)
    warn_strengths(np.asarray(c_mean), np.asarray(f_mean), "cohesion_mean", "friction_mean")
    cohesion = _truncated_normal(generator, c_mean, c_sd, n, 0, math.inf, "cohesion")
    friction = _truncated_normal(generator, f_mean, f_sd, n, 0, _HALF_PI, "friction_angle")
    if method == "bishop":
        return bishop_core(b, w, alpha, u, cohesion[:, None], friction[:, None], _TOL, _MAX_ITER)
    out = np.empty(n)
    for i in range(n):
        out[i] = spencer_core(
            b, w, alpha, u, np.full(b.size, cohesion[i]), np.full(b.size, friction[i]), _TOL, _MAX_ITER
        )[0]
    return out


def probability_of_failure(fos_samples: Any, threshold: Any = 1) -> tuple[Any, Any, int]:
    """Probability of failure from sampled factors of safety.

    Parameters
    ----------
    fos_samples : array_like [1]
        Sampled factors of safety, 1-D, at least one sample.
    threshold : float [1]
        Factor of safety below which a sample counts as a failure.

    Returns
    -------
    tuple [1]
        (pof [1], standard_error [1], n [count]): the fraction of samples strictly below the threshold, its binomial
        standard error and the number of samples.

    Equation
    --------
    pof = count(F < threshold) / n; standard_error = sqrt(pof (1 - pof) / n)

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-13; a binomial estimate)

    Validity
    --------
    The standard error is the Monte-Carlo error of the estimate, not a model uncertainty.

    Knowledge rows
    --------------
    none
    """
    samples = as_float_array(fos_samples, "fos_samples")
    check_rank(samples, "fos_samples", 1)
    check_finite(samples, "fos_samples")
    check_size(samples, "fos_samples", min_size=1)
    limit = as_scalar(check_finite(as_float_array(threshold, "threshold"), "threshold"), "threshold")
    n = int(samples.size)
    pof = float(np.count_nonzero(samples < limit)) / n
    return np.float64(pof), np.float64(math.sqrt(pof * (1 - pof) / n)), n


def required_samples(pof: Any, relative_error: Any) -> Any:
    """Monte-Carlo sample size that reaches a target relative error of the probability of failure.

    Parameters
    ----------
    pof : float or array_like [1]
        Probability of failure to estimate, 0 < p < 1.
    relative_error : float or array_like [1]
        Target relative standard error, > 0.

    Returns
    -------
    numpy.int64 or ndarray [count]
        Smallest integer n with sqrt((1 - p) / (n p)) <= relative_error (int64).

    Equation
    --------
    n = ceil((1 - p) / (p eps^2)), a quotient within a relative 1e-12 of an integer counting as that integer.

    Source
    ------
    minephys:spec-003-geotech, section 3 (FR-003-13; the binomial relative error)

    Validity
    --------
    More than 2**62 samples is an InputError naming pof.

    Knowledge rows
    --------------
    none
    """
    p = as_checked(pof, "pof", lo=0, hi=1, lo_open=True, hi_open=True)
    eps = as_checked(relative_error, "relative_error", lo=0, lo_open=True)
    p, eps = broadcast_all(pof=p, relative_error=eps)
    with np.errstate(over="ignore", divide="ignore"):
        quotient = (1 - p) / (p * eps * eps)
    if np.any(~np.isfinite(quotient) | (quotient > float(2**62))):
        raise InputError("the target needs more than 2**62 samples", argument="pof")
    nearest = np.rint(quotient)
    count = np.where(np.abs(quotient - nearest) <= _INTEGER_RULE * quotient, nearest, np.ceil(quotient)).astype(
        np.int64
    )
    return np.int64(count[()]) if count.ndim == 0 else count
