# Plan 003 — Geotechnical models (`minephys.geotech`)
Spec: ./spec.md

## Summary
One sub-package `src/minephys/geotech/` with private modules `_hoek_brown.py` (FR-003-01…06), `_lem.py` (slices,
Bishop, Spencer: FR-003-07…11, -22), `_pof.py` (Monte Carlo and PoF: FR-003-12, -13), `_creep.py` (Voight, inverse
velocity, Bayesian TTF: FR-003-14…17) and `_radar.py` (line of sight and phase: FR-003-18, -19). Validation through the
foundation helpers (FR-003-20, -21, -23, -24); constants from `geotech.yaml` (DC-003-01). The two LEM solvers share the
slice arrays, so `monte_carlo_fos` evaluates them vectorised over samples.

## Technical context
Runtime: CPython 3.12–3.14, Pyodide, Kit (foundation) · NumPy + PyYAML only · dev-only test oracle: pySlope 1.4.0
(MIT, Bishop only) as an optional cross-check, locked in the dev group, never a runtime dependency · target: wheel.

## Constitution check

| Principle | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | Hoek–Brown constants and D guidance verified on the 2002 and 2018 editions; Bishop's worked example and the Fredlund–Krahn benchmark are published; Spencer's slice equation is UNVERIFIED but has no constant |
| 3 Acceptance-test-first | yes | each task is a `[red]`/`[green]` pair |
| 4 Independent oracles | yes | published worked examples (Hoek 2002 p. 271; Slide hand calculation #1; Fredlund and Krahn via Slide #21), analytical limits (φ' = 0, infinite slope, θ = 0 identity, noise-free Voight, conjugate posterior, Fieller quantiles), pySlope as a reference implementation |
| 5 Determinism and tolerances | yes | seeded `rng` for Monte Carlo, Bayesian draws and phase noise; TC-1…TC-4 |
| 6 Purity and portability | yes | pure NumPy; 2×2 linear algebra by closed form; `erf` from `math` for the Gaussian CDF |
| 7 SI units | yes | Pa, N/m³, N/m, rad, m/s, s; the imperial benchmark is converted with the `units` rows; tripwires catch MPa, kPa, kN/m³ and mm/day slips |
| 9 Licence hygiene | yes | no table from Read and Stacey, Rocscience manuals or the standards is reproduced; benchmark inputs are cited facts |

## Design

| Component | Requirements | Notes |
|---|---|---|
| `_hoek_brown` | FR-003-01…06 | eq. numbers of the 2002 edition in the docstrings |
| `_lem.circular_slices` | FR-003-07, -08 | intersections by bracketed root on each polyline segment; equal widths between the two cuts; the sliding direction fixed by the sign of `Σ W sin α` |
| `_lem.bishop_simplified_fos` | FR-003-09, -11, -22 | fixed-point iteration from F = 1 (foundation solver helper); checks `m_α > 0` each step |
| `_lem.spencer_fos` | FR-003-10, -11, -22 | outer bracketed root in θ of `F_force(θ) − F_moment(θ)`; inner bracketed roots in F; starts from Bishop's F, which is the moment root at θ = 0 |
| `_pof.monte_carlo_fos`, `probability_of_failure`, `required_samples` | FR-003-12, -13 | truncated normals by rejection resampling from the same `Generator`; vectorised Bishop over samples |
| `_creep.voight_creep_series` | FR-003-14 | closed forms for α = 2 and α ≠ 2 |
| `_creep.inverse_velocity_ttf` | FR-003-15, -16 | centred OLS (subtract mean time) to keep the normal equations well conditioned for t ~ 1e6 s |
| `_creep.bayesian_ttf` | FR-003-17, -23 | closed-form 2×2 posterior; draws by Cholesky; quantiles by `numpy.quantile` (method `"linear"`) |
| `_radar` | FR-003-18, -19 | `wrap_phase(φ) = φ − 2π·ceil((φ − π)/(2π))` so that π maps to π and −π maps to π |

## Test strategy

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-003-01…05 | unit | published worked example: Hoek et al. 2002 p. 271 (φ' = 27.61°, c' = 0.35 MPa; φ' = 47.16°, c' = 0.58 MPa) at TC-2 with the inferred unit weight 27 kN/m³; hand calculation (GSI = 50 table, spec §7.4) at TC-1 | pytest, `knowledge` markers on the verified rows |
| FR-003-06 | hostile | analytical (tensile cut-off) | pytest |
| FR-003-07, FR-003-08 | unit + hostile | published benchmark: Fredlund and Krahn via Slide #21 pp. 91–92 (geometry → F within 0.01); analytical geometry (slice weights sum to the area of the circular segment × γ for a flat ground surface) | pytest |
| FR-003-09 | unit | published worked example: Slide hand calculation #1 (Table 1 p. 1 → 2.113, p. 9) at TC-2; analytical limits (P-003-07); reference implementation pySlope 1.4.0 on the same geometry (tolerance 0.01, discretisation-limited) | pytest |
| FR-003-10 | unit | analytical identity (θ = 0 moment root = Bishop); published benchmark Fredlund and Krahn Spencer 2.073 / 2.075 within 0.01; hand calculation (three slices, §7.4) at TC-3 | pytest |
| FR-003-11, FR-003-22 | hostile | analytical (negative driving moment; a constructed slice set with `m_α ≤ 0`; `max_iter=1`) | pytest |
| FR-003-12, FR-003-13 | unit | analytical (φ' = 0: PoF = Φ((1 − μ_F)/σ_F), TC-4; binomial standard error; `required_samples(0.05, 0.1)` = 1,900) | pytest |
| FR-003-14 | unit | analytical (closed-form solution of Voight's ODE; displacement = integral of velocity, checked by the derivative identity `dΩ/dt = v`) | pytest |
| FR-003-15, FR-003-16 | unit | analytical (noise-free series → t_f exactly; non-accelerating series → +inf) | pytest |
| FR-003-17 | unit | analytical (conjugate posterior formulas; Fieller-type quantiles of P-003-10) | pytest |
| FR-003-18, FR-003-19 | unit | published form: Monserrat et al. 2014 eq. 4 (sign) and eq. 7 (λ/4); analytical geometry (§7.4) | pytest |
| FR-003-20, FR-003-21, FR-003-23, FR-003-24 | hostile / unit | analytical (domain and tripwire tables) | Hypothesis + foundation contract suite |
| P-003-01 … P-003-12 | property / metamorphic | invariants stated in the spec | Hypothesis |
| NFR-003-01, NFR-003-02 | release | measurement | `tools/bench.py` |

Tolerances: TC-2 for printed published values (four significant figures: ±0.0005 on F = 2.113, ±0.005° on 27.61°,
±0.005 MPa on 0.35 MPa); |ΔF| ≤ 0.01 for the Fredlund–Krahn benchmark and pySlope (discretisation and figure-read
geometry, justified in spec §7.4); TC-3 for solver results against independent solutions; TC-4 for Monte Carlo.

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Spencer by nested bracketed roots | robust without SciPy; converges whenever both equations have roots in the bracket | Newton on (F, θ) jointly can diverge on steep toe slices |
| Flat prior by default in `bayesian_ttf` | a vague proper prior depends on the unit system | the docs' `N(0, 10²I)` prior changes meaning between days/mm and s/m |
| pySlope only in the dev group | an independent Bishop implementation for cross-checks | adding it at runtime breaks principle 6 |
