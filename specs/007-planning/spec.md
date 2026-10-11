# Spec 007 — Planning: block value, min-cut ultimate pit (up to 10⁵ blocks), nested pits, strip ratio, schedule NPV and Lane cut-off grades
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent

`minephys.planning` gives reference implementations of the classical strategic open-pit planning models on teaching-
to case-size instances (the min-cut up to 10⁵ blocks and 2 × 10⁶ arcs on a CPU):

- the block economic value (process or waste) and the break-even cut-off grade;
- block precedence arcs on a regular grid ("1-5" and "1-9" patterns);
- the ultimate pit as the maximum-weight closure of the precedence graph, solved exactly as a minimum $s$–$t$ cut by a
  pure-NumPy/Python max-flow, and nested pits over revenue factors;
- the strip ratio of a pit or a pushback;
- the net present value of a cash-flow series and of a block schedule, with precedence and capacity feasibility checks;
- Lane's limiting and balancing cut-off grades and the optimum cut-off for given capacities and opportunity cost.

The oracles are exhaustive enumeration and `networkx` (and OR-Tools where installed) in **tests only**: neither is a
runtime dependency.

**Who benefits:** students and planners who need an inspectable, exact solver for teaching-size block models;
PitStudio (case E1, shells and pushbacks, the pit design and the planning theory page), which uses this min-cut as its
only Python solver — so it must return the minimal maximum closure on instances of 10⁵ blocks in a stated CPU time
(NFR-007-06, P-007-10) — and ports the same algorithm to its web worker, checked against this reference.

**Out of scope:** full-size block models (more than 10⁵ blocks — use a dedicated solver), the parametric pseudoflow
algorithm, production-scheduling optimisation (the MILP is PitStudio's, solved with HiGHS; this module only evaluates
a given schedule), Lane's life-of-mine iteration of the opportunity cost, stockpiles, multiple metals and grade
uncertainty. MineLib instances are not redistributed and are not part of the default tests (share-alike licence,
availability). Results are educational, not reserve statements or economic advice.

## 2. User stories

### US-007-1 (P1) Ultimate pit and nested pits
As a student, I want the exact ultimate pit and its nested shells for a small block model with block values and
precedence arcs, so that I can see which blocks pay for their stripping. Independent test: on every instance of up to
16 blocks the pit equals the best closed set found by exhaustive enumeration.

### US-007-2 (P1) Block values and strip ratio
As a planner, I want block economic values with their destination, the break-even cut-off and the strip ratio of a pit
or pushback, so that I can build the inputs of the pit and read its stripping cost. Independent test: the four-block
worked example (three waste blocks over one ore block) gives the documented pit and strip ratio 3.

### US-007-3 (P1) Schedule NPV
As a planner, I want the NPV of a cash-flow series and of a block schedule, with the schedule checked against
precedence and capacity, so that I can compare schedules without trusting an infeasible one. Independent test: a
constant cash flow equals the annuity formula.

### US-007-4 (P2) Lane cut-off grades
As a mining engineer, I want Lane's limiting and balancing cut-off grades and the optimum cut-off for mine, plant and
market capacities, so that I can see why the optimum is not the break-even grade when capacities bind. Independent
test: the optimum equals the brute-force maximum of Lane's objective on a dense grade grid.

## 3. Functional requirements (EARS)

