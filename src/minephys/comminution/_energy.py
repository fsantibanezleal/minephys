"""Bond's third law and the Morrell energy-size relation with its circuit terms (spec 005 FR-005-01 to FR-005-12,
-32, -33).

Sizes arrive in metres and leave the boundary in micrometres (one conversion per call); the sources publish their
constants
in micrometres, grams per revolution and kWh per tonne, so each function converts once and returns J/kg. Every
constant is
read from its knowledge row at call time (`knowledge.get_value`), so a replaced row changes the result.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .._errors import InputError
from .._validate import broadcast_all, check_option, finalize, warn_validity
from ._common import (
    G_PER_KG,
    UM_PER_M,
    FloatArray,
    finer_than,
    flag,
    kwh_per_t_in_si,
    positive,
    row,
)

__all__ = [
    "bond_ball_mill_work_index",
    "bond_energy",
    "bond_operating_work_index",
    "morrell_crusher",
    "morrell_energy",
    "morrell_hpgr",
    "morrell_mib",
    "morrell_size_distribution_correction",
    "morrell_tumbling_coarse",
    "morrell_tumbling_fine",
]

STAGES = ("primary", "secondary", "tertiary", "pebble")


def _bond_bracket(p_um: FloatArray, f_um: FloatArray) -> FloatArray:
    """The factor 10 (1/sqrt(P80) - 1/sqrt(F80)) of Bond's law, sizes in micrometres, coefficient from its row."""
    return row("bond_law_coefficient") * (1 / np.sqrt(p_um) - 1 / np.sqrt(f_um))


def _warn_bond_limit(p80: FloatArray) -> None:
    warn_validity(p80, "p80", row("bond_min_product_size") / UM_PER_M, np.inf, "bond_min_product_size", stacklevel=4)


def _warn_morrell_limit(p80: FloatArray) -> None:
    warn_validity(
        p80, "p80", row("morrell_fine_grind_limit") / UM_PER_M, np.inf, "morrell_fine_grind_limit", stacklevel=4
    )


def bond_energy(work_index: Any, f80: Any, p80: Any) -> Any:
    """Specific comminution energy by Bond's third law.

    Parameters
    ----------
    work_index : float or array [J/kg]
        Bond work index W_i (> 0); the result has the same unit.
    f80 : float or array [m]
        Feed 80 % passing size (> 0).
    p80 : float or array [m]
        Product 80 % passing size (> 0, finer than `f80`).

    Returns
    -------
    float or array [J/kg]
        Specific energy W (`numpy.float64` for scalar inputs).

    Equation
    --------
    W = 10 W_i (1/sqrt(P80) - 1/sqrt(F80)) with P80 and F80 in micrometres.

    Source
    ------
    mcivor2016bondgmsg p. 1 "Calculations" and worked examples p. 2 (Bond's original is bibliographic:
    bond1961crushing).

    Validity
    --------
    Applies down to a product size of about 70 micrometres; a finer p80 emits ValidityWarning (row
    bond_min_product_size)
    and the result is still returned.

    Knowledge rows
    --------------
    bond_law_coefficient, bond_min_product_size
    """
    wi, f, p = broadcast_all(
        work_index=positive(work_index, "work_index"), f80=positive(f80, "f80"), p80=positive(p80, "p80")
    )
    finer_than(p, f, "p80", "f80")
    _warn_bond_limit(p)
    return finalize(wi * _bond_bracket(p * UM_PER_M, f * UM_PER_M), wi, f, p)


def bond_operating_work_index(specific_energy: Any, f80: Any, p80: Any) -> Any:
    """Bond operating work index from a measured specific energy.

    Parameters
    ----------
    specific_energy : float or array [J/kg]
        Measured specific energy W (> 0).
    f80 : float or array [m]
        Feed 80 % passing size (> 0).
    p80 : float or array [m]
        Product 80 % passing size (> 0, finer than `f80`).

    Returns
    -------
    float or array [J/kg]
        Operating work index W_io in the unit of `specific_energy`.

    Equation
    --------
    W_io = W / (10/sqrt(P80) - 10/sqrt(F80)) with P80 and F80 in micrometres.

    Source
    ------
    mcivor2016bondgmsg p. 1 "Calculations"; worked examples pp. 1-2.

    Validity
    --------
    Applies down to a product size of about 70 micrometres; a finer p80 emits ValidityWarning (row
    bond_min_product_size).

    Knowledge rows
    --------------
    bond_law_coefficient, bond_min_product_size
    """
    w, f, p = broadcast_all(
        specific_energy=positive(specific_energy, "specific_energy"), f80=positive(f80, "f80"), p80=positive(p80, "p80")
    )
    finer_than(p, f, "p80", "f80")
    _warn_bond_limit(p)
    return finalize(w / _bond_bracket(p * UM_PER_M, f * UM_PER_M), w, f, p)


