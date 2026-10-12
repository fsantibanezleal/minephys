# Blasting constants, limits and parameters

Table `blasting`, licence CC-BY-4.0.

Items: 38
UNVERIFIED: 13

### `cfr_816_67_distance_band_mid_max`

- Quantity: upper end of the second distance band
- Value: 5000
- Units: ft
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(2)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.ppv_limit`, `minephys.blasting.max_charge_per_delay`

### `cfr_816_67_distance_band_near_max`

- Quantity: upper end of the first distance band
- Value: 300
- Units: ft
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(2)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.ppv_limit`, `minephys.blasting.max_charge_per_delay`

### `cfr_816_67_ppv_limit_far`

- Quantity: maximum peak particle velocity, 5,001 ft and beyond
- Value: 0.75
- Units: in/s
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(2)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.ppv_limit`

### `cfr_816_67_ppv_limit_mid`

- Quantity: maximum peak particle velocity, 301 to 5,000 ft
- Value: 1.0
- Units: in/s
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(2)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.ppv_limit`

### `cfr_816_67_ppv_limit_near`

- Quantity: maximum peak particle velocity, 0 to 300 ft
- Value: 1.25
- Units: in/s
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(2)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.ppv_limit`

### `cfr_816_67_scaled_distance_factor_far`

- Quantity: scaled-distance factor Ds, 5,001 ft and beyond
- Value: 65
- Units: ft/lb^½
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(3)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.max_charge_per_delay`
- Notes: charge limit W = (D / Ds)^2 lb per 8-millisecond period

### `cfr_816_67_scaled_distance_factor_mid`

- Quantity: scaled-distance factor Ds, 301 to 5,000 ft
- Value: 55
- Units: ft/lb^½
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(3)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.max_charge_per_delay`
- Notes: charge limit W = (D / Ds)^2 lb per 8-millisecond period

### `cfr_816_67_scaled_distance_factor_near`

- Quantity: scaled-distance factor Ds, 0 to 300 ft
- Value: 50
- Units: ft/lb^½
- Role: limit
- Citation: `cfr30_816_67`, https://www.law.cornell.edu/cfr/text/30/816.67
- Page: § 816.67(d)(3)(i)
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.max_charge_per_delay`
- Notes: charge limit W = (D / Ds)^2 lb per 8-millisecond period

### `cunningham_n_burden_coefficient`

- Quantity: coefficient of B/d (d in mm) in the uniformity index first factor
- Value: 14
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 3, p. 202
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.uniformity_index`
- Notes: the 1987 form

### `cunningham_n_charge_exponent`

- Quantity: exponent of the charge-length term of the uniformity index
- Value: 0.1
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 3, p. 202
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.uniformity_index`
- Notes: the 1987 form

### `cunningham_n_charge_offset`

- Quantity: offset added to |BCL - CCL| / L in the uniformity index
- Value: 0.1
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 3, p. 202
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.uniformity_index`
- Notes: the 1987 form

### `cunningham_n_constant`

- Quantity: constant term of the uniformity index first factor
- Value: 2.2
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 3, p. 202
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.uniformity_index`
- Notes: the 1987 form

### `flyrock_air_density_reference`

- Quantity: reference air density used for flyrock trajectories
- Value: 1.24
- Units: kg/m³
- Role: parameter
- Citation: `szendrei2022`, DOI 10.17159/2411-9717/1873/2022
- Page: p. 728
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.flyrock_trajectory`
- Notes: documented value, never a default

### `flyrock_drag_coefficient_range`

- Quantity: published range of the drag coefficient of flyrock fragments
- Range: 0.6 to 1.8
- Units: 1
- Role: parameter
- Citation: `szendrei2022`, DOI 10.17159/2411-9717/1873/2022
- Page: p. 728
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.flyrock_trajectory`
- Notes: documented range, never a default

### `kuznetsov_charge_exponent`

- Quantity: exponent of the charge per hole in the Kuznetsov mean size
- Value: 1/6
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 1, p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`

### `kuznetsov_powder_factor_exponent`

- Quantity: exponent of the powder factor in the Kuznetsov mean size
- Value: -0.8
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 1, p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`

### `kuznetsov_tnt_relative_weight_strength`

- Quantity: relative weight strength of TNT (ANFO = 100)
- Value: 115
- Units: 1 (ANFO = 100)
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 1, p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: 115 being the RWS of TNT

### `kuzram_hardness_modulus_divisor`

- Quantity: divisor of Young's modulus (GPa) in the hardness factor
- Value: 3
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: p. 205
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.hardness_factor`

### `kuzram_hardness_modulus_switch`

- Quantity: Young's modulus below which the hardness factor uses the modulus
- Value: 50
- Units: GPa
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: p. 205
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.hardness_factor`

### `kuzram_hardness_ucs_divisor`

- Quantity: divisor of the uniaxial compressive strength (MPa) in the hardness factor
- Value: 5
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: p. 205
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.hardness_factor`

### `kuzram_rdi_density_coefficient`

- Quantity: coefficient of the density in the rock density influence
- Value: 0.025
- Units: 1/(kg/m³)
- Role: model_constant
- Citation: `mutinda2021`, DOI 10.17159/2411-9717/1401/2021
- Page: eq. 5, p. 109
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.rock_density_influence`
- Notes: Cunningham 1987 (primary not read); secondary transcription only

