# Spec 002 — Blasting models (`minephys.blasting`)
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent
A blast design trades explosive cost against fragmentation, ground vibration and flyrock, and fragmentation starts the
mine-to-mill chain. The consumers (PitStudio's blast case, its synthetic muck piles with exact size distributions, its
segmentation baseline and its browser ports) need one sourced, tested implementation of the classical prediction
equations. This module provides charge and powder factor, the Kuz-Ram model (Kuznetsov mean size with the 1983/1987
explosive-strength exponent 19/30 by default and Cunningham's 2005 exponent 19/20 as a named option, Cunningham's
uniformity index and rock factor), the Rosin–Rammler and Swebrec size distributions and the KCO link between them,
square-root scaled-distance peak particle velocity with the 30 CFR § 816.67 limits, and flyrock range (drag-free
bound, Lundborg's empirical maximum and a drag-inclusive ballistic trajectory).
**Out of scope:** Cunningham's 2005 timing and blastability modifiers (A_T, C(A), C(n)), crush-zone and xP-frag fines
models, frequency-dependent vibration criteria (USBM RI 8507 curves), airblast, launch-velocity prediction, rock
fracture simulation and default site constants (`K`, `β`, rock factor ratings).

## 2. User stories

| ID | Story | Priority | Independent test |
|---|---|---|---|
| US-002-1 | As a blasting engineer or student, I want x50, the uniformity index and the passing curve of a blast design, so that I can see oversize and fines and compare the Kuz-Ram versions. | P1 | worked example 1 of §7.4: x50 = 0.29941 m (19/30) and 0.31296 m (19/20) |
| US-002-2 | As a simulation developer, I want Swebrec and Rosin–Rammler distributions with closed-form percentiles, so that synthetic muck piles have exact size distributions. | P1 | the percentiles of §7.4 and the median identity P(x50) = 0.5 |
| US-002-3 | As a mining engineer, I want PPV from my site law and the 30 CFR § 816.67 limits and maximum charge per delay in SI units, so that I can check a design against the regulation. | P1 | 1,000 ft gives 330.58 lb = 149.948 kg per 8 ms period |
| US-002-4 | As a safety engineer, I want drag-free, empirical and drag-inclusive flyrock ranges, so that I can bound an exclusion zone and see what drag does. | P2 | the analytical limits of §7.4 (vacuum range 163.155 m; vertical apex with drag 72.500 m) |

## 3. Functional requirements (EARS)

SI units at the API (constitution principle 7): sizes and lengths in m, masses in kg, densities in kg/m³, velocities in
m/s, angles in rad. Sources published in cm, mm, inches, feet, pounds or in/s are converted at the boundary.
Signatures in §7.1.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-002-01 | Ubiquitous | `charge_per_hole(explosive_density, hole_diameter, charge_length)` shall return `ρ_e·(π/4)·d²·L_c` in kg, and `powder_factor(charge, burden, spacing, bench_height)` shall return `Q/(B·S·H)` in kg/m³. | unit |
| FR-002-02 | Ubiquitous | `kuznetsov_x50(rock_factor, powder_factor, charge, rws, variant="cunningham1983")` shall return `x50 = A·K^{−0.8}·Q^{1/6}·(115/RWS)^e` converted from cm to m, with `e = 19/30` for `variant="cunningham1983"` (default) and `e = 19/20` for `variant="cunningham2005"` (Cunningham 2005, eq. 1, p. 201), and with 115 the weight strength of TNT relative to ANFO = 100. | unit |
| FR-002-03 | Ubiquitous | `rock_factor(rmd, rdi, hf)` shall return `A = 0.06·(RMD + RDI + HF)` (Cunningham 2005, eq. 4, p. 204); `hardness_factor(youngs_modulus, ucs)` shall return `E/3` (E in GPa) when E < 50 GPa and `UCS/5` (UCS in MPa) otherwise (p. 205), taking both in Pa; and `rock_density_influence(density)` shall return `0.025·ρ − 50` with ρ in kg/m³. | unit |
| FR-002-04 | Ubiquitous | `uniformity_index(burden, spacing, hole_diameter, drilling_deviation, charge_length, bench_height, bottom_charge_length=None, column_charge_length=None)` shall return `n = (2.2 − 14B/d)·√((1 + S/B)/2)·(1 − W/B)·(\|BCL − CCL\|/L + 0.1)^{0.1}·L/H` with B, S, W, L, BCL, CCL, H in m and d converted to mm (Cunningham 2005, eq. 3, p. 202, the 1987 form), taking `BCL = L` and `CCL = 0` for a single-explosive column when both are `None`. | unit |
| FR-002-05 | Ubiquitous | `rosin_rammler_passing(size, x50, n)` shall return `P = 1 − exp(−ln 2·(x/x50)^n)` and `rosin_rammler_size(passing, x50, n)` shall return `x50·(ln(1/(1−P))/ln 2)^{1/n}`. | unit |
| FR-002-06 | Ubiquitous | `swebrec_passing(size, x50, xmax, b)` shall return `P = 1/(1 + [ln(xmax/x)/ln(xmax/x50)]^b)` for 0 < x < xmax and 1 for x ≥ xmax, and `swebrec_size(passing, x50, xmax, b)` shall return `xmax·(x50/xmax)^{((1−P)/P)^{1/b}}` for 0 < P < 1. | unit |
| FR-002-07 | Ubiquitous | `kco_undulation(n, x50, xmax)` shall return `b = 2·ln 2·ln(xmax/x50)·n`, and `kco_distribution(size, x50, xmax, n)` shall return `swebrec_passing(size, x50, xmax, kco_undulation(n, x50, xmax))`. | unit |
| FR-002-08 | Ubiquitous | `scaled_distance(distance, charge_per_delay)` shall return `D/√W` in m/kg^½, and `ppv_scaled_distance(distance, charge_per_delay, k_site, beta)` shall return `K·(D/√W)^{−β}` in m/s with `k_site` the PPV in m/s at a scaled distance of 1 m/kg^½ and no default for `k_site` or `beta`. | unit |
| FR-002-09 | Ubiquitous | `ppv_limit(distance, standard="30cfr816.67")` shall return the maximum PPV of 30 CFR § 816.67(d)(2)(i) converted to m/s (1.25, 1.00 and 0.75 in/s for D ≤ 300 ft, 300 ft < D ≤ 5,000 ft and D > 5,000 ft), and `max_charge_per_delay(distance, standard="30cfr816.67")` shall return `W = (D/D_s)²` of § 816.67(d)(3)(i) (W in lb per 8-millisecond period, D in ft, D_s = 50, 55, 65 in the same bands) converted to kg. | unit |
| FR-002-10 | Ubiquitous | `flyrock_range_no_drag(launch_speed, launch_angle, g=g₀)` shall return `v₀²·sin(2θ₀)/g` in m (launch and landing at the same level). | unit |
| FR-002-11 | Ubiquitous | `flyrock_range_lundborg(hole_diameter)` shall return Lundborg's empirical maximum throw `260·d^{2/3}` in m with d converted from m to inches. | unit |
| FR-002-12 | Ubiquitous | `flyrock_trajectory(launch_speed, launch_angle, diameter, rock_density, drag_coefficient, air_density, launch_height=0, time_step=1e-3, max_time=600, g=g₀)` shall integrate `m·dv/dt = −m·g·ẑ − ½·ρ_a·C_D·A·\|v\|·v` for a sphere (`m = ρ_r·πD³/6`, `A = πD²/4`) by fixed-step fourth-order Runge–Kutta from height `launch_height` until it reaches z = 0, locate the landing point by cubic Hermite interpolation on the last step, and return the arrays `t`, `x`, `z`, `vx`, `vz` with `range`, `flight_time` and `apex_height`. | unit |
| FR-002-13 | Unwanted | If the trajectory has not landed by `max_time`, or `max_time/time_step` exceeds 10⁶ steps, then `flyrock_trajectory` shall raise `InputError` naming `max_time` or `time_step`. | hostile |
| FR-002-14 | Unwanted | If the uniformity formula's factors leave the domain (`14B/d ≥ 2.2`, `W ≥ B`, or `BCL + CCL > L` when both are given), then `uniformity_index` shall raise `InputError` naming the argument. | hostile |
| FR-002-15 | Unwanted | If `x50 ≥ xmax` in a Swebrec or KCO function, or `passing` is outside (0, 1) in an inverse function, then the function shall raise `InputError` naming the argument. | hostile |
| FR-002-16 | Unwanted | If any argument violates its physical domain in Table 7.2, then the function shall raise `InputError` naming that argument (foundation FR-000-14). | hostile |
| FR-002-17 | Unwanted | If an input lies outside a validity range of Table 7.3 (the rock factor outside Cunningham's 0.8–22, a uniformity index outside the typical 0.8–1.5) or trips a unit tripwire of Table 7.3, then the function shall emit `ValidityWarning` naming the argument and the row and still return the result (foundation FR-000-16). | unit |
| FR-002-18 | Unwanted | If `variant` is not `"cunningham1983"` or `"cunningham2005"`, or `standard` is not `"30cfr816.67"`, then the function shall raise `InputError` listing the allowed values (foundation FR-000-15). | hostile |

## 4. Correctness properties

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-002-01 | `kuznetsov_x50` is strictly decreasing in powder factor and in RWS, linear in the rock factor, and multiplies by 2 when the charge multiplies by 64 (metamorphic: monotonicity, scaling). | A ∈ [0.8, 22], K ∈ [0.1, 3] kg/m³, Q ∈ [1, 3,000] kg, RWS ∈ [50, 200] | TC-1; exact ordering |
| P-002-02 | The two variants agree exactly at RWS = 115, and their ratio is `(115/RWS)^{19/20 − 19/30}` for every other RWS (metamorphic: identity, ratio invariance). | as P-002-01 | TC-1 |
| P-002-03 | `uniformity_index` is unchanged when every length (B, S, d, W, L, BCL, CCL, H) is scaled by the same factor, strictly decreasing in drilling deviation and in B/d, and linear in L/H with all ratios fixed (metamorphic: unit-change invariance, monotonicity). | B ∈ [1, 12] m, d ∈ [0.05, 0.4] m, S/B ∈ [1, 1.5], W/B ∈ [0, 0.2], L/H ∈ [0.3, 1] | TC-1 |
| P-002-04 | Every passing function is non-decreasing in size, equals 0.5 at x50, equals 1 at and beyond xmax (Swebrec), and its inverse round-trips (`size(passing(x)) = x`) (metamorphic: monotonicity, identity, round trip). | x ∈ (0, xmax), n, b ∈ [0.5, 4] | TC-1 |
| P-002-05 | Scaling size, x50 and xmax by the same λ leaves every passing value unchanged (metamorphic: unit-change invariance m ↔ cm ↔ mm). | λ ∈ [1e-3, 1e3] | TC-1 |
| P-002-06 | With b from `kco_undulation`, the Swebrec and Rosin–Rammler curves have the same value (0.5) and the same slope `dP/d ln x` at x50 (analytical derivation of the KCO link, independent of the published relation). | x50/xmax ∈ [0.01, 0.8], n ∈ [0.5, 2] | TC-1 (central difference with step 1e-6, rtol 1e-6) |
| P-002-07 | `ppv_scaled_distance` is unchanged when D → λD and W → λ²W, strictly decreasing in D, strictly increasing in W, and gives the same PPV when D, W and K are expressed in ft, lb and in/s with `K_SI = 0.0254·K_imp·c^{−β}`, `c = √0.45359237/0.3048` (metamorphic: square-root scaling, monotonicity, unit-change invariance). | D ∈ [10, 1e4] m, W ∈ [1, 5e3] kg, β ∈ [1, 2.5] | TC-1 |
| P-002-08 | `ppv_limit` is non-increasing and `max_charge_per_delay` non-decreasing in distance (metamorphic: monotonicity). | D ∈ (0, 1e4] m | exact ordering |
| P-002-09 | `flyrock_range_no_drag` is symmetric about 45° (`R(θ) = R(π/2 − θ)`), scales as v₀² and as 1/g (metamorphic: symmetry, scaling). | v₀ ∈ [1, 300] m/s, θ ∈ (0, π/2) | TC-1 |
| P-002-10 | `flyrock_trajectory` with `drag_coefficient = 0` reproduces the vacuum parabola (range and apex); with drag its range is below the vacuum range and strictly increasing in fragment diameter at fixed density; its vertical launch (θ = π/2) reaches the closed-form apex `(v_t²/2g)·ln(1 + v₀²/v_t²)` at `t = (v_t/g)·atan(v₀/v_t)`, `v_t² = 2mg/(ρ_a C_D A)` (analytical limits; metamorphic: ordering, monotonicity). | v₀ ∈ [5, 250] m/s, D ∈ [0.02, 1] m, C_D ∈ [0, 1.8] | TC-1 (no drag), TC-5 (drag), exact ordering |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-002-01 | `flyrock_trajectory` at the reference case (v₀ = 40 m/s, 45°, D = 0.1 m, default step) | ≤ 50 ms median (foundation NFR-000-07) | `tools/bench.py` |
| NFR-002-02 | Every other function of this module on scalar inputs | ≤ 1 ms median | `tools/bench.py` |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-002-01 | `src/minephys/knowledge/blasting.yaml` (rows of §7.5) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.blasting`, docs generator, PitStudio knowledge pages |

## 7. Edge cases and assumptions

### 7.1 Signatures

| Function | Arguments [units] | Returns [units] | Shape |
|---|---|---|---|
| `charge_per_hole` | explosive_density [kg/m³], hole_diameter [m], charge_length [m] | [kg] | elementwise |
| `powder_factor` | charge [kg], burden, spacing, bench_height [m] | [kg/m³] | elementwise |
| `kuznetsov_x50` | rock_factor [1], powder_factor [kg/m³], charge [kg], rws [1, ANFO = 100], variant | [m] | elementwise |
| `rock_factor` | rmd, rdi, hf [1] | [1] | elementwise |
| `hardness_factor` | youngs_modulus [Pa], ucs [Pa] | [1] | elementwise |
| `rock_density_influence` | density [kg/m³] | [1] | elementwise |
| `uniformity_index` | burden, spacing, hole_diameter, drilling_deviation, charge_length, bench_height, bottom_charge_length, column_charge_length [m] | [1] | elementwise |
| `rosin_rammler_passing`, `swebrec_passing`, `kco_distribution` | size, x50, xmax [m], n, b [1] | [1] | elementwise |
| `rosin_rammler_size`, `swebrec_size` | passing [1], x50, xmax [m], n, b [1] | [m] | elementwise |
| `kco_undulation` | n [1], x50, xmax [m] | [1] | elementwise |
| `scaled_distance` | distance [m], charge_per_delay [kg] | [m/kg^½] | elementwise |
| `ppv_scaled_distance` | distance [m], charge_per_delay [kg], k_site [m/s], beta [1] | [m/s] | elementwise |
| `ppv_limit`, `max_charge_per_delay` | distance [m], standard | [m/s], [kg] | elementwise |
| `flyrock_range_no_drag` | launch_speed [m/s], launch_angle [rad], g [m/s²] | [m] | elementwise |
| `flyrock_range_lundborg` | hole_diameter [m] | [m] | elementwise |
| `flyrock_trajectory` | launch_speed [m/s], launch_angle [rad], diameter [m], rock_density [kg/m³], drag_coefficient [1], air_density [kg/m³], launch_height [m], time_step [s], max_time [s], g [m/s²] | named result (arrays [s], [m], [m/s]; range [m], flight_time [s], apex_height [m]) | scalar inputs only |

### 7.2 Physical domain (violations raise `InputError`, FR-002-16)

| Argument | Domain |
|---|---|
| explosive_density, hole_diameter, charge_length, charge, burden, spacing, bench_height, powder_factor, rock_factor, rws, youngs_modulus, ucs, density, size, x50, xmax, n, b, distance, charge_per_delay, k_site, beta, launch_speed, diameter, rock_density, time_step, max_time, g | > 0 |
| rmd, rdi, hf | finite (ratings; `rdi` may be negative for light rock) |
| drilling_deviation, drag_coefficient, air_density, launch_height | ≥ 0 |
| bottom_charge_length, column_charge_length | ≥ 0, both given or both `None` |
| passing (inverse functions) | 0 < P < 1 |
| launch_angle | −π/2 ≤ θ ≤ π/2 (`flyrock_range_no_drag`: 0 ≤ θ ≤ π/2) |
| `time_step` | ≤ 0.1 s |

### 7.3 Validity ranges and unit tripwires (warn, FR-002-17)

| Row | Argument | Warns when | Basis |
|---|---|---|---|
| `kuzram_rock_factor_min`, `kuzram_rock_factor_max` | rock_factor | A < 0.8 or A > 22 | Cunningham 2005, p. 201 ("varying between 0.8 and 22") — verified |
| `kuzram_uniformity_typical_min`, `kuzram_uniformity_typical_max` | result of `uniformity_index` | n < 0.8 or n > 1.5 | typical range associated with the formula — UNVERIFIED |
| `tripwire_powder_factor_max` | powder_factor | > 5 kg/m³ | unit tripwire (g/m³ or kg/t slips) |
| `tripwire_rws_min` | rws | < 20 | unit tripwire (RWS as a fraction, ANFO = 1) |
| `tripwire_hole_diameter_max` | hole_diameter | > 1 m | unit tripwire (mm passed as m) |
| `tripwire_k_site_max` | k_site | > 100 m/s | unit tripwire (mm/s passed as m/s) |
| `tripwire_launch_speed_max` | launch_speed | > 500 m/s | unit tripwire (km/h) |
| `tripwire_air_density_max` | air_density | > 2 kg/m³ | unit tripwire |

Tripwire rows are design choices of this spec, not sourced limits (role `limit`, UNVERIFIED).

### 7.4 Worked values

Worked example 1 (illustrative design consistent with the theory page: ρ_e = 850 kg/m³, d = 0.25 m, L_c = 7.2 m,
B = 6 m, S = 7 m, H = 12 m, A = 7, RWS = 100, W = 0.3 m, single column, xmax = 1.5 m; spec writer's hand calculation):

| Quantity | Value |
|---|---|
| `charge_per_hole` | 300.41480 kg |
| `powder_factor` | 0.59606111 kg/m³ |
| `kuznetsov_x50` (default, 19/30) | 0.29940630 m |
| `kuznetsov_x50(variant="cunningham2005")` (19/20) | 0.31295501 m (ratio 1.0452519) |
| `uniformity_index` | 1.1164546 |
| `kco_undulation(1.1164546, 0.29940630, 1.5)` | 2.4940490 |
| x80: Swebrec / Rosin–Rammler | 0.59521759 m / 0.63672061 m |
| passing > 1 m (oversize): Swebrec / Rosin–Rammler | 3.1027 % / 6.9660 % |
| passing < 0.05 m (fines): Swebrec / Rosin–Rammler | 13.434 % / 8.9695 % |

Other values:

| Case | Value |
|---|---|
| `rock_factor(50, rock_density_influence(2700), hardness_factor(30e9, 150e6))` | RDI = 17.5, HF = 10, A = 4.65 |
| `hardness_factor(60e9, 150e6)` | 30 (UCS/5 branch) |
| `scaled_distance(300, 150)`; `ppv_scaled_distance(300, 150, 1.0, 1.6)` | 24.494897 m/kg^½; 5.9907197 × 10⁻³ m/s |
| `ppv_limit(304.8)` (1,000 ft) | 0.0254 m/s; at 50 m: 0.03175 m/s; at 2,000 m: 0.01905 m/s |
| `max_charge_per_delay(304.8)` | (1000/55)² = 330.57851 lb = 149.94789 kg |
| `flyrock_range_no_drag(40, π/4)` | 163.15459 m |
| `flyrock_range_lundborg(0.127)` (5-inch hole) | 760.24461 m; Szendrei and Tose 2022, p. 729, report "very close to 760 m" for this hole size |
| `flyrock_trajectory(40, π/2, 0.1, 2650, 0.47, 1.2)` | apex 72.500448 m at t = 3.7715338 s (closed form; vacuum apex 81.577297 m) |
| `flyrock_trajectory(40, π/4, D, 2650, 0, 1.2)` | range 163.15459 m for any D (no drag) |

### 7.5 Knowledge rows (DC-002-01)

| Row id | Value | Units | Role | Citation, page | Verification |
|---|---|---|---|---|---|
| `kuznetsov_powder_factor_exponent` | −0.8 | 1 | model_constant | Cunningham 2005, eq. 1, p. 201 | verified (2026-10-06) |
| `kuznetsov_charge_exponent` | "1/6" | 1 | model_constant | same | verified |
| `kuznetsov_tnt_relative_weight_strength` | 115 | 1 (ANFO = 100) | model_constant | same ("115 being the RWS of TNT") | verified |
| `kuzram_rws_exponent_2005` | "19/20" | 1 | model_constant | same | verified |
| `kuzram_rws_exponent_1983` | "19/30" | 1 | model_constant | Cunningham 1983/1987 (primary not read); printed in Mutinda et al. 2021, eq. 2, p. 109 | UNVERIFIED (secondary only) |
| `kuzram_rock_factor_coefficient` | 0.06 | 1 | model_constant | Cunningham 2005, eq. 4, p. 204 | verified |
| `kuzram_hardness_modulus_divisor`, `kuzram_hardness_ucs_divisor`, `kuzram_hardness_modulus_switch` | 3, 5, 50 | 1, 1, GPa | model_constant | Cunningham 2005, p. 205 | verified |
| `kuzram_rdi_density_coefficient`, `kuzram_rdi_offset` | 0.025, 50 | 1/(kg/m³), 1 | model_constant | Cunningham 1987 (primary not read); Mutinda et al. 2021, eq. 5, p. 109 | UNVERIFIED (secondary only) |
| `cunningham_n_constant`, `cunningham_n_burden_coefficient`, `cunningham_n_charge_offset`, `cunningham_n_charge_exponent` | 2.2, 14, 0.1, 0.1 | 1 | model_constant | Cunningham 2005, eq. 3, p. 202 (the 1987 form) | verified |
| `rosin_rammler_median_constant` | 0.693 | 1 | model_constant | Cunningham 2005, eq. 2, p. 202 | verified (implemented as ln 2; see §8) |
| `kuzram_rock_factor_min`, `kuzram_rock_factor_max` | 0.8, 22 | 1 | limit | Cunningham 2005, p. 201 | verified |
| `kuzram_uniformity_typical_min`, `kuzram_uniformity_typical_max` | 0.8, 1.5 | 1 | limit | literature range quoted with the formula | UNVERIFIED |
| `cfr_816_67_ppv_limit_near`, `_mid`, `_far` | 1.25, 1.00, 0.75 | in/s | limit | 30 CFR § 816.67(d)(2)(i) | verified |
| `cfr_816_67_distance_band_near_max`, `_mid_max` | 300, 5000 | ft | limit | same | verified |
| `cfr_816_67_scaled_distance_factor_near`, `_mid`, `_far` | 50, 55, 65 | ft/lb^½ | limit | same, (d)(2)(i) and (d)(3)(i) | verified |
| `lundborg_max_range_coefficient`, `lundborg_max_range_exponent` | 260, "2/3" | m/in^{2/3}, 1 | model_constant | Lundborg (primary not read); Szendrei and Tose 2022, eq. 1, p. 726 | UNVERIFIED (secondary only) |
| `flyrock_drag_coefficient_range` | 0.6–1.8 | 1 | parameter | Szendrei and Tose 2022, p. 728 | verified (not a default) |
| `flyrock_air_density_reference` | 1.24 | kg/m³ | parameter | same, p. 728 | verified (not a default) |
| `tripwire_*` (Table 7.3) | as listed | as listed | limit | this specification, §7.3 | UNVERIFIED (design choice) |

The centimetre, millimetre, inch, foot and pound definitions are rows of the foundation `units` table. The Swebrec form and the KCO relation
`b = 2 ln 2 ln(xmax/x50) n` are read on Mutinda et al. 2021 (eqs. 1 and 6, p. 109); the primary (Ouchterlony 2005) is
paywalled; neither carries a constant other than ln 2, and P-002-06 derives the KCO relation independently.

### 7.6 Assumptions
- Kuznetsov's x50 is used as the median of the Rosin–Rammler curve, as in Cunningham's practice; Cunningham 2005
  (p. 209) notes that Kuznetsov's mean is strictly not the Rosin–Rammler median.
- The powder factor divides by the bench volume B·S·H (subdrill excluded); callers using another convention say so.
- The rock-factor ratings (RMD from the rock-mass description; joint ratings inside RMD) are inputs; the lookup tables
  are not implemented.
- PPV site constants come from the user's own regression; none is shipped.
- Flyrock fragments are spheres with constant drag coefficient, no lift, spin or tumbling, over flat ground at z = 0;
  the launch velocity is an input (no model predicts it reliably).
- Functions that read an UNVERIFIED `model_constant` row emit `minephys.knowledge.UnverifiedParameterWarning` on use
  (008-knowledge FR-008-12): `kuznetsov_x50` with the default variant (`kuzram_rws_exponent_1983`),
  `rock_density_influence` and `flyrock_range_lundborg`. Their tests expect the warning.

## 8. Clarifications log
- **Resolved — exponent variants.** Default `cunningham1983` uses 19/30 (the 1983/1987 form named by the plan and the
  theory page); `cunningham2005` uses 19/20, verified on Cunningham 2005, eq. 1, p. 201. The 19/30 exponent is printed
  by Mutinda et al. 2021 (eq. 2, p. 109), who attribute it to Cunningham 2005 although Cunningham 2005 prints 19/20; the
  1983/1987 primary was not read, so `kuzram_rws_exponent_1983` stays UNVERIFIED. Its role is `model_constant` (part of
  a named equation variant), so the default does not breach foundation FR-000-22, and every model card states the
  status.
- **Resolved — rock factor.** The theory page writes `A = 0.06(RMD + JF + RDI + HF)`; Cunningham 2005 (eq. 4, p. 204)
  and Mutinda et al. 2021 (eq. 3) write `A = 0.06(RMD + RDI + HF)`, with the joint factor JF entering through RMD.
  The library follows the primary source.
- **Resolved — uniformity index.** The 1987 transcription, with B, S, W, L, H in m and d in mm, is verified on
  Cunningham 2005, eq. 3, p. 202.
- **Resolved — ln 2 versus 0.693.** Cunningham prints 0.693; the library uses ln 2 (relative difference 2.1 × 10⁻⁴)
  so that x50 is exactly the median, as the theory page states.
- **Resolved — CFR distance bands.** The regulation lists 0–300 ft, 301–5,000 ft and 5,001 ft and beyond; for
  non-integer distances the bands are D ≤ 300 ft, 300 < D ≤ 5,000 ft and D > 5,000 ft. The charge limit applies to any
  8-millisecond period, as printed.
- **Resolved — flyrock source year.** Szendrei and Tose appeared in J. S. Afr. Inst. Min. Metall. 122(12), December
  2022 (DOI 10.17159/2411-9717/1873/2022); the docs cite it as 2023.
- **Resolved — Lundborg.** The theory page leaves Lundborg's correlation untranscribed; this spec adds it as an
  UNVERIFIED secondary transcription with the published 5-inch value as its oracle.
- **Resolved — user stories as table rows.** Stories are table rows so that `tools/trace.py` defines their IDs.
