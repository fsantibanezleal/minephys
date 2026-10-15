"""ISC3 dispersion coefficients, the Gaussian plume and line sources (spec 006 FR-006-09 to FR-006-14)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .._argcheck import FloatArray, non_negative, positive, row
from .._errors import InputError
from .._validate import as_float_array, broadcast_all, check_finite, check_option, finalize, warn_validity

__all__ = ["finite_line_source_plume", "gaussian_plume", "line_source_plume", "pasquill_sigmas"]

CLASSES = ("A", "B", "C", "D", "E", "F")
TERRAINS = ("rural", "urban")
CAPPED = ("A", "B", "C")
M_PER_KM = 1000
MAX_IMAGE_TERMS = 1000
_TINY = 1e-16
_erf = np.vectorize(math.erf, otypes=[np.float64])


def _band_rows(cls: str) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Upper distances (km, infinity for the open band), a and b of the Table 1-2 bands of a class, read from the
    rows."""
    uppers: list[float] = []
    a_s: list[float] = []
    b_s: list[float] = []
    k = 1
    while True:
        try:
            a = row(f"isc3_pg_sigma_z_{cls}_{k}_a")
        except InputError:
            break
        a_s.append(a)
        b_s.append(row(f"isc3_pg_sigma_z_{cls}_{k}_b"))
        try:
            uppers.append(row(f"isc3_pg_sigma_z_{cls}_{k}_xmax"))
        except InputError:
            uppers.append(math.inf)
        k += 1
    return np.array(uppers), np.array(a_s), np.array(b_s)


