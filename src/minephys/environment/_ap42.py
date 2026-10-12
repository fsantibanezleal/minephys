"""AP-42 section 13.2.2 unpaved-road dust: emission factor, validity, fleet weight, precipitation and watering (spec
006).

The equation is published in US customary units; the functions take SI arguments and convert with exact definitions read
from knowledge rows (pound and foot of the `units` table, the mile as 5,280 feet, the short ton as its own conversion
row).
"""

from __future__ import annotations

import collections
import warnings
from typing import Any

import numpy as np

from .. import knowledge
from .._argcheck import FloatArray, non_negative, positive, row, unit_interval
from .._errors import InputError, InputTypeError, ValidityWarning
from .._validate import as_float_array, broadcast_all, check_domain, check_finite, check_option, check_rank, finalize

__all__ = [
    "ap42_unpaved_emission_factor",
    "ap42_unpaved_validity",
    "controlled_emission_factor",
    "fleet_mean_vehicle_weight",
    "line_emission_rate",
    "precipitation_correction",
    "watering_control_efficiency",
]

SIZE_CLASSES = {"PM2.5": "pm25", "PM10": "pm10", "PM30": "pm30"}
PERCENT = 100
FEET_PER_MILE = 5280
SECONDS_PER_HOUR = 3600
_validity_types: dict[tuple[str, ...], type] = {}


def _range(row_id: str) -> tuple[float, float]:
    lo, hi = knowledge.get_value(row_id)  # type: ignore[misc]
    return float(lo), float(hi)


def _mile() -> float:
    return row("ap42_mile_in_m")


def _mph() -> float:
    return _mile() / SECONDS_PER_HOUR


def _checked(
    value: Any, name: str, *, lo: float | None = None, lo_open: bool = False, hi: float | None = None
) -> FloatArray:
    return check_domain(check_finite(as_float_array(value, name), name), name, lo=lo, hi=hi, lo_open=lo_open)


def _inputs(
    silt_fraction: Any, mean_weight: Any, mean_speed: Any, mean_wheels: Any, moisture_fraction: Any
) -> dict[str, FloatArray]:
    given: dict[str, FloatArray] = {
        "silt_fraction": _checked(silt_fraction, "silt_fraction", lo=0, lo_open=True, hi=1),
        "mean_weight": positive(mean_weight, "mean_weight"),
    }
    if mean_speed is not None:
        given["mean_speed"] = positive(mean_speed, "mean_speed")
    if mean_wheels is not None:
        given["mean_wheels"] = positive(mean_wheels, "mean_wheels")
    if moisture_fraction is not None:
        given["moisture_fraction"] = _checked(moisture_fraction, "moisture_fraction", lo=0, hi=1)
    return dict(zip(given, broadcast_all(**given), strict=True))


def _bounds_si() -> dict[str, tuple[float, float, str]]:
    """The Table 13.2.2-3 ranges converted to the SI unit of each argument, with the row id."""
    st, mph = row("ap42_short_ton_in_kg"), _mph()
    out = {}
    for name, row_id, factor in (
        ("silt_fraction", "ap42_range_silt", 1 / PERCENT),
        ("mean_weight", "ap42_range_weight", st),
        ("mean_speed", "ap42_range_speed", mph),
        ("mean_wheels", "ap42_range_wheels", 1),
        ("moisture_fraction", "ap42_range_moisture", 1 / PERCENT),
    ):
        lo, hi = _range(row_id)
        out[name] = (lo * factor, hi * factor, row_id)
    return out


