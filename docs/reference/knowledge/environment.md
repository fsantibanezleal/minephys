# Environment constants and limits (AP-42, ISC3, lidar dust)

Table `environment`, licence CC-BY-4.0.

Items: 194
UNVERIFIED: 2

### `ap42_days_per_year`

- Quantity: days per year in the AP-42 annual precipitation correction
- Value: 365
- Units: d
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: eq. 2, p. 13.2.2-7
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.precipitation_correction`

### `ap42_industrial_a_pm10`

- Quantity: AP-42 industrial unpaved road silt exponent a for PM10
- Value: 0.9
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_a_pm25`

- Quantity: AP-42 industrial unpaved road silt exponent a for PM2.5
- Value: 0.9
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_a_pm30`

- Quantity: AP-42 industrial unpaved road silt exponent a for PM30
- Value: 0.7
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_b_pm10`

- Quantity: AP-42 industrial unpaved road weight exponent b for PM10
- Value: 0.45
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_b_pm25`

- Quantity: AP-42 industrial unpaved road weight exponent b for PM2.5
- Value: 0.45
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_b_pm30`

- Quantity: AP-42 industrial unpaved road weight exponent b for PM30
- Value: 0.45
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_k_pm10`

- Quantity: AP-42 industrial unpaved road emission factor coefficient k for PM10
- Value: 1.5
- Units: lb/VMT
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_k_pm25`

- Quantity: AP-42 industrial unpaved road emission factor coefficient k for PM2.5
- Value: 0.15
- Units: lb/VMT
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_industrial_k_pm30`

- Quantity: AP-42 industrial unpaved road emission factor coefficient k for PM30
- Value: 4.9
- Units: lb/VMT
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-2, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_lb_per_vmt_in_g_per_vkt`

- Quantity: AP-42 printed conversion of 1 lb per vehicle mile travelled
- Value: 281.9
- Units: g/VKT
- Role: conversion
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: p. 13.2.2-4
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`
- Notes: printed to four significant figures; the exact conversion is 281.9 g/VKT to within 2e-4

### `ap42_mile_in_m`

- Quantity: length of the international mile in metres (exact)
- Value: 1609.344
- Units: m
- Role: conversion
- Citation: `nisthb44`, DOI 10.6028/NIST.HB.44-2026, https://nvlpubs.nist.gov/nistpubs/hb/2026/NIST.HB.44-2026.pdf
- Page: Appendix C, PDF page 531 (1 mile = 1 609.344 m)
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`
- Notes: AP-42 gives the vehicle mile travelled; 5280 international feet

### `ap42_range_moisture`

- Quantity: validity range of the AP-42 surface moisture content for industrial roads
- Range: 0.03 to 13.0
- Units: %
- Role: limit
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-3, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`

### `ap42_range_silt`

- Quantity: validity range of the AP-42 silt content for industrial roads
- Range: 1.8 to 25.2
- Units: %
- Role: limit
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-3, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`

### `ap42_range_speed`

- Quantity: validity range of the AP-42 mean vehicle speed for industrial roads
- Range: 5.0 to 43.0
- Units: mph
- Role: limit
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-3, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`
- Notes: the metric column of the table prints 8 to 69 km/h

### `ap42_range_weight`

- Quantity: validity range of the AP-42 mean vehicle weight for industrial roads
- Range: 2.0 to 290.0
- Units: short tons
- Role: limit
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-3, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`
- Notes: the metric column of the table prints 1.8 to 260 Mg, the source rounding

### `ap42_range_wheels`

- Quantity: validity range of the AP-42 mean number of wheels for industrial roads
- Range: 4.0 to 17.0
- Units: 1
- Role: limit
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Table 13.2.2-3, p. 13.2.2-5
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`

### `ap42_short_ton_in_kg`

- Quantity: mass of the short ton (2000 lb) in kilograms
- Value: 907.18474
- Units: kg
- Role: conversion
- Citation: `nisthb44`, DOI 10.6028/NIST.HB.44-2026, https://nvlpubs.nist.gov/nistpubs/hb/2026/NIST.HB.44-2026.pdf
- Page: Appendix C (the figure 907.18474 kg was not located in the extracted text)
- Verification: UNVERIFIED
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`, `minephys.environment.ap42_unpaved_validity`
- Notes: exact by the definition 2000 lb x 0.45359237 kg/lb; kept as its own row so that the weight conversion does not move with the pound row

### `ap42_silt_reference`

- Quantity: reference silt content of the AP-42 equation 1a
- Value: 12
- Units: %
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: eq. 1a, p. 13.2.2-4
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_watering_ce_1`

- Quantity: vertex 1 of the watering control-efficiency curve - control efficiency
- Value: 0
- Units: %
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_watering_ce_2`

