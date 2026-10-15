"""Generalised Hoek-Brown criterion and its equivalent Mohr-Coulomb parameters (spec 003 FR-003-01 to FR-003-06,
FR-003-20, FR-003-21, FR-003-24). Constants are knowledge rows."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import _tripwire as tw
from .. import knowledge
from .._errors import InputError
from .._validate import (
    FloatArray,
    as_checked,
    as_float_array,
    broadcast_all,
    check_finite,
    check_option,
    finalize,
)

_APPLICATIONS = ("slope", "tunnel")
_CUTOFF_GUARD = 1e-12  # rounding allowance, relative to the tensile strength, for sigma3 exactly at the cut-off
_A_MIN = 1 / 2
_A_MAX = 2 / 3


def _row(row_id: str) -> float:
    value = knowledge.get_value(row_id)
    assert not isinstance(value, tuple)
    return float(value)


def _sigma_ci(value: Any) -> FloatArray:
    return as_checked(value, "sigma_ci", lo=0, lo_open=True)


def _hb_arguments(mb: Any, s: Any, a: Any) -> tuple[FloatArray, FloatArray, FloatArray]:
    return (
        as_checked(mb, "mb", lo=0, lo_open=True),
        as_checked(s, "s", lo=0, hi=1, lo_open=True),
        as_checked(a, "a", lo=_A_MIN, hi=_A_MAX),
    )


def _warn_sigma_ci(sigma_ci: FloatArray) -> None:
    tw.warn_min(sigma_ci, "sigma_ci", "tripwire_sigma_ci_min")
    tw.warn_max(sigma_ci, "sigma_ci", "tripwire_sigma_ci_max")


def hoek_brown_parameters(gsi: Any, mi: Any, disturbance: Any) -> tuple[Any, Any, Any]:
    """Generalised Hoek-Brown parameters of a rock mass.

    Parameters
    ----------
    gsi : float or array_like [1]
        Geological Strength Index, 0 < GSI <= 100.
    mi : float or array_like [1]
        Intact-rock parameter m_i, > 0.
    disturbance : float or array_like [1]
        Disturbance factor D, 0 <= D <= 1 (no default: it is a site judgement).

    Returns
    -------
    tuple of float or ndarray [1]
        (mb, s, a): the rock-mass constants m_b, s and a.

    Equation
    --------
    mb = mi exp((GSI - 100) / (28 - 14 D)); s = exp((GSI - 100) / (9 - 3 D)); a = 1/2 + (exp(-GSI/15) - exp(-20/3)) / 6.

    Source
    ------
    hoek2002, eq. 3 to 5, pp. 267-268

    Validity
    --------
    The 2002 edition; identical in Hoek and Brown 2019 (hoek2019). GSI = 100 and D = 0 give s = 1, mb = mi, a = 1/2.

    Knowledge rows
    --------------
    hb_mb_gsi_denominator_constant, hb_mb_disturbance_coefficient, hb_s_gsi_denominator_constant,
    hb_s_disturbance_coefficient, hb_a_gsi_scale, hb_a_offset_exponent
    """
    g = as_checked(gsi, "gsi", lo=0, hi=100, lo_open=True)
    m = as_checked(mi, "mi", lo=0, lo_open=True)
    d = as_checked(disturbance, "disturbance", lo=0, hi=1)
    g, m, d = broadcast_all(gsi=g, mi=m, disturbance=d)
    drop = g - 100
    mb = m * np.exp(drop / (_row("hb_mb_gsi_denominator_constant") - _row("hb_mb_disturbance_coefficient") * d))
    s = np.exp(drop / (_row("hb_s_gsi_denominator_constant") - _row("hb_s_disturbance_coefficient") * d))
    a = 1 / 2 + (np.exp(-g / _row("hb_a_gsi_scale")) - math.exp(-_row("hb_a_offset_exponent"))) / 6
    return finalize(mb, g, m, d), finalize(s, g, m, d), finalize(a, g, m, d)


def hoek_brown_sigma1(sigma3: Any, sigma_ci: Any, mb: Any, s: Any, a: Any) -> Any:
    """Major principal stress at failure of the generalised Hoek-Brown criterion.

    Parameters
    ----------
    sigma3 : float or array_like [Pa]
        Minor principal (confining) stress, not below the tensile strength -s sigma_ci / mb.
    sigma_ci : float or array_like [Pa]
        Uniaxial compressive strength of the intact rock, > 0.
    mb : float or array_like [1]
        Rock-mass constant m_b, > 0.
    s : float or array_like [1]
        Rock-mass constant s, 0 < s <= 1.
    a : float or array_like [1]
        Rock-mass constant a, 1/2 <= a <= 2/3.

    Returns
    -------
    float or ndarray [Pa]
        Major principal stress sigma1 at failure.

    Equation
    --------
    sigma1 = sigma3 + sigma_ci (mb sigma3 / sigma_ci + s)^a

    Source
    ------
    hoek2002, eq. 2, p. 267

    Validity
    --------
    sigma3 below the tensile strength makes the base of the power negative (InputError naming sigma3);
    sigma_ci outside tripwire_sigma_ci_min and tripwire_sigma_ci_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_sigma_ci_min, tripwire_sigma_ci_max
    """
    s3 = check_finite(as_float_array(sigma3, "sigma3"), "sigma3")
    ci = _sigma_ci(sigma_ci)
    m, sv, av = _hb_arguments(mb, s, a)
    s3, ci, m, sv, av = broadcast_all(sigma3=s3, sigma_ci=ci, mb=m, s=sv, a=av)
    _warn_sigma_ci(ci)
    tensile = -sv * ci / m  # the same expression as hoek_brown_tensile_strength
    if np.any(s3 < tensile - _CUTOFF_GUARD * np.abs(tensile)):
        raise InputError(
            "argument 'sigma3' lies below the tensile strength -s sigma_ci / mb: the base of the power is negative",
            argument="sigma3",
        )
    base = m * (s3 - tensile) / ci  # = mb sigma3 / sigma_ci + s, exactly zero at the tensile strength
    return finalize(s3 + ci * np.maximum(base, 0) ** av, s3, ci, m, sv, av)


def hoek_brown_uniaxial_strength(sigma_ci: Any, s: Any, a: Any) -> Any:
    """Uniaxial compressive strength of the rock mass.

    Parameters
    ----------
    sigma_ci : float or array_like [Pa]
        Uniaxial compressive strength of the intact rock, > 0.
    s : float or array_like [1]
        Rock-mass constant s, 0 < s <= 1.
    a : float or array_like [1]
        Rock-mass constant a, 1/2 <= a <= 2/3.

    Returns
    -------
    float or ndarray [Pa]
        Uniaxial compressive strength sigma_c of the rock mass.

    Equation
    --------
    sigma_c = sigma_ci s^a

    Source
    ------
    hoek2002, eq. 6, p. 267

    Validity
    --------
    sigma_ci outside tripwire_sigma_ci_min and tripwire_sigma_ci_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_sigma_ci_min, tripwire_sigma_ci_max
    """
    ci = _sigma_ci(sigma_ci)
    sv = as_checked(s, "s", lo=0, hi=1, lo_open=True)
    av = as_checked(a, "a", lo=_A_MIN, hi=_A_MAX)
    ci, sv, av = broadcast_all(sigma_ci=ci, s=sv, a=av)
    _warn_sigma_ci(ci)
    return finalize(ci * sv**av, ci, sv, av)


def hoek_brown_tensile_strength(sigma_ci: Any, mb: Any, s: Any) -> Any:
    """Tensile strength of the rock mass (a negative stress).

    Parameters
    ----------
    sigma_ci : float or array_like [Pa]
        Uniaxial compressive strength of the intact rock, > 0.
    mb : float or array_like [1]
        Rock-mass constant m_b, > 0.
    s : float or array_like [1]
        Rock-mass constant s, 0 < s <= 1.

    Returns
    -------
    float or ndarray [Pa]
        Tensile strength sigma_t (negative).

    Equation
    --------
    sigma_t = -s sigma_ci / mb

    Source
    ------
    hoek2002, eq. 7, p. 267

    Validity
    --------
    sigma_ci outside tripwire_sigma_ci_min and tripwire_sigma_ci_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_sigma_ci_min, tripwire_sigma_ci_max
    """
    ci = _sigma_ci(sigma_ci)
    m = as_checked(mb, "mb", lo=0, lo_open=True)
    sv = as_checked(s, "s", lo=0, hi=1, lo_open=True)
    ci, m, sv = broadcast_all(sigma_ci=ci, mb=m, s=sv)
    _warn_sigma_ci(ci)
    return finalize(-sv * ci / m, ci, m, sv)


def hoek_brown_rock_mass_strength(sigma_ci: Any, mb: Any, s: Any, a: Any) -> Any:
    """Global rock-mass strength (Hoek-Diederichs form of the 2002 edition).

    Parameters
    ----------
    sigma_ci : float or array_like [Pa]
        Uniaxial compressive strength of the intact rock, > 0.
    mb : float or array_like [1]
        Rock-mass constant m_b, > 0.
    s : float or array_like [1]
        Rock-mass constant s, 0 < s <= 1.
    a : float or array_like [1]
        Rock-mass constant a, 1/2 <= a <= 2/3.

    Returns
    -------
    float or ndarray [Pa]
        Rock-mass strength sigma_cm.

    Equation
    --------
    sigma_cm = sigma_ci (mb + 4 s - a (mb - 8 s)) (mb / 4 + s)^(a - 1) / (2 (1 + a) (2 + a))

    Source
    ------
    hoek2002, eq. 17, p. 270

    Validity
    --------
    sigma_ci outside tripwire_sigma_ci_min and tripwire_sigma_ci_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_sigma_ci_min, tripwire_sigma_ci_max
    """
    ci = _sigma_ci(sigma_ci)
    m, sv, av = _hb_arguments(mb, s, a)
    ci, m, sv, av = broadcast_all(sigma_ci=ci, mb=m, s=sv, a=av)
    _warn_sigma_ci(ci)
    strength = ci * (m + 4 * sv - av * (m - 8 * sv)) * (m / 4 + sv) ** (av - 1) / (2 * (1 + av) * (2 + av))
    return finalize(strength, ci, m, sv, av)


def equivalent_mohr_coulomb(sigma_ci: Any, mb: Any, s: Any, a: Any, sigma3_max: Any) -> tuple[Any, Any]:
    """Equivalent Mohr-Coulomb cohesion and friction angle of a Hoek-Brown rock mass.

    Parameters
    ----------
    sigma_ci : float or array_like [Pa]
        Uniaxial compressive strength of the intact rock, > 0.
    mb : float or array_like [1]
        Rock-mass constant m_b, > 0.
    s : float or array_like [1]
        Rock-mass constant s, 0 < s <= 1.
    a : float or array_like [1]
        Rock-mass constant a, 1/2 <= a <= 2/3.
    sigma3_max : float or array_like [Pa]
        Upper limit of the confining stress of the fit (see the function sigma3_max), >= 0.

    Returns
    -------
    tuple of float or ndarray [Pa]
        (cohesion [Pa], friction_angle [rad]).

    Equation
    --------
    With s3n = sigma3_max / sigma_ci and t = s + mb s3n: phi' = asin(6 a mb t^(a-1) / (2 (1 + a) (2 + a) + 6 a mb
    t^(a-1))) and c' = sigma_ci ((1 + 2 a) s + (1 - a) mb s3n) t^(a-1) / ((1 + a) (2 + a) sqrt(1 + 6 a mb t^(a-1) /
    ((1 + a) (2 + a)))).

    Source
    ------
    hoek2002, eq. 12 and 13, p. 269

    Validity
    --------
    An approximation over the stress range 0 to sigma3_max; sigma_ci outside its tripwires emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_sigma_ci_min, tripwire_sigma_ci_max
    """
    ci = _sigma_ci(sigma_ci)
    m, sv, av = _hb_arguments(mb, s, a)
    s3 = as_checked(sigma3_max, "sigma3_max", lo=0)
    ci, m, sv, av, s3 = broadcast_all(sigma_ci=ci, mb=m, s=sv, a=av, sigma3_max=s3)
    _warn_sigma_ci(ci)
    s3n = s3 / ci
    power = (sv + m * s3n) ** (av - 1)
    x = 6 * av * m * power
    phi = np.arcsin(x / (2 * (1 + av) * (2 + av) + x))
    cohesion = (
        ci
        * ((1 + 2 * av) * sv + (1 - av) * m * s3n)
        * power
        / ((1 + av) * (2 + av) * np.sqrt(1 + x / ((1 + av) * (2 + av))))
    )
    return finalize(cohesion, ci, m, sv, av, s3), finalize(phi, ci, m, sv, av, s3)


def sigma3_max(sigma_cm: Any, unit_weight: Any, height: Any, application: str) -> Any:
    """Upper limit of the confining stress for the Hoek-Brown to Mohr-Coulomb fit.

    Parameters
    ----------
    sigma_cm : float or array_like [Pa]
        Rock-mass strength, > 0.
    unit_weight : float or array_like [N/m^3]
        Unit weight of the rock mass, > 0.
    height : float or array_like [m]
        Slope height (slopes) or depth below surface (tunnels), > 0.
    application : {"slope", "tunnel"}
        The kind of excavation.

    Returns
    -------
    float or ndarray [Pa]
        sigma3_max.

    Equation
    --------
    sigma3_max = sigma_cm 0.72 (sigma_cm / (gamma H))^(-0.91) for a slope; sigma_cm 0.47 (sigma_cm / (gamma H))^(-0.94)
    for a tunnel.

    Source
    ------
    hoek2002, eq. 18 and 19, p. 270

    Validity
    --------
    unit_weight below tripwire_unit_weight_min (kN/m^3 passed as N/m^3) emits a ValidityWarning.

    Knowledge rows
    --------------
    hb_sigma3max_slope_coefficient, hb_sigma3max_slope_exponent, hb_sigma3max_tunnel_coefficient,
    hb_sigma3max_tunnel_exponent, tripwire_unit_weight_min
    """
    cm = as_checked(sigma_cm, "sigma_cm", lo=0, lo_open=True)
    gamma = as_checked(unit_weight, "unit_weight", lo=0, lo_open=True)
    h = as_checked(height, "height", lo=0, lo_open=True)
    kind = check_option(application, "application", _APPLICATIONS)
    cm, gamma, h = broadcast_all(sigma_cm=cm, unit_weight=gamma, height=h)
    tw.warn_min(gamma, "unit_weight", "tripwire_unit_weight_min")
    prefix = f"hb_sigma3max_{kind}"
    ratio = cm / (gamma * h)
    return finalize(cm * _row(f"{prefix}_coefficient") * ratio ** _row(f"{prefix}_exponent"), cm, gamma, h)
