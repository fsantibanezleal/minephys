"""Beverloo discharge, repose-angle stockpile geometry and belt-conveyor capacity, tension and power (spec 004
FR-004-01 to FR-004-07)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import _tripwire as tw
from .. import knowledge
from .._constants import STANDARD_GRAVITY
from .._errors import InputError
from .._validate import as_checked, broadcast_all, check_bool, finalize

_HALF_PI = math.pi / 2


def _row(row_id: str) -> float:
    value = knowledge.get_value(row_id)
    assert not isinstance(value, tuple)
    return float(value)


def beverloo_discharge(
    orifice_diameter: Any,
    particle_diameter: Any,
    bulk_density: Any,
    discharge_coefficient: Any,
    annulus_coefficient: Any,
    g: Any = STANDARD_GRAVITY,
) -> Any:
    """Mass discharge rate of a granular material through a circular orifice (Beverloo's law).

    Parameters
    ----------
    orifice_diameter : float or array_like [m]
        Orifice diameter D, > 0.
    particle_diameter : float or array_like [m]
        Particle diameter d, > 0.
    bulk_density : float or array_like [kg/m^3]
        Bulk density of the flowing material, > 0.
    discharge_coefficient : float or array_like [1]
        Discharge coefficient C, > 0; no default (the literature range is a documented row).
    annulus_coefficient : float or array_like [1]
        Annulus (empty-ring) coefficient k, >= 0; no default.
    g : float or array_like [m/s^2]
        Gravitational acceleration, > 0; the default is standard gravity.

    Returns
    -------
    float or ndarray [kg/s]
        Mass discharge rate.

    Equation
    --------
    Q = C rho_b sqrt(g) (D - k d)^(5/2)

    Source
    ------
    mankoc2007beverloo, Eq. 1, p. 1 (Beverloo et al. 1961, beverloo1961flow, the primary source, was not read)

    Validity
    --------
    Coarse, cohesionless, free-flowing material through a circular orifice in a flat-bottomed bin. D <= k d (no
    free-flowing opening) raises InputError naming orifice_diameter. The exponent is an UNVERIFIED model constant, so
    every call emits UnverifiedParameterWarning. An orifice above 10 m, a particle above 1 m and a bulk density below
    100 kg/m^3 emit a ValidityWarning.

    Knowledge rows
    --------------
    beverloo_exponent, tripwire_orifice_diameter_max, tripwire_particle_diameter_max, tripwire_bulk_density_min
    """
    orifice = as_checked(orifice_diameter, "orifice_diameter", lo=0, lo_open=True)
    particle = as_checked(particle_diameter, "particle_diameter", lo=0, lo_open=True)
    rho = as_checked(bulk_density, "bulk_density", lo=0, lo_open=True)
    c = as_checked(discharge_coefficient, "discharge_coefficient", lo=0, lo_open=True)
    k = as_checked(annulus_coefficient, "annulus_coefficient", lo=0)
    grav = as_checked(g, "g", lo=0, lo_open=True)
    orifice, particle, rho, c, k, grav = broadcast_all(
        orifice_diameter=orifice,
        particle_diameter=particle,
        bulk_density=rho,
        discharge_coefficient=c,
        annulus_coefficient=k,
        g=grav,
    )
    free = orifice - k * particle
    closed = free <= 0
    if closed.any():
        i = int(np.argmax(closed.ravel()))
        raise InputError(
            f"argument 'orifice_diameter' must exceed annulus_coefficient * particle_diameter (no free-flowing "
            f"opening), got {float(orifice.ravel()[i])!r} against {float((k * particle).ravel()[i])!r}",
            argument="orifice_diameter",
        )
    tw.warn_max(orifice, "orifice_diameter", "tripwire_orifice_diameter_max")
    tw.warn_max(particle, "particle_diameter", "tripwire_particle_diameter_max")
    tw.warn_min(rho, "bulk_density", "tripwire_bulk_density_min")
    exponent = _row("beverloo_exponent")
    return finalize(c * rho * np.sqrt(grav) * free**exponent, orifice, particle, rho, c, k, grav)


def repose_cone_height(base_radius: Any, repose_angle: Any) -> Any:
    """Height of a conical stockpile at its angle of repose.

    Parameters
    ----------
    base_radius : float or array_like [m]
        Radius of the cone base r, > 0.
    repose_angle : float or array_like [rad]
        Angle of repose phi, 0 < phi < pi/2.

    Returns
    -------
    float or ndarray [m]
        Cone height.

    Equation
    --------
    h = r tan(phi)

    Source
    ------
    minephys:spec-004-bulk, section 3 (FR-004-03; solid geometry, no empirical constant)

    Validity
    --------
    An ideal cone at one repose angle; toe and crest rounding are ignored. An angle above 1.05 rad (60 degrees)
    emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_repose_angle_max
    """
    r, phi = _cone_inputs(base_radius, repose_angle, "base_radius")
    return finalize(r * np.tan(phi), r, phi)


def repose_cone_volume(base_radius: Any, repose_angle: Any) -> Any:
    """Volume of a conical stockpile at its angle of repose.

    Parameters
    ----------
    base_radius : float or array_like [m]
        Radius of the cone base r, > 0.
    repose_angle : float or array_like [rad]
        Angle of repose phi, 0 < phi < pi/2.

    Returns
    -------
    float or ndarray [m^3]
        Cone volume.

    Equation
    --------
    V = (pi / 3) r^3 tan(phi)

    Source
    ------
    minephys:spec-004-bulk, section 3 (FR-004-03; solid geometry, no empirical constant)

    Validity
    --------
    An ideal cone at one repose angle; toe and crest rounding are ignored. An angle above 1.05 rad (60 degrees)
    emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_repose_angle_max
    """
    r, phi = _cone_inputs(base_radius, repose_angle, "base_radius")
    return finalize(_cone(r, phi), r, phi)


def repose_ridge_volume(base_half_width: Any, repose_angle: Any, length: Any, end_cones: Any = False) -> Any:
    """Volume of a prismatic ridge stockpile at its angle of repose, optionally with conical ends.

    Parameters
    ----------
    base_half_width : float or array_like [m]
        Half of the ridge base width r, > 0.
    repose_angle : float or array_like [rad]
        Angle of repose phi, 0 < phi < pi/2.
    length : float or array_like [m]
        Length of the prismatic part, >= 0.
    end_cones : bool
        When True the two half-cones of the ends are added.

    Returns
    -------
    float or ndarray [m^3]
        Ridge volume.

    Equation
    --------
    V = r^2 tan(phi) L, plus (pi / 3) r^3 tan(phi) when end_cones is True

    Source
    ------
    minephys:spec-004-bulk, section 3 (FR-004-04; solid geometry, no empirical constant)

    Validity
    --------
    An ideal ridge with a triangular cross-section at one repose angle. An angle above 1.05 rad (60 degrees) emits a
    ValidityWarning.

    Knowledge rows
    --------------
    tripwire_repose_angle_max
    """
    r, phi = _cone_inputs(base_half_width, repose_angle, "base_half_width")
    ln = as_checked(length, "length", lo=0)
    flag = check_bool(end_cones, "end_cones")
    r, phi, ln, flag = broadcast_all(base_half_width=r, repose_angle=phi, length=ln, end_cones=np.asarray(flag))
    volume = r * r * np.tan(phi) * ln
    return finalize(volume + np.where(flag, _cone(r, phi), 0), r, phi, ln, flag)


def _cone_inputs(radius: Any, angle: Any, name: str) -> tuple[Any, Any]:
    r = as_checked(radius, name, lo=0, lo_open=True)
    phi = as_checked(angle, "repose_angle", lo=0, hi=_HALF_PI, lo_open=True, hi_open=True)
    r, phi = broadcast_all(**{name: r, "repose_angle": phi})
    tw.warn_max(phi, "repose_angle", "tripwire_repose_angle_max")
    return r, phi


def _cone(r: Any, phi: Any) -> Any:
    return (math.pi / 3) * r**3 * np.tan(phi)


def conveyor_capacity(load_area: Any, belt_speed: Any, bulk_density: Any) -> Any:
    """Mass flow of material carried by a belt conveyor.

    Parameters
    ----------
    load_area : float or array_like [m^2]
        Cross-section area of the load on the belt A, > 0.
    belt_speed : float or array_like [m/s]
        Belt speed V, > 0.
    bulk_density : float or array_like [kg/m^3]
        Bulk density of the material, > 0.

    Returns
    -------
    float or ndarray [kg/s]
        Mass flow.

    Equation
    --------
    Q = rho_b A V

    Source
    ------
    minephys:spec-004-bulk, section 3 (FR-004-05; continuity, no empirical constant)

    Validity
    --------
    Steady load on the belt; the cross-section area is the user's (a CEMA table value or a measurement). A belt
    speed above 15 m/s and a bulk density below 100 kg/m^3 emit a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_belt_speed_max, tripwire_bulk_density_min
    """
    a = as_checked(load_area, "load_area", lo=0, lo_open=True)
    v = as_checked(belt_speed, "belt_speed", lo=0, lo_open=True)
    rho = as_checked(bulk_density, "bulk_density", lo=0, lo_open=True)
    a, v, rho = broadcast_all(load_area=a, belt_speed=v, bulk_density=rho)
    tw.warn_max(v, "belt_speed", "tripwire_belt_speed_max")
    tw.warn_min(rho, "bulk_density", "tripwire_bulk_density_min")
    return finalize(rho * a * v, a, v, rho)


def cema_effective_tension(
    length: Any,
    lift: Any,
    belt_weight: Any,
    material_weight: Any,
    kt: Any,
    kx: Any,
    ky: Any,
    pulley_tension: Any = 0,
    acceleration_tension: Any = 0,
    accessory_tension: Any = 0,
) -> Any:
    """Effective tension of a belt conveyor, in the public form of the CEMA method with the caller's factors.

    Parameters
    ----------
    length : float or array_like [m]
        Conveyor length L, >= 0.
    lift : float or array_like [m]
        Net lift H, finite; negative for a decline.
    belt_weight : float or array_like [N/m]
        Belt weight per length W_b, >= 0.
    material_weight : float or array_like [N/m]
        Material weight per length W_m, >= 0.
    kt : float or array_like [1]
        Temperature correction factor K_t, >= 0; no default.
    kx : float or array_like [N/m]
        Idler friction and flexure factor K_x, >= 0; no default.
    ky : float or array_like [1]
        Carry-flexure factor K_y, >= 0; no default.
    pulley_tension : float or array_like [N]
        Tension from the pulleys T_p, >= 0.
    acceleration_tension : float or array_like [N]
        Tension to accelerate the material T_am, >= 0.
    accessory_tension : float or array_like [N]
        Tension from the accessories T_ac, >= 0.

    Returns
    -------
    float or ndarray [N]
        Effective tension T_e (negative when a decline drives the belt).

    Equation
    --------
    T_e = L K_t (K_x + K_y W_b + 0.015 W_b) + W_m (L K_y + H) + T_p + T_am + T_ac

    Source
    ------
    cema_belt_conveyors_7th, effective tension equation (printed in pdhonline_m344, p. 13)

    Validity
    --------
    Only the published equation: no CEMA table is reproduced and K_x, K_y and K_t come from the user's copy of the
    standard or a measurement. The 0.015 return-belt coefficient is an UNVERIFIED model constant (secondary source
    only), so every call emits UnverifiedParameterWarning.

    Knowledge rows
    --------------
    cema_return_belt_coefficient
    """
    ln = as_checked(length, "length", lo=0)
    h = as_checked(lift, "lift")
    wb = as_checked(belt_weight, "belt_weight", lo=0)
    wm = as_checked(material_weight, "material_weight", lo=0)
    k_t = as_checked(kt, "kt", lo=0)
    k_x = as_checked(kx, "kx", lo=0)
    k_y = as_checked(ky, "ky", lo=0)
    t_p = as_checked(pulley_tension, "pulley_tension", lo=0)
    t_am = as_checked(acceleration_tension, "acceleration_tension", lo=0)
    t_ac = as_checked(accessory_tension, "accessory_tension", lo=0)
    named = {
        "length": ln,
        "lift": h,
        "belt_weight": wb,
        "material_weight": wm,
        "kt": k_t,
        "kx": k_x,
        "ky": k_y,
        "pulley_tension": t_p,
        "acceleration_tension": t_am,
        "accessory_tension": t_ac,
    }
    ln, h, wb, wm, k_t, k_x, k_y, t_p, t_am, t_ac = broadcast_all(**named)
    coefficient = _row("cema_return_belt_coefficient")
    tension = ln * k_t * (k_x + k_y * wb + coefficient * wb) + wm * (ln * k_y + h) + t_p + t_am + t_ac
    return finalize(tension, *named.values())


def conveyor_power(effective_tension: Any, belt_speed: Any, drive_efficiency: Any = 1) -> Any:
    """Drive power of a belt conveyor, motoring or regenerating.

    Parameters
    ----------
    effective_tension : float or array_like [N]
        Effective tension T_e, finite; negative for a decline that drives the belt.
    belt_speed : float or array_like [m/s]
        Belt speed V, > 0.
    drive_efficiency : float or array_like [1]
        Drive efficiency eta, 0 < eta <= 1.

    Returns
    -------
    float or ndarray [W]
        Shaft power, negative when power is regenerated.

    Equation
    --------
    P = T_e V / eta for T_e >= 0 and P = T_e V eta for T_e < 0

    Source
    ------
    minephys:spec-004-bulk, section 3 (FR-004-07; a power balance, no empirical constant)

    Validity
    --------
    Steady running, with one drive efficiency in both directions. A belt speed above 15 m/s emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_belt_speed_max
    """
    te = as_checked(effective_tension, "effective_tension")
    v = as_checked(belt_speed, "belt_speed", lo=0, lo_open=True)
    eta = as_checked(drive_efficiency, "drive_efficiency", lo=0, hi=1, lo_open=True)
    te, v, eta = broadcast_all(effective_tension=te, belt_speed=v, drive_efficiency=eta)
    tw.warn_max(v, "belt_speed", "tripwire_belt_speed_max")
    return finalize(np.where(te >= 0, te * v / eta, te * v * eta), te, v, eta)
