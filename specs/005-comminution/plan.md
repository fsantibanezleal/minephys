# Plan 005 — Comminution: Bond, Morrell, population balance, flotation kinetics and the mine-to-mill chain
Spec: ./spec.md

## Summary

`minephys.comminution` is a set of pure functions in seven private modules behind one public `__init__`. Each closed
form (Bond, Morrell, flotation, two-product) is a direct NumPy transcription of the equation in the spec with its
constants read through `minephys.knowledge.get_value` from `knowledge/comminution.yaml`. The population balance and the
crusher are small linear systems solved with NumPy only (matrix exponential by scaling and squaring; triangular
solves). The mine-to-mill chain composes the published pieces and adds no new physics. All inputs pass through the
foundation validators (`InputError`, `InputTypeError`, `ValidityWarning`). Every requirement is pinned first by tests
whose expected values come from the two guidelines' worked examples, analytical solutions or hand calculations.

## Technical context

Runtime: CPython 3.12–3.14, Pyodide and NVIDIA Kit (foundation) · NumPy and PyYAML only · no new dependency (the
quadrature and Runge–Kutta references are a few lines inside the tests) · unit factors from the foundation `units`
table · tests carry `@pytest.mark.req`, `@pytest.mark.oracle(kind, reference)` (FR-000-33) and, for verified rows,
`@pytest.mark.knowledge(id)` (FR-000-21).

## Constitution check

