# Tasks 007 — Planning: block value, min-cut ultimate pit (up to 10⁵ blocks), nested pits, strip ratio, schedule NPV and Lane cut-off grades
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/007-planning/tests.lock <files>`).
Dependencies: the foundation validators (T-000-003) and the catalogue schema of spec 008 (T-008-001); T-007-002
precedes every task that uses the `networkx` oracle.

## Phase 1 — Setup
- [ ] T-007-001 (DC-007-01) planning entries of `knowledge/catalogue/equations.yaml` and the §7 bibliography entries — test: tests/contract/test_t_007_001_planning_knowledge.py
- [ ] T-007-002 add `networkx` to the `dev` dependency group (test-only oracle; `uv add --dev networkx`), lock, and record the version; no runtime change

## Phase 2 — US-007-2 (P1) Block values and strip ratio
- [ ] T-007-010 [US-007-2] (FR-007-01, FR-007-02, P-007-01) block economic value, destination and break-even cut-off — test: tests/unit/test_t_007_010_block_value.py, tests/property/test_t_007_010_block_value_properties.py
- [ ] T-007-011 [US-007-2] (FR-007-08) block-value guards — test: tests/unit/test_t_007_011_block_value_guards.py
- [ ] T-007-012 [US-007-2] (FR-007-09, P-007-05) strip ratio of pits and pushbacks — test: tests/unit/test_t_007_012_strip_ratio.py, tests/property/test_t_007_012_strip_ratio_properties.py
- [ ] T-007-013 [US-007-2] (FR-007-10) strip-ratio guards (zero ore raises) — test: tests/unit/test_t_007_013_strip_ratio_guards.py

## Phase 3 — US-007-1 (P1) Ultimate pit and nested pits
- [ ] T-007-020 [US-007-1] (FR-007-03) regular-grid precedence arcs and their counts — test: tests/unit/test_t_007_020_precedence.py
- [ ] T-007-021 [US-007-1] (FR-007-04, FR-007-05, P-007-02, P-007-03, SC-007-01) min-cut ultimate pit against the worked example, exhaustive enumeration and `networkx` (OR-Tools when installed) — test: tests/unit/test_t_007_021_mincut.py, tests/property/test_t_007_021_mincut_oracles.py, tests/metamorphic/test_t_007_021_mincut_mr.py
- [ ] T-007-022 [US-007-1] (FR-007-06, P-007-04) nested pits over revenue factors — test: tests/unit/test_t_007_022_nested_pits.py, tests/property/test_t_007_022_nested_properties.py
- [ ] T-007-023 [US-007-1] (FR-007-07) min-cut, nested-pit and precedence guards (oversized instances, bad arcs, unknown pattern) — test: tests/unit/test_t_007_023_mincut_guards.py

## Phase 4 — US-007-3 (P1) Schedule NPV
- [ ] T-007-030 [US-007-3] (FR-007-11, P-007-06) NPV of a cash-flow series — test: tests/unit/test_t_007_030_npv.py, tests/property/test_t_007_030_npv_properties.py
- [ ] T-007-031 [US-007-3] (FR-007-12, P-007-07) schedule NPV and cash-flow aggregation — test: tests/unit/test_t_007_031_schedule_npv.py, tests/property/test_t_007_031_schedule_properties.py
- [ ] T-007-032 [US-007-3] (FR-007-13, FR-007-14) infeasible schedules and NPV guards — test: tests/unit/test_t_007_032_schedule_guards.py

## Phase 5 — US-007-4 (P2) Lane cut-off grades
- [ ] T-007-040 [US-007-4] (FR-007-15) limiting and balancing cut-offs on analytical histograms — test: tests/unit/test_t_007_040_lane_cutoffs.py
- [ ] T-007-041 [US-007-4] (FR-007-16, P-007-08, P-007-09) optimum cut-off against the brute-force grid, binding capacity and unit invariance — test: tests/unit/test_t_007_041_lane_optimum.py, tests/property/test_t_007_041_lane_properties.py
- [ ] T-007-042 [US-007-4] (FR-007-17) Lane guards — test: tests/unit/test_t_007_042_lane_guards.py

## Phase 6 — Non-functional and cross-cutting contract
- [ ] T-007-050 (NFR-007-01) import audit and source scan (no `networkx`/`ortools` in `src/`) — test: tests/contract/test_t_007_050_imports.py
- [ ] T-007-051 (NFR-007-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_007_051_bench_registry.py
- [ ] T-007-052 (NFR-007-03) one worked-example oracle per family in the Pyodide smoke subset — test: tests/pyodide/test_t_007_052_planning_smoke.py
- [ ] T-007-053 (NFR-007-04) model-card audit over `minephys.planning.__all__` — test: tests/contract/test_t_007_053_model_cards.py
- [ ] T-007-054 [US-007-1] (FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, P-000-01, P-000-02, P-000-03) the foundation cross-cutting contract checks (T-000-010) on every `minephys.planning` function — test: tests/property/test_t_007_054_planning_contract.py
- [ ] T-007-055 (NFR-007-05) 10,164-block min-cut benchmark (`slow`) — test: tests/unit/test_t_007_055_large_mincut_benchmark.py
- [ ] T-007-056 [US-007-1] (NFR-007-06, P-007-10) minimal maximum closure at the 10⁵-block cap: `networkx` agreement, ≤ 60 s and ≤ 2 GB (`slow`), and the penalised-problem relation on CI-size grids — test: tests/metamorphic/test_t_007_056_minimal_closure_at_scale.py

## Phase 7 — Polish and review
- [ ] T-007-090 (SC-007-02) mutation run on `minephys.planning`; record the score in the task log
- [ ] T-007-091 independent review of the diff against this spec; append tasks for gaps
- [ ] T-007-092 method pages `docs/methods/ultimate-pit-mincut.md` and `lane-cutoff.md`, and the reference-page names added by this spec
