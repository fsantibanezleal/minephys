"""Segment and cycle energy of a haul truck: diesel, trolley-assist and battery-electric (spec 001 FR-001-11,
FR-001-12, FR-001-16, FR-001-17, FR-001-25)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .. import _tripwire as tw
from .._constants import STANDARD_GRAVITY
from .._errors import InputError
from .._validate import (
    FloatArray,
    as_checked,
    as_float_array,
    as_scalar,
    broadcast_all,
    check_bool,
    check_finite,
    check_rank,
    check_size,
    finalize,
)
from ._road import _exact_grade_resistance

_MAX_SEGMENTS = 100_000
_SEGMENT_ARGS = ("mass", "length", "rolling_resistance", "grade")


def _wheel_energy(m: FloatArray, ln: FloatArray, rr: FloatArray, gr: FloatArray, flag: Any, g: FloatArray) -> FloatArray:
    """Wheel energy m g TR L of segments (positive uphill, negative when the road drives the truck)."""
    return m * g * (rr + np.where(flag, gr, _exact_grade_resistance(gr))) * ln


def segment_energy(
    mass: Any,
    length: Any,
    rolling_resistance: Any,
    grade: Any,
    efficiency: Any = 1,
    regen_efficiency: Any = 0,
    small_angle: bool = False,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Energy drawn from the source over one road segment at steady speed.

    Parameters
    ----------
    mass : float or array_like [kg]
        Gross vehicle mass, > 0.
    length : float or array_like [m]
        Segment length along the road, >= 0.
    rolling_resistance : float or array_like [1]
        Rolling resistance RR, 0 <= RR < 1.
    grade : float or array_like [1]
        Road grade, rise over run; negative downhill.
    efficiency : float or array_like [1]
        Source-to-wheel efficiency, 0 < eta <= 1.
    regen_efficiency : float or array_like [1]
        Fraction of the downhill wheel energy returned to the source, 0 <= r <= 1.
    small_angle : bool
        When True the grade itself is used as the grade resistance.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [J]
        Energy drawn from the source (negative when energy is returned).

    Equation
    --------
    E_w = mass g TR L; E = E_w / eta for E_w >= 0 and E = r E_w for E_w < 0.

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-11; a work balance, no empirical constant)

    Validity
    --------
    Steady speed (no kinetic-energy change) and along-road length; grade, rolling resistance and mass outside their
    tripwires emit a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_grade_abs_max, tripwire_rolling_resistance_max, tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    m = as_checked(mass, "mass", lo=0, lo_open=True)
    ln = as_checked(length, "length", lo=0)
    rr = as_checked(rolling_resistance, "rolling_resistance", lo=0, hi=1, hi_open=True)
    gr = check_finite(as_float_array(grade, "grade"), "grade")
    eta = as_checked(efficiency, "efficiency", lo=0, hi=1, lo_open=True)
    regen = as_checked(regen_efficiency, "regen_efficiency", lo=0, hi=1)
    flag = check_bool(small_angle, "small_angle")
    grav = as_checked(g, "g", lo=0, lo_open=True)
    m, ln, rr, gr, eta, regen, grav = broadcast_all(
        mass=m, length=ln, rolling_resistance=rr, grade=gr, efficiency=eta, regen_efficiency=regen, g=grav
    )
    _warn_segments(m, rr, gr)
    wheel = _wheel_energy(m, ln, rr, gr, flag, grav)
    return finalize(np.where(wheel >= 0, wheel / eta, regen * wheel), m, ln, rr, gr, eta, regen, grav)


def _warn_segments(m: FloatArray, rr: FloatArray, gr: FloatArray) -> None:
    tw.warn_abs_max(gr, "grade", "tripwire_grade_abs_max")
    tw.warn_max(rr, "rolling_resistance", "tripwire_rolling_resistance_max")
    tw.warn_min(m, "mass", "tripwire_truck_mass_min")
    tw.warn_max(m, "mass", "tripwire_truck_mass_max")


def _segments(
    mass: Any, length: Any, rolling_resistance: Any, grade: Any, extra: dict[str, Any] | None = None
) -> tuple[FloatArray, ...]:
    """Validated per-segment arrays (1-D, scalars broadcast, 1 to 100,000 segments), plus `extra` boolean arrays."""
    arrays = {
        "mass": as_float_array(mass, "mass"),
        "length": as_float_array(length, "length"),
        "rolling_resistance": as_float_array(rolling_resistance, "rolling_resistance"),
        "grade": as_float_array(grade, "grade"),
    }
    for name, arr in arrays.items():
        if arr.ndim > 1:
            check_rank(arr, name, 1)
    flags = {name: check_bool(value, name) for name, value in (extra or {}).items()}
    for name, flag in flags.items():
        if np.ndim(flag) > 1:
            raise InputError(f"argument '{name}' must be a 1-D array, got shape {np.shape(flag)}", argument=name)
    for name, arr in arrays.items():
        check_finite(arr, name)
    as_checked(arrays["mass"], "mass", lo=0, lo_open=True)
    as_checked(arrays["length"], "length", lo=0)
    as_checked(arrays["rolling_resistance"], "rolling_resistance", lo=0, hi=1, hi_open=True)
    merged = broadcast_all(**arrays, **flags)
    sizes = {name: int(np.size(a)) for name, a in zip([*arrays, *flags], merged, strict=True)}
    if merged[0].size == 0:
        raise InputError("argument 'mass' has no segments: at least one is required", argument="mass")
    check_size(merged[0], max(sizes, key=lambda n: sizes[n]), max_size=_MAX_SEGMENTS)
    return merged


def cycle_energy(
    mass: Any,
    length: Any,
    rolling_resistance: Any,
    grade: Any,
    efficiency: Any = 1,
    regen_efficiency: Any = 0,
    small_angle: bool = False,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Energy drawn from the source over a profile of road segments.

    Parameters
    ----------
    mass : float or array_like [kg]
        Gross vehicle mass per segment, > 0; 1-D array or scalar.
    length : float or array_like [m]
        Segment length per segment, >= 0; 1-D array or scalar.
    rolling_resistance : float or array_like [1]
        Rolling resistance per segment, 0 <= RR < 1; 1-D array or scalar.
    grade : float or array_like [1]
        Road grade per segment, rise over run; 1-D array or scalar.
    efficiency : float [1]
        Source-to-wheel efficiency, 0 < eta <= 1.
    regen_efficiency : float [1]
        Fraction of the downhill wheel energy returned to the source, 0 <= r <= 1.
    small_angle : bool
        When True the grade itself is used as the grade resistance.
    g : float [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    numpy.float64 [J]
        Sum of segment_energy over the segments.

    Equation
    --------
    E = sum_i segment_energy(mass_i, length_i, RR_i, grade_i).

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-12; a sum of work terms)

    Validity
    --------
    1 to 100,000 segments; tripwires as in segment_energy.

    Knowledge rows
    --------------
    tripwire_grade_abs_max, tripwire_rolling_resistance_max, tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    return _sum_segments(mass, length, rolling_resistance, grade, efficiency, regen_efficiency, small_angle, g)


def _sum_segments(
    mass: Any,
    length: Any,
    rolling_resistance: Any,
    grade: Any,
    efficiency: Any,
    regen_efficiency: Any,
    small_angle: Any,
    g: Any,
    *,
    efficiency_name: str = "efficiency",
) -> Any:
    m, ln, rr, gr = _segments(mass, length, rolling_resistance, grade)
    eta = as_scalar(as_checked(efficiency, efficiency_name, lo=0, hi=1, lo_open=True), efficiency_name)
    regen = as_scalar(as_checked(regen_efficiency, "regen_efficiency", lo=0, hi=1), "regen_efficiency")
    flag = check_bool(small_angle, "small_angle")
    grav = as_scalar(as_checked(g, "g", lo=0, lo_open=True), "g")
    _warn_segments(m, rr, gr)
    wheel = _wheel_energy(m, ln, rr, gr, flag, np.asarray(grav))
    return np.float64(np.sum(np.where(wheel >= 0, wheel / eta, regen * wheel)))


def bev_cycle_energy(
    mass: Any,
    length: Any,
    rolling_resistance: Any,
    grade: Any,
    drive_efficiency: Any,
    regen_efficiency: Any,
    small_angle: bool = False,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Net battery energy of a battery-electric truck over a profile of road segments.

    Parameters
    ----------
    mass : float or array_like [kg]
        Gross vehicle mass per segment, > 0; 1-D array or scalar.
    length : float or array_like [m]
        Segment length per segment, >= 0; 1-D array or scalar.
    rolling_resistance : float or array_like [1]
        Rolling resistance per segment, 0 <= RR < 1; 1-D array or scalar.
    grade : float or array_like [1]
        Road grade per segment, rise over run; 1-D array or scalar.
    drive_efficiency : float [1]
        Battery-to-wheel efficiency, 0 < eta <= 1.
    regen_efficiency : float [1]
        Wheel-to-battery regeneration efficiency, 0 <= r <= 1.
    small_angle : bool
        When True the grade itself is used as the grade resistance.
    g : float [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    numpy.float64 [J]
        Net battery energy (negative when regeneration exceeds consumption).

    Equation
    --------
    E = cycle_energy(..., efficiency=drive_efficiency, regen_efficiency=regen_efficiency).

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-17; regeneration is a battery-electric assumption, section 7.6)

    Validity
    --------
    1 to 100,000 segments; tripwires as in segment_energy.

    Knowledge rows
    --------------
    tripwire_grade_abs_max, tripwire_rolling_resistance_max, tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    return _sum_segments(
        mass, length, rolling_resistance, grade, drive_efficiency, regen_efficiency, small_angle, g,
        efficiency_name="drive_efficiency",
    )


def trolley_cycle_energy(
    mass: Any,
    length: Any,
    rolling_resistance: Any,
    grade: Any,
    on_trolley: Any,
    diesel_efficiency: Any,
    electric_efficiency: Any,
    small_angle: bool = False,
    g: Any = STANDARD_GRAVITY,
) -> tuple[Any, Any]:
    """Diesel and trolley-line energy of a trolley-assist truck over a profile of road segments.

    Parameters
    ----------
    mass : float or array_like [kg]
        Gross vehicle mass per segment, > 0; 1-D array or scalar.
    length : float or array_like [m]
        Segment length per segment, >= 0; 1-D array or scalar.
    rolling_resistance : float or array_like [1]
        Rolling resistance per segment, 0 <= RR < 1; 1-D array or scalar.
    grade : float or array_like [1]
        Road grade per segment, rise over run; 1-D array or scalar.
    on_trolley : bool or array_like of bool
        True for the segments under the trolley line.
    diesel_efficiency : float [1]
        Tank-to-wheel efficiency, 0 < eta <= 1.
    electric_efficiency : float [1]
        Line-to-wheel efficiency, 0 < eta <= 1.
    small_angle : bool
        When True the grade itself is used as the grade resistance.
    g : float [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    tuple of numpy.float64 [J]
        (diesel energy from the tank, electric energy from the line).

    Equation
    --------
    Segments with E_w > 0 draw E_w / eta_electric on the line and E_w / eta_diesel off it; segments with E_w <= 0 draw
    nothing (no regeneration into the line).

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-16; no published line-regeneration model was read, section 7.6)

    Validity
    --------
    1 to 100,000 segments; tripwires as in segment_energy.

    Knowledge rows
    --------------
    tripwire_grade_abs_max, tripwire_rolling_resistance_max, tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    m, ln, rr, gr, line = _segments(mass, length, rolling_resistance, grade, {"on_trolley": on_trolley})
    eta_d = as_scalar(as_checked(diesel_efficiency, "diesel_efficiency", lo=0, hi=1, lo_open=True), "diesel_efficiency")
    eta_e = as_scalar(
        as_checked(electric_efficiency, "electric_efficiency", lo=0, hi=1, lo_open=True), "electric_efficiency"
    )
    flag = check_bool(small_angle, "small_angle")
    grav = as_scalar(as_checked(g, "g", lo=0, lo_open=True), "g")
    _warn_segments(m, rr, gr)
    wheel = _wheel_energy(m, ln, rr, gr, flag, np.asarray(grav))
    uphill = wheel > 0
    diesel = np.sum(np.where(uphill & ~line.astype(bool), wheel / eta_d, 0))
    electric = np.sum(np.where(uphill & line.astype(bool), wheel / eta_e, 0))
    return np.float64(diesel), np.float64(electric)
