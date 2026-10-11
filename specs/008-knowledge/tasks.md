# Tasks 008 — Knowledge: loader, validator, lookup, equations and glossary catalogue, export and generated pages
Format: `- [ ] T-NNN-xxx [US-NNN-x] (REQ IDs) description — test: <path::name>`
Rule: every task with requirement IDs is a `[red]`/`[green]` commit pair; each task's tests live in their own file(s)
and are locked after `[red]` (`python tools/lock_tests.py specs/008-knowledge/tests.lock <files>`).
Order: after the foundation's schemas and honesty checks (T-000-001, T-000-014); Phase 1 and Phase 2 come before the
knowledge task of every module spec (001–007).

## Phase 1 — Setup
- [ ] T-008-001 (DC-008-01, DC-008-02, DC-008-03) `contracts/knowledge-equations.schema.json`, `knowledge-glossary.schema.json`, `knowledge-export.schema.json` with valid and invalid fixtures (no catalogue file is created here: the first entry of each catalogue is written by a module knowledge task, FR-008-22) — test: tests/contract/test_t_008_001_catalogue_schemas.py
- [ ] T-008-002 add `jsonschema` to the `dev` dependency group (test-only reference validator), lock, and record the version; no runtime change

## Phase 2 — US-008-1 (P1) Validated tables and bibliography
- [ ] T-008-010 [US-008-1] (FR-008-01, FR-008-02, FR-008-05, FR-008-09, P-008-01, P-008-02) table loading, DC-000-02 rules, cross-file integrity, cached immutable API, agreement with the JSON Schema — test: tests/unit/test_t_008_010_tables.py, tests/property/test_t_008_010_schema_agreement.py
- [ ] T-008-011 [US-008-1] (FR-008-03, P-008-05) BibTeX-subset parser and renderer with DC-000-03 rules — test: tests/unit/test_t_008_011_bibtex.py, tests/property/test_t_008_011_bibtex_roundtrip.py
- [ ] T-008-012 [US-008-4] (FR-008-04) equation and glossary catalogue rules — test: tests/unit/test_t_008_012_catalogues.py
- [ ] T-008-013 [US-008-1] (FR-008-06, FR-008-07) schema errors and hostile YAML (size, encoding, tags, aliases, duplicates, depth) — test: tests/unit/test_t_008_013_yaml_guards.py
- [ ] T-008-014 [US-008-1] (FR-008-08) hostile BibTeX — test: tests/unit/test_t_008_014_bibtex_guards.py
- [ ] T-008-015 [US-008-1] (FR-008-10) hostile table names and unknown ids (path traversal, no file opened) — test: tests/unit/test_t_008_015_name_guards.py
- [ ] T-008-016 [US-008-4] (FR-008-22) absent catalogue read as empty; a present table or catalogue file with no row or entry rejected — test: tests/unit/test_t_008_016_absent_catalogues.py

## Phase 3 — US-008-2 (P1) UNVERIFIED rows surfaced
- [ ] T-008-020 [US-008-2] (FR-008-11, FR-008-12, FR-008-13) `get_value` kinds, `UnverifiedParameterWarning` by role, no default filtering — test: tests/unit/test_t_008_020_values_and_warnings.py
- [ ] T-008-021 [US-008-2] (FR-008-14) extend the foundation pinning check to verified equation ids — test: tests/contract/test_t_008_021_equation_pins.py

## Phase 4 — US-008-3 (P1) One export for consumers
- [ ] T-008-030 [US-008-3] (FR-008-15, P-008-03) deterministic export valid against the export schema — test: tests/unit/test_t_008_030_export.py, tests/property/test_t_008_030_export_determinism.py
- [ ] T-008-031 [US-008-3] (FR-008-18, FR-008-19) CLI and validation report — test: tests/unit/test_t_008_031_cli.py
- [ ] T-008-032 [US-008-3] (FR-008-17) hostile output paths and CLI usage errors — test: tests/unit/test_t_008_032_output_guards.py

## Phase 5 — US-008-2/US-008-4 Pages and changes
- [ ] T-008-040 [US-008-2] (FR-008-16, P-008-04) Markdown pages with counts, UNVERIFIED labels, roles, licences and the EN/ES glossary — test: tests/unit/test_t_008_040_render.py, tests/property/test_t_008_040_label_counts.py
- [ ] T-008-041 [US-008-4] (FR-008-21, SC-008-02) the foundation docs generator calls `render_pages` — test: tests/unit/test_t_008_041_generator_uses_renderer.py
- [ ] T-008-042 [US-008-2] (FR-008-20) `knowledge_changes` for the foundation's release check — test: tests/unit/test_t_008_042_knowledge_changes.py

## Phase 6 — Non-functional and integrity
- [ ] T-008-060 (NFR-008-01) no knowledge file read at import (audit hook) — test: tests/unit/test_t_008_060_no_import_io.py
- [ ] T-008-061 (NFR-008-02) register the cold and warm load in `tools/bench.py` — test: tests/unit/test_t_008_061_bench_registry.py
- [ ] T-008-062 (NFR-008-03) knowledge smoke tests in the Pyodide job — test: tests/pyodide/test_t_008_062_knowledge_smoke.py
- [ ] T-008-063 (NFR-008-04) wheel contains the catalogue files — test: tests/contract/test_t_008_063_wheel_catalogue.py
- [ ] T-008-064 (NFR-008-05) import audit of `minephys.knowledge` — test: tests/contract/test_t_008_064_imports.py
- [ ] T-008-070 (SC-008-01) CI step running `python -m minephys.knowledge validate` on every push — test: tests/contract/test_t_008_070_integrity_step.py

## Phase 7 — Polish and review
- [ ] T-008-090 mutation run on `src/minephys/knowledge/` (target `mutation.other_min` of `thresholds.yaml`); record the score
- [ ] T-008-091 independent review of the diff against this spec; append tasks for gaps
- [ ] T-008-092 fill `docs/data-contract/README.md` (catalogue schemas, export, change policy) and the knowledge section of the reference page