Conventions (000-foundation): mass in kg, time in s, grade as a mass fraction (kg metal per kg rock), prices and
costs in currency per kg (or per kg of metal) and fixed costs in currency per s (FR-000-08); every formula here is
homogeneous, so any consistent units give the same result (P-007-01, P-007-09). Elementwise functions follow
FR-000-07; block indices are int64; non-finite, shape, size, domain and option errors raise `minephys.InputError`
naming the argument (FR-000-10, FR-000-12 to FR-000-15) and wrong types (non-numeric values, non-boolean masks,
non-integer arcs or periods) `minephys.InputTypeError` (FR-000-11). The solvers here terminate exactly (max-flow) or by
interval halving to a fixed width (bisection), so no `ConvergenceError` can arise.

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-007-01 | Ubiquitous | `block_economic_value(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost)` shall return the value $v = \max\big(T[g\,y\,(p - s_r) - c_p],\,0\big) - T c_m$ and a boolean `processed` that is true exactly where $T[g\,y\,(p - s_r) - c_p] > 0$, within TC-1 of the hand calculation. | unit |
| FR-007-02 | Ubiquitous | `breakeven_cutoff_grade(processing_cost, price, selling_cost, recovery)` shall return $g_{be} = c_p / (y\,(p - s_r))$. | unit |
| FR-007-03 | Ubiquitous | `regular_grid_precedence(shape, pattern="1-5")` shall return the int64 array of arcs $(i, j)$ ("mining $i$ requires $j$") for a `(nx, ny, nz)` grid in C order with level 0 at the top, linking each block below the top level to the in-grid blocks one level up at offsets {(0,0), (±1,0), (0,±1)} for `"1-5"` or $\lvert\Delta x\rvert, \lvert\Delta y\rvert \le 1$ for `"1-9"`; the arc count shall be $(n_z - 1)[n_x n_y + 2(n_x - 1)n_y + 2n_x(n_y - 1)]$ and $(n_z - 1)(3n_x - 2)(3n_y - 2)$ respectively. | unit |
| FR-007-04 | Ubiquitous | `ultimate_pit_mincut(values, arcs)` shall return a boolean pit mask and its value $\sum_{i \in \text{pit}} v_i$, where the pit is the **smallest** maximum-weight closed set (the source side of the minimum cut that is reachable from $s$ in the residual network: arcs $s \to i$ of capacity $v_i$ for $v_i > 0$, $i \to t$ of capacity $-v_i$ for $v_i < 0$, and infinite-capacity precedence arcs). | unit + property |
| FR-007-05 | State | While all values are integers of magnitude ≤ 2³⁰ (so that every partial sum is exact in float64), `ultimate_pit_mincut` shall return exactly the exhaustive-enumeration and `networkx` pit (mask equality, value equality); for real values the value shall agree within atol 1e-9 × $\sum_i \lvert v_i\rvert$. | unit + property |
| FR-007-06 | Ubiquitous | `nested_pits(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost, arcs, revenue_factors)` shall return one pit mask per revenue factor $\lambda$, each the FR-007-04 pit for $v_i(\lambda) = \max\big(T_i[\lambda g_i y (p - s_r) - c_p], 0\big) - T_i c_m$. | unit + property |
| FR-007-07 | Unwanted | If `ultimate_pit_mincut`, `nested_pits` or `regular_grid_precedence` gets NaN/inf values, arcs that are not an `(m, 2)` integer array, an arc index out of range, a self-arc, more than 10⁵ blocks or more than 2 × 10⁶ arcs, an empty block set, an unknown `pattern`, a non-positive grid dimension, or revenue factors that are negative or non-finite, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-007-08 | Unwanted | If `block_economic_value` or `breakeven_cutoff_grade` gets NaN/inf, a negative tonnage or cost, a grade outside [0, 1], a recovery outside (0, 1], or a price not greater than the selling cost, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-007-09 | Ubiquitous | `strip_ratio(pit, tonnage, is_ore)` shall return the waste tonnage over the ore tonnage of the selected blocks, $\sum_{i \in \text{pit}, \neg\text{ore}} T_i / \sum_{i \in \text{pit}, \text{ore}} T_i$ (t/t); a pushback's incremental ratio is the strip ratio of `outer & ~inner`. | unit |
| FR-007-10 | Unwanted | If `strip_ratio` gets mismatched lengths, a negative or non-finite tonnage, a non-boolean mask, or a selection with zero ore tonnage, then it shall raise `InputError` (it shall not return inf or nan). | unit (hostile) |
| FR-007-11 | Ubiquitous | `npv(cash_flows, rate, timing="end")` shall return $\sum_{t=1}^{T} CF_t/(1 + r)^t$ for `"end"` and $\sum_{t=0}^{T-1} CF_t/(1 + r)^t$ for `"start"`, with $r$ the discount rate per period. | unit + property |
| FR-007-12 | Ubiquitous | `schedule_npv(periods, block_values, rate, arcs=None, tonnage=None, capacities=None)` shall aggregate the block values into per-period cash flows (period index $t \ge 0$, −1 = not mined) and return the end-of-period NPV and the cash-flow array. | unit |
| FR-007-13 | Unwanted | If `schedule_npv` is given arcs and a block is mined in a period earlier than a block it requires (or that block is not mined), or is given tonnage and capacities and a period's mined tonnage exceeds its capacity, then it shall raise `InputError` naming the first violated arc or period. | unit (hostile) |
| FR-007-14 | Unwanted | If `npv` or `schedule_npv` gets NaN/inf, a rate ≤ −1, an empty cash-flow series, an unknown `timing`, period indices below −1 or non-integer, or mismatched lengths, then the function shall raise `InputError` naming the argument. | unit (hostile) |
| FR-007-15 | Ubiquitous | `lane_cutoff_grades(grade_edges, tonnage, price, selling_cost, recovery, processing_cost, mining_cost, fixed_cost, mine_capacity, plant_capacity, market_capacity, opportunity_cost=0)` shall return the limiting cut-offs $g_m = h/((s - r)y)$, $g_c = (h + (f + F)/C)/((s - r)y)$, $g_r = h/((s - r - (f + F)/R)\,y)$ (`None` when the denominator is ≤ 0: no finite market-limited cut-off) and the balancing cut-offs $g_{mc}$: $x(g) = C/M$, $g_{mr}$: $q(g) = R/M$, $g_{cr}$: $q(g)/x(g) = R/C$ (`None` when no root lies in the grade range), where $x(g)$ is the ore fraction and $q(g)$ the recovered metal per unit of material of a grade–tonnage histogram whose tonnage is uniform in grade inside each bin. | unit |
| FR-007-16 | Ubiquitous | `lane_cutoff_grades` shall return the optimum cut-off $g^\ast$ that maximises Lane's objective $V(g) = (s - r)\,q(g) - h\,x(g) - m - (f + F)\max(1/M,\ x(g)/C,\ q(g)/R)$ over the grade range, chosen as the best of the in-range limiting and balancing cut-offs and the range ends (the smallest such grade on ties within 1e-12 relative), together with $V(g^\ast)$ and the name(s) of the binding capacity. | unit + property |
| FR-007-17 | Unwanted | If `lane_cutoff_grades` gets grade edges that are not strictly increasing and non-negative, tonnage that is negative, all zero or mismatched with the bins, more than 10⁵ bins, a capacity ≤ 0, a recovery outside (0, 1], a negative cost, a price not greater than the selling cost, or NaN/inf, then it shall raise `InputError` naming the argument. | unit (hostile) |

