"""Environment: AP-42 unpaved-road dust, Gaussian plume dispersion and Beer-Lambert dust attenuation for lidar (spec
006)."""

from ._ap42 import (
    ap42_unpaved_emission_factor,
    ap42_unpaved_validity,
    controlled_emission_factor,
    fleet_mean_vehicle_weight,
    line_emission_rate,
    precipitation_correction,
    watering_control_efficiency,
)
from ._dispersion import finite_line_source_plume, gaussian_plume, line_source_plume, pasquill_sigmas
from ._optics import (
    LidarDustReturn,
    beer_lambert_transmittance,
    extinction_coefficient,
    lidar_dust_return,
    mass_extinction_coefficient,
    path_transmittance,
)

__all__ = [
    "LidarDustReturn",
    "ap42_unpaved_emission_factor",
    "ap42_unpaved_validity",
    "beer_lambert_transmittance",
    "controlled_emission_factor",
    "extinction_coefficient",
    "finite_line_source_plume",
    "fleet_mean_vehicle_weight",
    "gaussian_plume",
    "lidar_dust_return",
    "line_emission_rate",
    "line_source_plume",
    "mass_extinction_coefficient",
    "pasquill_sigmas",
    "path_transmittance",
    "precipitation_correction",
    "watering_control_efficiency",
]
