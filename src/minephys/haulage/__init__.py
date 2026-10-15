"""Haul-truck physics and fleet queueing (spec 001): resistances, rimpull and retarder speeds, loading passes, cycle
time, segment and cycle energy, fuel and CO2, trolley-assist and battery-electric energy, match factor, M/M/c,
finite-source queue and exact mean-value analysis. All functions take and return SI units."""

from __future__ import annotations

from ._cycle import (
    co2_from_diesel,
    co2_from_electricity,
    cycle_time,
    fuel_use,
    loading_passes,
    loose_density,
    match_factor,
    segment_travel_time,
)
from ._energy import bev_cycle_energy, cycle_energy, segment_energy, trolley_cycle_energy
from ._fleet import (
    FiniteSourceResult,
    MMCResult,
    MVAResult,
    finite_source_queue,
    mean_value_analysis,
    mmc_queue,
)
from ._road import (
    grade_resistance,
    required_force,
    retarder_limited_speed,
    rimpull_limited_speed,
    total_resistance,
)

__all__ = [
    "FiniteSourceResult",
    "MMCResult",
    "MVAResult",
    "bev_cycle_energy",
    "co2_from_diesel",
    "co2_from_electricity",
    "cycle_energy",
    "cycle_time",
    "finite_source_queue",
    "fuel_use",
    "grade_resistance",
    "loading_passes",
    "loose_density",
    "match_factor",
    "mean_value_analysis",
    "mmc_queue",
    "required_force",
    "retarder_limited_speed",
    "rimpull_limited_speed",
    "segment_energy",
    "segment_travel_time",
    "total_resistance",
    "trolley_cycle_energy",
]