- Quantity: vertex 2 of the watering control-efficiency curve - control efficiency
- Value: 0
- Units: %
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_watering_ce_3`

- Quantity: vertex 3 of the watering control-efficiency curve - control efficiency
- Value: 75
- Units: %
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_watering_ce_4`

- Quantity: vertex 4 of the watering control-efficiency curve - control efficiency
- Value: 95
- Units: %
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`
- Notes: the vector path of the figure gives 94.99 % at the end of the axis; 95 % is used

### `ap42_watering_m_1`

- Quantity: vertex 1 of the watering control-efficiency curve - ratio of the moisture of the watered surface to that of the uncontrolled surface
- Value: 0
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`
- Notes: vertices read on the vector path of the figure

### `ap42_watering_m_2`

- Quantity: vertex 2 of the watering control-efficiency curve - ratio of the moisture of the watered surface to that of the uncontrolled surface
- Value: 1
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_watering_m_3`

- Quantity: vertex 3 of the watering control-efficiency curve - ratio of the moisture of the watered surface to that of the uncontrolled surface
- Value: 2
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_watering_m_4`

- Quantity: vertex 4 of the watering control-efficiency curve - ratio of the moisture of the watered surface to that of the uncontrolled surface
- Value: 5
- Units: 1
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: Figure 13.2.2-2, p. 13.2.2-12
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.watering_control_efficiency`

### `ap42_weight_reference`

- Quantity: reference mean vehicle weight of the AP-42 equation 1a
- Value: 3
- Units: short tons
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: eq. 1a, p. 13.2.2-4
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.ap42_unpaved_emission_factor`

### `ap42_wet_day_threshold`

- Quantity: precipitation depth that counts a day as a wet day in the AP-42 annual correction
- Value: 0.254
- Units: mm
- Role: model_constant
- Citation: `epa2006ap42s1322`, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf
- Page: eq. 2, p. 13.2.2-7
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.precipitation_correction`

### `extinction_efficiency_large_particle`

- Quantity: extinction efficiency Q_ext of particles much larger than the wavelength
- Value: 2
- Units: 1
- Role: model_constant
- Citation: `bohren1983absorption`, DOI 10.1002/9783527618156
- Page: page not read (bibliographic, 1983 edition)
- Verification: UNVERIFIED
- Symbol: `minephys.environment.mass_extinction_coefficient`
- Notes: the large-particle limit; a model constant that warns when it is the default

### `isc3_briggs_urban_y_a_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class A
- Value: 0.32
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_a_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class A
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_a_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class A
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_b_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class B
- Value: 0.32
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_b_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class B
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_b_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class B
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_c_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class C
- Value: 0.22
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_c_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class C
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_c_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class C
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_d_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class D
- Value: 0.16
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_d_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class D
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_d_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class D
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_e_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class E
- Value: 0.11
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_e_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class E
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_e_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class E
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_f_coef`

- Quantity: ISC3 Briggs urban sigma_y coef, class F
- Value: 0.11
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_f_exponent`

- Quantity: ISC3 Briggs urban sigma_y exponent, class F
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_y_f_slope`

- Quantity: ISC3 Briggs urban sigma_y slope, class F
- Value: 0.0004
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-3, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_a_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class A
- Value: 0.24
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_a_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class A
- Value: 0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_a_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class A
- Value: 0.001
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_b_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class B
- Value: 0.24
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_b_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class B
- Value: 0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_b_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class B
- Value: 0.001
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_c_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class C
- Value: 0.2
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_c_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class C
- Value: 0
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: Table 1-4 prints 0.20 x with no correction term - written as slope 0 and exponent 0

### `isc3_briggs_urban_z_c_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class C
- Value: 0
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: Table 1-4 prints 0.20 x with no correction term - written as slope 0 and exponent 0

### `isc3_briggs_urban_z_d_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class D
- Value: 0.14
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_d_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class D
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_d_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class D
- Value: 0.0003
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_e_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class E
- Value: 0.08
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_e_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class E
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_e_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class E
- Value: 0.0015
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_f_coef`

- Quantity: ISC3 Briggs urban sigma_z coef, class F
- Value: 0.08
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_f_exponent`

- Quantity: ISC3 Briggs urban sigma_z exponent, class F
- Value: -0.5
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_briggs_urban_z_f_slope`

- Quantity: ISC3 Briggs urban sigma_z slope, class F
- Value: 0.0015
- Units: 1/m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-4, p. 1-19
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_deg_to_rad`

- Quantity: degree to radian factor written in the ISC3 lateral dispersion equation
- Value: 0.017453293
- Units: rad/deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: eq. 1-33, p. 1-14
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_lid_uniform_ratio`

- Quantity: ISC3 ratio of sigma_z to the mixing height from which the vertical term is uniform
- Value: 1.6
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: eq. 1-51, p. 1-33
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.gaussian_plume`

