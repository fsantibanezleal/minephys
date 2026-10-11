# Plan 001 — Haulage models (`minephys.haulage`)
Spec: ./spec.md

## Summary
One sub-package `src/minephys/haulage/` with three private modules behind a single public `__init__`:
`_road.py` (resistances, force, speeds, travel and cycle time: FR-001-01…10), `_energy.py` (segment and cycle energy,
fuel, CO₂, trolley, battery-electric: FR-001-11…17) and `_queues.py` (match factor, M/M/c, finite-source queue, MVA:
FR-001-18…21). All inputs pass through the foundation validators (FR-001-22…26); constants come from `haulage.yaml`
and the foundation `units` table (DC-001-01). The queue functions are the exact oracles for the consumers' DES.

## Technical context
Runtime: CPython 3.12–3.14, Pyodide, Kit (foundation) · NumPy + PyYAML only · no new dependency · target: wheel.

## Constitution check

| Principle | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | CO₂ factor verified on its primary page; rolling-resistance guidance rows are UNVERIFIED and never defaults; tripwires are labelled design choices |
| 3 Acceptance-test-first | yes | every task below is a `[red]`/`[green]` pair |
| 4 Independent oracles | yes | analytical identities and hand calculations (spec §7.4); the MVA ↔ finite-source identity and the Erlang-B form are independent formulas |
| 5 Determinism and tolerances | yes | no randomness; tolerance classes TC-0, TC-1, TC-2 |
| 6 Purity and portability | yes | pure NumPy; the queue sums use log-space accumulation, no SciPy |
| 7 SI units | yes | fractions for grades and resistances, 1/s for rates, J, m³, kg/J; tripwires catch the usual unit slips |
| 8 Stable API | yes | names follow the planned API in `docs/reference/README.md`, plus `segment_travel_time`, `required_force` arguments fixed here |
| 9 Licence hygiene | yes | no OEM chart reproduced; EPA document is a US Government work |

## Design

| Component | Requirements | Notes |
|---|---|---|
| `_road.grade_resistance`, `total_resistance`, `required_force` | FR-001-01…03 | exact `x/√(1+x²)` avoids `sin(arctan x)` round-off |
| `_road.rimpull_limited_speed` | FR-001-04, -05, -07 | without drag: closed form; with drag: the unique positive root of `½ρC_DA v³ + m g TR v − ηP = 0` by bracketed Newton (foundation solver helper, tolerance 1e-12 relative), then the traction branch `v = √((T − m g TR)/(½ρC_DA))` when `F_req(v*) > T` |
| `_road.retarder_limited_speed` | FR-001-06, -07 | |
| `_road.loose_density`, `loading_passes`, `segment_travel_time`, `cycle_time` | FR-001-08…10 | integer rule: `n = ceil(q)` unless `|q − round(q)| ≤ 1e-12·q` |
| `_energy.*` | FR-001-11…17 | `bev_cycle_energy` delegates to `cycle_energy` |
| `_queues.match_factor` | FR-001-18 | |
| `_queues.mmc_queue` | FR-001-19, -24 | Erlang C from the stable Erlang-B recursion `B_k = a B_{k−1}/(k + a B_{k−1})`, `C = B/(1 − ρ(1 − B))` |
| `_queues.finite_source_queue` | FR-001-20 | terms `t_n = N!/(N−n)!·rⁿ` accumulated in log space (log-sum-exp), so N ≤ 100,000 cannot overflow |
| `_queues.mean_value_analysis` | FR-001-21, -26 | O(N·K) loop over n with NumPy vectors over stations |
| validation | FR-001-22, -23, -25, -26 | domain table §7.2 and tripwire table §7.3 encoded once, read from rows |

Data flow: the theory diagram `docs/assets/diagrams/minephys-modules.svg` (haulage reads `knowledge`).

## Test strategy

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-001-01, FR-001-02 | unit | analytical (`sin(arctan 0.1)` = 0.0995037190209989; small-angle identity) | pytest |
| FR-001-03 | unit | hand calculation (spec §7.4: 470,719.2 N; drag and inertia terms) | pytest |
| FR-001-04, FR-001-05 | unit | hand calculation (§7.4 speeds, cubic root 3.8207366 m/s, stall) + docs' worked example with `g=9.81` at TC-2 | pytest |
| FR-001-06 | unit | hand calculation (§7.4: 7.9665329, 17.703406, 8.0162619 m/s) | pytest |
| FR-001-07 | hostile | analytical (unbounded speed) | pytest |
| FR-001-08, FR-001-09 | unit | hand calculation (§7.4 exact-multiple case = 3) | pytest |
| FR-001-10 | unit | analytical (sum, quotient) | pytest |
| FR-001-11, FR-001-12 | unit | hand calculation (§7.4 wheel and cycle energies) | pytest |
| FR-001-13, FR-001-14 | unit | published value (EPA 2025 Table 2 p. 2, 10.21 kg/US gal) + exact gallon definition; hand calculation 302.291 kg | pytest, `knowledge` marker |
| FR-001-15 | unit | analytical (product) | pytest |
| FR-001-16, FR-001-17 | unit | hand calculation (§7.4 trolley and BEV values) | pytest |
| FR-001-18 | unit | hand calculation (MF = 1.0) | pytest |
| FR-001-19, FR-001-24 | unit + hostile | hand calculation (§7.4) + analytical M/M/1 closed form | pytest |
| FR-001-20 | unit | hand calculation (§7.4 table) + analytical N = 1 limit `X = λμ/(λ+μ)` | pytest |
| FR-001-21 | unit | hand calculation (§7.4) + analytical identity with FR-001-20 | pytest |
| FR-001-22, FR-001-25, FR-001-26 | hostile | analytical (domain tables) | Hypothesis + foundation contract suite |
| FR-001-23 | unit | hand-chosen inputs on each side of every tripwire | `pytest.warns` |
| P-001-01 … P-001-13 | property / metamorphic | invariants stated in the spec | Hypothesis (`property_tests.ci_examples_per_test`) |
| NFR-001-01, NFR-001-02 | release | measurement | `tools/bench.py` |

Tolerances: TC-1 for every closed-form comparison; TC-2 for the docs' printed values; the Newton root (drag case) at
TC-3; integer outputs and orderings at TC-0. The finite-source sum is ill-conditioned only through overflow, which the
log-space form removes; P-001-10's bound is checked as an exact ordering.

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Log-space finite-source sum | N up to 100,000 overflows `N!/(N−n)!·rⁿ` in float64 | capping N at ~170 would refuse realistic MVA cross-checks |
| Integer tolerance in `loading_passes` | float64 swell arithmetic turns exact multiples into 3.0000000000000004 | plain `ceil` returns one pass too many |
