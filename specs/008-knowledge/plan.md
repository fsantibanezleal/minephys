# Plan 008 — Knowledge: loader, validator, lookup, equations and glossary catalogue, export and generated pages
Spec: ./spec.md

## Summary

The knowledge files ship inside the wheel. A hardened YAML reader (safe loader plus duplicate-key, alias, depth, size
and encoding checks) and a BibTeX-subset parser feed rule-based validators written in pure Python for the foundation's
table and bibliography contracts (DC-000-02, DC-000-03) and for this spec's catalogues (DC-008-01, DC-008-02). The JSON
Schemas in `contracts/` stay the neutral contract, and a property test keeps the validators equal to them. Validated
content becomes frozen dataclasses cached on first use. One exporter writes the deterministic JSON for PitStudio, one
renderer writes the pages that the foundation's docs generator commits, and a pure change detector serves the
foundation's changelog check.

## Technical context

Runtime: CPython 3.12–3.14, Pyodide, NVIDIA Kit · runtime dependencies PyYAML and NumPy · `importlib.resources` for
package data · foundation pieces used: `InputError`, `InputTypeError`, the `knowledge` and `oracle` test markers, the
`tools/check_knowledge.py` honesty checks and `tools/gen_knowledge_docs.py` · test-only tools: `jsonschema` (Draft
2020-12 reference validator), added to the `dev` group by T-008-002.

## Constitution check

| Principle (constitution 2.0.0) | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | every row keeps value, units, citation, page and status; UNVERIFIED rows are warned on use (model constants and parameters), counted, labelled and never filtered |
| 2 Spec before code | yes | FR/P/NFR/SC/DC-008 rows; the table and bibliography rules are the foundation's |
| 3 Acceptance-test-first | yes | one `[red]`/`[green]` pair per task |
| 4 Independent oracles | yes | `jsonschema` as reference validator; hand-written fixture corpus with expected errors; hand-written golden pages |
| 5 Determinism & explicit tolerances | yes | byte-identical export and pages (P-008-03), TC-0 throughout |
| 6 Purity and portability | yes | PyYAML and NumPy only; no file read at import (NFR-008-01); `importlib.resources` works from the wheel in Pyodide and Kit |
| 7 SI units at the API | n/a | the loader serves values in their published units; models convert |
| 8 Stable API | yes | planned names kept; additions listed in the clarifications log |
| 9 Licence hygiene | yes | share-alike tables stay in their own folder and keep their licence in the export and pages |
| 10 Simplicity | yes | rule functions instead of a schema engine at runtime |

## Design

| Component (`src/minephys/knowledge/`) | Contents | Requirements |
|---|---|---|
| `_yaml.py` | `read_yaml(resource)`: size ≤ 1 MiB, strict UTF-8, event scan rejecting anchors, aliases and non-core tags, depth ≤ 8, duplicate-key-detecting `SafeLoader` subclass | FR-008-07 |
| `_rules.py` | rule functions for DC-000-02 tables, DC-008-01 equations and DC-008-02 glossary, collecting every error as (file, index, field, message) | FR-008-02, 04 … 06, 19 |
| `_bibtex.py` | tokenizer and parser with line tracking, DC-000-03 rules, renderer | FR-008-03, 08, P-008-05 |
| `_model.py` | frozen dataclasses `Table`, `Row`, `Equation`, `Term`, `Reference`; `KnowledgeSchemaError(ValueError)`; `UnverifiedParameterWarning(UserWarning)` | FR-008-06, 09, 12 |
| `_store.py` | lazy, cached load via `importlib.resources.files("minephys.knowledge")`; table registry from the packaged stems | FR-008-01, 09, 10, NFR-008-01 … 03 |
| `__init__.py` | the public functions of FR-008-09 plus `export`, `export_json`, `render_pages`, `knowledge_changes` | FR-008-09 … 13, 15, 16, 19, 20 |
| `_export.py`, `_render.py` | deterministic JSON; Markdown pages with counts and labels | FR-008-13, 15, 16, P-008-03, 04 |
| `_changes.py` | `knowledge_changes(old_dir, new_dir)` | FR-008-20 |
| `__main__.py` | `argparse` CLI `validate`, `export`, `render` | FR-008-17, 18 |
| `catalogue/equations.yaml`, `catalogue/glossary.yaml` | data, filled by the module specs' knowledge tasks | DC-008-01, 02 |
| `contracts/knowledge-equations.schema.json`, `knowledge-glossary.schema.json`, `knowledge-export.schema.json` | JSON Schema 2020-12 | DC-008-01 … 03, P-008-01 |
| `tools/gen_knowledge_docs.py` (foundation) | calls `render_pages` | FR-008-21 |
| `tools/check_knowledge.py` (foundation) | extended to equation ids | FR-008-14 |

