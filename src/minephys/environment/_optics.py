"""Beer-Lambert dust attenuation and the lidar return state (spec 006 FR-006-15 to FR-006-18)."""

from __future__ import annotations

from typing import Any, NamedTuple

import numpy as np

from .. import knowledge
from .._argcheck import FloatArray, non_negative, positive, row, scalar
from .._errors import InputError
from .._validate import as_float_array, broadcast_all, check_finite, check_option, check_rank, finalize

__all__ = [
    "LidarDustReturn",
    "beer_lambert_transmittance",
    "extinction_coefficient",
    "lidar_dust_return",
    "mass_extinction_coefficient",
    "path_transmittance",
]

MAX_PROFILE_POINTS = 10**6
TARGETS = {
    "retroreflective": "lidar_dust_min_transmittance_retroreflective",
    "low_reflectivity": "lidar_dust_min_transmittance_low_reflectivity",
}


class LidarDustReturn(NamedTuple):
    """One-way and two-way transmittance, optical depth, state and the leading edge of the dust cloud (None without a
    profile)."""

    transmittance: Any
    two_way_transmittance: Any
    optical_depth: Any
    state: Any
    leading_edge: float | None


def mass_extinction_coefficient(diameter: Any, particle_density: Any, extinction_efficiency: Any = None) -> Any:
    """Mass extinction coefficient of spherical particles.

    Parameters
    ----------
    diameter : float or array [m]
        Particle diameter D (> 0).
    particle_density : float or array [kg/m^3]
        Particle density (> 0).
    extinction_efficiency : float or array [1], optional
        Extinction efficiency Q_ext (> 0); None reads the UNVERIFIED large-particle row, which warns.

    Returns
    -------
    float or array [m^2/kg]
        Mass extinction coefficient.

    Equation
    --------
    k_m = 3 Q_ext / (2 rho_p D).

    Source
    ------
    bohren1983absorption (the large-particle limit Q_ext = 2, page not read: UNVERIFIED); geometry derived in spec 006.

    Validity
    --------
    Particles much larger than the wavelength; the default efficiency is a model constant, not a site value.

    Knowledge rows
    --------------
    extinction_efficiency_large_particle
    """
    d = positive(diameter, "diameter")
    rho = positive(particle_density, "particle_density")
    q = positive(extinction_efficiency, "extinction_efficiency") if extinction_efficiency is not None else None
    if q is None:
        q = np.asarray(row("extinction_efficiency_large_particle"))
    d, rho, q = broadcast_all(diameter=d, particle_density=rho, extinction_efficiency=q)
    return finalize(3 * q / (2 * rho * d), d, rho, q)


def extinction_coefficient(mass_concentration: Any, mass_extinction: Any) -> Any:
    """Extinction coefficient of airborne dust.

    Parameters
    ----------
    mass_concentration : float or array [kg/m^3]
        Dust mass concentration (>= 0).
    mass_extinction : float or array [m^2/kg]
        Mass extinction coefficient (>= 0).

    Returns
    -------
    float or array [1/m]
        Extinction coefficient beta.

    Equation
    --------
    beta = k_m C.

    Source
    ------
    bohren1983absorption (definition of the extinction coefficient, not read); product defined in spec 006 FR-006-15.

    Validity
    --------
    Linear in concentration.

    Knowledge rows
    --------------
    none
    """
    c, k = broadcast_all(
        mass_concentration=non_negative(mass_concentration, "mass_concentration"),
        mass_extinction=non_negative(mass_extinction, "mass_extinction"),
    )
    return finalize(k * c, c, k)


def beer_lambert_transmittance(extinction: Any, path_length: Any) -> Any:
    """Transmittance of a uniform dusty path.

    Parameters
    ----------
    extinction : float or array [1/m]
        Extinction coefficient beta (>= 0).
    path_length : float or array [m]
        Path length (>= 0).

    Returns
    -------
    float or array [fraction]
        One-way transmittance.

    Equation
    --------
    T = exp(-beta L).

    Source
    ------
    bohren1983absorption (Beer-Lambert law, not read); definition in spec 006 FR-006-16.

    Validity
    --------
    Single scattering, uniform medium.

    Knowledge rows
    --------------
    none
    """
    b, length = broadcast_all(
        extinction=non_negative(extinction, "extinction"), path_length=non_negative(path_length, "path_length")
    )
    return finalize(np.exp(-b * length), b, length)


def _threshold(value: Any, name: str) -> float:
    v = scalar(value, name, lo=0, lo_open=True)
    if not v < 1:
        raise InputError(f"argument '{name}' must be below 1, got {v!r}", argument=name)
    return v


def _profile(positions: Any, profile: Any, pos_name: str, prof_name: str) -> tuple[FloatArray, FloatArray]:
    p = check_finite(as_float_array(positions, pos_name), pos_name)
    check_rank(p, pos_name, 1)
    if not 2 <= p.size <= MAX_PROFILE_POINTS:
        raise InputError(
            f"argument '{pos_name}' needs 2 to {MAX_PROFILE_POINTS:,} points, got {p.size}", argument=pos_name
        )
    if np.any(np.diff(p) <= 0):
        raise InputError(f"argument '{pos_name}' must be strictly increasing", argument=pos_name)
    beta = non_negative(profile, prof_name)
    if beta.ndim < 1 or beta.shape[-1] != p.size:
        raise InputError(
            f"argument '{prof_name}' must have {p.size} points along its last axis, got shape {tuple(beta.shape)}",
            argument=prof_name,
        )
    return p, beta


