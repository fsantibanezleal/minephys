"""Bulk-handling models (spec 004): Beverloo discharge, repose-angle stockpile geometry, belt-conveyor capacity,
effective tension and power, Gy's fundamental sampling error and bed-blending variance."""

from __future__ import annotations

from ._flow import (
    beverloo_discharge,
    cema_effective_tension,
    conveyor_capacity,
    conveyor_power,
    repose_cone_height,
    repose_cone_volume,
    repose_ridge_volume,
)
from ._sampling import gy_blending_variance, gy_fundamental_sampling_error, variance_reduction_ratio

__all__ = [
    "beverloo_discharge",
    "cema_effective_tension",
    "conveyor_capacity",
    "conveyor_power",
    "gy_blending_variance",
    "gy_fundamental_sampling_error",
    "repose_cone_height",
    "repose_cone_volume",
    "repose_ridge_volume",
    "variance_reduction_ratio",
]
