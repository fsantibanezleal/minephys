# Spec 006 — Environment: AP-42 unpaved-road dust, Gaussian plume dispersion and Beer–Lambert dust attenuation for lidar
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent

`minephys.environment` gives reference implementations of the screening-grade chain from haul-road traffic to dust
concentration and to its effect on lidar:

- the US EPA AP-42 §13.2.2 (November 2006) emission factor for unpaved industrial roads (equation 1a), its validity
  ranges (Table 13.2.2-3), the fleet-mean vehicle weight rule, the annual precipitation correction (equation 2) and the
  watering control-efficiency curve (Figure 13.2.2-2);
- steady-state Gaussian plume dispersion with ground reflection and optional mixing-lid reflections, the
  Pasquill–Gifford (rural) and Briggs (urban) dispersion coefficients as implemented in the EPA ISC3 model, and
  infinite and finite crosswind line sources for roads;
- Beer–Lambert attenuation by airborne dust (extinction from mass concentration), one- and two-way transmittance, and a
  lidar-return state calibrated to the transmittance thresholds measured in a mining-dust lidar study.

AP-42 is published in US customary units; the functions take SI arguments and convert explicitly with the foundation
`units` table. Every constant is a cited row of `knowledge/environment.yaml` (foundation DC-000-02, served by spec
008-knowledge).

**Who benefits:** environmental and mining engineers who need an inspectable, unit-safe screening chain; PitStudio,
whose haul-road dust case and lidar dust model use these functions live and in the studio.

**Out of scope:** regulatory dispersion modelling (AERMOD-class Monin–Obukhov similarity, terrain, building downwash,
plume rise, deposition, chemistry), paved roads (§13.2.1), chemically stabilised roads (equation 1a does not apply to
them), the public-road equation 1b, petroleum-resin control curves, Lagrangian particle dispersion and Stokes settling
(PitStudio studio physics), camera haze models, and lidar waveform simulation. Results are educational and
screening-grade, not air-permitting values.

## 2. User stories

### US-006-1 (P1) Haul-road emission factor
As an environmental engineer, I want the AP-42 unpaved-road emission factor in SI units with validity warnings, its
precipitation correction and its watering control efficiency, so that I can estimate PM2.5/PM10/PM30 emissions of a
haul road and see when heavy trucks extrapolate the regression. Independent test: AP-42's own printed numbers
(fleet-mean weight, controlled-factor table, unit conversion) reproduce.

### US-006-2 (P1) Plume dispersion
As a student, I want a Gaussian plume with ground reflection, rural and urban dispersion coefficients and road line
sources, so that I can map receptor concentrations from an emission rate and a stability class. Independent test: the
plume's downwind mass flux equals the emission rate by quadrature.

### US-006-3 (P2) Dust and lidar
As a perception engineer, I want the transmittance of a lidar path through dust and a return state calibrated to a
published mining-dust study, so that I can degrade simulated lidar consistently with measured behaviour. Independent
test: optical depths at the published thresholds (71–74 %, 2 %, 6 %) give the documented states.

### US-006-4 (P2) Cited constants
As a reviewer, I want every AP-42, ISC3 and lidar-study constant to be a cited knowledge row with page and status, so
that I can audit each number. Independent test: changing a knowledge row changes the result accordingly.

## 3. Functional requirements (EARS)

