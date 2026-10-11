# Tasks 003 — Geotechnical models (`minephys.geotech`)
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/003-geotech/tests.lock <files>`).

## Phase 1 — Setup
- [ ] T-003-001 (DC-003-01) `geotech.yaml` rows of spec §7.5 and their BibTeX entries; contract test of the table — test: tests/contract/test_t_003_001_geotech_table.py
- [ ] T-003-002 resolve and lock pySlope 1.4.0 in the dev group (test oracle only) and record it in `docs/frameworks/` — no requirement ID (tooling)

## Phase 2 — US-003-4 (P2) and US-003-1 (P1) rock-mass strength
- [ ] T-003-010 [US-003-4] (FR-003-01, FR-003-02, FR-003-03, FR-003-06, P-003-01, P-003-02, P-003-03) Hoek–Brown parameters, σ1, σc, σt, σcm — test: tests/unit/test_t_003_010_hoek_brown.py, tests/metamorphic/test_t_003_010_hoek_brown_mr.py
- [ ] T-003-011 [US-003-4] (FR-003-04, FR-003-05) equivalent Mohr–Coulomb and σ3max (pins the 2002 worked example) — test: tests/unit/test_t_003_011_equivalent_mc.py

## Phase 3 — US-003-1 (P1) limit equilibrium and probability of failure
- [ ] T-003-020 [US-003-1] (FR-003-07, FR-003-08) circular slices from a ground polyline — test: tests/unit/test_t_003_020_circular_slices.py
- [ ] T-003-021 [US-003-1] (FR-003-09, FR-003-11, FR-003-22, P-003-04, P-003-05, P-003-06, P-003-07) Bishop simplified (hand calculation #1, Fredlund–Krahn, limits) — test: tests/unit/test_t_003_021_bishop.py, tests/metamorphic/test_t_003_021_bishop_mr.py
- [ ] T-003-022 [US-003-1] (FR-003-10, FR-003-11, FR-003-22) Spencer (θ = 0 identity, Fredlund–Krahn, three-slice hand calculation) — test: tests/unit/test_t_003_022_spencer.py, tests/metamorphic/test_t_003_022_spencer_mr.py
- [ ] T-003-023 [US-003-1] (FR-003-09) pySlope cross-check on the Fredlund–Krahn geometry (skipped with "not run" if pySlope is absent) — test: tests/parity/test_t_003_023_pyslope_parity.py
- [ ] T-003-024 [US-003-1] (FR-003-12, FR-003-13, FR-003-24, P-003-08) Monte-Carlo factor of safety and probability of failure — test: tests/unit/test_t_003_024_pof.py, tests/property/test_t_003_024_pof_props.py

## Phase 4 — US-003-2 (P1) and US-003-3 (P1) creep and forecasting
- [ ] T-003-030 [US-003-3] (FR-003-14) Voight creep series — test: tests/unit/test_t_003_030_voight.py
- [ ] T-003-031 [US-003-2] (FR-003-15, FR-003-16, P-003-09) inverse-velocity time of failure — test: tests/unit/test_t_003_031_inverse_velocity.py, tests/metamorphic/test_t_003_031_inverse_velocity_mr.py
- [ ] T-003-032 [US-003-2] (FR-003-17, FR-003-23, P-003-10) Bayesian time of failure — test: tests/unit/test_t_003_032_bayesian_ttf.py, tests/property/test_t_003_032_bayesian_ttf_props.py

## Phase 5 — US-003-3 (P1) slope radar
- [ ] T-003-040 [US-003-3] (FR-003-18, P-003-11) line-of-sight projection — test: tests/unit/test_t_003_040_radar_los.py, tests/metamorphic/test_t_003_040_radar_los_mr.py
- [ ] T-003-041 [US-003-3] (FR-003-19, P-003-12) phase, wrapping, inverse and ambiguity limit — test: tests/unit/test_t_003_041_radar_phase.py, tests/metamorphic/test_t_003_041_radar_phase_mr.py

## Phase 6 — Hostile inputs and cross-cutting contract
- [ ] T-003-080 [US-003-1] (FR-003-20, FR-003-21, FR-003-23, FR-003-24, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, FR-000-18, P-000-01, P-000-02, P-000-03, P-000-04) domain and tripwire tables and the foundation contract suite on every `minephys.geotech` function — test: tests/property/test_t_003_080_geotech_contract.py
- [ ] T-003-081 [US-003-1] (NFR-003-01, NFR-003-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_003_081_geotech_bench_registry.py

## Phase 7 — Polish and independent review
- [ ] T-003-090 mutation run on `src/minephys/geotech/`; record the score
- [ ] T-003-091 independent review of the diff against this spec; append tasks for gaps
