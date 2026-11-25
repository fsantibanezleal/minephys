# Haulage constants and parameters

Table `haulage`, licence CC-BY-4.0.

Items: 19
UNVERIFIED: 13

### `battery_electric_battery_to_wheel_efficiency`

- Quantity: efficiency of a battery-electric haul truck from battery terminals to the wheel when discharging
- Value: 0.85845
- Units: 1
- Role: parameter
- Citation: `lindgren2022`, DOI 10.3390/en15134871
- Page: Table 2, p. 7
- Verification: verified (2026-11-25)
- Symbol: `minephys.haulage.bev_cycle_energy`
- Notes: Derived: (1 - 0.115) times (1 - 0.03), the DC-bus-to-wheel loss and the "Resistive loss in battery and DC/DC converter at 1C charge/discharge rate" 3 % (Table 2), the battery loss applied once. Uncertainty: the authors call the battery and power-electronics losses "highly uncertain since it is a new system that is yet to be developed" (p. 13); the 3 % holds at a 1C rate and no interval is given.

### `battery_electric_regeneration_efficiency`

- Quantity: electrical efficiency of regenerative braking from the wheel to the battery terminals
- Value: 0.85845
- Units: 1
- Role: parameter
- Citation: `lindgren2022`, DOI 10.3390/en15134871
- Page: Table 2, p. 7
- Verification: verified (2026-11-25)
- Symbol: `minephys.haulage.bev_cycle_energy`
- Notes: Derived: the DC-bus-to-wheel loss is "the same in reverse at regeneration" (Table 2), so (1 - 0.115) times (1 - 0.03). Boundary: electrical conversion only. It is an upper bound on the recovered share of braking energy, because friction braking and the practical electric braking power of 3300 kW (Table 2, note b) are not modelled. Uncertainty: no interval is given; the battery part is "highly uncertain" (p. 13).

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

### `diesel_electric_fuel_to_wheel_efficiency`

- Quantity: marginal efficiency of a diesel-electric haul truck from fuel energy to wheel energy (engine, generator, rectifier, DC bus, motor, gear)
- Value: 0.354
- Units: 1
- Role: parameter
- Citation: `lindgren2022`, DOI 10.3390/en15134871
- Page: Table 2, p. 7
- Verification: verified (2026-11-25)
- Symbol: `minephys.haulage.trolley_cycle_energy`
- Notes: Derived: 0.40 (Table 2, "ca 40% efficiency, fuel to DC-power", marginal diesel consumption 0.253 l/kWh) times 0.885 (the DC-bus-to-wheel row). Uncertainty: the source gives "ca 40%" with no interval; the authors inferred their parameters from truck specifications and recorded fuel consumption (p. 4) and their modelled DC-bus energy matched the measured 361 kWh per cycle within 1 % (358 kWh, p. 5), which checks the DC-bus energy, not this efficiency. The value is marginal: the load-independent consumption of 50 l/h in Table 2 is excluded, so a cycle-average efficiency from the tank is lower.

### `diesel_lower_heating_value_j_per_m3`

- Quantity: lower heating value of low-sulfur diesel fuel per unit volume
- Value: 35811696091.9353
- Units: J/m³
- Role: parameter
- Citation: `afdc2026fuelproperties`, https://afdc.energy.gov/fuels/properties
- Page: Fuel Properties Comparison, row Low Sulfur Diesel, lower heating value (128,488 Btu/gal)
- Verification: verified (2026-11-25)
- Symbol: `minephys.haulage.fuel_use`
- Notes: Converted: 128,488 Btu/gal times 1055.05585262 J/Btu (International Table Btu) divided by 3.785411784e-3 m3/gal, which is 35.81 MJ/l; the page does not say which Btu it uses (the thermochemical Btu would change the value by 0.03 %). The page cites the GREET 2019 input fuel specifications of Argonne National Laboratory for it. Uncertainty: the page gives one value and no interval; heating value varies with fuel grade. Cross-check: Table 2 of lindgren2022 (0.253 l/kWh at ca 40 %) implies 35.57 MJ/l, 0.7 % lower. The higher heating value on the same page is 138,490 Btu/gal and is not this row.

### `electric_dc_bus_to_wheel_efficiency`

- Quantity: efficiency of the electric drive from the DC bus to the wheel (motors, power electronics, gears), forward
- Value: 0.885
- Units: 1
- Role: parameter
- Citation: `lindgren2022`, DOI 10.3390/en15134871
- Page: Table 2, p. 7
- Verification: verified (2026-11-25)
- Symbol: `minephys.haulage.trolley_cycle_energy`
- Notes: Derived: 1 - 0.115 from "Loss from DC-bus to wheel, same in reverse at regeneration" 11.5 % (Table 2). Boundary: it starts at the DC bus; pantograph, contact-line, rectifier and feeder losses are not in it (the authors estimate the mine distribution loss at 2.63 %, p. 14, for one truck on a 500 m line). Uncertainty: the source gives no interval; the loss is a model parameter inferred by the authors from truck specifications (p. 4) and was not measured on its own.

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