def ap42_unpaved_emission_factor(
    silt_fraction: Any,
    mean_weight: Any,
    size_class: str,
    mean_speed: Any = None,
    mean_wheels: Any = None,
    moisture_fraction: Any = None,
    strict: bool = False,
) -> Any:
    """AP-42 emission factor of unpaved industrial roads (equation 1a) in SI units.

    Parameters
    ----------
    silt_fraction : float or array [1]
        Silt content of the road surface as a mass fraction, in (0, 1].
    mean_weight : float or array [kg]
        Mean vehicle weight of the fleet (> 0).
    size_class : str [option]
        "PM2.5", "PM10" or "PM30".
    mean_speed : float or array [m/s], optional
        Mean vehicle speed; enters only the validity check.
    mean_wheels : float or array [count], optional
        Mean number of wheels; enters only the validity check.
    moisture_fraction : float or array [1], optional
        Surface moisture content as a mass fraction; enters only the validity check.
    strict : bool [flag]
        True to raise InputError instead of warning when an argument lies outside its Table 13.2.2-3 range.

    Returns
    -------
    float or array [kg/m]
        Emission factor per vehicle-metre travelled.

    Equation
    --------
    E = k (s/12)^a (W/3)^b in lb/VMT with s the silt content in percent and W the weight in short tons, converted with
    1 lb = 0.45359237 kg and 1 mile = 1609.344 m.

    Source
    ------
    epa2006ap42s1322 eq. 1a, p. 13.2.2-4 and Tables 13.2.2-2 and 13.2.2-3, p. 13.2.2-5.

    Validity
    --------
    Industrial unpaved roads only (not chemically stabilised); outside Table 13.2.2-3 the value is extrapolated with a
    ValidityWarning (an InputError when strict). AP-42 rates the factor lower with default silt values and with the
    precipitation correction.

    Knowledge rows
    --------------
    ap42_industrial_k_pm25, ap42_industrial_k_pm10, ap42_industrial_k_pm30, ap42_industrial_a_pm25,
    ap42_industrial_a_pm10, ap42_industrial_a_pm30, ap42_industrial_b_pm25, ap42_industrial_b_pm10,
    ap42_industrial_b_pm30, ap42_silt_reference, ap42_weight_reference, ap42_range_silt, ap42_range_weight,
    ap42_range_speed, ap42_range_wheels, ap42_range_moisture, ap42_lb_per_vmt_in_g_per_vkt, ap42_mile_in_m,
    ap42_short_ton_in_kg
    """
    suffix = SIZE_CLASSES[check_option(size_class, "size_class", tuple(SIZE_CLASSES))]
    if not isinstance(strict, bool | np.bool_):
        raise InputTypeError("argument 'strict' must be boolean", argument="strict")
    given = _inputs(silt_fraction, mean_weight, mean_speed, mean_wheels, moisture_fraction)
    bounds = _bounds_si()
    failed = [n for n, v in given.items() if ((v < bounds[n][0]) | (v > bounds[n][1])).any()]
    if failed and strict:
        raise InputError("outside the AP-42 Table 13.2.2-3 range: " + ", ".join(failed), argument=failed[0])
    for name in failed:
        lo, hi, row_id = bounds[name]
        v = given[name]
        warnings.warn(
            ValidityWarning(
                f"argument '{name}' lies outside the AP-42 Table 13.2.2-3 range [{lo!r}, {hi!r}] ({row_id}); "
                f"received {float(v.min())!r} to {float(v.max())!r}",
                argument=name,
                bounds=(lo, hi),
                row=row_id,
            ),
            stacklevel=2,
        )
    s = PERCENT * given["silt_fraction"]
    w = given["mean_weight"] / row("ap42_short_ton_in_kg")
    e_lb = (
        row(f"ap42_industrial_k_{suffix}")
        * (s / row("ap42_silt_reference")) ** row(f"ap42_industrial_a_{suffix}")
        * (w / row("ap42_weight_reference")) ** row(f"ap42_industrial_b_{suffix}")
    )
    e = e_lb * row("pound") / _mile()
    return finalize(e, *given.values())


