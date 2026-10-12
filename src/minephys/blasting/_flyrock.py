"""Flyrock range: drag-free bound, Lundborg's empirical maximum and a drag-inclusive ballistic trajectory (spec 002
FR-002-10 to FR-002-13, FR-002-17)."""

from __future__ import annotations

import math
from typing import Any, NamedTuple

import numpy as np

from .. import _tripwire as tw
from .. import knowledge
from .._constants import STANDARD_GRAVITY
from .._errors import InputError
from .._solve import bracketed_root
from .._validate import as_checked, as_scalar, broadcast_all, finalize

_HALF_PI = math.pi / 2
_MAX_STEPS = 1_000_000
_MAX_TIME_STEP = 0.1


def _row(row_id: str) -> float:
    value = knowledge.get_value(row_id)
    assert not isinstance(value, tuple)
    return float(value)


def flyrock_range_no_drag(launch_speed: Any, launch_angle: Any, g: Any = STANDARD_GRAVITY) -> Any:
    """Range of a projectile in vacuum, launched and landing at the same level.

    Parameters
    ----------
    launch_speed : float or array_like [m/s]
        Launch speed, > 0.
    launch_angle : float or array_like [rad]
        Launch angle above the horizontal, 0 <= theta <= pi/2.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [m]
        Horizontal range (an upper bound: drag only shortens it).

    Equation
    --------
    R = v0^2 sin(2 theta) / g

    Source
    ------
    minephys:spec-002-blasting, section 3 (FR-002-10; vacuum projectile range, no empirical constant)

    Validity
    --------
    Launch and landing at the same level; launch_speed above tripwire_launch_speed_max (km/h passed as m/s) emits a
    ValidityWarning.

    Knowledge rows
    --------------
    tripwire_launch_speed_max
    """
    v = as_checked(launch_speed, "launch_speed", lo=0, lo_open=True)
    theta = as_checked(launch_angle, "launch_angle", lo=0, hi=_HALF_PI)
    grav = as_checked(g, "g", lo=0, lo_open=True)
    v, theta, grav = broadcast_all(launch_speed=v, launch_angle=theta, g=grav)
    tw.warn_max(v, "launch_speed", "tripwire_launch_speed_max")
    return finalize(v * v * np.sin(2 * theta) / grav, v, theta, grav)


def flyrock_range_lundborg(hole_diameter: Any) -> Any:
    """Lundborg's empirical maximum throw distance of flyrock.

    Parameters
    ----------
    hole_diameter : float or array_like [m]
        Blasthole diameter, > 0 (converted to inches inside the formula).

    Returns
    -------
    float or ndarray [m]
        Maximum throw distance.

    Equation
    --------
    R_max = 260 d^(2/3) with d in inches.

    Source
    ------
    szendrei2022, eq. 1, p. 726

    Validity
    --------
    Secondary transcription: both rows are UNVERIFIED model constants, so every call emits UnverifiedParameterWarning;
    hole_diameter above tripwire_hole_diameter_max (mm passed as m) emits a ValidityWarning.

    Knowledge rows
    --------------
    lundborg_max_range_coefficient, lundborg_max_range_exponent, tripwire_hole_diameter_max
    """
    d = as_checked(hole_diameter, "hole_diameter", lo=0, lo_open=True)
    tw.warn_max(d, "hole_diameter", "tripwire_hole_diameter_max")
    d_in = d / _row("inch")
    return finalize(_row("lundborg_max_range_coefficient") * d_in ** _row("lundborg_max_range_exponent"), d)


class FlyrockTrajectory(NamedTuple):
    """Trajectory samples (index 0 is the launch, the last sample is the landing point) and summary values."""

    t: np.ndarray
    x: np.ndarray
    z: np.ndarray
    vx: np.ndarray
    vz: np.ndarray
    range: float
    flight_time: float
    apex_height: float


def _hermite(s: float, p0: float, d0: float, p1: float, d1: float, dt: float) -> float:
    """Cubic Hermite interpolation at the fraction s of a step (values p0, p1 and derivatives d0, d1 per unit time)."""
    s2 = s * s
    s3 = s2 * s
    return (2 * s3 - 3 * s2 + 1) * p0 + (s3 - 2 * s2 + s) * dt * d0 + (3 * s2 - 2 * s3) * p1 + (s3 - s2) * dt * d1