def bond_ball_mill_work_index(closing_screen: Any, grindability: Any, f80: Any, p80: Any) -> Any:
    """Bond ball-mill test work index from the laboratory test.

    Parameters
    ----------
    closing_screen : float or array [m]
        Closing screen size P1 of the test (> 0).
    grindability : float or array [kg per mill revolution]
        Net mass of product finer than the screen per revolution, G_bp (> 0).
    f80 : float or array [m]
        Test feed 80 % passing size (> 0).
    p80 : float or array [m]
        Test product 80 % passing size (> 0, finer than `f80`).

    Returns
    -------
    float or array [J/kg]
        Ball-mill work index per metric tonne.

    Equation
    --------
    W_i = 1.1025 * 44.5 / (P1^0.23 G_bp^0.82 (10/sqrt(P80) - 10/sqrt(F80))) kWh/t, P1, P80 and F80 in micrometres and
    G_bp
    in g/rev, converted to J/kg.

    Source
    ------
    mcivor2016bondgmsg p. 10 Annex C1 "Calculations" and the test sheet p. 11 (10.0 kWh/short ton = 11.0 kWh/t).

    Validity
    --------
    The published short-ton factor 1.1025 differs from the exact 1.10231 by 0.01 %, below the resolution of the test.

    Knowledge rows
    --------------
    bond_bm_constant, bond_bm_exponent_screen, bond_bm_exponent_grindability, bond_short_ton_to_metric,
    bond_law_coefficient
    """
    p1, g, f, p = broadcast_all(
        closing_screen=positive(closing_screen, "closing_screen"),
        grindability=positive(grindability, "grindability"),
        f80=positive(f80, "f80"),
        p80=positive(p80, "p80"),
    )
    finer_than(p, f, "p80", "f80")
    bracket = _bond_bracket(p * UM_PER_M, f * UM_PER_M)
    per_t = (
        row("bond_short_ton_to_metric")
        * row("bond_bm_constant")
        / (
            (p1 * UM_PER_M) ** row("bond_bm_exponent_screen")
            * (g * G_PER_KG) ** row("bond_bm_exponent_grindability")
            * bracket
        )
    )
    return finalize(per_t * kwh_per_t_in_si(), p1, g, f, p)


def _size_term(x_um: FloatArray) -> FloatArray:
    """x^f(x) with f(x) = -(0.295 + x / 1e6) of the Morrell relation (x in micrometres)."""
    return x_um ** -(row("morrell_f_constant") + x_um / row("morrell_f_scale"))


def _delta(x1_um: FloatArray, x2_um: FloatArray) -> FloatArray:
    """The size bracket 4 (x2^f(x2) - x1^f(x1)) of the Morrell relation; x2 is the finer size."""
    return row("morrell_coefficient") * (_size_term(x2_um) - _size_term(x1_um))


def morrell_energy(m_index: Any, x1: Any, x2: Any) -> Any:
    """Specific energy by the Morrell relation for a size reduction x1 to x2.

    Parameters
    ----------
    m_index : float or array [J/kg]
        Morrell index M_i for the stage (> 0).
    x1 : float or array [m]
        Feed 80 % passing size (> 0).
    x2 : float or array [m]
        Product 80 % passing size (> 0, finer than `x1`).

    Returns
    -------
    float or array [J/kg]
        Specific energy W.

    Equation
    --------
    W = M_i 4 (x2^f(x2) - x1^f(x1)), f(x) = -(0.295 + x/10^6), sizes in micrometres.

    Source
    ------
    gmsg2016morrell eq. 2, p. 2; one standard deviation of the method is 6.5 % of the relative errors (p. 3).

    Validity
    --------
    Educational reference values, valid inside the ranges of the cited guideline; not a design value.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_relative_error_sd
    """
    mi, a, b = broadcast_all(m_index=positive(m_index, "m_index"), x1=positive(x1, "x1"), x2=positive(x2, "x2"))
    finer_than(b, a, "x2", "x1")
    return finalize(mi * _delta(a * UM_PER_M, b * UM_PER_M), mi, a, b)


