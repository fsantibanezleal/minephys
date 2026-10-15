# Comminution constants and limits (Bond, Morrell, Austin)

Table `comminution`, licence CC-BY-4.0.

Items: 22
UNVERIFIED: 1

### `austin_reference_size`

- Quantity: reference size x0 of the Austin selection function (default of its x0 argument)
- Value: 0.001
- Units: m
- Role: model_constant
- Citation: `austin1984ballmilling`, https://search.worldcat.org/search?q=Process+Engineering+of+Size+Reduction+Ball+Milling
- Page: not read (bibliographic, 1984 edition)
- Verification: UNVERIFIED
- Symbol: `minephys.comminution.austin_selection`
- Notes: 1 mm; the attribution of the selection-function form to Austin is UNVERIFIED, so the row warns when it is read

### `bond_bm_constant`

- Quantity: constant of the Bond ball-mill work index test equation
- Value: 44.5
- Units: kWh/short ton
- Role: model_constant
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 10, Annex C1 "Calculations"
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_ball_mill_work_index`

### `bond_bm_exponent_grindability`

- Quantity: exponent of the grindability (net grams per revolution) in the Bond ball-mill work index test equation
- Value: 0.82
- Units: 1
- Role: model_constant
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 10, Annex C1 "Calculations"
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_ball_mill_work_index`

### `bond_bm_exponent_screen`

- Quantity: exponent of the closing screen size in the Bond ball-mill work index test equation
- Value: 0.23
- Units: 1
- Role: model_constant
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 10, Annex C1 "Calculations"
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_ball_mill_work_index`

### `bond_law_coefficient`

- Quantity: coefficient of Bond's third law of comminution (sizes in micrometres)
- Value: 10
- Units: 1 (with sizes in µm)
- Role: model_constant
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 1, "Calculations"; worked examples p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_energy`, `minephys.comminution.bond_operating_work_index`, `minephys.comminution.bond_ball_mill_work_index`
- Notes: W = 10 Wi (1/sqrt(P80) - 1/sqrt(F80)) with P80 and F80 in micrometres; the law is homogeneous in the work index

### `bond_min_product_size`

- Quantity: smallest product size to which Bond's law applies (approximate lower validity bound)
- Value: 70
- Units: µm
- Role: limit
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 1 ("applies down to approximately 70 µm")
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_energy`, `minephys.comminution.bond_operating_work_index`
- Notes: a product P80 below this size emits a ValidityWarning and the result is still returned

### `bond_short_ton_to_metric`

- Quantity: published factor from kWh per short ton to kWh per metric tonne
- Value: 1.1025
- Units: (kWh/t)/(kWh/short ton)
- Role: conversion
- Citation: `mcivor2016bondgmsg`, http://www.ceecthefuture.org/wp-content/uploads/2015/12/Bond-GMSG-SME-conference.pdf
- Page: p. 10, Annex C1 ("Multiply by 1.1025 for kWh/mt")
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.bond_ball_mill_work_index`
- Notes: the exact factor is 1.10231; the 0.01 % difference is below the resolution of the test

### `morrell_coarse_fine_boundary`

- Quantity: size separating the coarse (Mia) and fine (Mib) tumbling-mill terms of the Morrell method
- Value: 750
- Units: µm
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eqs. B2-B3, p. 6
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_tumbling_coarse`, `minephys.comminution.morrell_tumbling_fine`

### `morrell_coefficient`

- Quantity: coefficient of the Morrell energy-size relation
- Value: 4
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 2, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_energy`, `minephys.comminution.morrell_tumbling_coarse`, `minephys.comminution.morrell_tumbling_fine`, `minephys.comminution.morrell_crusher`, `minephys.comminution.morrell_hpgr`, `minephys.comminution.morrell_size_distribution_correction`

### `morrell_f_constant`

- Quantity: constant of the size exponent f(x) = -(0.295 + x/10^6) of the Morrell relation
- Value: 0.295
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 2, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_energy`, `minephys.comminution.morrell_tumbling_coarse`, `minephys.comminution.morrell_tumbling_fine`, `minephys.comminution.morrell_crusher`, `minephys.comminution.morrell_hpgr`, `minephys.comminution.morrell_size_distribution_correction`, `minephys.comminution.morrell_mib`

### `morrell_f_scale`

- Quantity: size scale of the size exponent f(x) = -(0.295 + x/10^6) of the Morrell relation
- Value: 1000000
- Units: µm
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 2, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_energy`, `minephys.comminution.morrell_tumbling_coarse`, `minephys.comminution.morrell_tumbling_fine`, `minephys.comminution.morrell_crusher`, `minephys.comminution.morrell_hpgr`, `minephys.comminution.morrell_size_distribution_correction`, `minephys.comminution.morrell_mib`

### `morrell_fine_grind_limit`

- Quantity: finest final grind for which the Morrell fine term is stated to apply (approximate)
- Value: 45
- Units: µm
- Role: limit
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: section B.1, p. 6 ("approximately 45 µm")
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_tumbling_fine`
- Notes: a final grind P80 below this size emits a ValidityWarning and the result is still returned

### `morrell_k1_pebble_crusher`

- Quantity: factor on the coarse tumbling-mill energy when a pebble crusher is in the circuit
- Value: 0.95
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B2, p. 6
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_tumbling_coarse`

### `morrell_k2_open_circuit`

- Quantity: open-circuit factor of the Morrell crushing energy
- Value: 1.19
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B4, p. 6
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_crusher`

### `morrell_k3_open_circuit`

- Quantity: open-circuit factor of the Morrell HPGR energy
- Value: 1.19
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B6, p. 7
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_hpgr`

### `morrell_ks_crusher`

- Quantity: coefficient of the crusher size-dependent factor Sc = min(55 (x1 x2)^-0.2, 1)
- Value: 55
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B5, p. 7
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_crusher`

### `morrell_ks_hpgr`

- Quantity: coefficient of the HPGR size-dependent factor Sh = min(35 (x1 x2)^-0.2, 1)
- Value: 35
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: section B.2.3, p. 7
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_hpgr`

### `morrell_mib_constant`

- Quantity: constant of the Morrell fine-grinding index Mib from the Bond ball-mill test
- Value: 18.18
- Units: kWh/t
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 1, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_mib`

### `morrell_mib_screen_exponent`

- Quantity: exponent of the closing screen size in the Morrell Mib relation
- Value: 0.295
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. 1, p. 2
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_mib`

### `morrell_relative_error_sd`

- Quantity: one standard deviation of the relative error of the Morrell method
- Value: 0.065
- Units: 1
- Role: limit
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: p. 3 ("1 standard deviation is 6.5 % of the relative errors")
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_energy`
- Notes: stated in the model card of the energy functions; not used in a computation

### `morrell_s_exponent`

- Quantity: exponent of the product of feed and product sizes in the crusher and HPGR size-dependent factors
- Value: -0.2
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: eq. B5, p. 7
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_crusher`, `minephys.comminution.morrell_hpgr`

### `morrell_ws_factor`

- Quantity: factor of the Morrell size-distribution correction energy
- Value: 0.19
- Units: 1
- Role: model_constant
- Citation: `gmsg2016morrell`, https://www.smctesting.com/documents/Morrell_method_for_determining_comminution_circuit_specific_energy_and_assessing_energy_utilization_efficiency_of_existing_circuits.pdf
- Page: section B.2.4, p. 8
- Verification: verified (2026-10-06)
- Symbol: `minephys.comminution.morrell_size_distribution_correction`
