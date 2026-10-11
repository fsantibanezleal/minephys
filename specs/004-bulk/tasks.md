# Tasks 004 — Bulk-handling models (`minephys.bulk`)
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/004-bulk/tests.lock <files>`).

## Phase 1 — Setup
- [ ] T-004-001 (DC-004-01) `bulk.yaml` rows of spec §7.5 and their BibTeX entries; contract test of the table — test: tests/contract/test_t_004_001_bulk_table.py

## Phase 2 — US-004-1 (P1) discharge and stockpiles
- [ ] T-004-010 [US-004-1] (FR-004-01, FR-004-02, P-004-01, P-004-02) Beverloo discharge — test: tests/unit/test_t_004_010_beverloo.py, tests/metamorphic/test_t_004_010_beverloo_mr.py
- [ ] T-004-011 [US-004-1] (FR-004-03, FR-004-04, P-004-03) repose cone and ridge geometry — test: tests/unit/test_t_004_011_repose.py, tests/metamorphic/test_t_004_011_repose_mr.py

## Phase 3 — US-004-2 (P1) conveyors
- [ ] T-004-020 [US-004-2] (FR-004-05, FR-004-06, FR-004-07, P-004-04, P-004-05, P-004-06) conveyor capacity, CEMA effective tension and drive power — test: tests/unit/test_t_004_020_conveyor.py, tests/metamorphic/test_t_004_020_conveyor_mr.py

## Phase 4 — US-004-3 (P2) sampling and blending
- [ ] T-004-030 [US-004-3] (FR-004-08, FR-004-12, P-004-07) Gy fundamental sampling error — test: tests/unit/test_t_004_030_gy_fse.py, tests/metamorphic/test_t_004_030_gy_fse_mr.py
- [ ] T-004-031 [US-004-3] (FR-004-09, FR-004-12, P-004-08) bed-blending variance and variance reduction ratio — test: tests/unit/test_t_004_031_blending.py, tests/metamorphic/test_t_004_031_blending_mr.py

## Phase 5 — Hostile inputs and cross-cutting contract
- [ ] T-004-080 [US-004-1] (FR-004-10, FR-004-11, FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, P-000-01, P-000-02, P-000-03) domain and tripwire tables and the foundation contract suite on every `minephys.bulk` function — test: tests/property/test_t_004_080_bulk_contract.py
- [ ] T-004-081 [US-004-2] (NFR-004-01) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_004_081_bulk_bench_registry.py

## Phase 6 — Polish and independent review
- [ ] T-004-090 mutation run on `src/minephys/bulk/`; record the score
- [ ] T-004-091 independent review of the diff against this spec; append tasks for gaps
