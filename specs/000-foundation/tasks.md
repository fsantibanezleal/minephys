# Tasks 000 — Foundation: minephys
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/000-foundation/tests.lock <files>`).

## Phase 1 — Setup
- [ ] T-000-001 [US-000-6] (DC-000-02, DC-000-03, DC-000-04) the three JSON Schemas under `contracts/` plus valid and invalid fixtures for every rule of `data-model.md` — test: tests/contract/test_t_000_001_schemas.py
- [ ] T-000-002 [US-000-5] (FR-000-27, FR-000-32) exceptions, warnings and `__version__`; register the markers `req`, `oracle`, `knowledge`, `pyodide`, `kit` — test: tests/unit/test_t_000_002_package_api.py
- [ ] T-000-003 [US-000-2] (FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, FR-000-14, FR-000-15, FR-000-16) validation helpers, proven on fixture functions — test: tests/unit/test_t_000_003_validation_helpers.py
- [ ] T-000-004 [US-000-2] (FR-000-17) solver helper raising `ConvergenceError` with its attributes — test: tests/unit/test_t_000_004_solver_helper.py
- [ ] T-000-005 [US-000-2] (FR-000-18, P-000-04) random-source helper — test: tests/property/test_t_000_005_random_source.py
- [ ] T-000-006 [US-000-5] (P-000-05, FR-000-08) `units` table of spec §8 A7 (pins its verified rows) and conversion helpers (exact definitions) — test: tests/property/test_t_000_006_unit_conversions.py

## Phase 2 — Cross-cutting guarantees
- [ ] T-000-010 [US-000-2] (FR-000-05, FR-000-07, P-000-01, P-000-02, P-000-03) contract suite `tests/_contract_suite.py`, proven on fixture functions (each module spec then runs it on its own functions) — test: tests/property/test_t_000_010_contract_suite.py
- [ ] T-000-011 [US-000-3] (FR-000-06, NFR-000-03) import purity under an audit hook and import time — test: tests/unit/test_t_000_011_import_purity.py
- [ ] T-000-012 [US-000-5] (FR-000-08, FR-000-09) docstring and model-card audit over every exported function — test: tests/contract/test_t_000_012_model_cards.py
- [ ] T-000-013 [US-000-6] (FR-000-19) literal audit with `tools/literal_allowlist.txt` — test: tests/contract/test_t_000_013_literal_audit.py
- [ ] T-000-014 [US-000-6] (FR-000-20, FR-000-21, FR-000-22, FR-000-31) knowledge honesty checks (`tools/check_knowledge.py`): schema agreement, verified-row pinning, symbol resolution, citation resolution, no UNVERIFIED parameter defaults, licence separation — test: tests/contract/test_t_000_014_knowledge_honesty.py
- [ ] T-000-015 [US-000-6] (FR-000-23) knowledge docs generator with `--check` — test: tests/unit/test_t_000_015_gen_knowledge_docs.py
- [ ] T-000-016 [US-000-5] (FR-000-33, SC-000-02) oracle-marker inventory and report — test: tests/contract/test_t_000_016_oracle_markers.py

## Phase 3 — Packaging and runtimes
- [ ] T-000-020 [US-000-4] (FR-000-24, NFR-000-04, NFR-000-05) wheel contents, tag, size and metadata — test: tests/contract/test_t_000_020_wheel.py
- [ ] T-000-021 [US-000-3] (FR-000-25, NFR-000-06) Pyodide smoke job (Node 24, pinned Pyodide) — test: tests/pyodide/test_t_000_021_pyodide_smoke.py
- [ ] T-000-022 [US-000-2] (FR-000-26) Kit smoke import, skipped as "not run" when Kit is absent — test: tests/kit/test_t_000_022_kit_smoke.py
- [ ] T-000-023 [US-000-2] (NFR-000-07) benchmark runner `tools/bench.py` with a reference-size registry — test: tests/unit/test_t_000_023_bench_runner.py
- [ ] T-000-024 [US-000-2] (NFR-000-08, NFR-000-09) CI gates: coverage, mutation tool selection and lock, Hypothesis profiles, mypy strictness — test: tests/contract/test_t_000_024_ci_gates.py

## Phase 4 — Release discipline
- [ ] T-000-030 [US-000-7] (FR-000-28, FR-000-29, DC-000-04) API snapshot writer and checker; deprecation helper — test: tests/unit/test_t_000_030_api_stability.py
- [ ] T-000-031 [US-000-7] (FR-000-30) knowledge value-change check against the previous release — test: tests/unit/test_t_000_031_value_changelog.py
- [ ] T-000-032 [US-000-6] (SC-000-03, SC-000-04) release evidence report (honesty and portability summary) — test: tests/unit/test_t_000_032_release_evidence.py

## Phase 5 — Polish and independent review
- [ ] T-000-090 mutation run on `src/minephys/_validate.py`, `_solve.py`, `_random.py`, `units.py`; record the score
- [ ] T-000-091 independent review of the diff against this spec; append tasks for gaps
