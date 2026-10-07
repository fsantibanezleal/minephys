# Plan 007 — Planning: block value, min-cut ultimate pit (up to 10⁵ blocks), nested pits, strip ratio, schedule NPV and Lane cut-off grades
Spec: ./spec.md

## Summary

`minephys.planning` has four private modules. Block values, the break-even grade, the strip ratio and NPV are
vectorised closed forms. The ultimate pit builds the $s$–$t$ network of the closure problem and solves it with an own
max-flow (Dinic's algorithm on NumPy adjacency arrays, iterative so it is recursion-free in Pyodide); the pit is the set
reachable from $s$ in the residual network. Nested pits re-solve over the revenue factors. Lane's cut-offs evaluate the
grade–tonnage histogram analytically (uniform tonnage inside each bin) and find the balancing roots by bisection on
monotone functions. The oracles are exhaustive enumeration, `networkx` (and OR-Tools when installed), brute-force grids
and hand calculations, all inside the tests.

## Technical context

Runtime: CPython 3.12–3.14, Pyodide, NVIDIA Kit · runtime dependencies NumPy and PyYAML · test-only oracle `networkx`
(BSD-3-Clause, added to the `dev` group by T-007-002); OR-Tools optional, tests skip when it is absent · no recursion
deeper than 100 frames (Pyodide's stack is small).

## Constitution check

| Principle (constitution 2.0.0) | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | no published constants are needed; the Lane and Lerchs–Grossmann originals are unread and marked; derived forms are stated as derived; Picard and the controlling-capacity rule were read |
| 2 Spec before code | yes | FR/P/NFR/SC/DC-007 rows |
| 3 Acceptance-test-first | yes | one `[red]`/`[green]` pair per task |
| 4 Independent oracles | yes | exhaustive enumeration, `networkx` minimum cut, brute-force Lane grid, hand calculations |
| 5 Determinism & explicit tolerances | yes | deterministic algorithm; unique smallest optimal pit; TC-0 and TC-1 plus the justified tolerances below |
| 6 Purity and portability | yes | own max-flow, iterative (no deep recursion for Pyodide); `networkx` and OR-Tools test-only |
| 7 SI units at the API | yes | kg, s and mass fractions; every formula homogeneous (P-007-01, P-007-09) |
| 8 Stable API | yes | planned names kept; additions listed |
| 9 Licence hygiene | yes | `networkx` (BSD-3) test-only; MineLib (CC BY-SA) not redistributed and not in default tests |
| 10 Simplicity | yes | one max-flow algorithm; no LP/MILP solver in the library |

## Design

| Component (`src/minephys/planning/`) | Contents | Requirements |
|---|---|---|
| `_economics.py` | `block_economic_value` (returns `BlockValue(value, processed)`), `breakeven_cutoff_grade`, `strip_ratio`, `npv`, `schedule_npv` (returns `ScheduleNPV(npv, cash_flows)`) | FR-007-01, 02, 08 … 14, P-007-01, 05 … 07 |
| `_precedence.py` | `regular_grid_precedence` | FR-007-03, 07 |
| `_mincut.py` | network construction, Dinic max-flow (BFS levels + iterative blocking flow), residual reachability; `ultimate_pit_mincut` (returns `UltimatePit(mask, value)`), `nested_pits` | FR-007-04 … 07, P-007-02 … 04 |
| `_lane.py` | histogram functions $x(g)$, $q(g)$ (piecewise quadratic, closed form), bisection for balancing cut-offs, candidate evaluation; `lane_cutoff_grades` (returns `LaneCutoffs`) | FR-007-15 … 17, P-007-08, 09 |
| `knowledge/catalogue/equations.yaml` (planning entries), `knowledge/references.bib` | data | DC-007-01 |

The precedence arcs and network are kept as int64 arrays; capacities as float64 with `inf` for precedence arcs. The
residual reachability uses a strict positive-capacity test, so integer instances give exact masks.

## Test strategy

Tolerances. Closed forms against hand calculations: **TC-1** (a handful of operations). Integer min-cut instances:
**TC-0** (exact) equality of masks and values (all partial sums below 2⁵³). Real-valued instances: value
**atol 1e-9 × Σ|v|** (accumulated rounding over up to 10⁵ augmentations). Lane optimum against a 10⁶-point grid: the
grid's best value may sit up to one grid step from $g^\ast$, so $V(g^\ast) \ge V_{grid} - 10^{-9}\lvert V\rvert$ and
$\lvert g^\ast - g_{grid}\rvert \le$ one grid step. Bisection roots: **atol 1e-14 × bin width**.

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-007-01 | unit | hand calculation: $T$ = 10⁶ kg, $g$ = 0.01, $y$ = 0.85, $p - s_r$ = 8 per kg, $c_p$ = 0.01 per kg, $c_m$ = 0.002 per kg → processed, $v$ = 56,000; $g$ = 0.001 → waste, $v$ = −2,000 | pytest |
| FR-007-02 | unit | hand calculation: 0.01/(0.85 × 8) = 1.470588 × 10⁻³ (0.147 %, the PitStudio planning example) | pytest |
| FR-007-03 | unit | arc-count formulas by hand (3 × 3 × 2 "1-5" → 33 arcs; "1-9" → 49); explicit arc list of a 2 × 2 × 2 grid written by hand | pytest |
| FR-007-04, 05 | unit + property | worked example (PitStudio planning theory): three waste blocks of −1 over one ore block, $v_d$ = 5 → whole pit, value 2; $v_d$ = 2 → empty, value 0; $v_d$ = 3 → tie, smallest pit = empty; exhaustive enumeration of all closed subsets for ≤ 16 blocks (the smallest optimal closure is the intersection of all optimal closures); `networkx.minimum_cut` source side on integer instances up to 1,152 blocks | pytest + Hypothesis |
| FR-007-06 | unit + property | worked example (PitStudio planning theory) as inputs: unit tonnages, $c_p$ = 0, $c_m$ = 1, grade 0 for $a, b, c$ and $g\,y\,(p - s_r)$ = 6 for $d$, so $v_d(\lambda) = 6\lambda - 1$ → empty pit for $\lambda \le 2/3$ (at 2/3 the full pit ties at 0 and the smallest pit is empty), full pit for $\lambda > 2/3$; P-007-04 | pytest + Hypothesis |
| FR-007-07, 08, 10, 13, 14, 17 | unit (hostile) | each hostile class of the row → `InputError` (wrong types: `InputTypeError`) with the `argument` attribute (or the first violated arc / period); plus the foundation cross-cutting contract checks (T-007-054) | pytest parametrised + Hypothesis |
| FR-007-09 | unit | worked example with 1,000 t blocks: pit {a, b, c, d} → 3,000/1,000 = 3 | pytest |
| FR-007-11 | unit + property | annuity formula: 100 for 3 periods at 10 % → 100 (1 − 1.1⁻³)/0.1 = 248.685199; hand: (−500, 200, 300, 400) at 8 % → 240.666415 | pytest + Hypothesis |
| FR-007-12 | unit | hand aggregation of a 6-block schedule into 3 periods, then the annuity/hand NPV | pytest |
| FR-007-15 | unit | analytical, on a single bin with uniform grade on [0, 0.01] ($x(g) = 1 - 100g$, $q(g) = y(10^{-4} - g^2)/(2 \times 10^{-2})$): with $s$ = 10,000, $r$ = 2,000, $y$ = 0.9, $h$ = 2, $m$ = 0.5, $f$ = 300, $F$ = 0, $M$ = 100: $g_m$ = 2.777778 × 10⁻⁴; $C$ = 50 → $g_c$ = 1.111111 × 10⁻³, $g_{mc}$ = 5 × 10⁻³; $C$ = 95, $R$ = 0.2 → $g_r$ = 3.418803 × 10⁻⁴, $g_{mr}$ = 7.453560 × 10⁻³ (capacities per unit time; $R$ in metal mass, so it is 1,000 times smaller than in grade-per-mille units) | pytest |
| FR-007-16 | unit + property | brute force over 2 × 10⁶ grades on the same histogram (hand-computed): $C$ = 50, $R$ = 1 → $g^\ast$ = $g_c$ = 1.111111 × 10⁻³, $V$ = 27.944444, plant binds; $C$ = 95, $R$ = 1 → $g^\ast$ = $g_{mc}$ = 5 × 10⁻⁴, $V$ = 30.51, mine and plant bind; $C$ = 95, $R$ = 0.2 → $g^\ast$ = $g_r$ = 3.418803 × 10⁻⁴, $V$ = 26.784188, market binds; $C$ = 1,000, $R$ = 10 → $g^\ast$ = $g_m$ = 2.777778 × 10⁻⁴, $V$ = 30.527778, mine binds | pytest + Hypothesis |
| P-007-01 … 10 | property / metamorphic | the invariant itself (homogeneity, unit change, closure feasibility, monotone comparative statics, nesting, permutation, linearity, discount shift) | Hypothesis |
| NFR-007-01 | contract | fresh-interpreter import audit; `src/` contains no `networkx`/`ortools` import (source scan) | pytest |
| NFR-007-02 | benchmark | reference sizes registered in `tools/bench.py` | `tools/bench.py` |
| NFR-007-03 | pyodide | smoke subset | Pyodide job |
| NFR-007-04 | contract | foundation model-card audit on `minephys.planning.__all__` | pytest |
| NFR-007-05 | benchmark | wall clock, median of 3 | pytest `slow` |
| NFR-007-06, P-007-10 | benchmark + metamorphic | `networkx` minimum cut (reference implementation) on the 10⁵-block instance; the penalised problem n·v − 1 (unique optimum by construction); wall clock median of 3 and `resource`/`psutil` peak memory | pytest `slow`, Hypothesis |
| SC-007-01 | property | 500 seeded instances against `networkx`; all ≤ 16-block instances against enumeration | Hypothesis (fixed seeds) |
| SC-007-02 | mutation | mutation score | mutation tool of the foundation |

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Own Dinic max-flow instead of a library | the runtime may only use NumPy and PyYAML (constitution principle 6) | `networkx`/SciPy/OR-Tools at runtime would break the purity boundary |
| Smallest optimal pit as the defined output | makes the output unique and comparable bit-for-bit with the oracle and the TypeScript port | "any optimal pit" would make mask equality untestable on ties |
| Lane optimum by candidate evaluation, not the median rule | the candidate set is exact for unimodal stage values (derived in spec §7) and needs no unread transcription | Lane's median rule is a transcription of an unread source |
| Histogram with uniform tonnage per bin | gives continuous, monotone $x(g)$ and $q(g)$ with unique balancing roots | point masses per bin make balancing cut-offs ill-defined (step functions) |
