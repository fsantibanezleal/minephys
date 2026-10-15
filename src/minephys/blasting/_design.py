"""Blast design: charge, powder factor, the Kuz-Ram mean size, rock factor and the uniformity index (spec 002
FR-002-01 to FR-002-04, FR-002-14, FR-002-17, FR-002-18). Constants are knowledge rows."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import _tripwire as tw
from .. import knowledge
from .._errors import InputError
from .._validate import as_checked, as_float_array, broadcast_all, check_finite, check_option, finalize

_MM_PER_M = 1000
_PA_PER_GPA = 10**9
_PA_PER_MPA = 10**6
_CM_PER_M = 100
_VARIANTS = ("cunningham1983", "cunningham2005")


def _row(row_id: str) -> float:
    value = knowledge.get_value(row_id)
    assert not isinstance(value, tuple)
    return float(value)


def charge_per_hole(explosive_density: Any, hole_diameter: Any, charge_length: Any) -> Any:
    """Explosive mass in a cylindrical charge.

    Parameters
    ----------
    explosive_density : float or array_like [kg/m^3]
        Loaded density of the explosive, > 0.
    hole_diameter : float or array_like [m]
        Blasthole diameter, > 0.
    charge_length : float or array_like [m]
        Length of the explosive column, > 0.

    Returns
    -------
    float or ndarray [kg]
        Charge mass per hole.

    Equation
    --------
    Q = rho_e (pi / 4) d^2 L_c

    Source
    ------
    minephys:spec-002-blasting, section 3 (FR-002-01; cylinder volume times density)

    Validity
    --------
    hole_diameter > tripwire_hole_diameter_max (mm passed as m) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_hole_diameter_max
    """
    rho = as_checked(explosive_density, "explosive_density", lo=0, lo_open=True)
    d = as_checked(hole_diameter, "hole_diameter", lo=0, lo_open=True)
    length = as_checked(charge_length, "charge_length", lo=0, lo_open=True)
    rho, d, length = broadcast_all(explosive_density=rho, hole_diameter=d, charge_length=length)
    tw.warn_max(d, "hole_diameter", "tripwire_hole_diameter_max")
    return finalize(rho * (math.pi / 4) * d * d * length, rho, d, length)


def powder_factor(charge: Any, burden: Any, spacing: Any, bench_height: Any) -> Any:
    """Explosive mass per unit volume of rock blasted by one hole.

    Parameters
    ----------
    charge : float or array_like [kg]
        Explosive mass per hole, > 0.
    burden : float or array_like [m]
        Burden, > 0.
    spacing : float or array_like [m]
        Spacing, > 0.
    bench_height : float or array_like [m]
        Bench height, > 0 (subdrill excluded).

    Returns
    -------
    float or ndarray [kg/m^3]
        Powder factor.

    Equation
    --------
    K = Q / (B S H)

    Source
    ------
    minephys:spec-002-blasting, section 3 (FR-002-01; the bench-volume convention is stated in section 7.6)

    Validity
    --------
    Bench volume B S H per hole, subdrill excluded.

    Knowledge rows
    --------------
    none
    """
    q = as_checked(charge, "charge", lo=0, lo_open=True)
    b = as_checked(burden, "burden", lo=0, lo_open=True)
    s = as_checked(spacing, "spacing", lo=0, lo_open=True)
    h = as_checked(bench_height, "bench_height", lo=0, lo_open=True)
    q, b, s, h = broadcast_all(charge=q, burden=b, spacing=s, bench_height=h)
    return finalize(q / (b * s * h), q, b, s, h)


def kuznetsov_x50(rock_factor: Any, powder_factor: Any, charge: Any, rws: Any, variant: str = "cunningham1983") -> Any:
    """Kuznetsov mean fragment size (Kuz-Ram), with the 1983/1987 or the 2005 strength exponent.

    Parameters
    ----------
    rock_factor : float or array_like [1]
        Rock factor A, > 0 (Cunningham's range is 0.8 to 22).
    powder_factor : float or array_like [kg/m^3]
        Powder factor K, > 0.
    charge : float or array_like [kg]
        Explosive mass per hole Q, > 0.
    rws : float or array_like [1]
        Relative weight strength, ANFO = 100, > 0.
    variant : {"cunningham1983", "cunningham2005"}
        Strength exponent: 19/30 (default, UNVERIFIED secondary transcription) or 19/20 (verified).

    Returns
    -------
    float or ndarray [m]
        Mean fragment size x50.

    Equation
    --------
    x50 = A K^(-0.8) Q^(1/6) (115 / RWS)^e in cm, converted to m; e = 19/30 or 19/20.

    Source
    ------
    cunningham2005, eq. 1, p. 201

    Validity
    --------
    The default variant reads an UNVERIFIED row and emits UnverifiedParameterWarning; rock_factor outside 0.8 to 22,
    powder_factor above tripwire_powder_factor_max and rws below tripwire_rws_min emit a ValidityWarning.

    Knowledge rows
    --------------
    kuznetsov_powder_factor_exponent, kuznetsov_charge_exponent, kuznetsov_tnt_relative_weight_strength,
    kuzram_rws_exponent_2005, kuzram_rws_exponent_1983, kuzram_rock_factor_min, kuzram_rock_factor_max,
    tripwire_powder_factor_max, tripwire_rws_min
    """
    a = as_checked(rock_factor, "rock_factor", lo=0, lo_open=True)
    k = as_checked(powder_factor, "powder_factor", lo=0, lo_open=True)
    q = as_checked(charge, "charge", lo=0, lo_open=True)
    w = as_checked(rws, "rws", lo=0, lo_open=True)
    choice = check_option(variant, "variant", _VARIANTS)
    a, k, q, w = broadcast_all(rock_factor=a, powder_factor=k, charge=q, rws=w)
    tw.warn_min(a, "rock_factor", "kuzram_rock_factor_min")
    tw.warn_max(a, "rock_factor", "kuzram_rock_factor_max")
    tw.warn_max(k, "powder_factor", "tripwire_powder_factor_max")
    tw.warn_min(w, "rws", "tripwire_rws_min")
    exponent = _row("kuzram_rws_exponent_2005" if choice == "cunningham2005" else "kuzram_rws_exponent_1983")
    x50_cm = (
        a
        * k ** _row("kuznetsov_powder_factor_exponent")
        * q ** _row("kuznetsov_charge_exponent")
        * (_row("kuznetsov_tnt_relative_weight_strength") / w) ** exponent
    )
    return finalize(x50_cm / _CM_PER_M, a, k, q, w)


def rock_factor(rmd: Any, rdi: Any, hf: Any) -> Any:
    """Cunningham's rock factor from the three ratings.

    Parameters
    ----------
    rmd : float or array_like [1]
        Rock-mass description rating (joint ratings enter through it); finite.
    rdi : float or array_like [1]
        Rock density influence rating; finite and possibly negative for light rock.
    hf : float or array_like [1]
        Hardness factor; finite.

    Returns
    -------
    float or ndarray [1]
        Rock factor A.

    Equation
    --------
    A = 0.06 (RMD + RDI + HF)

    Source
    ------
    cunningham2005, eq. 4, p. 204

    Validity
    --------
    Cunningham's rock factor varies between 0.8 and 22; the check is made where A is used (kuznetsov_x50).

    Knowledge rows
    --------------
    kuzram_rock_factor_coefficient
    """
    r = check_finite(as_float_array(rmd, "rmd"), "rmd")
    d = check_finite(as_float_array(rdi, "rdi"), "rdi")
    h = check_finite(as_float_array(hf, "hf"), "hf")
    r, d, h = broadcast_all(rmd=r, rdi=d, hf=h)
    return finalize(_row("kuzram_rock_factor_coefficient") * (r + d + h), r, d, h)


def hardness_factor(youngs_modulus: Any, ucs: Any) -> Any:
    """Cunningham's hardness factor from the Young's modulus or the uniaxial compressive strength.

    Parameters
    ----------
    youngs_modulus : float or array_like [Pa]
        Young's modulus E, > 0.
    ucs : float or array_like [Pa]
        Uniaxial compressive strength, > 0.

    Returns
    -------
    float or ndarray [1]
        Hardness factor HF.

    Equation
    --------
    HF = E / 3 (E in GPa) when E < 50 GPa, else HF = UCS / 5 (UCS in MPa).

    Source
    ------
    cunningham2005, p. 205

    Validity
    --------
    The branch is chosen per element; the modulus is ignored from 50 GPa on.

    Knowledge rows
    --------------
    kuzram_hardness_modulus_divisor, kuzram_hardness_ucs_divisor, kuzram_hardness_modulus_switch
    """
    e = as_checked(youngs_modulus, "youngs_modulus", lo=0, lo_open=True)
    u = as_checked(ucs, "ucs", lo=0, lo_open=True)
    e, u = broadcast_all(youngs_modulus=e, ucs=u)
    e_gpa = e / _PA_PER_GPA
    soft = e_gpa < _row("kuzram_hardness_modulus_switch")
    hf = np.where(
        soft,
        e_gpa / _row("kuzram_hardness_modulus_divisor"),
        (u / _PA_PER_MPA) / _row("kuzram_hardness_ucs_divisor"),
    )
    return finalize(hf, e, u)


def rock_density_influence(density: Any) -> Any:
    """Cunningham's rock density influence rating.

    Parameters
    ----------
    density : float or array_like [kg/m^3]
        Rock density, > 0.

    Returns
    -------
    float or ndarray [1]
        Rating RDI (negative for light rock).

    Equation
    --------
    RDI = 0.025 rho - 50

    Source
    ------
    mutinda2021, eq. 5, p. 109

    Validity
    --------
    Secondary transcription: both rows are UNVERIFIED model constants, so every call emits UnverifiedParameterWarning.

    Knowledge rows
    --------------
    kuzram_rdi_density_coefficient, kuzram_rdi_offset
    """
    rho = as_checked(density, "density", lo=0, lo_open=True)
    return finalize(_row("kuzram_rdi_density_coefficient") * rho - _row("kuzram_rdi_offset"), rho)


def uniformity_index(
    burden: Any,
    spacing: Any,
    hole_diameter: Any,
    drilling_deviation: Any,
    charge_length: Any,
    bench_height: Any,
    bottom_charge_length: Any = None,
    column_charge_length: Any = None,
) -> Any:
    """Cunningham's uniformity index of the Kuz-Ram model (the 1987 form).

    Parameters
    ----------
    burden : float or array_like [m]
        Burden B, > 0.
    spacing : float or array_like [m]
        Spacing S, > 0.
    hole_diameter : float or array_like [m]
        Hole diameter d (converted to mm inside the formula), > 0.
    drilling_deviation : float or array_like [m]
        Standard deviation W of the drilling accuracy, >= 0 and below the burden.
    charge_length : float or array_like [m]
        Charge length L, > 0.
    bench_height : float or array_like [m]
        Bench height H, > 0.
    bottom_charge_length : float or array_like [m]
        Length of the bottom charge BCL, >= 0; None (with column_charge_length None) for a single explosive.
    column_charge_length : float or array_like [m]
        Length of the column charge CCL, >= 0; BCL + CCL must not exceed L.

    Returns
    -------
    float or ndarray [1]
        Uniformity index n.

    Equation
    --------
    n = (2.2 - 14 B / d) sqrt((1 + S / B) / 2) (1 - W / B) (|BCL - CCL| / L + 0.1)^0.1 L / H, d in mm.

    Source
    ------
    cunningham2005, eq. 3, p. 202

    Validity
    --------
    14 B / d < 2.2, W < B, BCL + CCL <= L; a result outside 0.8 to 1.5 (UNVERIFIED typical range) and a hole diameter
    above tripwire_hole_diameter_max emit a ValidityWarning.

    Knowledge rows
    --------------
    cunningham_n_constant, cunningham_n_burden_coefficient, cunningham_n_charge_offset, cunningham_n_charge_exponent,
    kuzram_uniformity_typical_min, kuzram_uniformity_typical_max, tripwire_hole_diameter_max
    """
    b = as_checked(burden, "burden", lo=0, lo_open=True)
    s = as_checked(spacing, "spacing", lo=0, lo_open=True)
    d = as_checked(hole_diameter, "hole_diameter", lo=0, lo_open=True)
    w = as_checked(drilling_deviation, "drilling_deviation", lo=0)
    length = as_checked(charge_length, "charge_length", lo=0, lo_open=True)
    h = as_checked(bench_height, "bench_height", lo=0, lo_open=True)
    if (bottom_charge_length is None) != (column_charge_length is None):
        missing = "column_charge_length" if column_charge_length is None else "bottom_charge_length"
        raise InputError(
            f"argument '{missing}' is required when the other column length is given (both or none)", argument=missing
        )
    single = bottom_charge_length is None
    bcl = length if single else as_checked(bottom_charge_length, "bottom_charge_length", lo=0)
    ccl = np.asarray(0.0) if single else as_checked(column_charge_length, "column_charge_length", lo=0)
    b, s, d, w, length, h, bcl, ccl = broadcast_all(
        burden=b,
        spacing=s,
        hole_diameter=d,
        drilling_deviation=w,
        charge_length=length,
        bench_height=h,
        bottom_charge_length=bcl,
        column_charge_length=ccl,
    )
    first = _row("cunningham_n_constant") - _row("cunningham_n_burden_coefficient") * b / (d * _MM_PER_M)
    if np.any(first <= 0):
        raise InputError(
            "the burden is too large for the hole diameter: 14 B / d must stay below 2.2", argument="burden"
        )
    if np.any(w >= b):
        raise InputError("argument 'drilling_deviation' must be smaller than the burden", argument="drilling_deviation")
    if not single and np.any(bcl + ccl > length):
        raise InputError(
            "argument 'column_charge_length': bottom plus column charge must not exceed charge_length",
            argument="column_charge_length",
        )
    tw.warn_max(d, "hole_diameter", "tripwire_hole_diameter_max")
    n = (
        first
        * np.sqrt((1 + s / b) / 2)
        * (1 - w / b)
        * (np.abs(bcl - ccl) / length + _row("cunningham_n_charge_offset")) ** _row("cunningham_n_charge_exponent")
        * length
        / h
    )
    tw.warn_min(n, "uniformity_index", "kuzram_uniformity_typical_min")
    tw.warn_max(n, "uniformity_index", "kuzram_uniformity_typical_max")
    return finalize(n, b, s, d, w, length, h, bcl, ccl)
