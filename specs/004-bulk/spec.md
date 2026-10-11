# Spec 004 — Bulk-handling models (`minephys.bulk`)
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent
Every tonne mined is dumped, stockpiled, fed through openings, carried on belts and sampled. The consumers need small,
sourced closed forms for these steps: the live browser figures (stockpile volume, discharge, belt capacity and power,
blending and sampling variance) and the analytical benchmarks that a GPU granular simulation must reproduce (Beverloo
discharge scaling, repose geometry). This module provides Beverloo's discharge law, cone and ridge stockpile geometry
at the angle of repose, belt-conveyor capacity, the public form of the CEMA effective-tension method and drive power,
Gy's fundamental sampling error and the bed-blending variance of a layered stockpile.
**Out of scope:** discrete-element or continuum granular simulation, chute design, the CEMA and ISO 5048 tables
(cross-section areas, idler and flexure factors are inputs), ISO 5048 and DIN 22101 power methods, start-up and
braking factors, sampling-protocol optimisation and default material factors.

## 2. User stories

| ID | Story | Priority | Independent test |
|---|---|---|---|
| US-004-1 | As a simulation developer, I want Beverloo's discharge law and repose-cone geometry, so that my GPU granular runs have analytical benchmarks. | P1 | the Beverloo values of §7.4 and the cone of 30 m radius at 37° |
| US-004-2 | As a mining engineer, I want belt capacity and the effective tension and power of a conveyor from my own factors, so that I can size a drive and check it against the lift-power floor. | P1 | the lift-floor identity: zero idler and flexure factors give power = ṁ·g·H |
| US-004-3 | As a geometallurgist or student, I want Gy's fundamental sampling error and the variance reduction of bed blending with correlated layers, so that I can reason about sampling and blending honestly. | P2 | ρ = 0.9 over 100 layers gives a variance reduction ratio of 5.81, not 100 |

## 3. Functional requirements (EARS)

SI units at the API (constitution principle 7); `g` defaults to g₀ = 9.80665 m/s² (foundation A1). Signatures in §7.1.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-004-01 | Ubiquitous | `beverloo_discharge(orifice_diameter, particle_diameter, bulk_density, discharge_coefficient, annulus_coefficient, g=g₀)` shall return the mass discharge rate `C·ρ_b·√g·(D − k·d)^{5/2}` in kg/s, with the exponent 5/2 read from row `beverloo_exponent` and no default for `C` or `k`. | unit |
| FR-004-02 | Unwanted | If `orifice_diameter ≤ annulus_coefficient·particle_diameter` (no free-flowing opening), then `beverloo_discharge` shall raise `InputError` naming `orifice_diameter`. | hostile |
| FR-004-03 | Ubiquitous | `repose_cone_height(base_radius, repose_angle)` shall return `r·tan φ` in m and `repose_cone_volume(base_radius, repose_angle)` shall return `(π/3)·r³·tan φ` in m³. | unit |
| FR-004-04 | Ubiquitous | `repose_ridge_volume(base_half_width, repose_angle, length, end_cones=False)` shall return `r²·tan φ·length` in m³, plus `(π/3)·r³·tan φ` (two half-cones) when `end_cones=True`. | unit |
| FR-004-05 | Ubiquitous | `conveyor_capacity(load_area, belt_speed, bulk_density)` shall return the mass flow `ρ_b·A·V` in kg/s. | unit |
| FR-004-06 | Ubiquitous | `cema_effective_tension(length, lift, belt_weight, material_weight, kt, kx, ky, pulley_tension=0, acceleration_tension=0, accessory_tension=0)` shall return `T_e = L·K_t·(K_x + K_y·W_b + 0.015·W_b) + W_m·(L·K_y + H) + T_p + T_am + T_ac` in N, with weights per length in N/m, `K_x` in N/m, `K_t` and `K_y` dimensionless and the 0.015 (return-belt term) read from row `cema_return_belt_coefficient`; `lift` may be negative (decline). | unit |
| FR-004-07 | Ubiquitous | `conveyor_power(effective_tension, belt_speed, drive_efficiency=1)` shall return `T_e·V/η` in W when `T_e ≥ 0` and `T_e·V·η` (≤ 0, regenerated power) when `T_e < 0`. | unit |
| FR-004-08 | Ubiquitous | `gy_fundamental_sampling_error(sample_mass, lot_mass, top_size, mineralogical_factor, shape_factor, granulometric_factor, liberation_factor)` shall return the relative variance `σ²_FSE = (1/M_S − 1/M_L)·c·f·g·ℓ·d³` (dimensionless), with masses in kg, `d` in m and `c` in kg/m³, and no default for any factor. | unit |
| FR-004-09 | Ubiquitous | `gy_blending_variance(input_variance, n_layers, lag1_correlation=0)` shall return `σ²_in/N·[1 + 2·Σ_{k=1}^{N−1}(1 − k/N)·ρᵏ]` (the variance of the mean of N layers whose grades follow a stationary first-order autoregressive series), evaluated in closed form so that N up to 10⁷ costs O(1), and `variance_reduction_ratio(n_layers, lag1_correlation=0)` shall return `σ²_in/σ²_out`. | unit |
| FR-004-10 | Unwanted | If any argument violates its physical domain in Table 7.2, then the function shall raise `InputError` naming that argument (foundation FR-000-14). | hostile |
| FR-004-11 | Unwanted | If any argument trips a unit tripwire in Table 7.3, then the function shall emit `ValidityWarning` naming the argument and the tripwire row and still return the result (foundation FR-000-16). | unit |
| FR-004-12 | Unwanted | If `sample_mass > lot_mass`, then `gy_fundamental_sampling_error` shall raise `InputError` naming `sample_mass`; if `n_layers` is not an integer in 1…10⁷ or `lag1_correlation` is outside (−1, 1), then the blending functions shall raise `InputError` naming the argument. | hostile |

