"""Unit-conversion helpers between SI and the unit-suffixed forms of the closed list in spec 000 section 8 (A2).

Every helper is elementwise (spec 000 FR-000-07) and converts exactly by definition. The factors are the `conversion`
rows of the `units` knowledge table (NIST SP 811 Appendix B.8 and NIST Handbook 44 (2026) Appendix C); the table is
read on the first call of a helper that needs it, never at import. The US gallon is 231 in^3 with 1 in = 0.0254 m,
derived exactly here (3.785411784e-3 m^3).
"""

from __future__ import annotations

import functools
import math
from typing import Any

from . import knowledge
from ._validate import as_float_array, check_finite, finalize

__all__ = [
    "deg_to_rad",
    "fraction_to_pct",
    "ft_to_m",
    "in_per_s_to_m_per_s",
    "j_to_kwh",
    "kg_to_lb",
    "kwh_to_j",
    "lb_to_kg",
    "m3_to_us_gal",
    "m_per_s_to_in_per_s",
    "m_to_ft",
    "pct_to_fraction",
    "rad_to_deg",
    "us_gal_to_m3",
]

_DEGREES_PER_HALF_TURN = 180
_PERCENT = 100


@functools.cache
def _factor(unit: str) -> float:
    """SI value of one `unit`: a `conversion` row of the `units` table, or the exact derived degree and US gallon."""
    if unit == "degree":
        return math.pi / _DEGREES_PER_HALF_TURN
    if unit == "us_gallon":
        inch = float(knowledge.get_value("inch"))  # type: ignore[arg-type]
        return float(knowledge.get_value("us_gallon_cubic_inches")) * inch**3  # type: ignore[arg-type]
    return float(knowledge.get_value(unit))  # type: ignore[arg-type]


def _scale(x: Any, argument: str, factor: str, *, divide: bool) -> Any:
    arr = check_finite(as_float_array(x, argument), argument)
    k = _factor(factor)
    return finalize(arr / k if divide else arr * k, arr)


def deg_to_rad(x: Any) -> Any:
    """Convert an angle from degrees to radians.

    Parameters
    ----------
    x : float or array_like [deg]
        Angle.

    Returns
    -------
    float or ndarray [rad]
        The angle in radians.
    """
    return _scale(x, "x", "degree", divide=False)


def rad_to_deg(x: Any) -> Any:
    """Convert an angle from radians to degrees.

    Parameters
    ----------
    x : float or array_like [rad]
        Angle.

    Returns
    -------
    float or ndarray [deg]
        The angle in degrees.
    """
    return _scale(x, "x", "degree", divide=True)


def pct_to_fraction(x: Any) -> Any:
    """Convert a percentage to a fraction.

    Parameters
    ----------
    x : float or array_like [%]
        Percentage.

    Returns
    -------
    float or ndarray [1]
        The fraction (25 % is 0.25).
    """
    arr = check_finite(as_float_array(x, "x"), "x")
    return finalize(arr / _PERCENT, arr)


def fraction_to_pct(x: Any) -> Any:
    """Convert a fraction to a percentage.

    Parameters
    ----------
    x : float or array_like [1]
        Fraction.

    Returns
    -------
    float or ndarray [%]
        The percentage (0.05 is 5 %).
    """
    arr = check_finite(as_float_array(x, "x"), "x")
    return finalize(arr * _PERCENT, arr)


def in_per_s_to_m_per_s(x: Any) -> Any:
    """Convert a speed from inches per second to metres per second (1 in = 0.0254 m, exact).

    Parameters
    ----------
    x : float or array_like [in/s]
        Speed.

    Returns
    -------
    float or ndarray [m/s]
        The speed in SI units.
    """
    return _scale(x, "x", "inch", divide=False)


def m_per_s_to_in_per_s(x: Any) -> Any:
    """Convert a speed from metres per second to inches per second.

    Parameters
    ----------
    x : float or array_like [m/s]
        Speed.

    Returns
    -------
    float or ndarray [in/s]
        The speed in inches per second.
    """
    return _scale(x, "x", "inch", divide=True)


def ft_to_m(x: Any) -> Any:
    """Convert a length from feet to metres (1 ft = 0.3048 m, exact).

    Parameters
    ----------
    x : float or array_like [ft]
        Length.

    Returns
    -------
    float or ndarray [m]
        The length in metres.
    """
    return _scale(x, "x", "foot", divide=False)


def m_to_ft(x: Any) -> Any:
    """Convert a length from metres to feet.

    Parameters
    ----------
    x : float or array_like [m]
        Length.

    Returns
    -------
    float or ndarray [ft]
        The length in feet.
    """
    return _scale(x, "x", "foot", divide=True)


def lb_to_kg(x: Any) -> Any:
    """Convert a mass from avoirdupois pounds to kilograms (1 lb = 0.45359237 kg, exact).

    Parameters
    ----------
    x : float or array_like [lb]
        Mass.

    Returns
    -------
    float or ndarray [kg]
        The mass in kilograms.
    """
    return _scale(x, "x", "pound", divide=False)


def kg_to_lb(x: Any) -> Any:
    """Convert a mass from kilograms to avoirdupois pounds.

    Parameters
    ----------
    x : float or array_like [kg]
        Mass.

    Returns
    -------
    float or ndarray [lb]
        The mass in pounds.
    """
    return _scale(x, "x", "pound", divide=True)


def us_gal_to_m3(x: Any) -> Any:
    """Convert a volume from US gallons to cubic metres (1 US gal = 231 in^3, exact).

    Parameters
    ----------
    x : float or array_like [US gal]
        Volume.

    Returns
    -------
    float or ndarray [m^3]
        The volume in cubic metres.
    """
    return _scale(x, "x", "us_gallon", divide=False)


def m3_to_us_gal(x: Any) -> Any:
    """Convert a volume from cubic metres to US gallons.

    Parameters
    ----------
    x : float or array_like [m^3]
        Volume.

    Returns
    -------
    float or ndarray [US gal]
        The volume in US gallons.
    """
    return _scale(x, "x", "us_gallon", divide=True)


def kwh_to_j(x: Any) -> Any:
    """Convert an energy from kilowatt-hours to joules (1 kWh = 3.6e6 J, exact).

    Parameters
    ----------
    x : float or array_like [kWh]
        Energy.

    Returns
    -------
    float or ndarray [J]
        The energy in joules.
    """
    return _scale(x, "x", "kilowatt_hour", divide=False)


def j_to_kwh(x: Any) -> Any:
    """Convert an energy from joules to kilowatt-hours.

    Parameters
    ----------
    x : float or array_like [J]
        Energy.

    Returns
    -------
    float or ndarray [kWh]
        The energy in kilowatt-hours.
    """
    return _scale(x, "x", "kilowatt_hour", divide=True)