def ap42_unpaved_validity(
    silt_fraction: Any, mean_weight: Any, mean_speed: Any = None, mean_wheels: Any = None, moisture_fraction: Any = None
) -> Any:
    """Flags for the AP-42 Table 13.2.2-3 validity ranges of unpaved industrial roads.

    Parameters
    ----------
    silt_fraction : float or array [1]
        Silt content as a mass fraction, in (0, 1].
    mean_weight : float or array [kg]
        Mean vehicle weight (> 0).
    mean_speed : float or array [m/s], optional
        Mean vehicle speed.
    mean_wheels : float or array [count], optional
        Mean number of wheels.
    moisture_fraction : float or array [1], optional
        Surface moisture content as a mass fraction.

    Returns
    -------
    named tuple of boolean arrays [mask]
        One field per argument given, named after it, plus `all`; true inside the range (bounds inclusive).

    Equation
    --------
    Silt 1.8 to 25.2 %, weight 2 to 290 short tons, speed 5 to 43 mph, 4 to 17 wheels, moisture 0.03 to 13 %.

    Source
    ------
    epa2006ap42s1322 Table 13.2.2-3, p. 13.2.2-5.

    Validity
    --------
    Ranges of the regression for industrial roads; vectorised use of the same test that the emission factor warns about.

    Knowledge rows
    --------------
    ap42_range_silt, ap42_range_weight, ap42_range_speed, ap42_range_wheels, ap42_range_moisture, ap42_mile_in_m,
    ap42_short_ton_in_kg
    """
    given = _inputs(silt_fraction, mean_weight, mean_speed, mean_wheels, moisture_fraction)
    bounds = _bounds_si()
    flags = {n: (v >= bounds[n][0]) & (v <= bounds[n][1]) for n, v in given.items()}
    every = np.logical_and.reduce(list(flags.values()))
    names = (*flags, "all")
    kind = _validity_types.setdefault(names, collections.namedtuple("Ap42Validity", names))
    values = [f[()] if f.ndim == 0 else f for f in flags.values()]
    return kind(*values, every[()] if every.ndim == 0 else every)


def fleet_mean_vehicle_weight(weights: Any, traffic_fractions: Any) -> Any:
    """Traffic-weighted mean vehicle weight of a fleet.

    Parameters
    ----------
    weights : array [kg]
        Weight of each vehicle class (> 0).
    traffic_fractions : array [fraction of traffic, any scale]
        Share of traffic of each class (>= 0, not all zero).

    Returns
    -------
    float [kg]
        The fleet-mean weight.

    Equation
    --------
    W = sum(w_i f_i) / sum(f_i).

    Source
    ------
    epa2006ap42s1322 p. 13.2.2-6 (fleet-mean example: 98 % of 2-ton and 2 % of 20-ton vehicles give 2.4 tons).

    Validity
    --------
    AP-42 requires the single fleet-mean weight rather than per-class factors.

    Knowledge rows
    --------------
    none
    """
    w = positive(weights, "weights")
    f = non_negative(traffic_fractions, "traffic_fractions")
    check_rank(w, "weights", 1)
    check_rank(f, "traffic_fractions", 1)
    if w.size != f.size:
        raise InputError(
            f"arguments weights and traffic_fractions differ in length: {w.size} and {f.size}",
            argument="traffic_fractions",
        )
    if w.size < 1 or not f.sum() > 0:
        raise InputError("argument 'traffic_fractions' must not be empty or all zero", argument="traffic_fractions")
    return np.float64(np.sum(w * f) / np.sum(f))


def precipitation_correction(emission_factor: Any, wet_days: Any) -> Any:
    """AP-42 annual correction of an emission factor for wet days.

    Parameters
    ----------
    emission_factor : float or array [any emission-factor unit]
        Uncorrected emission factor (>= 0); the result has the same unit.
    wet_days : float or array [d]
        Days a year with at least 0.254 mm of precipitation, in [0, 365].

    Returns
    -------
    float or array [same unit as emission_factor]
        Extrapolated annual average factor.

    Equation
    --------
    E_ext = E (365 - P) / 365.

    Source
    ------
    epa2006ap42s1322 eq. 2, p. 13.2.2-7.

    Validity
    --------
    AP-42 downgrades the quality rating by one letter when the correction is applied.

    Knowledge rows
    --------------
    ap42_wet_day_threshold, ap42_days_per_year
    """
    e = non_negative(emission_factor, "emission_factor")
    days = row("ap42_days_per_year")
    p = _checked(wet_days, "wet_days", lo=0, hi=days)
    e, p = broadcast_all(emission_factor=e, wet_days=p)
    return finalize(e * (days - p) / days, e, p)


