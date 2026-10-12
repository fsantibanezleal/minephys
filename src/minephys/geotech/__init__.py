"""Geotechnical models (spec 003): generalised Hoek-Brown and equivalent Mohr-Coulomb, Bishop and Spencer limit
equilibrium on circular slices, Monte-Carlo probability of failure, Voight creep, the inverse-velocity and Bayesian
time-of-failure forecasts and the line-of-sight and phase model of a ground-based slope radar."""

from __future__ import annotations

from ._hoek_brown import (
    equivalent_mohr_coulomb,
    hoek_brown_parameters,
    hoek_brown_rock_mass_strength,
    hoek_brown_sigma1,
    hoek_brown_tensile_strength,
    hoek_brown_uniaxial_strength,
    sigma3_max,
)
from ._lem import bishop_simplified_fos, spencer_fos
from ._monitoring import (
    BayesianTTF,
    InverseVelocityResult,
    bayesian_ttf,
    inverse_velocity_ttf,
    voight_creep_series,
)
from ._probability import monte_carlo_fos, probability_of_failure, required_samples
from ._radar import los_from_phase, los_phase, max_unambiguous_los_step, slope_radar_los, wrap_phase
from ._slices import Slices, circular_slices

__all__ = [
    "BayesianTTF",
    "InverseVelocityResult",
    "Slices",
    "bayesian_ttf",
    "bishop_simplified_fos",
    "circular_slices",
    "equivalent_mohr_coulomb",
    "hoek_brown_parameters",
    "hoek_brown_rock_mass_strength",
    "hoek_brown_sigma1",
    "hoek_brown_tensile_strength",
    "hoek_brown_uniaxial_strength",
    "inverse_velocity_ttf",
    "los_from_phase",
    "los_phase",
    "max_unambiguous_los_step",
    "monte_carlo_fos",
    "probability_of_failure",
    "required_samples",
    "sigma3_max",
    "slope_radar_los",
    "spencer_fos",
    "voight_creep_series",
    "wrap_phase",
]