## Test strategy

All checks are exact (TC-0): structural data and byte comparisons. Fixtures live in `tests/contract/fixtures/knowledge/`
(valid and invalid files written by hand; each invalid file is paired with the expected file, index and field of its
first error and its total error count). Tests carry `@pytest.mark.oracle(...)` (FR-000-33).

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-008-01 | contract | the packaged file list against `importlib.resources` of the installed package | pytest |
| FR-008-02, 03, 04 | unit | hand-written valid fixtures load; one fixture per rule violation fails with the expected (file, index, field); the same corpus through `jsonschema` gives the same accept/reject decisions | pytest + jsonschema |
| FR-008-05 | unit | fixtures with a duplicate row id across two tables, a missing citation key, a dangling `see_also`, a dangling equation `rows` id | pytest |
| FR-008-06, 07, 08, 10, 17 | unit (hostile) | hostile fixtures: 1 MiB + 1 byte; byte 0xFF; `!!python/object/apply:os.system`; `&a` / `*a` and a nested alias bomb; a repeated key; 9 nesting levels; a top-level list; unbalanced `{`; a duplicate entry key and field; `@string`; table names `../haulage`, `a/b`, `C:\x`, `/etc/x`, `""`, `None`, `3`; output paths that are files, directories or have no parent; unknown CLI options → the specified exception or exit code, and no file opened outside the package (audit hook) | pytest parametrised |
| FR-008-09 | unit | identity (`is`) of repeated results; `FrozenInstanceError` on assignment | pytest |
| FR-008-11, 12 | unit | fixture rows: `value` → float; `"19/30"` → 19/30 in float64 (bit-equal to `19/30`); `range` → (min, max); `pytest.warns(UnverifiedParameterWarning)` for UNVERIFIED `model_constant` and `parameter` rows with id and key in the message; no warning for verified rows and for UNVERIFIED `limit` and `conversion` rows | pytest |
| FR-008-13 | unit | returned counts equal the hand-counted fixture rows, UNVERIFIED included | pytest |
| FR-008-14 | contract (repository) | every verified equation id appears in a `knowledge` marker of some test (AST scan) | pytest |
| FR-008-15 | unit + contract | `jsonschema` validation of the export; two calls and two fresh interpreters with different `PYTHONHASHSEED` give equal bytes | pytest + jsonschema + subprocess |
| FR-008-16 | unit | golden pages written by hand for the fixture knowledge (counts, labels, roles, licences, EN/ES columns, DOIs) | pytest |
| FR-008-18, 19 | unit (CLI) | subprocess exit codes 0/1/2; a three-error fixture reports exactly three errors | pytest |
| FR-008-20 | unit | two fixture layouts with hand-listed changes (value, range, rational value, status; added and removed rows); `quantity`, `notes` and `page` changes excluded | pytest (tmp_path) |
| FR-008-21 | unit | the generator's output for the fixture knowledge equals `render_pages` output byte for byte | pytest |
| P-008-01 | property | `jsonschema` decision equals the pure validator's decision | Hypothesis + jsonschema |
| P-008-02, 05 | property | round-trip identity | Hypothesis |
| P-008-03 | property | byte equality under row and entry permutations | Hypothesis |
| P-008-04 | property | label counts equal status counts | Hypothesis |
| NFR-008-01 | unit | fresh interpreter with an audit hook: no `open` event for knowledge files at import | pytest (subprocess) |
| NFR-008-02 | benchmark | `tools/bench.py` entry, cold (fresh interpreter) and warm | `tools/bench.py` |
| NFR-008-03 | runtimes | knowledge smoke tests in the Pyodide job and the Kit smoke | foundation jobs |
| NFR-008-04 | contract | wheel listing (`zipfile`) on the CI-built wheel | pytest (wheel job) |
| NFR-008-05 | contract | fresh-interpreter import audit | pytest (subprocess) |
| SC-008-01, 02 | CI | `validate` exit 0; the pinning check; the generator `--check` | CI jobs |

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Hand-written validators mirroring the JSON Schemas | the runtime may not depend on `jsonschema` (constitution principle 6) | validating only in CI would let user tables (FR-008-19) and corrupted installs load unchecked |
| Hardened YAML reader on top of `SafeLoader` | PyYAML keeps the last duplicate key and shares aliases silently | `safe_load` alone would hide duplicate ids and allow alias bombs |
| Own BibTeX-subset parser | no runtime dependency may be added; the subset is small and fully specified | a bibliography library would be a new runtime dependency |
| Warning only for UNVERIFIED `model_constant` and `parameter` rows | tripwire and validity-limit rows are design choices read on every call; warning on them would drown the useful warnings | warning on every UNVERIFIED read would make the warning meaningless |
