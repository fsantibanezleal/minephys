"""Vertical slices of the mass above a circular slip surface (spec 003 FR-003-07, FR-003-08)."""

from __future__ import annotations

import math
from typing import Any, NamedTuple

import numpy as np

from .. import _tripwire as tw
from .._errors import InputError
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

_MIN_SLICES = 2
_MAX_SLICES = 10_000
_SAME_POINT = 1e-9  # relative tolerance for two intersections that are the same point


class Slices(NamedTuple):
    """Per-slice arrays of the mass between a ground polyline and a circle."""

    width: FloatArray
    weight: FloatArray
    base_angle: FloatArray
    base_length: FloatArray
    pore_pressure: FloatArray


def _polyline(surface_x: Any, surface_z: Any) -> tuple[FloatArray, FloatArray]:
    x = as_float_array(surface_x, "surface_x")
    z = as_float_array(surface_z, "surface_z")
    check_rank(x, "surface_x", 1)
    check_rank(z, "surface_z", 1)
    check_finite(x, "surface_x")
    check_finite(z, "surface_z")
    check_size(x, "surface_x", min_size=2)
    check_size(z, "surface_z", min_size=2)
    if x.size != z.size:
        raise InputError(
            f"arguments surface_x and surface_z must have the same length, got {x.size} and {z.size}",
            argument="surface_z",
        )
    if np.any(np.diff(x) <= 0):
        at = int(np.argmax(np.diff(x) <= 0))
        raise InputError(
            f"argument 'surface_x' must be strictly increasing (first violation after index {at})", argument="surface_x"
        )
    return x, z


def _intersections(x: FloatArray, z: FloatArray, cx: float, cz: float, radius: float) -> list[tuple[float, float]]:
    """Distinct points where the circle meets the polyline (tangent points count once)."""
    found: list[tuple[float, float]] = []
    scale = max(radius, float(np.max(np.abs(x))), float(np.max(np.abs(z))), 1)
    for i in range(x.size - 1):
        dx, dz = x[i + 1] - x[i], z[i + 1] - z[i]
        fx, fz = x[i] - cx, z[i] - cz
        a = dx * dx + dz * dz
        b = 2 * (fx * dx + fz * dz)
        c = fx * fx + fz * fz - radius * radius
        disc = b * b - 4 * a * c
        if disc < 0:
            continue
        root = math.sqrt(disc)
        for t in {(-b - root) / (2 * a), (-b + root) / (2 * a)}:
            if 0 <= t <= 1:
                point = (float(x[i] + t * dx), float(z[i] + t * dz))
                if not any(math.hypot(point[0] - p[0], point[1] - p[1]) <= _SAME_POINT * scale for p in found):
                    found.append(point)
    return found


def circular_slices(
    surface_x: Any,
    surface_z: Any,
    center_x: Any,
    center_z: Any,
    radius: Any,
    n_slices: Any,
    unit_weight: Any,
    pore_pressure_ratio: Any = 0,
) -> Slices:
    """Cut the mass between a ground polyline and a circle into equal-width vertical slices.

    Parameters
    ----------
    surface_x : array_like [m]
        Abscissas of the ground polyline, 1-D, strictly increasing, at least two points.
    surface_z : array_like [m]
        Elevations of the ground polyline, 1-D, same length as surface_x.
    center_x : float [m]
        Abscissa of the circle centre.
    center_z : float [m]
        Elevation of the circle centre.
    radius : float [m]
        Circle radius, > 0.
    n_slices : int [count]
        Number of slices, an integer from 2 to 10,000.
    unit_weight : float [N/m^3]
        Unit weight of the mass, > 0.
    pore_pressure_ratio : float [1]
        Pore-pressure ratio r_u, 0 <= r_u < 1.

    Returns
    -------
    Slices [N/m]
        Named arrays of length n_slices: width [m], weight [N/m], base_angle [rad], base_length [m] and
        pore_pressure [Pa].

    Equation
    --------
    b = (x_exit - x_entry) / n; W = gamma b h with h the ground height minus the lower arc at the slice mid-point;
    alpha = -asin((x_mid - x_c) / R) with its sign chosen so that the driving moment sum(W sin alpha) is positive;
    l = b / cos(alpha); u = r_u gamma h.

    Source
    ------
    rocscience2020slide, p. 1 (slice geometry; hand calculation 1)

    Validity
    --------
    The circle must cut the ground polyline at exactly two points (InputError naming radius otherwise); unit_weight
    below tripwire_unit_weight_min (kN/m^3 passed as N/m^3) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_unit_weight_min
    """
    x, z = _polyline(surface_x, surface_z)
    cx = as_scalar(check_finite(as_float_array(center_x, "center_x"), "center_x"), "center_x")
    cz = as_scalar(check_finite(as_float_array(center_z, "center_z"), "center_z"), "center_z")
    r = as_scalar(as_checked(radius, "radius", lo=0, lo_open=True), "radius")
    n = int(as_scalar(as_count(n_slices, "n_slices", lo=_MIN_SLICES, hi=_MAX_SLICES), "n_slices"))
    gamma_arr = as_checked(unit_weight, "unit_weight", lo=0, lo_open=True)
    gamma = as_scalar(gamma_arr, "unit_weight")
    ru = as_scalar(
        as_checked(pore_pressure_ratio, "pore_pressure_ratio", lo=0, hi=1, hi_open=True), "pore_pressure_ratio"
    )
    tw.warn_min(gamma_arr, "unit_weight", "tripwire_unit_weight_min")
    points = _intersections(x, z, cx, cz, r)
    if len(points) != 2:
        raise InputError(
            f"the circle must cut the ground polyline at exactly two points, it cuts it at {len(points)}",
            argument="radius",
        )
    x_entry, x_exit = sorted(p[0] for p in points)
    width = (x_exit - x_entry) / n
    mid = x_entry + width * (np.arange(n) + 0.5)
    arc = cz - np.sqrt(r * r - (mid - cx) ** 2)
    height = np.interp(mid, x, z) - arc
    if np.any(height <= 0):
        raise InputError("the circle lies above the ground between its two intersections", argument="center_z")
    weight = gamma * width * height
    angle = -np.arcsin((mid - cx) / r)
    if np.sum(weight * np.sin(angle)) < 0:
        angle = -angle
    return Slices(
        np.full(n, width),
        weight,
        angle,
        width / np.cos(angle),
        ru * gamma * height,
    )
