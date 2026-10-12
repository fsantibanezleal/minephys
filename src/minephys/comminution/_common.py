"""Unit helpers of `minephys.comminution` (spec 005 conventions); the argument checks live in `minephys._argcheck`."""

from __future__ import annotations

from .._argcheck import (
    FloatArray,
    count,
    finer_than,
    flag,
    non_negative,
    positive,
    row,
    scalar,
    unit_interval,
    vector,
)

UM_PER_M = 10**6
G_PER_KG = 1000
KG_PER_T = 1000

__all__ = [
    "G_PER_KG",
    "KG_PER_T",
    "UM_PER_M",
    "FloatArray",
    "count",
    "finer_than",
    "flag",
    "kwh_per_t_in_si",
    "non_negative",
    "positive",
    "row",
    "scalar",
    "unit_interval",
    "vector",
]


def kwh_per_t_in_si() -> float:
    """J/kg in one kWh/t, from the exact definition of the kilowatt hour (knowledge row `kilowatt_hour`)."""
    return row("kilowatt_hour") / KG_PER_T