def _depth(p: FloatArray, beta: FloatArray) -> FloatArray:
    return np.sum((beta[..., 1:] + beta[..., :-1]) / 2 * np.diff(p), axis=-1)


def path_transmittance(positions: Any, extinction_profile: Any) -> Any:
    """Transmittance of a path with a non-uniform extinction profile.

    Parameters
    ----------
    positions : array [m]
        Positions along the path (1-D, strictly increasing, 2 to 10^6 points).
    extinction_profile : array [1/m]
        Extinction coefficient at the positions (>= 0), along the last axis.

    Returns
    -------
    float or array [fraction]
        One-way transmittance, reduced over the profile axis.

    Equation
    --------
    T = exp(-integral of beta ds), the integral by the trapezoid rule (exact for piecewise-linear profiles).

    Source
    ------
    bohren1983absorption (Beer-Lambert law, not read); trapezoid rule in spec 006 FR-006-16.

    Validity
    --------
    Up to 10^6 profile points.

    Knowledge rows
    --------------
    none
    """
    p, beta = _profile(positions, extinction_profile, "positions", "extinction_profile")
    return finalize(np.exp(-_depth(p, beta)), beta[..., 0])


def lidar_dust_return(
    distance: Any,
    extinction: Any,
    positions: Any = None,
    target: str = "retroreflective",
    onset_transmittance: Any = None,
    min_transmittance: Any = None,
) -> LidarDustReturn:
    """Lidar return state through dust, calibrated to the thresholds of a mining-dust study.

    Parameters
    ----------
    distance : float or array [m]
        Sensor-to-target distance (> 0).
    extinction : float or array [1/m]
        Uniform extinction coefficient, or with `positions` the profile along its last axis (>= 0).
    positions : array [m], optional
        Profile positions, from 0 to `distance`, strictly increasing.
    target : str [option]
        "retroreflective" or "low_reflectivity".
    onset_transmittance : float [fraction], optional
        Transmittance below which dust affects the lidar; None reads the upper end of the published 71 to 74 % band.
    min_transmittance : float [fraction], optional
        Transmittance below which the target is lost; None reads the row of the target (2 % or 6 %).

    Returns
    -------
    LidarDustReturn
        `transmittance` (one-way T), `two_way_transmittance` (T^2), `optical_depth` (-ln T) [1], `state` ("unaffected",
        "degraded" or "lost") and `leading_edge` [m] (first position with beta > 0, or None).

    Equation
    --------
    State "unaffected" where T >= onset, "degraded" where the target minimum <= T < onset, "lost" below the minimum.

    Source
    ------
    phillips2017dust abstract (71 to 74 %, 2 % and 6 % transmittance thresholds); applying them to the one-way
    transmittance
    is an UNVERIFIED interpretation (spec 006 section 7).

    Validity
    --------
    Thresholds are quite variable with conditions; thresholds outside (0, 1) or a minimum at or above the onset raise
    InputError.

    Knowledge rows
    --------------
    lidar_dust_onset_transmittance, lidar_dust_min_transmittance_retroreflective,
    lidar_dust_min_transmittance_low_reflectivity
    """
    dist = positive(distance, "distance")
    kind = check_option(target, "target", tuple(TARGETS))
    onset = (
        float(knowledge.get_value("lidar_dust_onset_transmittance")[1])  # type: ignore[index]
        if onset_transmittance is None
        else _threshold(onset_transmittance, "onset_transmittance")
    )
    floor = row(TARGETS[kind]) if min_transmittance is None else _threshold(min_transmittance, "min_transmittance")
    if not floor < onset:
        raise InputError(
            "argument 'min_transmittance' must be smaller than the onset transmittance", argument="min_transmittance"
        )
    leading: float | None = None
    if positions is None:
        beta = non_negative(extinction, "extinction")
        beta, dist = broadcast_all(extinction=beta, distance=dist)
        depth = beta * dist
    else:
        p, beta = _profile(positions, extinction, "positions", "extinction")
        if dist.ndim != 0:
            raise InputError("argument 'distance' must be a scalar when a profile is given", argument="distance")
        if p[0] != 0 or p[-1] != float(dist):
            raise InputError("argument 'positions' must run from 0 to 'distance'", argument="positions")
        depth = _depth(p, beta)
        if beta.ndim == 1:
            hits = np.flatnonzero(beta > 0)
            leading = float(p[hits[0]]) if hits.size else None
    t = np.exp(-depth)
    state = np.where(t >= onset, "unaffected", np.where(t >= floor, "degraded", "lost"))
    state_out: Any = str(state) if state.ndim == 0 else state
    return LidarDustReturn(finalize(t, depth), finalize(t * t, depth), finalize(depth, depth), state_out, leading)