def watering_control_efficiency(moisture_ratio: Any) -> Any:
    """Instantaneous control efficiency of road watering (Figure 13.2.2-2).

    Parameters
    ----------
    moisture_ratio : float or array [1]
        Ratio of the moisture of the watered surface to that of the uncontrolled surface, in [0, 5].

    Returns
    -------
    float or array [fraction]
        Control efficiency, by linear interpolation between the published vertices.

    Equation
    --------
    CE interpolates linearly through (M, CE) = (0, 0), (1, 0), (2, 0.75), (5, 0.95).

    Source
    ------
    epa2006ap42s1322 Figure 13.2.2-2, p. 13.2.2-12 (vertices read on the vector path of the figure).

    Validity
    --------
    Defined for 0 <= M <= 5 only; beyond 5 the source gives no value, so InputError is raised.

    Knowledge rows
    --------------
    ap42_watering_m_1, ap42_watering_m_2, ap42_watering_m_3, ap42_watering_m_4, ap42_watering_ce_1,
    ap42_watering_ce_2, ap42_watering_ce_3, ap42_watering_ce_4
    """
    ms = [row(f"ap42_watering_m_{i}") for i in range(1, 5)]
    ces = [row(f"ap42_watering_ce_{i}") / PERCENT for i in range(1, 5)]
    m = _checked(moisture_ratio, "moisture_ratio", lo=ms[0], hi=ms[-1])
    return finalize(np.interp(m, ms, ces), m)


def controlled_emission_factor(emission_factor: Any, control_efficiency: Any) -> Any:
    """Emission factor after a control measure.

    Parameters
    ----------
    emission_factor : float or array [any emission-factor unit]
        Uncontrolled emission factor (>= 0).
    control_efficiency : float or array [fraction]
        Control efficiency, in [0, 1].

    Returns
    -------
    float or array [same unit as emission_factor]
        Controlled emission factor.

    Equation
    --------
    E_c = E (1 - CE).

    Source
    ------
    epa2006ap42s1322 Table 13.2.2-5, p. 13.2.2-16 (7.1 lb/VMT at 0, 62, 68, 74 and 80 % control).

    Validity
    --------
    Linear in the emission factor.

    Knowledge rows
    --------------
    none
    """
    e = non_negative(emission_factor, "emission_factor")
    ce = unit_interval(control_efficiency, "control_efficiency")
    e, ce = broadcast_all(emission_factor=e, control_efficiency=ce)
    return finalize(e * (1 - ce), e, ce)


def line_emission_rate(emission_factor: Any, vehicles_per_second: Any) -> Any:
    """Emission per unit length of a road.

    Parameters
    ----------
    emission_factor : float or array [kg/m]
        Emission factor per vehicle-metre travelled (>= 0).
    vehicles_per_second : float or array [1/s]
        Traffic rate (>= 0).

    Returns
    -------
    float or array [kg/(m s)]
        Line emission rate.

    Equation
    --------
    q_l = E n.

    Source
    ------
    epa2006ap42s1322 eq. 1a, p. 13.2.2-4 (the factor is per vehicle distance travelled); product defined in spec 006
    FR-006-08.

    Validity
    --------
    Steady traffic.

    Knowledge rows
    --------------
    none
    """
    e = non_negative(emission_factor, "emission_factor")
    n = non_negative(vehicles_per_second, "vehicles_per_second")
    e, n = broadcast_all(emission_factor=e, vehicles_per_second=n)
    return finalize(e * n, e, n)
