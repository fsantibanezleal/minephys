# Plan 006 — Environment: AP-42 unpaved-road dust, Gaussian plume dispersion and Beer–Lambert dust attenuation for lidar
Spec: ./spec.md

## Summary

`minephys.environment` is a set of pure, vectorised closed forms in four private modules. The AP-42 function takes SI
arguments, converts once to the published units with the foundation `units` table, evaluates equation 1a and converts
the result back to kg per vehicle-metre; validity ranges warn through the foundation validators. The plume functions
take $\sigma_y$ and $\sigma_z$ directly so that the dispersion-coefficient choice is explicit; `pasquill_sigmas`
evaluates the ISC3 tables, stored one coefficient per knowledge row. The Beer–Lambert and lidar functions integrate
extinction along a path and classify the result with the thresholds of the mining-dust study. Every requirement is
pinned first by tests whose expected values come from AP-42's printed numbers, the ISC3 tables, analytical integrals or
hand calculations.

## Technical context

Runtime: CPython 3.12–3.14, Pyodide, NVIDIA Kit (foundation) · NumPy and PyYAML only · `math.erf` from the standard
library, vectorised with `numpy.frompyfunc` (no SciPy) · quadratures written in the tests with NumPy
(`numpy.trapezoid` on fine grids) · tests carry `req`, `oracle` (FR-000-33) and `knowledge` (FR-000-21) markers.

## Constitution check

| Principle (constitution 2.0.0) | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | every constant read on the primary EPA documents or the study's abstract; the one UNVERIFIED model constant warns on use; extrapolation beyond AP-42's ranges warns |
| 2 Spec before code | yes | FR/P/NFR/SC/DC-006 rows |
| 3 Acceptance-test-first | yes | one `[red]`/`[green]` pair per task |
| 4 Independent oracles | yes | AP-42 printed numbers, ISC3 tables, analytical integrals, quadratures and hand calculations |
| 5 Determinism & explicit tolerances | yes | no randomness; TC-0, TC-1, TC-2 and two quadrature tolerances justified below |
| 6 Purity and portability | yes | no SciPy; no I/O at import; Pyodide smoke subset |
| 7 SI units at the API | yes | fractions, kg, m, s; lb/VMT, short tons, mph and % only inside, converted once with exact definitions |
| 8 Stable API | yes | planned names kept; additions listed |
| 9 Licence hygiene | yes | US Government documents and one cited abstract; no copied text or figure |
| 10 Simplicity | yes | functions and named tuples only |

## Design

| Component (`src/minephys/environment/`) | Contents | Requirements |
|---|---|---|
| `_ap42.py` | `ap42_unpaved_emission_factor`, `ap42_unpaved_validity` (returns `Ap42Validity`), `fleet_mean_vehicle_weight`, `precipitation_correction`, `watering_control_efficiency`, `controlled_emission_factor` | FR-006-01 … 07, P-006-01 … 04 |
| `_dispersion.py` | `pasquill_sigmas` (ISC3 rural bands and urban Briggs), `line_emission_rate` | FR-006-08 … 10, 14, P-006-09 |
| `_plume.py` | `gaussian_plume` (ground reflection; optional lid series and well-mixed limit), `line_source_plume`, `finite_line_source_plume` | FR-006-11 … 14, P-006-05 … 08 |
| `_optics.py` | `mass_extinction_coefficient`, `extinction_coefficient`, `beer_lambert_transmittance`, `path_transmittance`, `lidar_dust_return` (returns `LidarDustReturn`) | FR-006-15 … 18, P-006-10 … 12 |
| row access | `minephys.knowledge.get_value` for every constant; the ISC3 band rows assembled once into arrays | FR-006-19, DC-006-01 |
| `knowledge/environment.yaml`, `knowledge/catalogue/equations.yaml` (environment entries), `knowledge/references.bib` | data | DC-006-01, DC-006-02 |