def flyrock_trajectory(
    launch_speed: Any,
    launch_angle: Any,
    diameter: Any,
    rock_density: Any,
    drag_coefficient: Any,
    air_density: Any,
    launch_height: Any = 0,
    time_step: Any = 1e-3,
    max_time: Any = 600,
    g: Any = STANDARD_GRAVITY,
) -> FlyrockTrajectory:
    """Ballistic flight of a spherical rock fragment with quadratic air drag, integrated by fixed-step RK4.

    Parameters
    ----------
    launch_speed : float [m/s]
        Launch speed, > 0.
    launch_angle : float [rad]
        Launch angle above the horizontal, -pi/2 <= theta <= pi/2.
    diameter : float [m]
        Fragment diameter (sphere), > 0.
    rock_density : float [kg/m^3]
        Fragment density, > 0.
    drag_coefficient : float [1]
        Drag coefficient C_D, >= 0 (no default: published values span 0.6 to 1.8).
    air_density : float [kg/m^3]
        Air density, >= 0 (no default: 1.24 kg/m^3 is a published reference).
    launch_height : float [m]
        Launch height above the landing level z = 0, >= 0.
    time_step : float [s]
        Integration step, 0 < dt <= 0.1.
    max_time : float [s]
        Longest flight to integrate, > 0; max_time / time_step must not exceed 1,000,000 steps.
    g : float [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    FlyrockTrajectory [m]
        Named result: arrays t [s], x [m], z [m], vx [m/s], vz [m/s] and floats range [m], flight_time [s] and
        apex_height [m].

    Equation
    --------
    m dv/dt = -m g z_hat - 0.5 rho_a C_D A |v| v with m = rho_r pi D^3 / 6 and A = pi D^2 / 4; landing at z = 0 by
    cubic Hermite interpolation on the last step.

    Source
    ------
    szendrei2022, p. 728 (aerodynamic trajectory of a spherical fragment)

    Validity
    --------
    Spheres, constant drag coefficient, no lift, spin or tumbling, flat ground at z = 0; a flight that does not land
    by max_time is an InputError naming max_time; launch_speed and air_density above their tripwires emit a
    ValidityWarning.

    Knowledge rows
    --------------
    flyrock_drag_coefficient_range, flyrock_air_density_reference, tripwire_launch_speed_max,
    tripwire_air_density_max
    """
    v0 = as_scalar(as_checked(launch_speed, "launch_speed", lo=0, lo_open=True), "launch_speed")
    theta = as_scalar(as_checked(launch_angle, "launch_angle", lo=-_HALF_PI, hi=_HALF_PI), "launch_angle")
    diam = as_scalar(as_checked(diameter, "diameter", lo=0, lo_open=True), "diameter")
    rho_r = as_scalar(as_checked(rock_density, "rock_density", lo=0, lo_open=True), "rock_density")
    cd = as_scalar(as_checked(drag_coefficient, "drag_coefficient", lo=0), "drag_coefficient")
    rho_a = as_scalar(as_checked(air_density, "air_density", lo=0), "air_density")
    h0 = as_scalar(as_checked(launch_height, "launch_height", lo=0), "launch_height")
    dt = as_scalar(as_checked(time_step, "time_step", lo=0, hi=_MAX_TIME_STEP, lo_open=True), "time_step")
    t_max = as_scalar(as_checked(max_time, "max_time", lo=0, lo_open=True), "max_time")
    grav = as_scalar(as_checked(g, "g", lo=0, lo_open=True), "g")
    if t_max / dt > _MAX_STEPS:
        raise InputError(
            f"max_time / time_step = {t_max / dt:.6g} exceeds {_MAX_STEPS} steps: "
            "shorten max_time or enlarge time_step",
            argument="max_time",
        )
    tw.warn_max(np.asarray(v0), "launch_speed", "tripwire_launch_speed_max")
    tw.warn_max(np.asarray(rho_a), "air_density", "tripwire_air_density_max")

    mass = rho_r * math.pi * diam**3 / 6
    area = math.pi * diam * diam / 4
    c = _HALF * rho_a * cd * area / mass  # drag deceleration per unit speed squared [1/m]
    vx = v0 * math.cos(theta)
    vz = v0 * math.sin(theta)
    x, z = 0.0, h0
    ts, xs, zs, vxs, vzs = [0.0], [x], [z], [vx], [vz]
    half = dt / 2
    sixth = dt / 6
    sqrt = math.sqrt
    landed = h0 == 0 and vz <= 0
    steps = int(t_max / dt)
    i = 0
    while not landed and i < steps:
        i += 1
        sp = sqrt(vx * vx + vz * vz)
        ax1, az1 = -c * sp * vx, -grav - c * sp * vz
        vx2, vz2 = vx + half * ax1, vz + half * az1
        sp = sqrt(vx2 * vx2 + vz2 * vz2)
        ax2, az2 = -c * sp * vx2, -grav - c * sp * vz2
        vx3, vz3 = vx + half * ax2, vz + half * az2
        sp = sqrt(vx3 * vx3 + vz3 * vz3)
        ax3, az3 = -c * sp * vx3, -grav - c * sp * vz3
        vx4, vz4 = vx + dt * ax3, vz + dt * az3
        sp = sqrt(vx4 * vx4 + vz4 * vz4)
        ax4, az4 = -c * sp * vx4, -grav - c * sp * vz4
        x += sixth * (vx + 2 * vx2 + 2 * vx3 + vx4)
        z += sixth * (vz + 2 * vz2 + 2 * vz3 + vz4)
        vx += sixth * (ax1 + 2 * ax2 + 2 * ax3 + ax4)
        vz += sixth * (az1 + 2 * az2 + 2 * az3 + az4)
        ts.append(i * dt)
        xs.append(x)
        zs.append(z)
        vxs.append(vx)
        vzs.append(vz)
        landed = z <= 0
    if not landed:
        raise InputError(f"the rock has not landed by max_time = {t_max!r} s", argument="max_time")
    if len(ts) > 1:
        _land(ts, xs, zs, vxs, vzs, dt, c, grav)
    arrays = [np.array(a, dtype=np.float64) for a in (ts, xs, zs, vxs, vzs)]
    apex = _apex(arrays, dt, c, grav)
    t_arr, x_arr, z_arr, vx_arr, vz_arr = arrays
    return FlyrockTrajectory(t_arr, x_arr, z_arr, vx_arr, vz_arr, float(xs[-1]), float(ts[-1]), apex)


