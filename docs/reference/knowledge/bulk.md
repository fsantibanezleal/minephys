# Bulk-handling constants, limits and parameters

Table `bulk`, licence CC-BY-4.0.

Items: 15
UNVERIFIED: 14

### `beverloo_annulus_coefficient_range`

- Quantity: range of the annulus coefficient k
- Range: 1.0 to 2.0
- Units: 1
- Role: parameter
- Citation: `mankoc2007beverloo`, DOI 10.1007/s10035-007-0062-2, https://arxiv.org/abs/0707.4550
- Page: p. 1; darias2020 p. 1 reports 1.4 to 3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: secondary sources only; documented, never a default

### `beverloo_discharge_coefficient_dem`

- Quantity: discharge coefficient C fitted to a DEM study with the particle density
- Value: 0.56
- Units: 1
- Role: parameter
- Citation: `dasilva2025`, https://arxiv.org/abs/2512.03698
- Page: p. 9
- Verification: verified (2026-10-06)
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: fitted with the particle density of 3000 kg/m3, exponent 2.5 and g = 9.8 m/s2; not interchangeable with the bulk-density C; documented, never a default

### `beverloo_discharge_coefficient_range`

- Quantity: range of the discharge coefficient C (bulk-density form)
- Range: 0.55 to 0.65
- Units: 1
- Role: parameter
- Citation: `mankoc2007beverloo`, DOI 10.1007/s10035-007-0062-2, https://arxiv.org/abs/0707.4550
- Page: p. 1 (Beverloo et al. 1961 as quoted)
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: secondary source only; documented, never a default

### `beverloo_exponent`

- Quantity: exponent of the free opening in Beverloo's discharge law
- Value: 5/2
- Units: 1
- Role: model_constant
- Citation: `beverloo1961flow`, DOI 10.1016/0009-2509(61)85030-6
- Page: read in mankoc2007beverloo, eq. 1, p. 1 (secondary)
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: primary source paywalled and not read; the exponent also follows from dimensional analysis, which is the test oracle

### `cema_ky_typical_range`

- Quantity: typical range of the factor Ky
- Range: 0.016 to 0.035
- Units: 1
- Role: parameter
- Citation: `pdhonline_m344`, https://pdhonline.com/
- Page: p. 13 (normal selection 0.022)
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.cema_effective_tension`
- Notes: secondary source only; documented, never a default

### `cema_return_belt_coefficient`

- Quantity: return-belt coefficient of the CEMA effective tension
- Value: 0.015
- Units: 1
- Role: model_constant
- Citation: `cema_belt_conveyors_7th`, https://www.cemanet.org/
- Page: effective tension equation; printed in pdhonline_m344, p. 13
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.cema_effective_tension`
- Notes: secondary source only; the standard is paywalled and its errata page was unreachable

### `gy_fse_granulometric_factor_wide`

- Quantity: granulometric factor g of Gy's formula for wide size distributions
- Value: 0.25
- Units: 1
- Role: parameter
- Citation: `minkkinen2008`, https://www.eurachem.org/
- Page: p. 7
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.gy_fundamental_sampling_error`
- Notes: Gy's own text not read; documented, never a default

### `gy_fse_shape_factor_default`

- Quantity: shape factor f of Gy's formula
- Value: 0.5
- Units: 1
- Role: parameter
- Citation: `minkkinen2008`, https://www.eurachem.org/
- Page: p. 6
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.gy_fundamental_sampling_error`
- Notes: Gy's own text not read; documented, never a default

### `tripwire_belt_speed_max`

- Quantity: unit tripwire: largest plausible belt speed (ft/min or km/h passed as m/s)
- Value: 15.0
- Units: m/s
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.conveyor_capacity`, `minephys.bulk.conveyor_power`
- Notes: design choice of the specification, not a measurement

### `tripwire_bulk_density_min`

- Quantity: unit tripwire: smallest plausible bulk density (t/m3 passed as kg/m3)
- Value: 100.0
- Units: kg/m³
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`, `minephys.bulk.conveyor_capacity`
- Notes: design choice of the specification, not a measurement

### `tripwire_mineralogical_factor_min`

- Quantity: unit tripwire: smallest plausible mineralogical factor (g/cm3 passed as kg/m3)
- Value: 100.0
- Units: kg/m³
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.gy_fundamental_sampling_error`
- Notes: design choice of the specification, not a measurement

### `tripwire_orifice_diameter_max`

- Quantity: unit tripwire: largest plausible orifice diameter (mm passed as m)
- Value: 10.0
- Units: m
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: design choice of the specification, not a measurement

### `tripwire_particle_diameter_max`

- Quantity: unit tripwire: largest plausible particle diameter (mm passed as m)
- Value: 1.0
- Units: m
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.beverloo_discharge`
- Notes: design choice of the specification, not a measurement

### `tripwire_repose_angle_max`

- Quantity: unit tripwire: largest plausible angle of repose
- Value: 1.05
- Units: rad
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.repose_cone_height`, `minephys.bulk.repose_cone_volume`, `minephys.bulk.repose_ridge_volume`
- Notes: design choice of the specification, not a measurement

### `tripwire_top_size_max`

- Quantity: unit tripwire: largest plausible top size (cm passed as m)
- Value: 0.5
- Units: m
- Role: limit
- Citation: `minephys:spec-004-bulk`, https://github.com/fsantibanezleal/minephys/blob/main/specs/004-bulk/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.bulk.gy_fundamental_sampling_error`
- Notes: design choice of the specification, not a measurement
