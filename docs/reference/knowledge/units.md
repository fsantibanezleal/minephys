# Unit definitions and defined physical constants

Table `units`, licence CC-BY-4.0.

Items: 6
UNVERIFIED: 0

### `foot`

- Quantity: length of one international foot in metres (exact)
- Value: 0.3048
- Units: m
- Role: conversion
- Citation: `nistsp811`, DOI 10.6028/NIST.SP.811e2008
- Page: Appendix B.8
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.ft_to_m`, `minephys.units.m_to_ft`
- Notes: exact by definition

### `inch`

- Quantity: length of one international inch in metres (exact)
- Value: 0.0254
- Units: m
- Role: conversion
- Citation: `nistsp811`, DOI 10.6028/NIST.SP.811e2008
- Page: Appendix B.8; NIST Handbook 44 (2026), Appendix C, p. 21 ("2.54 centimeters (exactly)")
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.in_per_s_to_m_per_s`, `minephys.units.m_per_s_to_in_per_s`, `minephys.units.us_gal_to_m3`, `minephys.units.m3_to_us_gal`
- Notes: exact by definition

### `kilowatt_hour`

- Quantity: energy of one kilowatt-hour in joules (exact)
- Value: 3600000.0
- Units: J
- Role: conversion
- Citation: `nistsp811`, DOI 10.6028/NIST.SP.811e2008
- Page: Appendix B.8
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.kwh_to_j`, `minephys.units.j_to_kwh`
- Notes: 3.6e6 J, exact by definition (written as a decimal because YAML 1.1 reads 3.6e6 as a string)

### `pound`

- Quantity: mass of one avoirdupois pound in kilograms (exact)
- Value: 0.45359237
- Units: kg
- Role: conversion
- Citation: `nisthb44`, DOI 10.6028/NIST.HB.44-2026, https://nvlpubs.nist.gov/nistpubs/hb/2026/NIST.HB.44-2026.pdf
- Page: Appendix C, p. 17 (avoirdupois pound)
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.lb_to_kg`, `minephys.units.kg_to_lb`
- Notes: exact by definition

### `standard_gravity`

- Quantity: standard acceleration of free fall (exact defined value)
- Value: 9.80665
- Units: m/s²
- Role: conversion
- Citation: `nistsp811`, DOI 10.6028/NIST.SP.811e2008
- Page: Appendix B.8
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.us_gal_to_m3`
- Notes: acceleration of free fall, standard, exact; the models take it as the default of their g argument

### `us_gallon_cubic_inches`

- Quantity: volume of one US liquid gallon in cubic inches (exact)
- Value: 231
- Units: in³
- Role: conversion
- Citation: `nisthb44`, DOI 10.6028/NIST.HB.44-2026, https://nvlpubs.nist.gov/nistpubs/hb/2026/NIST.HB.44-2026.pdf
- Page: Appendix C, p. 25 ("231 cubic inches (exactly)")
- Verification: verified (2026-10-07)
- Symbol: `minephys.units.us_gal_to_m3`, `minephys.units.m3_to_us_gal`
- Notes: with 1 in = 0.0254 m the US gallon is 3.785411784e-3 m³, derived exactly in code