def _accel(vx: float, vz: float, c: float, grav: float) -> tuple[float, float]:
    speed = math.sqrt(vx * vx + vz * vz)
    return -c * speed * vx, -grav - c * speed * vz


def _land(
    ts: list[float],
    xs: list[float],
    zs: list[float],
    vxs: list[float],
    vzs: list[float],
    dt: float,
    c: float,
    grav: float,
) -> None:
    """Replace the last (below ground) sample by the landing point found by Hermite interpolation of z."""
    t0, x0, z0, vx0, vz0 = ts[-2], xs[-2], zs[-2], vxs[-2], vzs[-2]
    x1, z1, vx1, vz1 = xs[-1], zs[-1], vxs[-1], vzs[-1]
    s = bracketed_root(lambda f: _hermite(f, z0, vz0, z1, vz1, dt), 0, 1, rtol=_ROOT_RTOL) if z1 < 0 else 1
    ax0, az0 = _accel(vx0, vz0, c, grav)
    ax1, az1 = _accel(vx1, vz1, c, grav)
    ts[-1] = t0 + s * dt
    xs[-1] = _hermite(s, x0, vx0, x1, vx1, dt)
    zs[-1] = 0.0
    vxs[-1] = _hermite(s, vx0, ax0, vx1, ax1, dt)
    vzs[-1] = _hermite(s, vz0, az0, vz1, az1, dt)


def _apex(arrays: list[np.ndarray], dt: float, c: float, grav: float) -> float:
    """Highest point: the sampled maximum, refined on the step where the vertical velocity changes sign."""
    _, _, z, vx, vz = arrays
    rising = np.nonzero((vz[:-1] > 0) & (vz[1:] <= 0))[0]
    if rising.size == 0:
        return float(np.max(z))
    k = int(rising[0])
    step = float(arrays[0][k + 1] - arrays[0][k])
    _, az0 = _accel(float(vx[k]), float(vz[k]), c, grav)
    _, az1 = _accel(float(vx[k + 1]), float(vz[k + 1]), c, grav)
    s = bracketed_root(lambda f: _hermite(f, float(vz[k]), az0, float(vz[k + 1]), az1, step), 0, 1, rtol=_ROOT_RTOL)
    return max(float(np.max(z)), _hermite(s, float(z[k]), float(vz[k]), float(z[k + 1]), float(vz[k + 1]), step))


_HALF = 0.5
_ROOT_RTOL = 1e-13