## 4. Correctness properties

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-004-01 | Beverloo discharge is linear in bulk density and in C, scales as √g, and scales by λ^{5/2} when orifice and particle diameters both scale by λ (metamorphic: scaling, unit-change invariance m ↔ mm). | D ∈ [0.05, 2] m, d ∈ [1e-4, 0.05] m with D > k d, k ∈ [1, 3], λ ∈ [1e-3, 1e3] | TC-1 |
| P-004-02 | Beverloo discharge is strictly increasing in orifice diameter and strictly decreasing in particle diameter and in k (metamorphic: monotonicity). | as P-004-01 | exact ordering |
| P-004-03 | The cone volume equals one third of base area times height, scales as r³, and is strictly increasing in the repose angle; the ridge cross-section scales as r² and the ridge volume is linear in length (metamorphic: identity, scaling, monotonicity). | r ∈ [0.1, 500] m, φ ∈ (0.05, 1.5) rad | TC-1 |
| P-004-04 | Conveyor capacity is linear in each argument; `cema_effective_tension` is affine in length and strictly increasing in lift and in material weight (metamorphic: scaling, monotonicity). | L ∈ [1, 2e4] m, H ∈ [−500, 500] m | TC-1 / exact ordering |
| P-004-05 | With `kx = ky = 0`, no pulley, acceleration or accessory tension and `material_weight = ṁ·g/V`, `conveyor_power(cema_effective_tension(…), V)` equals the lift power `ṁ·g·H` (metamorphic: conservation). | ṁ ∈ [1, 3e3] kg/s, V ∈ [0.5, 8] m/s | TC-1 |
| P-004-06 | `cema_effective_tension` evaluated in imperial units (ft, lbf/ft, lbf) and converted gives the same tension as the SI call (metamorphic: unit-change invariance; the equation is dimensionally homogeneous). | as P-004-04 | TC-1 |
| P-004-07 | `gy_fundamental_sampling_error` is the same in SI and in Gy's cgs units (g, cm, g/cm³), scales as d³, is strictly decreasing in sample mass, is 0 when `sample_mass = lot_mass`, and tends to `c·f·g·ℓ·d³/M_S` as the lot mass grows (metamorphic: unit-change invariance, scaling, monotonicity, limit). | M_S ∈ [1e-3, 1e3] kg, M_L ≥ M_S, d ∈ [1e-5, 0.3] m | TC-1 |
| P-004-08 | `gy_blending_variance` equals `σ²_in/N` for ρ = 0, equals its explicit sum for N ≤ 1,000, is linear in `input_variance`, and the variance reduction ratio is non-decreasing in N for ρ ≥ 0 and strictly decreasing in ρ on (0, 1) for N ≥ 2 (metamorphic: identity, scaling, monotonicity). | N ∈ 1…10⁷, ρ ∈ (−0.99, 0.99) | TC-1 (sum identity rtol 1e-10 for N ≤ 1,000) |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-004-01 | Every function of this module on scalar inputs | ≤ 1 ms median (foundation NFR-000-07) | `tools/bench.py` |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-004-01 | `src/minephys/knowledge/bulk.yaml` (rows of §7.5) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.bulk`, docs generator, PitStudio knowledge pages |

## 7. Edge cases and assumptions

### 7.1 Signatures

| Function | Arguments [units] | Returns [units] | Shape |
|---|---|---|---|
| `beverloo_discharge` | orifice_diameter [m], particle_diameter [m], bulk_density [kg/m³], discharge_coefficient [1], annulus_coefficient [1], g [m/s²] | [kg/s] | elementwise |
| `repose_cone_height`, `repose_cone_volume` | base_radius [m], repose_angle [rad] | [m], [m³] | elementwise |
| `repose_ridge_volume` | base_half_width [m], repose_angle [rad], length [m], end_cones [bool] | [m³] | elementwise |
| `conveyor_capacity` | load_area [m²], belt_speed [m/s], bulk_density [kg/m³] | [kg/s] | elementwise |
| `cema_effective_tension` | length [m], lift [m], belt_weight [N/m], material_weight [N/m], kt [1], kx [N/m], ky [1], pulley_tension [N], acceleration_tension [N], accessory_tension [N] | [N] | elementwise |
| `conveyor_power` | effective_tension [N], belt_speed [m/s], drive_efficiency [1] | [W] | elementwise |
| `gy_fundamental_sampling_error` | sample_mass [kg], lot_mass [kg], top_size [m], mineralogical_factor [kg/m³], shape_factor [1], granulometric_factor [1], liberation_factor [1] | [1] (relative variance) | elementwise |
| `gy_blending_variance` | input_variance [unit²], n_layers [count], lag1_correlation [1] | [unit²] | elementwise |
| `variance_reduction_ratio` | n_layers [count], lag1_correlation [1] | [1] | elementwise |

### 7.2 Physical domain (violations raise `InputError`, FR-004-10)

| Argument | Domain |
|---|---|
| orifice_diameter, particle_diameter, bulk_density, discharge_coefficient, base_radius, base_half_width, load_area, belt_speed, sample_mass, lot_mass, top_size, mineralogical_factor, g | > 0 |
| annulus_coefficient, length, belt_weight, material_weight, kt, kx, ky, the three extra tensions, input_variance | ≥ 0 |
| repose_angle | 0 < φ < π/2 |
| lift, effective_tension | finite (negative allowed) |
| drive_efficiency | 0 < η ≤ 1 |
| shape_factor, granulometric_factor, liberation_factor | 0 < x ≤ 1 |
| n_layers | integer 1…10⁷ |
| lag1_correlation | −1 < ρ < 1 |

### 7.3 Unit tripwires (warn, FR-004-11; design choices of this spec, not sourced limits)

| Row | Argument | Warns when | Likely mistake |
|---|---|---|---|
| `tripwire_orifice_diameter_max` | orifice_diameter | > 10 m | mm passed as m |
| `tripwire_particle_diameter_max` | particle_diameter | > 1 m | mm passed as m |
| `tripwire_bulk_density_min` | bulk_density | < 100 kg/m³ | t/m³ passed as kg/m³ |
| `tripwire_repose_angle_max` | repose_angle | > 1.05 rad (60°) | steeper than granular heaps; check the angle |
| `tripwire_belt_speed_max` | belt_speed | > 15 m/s | ft/min or km/h passed as m/s |
| `tripwire_mineralogical_factor_min` | mineralogical_factor | < 100 kg/m³ | g/cm³ passed as kg/m³ |
| `tripwire_top_size_max` | top_size | > 0.5 m | cm passed as m |

### 7.4 Worked values (hand calculations with g₀ unless stated; values to the digits shown)

| Case | Value |
|---|---|
| `beverloo_discharge(0.3, 0.02, 1600, 0.56, 1.5)` | 106.28641 kg/s (382.6 t/h); D = 0.15 m → 13.996565 kg/s; D = 0.6 m → 688.26469 kg/s |
| `beverloo_discharge(0.03, 0.02, 1600, 0.56, 1.5)` | `InputError` (D = k·d) |
| `repose_cone_height(30, radians(37))`, `repose_cone_volume(30, radians(37))` | 22.606622 m, 21,306.239 m³ |
| `repose_ridge_volume(30, radians(37), 100)` | 67,819.865 m³; with `end_cones=True` 89,126.103 m³ |
| `conveyor_capacity(0.25, 4, 1600)` | 1,600 kg/s (5,760 t/h) |
| lift floor: ṁ = 2,000 t/h, V = 4 m/s, H = 30 m, `material_weight = ṁ·g₀/V` = 1,362.0347 N/m | T_e = 40,861.042 N; P = 163,444.17 W (= ṁ·g₀·H) |
| `cema_effective_tension(1000, 30, 300, 1362.0347…, 1.0, 10, 0.03)` | 105,222.08 N; `conveyor_power(…, 4, 0.9)` = 467,653.70 W |
| `gy_blending_variance(1, 100, 0)`, `(1, 100, 0.9)`, `(1, 10, 0.5)`, `(1, 2, −0.5)` | 0.01, 0.17200048, 0.26003906, 0.25 (variance reduction ratios 100, 5.8139, 3.8456, 4) |
| `gy_fundamental_sampling_error(1.0, 1000.0, 0.01, 1.0e4, 0.5, 0.25, 0.1)` | 1.24875 × 10⁻⁴ (relative standard deviation 1.1175 %); the same in cgs (1,000 g, 10⁶ g, 1 cm, 10 g/cm³) |

The closed form used for FR-004-09 is `Σ_{k=1}^{N−1}(1 − k/N)ρᵏ = ρ/(1−ρ) − ρ(1−ρᴺ)/(N(1−ρ)²)` for ρ ≠ 0 (arithmetic);
near ρ → 1 the implementation switches to the explicit sum for N ≤ 1,000 or a series expansion so that the result
stays within TC-1.

### 7.5 Knowledge rows (DC-004-01)

| Row id | Value | Units | Role | Citation, page | Verification |
|---|---|---|---|---|---|
| `beverloo_exponent` | "5/2" | 1 | model_constant | Beverloo, Leniger and van de Velde 1961 (primary paywalled, not read); printed in Mankoc et al. 2007, eq. 1, p. 1 | UNVERIFIED (secondary only); the exponent also follows from dimensional analysis, which is the test oracle |
| `beverloo_discharge_coefficient_range` | 0.55–0.65 | 1 | parameter | Beverloo et al. 1961 as quoted by Mankoc et al. 2007, p. 1 (bulk-density form) | UNVERIFIED (secondary only; not a default) |
| `beverloo_annulus_coefficient_range` | 1–2 | 1 | parameter | same, p. 1 (Darias, Madrid and Pugnaloni 2020, p. 1, report 1.4–3) | UNVERIFIED (secondary only; not a default) |
| `beverloo_discharge_coefficient_dem` | 0.56 | 1 | parameter | da Silva et al. 2025 (arXiv 2512.03698), p. 9: fitted with the **particle** density ρ = 3,000 kg/m³, exponent 2.5, g = 9.8 m/s² | verified (not a default; not interchangeable with the bulk-density C) |
| `cema_return_belt_coefficient` | 0.015 | 1 | model_constant | CEMA, *Belt Conveyors for Bulk Materials*, 7th ed. (paywalled; errata page unreachable); printed in PDHonline course M344, p. 13 | UNVERIFIED (secondary only) |
| `cema_ky_typical_range` | 0.016–0.035 | 1 | parameter | PDHonline course M344, p. 13 ("normal selection 0.022") | UNVERIFIED (secondary; not a default) |
| `gy_fse_shape_factor_default` | 0.5 | 1 | parameter | Gy (primary not read); Minkkinen 2008 (Eurachem workshop), p. 6 | UNVERIFIED (secondary; not a default) |
| `gy_fse_granulometric_factor_wide` | 0.25 | 1 | parameter | Gy (primary not read); Minkkinen 2008, p. 7 (wide size distributions) | UNVERIFIED (secondary; not a default) |
| `tripwire_*` (Table 7.3) | as listed | as listed | limit | this specification, §7.3 | UNVERIFIED (design choice, not a measurement) |

### 7.6 Assumptions
- Beverloo's law applies to coarse, cohesionless, free-flowing material through a circular orifice in a flat-bottomed
  bin; very small orifices (a few particle diameters) need the extended law of Mankoc et al., which is not
  implemented.
- Stockpiles are ideal cones or prismatic ridges at one repose angle; toe and crest rounding are ignored.
- The CEMA form is implemented only as the published equation with caller-supplied factors; no CEMA table is
  reproduced (constitution principle 9). `K_x`, `K_y`, `K_t` and the extra tensions must come from the user's licensed
  copy or a measurement.
- The blending model assumes a stationary AR(1) grade series reclaimed in full cross-section; real grade series need a
  variogram-based simulation, which the consumers do with these functions as building blocks.
- Functions that read an UNVERIFIED `model_constant` row emit `minephys.knowledge.UnverifiedParameterWarning` on use
  (008-knowledge FR-008-12): `beverloo_discharge` (`beverloo_exponent`) and `cema_effective_tension`
  (`cema_return_belt_coefficient`). Their tests expect the warning.

## 8. Clarifications log
- **Resolved — CEMA transcription.** The equation and its 0.015 coefficient are the public form quoted in the docs and
  the plan, and printed identically (with `±H`) in a public engineering course (PDHonline M344, p. 13); the standard is
  paywalled and its errata page was unreachable, so the row stays UNVERIFIED and the tests use the lift-floor identity
  (P-004-05) and hand calculations, which hold for any value of the coefficient.
- **Resolved — Beverloo density basis (docs contradiction).** The PitStudio bulk-flow page applies the DEM study's
  C = 0.56 together with a bulk density. That study fitted C with the particle density (3,000 kg/m³, p. 9), whereas
  Beverloo's law as printed by Mankoc et al. 2007 (eq. 1) uses the bulk density with 0.55 < C < 0.65. The library
  implements the bulk-density form; C and k have no default (constitution principle 1); the DEM row records its basis.
  The worked value of §7.4 passes C = 0.56 only as an illustrative input.
- **Resolved — Gy's formula.** The form `σ² = (1/M_S − 1/M_L)·c·f·g·ℓ·d³` is read on Minkkinen 2008 (p. 5) and,
  without the lot-mass term, on Geelhoed 2011 (eq. 1); Gy's own text was not read. The formula has no numeric
  constant; the shape and granulometric defaults of the literature are documented rows, not defaults.
- **Resolved — "Gy".** The plan's "Gy" covers both the fundamental sampling error and bed blending; both are
  implemented. The AR(1) variance of the mean is arithmetic (derived on the theory page); Gy's idealised `1/N` limit is
  its ρ = 0 case.
- **Resolved — user stories as table rows.** Stories are table rows so that `tools/trace.py` defines their IDs.