def pasquill_sigmas(x: Any, stability_class: str, terrain: str = "rural") -> tuple[Any, Any]:
    """Lateral and vertical dispersion coefficients of the ISC3 model.

    Parameters
    ----------
    x : float or array [m]
        Downwind distance (> 0).
    stability_class : str [option]
        Pasquill stability class, exactly "A" to "F".
    terrain : str [option]
        "rural" (Pasquill-Gifford fits of ISC3 Tables 1-1 and 1-2) or "urban" (Briggs, Tables 1-3 and 1-4).

    Returns
    -------
    tuple of float or array [m]
        (sigma_y, sigma_z).

    Equation
    --------
    Rural: sigma_y = 465.11628 x_km tan(0.017453293 (c - d ln x_km)), sigma_z = a x_km^b with the distance band of
    Table 1-2
    (capped at 5000 m for classes A, B, C). Urban: sigma = coef x (1 + slope x)^exponent with x in metres.

    Source
    ------
    epa1995isc3v2 eqs. 1-32 and 1-33, p. 1-14, Table 1-1 p. 1-16, Table 1-2 pp. 1-17 and 1-18, Tables 1-3 and 1-4 p.
    1-19;
    turner1970workbook (original curves, bibliographic).

    Validity
    --------
    Band k applies for x_km above the previous upper distance and up to its own. Urban concentrations closer than 100
    m may be
    suspect: a smaller x emits ValidityWarning (row isc3_urban_min_distance).

    Knowledge rows
    --------------
    isc3_sigma_y_scale, isc3_deg_to_rad, isc3_pg_sigma_y_c_a, isc3_pg_sigma_y_c_b, isc3_pg_sigma_y_c_c,
    isc3_pg_sigma_y_c_d, isc3_pg_sigma_y_c_e, isc3_pg_sigma_y_c_f, isc3_pg_sigma_y_d_a, isc3_pg_sigma_y_d_b,
    isc3_pg_sigma_y_d_c, isc3_pg_sigma_y_d_d, isc3_pg_sigma_y_d_e, isc3_pg_sigma_y_d_f, isc3_pg_sigma_z_a_1_xmax,
    isc3_pg_sigma_z_a_2_xmax, isc3_pg_sigma_z_a_3_xmax, isc3_pg_sigma_z_a_4_xmax, isc3_pg_sigma_z_a_5_xmax,
    isc3_pg_sigma_z_a_6_xmax, isc3_pg_sigma_z_a_7_xmax, isc3_pg_sigma_z_a_8_xmax, isc3_pg_sigma_z_a_1_a,
    isc3_pg_sigma_z_a_2_a, isc3_pg_sigma_z_a_3_a, isc3_pg_sigma_z_a_4_a, isc3_pg_sigma_z_a_5_a,
    isc3_pg_sigma_z_a_6_a, isc3_pg_sigma_z_a_7_a, isc3_pg_sigma_z_a_8_a, isc3_pg_sigma_z_a_9_a,
    isc3_pg_sigma_z_a_1_b, isc3_pg_sigma_z_a_2_b, isc3_pg_sigma_z_a_3_b, isc3_pg_sigma_z_a_4_b,
    isc3_pg_sigma_z_a_5_b, isc3_pg_sigma_z_a_6_b, isc3_pg_sigma_z_a_7_b, isc3_pg_sigma_z_a_8_b,
    isc3_pg_sigma_z_a_9_b, isc3_pg_sigma_z_b_1_xmax, isc3_pg_sigma_z_b_2_xmax, isc3_pg_sigma_z_b_1_a,
    isc3_pg_sigma_z_b_2_a, isc3_pg_sigma_z_b_3_a, isc3_pg_sigma_z_b_1_b, isc3_pg_sigma_z_b_2_b,
    isc3_pg_sigma_z_b_3_b, isc3_pg_sigma_z_c_1_a, isc3_pg_sigma_z_c_1_b, isc3_pg_sigma_z_d_1_xmax,
    isc3_pg_sigma_z_d_2_xmax, isc3_pg_sigma_z_d_3_xmax, isc3_pg_sigma_z_d_4_xmax, isc3_pg_sigma_z_d_5_xmax,
    isc3_pg_sigma_z_d_1_a, isc3_pg_sigma_z_d_2_a, isc3_pg_sigma_z_d_3_a, isc3_pg_sigma_z_d_4_a,
    isc3_pg_sigma_z_d_5_a, isc3_pg_sigma_z_d_6_a, isc3_pg_sigma_z_d_1_b, isc3_pg_sigma_z_d_2_b,
    isc3_pg_sigma_z_d_3_b, isc3_pg_sigma_z_d_4_b, isc3_pg_sigma_z_d_5_b, isc3_pg_sigma_z_d_6_b,
    isc3_pg_sigma_z_e_1_xmax, isc3_pg_sigma_z_e_2_xmax, isc3_pg_sigma_z_e_3_xmax, isc3_pg_sigma_z_e_4_xmax,
    isc3_pg_sigma_z_e_5_xmax, isc3_pg_sigma_z_e_6_xmax, isc3_pg_sigma_z_e_7_xmax, isc3_pg_sigma_z_e_8_xmax,
    isc3_pg_sigma_z_e_1_a, isc3_pg_sigma_z_e_2_a, isc3_pg_sigma_z_e_3_a, isc3_pg_sigma_z_e_4_a,
    isc3_pg_sigma_z_e_5_a, isc3_pg_sigma_z_e_6_a, isc3_pg_sigma_z_e_7_a, isc3_pg_sigma_z_e_8_a,
    isc3_pg_sigma_z_e_9_a, isc3_pg_sigma_z_e_1_b, isc3_pg_sigma_z_e_2_b, isc3_pg_sigma_z_e_3_b,
    isc3_pg_sigma_z_e_4_b, isc3_pg_sigma_z_e_5_b, isc3_pg_sigma_z_e_6_b, isc3_pg_sigma_z_e_7_b,
    isc3_pg_sigma_z_e_8_b, isc3_pg_sigma_z_e_9_b, isc3_pg_sigma_z_f_1_xmax, isc3_pg_sigma_z_f_2_xmax,
    isc3_pg_sigma_z_f_3_xmax, isc3_pg_sigma_z_f_4_xmax, isc3_pg_sigma_z_f_5_xmax, isc3_pg_sigma_z_f_6_xmax,
    isc3_pg_sigma_z_f_7_xmax, isc3_pg_sigma_z_f_8_xmax, isc3_pg_sigma_z_f_9_xmax, isc3_pg_sigma_z_f_1_a,
    isc3_pg_sigma_z_f_2_a, isc3_pg_sigma_z_f_3_a, isc3_pg_sigma_z_f_4_a, isc3_pg_sigma_z_f_5_a,
    isc3_pg_sigma_z_f_6_a, isc3_pg_sigma_z_f_7_a, isc3_pg_sigma_z_f_8_a, isc3_pg_sigma_z_f_9_a,
    isc3_pg_sigma_z_f_10_a, isc3_pg_sigma_z_f_1_b, isc3_pg_sigma_z_f_2_b, isc3_pg_sigma_z_f_3_b,
    isc3_pg_sigma_z_f_4_b, isc3_pg_sigma_z_f_5_b, isc3_pg_sigma_z_f_6_b, isc3_pg_sigma_z_f_7_b,
    isc3_pg_sigma_z_f_8_b, isc3_pg_sigma_z_f_9_b, isc3_pg_sigma_z_f_10_b, isc3_sigma_z_cap,
    isc3_briggs_urban_y_a_coef, isc3_briggs_urban_y_a_slope, isc3_briggs_urban_y_a_exponent,
    isc3_briggs_urban_y_b_coef, isc3_briggs_urban_y_b_slope, isc3_briggs_urban_y_b_exponent,
    isc3_briggs_urban_y_c_coef, isc3_briggs_urban_y_c_slope, isc3_briggs_urban_y_c_exponent,
    isc3_briggs_urban_y_d_coef, isc3_briggs_urban_y_d_slope, isc3_briggs_urban_y_d_exponent,
    isc3_briggs_urban_y_e_coef, isc3_briggs_urban_y_e_slope, isc3_briggs_urban_y_e_exponent,
    isc3_briggs_urban_y_f_coef, isc3_briggs_urban_y_f_slope, isc3_briggs_urban_y_f_exponent,
    isc3_briggs_urban_z_a_coef, isc3_briggs_urban_z_a_slope, isc3_briggs_urban_z_a_exponent,
    isc3_briggs_urban_z_b_coef, isc3_briggs_urban_z_b_slope, isc3_briggs_urban_z_b_exponent,
    isc3_briggs_urban_z_c_coef, isc3_briggs_urban_z_c_slope, isc3_briggs_urban_z_c_exponent,
    isc3_briggs_urban_z_d_coef, isc3_briggs_urban_z_d_slope, isc3_briggs_urban_z_d_exponent,
    isc3_briggs_urban_z_e_coef, isc3_briggs_urban_z_e_slope, isc3_briggs_urban_z_e_exponent,
    isc3_briggs_urban_z_f_coef, isc3_briggs_urban_z_f_slope, isc3_briggs_urban_z_f_exponent,
    isc3_urban_min_distance
    """
    xs = positive(x, "x")
    cls = check_option(stability_class, "stability_class", CLASSES)
    ground = check_option(terrain, "terrain", TERRAINS)
    key = cls.lower()
    if ground == "urban":
        warn_validity(xs, "x", row("isc3_urban_min_distance"), math.inf, "isc3_urban_min_distance", stacklevel=3)
        parts = []
        for axis in ("y", "z"):
            coef = row(f"isc3_briggs_urban_{axis}_{key}_coef")
            slope = row(f"isc3_briggs_urban_{axis}_{key}_slope")
            exponent = row(f"isc3_briggs_urban_{axis}_{key}_exponent")
            parts.append(coef * xs * (1 + slope * xs) ** exponent)
        return finalize(parts[0], xs), finalize(parts[1], xs)
    km = xs / M_PER_KM
    c, d = row(f"isc3_pg_sigma_y_c_{key}"), row(f"isc3_pg_sigma_y_d_{key}")
    sy = row("isc3_sigma_y_scale") * km * np.tan(row("isc3_deg_to_rad") * (c - d * np.log(km)))
    uppers, a_s, b_s = _band_rows(key)
    idx = np.searchsorted(uppers, km, side="left")
    sz = a_s[idx] * km ** b_s[idx]
    if cls in CAPPED:
        sz = np.minimum(sz, row("isc3_sigma_z_cap"))
    return finalize(sy, xs), finalize(sz, xs)


