# Tasks 005 — Comminution: Bond, Morrell, population balance, flotation kinetics and the mine-to-mill chain
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/005-comminution/tests.lock <files>`).
Dependencies: the foundation's schemas, validators and honesty checks (T-000-001, T-000-003, T-000-014) and the
knowledge loader of spec 008 (T-008-010); T-005-044 needs T-005-010, T-005-012, T-005-040 and T-005-042.
Verified rows are pinned from T-005-001 on: its contract test carries `@pytest.mark.knowledge(id)` and compares each
row with the value printed in the source (transcribed into the test); the worked-example tests add further pins.

## Phase 1 — Setup
- [ ] T-005-001 [US-005-5] (DC-005-01, DC-005-02) `knowledge/comminution.yaml` rows of spec §7, the comminution entries of `knowledge/catalogue/equations.yaml` and the §7 bibliography entries; transcription pins of every verified row — test: tests/contract/test_t_005_001_comminution_knowledge.py

## Phase 2 — US-005-1 (P1) Energy–size laws
- [ ] T-005-010 [US-005-1] (FR-005-01, FR-005-02, FR-005-03, P-005-01, P-005-02, P-005-03, SC-005-01) Bond's law, operating work index and ball-mill test work index against the Bond-efficiency guideline examples — test: tests/unit/test_t_005_010_bond.py, tests/property/test_t_005_010_bond_properties.py
- [ ] T-005-011 [US-005-1] (FR-005-04) Bond functions reject NaN/inf/non-positive/unordered/unbroadcastable/non-numeric inputs — test: tests/unit/test_t_005_011_bond_guards.py
- [ ] T-005-012 [US-005-1] (FR-005-05, FR-005-06, FR-005-07, FR-005-08, FR-005-09, FR-005-10, FR-005-11, P-005-03, P-005-04, P-005-05, SC-005-01) Morrell relation and circuit terms against the Morrell-method guideline Annex C — test: tests/unit/test_t_005_012_morrell.py, tests/property/test_t_005_012_morrell_properties.py
- [ ] T-005-013 [US-005-1] (FR-005-12) Morrell functions reject hostile inputs, sizes on the wrong side of 750 µm and unknown stages — test: tests/unit/test_t_005_013_morrell_guards.py
- [ ] T-005-014 [US-005-1] (FR-005-32, FR-005-33) validity warnings below 70 µm (Bond) and 45 µm (Morrell fine term) — test: tests/unit/test_t_005_014_validity_warnings.py

## Phase 3 — US-005-2 (P1) Population balance grinding
- [ ] T-005-020 [US-005-2] (FR-005-13, P-005-06, P-005-07, P-005-08) batch grinding against the analytical three-class solution, the repeated-rate solution and a Runge–Kutta reference — test: tests/unit/test_t_005_020_pbm_batch.py, tests/property/test_t_005_020_pbm_batch_properties.py
- [ ] T-005-021 [US-005-2] (FR-005-14, P-005-06, P-005-09) continuous perfectly mixed mill with N tanks — test: tests/unit/test_t_005_021_pbm_continuous.py, tests/property/test_t_005_021_pbm_continuous_properties.py
- [ ] T-005-022 [US-005-2] (FR-005-16, FR-005-17) Austin selection and breakage forms — test: tests/unit/test_t_005_022_austin_forms.py
- [ ] T-005-023 [US-005-2] (FR-005-15, FR-005-18) PBM and Austin guards (shapes, triangularity, column sums, sink class, oversized n) — test: tests/unit/test_t_005_023_pbm_guards.py

## Phase 4 — US-005-3 (P2) Flotation kinetics and recovery
- [ ] T-005-030 [US-005-3] (FR-005-19, FR-005-20, FR-005-21, P-005-10, P-005-11) first-order, Klimpel (quadrature and small-kt series) and cells-in-series recovery — test: tests/unit/test_t_005_030_flotation.py, tests/property/test_t_005_030_flotation_properties.py
- [ ] T-005-031 [US-005-3] (FR-005-22, P-005-12) two-product formula — test: tests/unit/test_t_005_031_two_product.py
- [ ] T-005-032 [US-005-3] (FR-005-23) flotation and two-product guards — test: tests/unit/test_t_005_032_flotation_guards.py

## Phase 5 — US-005-4 (P1) Mine-to-mill chain
- [ ] T-005-040 [US-005-4] (FR-005-24, FR-005-25, P-005-14) passing size, class masses and cumulative passing against the Swebrec closed form — test: tests/unit/test_t_005_040_psd.py, tests/property/test_t_005_040_psd_properties.py
- [ ] T-005-041 [US-005-4] (FR-005-26) PSD helper guards — test: tests/unit/test_t_005_041_psd_guards.py
- [ ] T-005-042 [US-005-4] (FR-005-27, FR-005-28, P-005-13) crusher matrix model and classification function — test: tests/unit/test_t_005_042_crusher.py, tests/property/test_t_005_042_crusher_properties.py
- [ ] T-005-043 [US-005-4] (FR-005-29) crusher guards — test: tests/unit/test_t_005_043_crusher_guards.py
- [ ] T-005-044 [US-005-4] (FR-005-30, P-005-15) mine-to-mill chain (composition, power scaling, identity-crusher Swebrec check) — test: tests/unit/test_t_005_044_chain.py, tests/metamorphic/test_t_005_044_chain_mr.py
- [ ] T-005-045 [US-005-4] (FR-005-31) chain guards — test: tests/unit/test_t_005_045_chain_guards.py

## Phase 6 — US-005-5 (P2) Cited constants and cross-cutting contract
- [ ] T-005-050 [US-005-5] (FR-005-34) constants come from the knowledge rows (fixture layout changes results analytically) — test: tests/contract/test_t_005_050_constants_from_knowledge.py
- [ ] T-005-060 (NFR-005-01) import audit of `minephys.comminution` — test: tests/contract/test_t_005_060_imports.py
- [ ] T-005-061 (NFR-005-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_005_061_bench_registry.py
- [ ] T-005-062 (NFR-005-03) one worked-example oracle per family in the Pyodide smoke subset — test: tests/pyodide/test_t_005_062_comminution_smoke.py
- [ ] T-005-063 (NFR-005-04) model-card audit over `minephys.comminution.__all__` — test: tests/contract/test_t_005_063_model_cards.py
- [ ] T-005-064 [US-005-1] (FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, P-000-01, P-000-02, P-000-03) the foundation cross-cutting contract checks (T-000-010) on every `minephys.comminution` function — test: tests/property/test_t_005_064_comminution_contract.py

## Phase 7 — Polish and review
- [ ] T-005-090 (SC-005-02) mutation run on `src/minephys/comminution/`; record the score
- [ ] T-005-091 independent review of the diff against this spec; append tasks for gaps
- [ ] T-005-092 method page `docs/methods/comminution.md`, the module diagram, and the reference-page names added by this spec