## 4. Correctness properties

Generators (Hypothesis, 200 examples in CI, 2,000 at release): random block models on grids up to 4 × 4 × 4 for the
exhaustive oracle (≤ 16 blocks after random removal) and up to 12 × 12 × 8 for the `networkx` oracle; integer values in
[−50, 50]; revenue factors in [0, 2]; grade histograms with 1–50 bins on [0, 0.05]; capacities log-uniform over
three decades; float64 values and int64 indices.

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-007-01 | Block value homogeneity and monotonicity: $v$ is linear in tonnage; expressing mass in t instead of kg (costs and prices per t) gives the same value; $v$ is non-decreasing in grade, price and recovery and non-increasing in each cost; `processed` ⇔ $g > g_{be}$. | valid inputs | TC-1 |
| P-007-02 | Closure feasibility: for every arc $(i, j)$, pit$[i]$ ⇒ pit$[j]$; and optimality: no closed set found by exhaustive enumeration has a larger value; the pit is contained in every optimal closed set (smallest). | ≤ 16 blocks | TC-0 |
| P-007-03 | Pit metamorphic relations: scaling all values by $\lambda > 0$ leaves the pit unchanged and scales its value by $\lambda$; adding $\delta > 0$ to one block's value never removes a block from the pit; raising the mining cost never adds one; relabelling blocks by a permutation (arcs relabelled) permutes the mask. | integer values | TC-0 |
| P-007-04 | Nested pits: for $\lambda_1 \le \lambda_2$, pit$(\lambda_1)$ ⊆ pit$(\lambda_2)$; pit(0) is empty when every block has positive mining cost. | $\lambda \in [0, 2]$ | TC-0 |
| P-007-05 | Strip ratio: invariant to scaling every tonnage by $\lambda$; swapping ore and waste labels gives 1/SR; for disjoint pushbacks, the total ratio is (W₁ + W₂)/(O₁ + O₂). | valid inputs | TC-1 |
| P-007-06 | NPV linearity and limits: NPV is linear in the cash flows; at $r = 0$ it is the sum; for non-negative flows with at least one positive flow it is strictly decreasing in $r$; delaying every flow by one period divides it by $(1 + r)$; `"start"` = (1 + r) × `"end"`. | $r \in (-0.5, 1]$ | TC-1 |
| P-007-07 | Schedule NPV consistency: `schedule_npv` equals `npv` of its own cash-flow array; moving a block to a later period (feasibly) with a positive value lowers the NPV when $r > 0$. | feasible schedules | TC-1 |
| P-007-08 | Lane optimality: $V(g^\ast) \ge V(g)$ for every $g$ of a 10⁶-point grid over the range; with $C, R \to \infty$ (10¹² × M) $g^\ast \to g_m$; $g_m \le g_c$ and $g_m \le g_r$; raising $f$ or $F$ never lowers $g_c$ or $g_r$. | histograms above | $V$: atol 1e-9 × $\lvert V\rvert$ (grid resolution) |
| P-007-10 | Minimal-closure metamorphic relation: for integer values $v$ and $n$ = number of blocks + 1, `ultimate_pit_mincut(v)` equals `ultimate_pit_mincut(n·v − 1)` (every value scaled by $n$ and lowered by 1), whose maximum closure is unique and is the minimal maximum closure of $v$; its value equals $n \cdot V - \lvert\text{pit}\rvert$ with $V$ the value of the pit of $v$. | integer values in [−50, 50]; grids up to 12 × 12 × 8 (CI) and the 10⁵-block instance of NFR-007-06 (`slow`) | TC-0 |
| P-007-09 | Lane unit invariance: changing the time unit (capacities and $f$, $F$ divided by $k$) or the mass unit (tonnage, capacities and per-mass prices and costs rescaled) leaves $g^\ast$ and the binding capacity unchanged. | $k \in [10^{-3}, 10^8]$ | rtol 1e-10 (bisection roots to 1e-14 of a bin width, rescaled) |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-007-01 | `minephys.planning` imports only the standard library, NumPy, PyYAML and `minephys` modules (foundation NFR-000-05); `networkx` and OR-Tools appear only under `tests/`. | 0 other top-level modules imported; 0 imports of them in `src/` | contract test (subprocess import audit + source scan) |
| NFR-007-02 | Latency (foundation NFR-000-07): closed forms on scalars; `ultimate_pit_mincut` and `nested_pits` (5 factors) at the reference size 6 × 6 × 6 blocks with "1-5" arcs; `lane_cutoff_grades` at 50 bins. | ≤ 1 ms; ≤ 50 ms median | `tools/bench.py` |
| NFR-007-03 | One worked-example oracle per function family runs in the Pyodide smoke subset (foundation FR-000-25). | 100 % pass | Pyodide job |
| NFR-007-04 | Every public function's docstring is a model card (foundation FR-000-09), including the instance-size limits and the oracle used in tests. | 100 % of `__all__` | foundation model-card audit |
| NFR-007-05 | `ultimate_pit_mincut` on a 22 × 22 × 21 grid (10,164 blocks, "1-5" arcs) stays teaching-friendly on CPython. | median of 3 runs ≤ 10 s on the CI runner | benchmark test (`slow`) |
| NFR-007-06 | `ultimate_pit_mincut` at the size cap: a 50 × 50 × 40 grid (100,000 blocks, "1-5" arcs, 479,700 arcs) with seeded integer values in [−50, 50] returns the minimal maximum closure (mask equal to the `networkx` source side of the minimum cut, value equal to the `networkx` cut value) on one CPU core of CPython 3.14. | median of 3 runs ≤ 60 s on the CI runner; peak resident memory ≤ 2 GB | benchmark test (`slow`) |
| SC-007-01 | Exactness: on 500 seeded integer instances the pit value equals the `networkx` minimum-cut value, and on every instance of ≤ 16 blocks the mask equals the exhaustive smallest optimal closure. | 100 % agreement | property tests |
| SC-007-02 | Mutation score on `minephys.planning`. | ≥ 0.80 (`mutation.numerical_core_min`) | mutation run |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-007-01 | planning entries of `src/minephys/knowledge/catalogue/equations.yaml` (block value, closure, min-cut reduction, strip ratio, NPV, Lane cut-offs) | `contracts/knowledge-equations.schema.json` (spec 008 DC-008-01) | this spec → knowledge export → PitStudio equation explorer |

