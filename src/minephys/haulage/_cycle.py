"""Loading passes, travel and cycle time, fuel and CO2, and the match factor (spec 001 FR-001-08 to FR-001-10,
FR-001-13 to FR-001-15, FR-001-18)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .. import _tripwire as tw
from .. import knowledge, units
from .._errors import InputError
from .._validate import as_checked, as_count, broadcast_all, finalize

_INTEGER_RULE = 1e-12  # a quotient within this relative distance of an integer counts as that integer
_MAX_COUNT = 100_000


def loose_density(bank_density: Any, swell: Any) -> Any:
    """Loose (swollen) density of broken rock.

    Parameters
    ----------
    bank_density : float or array_like [kg/m^3]
        In-situ (bank) density, > 0.
    swell : float or array_like [1]
        Swell factor as a fraction, >= 0.

    Returns
    -------
    float or ndarray [kg/m^3]
        Loose density.

    Equation
    --------
    rho_loose = rho_bank / (1 + swell)

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-08; an elementary volume balance, no empirical constant)

    Validity
    --------
    bank_density < tripwire_bank_density_min or swell > tripwire_swell_max emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_bank_density_min, tripwire_swell_max
    """
    bank = as_checked(bank_density, "bank_density", lo=0, lo_open=True)
    sw = as_checked(swell, "swell", lo=0)
    bank, sw = broadcast_all(bank_density=bank, swell=sw)
    tw.warn_min(bank, "bank_density", "tripwire_bank_density_min")
    tw.warn_max(sw, "swell", "tripwire_swell_max")
    return finalize(bank / (1 + sw), bank, sw)


def loading_passes(target_payload: Any, bucket_volume: Any, fill_factor: Any, loose_density: Any) -> Any:
    """Number of loader passes needed to fill a truck.

    Parameters
    ----------
    target_payload : float or array_like [kg]
        Payload to load, > 0.
    bucket_volume : float or array_like [m^3]
        Bucket (struck) volume, > 0.
    fill_factor : float or array_like [1]
        Bucket fill factor, 0 < k <= 2 (above 1 for heaped buckets).
    loose_density : float or array_like [kg/m^3]
        Loose density of the material, > 0.

    Returns
    -------
    numpy.int64 or ndarray [count]
        Smallest integer n >= 1 with n V k rho >= payload; a quotient within a relative 1e-12 of an integer counts as
        that integer. int64, not float64.

    Equation
    --------
    n = max(1, ceil(payload / (V k rho))), with the integer rule above.

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-09; an elementary capacity balance, no empirical constant)

    Validity
    --------
    More than 2**62 passes is an InputError naming target_payload.

    Knowledge rows
    --------------
    none
    """
    payload = as_checked(target_payload, "target_payload", lo=0, lo_open=True)
    volume = as_checked(bucket_volume, "bucket_volume", lo=0, lo_open=True)
    fill = as_checked(fill_factor, "fill_factor", lo=0, hi=2, lo_open=True)
    rho = as_checked(loose_density, "loose_density", lo=0, lo_open=True)
    payload, volume, fill, rho = broadcast_all(
        target_payload=payload, bucket_volume=volume, fill_factor=fill, loose_density=rho
    )
    with np.errstate(over="ignore", invalid="ignore"):
        quotient = payload / (volume * fill * rho)
    if np.any(~np.isfinite(quotient) | (quotient > float(2**62))):
        raise InputError("argument 'target_payload' needs more than 2**62 loader passes", argument="target_payload")
    nearest = np.rint(quotient)
    on_integer = (nearest >= 1) & (np.abs(quotient - nearest) <= _INTEGER_RULE * quotient)
    passes = np.where(on_integer, nearest, np.maximum(1, np.ceil(quotient))).astype(np.int64)
    return np.int64(passes[()]) if passes.ndim == 0 else passes


def segment_travel_time(length: Any, speed: Any) -> Any:
    """Travel time of a road segment at constant speed.

    Parameters
    ----------
    length : float or array_like [m]
        Segment length along the road, >= 0.
    speed : float or array_like [m/s]
        Constant speed, > 0.

    Returns
    -------
    float or ndarray [s]
        Travel time.

    Equation
    --------
    t = length / speed

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-10; kinematics, no empirical constant)

    Validity
    --------
    Constant speed over the segment.

    Knowledge rows
    --------------
    none
    """
    ln = as_checked(length, "length", lo=0)
    v = as_checked(speed, "speed", lo=0, lo_open=True)
    ln, v = broadcast_all(length=ln, speed=v)
    return finalize(ln / v, ln, v)


def cycle_time(
    spot_load: Any,
    load: Any,
    haul_travel: Any,
    spot_dump: Any,
    dump: Any,
    return_travel: Any,
    queue_load: Any = 0,
    queue_dump: Any = 0,
) -> Any:
    """Truck cycle time as the sum of its eight components.

    Parameters
    ----------
    spot_load : float or array_like [s]
        Spotting time at the loader, >= 0.
    load : float or array_like [s]
        Loading time, >= 0.
    haul_travel : float or array_like [s]
        Loaded travel time, >= 0.
    spot_dump : float or array_like [s]
        Spotting time at the dump, >= 0.
    dump : float or array_like [s]
        Dumping time, >= 0.
    return_travel : float or array_like [s]
        Empty travel time, >= 0.
    queue_load : float or array_like [s]
        Waiting time at the loader, >= 0.
    queue_dump : float or array_like [s]
        Waiting time at the dump, >= 0.

    Returns
    -------
    float or ndarray [s]
        Cycle time.

    Equation
    --------
    T = spot_load + load + haul_travel + spot_dump + dump + return_travel + queue_load + queue_dump

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-10; a sum of times, no empirical constant)

    Validity
    --------
    All components are non-negative durations.

    Knowledge rows
    --------------
    none
    """
    parts = {
        "spot_load": spot_load,
        "load": load,
        "haul_travel": haul_travel,
        "spot_dump": spot_dump,
        "dump": dump,
        "return_travel": return_travel,
        "queue_load": queue_load,
        "queue_dump": queue_dump,
    }
    checked = {name: as_checked(value, name, lo=0) for name, value in parts.items()}
    arrays = broadcast_all(**checked)
    total = arrays[0]
    for part in arrays[1:]:
        total = total + part
    return finalize(total, *arrays)


def fuel_use(source_energy: Any, fuel_energy_density: Any) -> Any:
    """Fuel volume that supplies a given energy.

    Parameters
    ----------
    source_energy : float or array_like [J]
        Energy drawn from the fuel, >= 0.
    fuel_energy_density : float or array_like [J/m^3]
        Volumetric energy content of the fuel, > 0.

    Returns
    -------
    float or ndarray [m^3]
        Fuel volume.

    Equation
    --------
    V = E / e_fuel

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-13; an energy balance, the caller supplies the fuel density)

    Validity
    --------
    fuel_energy_density < tripwire_fuel_energy_density_min (MJ/L passed as J/m^3) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_fuel_energy_density_min
    """
    energy = as_checked(source_energy, "source_energy", lo=0)
    density = as_checked(fuel_energy_density, "fuel_energy_density", lo=0, lo_open=True)
    energy, density = broadcast_all(source_energy=energy, fuel_energy_density=density)
    tw.warn_min(density, "fuel_energy_density", "tripwire_fuel_energy_density_min")
    return finalize(energy / density, energy, density)


def co2_from_diesel(fuel_volume: Any, emission_factor: Any = None) -> Any:
    """Combustion CO2 of diesel fuel.

    Parameters
    ----------
    fuel_volume : float or array_like [m^3]
        Diesel volume burned, >= 0.
    emission_factor : float or array_like [kg/m^3]
        CO2 per unit fuel volume, > 0; None uses the verified row (10.21 kg per US gallon converted to SI).

    Returns
    -------
    float or ndarray [kg]
        CO2 mass (combustion only, no upstream emissions).

    Equation
    --------
    m_CO2 = V f, with f = 10.21 kg / (231 in^3) = 2,697.1967 kg/m^3 by default.

    Source
    ------
    epa2025ghghub, Table 2, p. 2

    Validity
    --------
    Tank-to-wheel combustion CO2 only; the CH4 and N2O factors are not implemented.

    Knowledge rows
    --------------
    diesel_co2_kg_per_us_gal
    """
    volume = as_checked(fuel_volume, "fuel_volume", lo=0)
    if emission_factor is None:
        factor = np.asarray(float(knowledge.get_value("diesel_co2_kg_per_us_gal")) / float(units.us_gal_to_m3(1)))  # type: ignore[arg-type]
    else:
        factor = as_checked(emission_factor, "emission_factor", lo=0, lo_open=True)
    volume, factor = broadcast_all(fuel_volume=volume, emission_factor=factor)
    return finalize(volume * factor, volume, factor)


def co2_from_electricity(energy: Any, grid_intensity: Any) -> Any:
    """CO2 of grid electricity.

    Parameters
    ----------
    energy : float or array_like [J]
        Electric energy drawn, >= 0.
    grid_intensity : float or array_like [kg/J]
        Grid emission intensity, >= 0 (no default: it is a site value).

    Returns
    -------
    float or ndarray [kg]
        CO2 mass.

    Equation
    --------
    m_CO2 = E i_grid

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-15; a product, the caller supplies the intensity)

    Validity
    --------
    grid_intensity > tripwire_grid_intensity_max (kg/kWh passed as kg/J) emits a ValidityWarning.

    Knowledge rows
    --------------
    tripwire_grid_intensity_max
    """
    e = as_checked(energy, "energy", lo=0)
    intensity = as_checked(grid_intensity, "grid_intensity", lo=0)
    e, intensity = broadcast_all(energy=e, grid_intensity=intensity)
    tw.warn_max(intensity, "grid_intensity", "tripwire_grid_intensity_max")
    return finalize(e * intensity, e, intensity)


def match_factor(n_trucks: Any, n_loaders: Any, load_time: Any, cycle_time: Any) -> Any:
    """Homogeneous truck-loader match factor.

    Parameters
    ----------
    n_trucks : int or array_like [count]
        Number of trucks, an integer from 1 to 100,000.
    n_loaders : int or array_like [count]
        Number of loaders, an integer from 1 to 100,000.
    load_time : float or array_like [s]
        Loading time of one truck, > 0 and below the cycle time.
    cycle_time : float or array_like [s]
        Truck cycle time excluding waiting, > 0.

    Returns
    -------
    float or ndarray [1]
        Match factor (1 means fleet and loaders are balanced).

    Equation
    --------
    MF = n_trucks load_time / (n_loaders cycle_time)

    Source
    ------
    minephys:spec-001-haulage, section 3 (FR-001-18; the homogeneous ratio, the heterogeneous form was not read)

    Validity
    --------
    Homogeneous fleet; cycle_time excludes waiting.

    Knowledge rows
    --------------
    none
    """
    trucks = as_count(n_trucks, "n_trucks", hi=_MAX_COUNT)
    loaders = as_count(n_loaders, "n_loaders", hi=_MAX_COUNT)
    load = as_checked(load_time, "load_time", lo=0, lo_open=True)
    cycle = as_checked(cycle_time, "cycle_time", lo=0, lo_open=True)
    trucks, loaders, load, cycle = broadcast_all(n_trucks=trucks, n_loaders=loaders, load_time=load, cycle_time=cycle)
    if np.any(load >= cycle):
        raise InputError("argument 'load_time' must be smaller than cycle_time", argument="load_time")
    return finalize(trucks * load / (loaders * cycle), trucks, loaders, load, cycle)