def _v_term(z: FloatArray, h: FloatArray, sz: FloatArray) -> FloatArray:
    return np.exp(-((z - h) ** 2) / (2 * sz**2)) + np.exp(-((z + h) ** 2) / (2 * sz**2))


def _lid_term(z: FloatArray, h: FloatArray, sz: FloatArray, zi: FloatArray) -> FloatArray:
    """Vertical term with a mixing lid: the image series of ISC3 eq. 1-50, or the well-mixed form of eq. 1-51."""
    v = _v_term(z, h, sz)
    for i in range(1, MAX_IMAGE_TERMS + 1):
        shift = 2 * i * zi
        t = (
            np.exp(-((z - h + shift) ** 2) / (2 * sz**2))
            + np.exp(-((z - h - shift) ** 2) / (2 * sz**2))
            + np.exp(-((z + h + shift) ** 2) / (2 * sz**2))
            + np.exp(-((z + h - shift) ** 2) / (2 * sz**2))
        )
        v = v + t
        if np.all(t <= _TINY * v):
            break
    mixed = np.sqrt(2 * np.pi) * sz / zi
    out = np.where(sz / zi >= row("isc3_lid_uniform_ratio"), mixed, v)
    return np.where(h > zi, 0, out)


def gaussian_plume(
    q: Any, u: Any, y: Any, z: Any, h: Any, sigma_y: Any, sigma_z: Any, mixing_height: Any = None
) -> Any:
    """Steady-state Gaussian plume of a point source with ground reflection and an optional mixing lid.

    Parameters
    ----------
    q : float or array [kg/s]
        Emission rate (>= 0).
    u : float or array [m/s]
        Wind speed (> 0).
    y : float or array [m]
        Crosswind distance of the receptor.
    z : float or array [m]
        Receptor height (>= 0).
    h : float or array [m]
        Source height (>= 0).
    sigma_y : float or array [m]
        Lateral dispersion coefficient (> 0).
    sigma_z : float or array [m]
        Vertical dispersion coefficient (> 0).
    mixing_height : float or array [m], optional
        Height of the mixing lid (> 0); None for unlimited mixing.

    Returns
    -------
    float or array [kg/m^3]
        Concentration.

    Equation
    --------
    C = q / (2 pi u sigma_y sigma_z) exp(-y^2 / 2 sigma_y^2) V, V = exp(-(z-h)^2 / 2 sigma_z^2) + exp(-(z+h)^2 / 2
    sigma_z^2);
    with a lid the image series of ISC3 eq. 1-50, and V = sqrt(2 pi) sigma_z / z_i where sigma_z / z_i >= 1.6 (eq.
    1-51).

    Source
    ------
    epa1995isc3v2 eqs. 1-1, 1-50 and 1-51, pp. 1-3 and 1-33.

    Validity
    --------
    A source above the lid gives zero concentration; the image series stops when a term is below 1e-16 of the sum (at
    most 1,000
    terms). No plume rise, deposition or terrain.

    Knowledge rows
    --------------
    isc3_lid_uniform_ratio
    """
    parts = {
        "q": non_negative(q, "q"),
        "u": positive(u, "u"),
        "y": _real(y, "y"),
        "z": non_negative(z, "z"),
        "h": non_negative(h, "h"),
        "sigma_y": positive(sigma_y, "sigma_y"),
        "sigma_z": positive(sigma_z, "sigma_z"),
    }
    qa, ua, ya, za, ha, sy, sz = broadcast_all(**parts)
    if mixing_height is None:
        # the exponentials run on the un-broadcast shapes (a receptor grid has y along one axis and z along the
        # other), so the grid costs two products instead of four exponentials of the full size
        q0, u0, y0, z0, h0, sy0, sz0 = parts.values()
        base = q0 / (2 * np.pi * u0 * sy0 * sz0) * np.exp(-(y0**2) / (2 * sy0**2))
        return finalize(base * _v_term(z0, h0, sz0), qa, ua, ya, za, ha, sy, sz)
    zi = positive(mixing_height, "mixing_height")
    qa, ua, ya, za, ha, sy, sz, zi = broadcast_all(
        q=qa, u=ua, y=ya, z=za, h=ha, sigma_y=sy, sigma_z=sz, mixing_height=zi
    )
    base = qa / (2 * np.pi * ua * sy * sz) * np.exp(-(ya**2) / (2 * sy**2))
    return finalize(base * _lid_term(za, ha, sz, zi), qa, ua, ya, za, ha, sy, sz, zi)