## 7. Edge cases and assumptions

**Knowledge rows.** The planning models have no published constants: every economic and capacity parameter is an
input. The module therefore ships no `knowledge/planning.yaml` (the foundation requires at least one row per table);
its sources are recorded in its equation entries (DC-007-01) and the bibliography. The instance-size caps of FR-007-07
and FR-007-17 are design limits of this spec, written in the code's validation table, not published values.

**Sources and their status**

| Item | Source | Status |
|---|---|---|
| Maximum closure of a graph; reduction to a minimum cut | Picard (1976), Management Science 22(11):1268–1272, `picard1976closure` (publisher metadata and abstract read: a closure contains all successors of its members; a maximal closure is a closure of maximal value) | verified (definition); the reduction is re-derived in the PitStudio planning theory and in the plan's test strategy |
| Ultimate pit as maximum closure | Lerchs and Grossmann (1965), Trans. CIM 58(633):47–54, `lerchs1965optimum` | bibliographic, **UNVERIFIED** (not read); the tests do not depend on it (exhaustive enumeration is the oracle) |
| Pseudoflow and parametric nested cuts | Hochbaum (2008), Operations Research 56(4):992–1009, `hochbaum2008pseudoflow` (abstract read) | verified (context); not implemented |
| Lane's cut-off theory | Lane (1964), Colorado School of Mines Quarterly 59(4):811–829, `lane1964choosing`; Lane (1988), The Economic Definition of Ore, `lane1988economic` | bibliographic, **UNVERIFIED** (not read) |
| Lane's controlling-capacity rule (the binding stage is the one with the least value; the optimum maximises it) | Cetin and Dowd (2013), JSAIMM 113(8):659–665, pp. 660 and 663, `cetin2013gridsearch` | verified (read) |
| MineLib instances and formats | Espinoza et al. (2013), Annals of OR 206(1):93–114, `espinoza2013minelib` | context only; not used in default tests |

