"""Rosin-Rammler and Swebrec size distributions and the KCO link (spec 002 FR-002-05 to FR-002-07, FR-002-15)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .._errors import InputError
from .._validate import FloatArray, as_checked, broadcast_all, finalize

_LN2 = math.log(2)


def _open_unit(value: Any, name: str) -> FloatArray:
    return as_checked(value, name, lo=0, hi=1, lo_open=True, hi_open=True)


def _check_x50_below_xmax(x50: FloatArray, xmax: FloatArray) -> None:
    if np.any(x50 >= xmax):
        raise InputError("argument 'x50' must be smaller than xmax (ln(xmax / x50) must be positive)", argument="x50")


def rosin_rammler_passing(size: Any, x50: Any, n: Any) -> Any:
    """Cumulative fraction passing a size for a Rosin-Rammler distribution written with its median.

    Parameters
    ----------
    size : float or array_like [m]
        Sieve or particle size, > 0.
    x50 : float or array_like [m]
        Median size, > 0.
    n : float or array_like [1]
        Uniformity index (Rosin-Rammler exponent), > 0.

    Returns
    -------
    float or ndarray [1]
        Fraction passing, from 0 to 1.

    Equation
    --------
    P = 1 - exp(-ln 2 (x / x50)^n)

    Source
    ------
    cunningham2005, eq. 2, p. 202

    Validity
    --------
    ln 2 is used instead of the printed 0.693 so that x50 is exactly the median (relative difference 2.1e-4).

    Knowledge rows
    --------------
    rosin_rammler_median_constant
    """
    x = as_checked(size, "size", lo=0, lo_open=True)
    m = as_checked(x50, "x50", lo=0, lo_open=True)
    k = as_checked(n, "n", lo=0, lo_open=True)
    x, m, k = broadcast_all(size=x, x50=m, n=k)
    with np.errstate(over="ignore"):
        passing = -np.expm1(-_LN2 * (x / m) ** k)
    return finalize(passing, x, m, k)


def rosin_rammler_size(passing: Any, x50: Any, n: Any) -> Any:
    """Size at a given cumulative fraction passing for a Rosin-Rammler distribution (its percentile).

    Parameters
    ----------
    passing : float or array_like [1]
        Fraction passing, 0 < P < 1.
    x50 : float or array_like [m]
        Median size, > 0.
    n : float or array_like [1]
        Uniformity index, > 0.

    Returns
    -------
    float or ndarray [m]
        Size x at which the fraction passing is P.

    Equation
    --------
    x = x50 (ln(1 / (1 - P)) / ln 2)^(1 / n)

    Source
    ------
    cunningham2005, eq. 2, p. 202

    Validity
    --------
    Inverse of rosin_rammler_passing; P outside (0, 1) is an InputError naming passing.

    Knowledge rows
    --------------
    rosin_rammler_median_constant
    """
    p = _open_unit(passing, "passing")
    m = as_checked(x50, "x50", lo=0, lo_open=True)
    k = as_checked(n, "n", lo=0, lo_open=True)
    p, m, k = broadcast_all(passing=p, x50=m, n=k)
    return finalize(m * (-np.log1p(-p) / _LN2) ** (1 / k), p, m, k)


def swebrec_passing(size: Any, x50: Any, xmax: Any, b: Any) -> Any:
    """Cumulative fraction passing a size for the Swebrec function.

    Parameters
    ----------
    size : float or array_like [m]
        Sieve or particle size, > 0.
    x50 : float or array_like [m]
        Median size, > 0 and below xmax.
    xmax : float or array_like [m]
        Largest size, > 0.
    b : float or array_like [1]
        Undulation parameter, > 0.

    Returns
    -------
    float or ndarray [1]
        Fraction passing, from 0 to 1 (exactly 1 for size >= xmax).

    Equation
    --------
    P = 1 / (1 + [ln(xmax / x) / ln(xmax / x50)]^b) for 0 < x < xmax, and P = 1 for x >= xmax.

    Source
    ------
    mutinda2021, eq. 1, p. 109

    Validity
    --------
    x50 >= xmax is an InputError naming x50; the primary (Ouchterlony 2005) is paywalled.

    Knowledge rows
    --------------
    none
    """
    x = as_checked(size, "size", lo=0, lo_open=True)
    m = as_checked(x50, "x50", lo=0, lo_open=True)
    top = as_checked(xmax, "xmax", lo=0, lo_open=True)
    undulation = as_checked(b, "b", lo=0, lo_open=True)
    x, m, top, undulation = broadcast_all(size=x, x50=m, xmax=top, b=undulation)
    _check_x50_below_xmax(m, top)
    inside = x < top
    with np.errstate(over="ignore", divide="ignore"):
        ratio = np.where(inside, np.log(top / x) / np.log(top / m), 1)
        passing = np.where(inside, 1 / (1 + ratio**undulation), 1)
    return finalize(passing, x, m, top, undulation)


def swebrec_size(passing: Any, x50: Any, xmax: Any, b: Any) -> Any:
    """Size at a given cumulative fraction passing for the Swebrec function (its percentile).

    Parameters
    ----------
    passing : float or array_like [1]
        Fraction passing, 0 < P < 1.
    x50 : float or array_like [m]
        Median size, > 0 and below xmax.
    xmax : float or array_like [m]
        Largest size, > 0.
    b : float or array_like [1]
        Undulation parameter, > 0.

    Returns
    -------
    float or ndarray [m]
        Size x at which the fraction passing is P (0.0 where it underflows).

    Equation
    --------
    x = xmax (x50 / xmax)^(((1 - P) / P)^(1 / b))

    Source
    ------
    mutinda2021, eq. 1, p. 109

    Validity
    --------
    Inverse of swebrec_passing; P outside (0, 1) is an InputError naming passing; x50 >= xmax names x50.

    Knowledge rows
    --------------
    none
    """
    p = _open_unit(passing, "passing")
    m = as_checked(x50, "x50", lo=0, lo_open=True)
    top = as_checked(xmax, "xmax", lo=0, lo_open=True)
    undulation = as_checked(b, "b", lo=0, lo_open=True)
    p, m, top, undulation = broadcast_all(passing=p, x50=m, xmax=top, b=undulation)
    _check_x50_below_xmax(m, top)
    with np.errstate(over="ignore", under="ignore"):
        size = top * (m / top) ** (((1 - p) / p) ** (1 / undulation))
    return finalize(size, p, m, top, undulation)


def kco_undulation(n: Any, x50: Any, xmax: Any) -> Any:
    """Swebrec undulation parameter implied by the Kuz-Ram uniformity index (KCO link).

    Parameters
    ----------
    n : float or array_like [1]
        Uniformity index, > 0.
    x50 : float or array_like [m]
        Median size, > 0 and below xmax.
    xmax : float or array_like [m]
        Largest size, > 0.

    Returns
    -------
    float or ndarray [1]
        Undulation parameter b.

    Equation
    --------
    b = 2 ln 2 ln(xmax / x50) n

    Source
    ------
    mutinda2021, eq. 6, p. 109

    Validity
    --------
    x50 >= xmax is an InputError naming x50.

    Knowledge rows
    --------------
    none
    """
    k = as_checked(n, "n", lo=0, lo_open=True)
    m = as_checked(x50, "x50", lo=0, lo_open=True)
    top = as_checked(xmax, "xmax", lo=0, lo_open=True)
    k, m, top = broadcast_all(n=k, x50=m, xmax=top)
    _check_x50_below_xmax(m, top)
    return finalize(2 * _LN2 * np.log(top / m) * k, k, m, top)


def kco_distribution(size: Any, x50: Any, xmax: Any, n: Any) -> Any:
    """Kuznetsov-Cunningham-Ouchterlony size distribution: the Swebrec curve with the KCO undulation parameter.

    Parameters
    ----------
    size : float or array_like [m]
        Sieve or particle size, > 0.
    x50 : float or array_like [m]
        Median size, > 0 and below xmax.
    xmax : float or array_like [m]
        Largest size, > 0.
    n : float or array_like [1]
        Kuz-Ram uniformity index, > 0.

    Returns
    -------
    float or ndarray [1]
        Fraction passing, from 0 to 1.

    Equation
    --------
    P = swebrec_passing(x, x50, xmax, b) with b = kco_undulation(n, x50, xmax).

    Source
    ------
    mutinda2021, eq. 6, p. 109

    Validity
    --------
    x50 >= xmax is an InputError naming x50.

    Knowledge rows
    --------------
    none
    """
    x = as_checked(size, "size", lo=0, lo_open=True)
    k = as_checked(n, "n", lo=0, lo_open=True)
    return swebrec_passing(x, x50, xmax, kco_undulation(k, x50, xmax))
