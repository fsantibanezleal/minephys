# Spec 003 — Geotechnical models (`minephys.geotech`)
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent
Pit walls fail; design asks whether a wall is stable and how likely it is to fail, and operations ask, once a wall
moves, when it will fail. The consumers (PitStudio's slope case, its forecasters' classical baseline, its synthetic
slope-radar series and its browser ports) need one sourced, tested implementation of the classical answers. This
module provides the generalised Hoek–Brown criterion with its equivalent Mohr–Coulomb parameters, circular-surface
limit equilibrium by Bishop's simplified method and Spencer's method on slice data, a Monte-Carlo probability of
failure, Voight's accelerating-creep series, the inverse-velocity time-of-failure forecast, a conjugate Bayesian
time-of-failure posterior and the analytical line-of-sight and phase model of ground-based interferometric radar.
**Out of scope:** critical-surface search, non-circular surfaces, Janbu's method, finite-element strength reduction,
kinematic stereonet analysis, run-out, radar hardware, focusing, atmospheric correction and spatial phase
unwrapping; FoS and PoF acceptance criteria (inputs of the consumer, never defaults here).

## 2. User stories

| ID | Story | Priority | Independent test |
|---|---|---|---|
| US-003-1 | As a geotechnical engineer or student, I want the factor of safety of a circular slip surface by Bishop and Spencer with strengths from Hoek–Brown, and its probability of failure under uncertain strength, so that I can reproduce textbook and benchmark analyses. | P1 | the published benchmarks of §7.4 (hand calculation #1: 2.113; Fredlund and Krahn: 2.080 / 2.073) |
| US-003-2 | As a monitoring engineer, I want an inverse-velocity forecast and a Bayesian posterior of the failure time from a velocity series, so that I see the forecast with its uncertainty. | P1 | the noise-free series of §7.4 returns 10 days exactly |
| US-003-3 | As a simulation developer, I want Voight creep series projected on a radar line of sight, with interferometric phase and wrapping, so that synthetic slope-radar data have exact ground truth. | P1 | the line-of-sight and phase values of §7.4 |
| US-003-4 | As a student, I want the Hoek–Brown parameters and equivalent Mohr–Coulomb strength of the 2002 edition's worked example, so that I can check my own calculation. | P2 | φ' = 27.61°, c' = 0.35 MPa for the 100 m slope |

## 3. Functional requirements (EARS)

SI units at the API (constitution principle 7): stresses and cohesion in Pa, unit weights in N/m³, weights in N per
metre of slope (plane strain), angles in rad, velocities in m/s, times in s, positions in m. Signatures in §7.1.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-003-01 | Ubiquitous | `hoek_brown_parameters(gsi, mi, disturbance)` shall return `(mb, s, a)` with `mb = mi·exp((GSI−100)/(28−14D))`, `s = exp((GSI−100)/(9−3D))` and `a = 1/2 + (e^{−GSI/15} − e^{−20/3})/6` (Hoek, Carranza-Torres and Corkum 2002, eqs. 3–5). | unit |
| FR-003-02 | Ubiquitous | `hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a)` shall return `σ1 = σ3 + σci·(mb·σ3/σci + s)^a` in Pa (eq. 2). | unit |
| FR-003-03 | Ubiquitous | `hoek_brown_uniaxial_strength(sigma_ci, s, a)` shall return `σci·s^a` (eq. 6), `hoek_brown_tensile_strength(sigma_ci, mb, s)` shall return `−s·σci/mb` (eq. 7), and `hoek_brown_rock_mass_strength(sigma_ci, mb, s, a)` shall return `σcm = σci·(mb + 4s − a(mb − 8s))·(mb/4 + s)^{a−1}/(2(1+a)(2+a))` (eq. 17), all in Pa. | unit |
| FR-003-04 | Ubiquitous | `equivalent_mohr_coulomb(sigma_ci, mb, s, a, sigma3_max)` shall return `(cohesion, friction_angle)` in (Pa, rad) from eqs. 12–13 of the 2002 edition with `σ3n = σ3max/σci`. | unit |
| FR-003-05 | Ubiquitous | `sigma3_max(sigma_cm, unit_weight, height, application)` shall return `σcm·0.72·(σcm/(γH))^{−0.91}` for `application="slope"` (eq. 19, H the slope height) and `σcm·0.47·(σcm/(γH))^{−0.94}` for `"tunnel"` (eq. 18, H the depth), in Pa. | unit |
| FR-003-06 | Unwanted | If `sigma3` is below the tensile strength `−s·σci/mb` (the base of the power becomes negative), then `hoek_brown_sigma1` shall raise `InputError` naming `sigma3`. | hostile |
| FR-003-07 | Ubiquitous | `circular_slices(surface_x, surface_z, center_x, center_z, radius, n_slices, unit_weight, pore_pressure_ratio=0)` shall cut the mass between a ground polyline and a circle into `n_slices` equal-width vertical slices between the two intersection points and return per-slice `width` (m), `weight = γ·b·h` (N/m, with `h` the mid-slice height), `base_angle` (rad, signed so that the driving moment `Σ W sin α` is positive), `base_length = b/cos α` (m) and `pore_pressure = r_u·γ·h` (Pa). | unit |
| FR-003-08 | Unwanted | If the surface x-coordinates are not strictly increasing, or the circle does not cut the ground polyline at exactly two points, or `n_slices` is outside 2…10,000, then `circular_slices` shall raise `InputError` naming the argument. | hostile |
| FR-003-09 | Ubiquitous | `bishop_simplified_fos(width, weight, base_angle, pore_pressure, cohesion, friction_angle, tol=1e-12, max_iter=200)` shall return the fixed point F of `F = Σ[c'b + (W − u·b)tanφ']/m_α / Σ W sin α`, `m_α = cos α (1 + tan α tan φ'/F)`, iterated from F = 1 until the relative step is ≤ `tol`. | unit |
| FR-003-10 | Ubiquitous | `spencer_fos(width, weight, base_angle, pore_pressure, cohesion, friction_angle, tol=1e-12, max_iter=200)` shall return `(fos, theta)` such that, with `Q_i = [c'l_i/F + (W_i cos α_i − u_i l_i)tanφ'/F − W_i sin α_i] / [cos(α_i−θ) + sin(α_i−θ)tanφ'/F]`, both `Σ Q_i = 0` (force) and `Σ Q_i cos(α_i − θ) = 0` (moment about the circle centre) hold to a relative residual ≤ `tol`. | unit |
| FR-003-11 | Unwanted | If the driving moment `Σ W sin α` is ≤ 0, then the LEM functions shall raise `InputError` naming `base_angle`; if any `m_α` (Bishop) or Spencer denominator becomes ≤ 0 during iteration, then they shall raise `ConvergenceError` whose message names the first such slice index. | hostile |
| FR-003-12 | Ubiquitous | `monte_carlo_fos(width, weight, base_angle, pore_pressure, cohesion_mean, cohesion_sd, friction_mean, friction_sd, n_samples, rng, method="bishop")` shall draw cohesion and friction angle independently from normal distributions truncated to `c' ≥ 0` and `0 ≤ φ' < π/2` (by resampling rejected draws from `rng`), evaluate the chosen method (`"bishop"` or `"spencer"`) for each draw on the fixed slices, and return the `n_samples` factors of safety. | unit |
| FR-003-13 | Ubiquitous | `probability_of_failure(fos_samples, threshold=1)` shall return `(pof, standard_error, n)` with `pof` the fraction of samples below `threshold` and `standard_error = √(pof(1−pof)/n)`; `required_samples(pof, relative_error)` shall return `⌈(1−p)/(p·ε²)⌉`. | unit |
| FR-003-14 | Ubiquitous | `voight_creep_series(t, failure_time, a, alpha)` shall return `(velocity, displacement)` with `v(t) = [A(α−1)(t_f − t)]^{1/(1−α)}` in m/s (the solution of `Ω̈ = A Ω̇^α`) and the displacement accumulated from `t[0]` in closed form (`(1/A)·ln((t_f − t₀)/(t_f − t))` for α = 2). | unit |
| FR-003-15 | Ubiquitous | `inverse_velocity_ttf(t, velocity, window=None)` shall fit `1/v = β₀ + β₁t` by ordinary least squares to the last `window` samples (all when `None`) and return `(failure_time = −β₀/β₁, slope, intercept, r_squared, accelerating, n_used)`. | unit |
| FR-003-16 | State | While the fitted slope β₁ is ≥ 0 (the wall is not accelerating), `inverse_velocity_ttf` shall return `accelerating=False` and `failure_time=+inf`. | unit |
| FR-003-17 | Ubiquitous | `bayesian_ttf(t, velocity, rng, noise_sd=None, prior_mean=None, prior_cov=None, n_draws=10_000, credible=0.9, window=None)` shall compute the conjugate Gaussian posterior `Σ_N = (Σ₀⁻¹ + XᵀX/σ²)⁻¹`, `μ_N = Σ_N(Σ₀⁻¹μ₀ + Xᵀy/σ²)` of (β₀, β₁) for `y = 1/v` (a flat prior, `Σ₀⁻¹ = 0`, when `prior_cov` is `None`; σ from the residuals `√(RSS/(n−2))` when `noise_sd` is `None`), draw `n_draws` samples, and return the posterior mean and covariance, the median and equal-tailed `credible` interval of `t_f = −β₀/β₁` over draws with β₁ < 0, and the fraction of draws with β₁ ≥ 0. | unit |
| FR-003-18 | Ubiquitous | `slope_radar_los(displacement, radar_position, target_position)` shall return the line-of-sight displacement `d = u·ê` in m with `ê = (target − radar)/‖target − radar‖`, positive for motion away from the radar (range increase), for arrays of 3-vectors in the last axis that broadcast. | unit |
| FR-003-19 | Ubiquitous | `los_phase(los_displacement, wavelength, noise_sd=0, rng=None)` shall return the unwrapped interferometric phase `Δφ = 4π·d/λ` in rad (plus Gaussian noise of `noise_sd` rad drawn from `rng` when `noise_sd > 0`); `wrap_phase(phase)` shall map to (−π, π]; `los_from_phase(phase, wavelength)` shall return `λ·Δφ/(4π)`; and `max_unambiguous_los_step(wavelength)` shall return `λ/4`. | unit |
| FR-003-20 | Unwanted | If any argument violates its physical domain in Table 7.2, then the function shall raise `InputError` naming that argument (foundation FR-000-14). | hostile |
| FR-003-21 | Unwanted | If any argument trips a unit tripwire in Table 7.3, then the function shall emit `ValidityWarning` naming the argument and the row and still return the result (foundation FR-000-16). | unit |
| FR-003-22 | Unwanted | If `bishop_simplified_fos` or `spencer_fos` does not converge within `max_iter` iterations (`max_iter` ≤ 10,000), then it shall raise `ConvergenceError` (foundation FR-000-17). | hostile |
| FR-003-23 | Unwanted | If `noise_sd > 0` is given without `rng`, if `prior_cov` is not a symmetric positive-definite 2×2 matrix or `prior_mean` not of length 2 when given, if `t` is not strictly increasing, if fewer than 3 samples are used, or if `n_samples` or `n_draws` is outside 1…10⁶ (100…10⁶ for `n_draws`), then the function shall raise `InputError` naming the argument. | hostile |
| FR-003-24 | Unwanted | If `method` is not `"bishop"` or `"spencer"`, or `application` is not `"slope"` or `"tunnel"`, then the function shall raise `InputError` listing the allowed values (foundation FR-000-15). | hostile |

## 4. Correctness properties

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-003-01 | Scaling `sigma3` and `sigma_ci` by k scales σ1, σc, σt, σcm, σ3max-derived cohesion by k and leaves `friction_angle` unchanged (metamorphic: unit-change invariance Pa ↔ MPa). | GSI ∈ [10, 100], mi ∈ [4, 33], D ∈ [0, 1], k ∈ [1e-6, 1e6] | TC-1 |
| P-003-02 | `mb` and `s` are strictly increasing in GSI and strictly decreasing in D; σ1 is strictly increasing in σ3 and GSI and decreasing in D; the equivalent friction angle is non-increasing in `sigma3_max` (metamorphic: monotonicity). | as P-003-01 | exact ordering |
| P-003-03 | GSI = 100 and D = 0 give s = 1, mb = mi and a = 1/2 (the intact-rock criterion), and `hoek_brown_sigma1` at σ3 = σt returns σt (identities). | — | TC-1 |
| P-003-04 | Scaling weight, cohesion and pore pressure by the same k leaves the Bishop and Spencer factors of safety and Spencer's θ unchanged (metamorphic: unit-change invariance N ↔ kN). | 3–200 slices, \|α\| < 60°, φ' ∈ [10°, 45°] | TC-3 |
| P-003-05 | The factors of safety are strictly increasing in cohesion and in friction angle and strictly decreasing in pore pressure (metamorphic: monotonicity). | as P-003-04 | exact ordering |
| P-003-06 | Permuting the slices, or splitting any slice into two slices of the same base angle with half its width, weight and the same pore pressure, leaves both factors of safety unchanged (metamorphic: permutation, refinement invariance). | as P-003-04 | TC-3 |
| P-003-07 | With φ' = 0 Bishop's F equals `Σ c'l/Σ W sin α`; with c' = 0, dry slices and all base angles equal to β it equals `tan φ'/tan β`; Spencer's moment equation at θ = 0 has Bishop's F as its root (analytical limits and identity). | as P-003-04 | TC-3 |
| P-003-08 | `monte_carlo_fos` with zero standard deviations returns the deterministic factor of safety for every sample; with φ' = 0 (F linear in c') its PoF matches `Φ((1 − μ_F)/σ_F)` when the truncation probability is below 1e-6; the same seed gives the same samples (metamorphic: degeneracy; analytical limit; determinism). | n = 20,000 | exact; TC-4; exact |
| P-003-09 | For a noise-free α = 2 Voight series, `inverse_velocity_ttf` returns the true t_f; shifting all times by τ shifts t_f by τ; scaling times by k and velocities by 1/k scales t_f by k; scaling velocities by k leaves t_f unchanged (metamorphic: exact recovery, shift, unit-change invariance, scale invariance). | t_f ∈ [1e4, 1e8] s, 3–1,000 samples, k ∈ [1e-3, 1e3] | TC-1 relative to t_f |
| P-003-10 | With a flat prior and known σ, the `bayesian_ttf` posterior mean equals the OLS fit and its covariance equals `σ²(XᵀX)⁻¹`; with known σ, adding a sample never increases `det Σ_N`; when P(β₁ ≥ 0) < 1e-9 the empirical CDF of the t_f draws at the analytical quantiles (roots of `(μ₀ + τμ₁)/√(Σ₀₀ + 2τΣ₀₁ + τ²Σ₁₁) = ∓z`) is within 4 binomial standard errors of the nominal level (analytical identity; monotonicity; analytical distribution). | 3–200 samples | TC-1; exact ordering; TC-4 |
| P-003-11 | `slope_radar_los` is invariant to a common rotation and translation of radar, target and displacement, linear in the displacement, bounded by ‖u‖ in magnitude, zero for displacement perpendicular to the line of sight, and changes sign with u (metamorphic: rigid-motion invariance, linearity, bound, symmetry). | positions in [−5e3, 5e3]³ m, ‖u‖ ≤ 1 m | TC-1 (atol 1e-15·‖u‖ for the perpendicular case) |
| P-003-12 | `wrap_phase` is 2π-periodic and idempotent and returns values in (−π, π]; `los_from_phase(los_phase(d, λ), λ) = d`; `wrap_phase(los_phase(d, λ)) = los_phase(d, λ)` exactly when \|d\| < λ/4 (metamorphic: periodicity, round trip, ambiguity limit). | \|φ\| ≤ 1e3 rad, λ ∈ [1e-3, 0.3] m | TC-1 (periodicity rtol 1e-12·\|φ\|) |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-003-01 | `bishop_simplified_fos` and `spencer_fos` on 200 slices; `monte_carlo_fos` (Bishop) with 10,000 samples on 50 slices; `bayesian_ttf` with 10,000 draws | ≤ 50 ms median each (foundation NFR-000-07) | `tools/bench.py` |
| NFR-003-02 | Closed-form functions of this module on scalar inputs | ≤ 1 ms median | `tools/bench.py` |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-003-01 | `src/minephys/knowledge/geotech.yaml` (rows of §7.5) | `contracts/knowledge-table.schema.json` (foundation DC-000-02) | this spec → `minephys.geotech`, docs generator, PitStudio knowledge pages |

## 7. Edge cases and assumptions

### 7.1 Signatures

| Function | Arguments [units] | Returns [units] | Shape |
|---|---|---|---|
| `hoek_brown_parameters` | gsi [1], mi [1], disturbance [1] | (mb [1], s [1], a [1]) | elementwise |
| `hoek_brown_sigma1` | sigma3 [Pa], sigma_ci [Pa], mb, s, a [1] | [Pa] | elementwise |
| `hoek_brown_uniaxial_strength`, `hoek_brown_tensile_strength`, `hoek_brown_rock_mass_strength` | sigma_ci [Pa], mb, s, a [1] | [Pa] | elementwise |
| `equivalent_mohr_coulomb` | sigma_ci [Pa], mb, s, a [1], sigma3_max [Pa] | (cohesion [Pa], friction_angle [rad]) | elementwise |
| `sigma3_max` | sigma_cm [Pa], unit_weight [N/m³], height [m], application | [Pa] | elementwise |
| `circular_slices` | surface_x, surface_z [m] (1-D, ≥ 2 points), center_x, center_z, radius [m], n_slices [count], unit_weight [N/m³], pore_pressure_ratio [1] | named arrays (width [m], weight [N/m], base_angle [rad], base_length [m], pore_pressure [Pa]) | aggregate |
| `bishop_simplified_fos` | width [m], weight [N/m], base_angle [rad], pore_pressure [Pa], cohesion [Pa], friction_angle [rad] (1-D per slice; cohesion and friction may be scalars) | [1] | aggregate, 1…10,000 slices |
| `spencer_fos` | as Bishop | (fos [1], theta [rad]) | aggregate, 2…10,000 slices |
| `monte_carlo_fos` | slices as Bishop, cohesion_mean, cohesion_sd [Pa], friction_mean, friction_sd [rad], n_samples [count], rng, method | [1] (n_samples) | aggregate |
| `probability_of_failure` | fos_samples [1], threshold [1] | (pof [1], standard_error [1], n [count]) | aggregate, ≥ 1 sample |
| `required_samples` | pof [1], relative_error [1] | count | elementwise |
| `voight_creep_series` | t [s] (1-D), failure_time [s], a [unit depends on α], alpha [1] | (velocity [m/s], displacement [m]) | aggregate (1-D, ≥ 1) |
| `inverse_velocity_ttf` | t [s], velocity [m/s] (1-D), window [count] | named result (failure_time [s], slope [1/m], intercept [s/m], r_squared [1], accelerating [bool], n_used [count]) | aggregate, 3…10⁶ samples |
| `bayesian_ttf` | t [s], velocity [m/s], rng, noise_sd [s/m], prior_mean (2), prior_cov (2×2), n_draws [count], credible [1], window [count] | named result | aggregate |
| `slope_radar_los` | displacement [m], radar_position [m], target_position [m] (last axis 3) | [m] | broadcast over leading axes |
| `los_phase`, `wrap_phase`, `los_from_phase`, `max_unambiguous_los_step` | los_displacement [m], wavelength [m], phase [rad], noise_sd [rad], rng | [rad] or [m] | elementwise |

`A` in `voight_creep_series` has units (m/s)^{1−α}/s (1/m for α = 2).

### 7.2 Physical domain (violations raise `InputError`, FR-003-20)

| Argument | Domain |
|---|---|
| gsi | 0 < GSI ≤ 100 |
| mi, sigma_ci, mb, sigma_cm, unit_weight, height, radius, width, failure_time, a (Voight), wavelength, relative_error | > 0 |
| disturbance | 0 ≤ D ≤ 1 |
| s | 0 < s ≤ 1 |
| a (Hoek–Brown) | 1/2 ≤ a ≤ 2/3 |
| sigma3_max, weight, pore_pressure, cohesion, pore_pressure_ratio, cohesion_mean, the two standard deviations, noise_sd | ≥ 0 (`pore_pressure_ratio` < 1) |
| base_angle | −π/2 < α < π/2 |
| friction_angle, friction_mean | 0 ≤ φ' < π/2 |
| alpha (Voight) | > 1 |
| t (Voight) | every t < failure_time |
| velocity | > 0 |
| pof | 0 < p < 1 |
| credible | 0 < q < 1 |
| radar and target positions | distinct (‖target − radar‖ > 0) |

### 7.3 Unit tripwires (warn, FR-003-21; design choices of this spec, not sourced limits)

| Row | Argument | Warns when | Likely mistake |
|---|---|---|---|
| `tripwire_sigma_ci_min`, `tripwire_sigma_ci_max` | sigma_ci | < 1 × 10⁵ Pa or > 1 × 10⁹ Pa | MPa passed as Pa, or kPa as Pa |
| `tripwire_cohesion_min` | cohesion, cohesion_mean | 0 < c' < 100 Pa | kPa passed as Pa |
| `tripwire_unit_weight_min` | unit_weight | < 1,000 N/m³ | kN/m³ passed as N/m³ |
| `tripwire_friction_angle_max` | friction_angle, friction_mean | > 1.2 rad (68.8°) | check the angle |
| `tripwire_slope_velocity_max` | velocity | > 1 × 10⁻² m/s | mm/day passed as m/s |
| `tripwire_wavelength_range` | wavelength | < 1 × 10⁻⁴ m or > 1 m | mm passed as m |

### 7.4 Worked values

Published worked examples and benchmarks (values as printed; tolerance TC-2 unless stated):

| Source (page) | Inputs | Printed result |
|---|---|---|
| Hoek, Carranza-Torres and Corkum 2002, p. 271 (PDF p. 6) | σci = 50 MPa, mi = 10, GSI = 45; slope 100 m high, D = 1 | φ' = 27.61°, c' = 0.35 MPa |
| same | same rock, tunnel at 100 m depth, D = 0 | φ' = 47.16°, c' = 0.58 MPa |
| Rocscience Slide hand calculation #1, Table 1 p. 1, result p. 9 | 7 slices, b = 2.5 m, mid-heights 0.8, 2.3, 3.3, 3.9, 4.1, 3.6, 1.65 m, α = −9, 0.5, 9, 18.5, 28, 39, 52°, c' = 20 kPa, φ' = 20°, γ = 20 kN/m³, dry (W = γ·b·h) | Bishop F = 2.113 |
| Fredlund and Krahn 1977, as Slide verification problem #21, pp. 91–92 | ground (ft) (0, 60), (60, 60), (140, 20), (180, 20); circle centre (120, 90), R = 80 ft; c' = 600 psf, φ' = 20°, γ = 120 pcf | dry: Bishop 2.080 (F&K) / 2.079 (Slide), Spencer 2.073 / 2.075; r_u = 0.25: Bishop 1.766 / 1.763 |

The 2002 example prints no unit weight; γ = 0.027 MN/m³ (27 kN/m³) reproduces all four printed values to their last
digit (the spec writer's independent calculation: 27.610°, 0.3480 MPa, 47.155°, 0.5834 MPa), so the test passes
`unit_weight = 27,000 N/m³` and states that this input was inferred. For the Fredlund–Krahn benchmark the geometry is
read from a figure and the published codes differ by up to 0.003, so the tolerance is |ΔF| ≤ 0.01 with 100 uniform
slices (spec writer's independent values: Bishop 2.0753, Spencer 2.0715 at θ = 14.46°, Bishop with r_u = 0.25 1.7589).
Imperial inputs are converted with the foundation `units` rows (ft, lbf); F is dimensionless.

Hand calculations (spec writer, independent of the code; TC-1 or TC-3):

| Case | Value |
|---|---|
| `hoek_brown_parameters(50, 10, D)`, σci = 50 MPa | D = 0: mb = 1.676772, s = 3.865920 × 10⁻³, a = 0.505734, σ1(σ3 = 1 MPa) = 10.48924 MPa, σc = 3.01136 MPa, σt = −0.115279 MPa; D = 0.7: mb = 0.641037, σ1 = 6.67494 MPa; D = 1: mb = 0.281157, σ1 = 4.71751 MPa |
| three slices b = 2 m, W = (60, 120, 80) kN/m, α = (5°, 25°, 50°), c' = 5 kPa, φ' = 25°, dry | Bishop 1.2842941; Spencer 1.2775177 at θ = 27.0414°; with u = (0, 20, 10) kPa: Bishop 1.0026751, Spencer 1.0013315 |
| three slices b = 2 m, W = (40, 80, 50) kN/m, α = (−10°, 15°, 40°), c' = 10 kPa, φ' = 0 | F = Σc'l/ΣW sin α = 1.4623899 |
| c' = 0, φ' = 30°, all α = 20°, dry | F = tan 30°/tan 20° = 1.5862568 |
| Monte Carlo on the φ' = 0 slices with c' ~ N(10 kPa, 2 kPa), n = 20,000 | μ_F = 1.4623899, σ_F = 0.2924780, PoF = Φ(−1.58094) = 0.056946 (4 SE = 0.0066) |
| `required_samples(0.05, 0.1)` | 1,900 |
| Voight α = 2, A = 10 m⁻¹, t_f = 864,000 s (10 days) | v(0) = 1.1574074 × 10⁻⁷ m/s (10 mm/day); displacement from day 0 to day 6 = 0.091629073 m |
| `inverse_velocity_ttf` on that series at days 0…6 | failure_time = 864,000 s, slope = −10 m⁻¹, intercept = 8.64 × 10⁶ s/m, r² = 1 |
| `bayesian_ttf` on the same series, flat prior, `noise_sd = 4.32e4` s/m | posterior covariance diag (8.66468571 × 10⁸, 8.92857143 × 10⁻³), median t_f = 864,000 s, 5 % and 95 % quantiles 854,367.67 s and 873,924.60 s (analytical, P-003-10) |
| radar at the origin, target at (1000, 0, 0) m, u = (−0.01, 0.01, 0) m, λ = 0.0175 m | d = −0.01 m (toward the radar); Δφ = −7.1807832 rad; wrapped −0.8975979 rad; λ/4 = 4.375 mm |
| u = 0.02 m at 60° to the line of sight | d = 0.01 m |
| 50.8 mm/day sampled 240 times a day, λ = 0.0175 m | 0.21167 mm per scan, 0.15199 rad per scan: no wrapping |

### 7.5 Knowledge rows (DC-003-01)

| Row id | Value | Units | Role | Citation, page | Verification |
|---|---|---|---|---|---|
| `hb_mb_gsi_denominator_constant`, `hb_mb_disturbance_coefficient` | 28, 14 | 1 | model_constant | Hoek, Carranza-Torres and Corkum 2002, eq. 3, pp. 267–268 (PDF pp. 2–3) | verified (2026-10-06) |
| `hb_s_gsi_denominator_constant`, `hb_s_disturbance_coefficient` | 9, 3 | 1 | model_constant | same, eq. 4, pp. 267–268 | verified |
| `hb_a_gsi_scale`, `hb_a_offset_exponent` | 15, "20/3" | 1 | model_constant | same, eq. 5, pp. 267–268 (identical in Hoek and Brown 2019, eqs. 4–6, in-press p. 2) | verified |
| `hb_sigma3max_slope_coefficient`, `hb_sigma3max_slope_exponent` | 0.72, −0.91 | 1 | model_constant | same, eq. 19, p. 270 | verified |
| `hb_sigma3max_tunnel_coefficient`, `hb_sigma3max_tunnel_exponent` | 0.47, −0.94 | 1 | model_constant | same, eq. 18, p. 270 | verified |
| `hb_disturbance_open_pit_production_blasting` | 1.0 | 1 | parameter | same, Table 1, p. 272 (PDF p. 7); Hoek and Brown 2019, Table 2 (in-press p. 9) | verified |
| `hb_disturbance_open_pit_mechanical_excavation` | 0.7 | 1 | parameter | same | verified |
| `gbsar_ku_band_wavelength` | 0.0175 | m | parameter | Wolff et al. 2023 (preprint), p. 8 ("Ku-band with a wavelength equal to 1.75 cm") | verified (not a default) |
| `tripwire_*` (Table 7.3) | as listed | as listed | limit | this specification, §7.3 | UNVERIFIED (design choice, not a measurement) |

The phase relation `Δφ = 4π(R₂ − R₁)/λ` (no minus sign; positive phase = range increase) and the λ/4 ambiguity limit
are read on Monserrat, Crosetto and Luzi 2014, eqs. 4 and 7 (accepted manuscript pp. 4 and 9); they carry no constant
other than 4π. Bishop's equation is read on the Rocscience hand-calculation note (eqs. 4–6, p. 3). Spencer's slice
equation (FR-003-10) was not read on a primary source (the sources reached were blocked); it carries no constant, and
its oracles are the θ = 0 identity and the Fredlund–Krahn benchmark.

### 7.6 Assumptions
- Plane strain; weights per metre of slope; one circular surface given by the caller (no critical-surface search).
- Pore pressure enters as a given value per slice or through `r_u`; no water table, seepage or tension crack.
- Hoek–Brown strength enters limit equilibrium only through the caller (for example `equivalent_mohr_coulomb` at the
  slope's `sigma3_max`); the conversion is the 2002 edition's, an approximation over the stress range.
- The Monte-Carlo analysis keeps the slip surface fixed; this underestimates PoF compared with a per-sample critical
  surface, as the theory page states.
- Inverse velocity assumes the terminal accelerating stage with α ≈ 2 (Carlà et al. 2017 note that α is frequently
  near 2); smoothing of noisy velocities (their short and long moving averages) is the caller's choice.
- The radar model is geometric and phase-only: no atmosphere, focusing or spatial unwrapping; temporal unwrapping is
  the caller's.

## 8. Clarifications log
- **Resolved — radar sign convention.** Monserrat et al. 2014 (eq. 4) write `Δφ = 4π(R₂ − R₁)/λ` without a minus
  sign, so positive phase means a range increase. The library adopts it: `d = u·ê` with `ê` from radar to target, and
  `Δφ = +4πd/λ`. The PitStudio theory page on slopes writes `d = −(λ/4π)Δφ`; the docs left the sign to the
  specification, and this spec pins it to the primary source.
- **Resolved — open-pit disturbance factor.** D = 1.0 (production blasting) and D = 0.7 (mechanical excavation) are
  verified in Table 1 of the 2002 edition and Table 2 of the 2018 edition; they are documented rows, not defaults
  (`disturbance` is required).
- **Resolved — Hoek–Brown to Mohr–Coulomb conversion.** The 2002 edition's eqs. 12–13 with σ3max from eq. 19 (slopes)
  or eq. 18 (tunnels) are the conversion; the docs left it open.
- **Resolved — Bayesian TTF formulation.** A conjugate Gaussian linear model on `1/v` with a flat default prior; a
  vague `N(0, 10²I)` prior as on the theory page is unit-dependent, so the default is the flat limit and any proper
  prior is explicit.
- **Resolved — user stories as table rows.** Stories are table rows so that `tools/trace.py` defines their IDs.