Data flow (PitStudio's haul-road dust case, for orientation): traffic (vehicles/s, fleet weights) →
`fleet_mean_vehicle_weight` → `ap42_unpaved_emission_factor` (with warnings) → `precipitation_correction` /
`controlled_emission_factor` → `line_emission_rate` → `line_source_plume` or `finite_line_source_plume` with
`pasquill_sigmas` → concentration → `extinction_coefficient` → `lidar_dust_return`.

## Test strategy

Tolerances (float64). Closed forms against hand calculations: **TC-1** (≤ 20 operations including `pow`, `exp`, `tan`,
`log`). Values printed by AP-42 with one decimal: **TC-2** (± 0.05 of the printed value); the printed conversion
281.9 g/VKT: **rtol 2e-4** (the exact factor is 281.849). Quadrature oracles: **rtol 1e-6** for the double integral of
P-006-07 (trapezoid on a 4,001 × 4,001 grid over ± 10 σ; discretisation error ≪ 1e-8, margin for the lid series) and
**rtol 1e-8** for the single integrals of P-006-08. Orderings, symmetries and states: **TC-0**.

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-006-01 | unit | hand calculation in published units, then converted: silt 0.10, 263,083.57 kg (290 short tons) → 0.995870 / 9.958701 / 33.739896 lb/VMT (PM2.5/PM10/PM30) = 2.806822 × 10⁻³ kg/m for PM10; silt 0.08, 181,436.95 kg (200 short tons) → PM10 6.892362 lb/VMT; reference point silt 0.12, 2,721.55 kg (3 short tons) → exactly $k$ (analytical) | pytest |
| FR-006-02 | unit | Table 13.2.2-3 bounds (inclusive) at the bounds, just inside and just outside (± 1 ulp of the converted bound) | pytest |
| FR-006-03 | unit | 320 short tons (290,299.12 kg) → `pytest.warns(ValidityWarning)` naming `mean_weight` and `ap42_range_weight`, value equal to the closed form; `strict=True` → `InputError` naming each failed argument | pytest |
| FR-006-04 | unit | AP-42 example (p. 13.2.2-6): 98 % 2-ton and 2 % 20-ton vehicles → 2.36 short tons, printed "2.4 tons" (TC-2) | pytest |
| FR-006-05 | unit | hand calculation: 9.958701 × 215/365 = 5.866084 lb/VMT at $P$ = 150 | pytest |
| FR-006-06 | unit | Figure 13.2.2-2 vertices and hand interpolation: $M$ = 1.5 → 0.375, 3.5 → 0.85, 5 → 0.95; AP-42 Table 13.2.2-5 (p. 13.2.2-16): 7.1 lb/VMT at 0/62/68/74/80 % → printed 7.1/2.7/2.3/1.8/1.4 (TC-2) | pytest |
| FR-006-07, 14, 18 | unit (hostile) | each hostile class of the row → `InputError` (non-numeric: `InputTypeError`) with the `argument` attribute; plus the foundation cross-cutting contract checks (T-006-054) | pytest parametrised + Hypothesis |
| FR-006-08 | unit | hand calculation: 2.806822 × 10⁻³ kg/m × 200/86,400 s⁻¹ = 6.497274 × 10⁻⁶ kg/(m·s) | pytest |
| FR-006-09 | unit | ISC3 Tables 1-1/1-2 by hand: class D at 1 km → σ_y = 68.126741 m, σ_z = 32.093 m; D at 0.5 km → 36.146194, 18.296893; C at 1 km → 103.113800, 61.141; F at 2 km → 63.675319, 21.627177; A at 0.2 km → 49.971379, 29.301954; A at 3.5 km → σ_z = 5,000 m; urban D at 1,000 m (Tables 1-3/1-4) → 135.224681, 122.788123; band-edge convention at 0.30 km (D) and 3.11 km (A) | pytest |
| FR-006-10 | unit | urban class D at 50 m → `pytest.warns(ValidityWarning)` with `argument == "x"`; at 100 m no warning | pytest |
| FR-006-11 | unit + property | hand calculation: $q$ = 10⁻³ kg/s, $u$ = 3 m/s, σ_y = 36 m, σ_z = 20 m, ground-level centreline: $h$ = 0 → $q/(\pi u \sigma_y \sigma_z)$ = 1.47365688 × 10⁻⁷ kg/m³; $h$ = 10 m → 1.30049763 × 10⁻⁷ kg/m³; P-006-07 by quadrature | pytest + Hypothesis |
| FR-006-12 | unit + property | analytical: eq. 1-51 well-mixed limit $V = \sqrt{2\pi}\sigma_z/z_i$ and continuity of the series towards it as σ_z/z_i → 1.6 (difference ≤ 1e-3 relative); flux over [0, $z_i$] = $q$ by quadrature; $h > z_i$ → 0 | pytest + Hypothesis |
| FR-006-13 | unit + property | analytical: $\int e^{-y^2/2\sigma_y^2}dy = \sqrt{2\pi}\sigma_y$ gives the infinite line; ground-level case $\sqrt{2/\pi}\,q_\ell/(u\sigma_z)$ = 8.64012 × 10⁻⁸ kg/m³ for $q_\ell$ = 6.497274 × 10⁻⁶ kg/(m·s), $u$ = 3, σ_z = 20; erf form against quadrature of the point kernel over the segment | pytest + Hypothesis |
| FR-006-15 | unit | analytical geometry: $Q_{ext}\,\pi D^2/4$ per particle over its mass $\rho_p \pi D^3/6$; $D$ = 10 µm, $\rho_p$ = 2,650 kg/m³, $Q_{ext}$ = 2 → 113.207547 m²/kg; 1 mg/m³ → β = 1.132075 × 10⁻⁴ m⁻¹ | pytest |
| FR-006-16 | unit + property | analytical: β = 1.132075 × 10⁻⁴ m⁻¹ over 50 m → $T$ = 0.994356; trapezoid exact for linear profiles (integral of a ramp by hand) | pytest + Hypothesis |
| FR-006-17 | unit | hand calculation at the published thresholds: optical depths 0.301105 (74 %), 0.342490 (71 %), 2.813411 (6 %), 3.912023 (2 %); β = 0.01 m⁻¹ uniform: 20 m → $T$ = 0.8187 unaffected; 40 m → 0.6703 degraded; 300 m → 0.0498 degraded (retroreflective) / lost (low reflectivity); 400 m → 0.0183 lost; a profile that is zero up to 15 m → leading edge 15 m | pytest |
| FR-006-19 | contract | analytical sensitivity: fixture `ap42_industrial_k_pm10` = 3.0 doubles $E$; `ap42_watering_ce_4` = 90 changes $CE(5)$ to 0.90; an ISC3 $(c, d)$ change moves σ_y as the formula predicts | pytest (fixture knowledge layout) |
| P-006-01 … 12 | property / metamorphic | the invariant itself (power-law scaling, unit invariance, size-class ratio, linearity, symmetry, reciprocity, flux conservation, multiplicativity, monotonicity) | Hypothesis |
| NFR-006-01 | contract | fresh-interpreter import audit | pytest (subprocess) |
| NFR-006-02 | benchmark | reference sizes registered in `tools/bench.py` | `tools/bench.py` |
| NFR-006-03 | pyodide | smoke subset | Pyodide job |
| NFR-006-04 | contract | foundation model-card audit on `minephys.environment.__all__` | pytest |
| SC-006-01 | unit | AP-42 printed numbers listed above | pytest |
| SC-006-02 | mutation | mutation score | foundation mutation tool |

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Range violations warn by default, `strict` opt-in error | haul trucks routinely exceed 290 short tons; raising by default would block the main use case, and the foundation makes validity a warning (FR-000-16) | silent extrapolation is forbidden by constitution principle 1 |
| Separate `ap42_unpaved_validity` returning arrays | vectorised callers need per-element flags, which a single warning per call cannot give | relying on warnings alone loses which elements extrapolate |
| ISC3 tables instead of a single Briggs rural formula set | ISC3 is a primary EPA source that could be read; the commonly quoted Briggs rural set was only available second-hand | a secondary transcription would stay UNVERIFIED |
| Thresholds applied to the one-way transmittance | the abstract speaks of "atmospheric transmittance" of the path | applying them to $T^2$ would double the optical depth without a source |
