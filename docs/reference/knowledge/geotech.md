# Geotechnical constants, limits and parameters

Table `geotech`, licence CC-BY-4.0.

Items: 20
UNVERIFIED: 7

### `gbsar_ku_band_wavelength`

- Quantity: wavelength of a Ku-band ground-based radar
- Value: 0.0175
- Units: m
- Role: parameter
- Citation: `wolff2023`, https://scholar.google.com/
- Page: p. 8
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.los_phase`, `minephys.geotech.los_from_phase`, `minephys.geotech.max_unambiguous_los_step`
- Notes: Ku-band with a wavelength equal to 1.75 cm; documented value, never a default

### `hb_a_gsi_scale`

- Quantity: GSI scale of the exponent a
- Value: 15
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 5, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`
- Notes: a = 1/2 + (exp(-GSI/15) - exp(-20/3)) / 6; identical in Hoek and Brown 2019, eqs. 4-6, in-press p. 2

### `hb_a_offset_exponent`

- Quantity: offset exponent of the exponent a (exact rational)
- Value: 20/3
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 5, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`

### `hb_disturbance_open_pit_mechanical_excavation`

- Quantity: disturbance factor of an open-pit slope excavated mechanically
- Value: 0.7
- Units: 1
- Role: parameter
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: Table 1, p. 272
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`
- Notes: documented value, never a default (disturbance is a required argument)

### `hb_disturbance_open_pit_production_blasting`

- Quantity: disturbance factor of an open-pit slope with production blasting
- Value: 1.0
- Units: 1
- Role: parameter
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: Table 1, p. 272
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`
- Notes: documented value, never a default (disturbance is a required argument); Hoek and Brown 2019, Table 2 (in-press p. 9)

### `hb_mb_disturbance_coefficient`

- Quantity: coefficient of D in the GSI denominator of m_b
- Value: 14
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 3, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`

### `hb_mb_gsi_denominator_constant`

- Quantity: constant of the GSI denominator of m_b
- Value: 28
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 3, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`
- Notes: mb = mi exp((GSI - 100) / (28 - 14 D))

### `hb_s_disturbance_coefficient`

- Quantity: coefficient of D in the GSI denominator of s
- Value: 3
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 4, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`

### `hb_s_gsi_denominator_constant`

- Quantity: constant of the GSI denominator of s
- Value: 9
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 4, pp. 267-268
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.hoek_brown_parameters`
- Notes: s = exp((GSI - 100) / (9 - 3 D))

### `hb_sigma3max_slope_coefficient`

- Quantity: coefficient of sigma3max for slopes
- Value: 0.72
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 19, p. 270
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.sigma3_max`

### `hb_sigma3max_slope_exponent`

- Quantity: exponent of sigma_cm / (gamma H) in sigma3max for slopes
- Value: -0.91
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 19, p. 270
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.sigma3_max`

### `hb_sigma3max_tunnel_coefficient`

- Quantity: coefficient of sigma3max for tunnels
- Value: 0.47
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 18, p. 270
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.sigma3_max`

### `hb_sigma3max_tunnel_exponent`

- Quantity: exponent of sigma_cm / (gamma H) in sigma3max for tunnels
- Value: -0.94
- Units: 1
- Role: model_constant
- Citation: `hoek2002`, https://www.semanticscholar.org/paper/HOEK-BROWN-FAILURE-CRITERION-2002-EDITION-Hoek-Carranza-Torres/e44829e6d2c1484d25efe6be2db830e16c8f9d89
- Page: eq. 18, p. 270
- Verification: verified (2026-10-06)
- Symbol: `minephys.geotech.sigma3_max`

### `tripwire_cohesion_min`

- Quantity: unit tripwire: smallest plausible nonzero cohesion
- Value: 100.0
- Units: Pa
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.bishop_simplified_fos`, `minephys.geotech.spencer_fos`, `minephys.geotech.monte_carlo_fos`
- Notes: design choice of the specification, not a measurement

### `tripwire_friction_angle_max`

- Quantity: unit tripwire: largest plausible friction angle
- Value: 1.2
- Units: rad
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.bishop_simplified_fos`, `minephys.geotech.spencer_fos`, `minephys.geotech.monte_carlo_fos`
- Notes: design choice of the specification, not a measurement

### `tripwire_sigma_ci_max`

- Quantity: unit tripwire: largest plausible intact-rock strength
- Value: 1000000000.0
- Units: Pa
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.hoek_brown_sigma1`, `minephys.geotech.hoek_brown_uniaxial_strength`, `minephys.geotech.hoek_brown_tensile_strength`, `minephys.geotech.hoek_brown_rock_mass_strength`, `minephys.geotech.equivalent_mohr_coulomb`
- Notes: design choice of the specification, not a measurement

### `tripwire_sigma_ci_min`

- Quantity: unit tripwire: smallest plausible intact-rock strength
- Value: 100000.0
- Units: Pa
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.hoek_brown_sigma1`, `minephys.geotech.hoek_brown_uniaxial_strength`, `minephys.geotech.hoek_brown_tensile_strength`, `minephys.geotech.hoek_brown_rock_mass_strength`, `minephys.geotech.equivalent_mohr_coulomb`
- Notes: design choice of the specification, not a measurement

### `tripwire_slope_velocity_max`

- Quantity: unit tripwire: largest plausible slope velocity
- Value: 0.01
- Units: m/s
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.inverse_velocity_ttf`, `minephys.geotech.bayesian_ttf`
- Notes: design choice of the specification, not a measurement

### `tripwire_unit_weight_min`

- Quantity: unit tripwire: smallest plausible unit weight
- Value: 1000.0
- Units: N/m³
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.sigma3_max`, `minephys.geotech.circular_slices`
- Notes: design choice of the specification, not a measurement

### `tripwire_wavelength_range`

- Quantity: unit tripwire: plausible radar wavelength range
- Range: 0.0001 to 1.0
- Units: m
- Role: limit
- Citation: `minephys:spec-003-geotech`, https://github.com/fsantibanezleal/minephys/blob/main/specs/003-geotech/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.geotech.los_phase`, `minephys.geotech.los_from_phase`, `minephys.geotech.max_unambiguous_los_step`
- Notes: design choice of the specification, not a measurement
