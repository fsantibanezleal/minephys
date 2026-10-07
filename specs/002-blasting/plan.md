# Plan 002 — Blasting models (`minephys.blasting`)
Spec: ./spec.md

## Summary
One sub-package `src/minephys/blasting/` with private modules `_design.py` (charge and powder factor: FR-002-01),
`_kuzram.py` (x50 variants, rock factor, uniformity: FR-002-02…04, -14, -18), `_distributions.py` (Rosin–Rammler,
Swebrec, KCO: FR-002-05…07, -15), `_vibration.py` (scaled distance, PPV, 30 CFR § 816.67: FR-002-08, -09) and
`_flyrock.py` (drag-free, Lundborg, RK4 trajectory: FR-002-10…13). Validation through the foundation helpers
(FR-002-16, -17); constants from `blasting.yaml` and the `units` table (DC-002-01).

## Technical context
Runtime: CPython 3.12–3.14, Pyodide, Kit (foundation) · NumPy + PyYAML only · dev-only test oracle: SciPy
(`scipy.integrate.solve_ivp`, DOP853) for drag trajectories, resolved and locked in the dev group, never a runtime
dependency · target: wheel.

## Constitution check

| Principle | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | Kuznetsov constants, the 2005 exponent, the 1987 uniformity index, the rock factor, the hardness factor and the 30 CFR limits verified on their primary pages; the 1983/1987 exponent, RDI and Lundborg rows are UNVERIFIED secondary transcriptions, flagged; no site constant is a default |
| 3 Acceptance-test-first | yes | each task is a `[red]`/`[green]` pair |
| 4 Independent oracles | yes | hand calculations from the verified equations; analytical identities (median, round trip, KCO slope match, square-root scaling, vacuum ballistics, vertical-drag closed form); the published Lundborg value; SciPy as a reference integrator |
| 5 Determinism and tolerances | yes | no randomness; TC-1, TC-2, TC-5 |
| 6 Purity and portability | yes | RK4 in NumPy; SciPy only in tests |
| 7 SI units | yes | sizes in m (Kuznetsov's cm converted), d in m (converted to mm inside the uniformity formula), PPV in m/s (in/s converted), charges in kg (lb converted), distances in m (ft converted) |
| 9 Licence hygiene | yes | the regulation is a US Government work; no paywalled table is reproduced |

## Design

| Component | Requirements | Notes |
|---|---|---|
| `_design` | FR-002-01 | |
| `_kuzram.kuznetsov_x50` | FR-002-02, -18 | exponent from the variant's row as an exact rational |
| `_kuzram.rock_factor`, `hardness_factor`, `rock_density_influence` | FR-002-03 | modulus and UCS converted Pa → GPa / MPa at the boundary |
| `_kuzram.uniformity_index` | FR-002-04, -14 | factors checked before multiplication so that the error names the violated factor |
| `_distributions` | FR-002-05…07, -15 | Swebrec evaluated as `1/(1 + exp(b·(ln ln(xmax/x) − ln ln(xmax/x50))))` for stability near xmax |
| `_vibration` | FR-002-08, -09, -18 | band lookup with `numpy.select` on distance in ft |
| `_flyrock.flyrock_trajectory` | FR-002-12, -13 | fixed-step RK4; cubic Hermite landing (exact for the drag-free quadratic trajectory); arrays preallocated to the step cap |

## Test strategy

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-002-01 | unit | hand calculation (spec §7.4: 300.41480 kg, 0.59606111 kg/m³) | pytest |
| FR-002-02 | unit | hand calculation from the verified equation (Cunningham 2005 eq. 1, p. 201): 0.29940630 m and 0.31295501 m; analytical identity at RWS = 115 | pytest, `knowledge` markers |
| FR-002-03 | unit | hand calculation from the verified equations (eq. 4 p. 204; HF p. 205): A = 4.65, HF = 10 and 30 | pytest |
| FR-002-04, FR-002-14 | unit + hostile | hand calculation from the verified 1987 form (eq. 3 p. 202): 1.1164546; analytical domain limits | pytest |
| FR-002-05, FR-002-06, FR-002-15 | unit + hostile | analytical (P(x50) = 0.5, P(xmax) = 1, inverse round trip) + hand calculation (§7.4 percentiles) | pytest |
| FR-002-07 | unit | analytical (slope match at x50, P-002-06) + hand calculation (b = 2.4940490) | pytest |
| FR-002-08 | unit | hand calculation (24.494897 m/kg^½; 5.9907197 × 10⁻³ m/s) | pytest |
| FR-002-09 | unit | published values (30 CFR § 816.67(d)(2)(i), (d)(3)(i)) + exact unit definitions: 149.94789 kg at 1,000 ft | pytest, `knowledge` markers |
| FR-002-10 | unit | analytical (vacuum range) | pytest |
| FR-002-11 | unit | published worked value (Szendrei and Tose 2022, p. 729: ≈ 760 m for a 5-inch hole) at TC-2 (3 significant figures) + hand calculation 760.24461 m | pytest |
| FR-002-12 | unit | analytical (no-drag parabola at TC-1; vertical launch with drag at TC-5) + reference implementation (SciPy DOP853, rtol 1e-11, for oblique drag cases, TC-5) | pytest |
| FR-002-13 | hostile | analytical (never-landing upward launch with tiny `max_time`; step cap) | pytest |
| FR-002-16, FR-002-17, FR-002-18 | hostile / unit | analytical (domain, validity and tripwire tables) | Hypothesis + foundation contract suite |
| P-002-01 … P-002-10 | property / metamorphic | invariants stated in the spec | Hypothesis |
| NFR-002-01, NFR-002-02 | release | measurement | `tools/bench.py` |

Tolerances: TC-1 for closed forms; TC-2 for the published Lundborg value; TC-5 for drag trajectories (RK4 at
Δt = 1 ms has a global error far below 1e-6 relative on these smooth trajectories); exact orderings for the
monotonicity properties.

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Default variant with an UNVERIFIED exponent | the approved plan and the theory page fix 19/30 as the default | defaulting to the verified 19/20 would contradict the plan; the status is flagged instead |
| SciPy in the dev group | an independent integrator for oblique drag trajectories, where no closed form exists | step-halving self-convergence is not an independent oracle |