def morrell_tumbling_coarse(mia: Any, x1: Any, pebble_crusher: Any) -> Any:
    """Coarse tumbling-mill energy W_a of the Morrell method (from the feed size to the 750 micrometre boundary).

    Parameters
    ----------
    mia : float or array [J/kg]
        Morrell index M_ia (> 0).
    x1 : float or array [m]
        Feed 80 % passing size of the tumbling mill (> 0 and coarser than the 750 micrometre boundary).
    pebble_crusher : bool [flag]
        True when the circuit has a pebble crusher.

    Returns
    -------
    float or array [J/kg]
        Specific energy W_a.

    Equation
    --------
    W_a = K_1 M_ia 4 (750^f(750) - x1^f(x1)), K_1 = 0.95 with a pebble crusher and 1 otherwise, sizes in micrometres.

    Source
    ------
    gmsg2016morrell eqs. B2-B3, p. 6.

    Validity
    --------
    Defined for feeds coarser than the boundary (row morrell_coarse_fine_boundary); finer feeds raise InputError.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_coarse_fine_boundary, morrell_k1_pebble_crusher
    """
    m, x = broadcast_all(mia=positive(mia, "mia"), x1=positive(x1, "x1"))
    use_pebble = flag(pebble_crusher, "pebble_crusher")
    boundary = row("morrell_coarse_fine_boundary")
    x_um = x * UM_PER_M
    if not (x_um > boundary).all():
        raise InputError(f"argument 'x1' must be coarser than the {boundary!r} micrometre boundary", argument="x1")
    k1 = row("morrell_k1_pebble_crusher") if use_pebble else 1
    return finalize(k1 * m * _delta(x_um, np.full_like(x_um, boundary)), m, x)


def morrell_tumbling_fine(mib: Any, p80: Any) -> Any:
    """Fine tumbling-mill energy W_b of the Morrell method (from the 750 micrometre boundary to the final grind).

    Parameters
    ----------
    mib : float or array [J/kg]
        Morrell index M_ib (> 0).
    p80 : float or array [m]
        Final grind 80 % passing size (> 0 and finer than the 750 micrometre boundary).

    Returns
    -------
    float or array [J/kg]
        Specific energy W_b.

    Equation
    --------
    W_b = M_ib 4 (P80^f(P80) - 750^f(750)), sizes in micrometres.

    Source
    ------
    gmsg2016morrell eqs. B2-B3, p. 6; section B.1, p. 6 (applies down to approximately 45 micrometres).

    Validity
    --------
    A final grind finer than about 45 micrometres emits ValidityWarning (row morrell_fine_grind_limit); a grind of 750
    micrometres or coarser raises InputError.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_coarse_fine_boundary, morrell_fine_grind_limit
    """
    m, p = broadcast_all(mib=positive(mib, "mib"), p80=positive(p80, "p80"))
    boundary = row("morrell_coarse_fine_boundary")
    p_um = p * UM_PER_M
    if not (p_um < boundary).all():
        raise InputError(f"argument 'p80' must be finer than the {boundary!r} micrometre boundary", argument="p80")
    _warn_morrell_limit(p)
    return finalize(m * _delta(np.full_like(p_um, boundary), p_um), m, p)


def _size_factor(coefficient_row: str, x1_um: FloatArray, x2_um: FloatArray) -> FloatArray:
    """The size-dependent factor min(K (x1 x2)^-0.2, 1) of crushers and HPGRs."""
    return np.minimum(row(coefficient_row) * (x1_um * x2_um) ** row("morrell_s_exponent"), 1)


def morrell_crusher(mic: Any, x1: Any, x2: Any, closed_circuit: Any, stage: str) -> Any:
    """Crushing energy W_c of the Morrell method for one crushing stage.

    Parameters
    ----------
    mic : float or array [J/kg]
        Morrell index M_ic (> 0).
    x1 : float or array [m]
        Feed 80 % passing size (> 0).
    x2 : float or array [m]
        Product 80 % passing size (> 0, finer than `x1`).
    closed_circuit : bool [flag]
        True for a closed circuit (K_2 = 1), false for an open one.
    stage : str [option]
        "primary", "secondary", "tertiary" or "pebble"; the size factor applies to the first two.

    Returns
    -------
    float or array [J/kg]
        Specific energy W_c per tonne through the crusher.

    Equation
    --------
    W_c = S_c K_2 M_ic 4 (x2^f(x2) - x1^f(x1)), K_2 = 1 closed or 1.19 open, S_c = min(55 (x1 x2)^-0.2, 1) for
    primary and
    secondary stages and 1 for tertiary and pebble stages (sizes in micrometres).

    Source
    ------
    gmsg2016morrell eqs. B4-B5, pp. 6-7.

    Validity
    --------
    Educational reference values inside the ranges of the cited guideline.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_k2_open_circuit, morrell_ks_crusher,
    morrell_s_exponent
    """
    m, a, b = broadcast_all(mic=positive(mic, "mic"), x1=positive(x1, "x1"), x2=positive(x2, "x2"))
    closed = flag(closed_circuit, "closed_circuit")
    check_option(stage, "stage", STAGES)
    finer_than(b, a, "x2", "x1")
    a_um, b_um = a * UM_PER_M, b * UM_PER_M
    k2 = 1 if closed else row("morrell_k2_open_circuit")
    s = _size_factor("morrell_ks_crusher", a_um, b_um) if stage in ("primary", "secondary") else 1
    return finalize(s * k2 * m * _delta(a_um, b_um), m, a, b)