### `isc3_pg_sigma_y_c_a`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class A
- Value: 24.167
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_c_b`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class B
- Value: 18.333
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_c_c`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class C
- Value: 12.5
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_c_d`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class D
- Value: 8.333
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_c_e`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class E
- Value: 6.25
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_c_f`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient c, stability class F
- Value: 4.1667
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_a`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class A
- Value: 2.5334
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_b`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class B
- Value: 1.8096
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_c`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class C
- Value: 1.0857
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_d`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class D
- Value: 0.72382
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_e`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class E
- Value: 0.54287
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_y_d_f`

- Quantity: ISC3 Pasquill-Gifford sigma_y coefficient d, stability class F
- Value: 0.36191
- Units: deg
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-1, p. 1-16
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class A
- Value: 122.8
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class A
- Value: 0.9447
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_1_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 1 of class A - upper distance
- Value: 0.1
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_2_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 2 of class A
- Value: 158.08
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_2_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 2 of class A
- Value: 1.0542
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_2_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 2 of class A - upper distance
- Value: 0.15
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_3_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 3 of class A
- Value: 170.22
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_3_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 3 of class A
- Value: 1.0932
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_3_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 3 of class A - upper distance
- Value: 0.2
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_4_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 4 of class A
- Value: 179.52
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_4_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 4 of class A
- Value: 1.1262
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_4_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 4 of class A - upper distance
- Value: 0.25
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_5_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 5 of class A
- Value: 217.41
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_5_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 5 of class A
- Value: 1.2644
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_5_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 5 of class A - upper distance
- Value: 0.3
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_6_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 6 of class A
- Value: 258.89
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_6_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 6 of class A
- Value: 1.4094
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_6_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 6 of class A - upper distance
- Value: 0.4
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_7_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 7 of class A
- Value: 346.75
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_7_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 7 of class A
- Value: 1.7283
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_7_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 7 of class A - upper distance
- Value: 0.5
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_8_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 8 of class A
- Value: 453.85
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_8_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 8 of class A
- Value: 2.1166
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_a_8_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 8 of class A - upper distance
- Value: 3.11
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_a_9_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 9 of class A
- Value: 5000
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: Table 1-2 prints ** (sigma_z equals 5000 m beyond 3.11 km) for class A - written as a = 5000 m and b = 0

### `isc3_pg_sigma_z_a_9_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 9 of class A
- Value: 0
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class B
- Value: 90.673
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class B
- Value: 0.93198
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_1_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 1 of class B - upper distance
- Value: 0.2
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_b_2_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 2 of class B
- Value: 98.483
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_2_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 2 of class B
- Value: 0.98332
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_2_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 2 of class B - upper distance
- Value: 0.4
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_b_3_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 3 of class B
- Value: 109.3
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_b_3_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 3 of class B
- Value: 1.0971
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_c_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class C
- Value: 61.141
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_c_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class C
- Value: 0.91465
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class D
- Value: 34.459
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class D
- Value: 0.86974
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_1_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 1 of class D - upper distance
- Value: 0.3
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_d_2_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 2 of class D
- Value: 32.093
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_2_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 2 of class D
- Value: 0.81066
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_2_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 2 of class D - upper distance
- Value: 1.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_d_3_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 3 of class D
- Value: 32.093
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_3_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 3 of class D
- Value: 0.64403
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_3_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 3 of class D - upper distance
- Value: 3.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_d_4_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 4 of class D
- Value: 33.504
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_4_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 4 of class D
- Value: 0.60486
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_4_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 4 of class D - upper distance
- Value: 10.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_d_5_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 5 of class D
- Value: 36.65
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_5_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 5 of class D
- Value: 0.56589
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_5_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 5 of class D - upper distance
- Value: 30.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_d_6_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 6 of class D
- Value: 44.053
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_d_6_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 6 of class D
- Value: 0.51179
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class E
- Value: 24.26
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class E
- Value: 0.8366
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_1_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 1 of class E - upper distance
- Value: 0.1
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_2_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 2 of class E
- Value: 23.331
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_2_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 2 of class E
- Value: 0.81956
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_2_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 2 of class E - upper distance
- Value: 0.3
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_3_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 3 of class E
- Value: 21.628
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_3_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 3 of class E
- Value: 0.7566
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_3_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 3 of class E - upper distance
- Value: 1.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_4_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 4 of class E
- Value: 21.628
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_4_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 4 of class E
- Value: 0.63077
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_4_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 4 of class E - upper distance
- Value: 2.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_5_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 5 of class E
- Value: 22.534
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_5_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 5 of class E
- Value: 0.57154
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_5_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 5 of class E - upper distance
- Value: 4.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_6_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 6 of class E
- Value: 24.703
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_6_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 6 of class E
- Value: 0.50527
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_6_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 6 of class E - upper distance
- Value: 10.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_7_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 7 of class E
- Value: 26.97
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_7_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 7 of class E
- Value: 0.46713
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_7_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 7 of class E - upper distance
- Value: 20.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_8_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 8 of class E
- Value: 35.42
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_8_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 8 of class E
- Value: 0.37615
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_8_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 8 of class E - upper distance
- Value: 40.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_e_9_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 9 of class E
- Value: 47.618
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_e_9_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 9 of class E
- Value: 0.29592
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_10_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 10 of class F
- Value: 34.219
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_10_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 10 of class F
- Value: 0.21716
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_1_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 1 of class F
- Value: 15.209
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_1_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 1 of class F
- Value: 0.81558
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_1_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 1 of class F - upper distance
- Value: 0.2
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_2_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 2 of class F
- Value: 14.457
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_2_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 2 of class F
- Value: 0.78407
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_2_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 2 of class F - upper distance
- Value: 0.7
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_3_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 3 of class F
- Value: 13.953
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_3_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 3 of class F
- Value: 0.68465
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_3_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 3 of class F - upper distance
- Value: 1.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_4_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 4 of class F
- Value: 13.953
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_4_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 4 of class F
- Value: 0.63227
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_4_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 4 of class F - upper distance
- Value: 2.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_5_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 5 of class F
- Value: 14.823
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_5_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 5 of class F
- Value: 0.54503
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_5_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 5 of class F - upper distance
- Value: 3.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_6_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 6 of class F
- Value: 16.187
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_6_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 6 of class F
- Value: 0.4649
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_6_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 6 of class F - upper distance
- Value: 7.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_7_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 7 of class F
- Value: 17.836
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_7_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 7 of class F
- Value: 0.41507
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_7_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 7 of class F - upper distance
- Value: 15.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_8_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 8 of class F
- Value: 22.651
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_8_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 8 of class F
- Value: 0.32681
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_8_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 8 of class F - upper distance
- Value: 30.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_pg_sigma_z_f_9_a`

- Quantity: ISC3 Pasquill-Gifford sigma_z coefficient a, band 9 of class F
- Value: 27.074
- Units: m
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_9_b`

