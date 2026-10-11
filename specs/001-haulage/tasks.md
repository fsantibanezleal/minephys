# Tasks 001 — Haulage models (`minephys.haulage`)
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/001-haulage/tests.lock <files>`).

## Phase 1 — Setup
- [ ] T-001-001 (DC-001-01) `haulage.yaml` rows of spec §7.5 and their BibTeX entries; contract test of the table — test: tests/contract/test_t_001_001_haulage_table.py

## Phase 2 — US-001-2 (P1) road physics
- [ ] T-001-010 [US-001-2] (FR-001-01, FR-001-02, P-001-01) grade and total resistance — test: tests/unit/test_t_001_010_resistance.py, tests/metamorphic/test_t_001_010_resistance_mr.py
- [ ] T-001-011 [US-001-2] (FR-001-03) required force — test: tests/unit/test_t_001_011_required_force.py
- [ ] T-001-012 [US-001-2] (FR-001-04, FR-001-05, P-001-02, P-001-03) rimpull- and traction-limited speed — test: tests/unit/test_t_001_012_rimpull_speed.py, tests/metamorphic/test_t_001_012_rimpull_speed_mr.py
- [ ] T-001-013 [US-001-2] (FR-001-06, P-001-04) retarder-limited speed — test: tests/unit/test_t_001_013_retarder_speed.py, tests/metamorphic/test_t_001_013_retarder_speed_mr.py
- [ ] T-001-014 [US-001-2] (FR-001-07) unbounded steady speed needs a finite speed limit — test: tests/unit/test_t_001_014_unbounded_speed.py
- [ ] T-001-015 [US-001-2] (FR-001-10) segment travel time and cycle time — test: tests/unit/test_t_001_015_cycle_time.py

## Phase 3 — US-001-4 (P2) loading
- [ ] T-001-020 [US-001-4] (FR-001-08, FR-001-09, P-001-13) loose density and loading passes — test: tests/unit/test_t_001_020_loading_passes.py, tests/property/test_t_001_020_loading_passes_props.py

## Phase 4 — US-001-1 (P1) energy, fuel and CO₂
- [ ] T-001-030 [US-001-1] (FR-001-11, FR-001-12, P-001-05, P-001-06, P-001-07) segment and cycle energy — test: tests/unit/test_t_001_030_energy.py, tests/metamorphic/test_t_001_030_energy_mr.py
- [ ] T-001-031 [US-001-1] (FR-001-13, FR-001-14, FR-001-15) fuel, diesel CO₂ (pins row `diesel_co2_kg_per_us_gal`) and grid CO₂ — test: tests/unit/test_t_001_031_fuel_co2.py
- [ ] T-001-032 [US-001-1] (FR-001-16, FR-001-17, FR-001-25) trolley-assist and battery-electric cycle energy; segment-array guards — test: tests/unit/test_t_001_032_trolley_bev.py

## Phase 5 — US-001-3 (P1) fleet queueing
- [ ] T-001-040 [US-001-3] (FR-001-18, P-001-12) match factor — test: tests/unit/test_t_001_040_match_factor.py
- [ ] T-001-041 [US-001-3] (FR-001-19, FR-001-24, P-001-08, P-001-09) M/M/c queue — test: tests/unit/test_t_001_041_mmc_queue.py, tests/metamorphic/test_t_001_041_mmc_queue_mr.py
- [ ] T-001-042 [US-001-3] (FR-001-20, P-001-10) finite-source queue — test: tests/unit/test_t_001_042_finite_source.py, tests/metamorphic/test_t_001_042_finite_source_mr.py
- [ ] T-001-043 [US-001-3] (FR-001-21, FR-001-26, P-001-11) mean-value analysis — test: tests/unit/test_t_001_043_mva.py, tests/metamorphic/test_t_001_043_mva_mr.py

## Phase 6 — Hostile inputs and cross-cutting contract
- [ ] T-001-080 [US-001-2] (FR-001-22, FR-001-23, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, P-000-01, P-000-02, P-000-03) domain and tripwire tables and the foundation contract suite on every `minephys.haulage` function — test: tests/property/test_t_001_080_haulage_contract.py
- [ ] T-001-081 [US-001-2] (NFR-001-01, NFR-001-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_001_081_haulage_bench_registry.py

## Phase 7 — Polish and independent review
- [ ] T-001-090 mutation run on `src/minephys/haulage/`; record the score
- [ ] T-001-091 independent review of the diff against this spec; append tasks for gaps
