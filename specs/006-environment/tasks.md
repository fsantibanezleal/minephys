# Tasks 006 — Environment: AP-42 unpaved-road dust, Gaussian plume dispersion and Beer–Lambert dust attenuation for lidar
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/006-environment/tests.lock <files>`).
Dependencies: the foundation's schemas, validators, `units` table and honesty checks (T-000-001, T-000-003, T-000-006,
T-000-014) and the knowledge loader of spec 008 (T-008-010).
Verified rows are pinned from T-006-001 on: its contract test carries `@pytest.mark.knowledge(id)` and compares each
row with the value printed in the source (transcribed into the test); the worked-example tests add further pins.

## Phase 1 — Setup
- [ ] T-006-001 [US-006-4] (DC-006-01, DC-006-02) `knowledge/environment.yaml` rows of spec §7 (AP-42 constants and ranges, watering vertices, ISC3 coefficients, lidar thresholds), the environment entries of `knowledge/catalogue/equations.yaml` and the §7 bibliography entries; transcription pins of every verified row — test: tests/contract/test_t_006_001_environment_knowledge.py

## Phase 2 — US-006-1 (P1) Haul-road emission factor
- [ ] T-006-010 [US-006-1] (FR-006-01, P-006-01, P-006-02, P-006-03) AP-42 equation 1a with SI arguments, against the published-unit form — test: tests/unit/test_t_006_010_ap42.py, tests/property/test_t_006_010_ap42_properties.py
- [ ] T-006-011 [US-006-1] (FR-006-02, FR-006-03) validity flags, `ValidityWarning` and strict mode at the Table 13.2.2-3 bounds — test: tests/unit/test_t_006_011_ap42_validity.py
- [ ] T-006-012 [US-006-1] (FR-006-04, FR-006-05, FR-006-06, P-006-04, SC-006-01) fleet-mean weight, precipitation correction, watering control efficiency and controlled factor against AP-42's printed numbers — test: tests/unit/test_t_006_012_ap42_corrections.py, tests/property/test_t_006_012_corrections_properties.py
- [ ] T-006-013 [US-006-1] (FR-006-07) AP-42 guards — test: tests/unit/test_t_006_013_ap42_guards.py

## Phase 3 — US-006-2 (P1) Plume dispersion
- [ ] T-006-020 [US-006-2] (FR-006-08, FR-006-09, FR-006-10, P-006-09) line emission rate and ISC3 dispersion coefficients (rural bands, caps, urban Briggs, band-edge convention, urban near-field warning) — test: tests/unit/test_t_006_020_sigmas.py, tests/property/test_t_006_020_sigmas_properties.py
- [ ] T-006-021 [US-006-2] (FR-006-11, FR-006-12, P-006-05, P-006-06, P-006-07) point-source plume with ground reflection and the optional mixing lid — test: tests/unit/test_t_006_021_plume.py, tests/metamorphic/test_t_006_021_plume_mr.py
- [ ] T-006-022 [US-006-2] (FR-006-13, P-006-08) infinite and finite crosswind line sources — test: tests/unit/test_t_006_022_line_source.py, tests/metamorphic/test_t_006_022_line_source_mr.py
- [ ] T-006-023 [US-006-2] (FR-006-14) dispersion and plume guards — test: tests/unit/test_t_006_023_plume_guards.py

## Phase 4 — US-006-3 (P2) Dust and lidar
- [ ] T-006-030 [US-006-3] (FR-006-15, FR-006-16, P-006-10, P-006-11) mass extinction, extinction coefficient and path transmittance — test: tests/unit/test_t_006_030_beer_lambert.py, tests/property/test_t_006_030_beer_lambert_properties.py
- [ ] T-006-031 [US-006-3] (FR-006-17, P-006-12) lidar return state at the published thresholds and the leading edge of a profile — test: tests/unit/test_t_006_031_lidar_dust.py, tests/property/test_t_006_031_lidar_properties.py
- [ ] T-006-032 [US-006-3] (FR-006-18) optics and lidar guards — test: tests/unit/test_t_006_032_optics_guards.py

## Phase 5 — US-006-4 (P2) Cited constants and cross-cutting contract
- [ ] T-006-040 [US-006-4] (FR-006-19) constants come from the knowledge rows (fixture layout changes results analytically) — test: tests/contract/test_t_006_040_constants_from_knowledge.py
- [ ] T-006-050 (NFR-006-01) import audit of `minephys.environment` — test: tests/contract/test_t_006_050_imports.py
- [ ] T-006-051 (NFR-006-02) register the reference sizes in `tools/bench.py` — test: tests/unit/test_t_006_051_bench_registry.py
- [ ] T-006-052 (NFR-006-03) one worked-example oracle per family in the Pyodide smoke subset — test: tests/pyodide/test_t_006_052_environment_smoke.py
- [ ] T-006-053 (NFR-006-04) model-card audit over `minephys.environment.__all__` — test: tests/contract/test_t_006_053_model_cards.py
- [ ] T-006-054 [US-006-1] (FR-000-05, FR-000-07, FR-000-10, FR-000-11, FR-000-12, FR-000-13, P-000-01, P-000-02, P-000-03) the foundation cross-cutting contract checks (T-000-010) on every `minephys.environment` function — test: tests/property/test_t_006_054_environment_contract.py

## Phase 6 — Polish and review
- [ ] T-006-090 (SC-006-02) mutation run on `src/minephys/environment/`; record the score
- [ ] T-006-091 independent review of the diff against this spec; append tasks for gaps
- [ ] T-006-092 method pages `docs/methods/ap42-unpaved-roads.md`, `gaussian-plume.md`, `dust-lidar.md`, and the reference-page names added by this spec