**Assumptions and edge cases**

- Lane's limiting cut-offs are not transcribed from the unread original; they are derived from the objective of
  FR-007-16 (which follows the verified controlling-capacity rule): each $v_k(g)$ has derivative
  $-\varphi(g)\,[\,(s - r)y g - h - \dots]$ with $\varphi \ge 0$ the grade density, so it is unimodal with its maximum
  at the corresponding limiting cut-off, and two $v_k$ cross exactly where their capacity times are equal (the balancing
  cut-offs). The candidate set of FR-007-16 therefore contains the maximiser whenever the density is positive; on
  zero-density gaps $V$ is flat and the smallest optimal grade is returned. The brute-force grid (P-007-08) is the
  oracle and does not depend on this argument.
- The opportunity cost $F$ (Lane: discount rate × value of the remaining reserve) is an input; the life-of-mine
  iteration that updates it is out of scope.
- `ultimate_pit_mincut` returns the smallest optimal pit: zero-value blocks that are not required are left out. This
  makes the result unique and equal to the `networkx` source side (nodes reachable from $s$ in the residual network).
- Real-valued block values can make floating-point ties between distinct closures; mask equality is required only
  for integer values (FR-007-05), and the value tolerance otherwise.
- Precedence arcs come from a slope rule chosen by the caller; "1-5" approximates a 45° wall on cubic blocks (PitStudio
  planning theory); geotechnical domain-specific angles are the caller's arcs.
