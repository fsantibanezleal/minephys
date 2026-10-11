# Spec 001 — Haulage models (`minephys.haulage`)
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent
Haul-truck physics and fleet queueing are the largest lever on open-pit cost and energy, and the consumers (the
PitStudio pipelines, its discrete-event engine and its browser ports) need one sourced, tested implementation to
compute against and to test against. This module provides steady-state, one-dimensional longitudinal truck physics
(grade and rolling resistance, required force, rimpull-, traction- and retarder-limited speeds), loading passes and
cycle time, segment and cycle energy with fuel and CO₂, trolley-assist and battery-electric energy, and the closed
analytical fleet models (match factor, M/M/c, finite-source queue, exact mean-value analysis). The analytical queue
models are the exact oracles that a discrete-event simulation must reproduce in the exponential case.
**Out of scope:** discrete-event simulation, dispatching and route search over a road network such as A\* (the
consumers' engine and code), transient speed integration along
a profile, lateral dynamics and superelevation, OEM rimpull or retarder charts, heterogeneous-fleet match factor,
upstream (well-to-tank) fuel emissions and default grid intensities.

## 2. User stories

| ID | Story | Priority | Independent test |
|---|---|---|---|
| US-001-1 | As a mining engineer, I want the energy, fuel and CO₂ of a haul cycle for diesel, trolley-assist and battery-electric trucks, so that I can compare power trains per tonne hauled. | P1 | the three-segment cycle of §7.4 returns the hand-calculated energies |
| US-001-2 | As a pipeline developer, I want rimpull-, traction- and retarder-limited steady speeds and travel times per road segment, so that a simulator's travel times come from physics. | P1 | worked example 1 (§7.4) reproduces its speeds |
| US-001-3 | As a simulation developer, I want exact match-factor, M/M/c, finite-source and mean-value-analysis results, so that my discrete-event engine can be tested against them in the exponential case. | P1 | the finite-source table of §7.4 is reproduced by both the closed form and MVA |
| US-001-4 | As a student, I want loading passes from bucket size, fill factor and swell, so that I can relate loader and truck sizes. | P2 | the exact-multiple case of §7.4 returns 3 passes |

## 3. Functional requirements (EARS)

All functions take and return SI units (constitution principle 7); grade is rise over run (`tan θ`), resistances are
fractions of gross vehicle weight, and `g` defaults to standard gravity g₀ = 9.80665 m/s² (foundation A1). Signatures
are in §7.1.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-001-01 | Ubiquitous | `grade_resistance(grade, small_angle=False)` shall return `grade/√(1+grade²)` (that is `sin(arctan grade)`), and `grade` itself when `small_angle=True`. | unit |
| FR-001-02 | Ubiquitous | `total_resistance(rolling_resistance, grade, small_angle=False)` shall return `rolling_resistance + grade_resistance(grade, small_angle)`. | unit |
| FR-001-03 | Ubiquitous | `required_force(mass, total_resistance, acceleration=0, effective_mass=None, drag_area=0, air_density=None, speed=0, g=g₀)` shall return `mass·g·total_resistance + m_eff·acceleration + ½·air_density·drag_area·speed²` in N, with `m_eff = mass` when `effective_mass` is `None`. | unit |
| FR-001-04 | Ubiquitous | `rimpull_limited_speed(power, mass, total_resistance, efficiency=1, traction_limit=+inf, speed_limit=+inf, drag_area=0, air_density=None, g=g₀)` shall return `min(v_ss, speed_limit)` in m/s, where `v_ss` is the largest `v ≥ 0` with `min(traction_limit, efficiency·power/v) ≥ mass·g·total_resistance + ½·air_density·drag_area·v²`; without drag and traction limit this is `efficiency·power/(mass·g·total_resistance)`. | unit |
| FR-001-05 | State | While `mass·g·total_resistance` exceeds `traction_limit`, `rimpull_limited_speed` shall return 0.0 (the truck cannot hold the grade). | unit |
| FR-001-06 | Ubiquitous | `retarder_limited_speed(retarder_power, mass, rolling_resistance, grade, speed_limit=+inf, small_angle=False, g=g₀)` shall return `min(retarder_power/(mass·g·f), speed_limit)` in m/s with the net braking fraction `f = −grade_resistance(grade) − rolling_resistance`, and shall return `speed_limit` while `f ≤ 0`. | unit |
| FR-001-07 | Unwanted | If the steady speed is unbounded (rimpull: `total_resistance ≤ 0` with `drag_area = 0`; retarder: `f ≤ 0`) and `speed_limit` is `+inf`, then the function shall raise `InputError` naming `speed_limit`. | hostile |
| FR-001-08 | Ubiquitous | `loose_density(bank_density, swell)` shall return `bank_density/(1+swell)` in kg/m³. | unit |
| FR-001-09 | Ubiquitous | `loading_passes(target_payload, bucket_volume, fill_factor, loose_density)` shall return the smallest integer `n ≥ 1` with `n·bucket_volume·fill_factor·loose_density ≥ target_payload`, treating a quotient within a relative 1e-12 of an integer as that integer, as an `int64` scalar or array. | unit |
| FR-001-10 | Ubiquitous | `segment_travel_time(length, speed)` shall return `length/speed` in s, and `cycle_time(spot_load, load, haul_travel, spot_dump, dump, return_travel, queue_load=0, queue_dump=0)` shall return the sum of its eight components in s. | unit |
| FR-001-11 | Ubiquitous | `segment_energy(mass, length, rolling_resistance, grade, efficiency=1, regen_efficiency=0, small_angle=False, g=g₀)` shall return the energy drawn from the source in J: `E_w/efficiency` when the wheel energy `E_w = mass·g·total_resistance·length` is ≥ 0, and `regen_efficiency·E_w` (≤ 0, energy returned) otherwise. | unit |
| FR-001-12 | Ubiquitous | `cycle_energy(mass, length, rolling_resistance, grade, efficiency=1, regen_efficiency=0, small_angle=False, g=g₀)` shall take 1-D per-segment arrays (scalars broadcast) and return the sum of `segment_energy` over the segments in J. | unit |
| FR-001-13 | Ubiquitous | `fuel_use(source_energy, fuel_energy_density)` shall return `source_energy/fuel_energy_density` in m³ of fuel. | unit |
| FR-001-14 | Ubiquitous | `co2_from_diesel(fuel_volume, emission_factor=None)` shall return kg CO₂; with `emission_factor=None` it shall use 10.21 kg CO₂ per US gallon (row `diesel_co2_kg_per_us_gal`, verified) divided by the exact US gallon 3.785411784 × 10⁻³ m³, i.e. 2,697.1967 kg/m³, and otherwise the given factor in kg/m³. | unit |
| FR-001-15 | Ubiquitous | `co2_from_electricity(energy, grid_intensity)` shall return `energy·grid_intensity` in kg, with `grid_intensity` in kg/J and no default. | unit |
| FR-001-16 | Ubiquitous | `trolley_cycle_energy(mass, length, rolling_resistance, grade, on_trolley, diesel_efficiency, electric_efficiency, small_angle=False, g=g₀)` shall return the pair `(diesel_energy, electric_energy)` in J: segments with `E_w > 0` draw `E_w/electric_efficiency` from the line where `on_trolley` is true and `E_w/diesel_efficiency` from the tank otherwise; segments with `E_w ≤ 0` draw nothing. | unit |
| FR-001-17 | Ubiquitous | `bev_cycle_energy(mass, length, rolling_resistance, grade, drive_efficiency, regen_efficiency, small_angle=False, g=g₀)` shall return the net battery energy in J, equal to `cycle_energy(…, efficiency=drive_efficiency, regen_efficiency=regen_efficiency)`. | unit |
| FR-001-18 | Ubiquitous | `match_factor(n_trucks, n_loaders, load_time, cycle_time)` shall return `n_trucks·load_time/(n_loaders·cycle_time)` (dimensionless), with `cycle_time` the truck cycle excluding waiting. | unit |
| FR-001-19 | Ubiquitous | `mmc_queue(arrival_rate, service_rate, servers)` shall return a named result with `utilisation ρ = λ/(cμ)`, `erlang_c` C(c, a) with `a = λ/μ`, `mean_wait` `W_q = C/(cμ−λ)` in s, `mean_queue_length` `L_q = λW_q`, `mean_time_in_system` `W = W_q + 1/μ` in s and `mean_in_system` `L = λW`, computed without overflow for `servers` up to 10,000. | unit |
| FR-001-20 | Ubiquitous | `finite_source_queue(n_trucks, travel_rate, service_rate)` shall return a named result for one loader and N trucks with exponential times: `idle_probability π₀ = [Σ_{n=0}^{N} N!/(N−n)!·(λ/μ)ⁿ]⁻¹`, `utilisation 1−π₀`, `throughput X = μ(1−π₀)` in 1/s, `mean_at_loader L = N − X/λ` and `mean_time_at_loader L/X` in s, without overflow for N up to 100,000. | unit |
| FR-001-21 | Ubiquitous | `mean_value_analysis(population, service_time, visit_ratio, station_type)` shall run exact single-class MVA for n = 1…N over K stations (`W_k(n) = S_k(1 + L_k(n−1))` for `"queue"`, `W_k = S_k` for `"delay"`, `X(n) = n/Σ v_k W_k(n)`, `L_k(n) = v_k X(n) W_k(n)`) and return the throughput array `X(1…N)` in 1/s and, at n = N, the residence times (s), queue lengths and utilisations `v_k X S_k` per station. | unit |
| FR-001-22 | Unwanted | If any argument violates its physical domain in Table 7.2, then the function shall raise `InputError` naming that argument (foundation FR-000-14). | hostile |
| FR-001-23 | Unwanted | If any argument trips a unit tripwire in Table 7.3, then the function shall emit `ValidityWarning` naming the argument and the tripwire row and shall still return the result (foundation FR-000-16). | unit |
| FR-001-24 | Unwanted | If `arrival_rate ≥ servers·service_rate` (ρ ≥ 1, no steady state), then `mmc_queue` shall raise `InputError` naming `arrival_rate`. | hostile |
| FR-001-25 | Unwanted | If the per-segment arrays of `cycle_energy`, `trolley_cycle_energy` or `bev_cycle_energy` are not 1-D, have different lengths after broadcasting scalars, are empty, or exceed 100,000 segments, or if `on_trolley` is not boolean, then the function shall raise `InputError` (or `InputTypeError` for a non-boolean `on_trolley`) naming the argument. | hostile |
| FR-001-26 | Unwanted | If `servers`, `n_trucks`, `n_loaders` or `population` is not an integer ≥ 1 or exceeds its cap (10,000 servers; 100,000 trucks or population), or `mean_value_analysis` has more than 1,000 stations, a `station_type` other than `"queue"` or `"delay"`, arrays of different lengths, or `Σ v_k S_k = 0`, then the function shall raise `InputError` naming the argument. | hostile |

## 4. Correctness properties

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-001-01 | `grade_resistance` is odd (`GR(−x) = −GR(x)`), strictly increasing, and `|GR_exact(x)| ≤ |x|` with equality only at x = 0 (metamorphic: symmetry, monotonicity). | grade ∈ [−1, 1] | exact for symmetry; TC-1 otherwise |
| P-001-02 | Without drag and traction limit, `rimpull_limited_speed` scales linearly with `power·efficiency` and inversely with `mass` and with `total_resistance` while below `speed_limit` (metamorphic: scaling). | power ∈ [1e5, 5e6] W, mass ∈ [2e4, 7e5] kg, TR ∈ [0.01, 0.3], k ∈ [0.1, 10] | TC-1 |
| P-001-03 | `rimpull_limited_speed` is non-increasing in mass, total resistance, drag area and air density and non-decreasing in power, efficiency, traction limit and speed limit; adding drag never increases the speed (metamorphic: monotonicity). | as P-001-02, drag_area ∈ [0, 100] m² | exact ordering |
| P-001-04 | Uncapped `retarder_limited_speed·mass` is constant in mass, and the speed is non-increasing in downgrade steepness (metamorphic: scaling, monotonicity). | grade ∈ [−0.3, −0.03], RR ∈ [0, 0.03], mass ∈ [2e4, 7e5] kg | TC-1 |
| P-001-05 | Splitting a segment into two consecutive segments of the same mass, grade and rolling resistance with lengths L₁ + L₂ = L leaves `cycle_energy` unchanged, and permuting segments leaves it unchanged (metamorphic: additivity, permutation invariance). | 1–200 segments | TC-1 (rtol 1e-12 relative to Σ\|E\|) |
| P-001-06 | With zero rolling resistance, unit efficiencies and full regeneration, the cycle energy of constant mass over a profile that returns to its start elevation is 0, and in general equals `mass·g·Δh` (metamorphic: conservation). | random closed profiles, 2–200 segments, \|grade\| ≤ 0.3 | atol 1e-12·Σ\|E_w\| |
| P-001-07 | Energy is linear in mass and in length (k·m or k·L gives k·E), and `co2_from_diesel(V)` equals 10.21 × V/(3.785411784 × 10⁻³) (metamorphic: scaling, unit-change invariance m³ ↔ US gal). | k ∈ [1e-3, 1e3] | TC-1 |
| P-001-08 | `mmc_queue` is invariant to the time unit: scaling λ and μ by k leaves ρ, C, L_q and L unchanged and divides W_q and W by k (metamorphic: unit-change invariance). | c ∈ 1…50, ρ ∈ (0, 0.99), k ∈ [1e-4, 1e4] | TC-1 |
| P-001-09 | `mmc_queue` satisfies Little's law (`L_q = λW_q`, `L = λW`), `0 < C < 1`, `C = ρ` for c = 1, W_q strictly increasing in λ and non-increasing in c, and C(c, a) equals the Erlang-B recursion form `B/(1 − ρ(1 − B))` (metamorphic: monotonicity; identity). | as P-001-08 | TC-1 |
| P-001-10 | `finite_source_queue` throughput is non-decreasing in N and bounded by `min(N/(1/λ+1/μ), μ)`, satisfies the flow balance `X = λ(N − L)`, and scales by k when λ and μ scale by k (metamorphic: monotonicity, bound, scaling). | N ∈ 1…500, λ/μ ∈ [1e-3, 10] | TC-1; bound exact ordering |
| P-001-11 | `mean_value_analysis` conserves the population (`Σ_k L_k(N) = N`), is invariant to station order, divides X by k when all service times scale by k, gives non-decreasing X(n), and with one `"queue"` and one `"delay"` station equals `finite_source_queue` (metamorphic: conservation, permutation, scaling; identity). | N ∈ 1…500, K ∈ 1…20 | TC-1 |
| P-001-12 | `match_factor` is unchanged when both times scale by k and is linear in `n_trucks` (metamorphic: unit-change invariance, scaling). | k ∈ [1e-3, 1e3] | TC-1 |
| P-001-13 | `loading_passes` is non-decreasing in target payload and non-increasing in bucket volume, fill factor and loose density, and `n·V·k·ρ ≥ M > (n−1)·V·k·ρ` up to the 1e-12 integer rule (metamorphic: monotonicity; bracket identity). | M ∈ [1e3, 6e5] kg, V ∈ [1, 60] m³ | exact |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-001-01 | Latency of `mean_value_analysis` at the reference size N = 200, K = 10, and of `cycle_energy` at 1,000 segments | ≤ 50 ms median (foundation NFR-000-07) | `tools/bench.py` |
| NFR-001-02 | Closed-form functions of this module on scalar inputs | ≤ 1 ms median | `tools/bench.py` |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-001-01 | `src/minephys/knowledge/haulage.yaml` (rows of §7.5) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.haulage`, docs generator, PitStudio knowledge pages |

## 7. Edge cases and assumptions

### 7.1 Signatures (keyword-only after the first positional arguments shown)

| Function | Arguments [units] | Returns [units] | Shape |
|---|---|---|---|
| `grade_resistance` | grade [1], small_angle | [1] | elementwise |
| `total_resistance` | rolling_resistance [1], grade [1], small_angle | [1] | elementwise |
| `required_force` | mass [kg], total_resistance [1], acceleration [m/s²], effective_mass [kg], drag_area [m²], air_density [kg/m³], speed [m/s], g [m/s²] | [N] | elementwise |
| `rimpull_limited_speed` | power [W], mass [kg], total_resistance [1], efficiency [1], traction_limit [N], speed_limit [m/s], drag_area [m²], air_density [kg/m³], g [m/s²] | [m/s] | elementwise |
| `retarder_limited_speed` | retarder_power [W], mass [kg], rolling_resistance [1], grade [1], speed_limit [m/s], small_angle, g [m/s²] | [m/s] | elementwise |
| `loose_density` | bank_density [kg/m³], swell [1] | [kg/m³] | elementwise |
| `loading_passes` | target_payload [kg], bucket_volume [m³], fill_factor [1], loose_density [kg/m³] | count (int64) | elementwise |
| `segment_travel_time` | length [m], speed [m/s] | [s] | elementwise |
| `cycle_time` | eight components [s] | [s] | elementwise |
| `segment_energy` | mass [kg], length [m], rolling_resistance [1], grade [1], efficiency [1], regen_efficiency [1], small_angle, g [m/s²] | [J] | elementwise |
| `cycle_energy`, `bev_cycle_energy` | per-segment 1-D arrays as `segment_energy` | [J] scalar | aggregate, 1…100,000 segments |
| `trolley_cycle_energy` | as `cycle_energy` + on_trolley [bool], diesel_efficiency [1], electric_efficiency [1] | ([J], [J]) | aggregate |
| `fuel_use` | source_energy [J], fuel_energy_density [J/m³] | [m³] | elementwise |
| `co2_from_diesel` | fuel_volume [m³], emission_factor [kg/m³] | [kg] | elementwise |
| `co2_from_electricity` | energy [J], grid_intensity [kg/J] | [kg] | elementwise |
| `match_factor` | n_trucks [count], n_loaders [count], load_time [s], cycle_time [s] | [1] | elementwise |
| `mmc_queue` | arrival_rate [1/s], service_rate [1/s], servers [count] | named result | scalar inputs only (rank 0) |
| `finite_source_queue` | n_trucks [count], travel_rate [1/s], service_rate [1/s] | named result | scalar inputs only |
| `mean_value_analysis` | population [count], service_time [s] (K), visit_ratio [1] (K), station_type (K strings) | named result | aggregate, K ∈ 1…1,000 |

### 7.2 Physical domain (violations raise `InputError`, FR-001-22)

| Argument | Domain |
|---|---|
| grade | finite |
| rolling_resistance | 0 ≤ RR < 1 |
| mass, effective_mass, power, retarder_power, bank_density, loose_density, target_payload, bucket_volume, fuel_energy_density, emission_factor, service_rate, travel_rate, arrival_rate | > 0 |
| efficiency, diesel_efficiency, electric_efficiency, drive_efficiency, fill_factor | 0 < x ≤ 1 (`fill_factor` ≤ 2) |
| regen_efficiency | 0 ≤ x ≤ 1 |
| swell, drag_area, length, the eight `cycle_time` components | ≥ 0 |
| acceleration | finite (negative values are decelerations) |
| air_density | > 0, required when `drag_area > 0` (else `InputError` naming `air_density`) |
| traction_limit, speed_limit | > 0; `+inf` allowed (the only arguments of this module that accept `+inf`) |
| speed (travel time), source_energy, fuel_volume, energy, grid_intensity | speed > 0; the others ≥ 0 |
| load_time, cycle_time (match factor) | > 0 and `load_time < cycle_time` |
| g | > 0 |

### 7.3 Unit tripwires (warn, FR-001-23; design choices of this spec, not sourced limits)

| Row | Argument | Warns when | Likely mistake |
|---|---|---|---|
| `tripwire_grade_abs_max` | grade | \|grade\| > 0.30 | percent passed as a fraction |
| `tripwire_rolling_resistance_max` | rolling_resistance | RR > 0.20 | percent passed as a fraction |
| `tripwire_truck_mass_min`, `tripwire_truck_mass_max` | mass | < 1,000 kg or > 2,000,000 kg | tonnes passed as kg, or grams |
| `tripwire_swell_max` | swell | > 1.0 | percent passed as a fraction |
| `tripwire_bank_density_min` | bank_density | < 500 kg/m³ | t/m³ passed as kg/m³ |
| `tripwire_fuel_energy_density_min` | fuel_energy_density | < 1 × 10⁹ J/m³ | MJ/L passed as J/m³ |
| `tripwire_grid_intensity_max` | grid_intensity | > 1 × 10⁻⁶ kg/J | kg/kWh passed as kg/J |

### 7.4 Worked values (hand calculations with g₀ = 9.80665 m/s² unless stated; values to the digits shown)

Worked example 1 (illustrative inputs consistent with the theory page: 400 t gross, 1.8 MW at the wheels, 10 % grade,
2 % rolling resistance, `small_angle=True`):

| Quantity | Value |
|---|---|
| `required_force(400000, 0.12)` | 470,719.2 N |
| `rimpull_limited_speed(1.8e6, 400000, 0.12)` | 3.8239358 m/s (with `g=9.81`: 3.8226300 m/s, the docs' 3.82 m/s) |
| same at TR = 0.04, 0.08, 0.16 | 11.471807, 5.7359037, 2.8679518 m/s |
| with `drag_area=45`, `air_density=1.2` (cubic root) | 3.8207366 m/s |
| `traction_limit=400e3` | 0.0 (FR-001-05) |
| `retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, small_angle=True)` | 7.9665329 m/s |
| same with `mass=180000` | 17.703406 m/s |
| same as the 400 t case with exact grade resistance (0.099503719) | 8.0162619 m/s |
| `grade_resistance(0.10)` | 0.0995037190209989 |
| `segment_energy(400000, 3000, 0.02, 0.10, small_angle=True)` | 1.4121576 × 10⁹ J (392.266 kWh) |
| `fuel_use(segment_energy(…, efficiency=0.35), 36e9)` | 0.112076 m³ |
| `co2_from_diesel(0.112076)` | 302.291 kg |

Cycle example (exact grade resistance): segments (mass kg, length m, RR, grade, on_trolley) = (400000, 3000, 0.02,
0.10, true), (180000, 3000, 0.02, −0.10, false), (400000, 1000, 0.03, 0, false).

| Quantity | Value |
|---|---|
| wheel energies | 1.40631738 × 10⁹, −4.21019179 × 10⁸, 1.17679800 × 10⁸ J |
| `cycle_energy(…, efficiency=0.35)` (diesel, no regeneration) | 4.35427764 × 10⁹ J → 0.120952 m³ diesel → 326.232 kg CO₂ |
| `trolley_cycle_energy(…, diesel_efficiency=0.35, electric_efficiency=0.9)` | (3.36228000 × 10⁸ J, 1.56257486 × 10⁹ J) |
| `bev_cycle_energy(…, drive_efficiency=0.85, regen_efficiency=0.6)` | 1.54032635 × 10⁹ J (427.868 kWh) |

Queues (rates per hour converted to 1/s):

| Case | Value |
|---|---|
| `mmc_queue(24/3600, 15/3600, 2)` | ρ = 0.8, C = 0.7111111, W_q = 426.6667 s, L_q = 2.8444444, W = 666.6667 s, L = 4.4444444 |
| `mmc_queue(10/3600, 15/3600, 1)` | C = ρ = 0.6666667, W_q = 480.0 s |
| `finite_source_queue(N, 3/3600, 15/3600)` | X·3600 = 2.500000, 7.055085, 10.726983, 12.122291, 13.949282 for N = 1, 3, 5, 6, 8; π₀(N = 5) = 0.284868 (sum 3.5104) |
| `mean_value_analysis(5, [240, 1200], [1, 1], ["queue", "delay"])` | X·3600 = 10.726983 (= the finite-source value), L = (1.4243391, 3.5756609) |
| `mean_value_analysis(8, [240, 60, 1200], [1, 1, 1], ["queue", "queue", "delay"])` | X·3600 for n = 1…8: 2.4000000, 4.6728972, 6.7856723, 8.7001686, 10.376463, 11.779540, 12.888759, 13.707006; at N = 8, W = (825.18739, 75.927974, 1200) s |
| `match_factor(6, 1, 240, 1440)` | 1.0 |

Loading: `loading_passes(216000, 40, 0.9, loose_density(2700, 0.35))` = 3 (the quotient is 3.0000000000000004 in
float64; FR-001-09's integer rule applies); `loading_passes(220000, 40, 0.9, 2000)` = 4.

### 7.5 Knowledge rows (DC-001-01)

| Row id | Value | Units | Role | Citation, page | Verification |
|---|---|---|---|---|---|
| `diesel_co2_kg_per_us_gal` | 10.21 | kg CO₂ / US gal | parameter | US EPA GHG Emission Factors Hub 2025, Table 2, p. 2 | verified (2026-10-06) |
| `rolling_resistance_hard_smooth` | 0.015 | 1 | parameter | OEM rolling-resistance article | UNVERIFIED (source unreachable) |
| `rolling_resistance_firm_maintained` | 0.03 | 1 | parameter | same | UNVERIFIED |
| `rolling_resistance_rutted_soft` | 0.08 | 1 | parameter | same | UNVERIFIED |
| `rolling_resistance_loose_gravel` | 0.10 | 1 | parameter | same | UNVERIFIED |
| `rolling_resistance_per_cm_penetration` | 0.006 | 1 per cm | parameter | same | UNVERIFIED |
| `tripwire_*` (Table 7.3) | as listed | as listed | limit | this specification, §7.3 | UNVERIFIED (design choice, not a measurement) |

Standard gravity and the US gallon, inch and pound definitions are rows of the foundation `units` table. The rolling-
resistance rows document typical inputs only; no function uses them as defaults (foundation FR-000-22).

### 7.6 Assumptions
- Rolling resistance is applied to the full gross weight (the industry `TR = RR + GR` decomposition), not to the
  normal component.
- `segment_energy` assumes steady speed (no kinetic-energy change) and along-road `length`; the grade term equals the
  potential-energy change exactly when `small_angle=False`.
- Trolley segments do not regenerate into the line (no published regeneration model for the line was read); a
  battery-electric truck regenerates with `regen_efficiency`.
- Queue models assume exponential times and single-class product form; they are bounds and test oracles, not
  forecasts.

## 8. Clarifications log
- **Resolved — grade convention.** The theory page writes resistances in percent and `GR ≈ 100 tan θ`; the library
  uses fractions and the exact `sin(arctan grade)` by default, with `small_angle=True` for the percent-style
  convention used in the docs' worked example.
- **Resolved — gravity.** Oracles use g₀ = 9.80665 m/s² (foundation A1); with `g=9.81` the docs' worked example is
  reproduced to its printed digits (3.82 m/s, 470.9 kN, 28.7 km/h, 63.7 km/h).
- **Resolved — CO₂ factor.** Diesel 10.21 kg CO₂ per US gallon is verified on the EPA GHG Emission Factors Hub 2025,
  Table 2 ("Mobile Combustion CO₂"), p. 2; it is combustion (tank-to-wheel) CO₂ only. The non-road CH₄ and N₂O factors
  (Table 5, p. 3) are not implemented; the theory page's remark that they are "separate rows of the same table" is
  corrected here: they are in a separate table.
- **Resolved — finite-source transcription.** The docs mark the machine-repairman formula UNVERIFIED. It is read on
  Sztrik, *Basic Queueing Theory*, §3.2 "The M/M/1/n/n queue", pp. 125–127 (`P₀ = 1/Σ n!/(n−k)!·ϱᵏ`, `U = 1 − P₀`,
  throughput `μU`, mean number `n − U/ϱ`), and its tests also use the independent MVA identity (P-001-11). The Erlang C
  and MVA recursions are read on the cited encyclopedia pages; MVA delay stations follow the standard extension
  (`W_k = S_k`). None of these formulas carries a constant.
- **Resolved — resistance decomposition.** `TR = RR + GR` is the industry convention cited by the theory page
  (Soofastaei et al. 2016); the article was blocked when this spec was written, so the statement stays a cited
  convention without a page. It carries no constant.
- **Resolved — match factor.** Only the homogeneous ratio is implemented, with the theory page's cycle time excluding
  waiting. Burt and Caccetta's heterogeneous extension and their exact cycle-time definition were not read (the
  primary was blocked), so the extension is out of scope.
- **Resolved — user stories as table rows.** Stories are table rows so that `tools/trace.py` defines their IDs.
- Integration 2026-10-07: route search (A\* over a haul-road graph) is PitStudio code, not `minephys.haulage` (the
  plan lists no routing in this module); this spec specifies none and now says so in the out-of-scope list.