def morrell_hpgr(mih: Any, x1: Any, x2: Any, closed_circuit: Any) -> Any:
    """High-pressure grinding roll energy W_h of the Morrell method.

    Parameters
    ----------
    mih : float or array [J/kg]
        Morrell index M_ih (> 0).
    x1 : float or array [m]
        Feed 80 % passing size (> 0).
    x2 : float or array [m]
        Product 80 % passing size (> 0, finer than `x1`).
    closed_circuit : bool [flag]
        True for a closed circuit (K_3 = 1), false for an open one.

    Returns
    -------
    float or array [J/kg]
        Specific energy W_h.

    Equation
    --------
    W_h = S_h K_3 M_ih 4 (x2^f(x2) - x1^f(x1)), K_3 = 1 closed or 1.19 open, S_h = min(35 (x1 x2)^-0.2, 1).

    Source
    ------
    gmsg2016morrell eq. B6, p. 7 and section B.2.3, p. 7.

    Validity
    --------
    Educational reference values inside the ranges of the cited guideline.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_k3_open_circuit, morrell_ks_hpgr,
    morrell_s_exponent
    """
    m, a, b = broadcast_all(mih=positive(mih, "mih"), x1=positive(x1, "x1"), x2=positive(x2, "x2"))
    closed = flag(closed_circuit, "closed_circuit")
    finer_than(b, a, "x2", "x1")
    a_um, b_um = a * UM_PER_M, b * UM_PER_M
    k3 = 1 if closed else row("morrell_k3_open_circuit")
    return finalize(_size_factor("morrell_ks_hpgr", a_um, b_um) * k3 * m * _delta(a_um, b_um), m, a, b)


def morrell_size_distribution_correction(mia: Any, x1: Any, x2: Any) -> Any:
    """Size-distribution correction energy W_s of the Morrell method.

    Parameters
    ----------
    mia : float or array [J/kg]
        Morrell index M_ia (> 0).
    x1 : float or array [m]
        Circuit feed 80 % passing size (> 0).
    x2 : float or array [m]
        Ball-mill circuit feed 80 % passing size (> 0, finer than `x1`).

    Returns
    -------
    float or array [J/kg]
        Specific energy W_s.

    Equation
    --------
    W_s = 0.19 M_ia 4 (x2^f(x2) - x1^f(x1)), sizes in micrometres.

    Source
    ------
    gmsg2016morrell section B.2.4, p. 8.

    Validity
    --------
    Educational reference values inside the ranges of the cited guideline.

    Knowledge rows
    --------------
    morrell_coefficient, morrell_f_constant, morrell_f_scale, morrell_ws_factor
    """
    m, a, b = broadcast_all(mia=positive(mia, "mia"), x1=positive(x1, "x1"), x2=positive(x2, "x2"))
    finer_than(b, a, "x2", "x1")
    return finalize(row("morrell_ws_factor") * m * _delta(a * UM_PER_M, b * UM_PER_M), m, a, b)


def morrell_mib(closing_screen: Any, grindability: Any, f80: Any, p80: Any) -> Any:
    """Morrell fine-grinding index M_ib from a Bond ball-mill test.

    Parameters
    ----------
    closing_screen : float or array [m]
        Closing screen size P100 of the test (> 0).
    grindability : float or array [kg per mill revolution]
        Net mass of product finer than the screen per revolution, G_bp (> 0).
    f80 : float or array [m]
        Test feed 80 % passing size (> 0).
    p80 : float or array [m]
        Test product 80 % passing size (> 0, finer than `f80`).

    Returns
    -------
    float or array [J/kg]
        Index M_ib (kWh/t converted to J/kg).

    Equation
    --------
    M_ib = 18.18 / (P100^0.295 G_bp (P80^f(P80) - F80^f(F80))) kWh/t, sizes in micrometres and G_bp in g/rev.

    Source
    ------
    gmsg2016morrell eq. 1, p. 2.

    Validity
    --------
    Educational reference values inside the ranges of the cited guideline.

    Knowledge rows
    --------------
    morrell_mib_constant, morrell_mib_screen_exponent, morrell_f_constant, morrell_f_scale
    """
    p100, g, f, p = broadcast_all(
        closing_screen=positive(closing_screen, "closing_screen"),
        grindability=positive(grindability, "grindability"),
        f80=positive(f80, "f80"),
        p80=positive(p80, "p80"),
    )
    finer_than(p, f, "p80", "f80")
    p_um, f_um = p * UM_PER_M, f * UM_PER_M
    per_t = row("morrell_mib_constant") / (
        (p100 * UM_PER_M) ** row("morrell_mib_screen_exponent") * (g * G_PER_KG) * (_size_term(p_um) - _size_term(f_um))
    )
    return finalize(per_t * kwh_per_t_in_si(), p100, g, f, p)