def _real(value: Any, name: str) -> FloatArray:
    return check_finite(as_float_array(value, name), name)


def line_source_plume(q_line: Any, u: Any, z: Any, h: Any, sigma_z: Any) -> Any:
    """Concentration downwind of an infinite crosswind line source.

    Parameters
    ----------
    q_line : float or array [kg/(m s)]
        Emission per unit length (>= 0).
    u : float or array [m/s]
        Wind speed (> 0).
    z : float or array [m]
        Receptor height (>= 0).
    h : float or array [m]
        Source height (>= 0).
    sigma_z : float or array [m]
        Vertical dispersion coefficient at the receptor distance (> 0).

    Returns
    -------
    float or array [kg/m^3]
        Concentration.

    Equation
    --------
    C = q_l / (sqrt(2 pi) u sigma_z) V, V = exp(-(z-h)^2 / 2 sigma_z^2) + exp(-(z+h)^2 / 2 sigma_z^2).

    Source
    ------
    epa1995isc3v2 eq. 1-1 integrated over the crosswind direction (derived in spec 006 FR-006-13).

    Validity
    --------
    Wind perpendicular to the road; roads at an angle are approximated by finite segments.

    Knowledge rows
    --------------
    none
    """
    q, ua, za, ha, sz = broadcast_all(
        q_line=non_negative(q_line, "q_line"),
        u=positive(u, "u"),
        z=non_negative(z, "z"),
        h=non_negative(h, "h"),
        sigma_z=positive(sigma_z, "sigma_z"),
    )
    return finalize(q / (np.sqrt(2 * np.pi) * ua * sz) * _v_term(za, ha, sz), q, ua, za, ha, sz)