- Quantity: ISC3 Pasquill-Gifford sigma_z exponent b, band 9 of class F
- Value: 0.27436
- Units: 1
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_pg_sigma_z_f_9_xmax`

- Quantity: ISC3 Pasquill-Gifford sigma_z band 9 of class F - upper distance
- Value: 60.0
- Units: km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2, pp. 1-17, 1-18
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`
- Notes: the band applies for distances above the previous upper distance and up to this one

### `isc3_sigma_y_scale`

- Quantity: scale of the ISC3 Pasquill-Gifford lateral dispersion coefficient
- Value: 465.11628
- Units: m/km
- Role: model_constant
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: eq. 1-32, p. 1-14
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_sigma_z_cap`

- Quantity: upper bound of the ISC3 Pasquill-Gifford sigma_z for classes A, B and C
- Value: 5000
- Units: m
- Role: limit
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: Table 1-2 footnotes, p. 1-17
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `isc3_urban_min_distance`

- Quantity: ISC3 distance below which urban concentrations may be suspect
- Value: 100
- Units: m
- Role: limit
- Citation: `epa1995isc3v2`, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf
- Page: p. 1-15
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.pasquill_sigmas`

### `lidar_dust_min_transmittance_low_reflectivity`

- Quantity: lowest transmittance at which a low-reflectivity target is still measured
- Value: 0.06
- Units: 1
- Role: limit
- Citation: `phillips2017dust`, DOI 10.1002/rob.21701
- Page: abstract, J. Field Robotics 34(5)
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.lidar_dust_return`

### `lidar_dust_min_transmittance_retroreflective`

- Quantity: lowest transmittance at which a retroreflective target is still measured
- Value: 0.02
- Units: 1
- Role: limit
- Citation: `phillips2017dust`, DOI 10.1002/rob.21701
- Page: abstract, J. Field Robotics 34(5)
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.lidar_dust_return`

### `lidar_dust_onset_transmittance`

- Quantity: atmospheric transmittance below which dust starts to affect lidar measurements
- Range: 0.71 to 0.74
- Units: 1
- Role: limit
- Citation: `phillips2017dust`, DOI 10.1002/rob.21701
- Page: abstract, J. Field Robotics 34(5)
- Verification: verified (2026-10-06)
- Symbol: `minephys.environment.lidar_dust_return`
- Notes: the abstract reports 71 % to 74 %, quite variable with conditions; read as the one-way transmittance (UNVERIFIED interpretation)
