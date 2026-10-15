"""Gy's fundamental sampling error and the bed-blending variance of a layered stockpile (spec 004 FR-004-08,
FR-004-09, FR-004-12)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .. import _tripwire as tw
from .._errors import InputError
from .._validate import FloatArray, as_checked, as_count, broadcast_all, finalize

_MAX_LAYERS = 10_000_000
_SERIES_TERMS = 40


def gy_fundamental_sampling_error(
    sample_mass: Any,
    lot_mass: Any,
    top_size: Any,
    mineralogical_factor: Any,
    shape_factor: Any,
    granulometric_factor: Any,
    liberation_factor: Any,
) -> Any:
    """Relative variance of the fundamental sampling error of Gy.

    Parameters
    ----------
    sample_mass : float or array_like [kg]
        Mass of the sample M_S, > 0 and not above the lot mass.
    lot_mass : float or array_like [kg]
        Mass of the lot M_L, > 0.
    top_size : float or array_like [m]
        Nominal top size of the particles d, > 0.
    mineralogical_factor : float or array_like [kg/m^3]
        Mineralogical factor c, > 0; no default.
    shape_factor : float or array_like [1]
        Particle shape factor f, 0 < f <= 1; no default.
    granulometric_factor : float or array_like [1]
        Size-distribution factor g, 0 < g <= 1; no default.
    liberation_factor : float or array_like [1]
        Liberation factor l, 0 < l <= 1; no default.

    Returns
    -------
    float or ndarray [1]
        Relative variance (the square of the relative standard deviation).

    Equation
    --------
    s^2 = (1 / M_S - 1 / M_L) c f g l d^3

    Source
    ------
    minkkinen2008, p. 5 (without the lot-mass term in geelhoed2011, Eq. 1)

    Validity
    --------
    Gy's own text was not read. The mass term is evaluated as (M_L - M_S) / (M_S M_L) so that a sample close to the
    lot does not cancel. sample_mass above lot_mass raises InputError naming sample_mass. A mineralogical factor
    below 100 kg/m^3 and a top size above 0.5 m emit a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_mineralogical_factor_min, tripwire_top_size_max
    """
    ms = as_checked(sample_mass, "sample_mass", lo=0, lo_open=True)
    ml = as_checked(lot_mass, "lot_mass", lo=0, lo_open=True)
    d = as_checked(top_size, "top_size", lo=0, lo_open=True)
    c = as_checked(mineralogical_factor, "mineralogical_factor", lo=0, lo_open=True)
    f = as_checked(shape_factor, "shape_factor", lo=0, hi=1, lo_open=True)
    g = as_checked(granulometric_factor, "granulometric_factor", lo=0, hi=1, lo_open=True)
    ell = as_checked(liberation_factor, "liberation_factor", lo=0, hi=1, lo_open=True)
    named = {
        "sample_mass": ms,
        "lot_mass": ml,
        "top_size": d,
        "mineralogical_factor": c,
        "shape_factor": f,
        "granulometric_factor": g,
        "liberation_factor": ell,
    }
    ms, ml, d, c, f, g, ell = broadcast_all(**named)
    larger = ms > ml
    if larger.any():
        i = int(np.argmax(larger.ravel()))
        raise InputError(
            f"argument 'sample_mass' must not exceed lot_mass, got {float(ms.ravel()[i])!r} against "
            f"{float(ml.ravel()[i])!r}",
            argument="sample_mass",
        )
    tw.warn_min(c, "mineralogical_factor", "tripwire_mineralogical_factor_min")
    tw.warn_max(d, "top_size", "tripwire_top_size_max")
    return finalize((ml - ms) / (ms * ml) * c * f * g * ell * d**3, *named.values())


def _blending_factor(n: FloatArray, rho: FloatArray) -> FloatArray:
    """A = 1 + 2 sum_{k=1}^{N-1} (1 - k/N) rho^k in O(1) for every N, stable for correlations close to +-1.

    With q = 1 - rho and t = 1 - rho^N the sum is rho (N q - t) / (N q^2), so A = (1 + rho) / q - 2 rho t / (N q^2).
    That difference cancels when N q is small, where the binomial series N q - t = sum_{j>=2} (-1)^j C(N, j) q^j is
    used instead (it converges for N q < 1). t is built from log1p and expm1 so that rho^N is exact near 1.
    """
    q = 1 - rho
    with np.errstate(all="ignore"):
        magnitude = np.abs(rho)
        log_mag = np.where(2 * magnitude > 1, np.log1p(-(1 - magnitude)), np.log(magnitude))
        odd_negative = (rho < 0) & (n % 2 == 1)
        t = np.where(odd_negative, 1 + np.exp(n * log_mag), -np.expm1(n * log_mag))
        closed = (1 + rho) / q - 2 * rho * t / (n * q * q)
    result = np.array(closed, dtype=np.float64).reshape(-1)
    small = (n * q < 1).reshape(-1)
    if small.any():
        ns, qs, rs = n.reshape(-1)[small], q.reshape(-1)[small], rho.reshape(-1)[small]
        term = ns * (ns - 1) / 2
        total = term.copy()
        for j in range(2, _SERIES_TERMS):
            term = -term * (ns - j) / (j + 1) * qs
            total = total + term
        result[small] = 1 + 2 * rs / ns * total
    return result.reshape(closed.shape)


def _blending_inputs(n_layers: Any, lag1_correlation: Any) -> tuple[FloatArray, FloatArray]:
    n = as_count(n_layers, "n_layers", lo=1, hi=_MAX_LAYERS)
    rho = as_checked(lag1_correlation, "lag1_correlation", lo=-1, hi=1, lo_open=True, hi_open=True)
    return n, rho


def gy_blending_variance(input_variance: Any, n_layers: Any, lag1_correlation: Any = 0) -> Any:
    """Variance of the mean grade of a bed of N layers whose grades follow a stationary first-order autoregression.

    Parameters
    ----------
    input_variance : float or array_like [1]
        Variance of the grade of one layer, in the squared unit of the grade, >= 0.
    n_layers : float or array_like [1]
        Number of layers N, a whole number from 1 to 10,000,000.
    lag1_correlation : float or array_like [1]
        Lag-1 autocorrelation rho of the layer grades, -1 < rho < 1.

    Returns
    -------
    float or ndarray [1]
        Variance of the blended grade, in the squared unit of input_variance.

    Equation
    --------
    s_out^2 = s_in^2 / N (1 + 2 sum_{k=1}^{N-1} (1 - k / N) rho^k)

    Source
    ------
    minephys:spec-004-bulk, section 7.4 (the sum is arithmetic, derived on the theory page; rho = 0 is Gy's 1/N)

    Validity
    --------
    A stationary AR(1) grade series reclaimed over the full cross-section. The sum is evaluated in closed form, so
    N up to 10,000,000 costs O(1). A layer count that is not a whole number in 1 to 10,000,000 or a correlation
    outside (-1, 1) raises InputError.

    Knowledge rows
    --------------
    none
    """
    var = as_checked(input_variance, "input_variance", lo=0)
    n, rho = _blending_inputs(n_layers, lag1_correlation)
    var, n, rho = broadcast_all(input_variance=var, n_layers=n, lag1_correlation=rho)
    return finalize(var * _blending_factor(n, rho) / n, var, n, rho)


def variance_reduction_ratio(n_layers: Any, lag1_correlation: Any = 0) -> Any:
    """Ratio of the layer variance to the variance of the blended grade.

    Parameters
    ----------
    n_layers : float or array_like [1]
        Number of layers N, a whole number from 1 to 10,000,000.
    lag1_correlation : float or array_like [1]
        Lag-1 autocorrelation rho of the layer grades, -1 < rho < 1.

    Returns
    -------
    float or ndarray [1]
        Variance reduction ratio (equal to N for uncorrelated layers).

    Equation
    --------
    R = N / (1 + 2 sum_{k=1}^{N-1} (1 - k / N) rho^k)

    Source
    ------
    minephys:spec-004-bulk, section 7.4 (the sum is arithmetic, derived on the theory page; rho = 0 is Gy's 1/N)

    Validity
    --------
    A stationary AR(1) grade series reclaimed over the full cross-section, as for gy_blending_variance.

    Knowledge rows
    --------------
    none
    """
    n, rho = _blending_inputs(n_layers, lag1_correlation)
    n, rho = broadcast_all(n_layers=n, lag1_correlation=rho)
    return finalize(n / _blending_factor(n, rho), n, rho)