Conventions (000-foundation): SI units at the API (FR-000-08; mass in kg, length in m, time in s, speed in m/s,
emission factor in kg per vehicle-metre travelled, emission rates in kg/s or kg/(m·s), concentration in kg/m³,
extinction in 1/m, silt and moisture contents as fractions); elementwise functions follow FR-000-07; non-finite,
shape, size, domain and option errors raise `minephys.InputError` naming the argument (FR-000-10, FR-000-12 to
FR-000-15), non-numeric arguments `minephys.InputTypeError` (FR-000-11); validity-range violations emit
`minephys.ValidityWarning` (FR-000-16). Unit factors come from the foundation `units` table (exact definitions:
1 lb = 0.45359237 kg, 1 mile = 1,609.344 m, 1 short ton = 907.18474 kg, 1 mph = 0.44704 m/s).

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-006-01 | Ubiquitous | `ap42_unpaved_emission_factor(silt_fraction, mean_weight, size_class, mean_speed=None, mean_wheels=None, moisture_fraction=None, strict=False)` shall return, in kg per vehicle-metre, $E = k\,(s/12)^a\,(W/3)^b \times 0.45359237/1609.344$ with $s$ = 100 × `silt_fraction` (%) and $W$ = `mean_weight` / 907.18474 (short tons), and $(k, a, b)$ = (0.15, 0.9, 0.45), (1.5, 0.9, 0.45), (4.9, 0.7, 0.45) lb/VMT for `size_class` `"PM2.5"`, `"PM10"`, `"PM30"`, within TC-1 of the hand calculation; the optional arguments enter only the validity check. | unit |
| FR-006-02 | Ubiquitous | `ap42_unpaved_validity(silt_fraction, mean_weight, mean_speed=None, mean_wheels=None, moisture_fraction=None)` shall return a named tuple of boolean arrays, one per given argument plus `all`, true where the value lies inside the Table 13.2.2-3 industrial-road range (silt 1.8–25.2 %, weight 2–290 short tons, speed 5–43 mph, 4–17 wheels, moisture 0.03–13 %), bounds inclusive. | unit |
| FR-006-03 | Unwanted | If an argument of `ap42_unpaved_emission_factor` lies outside its Table 13.2.2-3 range, then the function shall emit `ValidityWarning` naming the argument, the bounds and the row id and shall return the extrapolated value (FR-000-16); while `strict=True` it shall raise `InputError` instead. | unit (`pytest.warns`) |
| FR-006-04 | Ubiquitous | `fleet_mean_vehicle_weight(weights, traffic_fractions)` shall return the traffic-weighted mean $\sum_i w_i f_i / \sum_i f_i$ (kg), the single fleet weight that AP-42 requires instead of per-class factors. | unit |
| FR-006-05 | Ubiquitous | `precipitation_correction(emission_factor, wet_days)` shall return $E_{ext} = E\,(365 - P)/365$, with $P$ the number of days a year with at least 0.254 mm of precipitation. | unit |
| FR-006-06 | Ubiquitous | `watering_control_efficiency(moisture_ratio)` shall return the instantaneous control efficiency (fraction) by linear interpolation between the vertices $(M, CE)$ = (0, 0), (1, 0), (2, 0.75), (5, 0.95) of Figure 13.2.2-2, and `controlled_emission_factor(emission_factor, control_efficiency)` shall return $E\,(1 - CE)$. | unit |
| FR-006-07 | Unwanted | If an AP-42 function (FR-006-01 to FR-006-06) gets NaN/inf, a silt fraction ≤ 0 or > 1, a weight, speed or wheel count ≤ 0, a moisture fraction outside [0, 1], an unknown `size_class`, negative or all-zero traffic fractions, mismatched lengths, `wet_days` outside [0, 365], a moisture ratio outside [0, 5], a control efficiency outside [0, 1] or a negative emission factor, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-006-08 | Ubiquitous | `line_emission_rate(emission_factor, vehicles_per_second)` shall return the road's emission per unit length $q_\ell = E \cdot n$ in kg/(m·s). | unit |
| FR-006-09 | Ubiquitous | `pasquill_sigmas(x, stability_class, terrain="rural")` shall return $(\sigma_y, \sigma_z)$ in m at downwind distance $x$ (m): for `"rural"`, $\sigma_y = 465.11628\,x_{km} \tan\!\big(0.017453293\,(c - d \ln x_{km})\big)$ with $(c, d)$ of ISC3 Table 1-1 and $\sigma_z = a\,x_{km}^{\,b}$ with the distance-band $(a, b)$ of Table 1-2 (band $k$ applies for $x_{km}$ in (upper$_{k-1}$, upper$_k$]), capped at 5,000 m for classes A, B and C and equal to 5,000 m for class A beyond 3.11 km; for `"urban"`, the Briggs formulas of Tables 1-3 and 1-4 with $x$ in m. | unit |
| FR-006-10 | Unwanted | If `pasquill_sigmas` gets `terrain="urban"` and $x < 100$ m, then it shall emit `ValidityWarning` naming `x` and the row `isc3_urban_min_distance` (ISC3: concentrations closer than 100 m may be suspect) and shall still return the result. | unit (`pytest.warns`) |
| FR-006-11 | Ubiquitous | `gaussian_plume(q, u, y, z, h, sigma_y, sigma_z, mixing_height=None)` shall return the steady-state concentration $C = \dfrac{q}{2\pi u \sigma_y \sigma_z} e^{-y^2/2\sigma_y^2}\,V$ (kg/m³) with the ground-reflection vertical term $V = e^{-(z-h)^2/2\sigma_z^2} + e^{-(z+h)^2/2\sigma_z^2}$. | unit + property |
| FR-006-12 | Optional | Where `mixing_height` $z_i$ is given, `gaussian_plume` shall add the image-source series of ISC3 eq. 1-50 (terms $H_1 \dots H_4$ for $i = 1, 2, \dots$ until a term is below 1e-16 of the sum, at most 1,000 terms), shall use $V = \sqrt{2\pi}\,\sigma_z / z_i$ (eq. 1-51) where $\sigma_z / z_i \ge 1.6$, and shall return 0 where $h > z_i$. | unit + property |
| FR-006-13 | Ubiquitous | `line_source_plume(q_line, u, z, h, sigma_z)` shall return the concentration downwind of an infinite crosswind line source, $C = \dfrac{q_\ell}{\sqrt{2\pi}\,u\,\sigma_z}\,V$ (kg/m³), and `finite_line_source_plume(q_line, u, y, z, h, y1, y2, sigma_y, sigma_z)` that of a crosswind segment $[y_1, y_2]$, $C = \dfrac{q_\ell}{2\sqrt{2\pi}\,u\,\sigma_z}\big[\operatorname{erf}\tfrac{y_2 - y}{\sqrt 2 \sigma_y} - \operatorname{erf}\tfrac{y_1 - y}{\sqrt 2 \sigma_y}\big] V$. | unit + property |
| FR-006-14 | Unwanted | If `pasquill_sigmas`, `gaussian_plume`, `line_source_plume`, `finite_line_source_plume` or `line_emission_rate` gets NaN/inf, $x \le 0$, an unknown stability class (not exactly `"A"` to `"F"`) or terrain, $u \le 0$, $\sigma \le 0$, $z < 0$, $h < 0$, a negative emission or vehicle rate, $y_1 \ge y_2$, a mixing height ≤ 0, or unbroadcastable arrays, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-006-15 | Ubiquitous | `mass_extinction_coefficient(diameter, particle_density, extinction_efficiency=None)` (with `None` meaning the row `extinction_efficiency_large_particle`, 2) shall return $k_m = 3 Q_{ext} / (2 \rho_p D)$ (m²/kg) for spheres of diameter $D$ (m) and density $\rho_p$ (kg/m³), and `extinction_coefficient(mass_concentration, mass_extinction)` shall return $\beta = k_m C$ (1/m). | unit |
| FR-006-16 | Ubiquitous | `beer_lambert_transmittance(extinction, path_length)` shall return $T = e^{-\beta L}$, and `path_transmittance(positions, extinction_profile)` shall return $T = \exp(-\int \beta\,ds)$ with the integral by the trapezoid rule over the given positions (exact for piecewise-linear profiles). | unit + property |
| FR-006-17 | Ubiquitous | `lidar_dust_return(distance, extinction, positions=None, target="retroreflective", onset_transmittance=None, min_transmittance=None)` shall return the one-way transmittance $T$ of the sensor-to-target path (uniform `extinction` over `distance`, or, with `positions` from 0 to `distance`, the profile integrated as in FR-006-16), the two-way transmittance $T^2$, the optical depth $-\ln T$ and a state: `"unaffected"` where $T \ge$ the onset threshold (default 0.74, the upper end of the published 71–74 % band), `"degraded"` where the target minimum ≤ $T$ < onset (defaults 0.02 retroreflective, 0.06 low reflectivity), and `"lost"` where $T$ is below the target minimum; with a profile it shall also return the distance of the cloud's leading edge (first position with $\beta > 0$, or `None` when there is none). | unit |
| FR-006-18 | Unwanted | If a Beer–Lambert or lidar function gets NaN/inf, a negative extinction, concentration or length, a non-positive distance, diameter, density or extinction efficiency, positions that are not strictly increasing, not starting at 0 or not ending at `distance`, a profile of a different length, more than 10⁶ profile points, an unknown `target`, or thresholds outside (0, 1) with minimum ≥ onset, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-006-19 | Ubiquitous | Every constant in FR-006-01 to FR-006-17 shall be read through `minephys.knowledge.get_value` from its row of `knowledge/environment.yaml` or of the foundation `units` table (§7; foundation FR-000-19), so that replacing a row value in a test fixture changes the result by the corresponding analytical amount. | contract |

