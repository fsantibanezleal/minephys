# Haulage constants and parameters

Table `haulage`, licence CC-BY-4.0.

Items: 14
UNVERIFIED: 13

### `diesel_co2_kg_per_us_gal`

- Quantity: diesel fuel combustion CO₂ emission factor
- Value: 10.21
- Units: kg CO₂ / US gal
- Role: parameter
- Citation: `epa2025ghghub`, https://www.epa.gov/system/files/documents/2025-01/ghg-emission-factors-hub-2025.pdf
- Page: Table 2, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.haulage.co2_from_diesel`
- Notes: combustion (tank-to-wheel) CO₂ only; the CH₄ and N₂O factors are in Table 5 (p. 3) of the same document

### `rolling_resistance_firm_maintained`

- Quantity: rolling resistance of a firm, maintained surface with slight flexing
- Value: 0.03
- Units: 1
- Role: parameter
- Citation: `oem2016rollingresistance`, https://www.cat.com/en_US/articles/ci-articles/rolling-resistance-factors.html
- Page: rolling-resistance table
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`
- Notes: typical input only, never a default; the source was unreachable at specification (2026-10-02)

### `rolling_resistance_hard_smooth`

- Quantity: rolling resistance of a hard, smooth surface with no tyre penetration
- Value: 0.015
- Units: 1
- Role: parameter
- Citation: `oem2016rollingresistance`, https://www.cat.com/en_US/articles/ci-articles/rolling-resistance-factors.html
- Page: rolling-resistance table
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`
- Notes: typical input only, never a default; the source was unreachable at specification (2026-10-02)

### `rolling_resistance_loose_gravel`

- Quantity: rolling resistance of loose gravel with 150 mm or more tyre penetration
- Value: 0.1
- Units: 1
- Role: parameter
- Citation: `oem2016rollingresistance`, https://www.cat.com/en_US/articles/ci-articles/rolling-resistance-factors.html
- Page: rolling-resistance table
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`
- Notes: typical input only, never a default; the source was unreachable at specification (2026-10-02)

### `rolling_resistance_per_cm_penetration`

- Quantity: added rolling resistance per centimetre of tyre penetration (about 6 kg per tonne)
- Value: 0.006
- Units: 1 per cm
- Role: parameter
- Citation: `oem2016rollingresistance`, https://www.cat.com/en_US/articles/ci-articles/rolling-resistance-factors.html
- Page: rolling-resistance table
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`
- Notes: typical input only, never a default; the source was unreachable at specification (2026-10-02)

### `rolling_resistance_rutted_soft`

- Quantity: rolling resistance of rutted soft dirt with about 100 mm tyre penetration
- Value: 0.08
- Units: 1
- Role: parameter
- Citation: `oem2016rollingresistance`, https://www.cat.com/en_US/articles/ci-articles/rolling-resistance-factors.html
- Page: rolling-resistance table
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`
- Notes: typical input only, never a default; the source was unreachable at specification (2026-10-02)

### `tripwire_bank_density_min`

- Quantity: unit tripwire: smallest plausible bank density
- Value: 500.0
- Units: kg/m³
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.loose_density`
- Notes: design choice of the specification, not a measurement

### `tripwire_fuel_energy_density_min`

- Quantity: unit tripwire: smallest plausible fuel volumetric energy content
- Value: 1000000000.0
- Units: J/m³
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.fuel_use`
- Notes: design choice of the specification, not a measurement

### `tripwire_grade_abs_max`

- Quantity: unit tripwire: largest plausible absolute grade as a fraction
- Value: 0.3
- Units: 1
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.grade_resistance`, `minephys.haulage.total_resistance`, `minephys.haulage.retarder_limited_speed`, `minephys.haulage.segment_energy`, `minephys.haulage.cycle_energy`, `minephys.haulage.bev_cycle_energy`, `minephys.haulage.trolley_cycle_energy`
- Notes: design choice of the specification, not a measurement

### `tripwire_grid_intensity_max`

- Quantity: unit tripwire: largest plausible grid emission intensity
- Value: 1e-06
- Units: kg/J
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.co2_from_electricity`
- Notes: design choice of the specification, not a measurement

### `tripwire_rolling_resistance_max`

- Quantity: unit tripwire: largest plausible rolling resistance as a fraction
- Value: 0.2
- Units: 1
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.total_resistance`, `minephys.haulage.retarder_limited_speed`, `minephys.haulage.segment_energy`, `minephys.haulage.cycle_energy`, `minephys.haulage.bev_cycle_energy`, `minephys.haulage.trolley_cycle_energy`
- Notes: design choice of the specification, not a measurement

### `tripwire_swell_max`

- Quantity: unit tripwire: largest plausible swell factor as a fraction
- Value: 1.0
- Units: 1
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.loose_density`
- Notes: design choice of the specification, not a measurement

### `tripwire_truck_mass_max`

- Quantity: unit tripwire: largest plausible gross truck mass
- Value: 2000000.0
- Units: kg
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.required_force`, `minephys.haulage.rimpull_limited_speed`, `minephys.haulage.retarder_limited_speed`, `minephys.haulage.segment_energy`, `minephys.haulage.cycle_energy`, `minephys.haulage.bev_cycle_energy`, `minephys.haulage.trolley_cycle_energy`
- Notes: design choice of the specification, not a measurement

### `tripwire_truck_mass_min`

- Quantity: unit tripwire: smallest plausible gross truck mass
- Value: 1000.0
- Units: kg
- Role: limit
- Citation: `minephys:spec-001-haulage`, https://github.com/fsantibanezleal/minephys/blob/main/specs/001-haulage/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.haulage.required_force`, `minephys.haulage.rimpull_limited_speed`, `minephys.haulage.retarder_limited_speed`, `minephys.haulage.segment_energy`, `minephys.haulage.cycle_energy`, `minephys.haulage.bev_cycle_energy`, `minephys.haulage.trolley_cycle_energy`
- Notes: design choice of the specification, not a measurement
