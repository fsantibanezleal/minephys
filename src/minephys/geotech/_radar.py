"""Line-of-sight projection and interferometric phase of a ground-based slope radar (spec 003 FR-003-18, FR-003-19,
FR-003-20, FR-003-21, FR-003-23). Positive line-of-sight displacement and positive phase mean a range increase."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import knowledge
from .._errors import InputError
from .._random import as_generator
from .._validate import (
    FloatArray,
    as_checked,
    as_float_array,
    broadcast_all,
    check_finite,
    finalize,
    warn_validity,
)


def _vectors(displacement: Any, radar_position: Any, target_position: Any) -> tuple[FloatArray, FloatArray, FloatArray]:
    arrays = {}
    for name, value in (
        ("displacement", displacement),
        ("radar_position", radar_position),
        ("target_position", target_position),
    ):
        arr = as_float_array(value, name)
        if arr.ndim < 1 or arr.shape[-1] != 3:
            raise InputError(f"argument '{name}' needs 3-vectors in its last axis, got shape {tuple(arr.shape)}", argument=name)
        arrays[name] = check_finite(arr, name)
    return arrays["displacement"], arrays["radar_position"], arrays["target_position"]


def slope_radar_los(displacement: Any, radar_position: Any, target_position: Any) -> Any:
    """Line-of-sight component of a displacement seen by a radar.

    Parameters
    ----------
    displacement : array_like [m]
        Displacement vectors, 3-vectors in the last axis.
    radar_position : array_like [m]
        Radar positions, 3-vectors in the last axis.
    target_position : array_like [m]
        Target positions, 3-vectors in the last axis; each must differ from its radar position.

    Returns
    -------
    numpy.float64 or ndarray [m]
        Line-of-sight displacement, positive for motion away from the radar (range increase); the leading axes
        of the three arguments broadcast.

    Equation
    --------
    d = u . e with e = (target - radar) / |target - radar|

    Source
    ------
    monserrat2014, eq. 4, p. 4 (the sign convention of the phase relation)

    Validity
    --------
    Geometric projection only: no atmosphere, focusing or phase unwrapping.

    Knowledge rows
    --------------
    none
    """
    u, radar, target = _vectors(displacement, radar_position, target_position)
    try:
        lead = np.broadcast_shapes(u.shape[:-1], radar.shape[:-1], target.shape[:-1])
    except ValueError:
        raise InputError(
            "arguments displacement, radar_position, target_position cannot be broadcast together: "
            f"displacement has shape {tuple(u.shape)}, radar_position has shape {tuple(radar.shape)}, "
            f"target_position has shape {tuple(target.shape)}",
            argument="displacement, radar_position, target_position",
        ) from None
    diff = np.broadcast_to(target, (*lead, 3)) - np.broadcast_to(radar, (*lead, 3))
    if not np.all(np.isfinite(diff)):
        raise InputError("the radar-target vector overflows: positions are too large", argument="target_position")
    scale = np.max(np.abs(diff), axis=-1, keepdims=True)
    if np.any(scale == 0):
        raise InputError("radar_position and target_position must be distinct", argument="target_position")
    unit = diff / scale
    unit = unit / np.sqrt(np.sum(unit * unit, axis=-1, keepdims=True))
    projection = np.sum(np.broadcast_to(u, (*lead, 3)) * unit, axis=-1)
    return np.float64(projection) if projection.ndim == 0 else projection.astype(np.float64)


def _wavelength(value: Any) -> FloatArray:
    arr = as_checked(value, "wavelength", lo=0, lo_open=True)
    low, high = knowledge.get_value("tripwire_wavelength_range")  # type: ignore[misc]
    warn_validity(arr, "wavelength", low, high, "tripwire_wavelength_range", stacklevel=4)
    return arr


def los_phase(los_displacement: Any, wavelength: Any, noise_sd: Any = 0, rng: Any = None) -> Any:
    """Unwrapped two-way interferometric phase of a line-of-sight displacement, optionally with Gaussian noise.

    Parameters
    ----------
    los_displacement : float or array_like [m]
        Line-of-sight displacement, positive for a range increase.
    wavelength : float or array_like [m]
        Radar wavelength, > 0 (no default: the Ku band is 1.75 cm).
    noise_sd : float or array_like [rad]
        Standard deviation of the added Gaussian phase noise, >= 0.
    rng : numpy.random.Generator or int
        Random source for the noise (a Generator or an integer seed); required when noise_sd > 0.

    Returns
    -------
    float or ndarray [rad]
        Unwrapped phase, positive for a range increase.

    Equation
    --------
    delta_phi = 4 pi d / lambda (+ noise_sd z with independent standard normal z per element)

    Source
    ------
    monserrat2014, eq. 4, p. 4

    Validity
    --------
    wavelength outside tripwire_wavelength_range (mm passed as m) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_wavelength_range
    """
    d = as_checked(los_displacement, "los_displacement")
    lam = _wavelength(wavelength)
    sd = as_checked(noise_sd, "noise_sd", lo=0)
    generator = None if rng is None else as_generator(rng)
    d, lam, sd = broadcast_all(los_displacement=d, wavelength=lam, noise_sd=sd)
    phase = 4 * math.pi * d / lam
    if np.any(sd > 0):
        if generator is None:
            raise InputError("argument 'rng' is required when noise_sd > 0", argument="rng")
        phase = phase + sd * generator.standard_normal(phase.shape)
    return finalize(phase, d, lam, sd)


def wrap_phase(phase: Any) -> Any:
    """Map a phase to the interval (-pi, pi].

    Parameters
    ----------
    phase : float or array_like [rad]
        Phase to wrap.

    Returns
    -------
    float or ndarray [rad]
        The same angle in (-pi, pi]; pi stays pi and -pi maps to pi.

    Equation
    --------
    wrapped = phi - 2 pi ceil((phi - pi) / (2 pi))

    Source
    ------
    monserrat2014, eq. 7, p. 9 (phase wrapping and the ambiguity limit)

    Validity
    --------
    The value is exact up to rounding of the argument; beyond about 1e6 rad the reduction loses its precision.

    Knowledge rows
    --------------
    none
    """
    phi = as_checked(phase, "phase")
    turn = 2 * math.pi
    with np.errstate(over="ignore", invalid="ignore"):
        wrapped = phi - turn * np.ceil((phi - math.pi) / turn)
    if not np.all(np.isfinite(wrapped)):
        raise InputError("the phase is too large to be reduced to one turn", argument="phase")
    return finalize(wrapped, phi)


def los_from_phase(phase: Any, wavelength: Any) -> Any:
    """Line-of-sight displacement of an unwrapped two-way phase.

    Parameters
    ----------
    phase : float or array_like [rad]
        Unwrapped phase.
    wavelength : float or array_like [m]
        Radar wavelength, > 0.

    Returns
    -------
    float or ndarray [m]
        Line-of-sight displacement, positive for a range increase.

    Equation
    --------
    d = lambda delta_phi / (4 pi)

    Source
    ------
    monserrat2014, eq. 4, p. 4

    Validity
    --------
    wavelength outside tripwire_wavelength_range emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_wavelength_range
    """
    phi = as_checked(phase, "phase")
    lam = _wavelength(wavelength)
    phi, lam = broadcast_all(phase=phi, wavelength=lam)
    return finalize(lam * phi / (4 * math.pi), phi, lam)


def max_unambiguous_los_step(wavelength: Any) -> Any:
    """Largest line-of-sight step between two scans that the wrapped phase can represent.

    Parameters
    ----------
    wavelength : float or array_like [m]
        Radar wavelength, > 0.

    Returns
    -------
    float or ndarray [m]
        lambda / 4.

    Equation
    --------
    max |d| = lambda / 4

    Source
    ------
    monserrat2014, eq. 7, p. 9

    Validity
    --------
    wavelength outside tripwire_wavelength_range emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_wavelength_range
    """
    lam = _wavelength(wavelength)
    return finalize(lam / 4, lam)

