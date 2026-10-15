"""Road resistance, required force and steady speeds of a haul truck (spec 001 FR-001-01 to FR-001-07)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import _tripwire as tw
from .._constants import STANDARD_GRAVITY
from .._errors import InputError
from .._validate import FloatArray, as_checked, as_float_array, broadcast_all, check_bool, check_finite, finalize

_HALF = 0.5
_NEWTON_CAP = 200
_NEWTON_RTOL = 1e-15


def _exact_grade_resistance(grade: FloatArray) -> FloatArray:
    """sin(arctan grade) = grade / sqrt(1 + grade^2), overflow-free and exact for tiny grades."""
    return grade / np.hypot(1, grade)


def grade_resistance(grade: Any, small_angle: bool = False) -> Any:
    """Grade resistance as a fraction of the gross vehicle weight.

    Parameters
    ----------
    grade : float or array_like [1]
        Road grade, rise over run (tan of the road angle); negative downhill.
    small_angle : bool
        When True the grade itself is returned (the percent-style convention GR = grade).

    Returns
    -------
    float or ndarray [1]
        Grade resistance GR (negative downhill).

    Equation
    --------
    GR = grade / sqrt(1 + grade^2) = sin(arctan grade); GR = grade when small_angle is True.

    Source
    ------
    soofastaei2016, pp. 285-293 (the decomposition TR = RR + GR; the page of the statement was not read)

    Validity
    --------
    Any finite grade; |grade| > tripwire_grade_abs_max (a percent passed as a fraction) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_grade_abs_max
    """
    g = check_finite(as_float_array(grade, "grade"), "grade")
    flag = check_bool(small_angle, "small_angle")
    tw.warn_abs_max(g, "grade", "tripwire_grade_abs_max")
    return finalize(np.where(flag, g, _exact_grade_resistance(g)), g)


def total_resistance(rolling_resistance: Any, grade: Any, small_angle: bool = False) -> Any:
    """Total resistance TR = RR + GR as a fraction of the gross vehicle weight.

    Parameters
    ----------
    rolling_resistance : float or array_like [1]
        Rolling resistance RR, 0 <= RR < 1.
    grade : float or array_like [1]
        Road grade, rise over run; negative downhill.
    small_angle : bool
        When True the grade itself is used as the grade resistance.

    Returns
    -------
    float or ndarray [1]
        Total resistance TR.

    Equation
    --------
    TR = RR + GR(grade), GR as in grade_resistance.

    Source
    ------
    soofastaei2016, pp. 285-293 (the decomposition TR = RR + GR; the page of the statement was not read)

    Validity
    --------
    0 <= RR < 1; RR > tripwire_rolling_resistance_max or |grade| > tripwire_grade_abs_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_rolling_resistance_max, tripwire_grade_abs_max
    """
    rr = as_checked(rolling_resistance, "rolling_resistance", lo=0, hi=1, hi_open=True)
    g = check_finite(as_float_array(grade, "grade"), "grade")
    flag = check_bool(small_angle, "small_angle")
    rr, g = broadcast_all(rolling_resistance=rr, grade=g)
    tw.warn_max(rr, "rolling_resistance", "tripwire_rolling_resistance_max")
    tw.warn_abs_max(g, "grade", "tripwire_grade_abs_max")
    return finalize(rr + np.where(flag, g, _exact_grade_resistance(g)), rr, g)


def _air_density(air_density: Any, drag_area: FloatArray) -> FloatArray:
    """The air density array; None is allowed only while no drag area is positive."""
    if air_density is None:
        if np.any(drag_area > 0):
            raise InputError("argument 'air_density' is required when drag_area > 0", argument="air_density")
        return np.asarray(0.0)
    return as_checked(air_density, "air_density", lo=0, lo_open=True)


def required_force(
    mass: Any,
    total_resistance: Any,
    acceleration: Any = 0,
    effective_mass: Any = None,
    drag_area: Any = 0,
    air_density: Any = None,
    speed: Any = 0,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Tractive force needed to move the truck against rolling, grade, inertia and aerodynamic drag.

    Parameters
    ----------
    mass : float or array_like [kg]
        Gross vehicle mass, > 0.
    total_resistance : float or array_like [1]
        Total resistance TR (rolling plus grade), as a fraction of the weight; negative downhill.
    acceleration : float or array_like [m/s^2]
        Longitudinal acceleration (negative for deceleration).
    effective_mass : float or array_like [kg]
        Mass used in the inertia term (rotating-mass allowance); None means `mass`.
    drag_area : float or array_like [m^2]
        Aerodynamic drag area C_D A, >= 0.
    air_density : float or array_like [kg/m^3]
        Air density, > 0; required when `drag_area` > 0.
    speed : float or array_like [m/s]
        Vehicle speed for the drag term, >= 0.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [N]
        Required tractive force (negative when the road drives the truck).

    Equation
    --------
    F = mass g TR + m_eff a + 0.5 rho C_D A v^2, with m_eff = mass when effective_mass is None.

    Source
    ------
    soofastaei2016, pp. 285-293 (required tractive force; the page of the statement was not read)

    Validity
    --------
    Steady longitudinal motion along one road segment; mass outside tripwire_truck_mass_min and
    tripwire_truck_mass_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    m = as_checked(mass, "mass", lo=0, lo_open=True)
    tr = check_finite(as_float_array(total_resistance, "total_resistance"), "total_resistance")
    a = check_finite(as_float_array(acceleration, "acceleration"), "acceleration")
    m_eff = m if effective_mass is None else as_checked(effective_mass, "effective_mass", lo=0, lo_open=True)
    cda = as_checked(drag_area, "drag_area", lo=0)
    rho = _air_density(air_density, cda)
    v = as_checked(speed, "speed", lo=0)
    grav = as_checked(g, "g", lo=0, lo_open=True)
    m, tr, a, m_eff, cda, rho, v, grav = broadcast_all(
        mass=m,
        total_resistance=tr,
        acceleration=a,
        effective_mass=m_eff,
        drag_area=cda,
        air_density=rho,
        speed=v,
        g=grav,
    )
    tw.warn_min(m, "mass", "tripwire_truck_mass_min")
    tw.warn_max(m, "mass", "tripwire_truck_mass_max")
    force = m * grav * tr + m_eff * a + _HALF * rho * cda * v * v
    return finalize(force, m, tr, a, m_eff, cda, rho, v, grav)


def _drag_speed(k: FloatArray, f0: FloatArray, power: FloatArray) -> FloatArray:
    """The unique positive root of k v^3 + f0 v - power = 0 (k > 0, power > 0) by Newton from above.

    f(v) = k v^3 + f0 v - power is increasing and convex beyond its minimum, so Newton started at a point with
    f >= 0 (min(power / f0, (power / k)^(1/3)) for f0 > 0, (power / k)^(1/3) + sqrt(-f0 / k) otherwise) decreases
    monotonically to the root; the iteration is overflow-free for any positive k.
    """
    cube = np.cbrt(power / k)
    up = np.where(f0 > 0, np.minimum(power / np.where(f0 > 0, f0, 1), cube), cube + np.sqrt(np.maximum(-f0, 0) / k))
    v = up
    for _ in range(_NEWTON_CAP):
        step = (k * v * v * v + f0 * v - power) / (3 * k * v * v + f0)
        v = v - step
        if np.all(np.abs(step) <= _NEWTON_RTOL * np.abs(v)):
            break
    return v


def rimpull_limited_speed(
    power: Any,
    mass: Any,
    total_resistance: Any,
    efficiency: Any = 1,
    traction_limit: Any = math.inf,
    speed_limit: Any = math.inf,
    drag_area: Any = 0,
    air_density: Any = None,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Steady speed limited by the available power, the traction limit and the speed limit.

    Parameters
    ----------
    power : float or array_like [W]
        Power at the wheels before the drive efficiency, > 0.
    mass : float or array_like [kg]
        Gross vehicle mass, > 0.
    total_resistance : float or array_like [1]
        Total resistance TR as a fraction of the weight.
    efficiency : float or array_like [1]
        Drive efficiency, 0 < eta <= 1.
    traction_limit : float or array_like [N]
        Largest tractive force the wheels can transmit, > 0; +inf allowed.
    speed_limit : float or array_like [m/s]
        Speed cap, > 0; +inf allowed.
    drag_area : float or array_like [m^2]
        Aerodynamic drag area C_D A, >= 0.
    air_density : float or array_like [kg/m^3]
        Air density, > 0; required when `drag_area` > 0.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [m/s]
        min(v_ss, speed_limit); 0 when mass g TR exceeds the traction limit.

    Equation
    --------
    v_ss is the largest v >= 0 with min(T, eta P / v) >= mass g TR + 0.5 rho C_D A v^2; without drag and traction
    limit v_ss = eta P / (mass g TR), with drag the positive root of 0.5 rho C_D A v^3 + mass g TR v - eta P = 0.

    Source
    ------
    soofastaei2016, pp. 285-293 (steady-state force balance; the page of the statement was not read)

    Validity
    --------
    An unbounded speed (TR <= 0 without drag) needs a finite speed_limit (InputError otherwise); mass outside
    tripwire_truck_mass_min and tripwire_truck_mass_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    p = as_checked(power, "power", lo=0, lo_open=True)
    m = as_checked(mass, "mass", lo=0, lo_open=True)
    tr = check_finite(as_float_array(total_resistance, "total_resistance"), "total_resistance")
    eta = as_checked(efficiency, "efficiency", lo=0, hi=1, lo_open=True)
    limit_t = as_checked(traction_limit, "traction_limit", lo=0, lo_open=True, allow_posinf=True)
    limit_v = as_checked(speed_limit, "speed_limit", lo=0, lo_open=True, allow_posinf=True)
    cda = as_checked(drag_area, "drag_area", lo=0)
    rho = _air_density(air_density, cda)
    grav = as_checked(g, "g", lo=0, lo_open=True)
    p, m, tr, eta, limit_t, limit_v, cda, rho, grav = broadcast_all(
        power=p,
        mass=m,
        total_resistance=tr,
        efficiency=eta,
        traction_limit=limit_t,
        speed_limit=limit_v,
        drag_area=cda,
        air_density=rho,
        g=grav,
    )
    tw.warn_min(m, "mass", "tripwire_truck_mass_min")
    tw.warn_max(m, "mass", "tripwire_truck_mass_max")
    f0 = m * grav * tr
    k = _HALF * rho * cda
    drag = k > 0
    unbounded = ~drag & (f0 <= 0)
    if np.any(unbounded & np.isinf(limit_v)):
        raise InputError(
            "argument 'speed_limit' must be finite: the steady speed is unbounded for this resistance without drag",
            argument="speed_limit",
        )
    ep = eta * p
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        k_safe = np.where(drag, k, 1)
        v_power = np.where(drag, _drag_speed(k_safe, f0, ep), np.where(f0 > 0, ep / np.where(f0 > 0, f0, 1), np.inf))
        v_traction = np.where(drag, np.sqrt(np.maximum(limit_t - f0, 0) / k_safe), np.inf)
    v_ss = np.where(f0 > limit_t, 0, np.minimum(v_power, v_traction))
    return finalize(np.minimum(v_ss, limit_v), p, m, tr, eta, limit_t, limit_v, cda, rho, grav)


def retarder_limited_speed(
    retarder_power: Any,
    mass: Any,
    rolling_resistance: Any,
    grade: Any,
    speed_limit: Any = math.inf,
    small_angle: bool = False,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Steady downhill speed limited by the retarder power.

    Parameters
    ----------
    retarder_power : float or array_like [W]
        Continuous retarder power, > 0.
    mass : float or array_like [kg]
        Gross vehicle mass, > 0.
    rolling_resistance : float or array_like [1]
        Rolling resistance RR, 0 <= RR < 1.
    grade : float or array_like [1]
        Road grade, rise over run; negative downhill.
    speed_limit : float or array_like [m/s]
        Speed cap, > 0; +inf allowed.
    small_angle : bool
        When True the grade itself is used as the grade resistance.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [m/s]
        min(retarder_power / (mass g f), speed_limit) with the net braking fraction f; speed_limit when f <= 0.

    Equation
    --------
    f = -GR(grade) - RR; v = min(P_ret / (mass g f), speed_limit) for f > 0 and v = speed_limit for f <= 0.

    Source
    ------
    soofastaei2016, pp. 285-293 (retarder power balance; the page of the statement was not read)

    Validity
    --------
    f <= 0 with an infinite speed_limit is an InputError; RR, grade and mass outside their tripwires emit a
    ValidityWarning.

    Knowledge rows
    --------------
    tripwire_grade_abs_max, tripwire_rolling_resistance_max, tripwire_truck_mass_min, tripwire_truck_mass_max
    """
    p = as_checked(retarder_power, "retarder_power", lo=0, lo_open=True)
    m = as_checked(mass, "mass", lo=0, lo_open=True)
    rr = as_checked(rolling_resistance, "rolling_resistance", lo=0, hi=1, hi_open=True)
    gr = check_finite(as_float_array(grade, "grade"), "grade")
    limit_v = as_checked(speed_limit, "speed_limit", lo=0, lo_open=True, allow_posinf=True)
    flag = check_bool(small_angle, "small_angle")
    grav = as_checked(g, "g", lo=0, lo_open=True)
    p, m, rr, gr, limit_v, grav = broadcast_all(
        retarder_power=p, mass=m, rolling_resistance=rr, grade=gr, speed_limit=limit_v, g=grav
    )
    tw.warn_abs_max(gr, "grade", "tripwire_grade_abs_max")
    tw.warn_max(rr, "rolling_resistance", "tripwire_rolling_resistance_max")
    tw.warn_min(m, "mass", "tripwire_truck_mass_min")
    tw.warn_max(m, "mass", "tripwire_truck_mass_max")
    braking = -np.where(flag, gr, _exact_grade_resistance(gr)) - rr
    needed = braking > 0
    if np.any(~needed & np.isinf(limit_v)):
        raise InputError(
            "argument 'speed_limit' must be finite: no braking is needed, so the steady speed is unbounded",
            argument="speed_limit",
        )
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.where(needed, p / (m * grav * np.where(needed, braking, 1)), np.inf)
    return finalize(np.minimum(v, limit_v), p, m, rr, gr, limit_v, grav)