def finite_line_source_plume(
    q_line: Any, u: Any, y: Any, z: Any, h: Any, y1: Any, y2: Any, sigma_y: Any, sigma_z: Any
) -> Any:
    """Concentration downwind of a crosswind line-source segment.

    Parameters
    ----------
    q_line : float or array [kg/(m s)]
        Emission per unit length (>= 0).
    u : float or array [m/s]
        Wind speed (> 0).
    y : float or array [m]
        Crosswind distance of the receptor.
    z : float or array [m]
        Receptor height (>= 0).
    h : float or array [m]
        Source height (>= 0).
    y1 : float or array [m]
        Start of the segment.
    y2 : float or array [m]
        End of the segment (> y1).
    sigma_y : float or array [m]
        Lateral dispersion coefficient (> 0).
    sigma_z : float or array [m]
        Vertical dispersion coefficient (> 0).

    Returns
    -------
    float or array [kg/m^3]
        Concentration.

    Equation
    --------
    C = q_l / (2 sqrt(2 pi) u sigma_z) [erf((y2 - y)/(sqrt(2) sigma_y)) - erf((y1 - y)/(sqrt(2) sigma_y))] V.

    Source
    ------
    epa1995isc3v2 eq. 1-1 integrated over the segment (derived in spec 006 FR-006-13).

    Validity
    --------
    Tends to the infinite line source as the segment grows; additive over adjacent segments.

    Knowledge rows
    --------------
    none
    """
    q, ua, ya, za, ha, a, b, sy, sz = broadcast_all(
        q_line=non_negative(q_line, "q_line"),
        u=positive(u, "u"),
        y=_real(y, "y"),
        z=non_negative(z, "z"),
        h=non_negative(h, "h"),
        y1=_real(y1, "y1"),
        y2=_real(y2, "y2"),
        sigma_y=positive(sigma_y, "sigma_y"),
        sigma_z=positive(sigma_z, "sigma_z"),
    )
    if not (a < b).all():
        raise InputError("argument 'y1' must be smaller than 'y2'", argument="y1")
    root = np.sqrt(2) * sy
    span = _erf((b - ya) / root) - _erf((a - ya) / root)
    return finalize(
        q / (2 * np.sqrt(2 * np.pi) * ua * sz) * span * _v_term(za, ha, sz), q, ua, ya, za, ha, a, b, sy, sz
    )
