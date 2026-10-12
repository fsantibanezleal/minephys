"""Scaled distance, the square-root site law and the 30 CFR 816.67 limits (spec 002 FR-002-08, FR-002-09,
FR-002-18). Regulation values are knowledge rows in their published units and converted at the boundary."""

from __future__ import annotations

from typing import Any

import numpy as np

from .. import _tripwire as tw
from .. import knowledge, units
from .._validate import as_checked, broadcast_all, check_option, finalize

_STANDARDS = ("30cfr816.67",)


def _row(row_id: str) -> float:
    value = knowledge.get_value(row_id)
    assert not isinstance(value, tuple)
    return float(value)


def scaled_distance(distance: Any, charge_per_delay: Any) -> Any:
    """Square-root scaled distance of a blast.

    Parameters
    ----------
    distance : float or array_like [m]
        Distance from the blast to the receiver, > 0.
    charge_per_delay : float or array_like [kg]
        Maximum explosive mass detonated within one delay period, > 0.

    Returns
    -------
    float or ndarray [m/kg^0.5]
        Scaled distance.

    Equation
    --------
    SD = D / sqrt(W)

    Source
    ------
    cfr30_816_67, section 816.67(d)(3)

    Validity
    --------
    Square-root scaling (charge per delay), the form used by the regulation and the common site law.

    Knowledge rows
    --------------
    none
    """
    d = as_checked(distance, "distance", lo=0, lo_open=True)
    w = as_checked(charge_per_delay, "charge_per_delay", lo=0, lo_open=True)
    d, w = broadcast_all(distance=d, charge_per_delay=w)
    return finalize(d / np.sqrt(w), d, w)


def ppv_scaled_distance(distance: Any, charge_per_delay: Any, k_site: Any, beta: Any) -> Any:
    """Peak particle velocity from the square-root scaled-distance site law.

    Parameters
    ----------
    distance : float or array_like [m]
        Distance from the blast to the receiver, > 0.
    charge_per_delay : float or array_like [kg]
        Maximum explosive mass detonated within one delay period, > 0.
    k_site : float or array_like [m/s]
        Site constant: the PPV at a scaled distance of 1 m/kg^0.5, > 0 (no default: fit it on site data).
    beta : float or array_like [1]
        Site attenuation exponent, > 0 (no default).

    Returns
    -------
    float or ndarray [m/s]
        Peak particle velocity.

    Equation
    --------
    PPV = K (D / sqrt(W))^(-beta)

    Source
    ------
    cfr30_816_67, section 816.67(d)(3)

    Validity
    --------
    Site constants come from the user's own regression; k_site above tripwire_k_site_max (mm/s passed as m/s) emits a
    ValidityWarning.

    Knowledge rows
    --------------
    tripwire_k_site_max
    """
    d = as_checked(distance, "distance", lo=0, lo_open=True)
    w = as_checked(charge_per_delay, "charge_per_delay", lo=0, lo_open=True)
    k = as_checked(k_site, "k_site", lo=0, lo_open=True)
    b = as_checked(beta, "beta", lo=0, lo_open=True)
    d, w, k, b = broadcast_all(distance=d, charge_per_delay=w, k_site=k, beta=b)
    tw.warn_max(k, "k_site", "tripwire_k_site_max")
    with np.errstate(over="ignore", under="ignore"):
        ppv = k * (d / np.sqrt(w)) ** (-b)
    return finalize(ppv, d, w, k, b)


def _bands(distance_ft: Any) -> tuple[Any, Any]:
    """Boolean masks (near, far) of the three bands: D <= 300 ft, 300 ft < D <= 5,000 ft, D > 5,000 ft."""
    near = distance_ft <= _row("cfr_816_67_distance_band_near_max")
    far = distance_ft > _row("cfr_816_67_distance_band_mid_max")
    return near, far


def ppv_limit(distance: Any, standard: str = "30cfr816.67") -> Any:
    """Maximum allowed peak particle velocity of 30 CFR 816.67 at a distance.

    Parameters
    ----------
    distance : float or array_like [m]
        Distance from the blast to the nearest protected structure, > 0.
    standard : {"30cfr816.67"}
        Regulation; the only allowed value.

    Returns
    -------
    float or ndarray [m/s]
        Limit: 1.25, 1.00 and 0.75 in/s converted to m/s for D <= 300 ft, 300 ft < D <= 5,000 ft and D > 5,000 ft.

    Equation
    --------
    PPV_max = 1.25, 1.00 or 0.75 in/s by distance band (816.67(d)(2)(i)).

    Source
    ------
    cfr30_816_67, section 816.67(d)(2)(i)

    Validity
    --------
    Distances in feet are D / 0.3048 m; the bands are D <= 300 ft, 300 ft < D <= 5,000 ft and D > 5,000 ft.

    Knowledge rows
    --------------
    cfr_816_67_ppv_limit_near, cfr_816_67_ppv_limit_mid, cfr_816_67_ppv_limit_far, cfr_816_67_distance_band_near_max,
    cfr_816_67_distance_band_mid_max
    """
    d = as_checked(distance, "distance", lo=0, lo_open=True)
    check_option(standard, "standard", _STANDARDS)
    near, far = _bands(units.m_to_ft(d))
    in_per_s = np.where(
        near,
        _row("cfr_816_67_ppv_limit_near"),
        np.where(far, _row("cfr_816_67_ppv_limit_far"), _row("cfr_816_67_ppv_limit_mid")),
    )
    return finalize(units.in_per_s_to_m_per_s(in_per_s), d)


def max_charge_per_delay(distance: Any, standard: str = "30cfr816.67") -> Any:
    """Maximum charge per 8-millisecond period allowed by 30 CFR 816.67 at a distance.

    Parameters
    ----------
    distance : float or array_like [m]
        Distance from the blast to the nearest protected structure, > 0.
    standard : {"30cfr816.67"}
        Regulation; the only allowed value.

    Returns
    -------
    float or ndarray [kg]
        Maximum explosive mass per 8-millisecond period.

    Equation
    --------
    W = (D / Ds)^2 in lb with D in ft and Ds = 50, 55 or 65 ft/lb^0.5 by distance band (816.67(d)(3)(i)).

    Source
    ------
    cfr30_816_67, section 816.67(d)(3)(i)

    Validity
    --------
    The limit drops at each band edge because Ds grows from band to band; it is non-decreasing only within a band.

    Knowledge rows
    --------------
    cfr_816_67_scaled_distance_factor_near, cfr_816_67_scaled_distance_factor_mid,
    cfr_816_67_scaled_distance_factor_far, cfr_816_67_distance_band_near_max, cfr_816_67_distance_band_mid_max
    """
    d = as_checked(distance, "distance", lo=0, lo_open=True)
    check_option(standard, "standard", _STANDARDS)
    d_ft = units.m_to_ft(d)
    near, far = _bands(d_ft)
    factor = np.where(
        near,
        _row("cfr_816_67_scaled_distance_factor_near"),
        np.where(far, _row("cfr_816_67_scaled_distance_factor_far"), _row("cfr_816_67_scaled_distance_factor_mid")),
    )
    return finalize(units.lb_to_kg((d_ft / factor) ** 2), d)
