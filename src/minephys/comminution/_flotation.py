"""Flotation kinetics and the two-product formula (spec 005 FR-005-19 to FR-005-23)."""

from __future__ import annotations

import math
from typing import Any, NamedTuple

import numpy as np

from .._errors import InputError
from .._validate import broadcast_all, finalize
from ._common import FloatArray, count, non_negative, positive, unit_interval

__all__ = ["TwoProduct", "flotation_cell_recovery", "flotation_first_order", "klimpel_recovery", "two_product_recovery"]

_SERIES_TERMS = 20
# 1 - (1 - e^-u)/u = u/2 - u^2/6 + u^3/24 - ... = sum_k (-1)^(k+1) u^k / (k+1)!   (exact coefficients from integers)
_KLIMPEL = tuple((-1) ** (k + 1) / math.factorial(k + 1) for k in range(1, _SERIES_TERMS + 1))


class TwoProduct(NamedTuple):
    """Mass yield of the concentrate and recovery of the valuable component, both dimensionless."""

    mass_yield: Any
    recovery: Any


def flotation_first_order(r_inf: Any, k: Any, t: Any) -> Any:
    """First-order flotation recovery.

    Parameters
    ----------
    r_inf : float or array [fraction]
        Ultimate recovery R_inf, in (0, 1].
    k : float or array [1/s]
        Rate constant (> 0).
    t : float or array [s]
        Flotation time (>= 0).

    Returns
    -------
    float or array [fraction]
        Recovery R(t).

    Equation
    --------
    R = R_inf (1 - exp(-k t)).

    Source
    ------
    wills2016 (textbook form, not read: the oracle is the hand calculation of spec 005 section 7); gharai2016flotation
    (review, not read).

    Validity
    --------
    Recovery depends on k and t only through the product k t.

    Knowledge rows
    --------------
    none
    """
    r, rate, time = broadcast_all(
        r_inf=unit_interval(r_inf, "r_inf", lo_open=True), k=positive(k, "k"), t=non_negative(t, "t")
    )
    return finalize(r * -np.expm1(-rate * time), r, rate, time)


def _klimpel_factor(u: FloatArray) -> FloatArray:
    """1 - (1 - exp(-u)) / u without cancellation: a series for u < 1, the closed form above."""
    acc = np.full_like(u, _KLIMPEL[-1])
    for coefficient in reversed(_KLIMPEL[:-1]):
        acc = acc * u + coefficient
    series = acc * u
    with np.errstate(divide="ignore", invalid="ignore"):
        closed = 1 + np.expm1(-u) / u
    return np.where(u < 1, series, closed)


def klimpel_recovery(r_inf: Any, k: Any, t: Any) -> Any:
    """Klimpel flotation recovery (first-order recovery averaged over a uniform rate distribution on [0, k]).

    Parameters
    ----------
    r_inf : float or array [fraction]
        Ultimate recovery R_inf, in (0, 1].
    k : float or array [1/s]
        Maximum rate constant (> 0).
    t : float or array [s]
        Flotation time (>= 0).

    Returns
    -------
    float or array [fraction]
        Recovery R(t), zero at t = 0.

    Equation
    --------
    R = R_inf [1 - (1 - exp(-k t)) / (k t)].

    Source
    ------
    gharai2016flotation (review transcription, not read: UNVERIFIED); the form is derived in spec 005 section 7.

    Validity
    --------
    Series evaluation for k t < 1 keeps full precision for small k t.

    Knowledge rows
    --------------
    none
    """
    r, rate, time = broadcast_all(
        r_inf=unit_interval(r_inf, "r_inf", lo_open=True), k=positive(k, "k"), t=non_negative(t, "t")
    )
    return finalize(r * _klimpel_factor(rate * time), r, rate, time)


def flotation_cell_recovery(r_inf: Any, k: Any, tau: Any, n_cells: Any = 1) -> Any:
    """Recovery of equal perfectly mixed cells in series.

    Parameters
    ----------
    r_inf : float or array [fraction]
        Ultimate recovery R_inf, in (0, 1].
    k : float or array [1/s]
        Rate constant (> 0).
    tau : float or array [s]
        Mean residence time of each cell (> 0).
    n_cells : int [count]
        Number of cells in series (>= 1).

    Returns
    -------
    float or array [fraction]
        Recovery of the bank.

    Equation
    --------
    R = R_inf [1 - (1 + k tau)^(-N)], for one cell R_inf k tau / (1 + k tau).

    Source
    ------
    wills2016 (textbook form, not read); the form is derived in spec 005 section 7 by integrating the first-order law
    against
    an exponential residence-time distribution (UNVERIFIED).

    Validity
    --------
    As N grows with N tau fixed the recovery tends to the first-order recovery.

    Knowledge rows
    --------------
    none
    """
    r, rate, res = broadcast_all(
        r_inf=unit_interval(r_inf, "r_inf", lo_open=True), k=positive(k, "k"), tau=positive(tau, "tau")
    )
    n = count(n_cells, "n_cells")
    return finalize(r * -np.expm1(-n * np.log1p(rate * res)), r, rate, res)


def two_product_recovery(feed_grade: Any, concentrate_grade: Any, tail_grade: Any) -> TwoProduct:
    """Two-product formula: concentrate mass yield and recovery from the three grades.

    Parameters
    ----------
    feed_grade : float or array [grade, any one unit]
        Feed grade f.
    concentrate_grade : float or array [grade, same unit]
        Concentrate grade c (> f).
    tail_grade : float or array [grade, same unit]
        Tailings grade t (>= 0, < f).

    Returns
    -------
    TwoProduct [1]
        `mass_yield` C/F and `recovery` R, both dimensionless fractions.

    Equation
    --------
    C/F = (f - t)/(c - t), R = c (f - t) / (f (c - t)).

    Source
    ------
    wills2016 (textbook form, not read: the oracle is the hand calculation of spec 005 section 7).

    Validity
    --------
    Requires 0 <= t < f < c; real assays outside this order are rejected instead of returning a recovery outside [0, 1].

    Knowledge rows
    --------------
    none
    """
    f, c, t = broadcast_all(
        feed_grade=non_negative(feed_grade, "feed_grade"),
        concentrate_grade=non_negative(concentrate_grade, "concentrate_grade"),
        tail_grade=non_negative(tail_grade, "tail_grade"),
    )
    for lower, upper, name in ((t, f, "tail_grade"), (f, c, "feed_grade")):
        bad = ~(lower < upper)
        if bad.any():
            raise InputError("the grades must satisfy 0 <= tail_grade < feed_grade < concentrate_grade", argument=name)
    yield_ = (f - t) / (c - t)
    return TwoProduct(finalize(yield_, f, c, t), finalize(c * (f - t) / (f * (c - t)), f, c, t))
