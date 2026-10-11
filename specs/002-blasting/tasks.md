# Tasks 002 — Blasting models (`minephys.blasting`)
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/002-blasting/tests.lock <files>`).

## Phase 1 — Setup
- [ ] T-002-001 (DC-002-01) `blasting.yaml` rows of spec §7.5 and their BibTeX entries; contract test of the table — test: tests/contract/test_t_002_001_blasting_table.py
- [ ] T-002-002 resolve and lock SciPy in the dev group (test oracle only) and record it in `docs/frameworks/` — no requirement ID (tooling)

## Phase 2 — US-002-1 (P1) Kuz-Ram
- [ ] T-002-010 [US-002-1] (FR-002-01) charge per hole and powder factor — test: tests/unit/test_t_002_010_design.py
- [ ] T-002-011 [US-002-1] (FR-002-02, FR-002-18, P-002-01, P-002-02) Kuznetsov x50 with both exponent variants — test: tests/unit/test_t_002_011_kuznetsov.py, tests/metamorphic/test_t_002_011_kuznetsov_mr.py
- [ ] T-002-012 [US-002-1] (FR-002-03) rock factor, hardness factor, rock density influence — test: tests/unit/test_t_002_012_rock_factor.py
- [ ] T-002-013 [US-002-1] (FR-002-04, FR-002-14, P-002-03) uniformity index — test: tests/unit/test_t_002_013_uniformity.py, tests/metamorphic/test_t_002_013_uniformity_mr.py

## Phase 3 — US-002-2 (P1) size distributions
- [ ] T-002-020 [US-002-2] (FR-002-05, FR-002-06, FR-002-15, P-002-04, P-002-05) Rosin–Rammler and Swebrec passing and percentiles — test: tests/unit/test_t_002_020_distributions.py, tests/metamorphic/test_t_002_020_distributions_mr.py
- [ ] T-002-021 [US-002-2] (FR-002-07, P-002-06) KCO undulation and distribution — test: tests/unit/test_t_002_021_kco.py, tests/property/test_t_002_021_kco_props.py

## Phase 4 — US-002-3 (P1) vibration
- [ ] T-002-030 [US-002-3] (FR-002-08, P-002-07) scaled distance and PPV site law — test: tests/unit/test_t_002_030_ppv.py, tests/metamorphic/test_t_002_030_ppv_mr.py
- [ ] T-002-031 [US-002-3] (FR-002-09, P-002-08) 30 CFR § 816.67 PPV limit and maximum charge per delay (pins the CFR rows) — test: tests/unit/test_t_002_031_cfr_limits.py

## Phase 5 — US-002-4 (P2) flyrock
- [ ] T-002-040 [US-002-4] (FR-002-10, FR-002-11, P-002-09) drag-free and Lundborg ranges — test: tests/unit/test_t_002_040_flyrock_ranges.py, tests/metamorphic/test_t_002_040_flyrock_ranges_mr.py
- [ ] T-002-041 [US-002-4] (FR-002-12, FR-002-13, P-002-10) RK4 drag trajectory (analytical limits; SciPy reference) — test: tests/unit/test_t_002_041_flyrock_trajectory.py, tests/parity/test_t_002_041_flyrock_scipy.py

## Phase 6 — Hostile inputs and cross-cutting contract
- [ ] T-002-080 [US-002-1] (FR-002-16, FR-002-17, FR-002-18, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, P-000-01, P-000-02, P-000-03) domain, validity and tripwire tables and the foundation contract suite on every `minephys.blasting` function — test: tests/property/test_t_002_080_blasting_contract.py
- [ ] T-002-081 [US-002-4] (NFR-002-01, NFR-002-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_002_081_blasting_bench_registry.py

## Phase 7 — Polish and independent review
- [ ] T-002-090 mutation run on `src/minephys/blasting/`; record the score
- [ ] T-002-091 independent review of the diff against this spec; append tasks for gaps