- NPV uses end-of-period discounting by default (cash flow of period $t$, 0-based, discounted by $(1 + r)^{t+1}$);
  `"start"` is available for mid-life conventions the caller wants.
- The schedule feasibility check is a check, not an optimiser: it reports the first violation and computes nothing
  else.
- Instance size is capped at 10⁵ blocks and 2 × 10⁶ arcs (FR-007-07): every instance up to and including the cap is
  solved exactly (NFR-007-06 bounds the time at the cap); larger models need a dedicated solver. PitStudio's web worker
  carries its own limits.

**Bibliography keys used:** `picard1976closure` (https://doi.org/10.1287/mnsc.22.11.1268), `lerchs1965optimum`
(bibliographic), `hochbaum2008pseudoflow` (https://doi.org/10.1287/opre.1080.0524), `lane1964choosing`
(bibliographic), `lane1988economic` (bibliographic), `cetin2013gridsearch`
(https://www.saimm.co.za/Journal/v113n08p659.pdf), `espinoza2013minelib` (https://doi.org/10.1007/s10479-012-1258-3).

## 8. Clarifications log

- Resolved: the docs list `block_economic_value`, `lane_cutoff_grades`, `ultimate_pit_mincut`, `nested_pits`; this
  spec adds `breakeven_cutoff_grade`, `regular_grid_precedence`, `strip_ratio`, `npv` and `schedule_npv` (the plan's
  E1 KPIs are NPV and strip ratio). The reference page is updated in the build phase.
- Resolved: the PitStudio planning theory writes the recovery as $r$ in the block value and $y$ in Lane's formulas; this
  spec uses $y$ for recovery throughout and $s_r$ / $r$ for the selling cost, matching Lane's notation.
- Resolved: the theory page attributes the closure-to-cut reduction to Picard (1976) as "citation UNVERIFIED"; the
  publisher record (Management Science 22(11):1268–1272) and abstract were read, so the citation is verified; the
  Lerchs–Grossmann and Lane originals remain bibliographic.
- Resolved: Lane's formulas, "UNVERIFIED transcription — pinned at specification", are kept as derived forms (§7) with
  a brute-force oracle, rather than as a transcription of the unread original.
- Resolved: OR-Tools is optional in tests (skipped when not installed); `networkx` is the required test oracle, added
  to the `dev` dependency group only.
- Resolved (foundation alignment): errors are `InputError` / `InputTypeError`; "no finite cut-off" and "no balancing
  root" are returned as `None` rather than as inf or NaN; latency is measured at a small reference size through
  `tools/bench.py` (NFR-000-07), with the 10,164-block run kept as a separate teaching-size benchmark; tolerances cite
  the foundation classes.
- Integration 2026-10-07: PitStudio uses this min-cut as its only Python solver (case E1, pit design, browser parity
  goldens), so the spec now states the size it must handle and the result it must return: instances up to the cap of
  10⁵ blocks in ≤ 60 s on the CI runner's CPU (NFR-007-06, the same bound PitStudio records for its baked runs) and the
  minimal maximum closure (FR-007-04, with the new metamorphic check P-007-10: the penalised problem n·v − 1 has the
  minimal closure as its unique optimum). The title and intent no longer say "small". Task T-007-056.

## 9. Changes (only for features that modify earlier behaviour)
### ADDED Requirements
(none — new module)
### MODIFIED Requirements
(none)
### REMOVED Requirements
(none)