## 4. Correctness properties

Generators (Hypothesis, `property_tests` of `thresholds.yaml`): silt fraction in [0.018, 0.252]; weight in
[1,814, 263,083] kg (2–290 short tons) and, for extrapolation checks, up to 400,000 kg; wind speed log-uniform in
[0.5, 20] m/s; $x$ log-uniform in [10 m, 100 km]; heights in [0, 200] m; concentrations log-uniform in
[10⁻¹⁰, 10⁻²] kg/m³; float64 throughout.

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-006-01 | AP-42 power-law scaling: $E(\lambda s, W) = \lambda^{a} E(s, W)$ and $E(s, \lambda W) = \lambda^{b} E(s, W)$; hence $E$ strictly increases with silt and weight. | $\lambda \in [0.5, 2]$ | TC-1 |
| P-006-02 | AP-42 unit invariance: the SI result equals the published-unit expression evaluated in the test (lb/VMT with $s$ in % and $W$ in short tons) times $0.45359237/1609.344$; that factor equals AP-42's printed 1 lb/VMT = 281.9 g/VKT within rtol 2e-4. | valid inputs | TC-1; rtol 2e-4 |
| P-006-03 | AP-42 size-class relations: $E_{PM2.5} = 0.1\,E_{PM10}$, and $E_{PM10} < E_{PM30}$ for every silt fraction ≤ 1 and weight > 0. | full domain | TC-1; TC-0 (strict) |
| P-006-04 | Precipitation and control are linear and monotone: $E_{ext}$ is $E$ at $P = 0$, 0 at $P = 365$ and non-increasing in $P$; $CE(M)$ is continuous and non-decreasing on [0, 5]; `controlled_emission_factor` is linear in $E$. | $P \in [0, 365]$, $M \in [0, 5]$ | TC-1 |
| P-006-05 | Plume linearity and wind scaling: $C$ is linear in $q$ (two sources superpose) and $C(\lambda u) = C(u)/\lambda$ at fixed $\sigma$. | $\lambda \in [0.1, 10]$ | TC-1 |
| P-006-06 | Plume symmetry and reciprocity: $C(y) = C(-y)$, and $C$ is unchanged when the source height $h$ and the receptor height $z$ are exchanged. | as above | TC-0 / TC-1 |
| P-006-07 | Plume mass conservation: $u \int_{-\infty}^{\infty}\int_0^{\infty} C\,dz\,dy = q$ without a lid, and $u \int\int_0^{z_i} C\,dz\,dy = q$ with a lid and $h < z_i$. | $\sigma_y, \sigma_z \in [1, 500]$ m | rtol 1e-6 (quadrature) |
| P-006-08 | Line sources: `line_source_plume` equals the integral over $y$ of `gaussian_plume` with $q = q_\ell\,dy$; `finite_line_source_plume` tends to it as $[y_1, y_2] \to (-\infty, \infty)$ (≤ 1e-12 relative for half-length ≥ 10 $\sigma_y$) and is additive over adjacent segments. | as above | rtol 1e-8 (quadrature); TC-1 |
| P-006-09 | Dispersion coefficients: for every class $\sigma_y$ is strictly increasing in $x$ and $\sigma_z$ is non-decreasing except at the Table 1-2 band edges, where a drop is at most 1e-4 relative (hand-checked: largest drop 9e-5); at any fixed $x$ both are ordered A ≥ B ≥ C ≥ D ≥ E ≥ F. | $x \in$ [10 m, 100 km], both terrains | as stated |
| P-006-10 | Beer–Lambert multiplicativity: $T(L_1 + L_2) = T(L_1)\,T(L_2)$; two-way transmittance = one-way²; `path_transmittance` of a constant profile equals `beer_lambert_transmittance`. | as above | TC-1 |
| P-006-11 | Extinction scaling: optical depth is linear in concentration and in path length; $k_m \propto 1/D$ and $\propto 1/\rho_p$. | as above | TC-1 |
| P-006-12 | Lidar state monotonicity: increasing the concentration or the distance never moves the state towards `"unaffected"` (order unaffected → degraded → lost). | as above | TC-0 |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-006-01 | `minephys.environment` imports only the standard library, NumPy, PyYAML and `minephys` modules (`math.erf` vectorised with NumPy; no SciPy; foundation NFR-000-05). | 0 other top-level modules imported | contract test (subprocess import audit) |
| NFR-006-02 | Latency (foundation NFR-000-07): closed forms on scalars; `gaussian_plume` over a 1,000 × 1,000 receptor grid. | ≤ 1 ms median; ≤ 0.5 s median | `tools/bench.py` |
| NFR-006-03 | One worked-example oracle per function family runs in the Pyodide smoke subset (foundation FR-000-25). | 100 % pass | Pyodide job |
| NFR-006-04 | Every public function's docstring is a model card (foundation FR-000-09), including the unit conversions and the validity ranges. | 100 % of `__all__` | foundation model-card audit |
| SC-006-01 | AP-42's printed numbers reproduce: the controlled emission factors of Table 13.2.2-5 (7.1 lb/VMT at 0, 62, 68, 74, 80 % → 7.1, 2.7, 2.3, 1.8, 1.4), the 2.4-ton fleet-mean example and the 281.9 g/VKT conversion. | each within TC-2 | unit tests |
| SC-006-02 | Mutation score on `minephys.environment`. | ≥ 0.80 (`mutation.numerical_core_min`) | mutation run |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-006-01 | `src/minephys/knowledge/environment.yaml` (rows of §7) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.environment`, knowledge export, docs generator, PitStudio knowledge pages |
| DC-006-02 | environment entries of `src/minephys/knowledge/catalogue/equations.yaml` | `contracts/knowledge-equations.schema.json` (spec 008 DC-008-01) | this spec → knowledge export → PitStudio equation explorer |

## 7. Edge cases and assumptions

**Knowledge rows** (`knowledge/environment.yaml`, foundation DC-000-02). All values were read on the cited document
on 2026-10-06; each verified row is pinned by a `@pytest.mark.knowledge` test (foundation FR-000-21). Published tables
with several coefficients become one row per coefficient, with the id patterns shown.

| Row id (pattern) | Value | Units as published | Role | Citation · page | Status |
|---|---|---|---|---|---|
| `ap42_industrial_k_{pm25,pm10,pm30}` | 0.15, 1.5, 4.9 | lb/VMT | model_constant | `epa2006ap42s1322` · Table 13.2.2-2, p. 13.2.2-5 | verified (2026-10-06) |
| `ap42_industrial_a_{pm25,pm10,pm30}` | 0.9, 0.9, 0.7 | 1 | model_constant | same | verified (2026-10-06) |
| `ap42_industrial_b_{pm25,pm10,pm30}` | 0.45 | 1 | model_constant | same | verified (2026-10-06) |
| `ap42_silt_reference`, `ap42_weight_reference` | 12, 3 | %, short tons | model_constant | eq. 1a, p. 13.2.2-4 | verified (2026-10-06) |
| `ap42_range_silt` | range 1.8–25.2 | % | limit | Table 13.2.2-3, p. 13.2.2-5 | verified (2026-10-06) |
| `ap42_range_weight` | range 2–290 (1.8–260 Mg) | short tons | limit | same | verified (2026-10-06) |
| `ap42_range_speed` | range 5–43 (8–69 km/h) | mph | limit | same | verified (2026-10-06) |
| `ap42_range_wheels` | range 4–17 | 1 | limit | same | verified (2026-10-06) |
| `ap42_range_moisture` | range 0.03–13 | % | limit | same | verified (2026-10-06) |
| `ap42_lb_per_vmt_in_g_per_vkt` | 281.9 | g/VKT | conversion | p. 13.2.2-4 | verified (2026-10-06) |
| `ap42_wet_day_threshold` | 0.254 | mm | model_constant | eq. 2, p. 13.2.2-7 | verified (2026-10-06) |
| `ap42_days_per_year` | 365 | d | model_constant | eq. 2, p. 13.2.2-7 | verified (2026-10-06) |
| `ap42_watering_m_{1,2,3,4}`, `ap42_watering_ce_{1,2,3,4}` | $M$ = 0, 1, 2, 5; CE = 0, 0, 75, 95 | 1, % | model_constant | Figure 13.2.2-2, p. 13.2.2-12 | verified (2026-10-06) |
| `isc3_sigma_y_scale`, `isc3_deg_to_rad` | 465.11628, 0.017453293 | m/km, rad/deg | model_constant | `epa1995isc3v2` · eqs. 1-32, 1-33, p. 1-14 | verified (2026-10-06) |
| `isc3_pg_sigma_y_{c,d}_{a..f}` | 12 coefficients (Table 1-1) | deg | model_constant | Table 1-1, p. 1-16 | verified (2026-10-06) |
| `isc3_pg_sigma_z_{a..f}_{k}_{xmax,a,b}` | per class and distance band (Table 1-2: 9, 3, 1, 6, 9 and 10 bands for A to F) | km, m, 1 | model_constant | Table 1-2, pp. 1-17, 1-18 | verified (2026-10-06) |
| `isc3_sigma_z_cap` | 5,000 | m | limit | Table 1-2 footnotes, p. 1-17 | verified (2026-10-06) |
| `isc3_briggs_urban_{y,z}_{a..f}_{coef,slope,exponent}` | Tables 1-3 and 1-4 coefficients | m, 1/m, 1 | model_constant | Tables 1-3, 1-4, p. 1-19 | verified (2026-10-06) |
| `isc3_urban_min_distance` | 100 | m | limit | p. 1-15 | verified (2026-10-06) |
| `isc3_lid_uniform_ratio` | 1.6 | 1 | model_constant | eq. 1-51, p. 1-33 | verified (2026-10-06) |
| `lidar_dust_onset_transmittance` | range 0.71–0.74 | 1 | limit | `phillips2017dust` · abstract | verified (2026-10-06) |
| `lidar_dust_min_transmittance_retroreflective` | 0.02 | 1 | limit | same | verified (2026-10-06) |
| `lidar_dust_min_transmittance_low_reflectivity` | 0.06 | 1 | limit | same | verified (2026-10-06) |
| `extinction_efficiency_large_particle` | 2 | 1 | model_constant | `bohren1983absorption` · page not read | UNVERIFIED (warns on use, spec 008 FR-008-12) |

The pound, mile, short ton and mile-per-hour definitions are rows of the foundation `units` table.

**How the UNVERIFIED items of the docs were pinned during specification**

- AP-42 constants and ranges: read on the primary PDF (November 2006), Tables 13.2.2-2 and 13.2.2-3, p. 13.2.2-5.
- Watering control-efficiency curve: read on the primary PDF (p. 13.2.2-12). Its vertices were taken from the figure's
  vector path in the PDF, which gives (0, 0), (1, 0), (2, 75.0 %) and (5, 94.99 %); the text calls it a simple bilinear
  relation (p. 13.2.2-11) and the axis ends at $M$ = 5. The value 95 % is used.
- Dispersion coefficients: pinned to the EPA ISC3 user's guide, volume II (EPA-454/B-95-003b), Tables 1-1 to 1-4,
  which fit the Pasquill–Gifford curves (rural) and give Briggs' formulas (urban); the Gaussian plume and its vertical
  term follow its eqs. 1-1, 1-50 and 1-51. The original curves (Turner's workbook) were not read and are cited
  bibliographically.
- Lidar thresholds: read on the publisher-deposited abstract of the mining-dust study ("dust starts to affect
  measurements when the atmospheric transmittance is less than 71 %–74 %, but this is quite variable with
  conditions"; "transmittance as low as 2 % if the target is retroreflective and 6 % if it is of low reflectivity").

**Assumptions and edge cases**

- Large haul trucks give fleet-mean weights at or above 290 short tons. The factor is still returned with a
  `ValidityWarning` (the regression extrapolates); `ap42_unpaved_validity` gives the same flags as arrays for
  vectorised use, and consumers must show them. AP-42 downgrades the rating by two letters when default silt values are
  used and by one letter for the precipitation correction; the model cards say so.
- The weight range is checked in short tons (2–290); the metric column (1.8–260 Mg) is the source's rounding and is
  kept in the row notes for display.
- Equation 1a is not valid for chemically stabilised roads; the functions cannot detect that, and the model card
  states it.
- The watering curve is defined only for $0 \le M \le 5$; beyond 5 the source gives no value, so the function rejects
  it rather than extrapolating.
- The study's "atmospheric transmittance" is interpreted as the **one-way** transmittance of the sensor-to-target path;
  the abstract does not state it and the full text was not read (**UNVERIFIED interpretation**). The thresholds are
  applied to $T$, not $T^2$; both are returned.
- The extinction efficiency $Q_{ext} \to 2$ for particles much larger than the wavelength is the large-particle limit
  (**UNVERIFIED** page); it is a model constant, not a site parameter, and warns when used as the default. Its tests do
  not depend on its value ($k_m$ is checked for any given $Q_{ext}$, P-006-11).
- ISC3 distance bands are printed with two decimals ("< 0.10", "0.10–0.15", …). This spec assigns each band the
  interval (previous upper bound, upper bound]; tests check that convention at the band edges and compare with the
  table away from them. ISC3 also drops the mixing-lid series for classes E and F; `gaussian_plume` takes $\sigma$ values
  directly, so that choice is the caller's (pass `mixing_height=None`).
- The infinite line source assumes the wind is perpendicular to the road and $\sigma_z$ evaluated at the receptor's
  distance from the road; roads at an angle are approximated by `finite_line_source_plume` segments.

**Bibliography keys used** (foundation DC-000-03): `epa2006ap42s1322` (US EPA (2006), AP-42 Fifth Edition, Vol. I,
§13.2.2 Unpaved Roads, https://www.epa.gov/sites/default/files/2020-10/documents/13.2.2_unpaved_roads.pdf; access
`regulation`), `epa1995isc3v2` (US EPA (1995), User's guide for the Industrial Source Complex (ISC3) dispersion
models, Vol. II, EPA-454/B-95-003b, https://gaftp.epa.gov/aqmg/SCRAM/models/other/isc3/isc3v2.pdf; `open`),
`turner1970workbook` (`bibliographic-only`), `phillips2017dust` (https://doi.org/10.1002/rob.21701; `paywalled`,
abstract read), `bohren1983absorption` (https://doi.org/10.1002/9783527618156; `paywalled`), `niosh2012dust`
(https://doi.org/10.26616/nioshpub2012112; `open`, control practice, model card only).

## 8. Clarifications log

- Resolved (UNVERIFIED pinned): the theory skeleton marks the AP-42 constants and ranges and the plume coefficients
  "UNVERIFIED — pinned at specification"; they are verified rows now (§7). The PitStudio pages already carry the
  verified AP-42 values; there is no contradiction in the values themselves.
- Resolved (UNVERIFIED pinned): the watering control-efficiency curve, "UNVERIFIED — pinned at specification" in the
  method page and "read from the figure" in the dust theory page, was confirmed on the primary PDF, including its 95 %
  end point at $M$ = 5.
- Resolved: "Pasquill–Gifford or Briggs" coefficients are pinned to one primary EPA source (ISC3 vol. II) for both
  terrains, instead of a secondary reproduction of Briggs' rural formulas.
- Resolved (foundation alignment): arguments are SI only (silt and moisture as fractions, weight in kg, speed in m/s),
  so no published-unit entry point is exposed (the suffix list of foundation A2 has no lb/VMT or short-ton suffix);
  tests evaluate the published-unit form themselves. Range violations warn with `ValidityWarning` (FR-000-16), with an
  opt-in `strict` error; errors are `InputError`; multi-coefficient tables are one row per coefficient (DC-000-02 has
  no tabular value).
- Resolved: the reference page's `pasquill_sigmas` takes a `terrain` argument; `beer_lambert_transmittance` and
  `lidar_dust_return` keep their planned names; the added names (`ap42_unpaved_validity`, `fleet_mean_vehicle_weight`,
  `watering_control_efficiency`, `controlled_emission_factor`, `line_emission_rate`, `finite_line_source_plume`,
  `mass_extinction_coefficient`, `extinction_coefficient`, `path_transmittance`) are added in the build phase.
- Resolved: Lagrangian particles, Stokes settling and the camera haze model belong to PitStudio (studio physics and
  sensors); this module covers the closed forms only.

## 9. Changes (only for features that modify earlier behaviour)
### ADDED Requirements
(none — new module)
### MODIFIED Requirements
(none)
### REMOVED Requirements
(none)