| Principle (constitution 2.0.0) | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | 21 rows verified on two readable guidelines; the Austin reference size is UNVERIFIED and warns on use; typical work indices are never defaults; validity limits warn |
| 2 Spec before code | yes | FR/P/NFR/SC/DC-005 rows; added names listed in the clarifications log |
| 3 Acceptance-test-first | yes | one `[red]`/`[green]` pair per task in `tasks.md` |
| 4 Independent oracles | yes | worked examples (with page), analytical solutions (Reid's three-class solution, quadrature, Swebrec closed form) and hand calculations; none from the code under test |
| 5 Determinism & explicit tolerances | yes | no randomness; TC-0, TC-1, TC-2 and two justified module tolerances (matrix functions, grid interpolation) |
| 6 Purity and portability | yes | own matrix exponential (no SciPy); no I/O at import; Pyodide smoke subset |
| 7 SI units at the API | yes | sizes in m, energies in J/kg, grindability in kg/rev; µm, g and kWh/t only inside, converted once |
| 8 Stable API | yes | planned names kept; additions documented |
| 9 Licence hygiene | yes | equations and a few printed numbers cited with page; no guideline text reproduced |
| 10 Simplicity | yes | functions and small named tuples; no solver framework |

## Design

| Component (`src/minephys/comminution/`) | Contents | Requirements |
|---|---|---|
| `_bond.py` | `bond_energy`, `bond_operating_work_index`, `bond_ball_mill_work_index` | FR-005-01 … 04, 32, P-005-01 … 03 |
| `_morrell.py` | `morrell_energy`, `morrell_tumbling_coarse`, `morrell_tumbling_fine`, `morrell_crusher`, `morrell_hpgr`, `morrell_size_distribution_correction`, `morrell_mib` | FR-005-05 … 12, 33, P-005-03 … 05 |
| `_pbm.py` | `pbm_batch_grinding` (scaling and squaring with a Padé approximant, valid for repeated selection values), `pbm_continuous_mill` (N unit-triangular solves), `austin_selection`, `austin_breakage` | FR-005-13 … 18, P-005-06 … 09 |
| `_flotation.py` | `flotation_first_order`, `klimpel_recovery` (uses `expm1` for small $kt$), `flotation_cell_recovery`, `two_product_recovery` | FR-005-19 … 23, P-005-10 … 12 |
| `_psd.py` | `passing_size`, `class_masses`, `cumulative_passing` | FR-005-24 … 26, P-005-14 |
| `_crusher.py` | `crusher_matrix_model` (unit lower-triangular solve), `whiten_classification` | FR-005-27 … 29, P-005-13 |
| `_chain.py` | `mine_to_mill_chain` returning `ChainResult(product_passing, f80, fines_fraction, specific_energy, throughput)` | FR-005-30, 31, P-005-15 |
| row access | `minephys.knowledge.get_value` for every constant (no literals beyond the allow-list) | FR-005-34, DC-005-01 |
| `knowledge/comminution.yaml`, `knowledge/catalogue/equations.yaml` (comminution entries), `knowledge/references.bib` (keys of §7) | data | DC-005-01, DC-005-02 |

Data flow of the chain (FR-005-30): blast passing curve on a size grid (from `minephys.blasting` or any source) →
`class_masses` → `crusher_matrix_model` → `cumulative_passing` → `passing_size` ($F_{80}$, fines) → `bond_energy` or
`morrell_tumbling_coarse` + `morrell_tumbling_fine` → $\dot m = P/W$. The module diagram is added to
`docs/assets/diagrams/` with the method page in the build phase.

## Test strategy

Tolerances (float64). Closed forms against hand calculations: **TC-1** (rtol 1e-12; ≤ 15 operations including `pow`,
`sqrt`, `exp`, well-conditioned). Sums of three closed forms (P-005-03, P-005-04): rtol 1e-11. Printed values: **TC-2**
(± 0.05 kWh/t for one decimal, ± 0.005 for two; totals ± 0.1 kWh/t because the guideline adds rounded stage values).
Matrix functions: **rtol 1e-10, atol 1e-13** (scaling-and-squaring error grows with $\|A\|t$; generators bound
$S_{\max}t \le 50$); against the fixed-step Runge–Kutta reference **TC-5** (rtol 1e-6, here met at 1e-8 with a step of
10⁻³/$S_{\max}$). Interpolated sizes on a grid: **rtol 2e-3** (hand-checked log-log interpolation error ≤ 4.3e-4 on a
400-point grid). Orderings and exact identities: **TC-0**.

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-005-01 | unit | hand calculation: $W_i$ = 15 kWh/t, $F_{80}$ = 2,000 µm, $P_{80}$ = 150 µm → 8.893347 kWh/t = 32,016.05 J/kg; worked example (`mcivor2016bondgmsg`, p. 2): 9.5 × (10/√1,000 − 10/√19,300) = 2.32, 9.8 × (…) = 4.77, 16.0 → 0.9, 14.5 → 3.4, 13.8 → 8.0 kWh/t; analytical limit: $W \to W_i$ as $F_{80} \to \infty$ at $P_{80}$ = 100 µm, $\lvert W - W_i\rvert \le 10 W_i/\sqrt{F_{80,\mu m}}$ | pytest |
| FR-005-02 | unit | worked example (pp. 1–2): 7.0 kWh/t, 2,500 → 212 µm gives 14.4; 7.09 → 9.70; 8.56 → 11.7; 12.3 → 14.1; 14.6 → 16.8 kWh/t | pytest |
| FR-005-03 | unit | worked example, test sheet (p. 11): 106 µm, 1.825 × 10⁻³ kg/rev, 2,746.1 → 79.7 µm → 10.0 kWh/st, 11.0 kWh/t; hand calculation 11.028663 kWh/t | pytest |
| FR-005-04, 12, 15, 18, 23, 26, 29, 31 | unit (hostile) | each hostile class of the row (NaN, ±inf, 0, negative, wrong order, wrong shape, unknown option, oversized, non-numeric) → `InputError` (or `InputTypeError`) whose `argument` attribute names the argument; plus the foundation cross-cutting contract checks (T-005-064) | pytest parametrised + Hypothesis |
| FR-005-05 | unit | hand calculation: $M_i$ = 20 kWh/t, 2,000 → 150 µm → 9.862056 kWh/t (exponents −0.297 and −0.29515) | pytest |
| FR-005-06, 07 | unit | worked example (`gmsg2016morrell`, Annex C, pp. 11–12): $W_a$ = 9.6 (100 mm, $K_1$ = 0.95), 4.5 (4 mm), 5.5 (6.5 mm); $W_b$ = 8.4 (106 µm); hand values 9.625169, 4.454749, 5.454933, 8.375604 kWh/t | pytest |
| FR-005-08 | unit | worked example: pebble crusher 52.5 → 12 mm open 1.13 (stage `"pebble"`, $S_c$ = 0.956 not applied; hand 1.132374); secondary 100 → 35 mm closed 0.4 ($S_c$ = 0.678499; hand 0.411598), open 0.5 (hand 0.489802); tertiary 35 → 6.5 mm closed 1.1 ($S_c$ = 1.172 → 1; hand 1.129098) | pytest |
| FR-005-09 | unit | worked example: HPGR 35 → 4 mm closed 2.4 ($S_h$ = 0.821944); hand 2.380690 kWh/t | pytest |
| FR-005-10 | unit | worked example: $W_s$ = 0.9 (6.5 mm vs 100 mm); hand 0.888597 kWh/t | pytest |
| FR-005-11 | unit | hand calculation of eq. 1 on the Bond test-sheet data (1.825 × 10⁻³ kg/rev): 13.976217 kWh/t | pytest |
| FR-005-13 | unit + property | analytical solution of the batch grinding equation (`reid1965batch`) derived by hand for the three-class mill $S$ = (0.5, 0.3, 0)/60 s⁻¹, $b_{21}$ = 0.6, $b_{31}$ = 0.4, $b_{32}$ = 1: at 60, 120, 300 s, $\mathbf m$ = (0.606531, 0.201431, 0.192038), (0.367879, 0.271398, 0.360722), (0.082085, 0.211568, 0.706347); repeated selection values: $m_2 = b_{21} S t e^{-St} m_1(0)$; general cases: fixed-step Runge–Kutta reference in the test | pytest + Hypothesis |
| FR-005-14 | unit + property | analytical: one tank, $\tau$ = 120 s on the mill above → (0.5, 0.1875, 0.3125); $N$ tanks: $m_1 = (1 + S_1\tau/N)^{-N}$ | pytest + Hypothesis |
| FR-005-16, 17 | unit + property | hand calculation of the written forms at three sizes; telescoping column sums = 1 | pytest + Hypothesis |
| FR-005-19, 21 | unit | hand calculation: $k$ = 1/60 s⁻¹, $R_\infty$ = 0.9, $t$ = 300 s → 0.893936; one cell $\tau$ = 300 s → 0.75 | pytest |
| FR-005-20 | unit + property | quadrature: the average of $R_\infty(1 - e^{-k't})$ over $k' \in [0, k]$ by the trapezoid rule on 2 × 10⁵ panels (0.721213 at $kt$ = 5, agreement 1e-9); series $R_\infty(u/2 - u^2/6 + u^3/24)$ for $u \le 10^{-4}$ | pytest + Hypothesis |
| FR-005-22 | unit | hand calculation: $f$ = 1 %, $c$ = 25 %, $t$ = 0.1 % → yield 0.0361446, recovery 0.903614 | pytest |
| FR-005-24, 25 | unit + property | analytical: Swebrec closed-form $x_{80} = x_{\max}(x_{50}/x_{\max})^{0.25^{1/b}}$ (0.70711 m for $x_{50}$ = 0.25 m, $x_{\max}$ = 2 m, $b$ = 2); exact grid points; exact round trip `cumulative_passing(class_masses(·))` | pytest + Hypothesis |
| FR-005-27 | unit + property | hand calculation of the sequential balance: $\mathbf f$ = (0.6, 0.3, 0.1), $c$ = (0.8, 0.4, 0), $b_{21}$ = 0.7, $b_{31}$ = 0.3, $b_{32}$ = 1 → $\mathbf p$ = (0.12, 0.3816, 0.4984); two classes with $c_1$ = 0.5 → (0.5, 0.5) | pytest + Hypothesis |
| FR-005-28 | unit | hand calculation: $k_3$ = 2 at the midpoint → 0.75; at $k_1$ → 0; at $k_2$ → 1 | pytest |
| FR-005-30 | unit + property | composition by hand of the already-pinned functions on a 3-class and a 400-point case; P-005-15 (Swebrec closed form with $C$ = 0) | pytest + Hypothesis |
| FR-005-32, 33 | unit | inputs on each side of 70 µm and 45 µm: `pytest.warns(ValidityWarning)` with `argument == "p80"` and the row id; the returned value equals the closed form | pytest |
| FR-005-34 | contract | analytical sensitivity: a fixture table with `bond_law_coefficient` = 20 doubles `bond_energy`; `morrell_ws_factor` = 0.38 doubles $W_s$; `morrell_ks_crusher` changed moves $S_c$ by the same ratio | pytest (fixture knowledge layout) |
| P-005-01 … 15 | property / metamorphic | the invariant itself (monotonicity, scaling, additivity, conservation, semigroup, limits) | Hypothesis (`property_tests.ci_examples_per_test`) |
| NFR-005-01 | contract | fresh-interpreter import audit: modules imported by `import minephys.comminution` ⊆ standard library ∪ {numpy, yaml, minephys} | pytest (subprocess) |
| NFR-005-02 | benchmark | reference sizes registered in `tools/bench.py` | `tools/bench.py` |
| NFR-005-03 | pyodide | smoke subset (one oracle per family) | Pyodide job |
| NFR-005-04 | contract | foundation model-card audit on `minephys.comminution.__all__` | pytest |
| SC-005-01 | unit | the printed values listed above | pytest |
| SC-005-02 | mutation | mutation score of the module | foundation mutation tool |

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Own matrix exponential (scaling and squaring) | SciPy is excluded from the runtime (constitution principle 6) | eigen-decomposition fails for repeated selection values, which are common (equal rates by design) |
| Stage-based $S_c$ (applied only to primary and secondary crushers) | the guideline states that tertiary and pebble crushers take unity, and its pebble example ($S_c$ would be 0.956) does not apply it | applying $\min(S_c, 1)$ everywhere contradicts the published 1.13 kWh/t |
| Strictly lower-triangular breakage (no self-breakage) | keeps $I - BC$ and the PBM well posed with exact mass conservation | self-breakage terms need an iterative solve and have no read source here |
| The chain's crusher parameters are inputs, not a closed-side-setting correlation | no correlation was read on a primary source | an unsourced correlation would be an unverified default inside a headline output |