### `kuzram_rdi_offset`

- Quantity: offset of the rock density influence
- Value: 50
- Units: 1
- Role: model_constant
- Citation: `mutinda2021`, DOI 10.17159/2411-9717/1401/2021
- Page: eq. 5, p. 109
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.rock_density_influence`
- Notes: Cunningham 1987 (primary not read); secondary transcription only

### `kuzram_rock_factor_coefficient`

- Quantity: coefficient of the rock factor sum
- Value: 0.06
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 4, p. 204
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.rock_factor`

### `kuzram_rock_factor_max`

- Quantity: largest rock factor of Cunningham's range
- Value: 22
- Units: 1
- Role: limit
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: the rock factor varies between 0.8 and 22

### `kuzram_rock_factor_min`

- Quantity: smallest rock factor of Cunningham's range
- Value: 0.8
- Units: 1
- Role: limit
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: the rock factor varies between 0.8 and 22

### `kuzram_rws_exponent_1983`

- Quantity: exponent of the relative weight strength ratio, 1983/1987 form
- Value: 19/30
- Units: 1
- Role: model_constant
- Citation: `mutinda2021`, DOI 10.17159/2411-9717/1401/2021
- Page: eq. 2, p. 109
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: Cunningham 1983/1987 (primary not read); Mutinda et al. 2021 print 19/30 and attribute it to Cunningham 2005, which prints 19/20; secondary transcription only

### `kuzram_rws_exponent_2005`

- Quantity: exponent of the relative weight strength ratio, Cunningham 2005 form
- Value: 19/20
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 1, p. 201
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.kuznetsov_x50`

### `kuzram_uniformity_typical_max`

- Quantity: upper end of the typical uniformity index range
- Value: 1.5
- Units: 1
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.uniformity_index`
- Notes: typical range associated with the formula; the literature source was not read

### `kuzram_uniformity_typical_min`

- Quantity: lower end of the typical uniformity index range
- Value: 0.8
- Units: 1
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.uniformity_index`
- Notes: typical range associated with the formula; the literature source was not read

### `lundborg_max_range_coefficient`

- Quantity: coefficient of Lundborg's empirical maximum throw
- Value: 260
- Units: m/in^(2/3)
- Role: model_constant
- Citation: `szendrei2022`, DOI 10.17159/2411-9717/1873/2022
- Page: eq. 1, p. 726
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.flyrock_range_lundborg`
- Notes: Lundborg (primary not read); secondary transcription only

### `lundborg_max_range_exponent`

- Quantity: exponent of the hole diameter in Lundborg's maximum throw
- Value: 2/3
- Units: 1
- Role: model_constant
- Citation: `szendrei2022`, DOI 10.17159/2411-9717/1873/2022
- Page: eq. 1, p. 726
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.flyrock_range_lundborg`
- Notes: Lundborg (primary not read); secondary transcription only

### `rosin_rammler_median_constant`

- Quantity: constant printed in the Rosin-Rammler median form
- Value: 0.693
- Units: 1
- Role: model_constant
- Citation: `cunningham2005`, https://www.smctesting.com/documents/mine-to-mill/The%20kuz%20ram%20fragmentation%20model%2020%20years%20on.pdf
- Page: eq. 2, p. 202
- Verification: verified (2026-10-06)
- Symbol: `minephys.blasting.rosin_rammler_passing`, `minephys.blasting.rosin_rammler_size`
- Notes: documented only: the library uses ln 2 (relative difference 2.1e-4) so that x50 is exactly the median

### `tripwire_air_density_max`

- Quantity: unit tripwire: largest plausible air density
- Value: 2.0
- Units: kg/m³
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.flyrock_trajectory`
- Notes: design choice of the specification, not a measurement

### `tripwire_hole_diameter_max`

- Quantity: unit tripwire: largest plausible hole diameter
- Value: 1.0
- Units: m
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.charge_per_hole`, `minephys.blasting.uniformity_index`, `minephys.blasting.flyrock_range_lundborg`
- Notes: design choice of the specification, not a measurement

### `tripwire_k_site_max`

- Quantity: unit tripwire: largest plausible site constant K
- Value: 100.0
- Units: m/s
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.ppv_scaled_distance`
- Notes: design choice of the specification, not a measurement

### `tripwire_launch_speed_max`

- Quantity: unit tripwire: largest plausible launch speed
- Value: 500.0
- Units: m/s
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.flyrock_range_no_drag`, `minephys.blasting.flyrock_trajectory`
- Notes: design choice of the specification, not a measurement

### `tripwire_powder_factor_max`

- Quantity: unit tripwire: largest plausible powder factor
- Value: 5.0
- Units: kg/m³
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: design choice of the specification, not a measurement

### `tripwire_rws_min`

- Quantity: unit tripwire: smallest plausible relative weight strength (ANFO = 100)
- Value: 20.0
- Units: 1 (ANFO = 100)
- Role: limit
- Citation: `minephys:spec-002-blasting`, https://github.com/fsantibanezleal/minephys/blob/main/specs/002-blasting/spec.md
- Page: §7.3
- Verification: UNVERIFIED
- Symbol: `minephys.blasting.kuznetsov_x50`
- Notes: design choice of the specification, not a measurement
