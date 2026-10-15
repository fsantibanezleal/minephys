# Spec 008 — Knowledge: loader, validator, lookup, equations and glossary catalogue, export and generated pages
Status: Clarified
Tier: M · Parent: 000-foundation · Approved: —
Supersedes/Modifies: (none)

## 1. Intent

`minephys.knowledge` is the machine-readable half of the knowledge base. The foundation fixes the data contract of the
parameter tables (DC-000-02) and of the bibliography (DC-000-03) and the library-wide honesty checks (FR-000-19 to
FR-000-23, FR-000-30, FR-000-31). This spec specifies the code that serves them and the two catalogues the consumers
also need:

- the **loader and validator** of every knowledge table (`knowledge/*.yaml`, `knowledge/share-alike/*.yaml`) and of
  `knowledge/references.bib`, in pure Python (no `jsonschema` at runtime), with hardened YAML and BibTeX parsing;
- a small **read-only lookup API** (`list_tables`, `load_table`, `get_parameter`, `list_parameters`, `get_value`,
  `bibliography`, `equations`, `glossary`, `validate_tables`);
- the **equations catalogue** (LaTeX, symbols with units, function, citation, page, status) and the **bilingual
  glossary** (English and Spanish), under `knowledge/catalogue/`;
- one deterministic **JSON export** of everything, consumed by PitStudio's docs build and `/knowledge` route;
- the **page renderer** behind the foundation's docs generator, and the pure **change detector** behind its
  changelog check.

**UNVERIFIED rows are surfaced everywhere and never hidden:** in the API, the export, the pages, and as a warning when
code reads an UNVERIFIED model constant or parameter.

**Who benefits:** every `minephys` module (defaults come from the tables); reviewers auditing each number; PitStudio,
which generates its parameter browser, equation explorer, bibliography and glossary from the export of the pinned
`minephys` version.

**Out of scope:** unit conversion of table values (models convert at their boundary with the foundation `units`
table), editing tools, languages beyond English and Spanish, network access (no DOI resolution at runtime), and the
PitStudio pages themselves.

## 2. User stories

### US-008-1 (P1) Validated tables and bibliography
As a model author, I want every table and bibliography entry validated at load against the foundation contract, so
that no uncited or malformed number can reach a model. Independent test: a fixture table with a missing page or an
unknown citation key fails to load with an error naming the file, row and field.

### US-008-2 (P1) UNVERIFIED rows surfaced
As a reader of results, I want every UNVERIFIED row visible in the API, the export and the pages, and a warning when
code reads an UNVERIFIED constant, so that nothing unverified passes as verified. Independent test: the count of
"UNVERIFIED" labels in the rendered pages equals the number of UNVERIFIED rows and entries.

### US-008-3 (P1) One export for consumers
As the PitStudio docs build, I want one deterministic JSON export valid against a published JSON Schema, so that my
pages and web route can be generated and drift-checked. Independent test: two exports of the same version are
byte-identical and validate against the schema.

### US-008-4 (P2) Equations and glossary
As a student, I want each model's equation with its symbols and units, and a glossary in English and Spanish, so that
I can read the models without the code. Independent test: every exported function named in the equations catalogue
resolves, and every glossary term has both languages.

## 3. Functional requirements (EARS)

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-008-01 | Ubiquitous | The loader shall read the tables `minephys/knowledge/*.yaml` and `minephys/knowledge/share-alike/*.yaml`, the bibliography `minephys/knowledge/references.bib` and the catalogues `minephys/knowledge/catalogue/equations.yaml` and `catalogue/glossary.yaml` (when present, FR-008-22) through `importlib.resources` (never through paths built from `__file__`). | contract |
| FR-008-02 | Ubiquitous | The loader shall accept a table only if it satisfies every rule of the foundation data model for DC-000-02 (`schema_version`, `table` equal to the file stem, `title`, `licence`, at least one row; row fields `id`, `quantity`, exactly one of `value` (finite number or exact rational string `"p/q"`) and `range` (`min ≤ max`), `units`, `role`, `citation`, `page`, `verification`, `verified_on` exactly when verified, `symbol`, optional `notes`; no other field). | unit |
| FR-008-03 | Ubiquitous | The bibliography parser shall read the BibTeX subset of §7 and accept an entry only if it satisfies every DC-000-03 rule (key pattern, entry type, `author` or `organization`, `title`, `year` in 1800–2100, `doi` or `url` with their patterns, `access` enum, optional fields only from the allowed list, unknown fields rejected). | unit |
| FR-008-04 | Ubiquitous | The loader shall accept `catalogue/equations.yaml` only if it satisfies the equation rules of §7 (DC-008-01) and `catalogue/glossary.yaml` only if it satisfies the glossary rules of §7 (DC-008-02). | unit |
| FR-008-05 | Ubiquitous | The loader shall check cross-file integrity: row ids unique across all tables; equation ids and glossary ids unique; every `citation` key present in the bibliography; every equation `rows` id and glossary `see_also` id resolving. | unit |
| FR-008-06 | Unwanted | If a packaged or user-supplied knowledge file violates FR-008-02 to FR-008-05, then the loader shall raise `KnowledgeSchemaError` (a `ValueError` subclass with `file`, `index` and `field` attributes) whose message names the file, the 1-based row or entry index and the field, and shall return no partially validated data. | unit (hostile) |
| FR-008-07 | Unwanted | If a YAML file is larger than 1 MiB, is not valid UTF-8, uses a tag outside the YAML core schema (for example `!!python/object/apply`), uses an anchor or alias, repeats a mapping key, nests deeper than 8 levels, or has a non-mapping top level, then the loader shall raise `KnowledgeSchemaError` without constructing arbitrary objects or expanding aliases. | unit (hostile) |
| FR-008-08 | Unwanted | If `references.bib` is larger than 1 MiB, has unbalanced braces or quotes, repeats an entry key or a field within an entry, or uses an unsupported entry type (including `@string`, `@preamble`, `@comment`), then the parser shall raise `KnowledgeSchemaError` naming the entry key (when known) and the 1-based line. | unit (hostile) |
| FR-008-09 | Ubiquitous | `minephys.knowledge` shall provide `list_tables()`, `load_table(table)`, `get_parameter(id)`, `list_parameters(table=None, role=None, verification=None)`, `get_value(id)`, `bibliography()`, `equations(domain=None)`, `glossary(domain=None)` and `validate_tables(path=None)`, returning immutable objects (frozen dataclasses and tuples), loading and validating every file once on first use and returning the cached objects afterwards. | unit |
| FR-008-10 | Unwanted | If `load_table` gets a name that is not one of `list_tables()` (including names containing `/`, `\`, `..`, a drive or an absolute path, and the empty string), or `get_parameter` / `get_value` gets an unknown id, then the function shall raise `minephys.InputError` naming the argument without opening any file; a non-string argument shall raise `minephys.InputTypeError`. | unit (hostile) |
| FR-008-11 | Ubiquitous | `get_value(id)` shall return a `value` row as a float (a `"p/q"` string evaluated as p / q in float64) and a `range` row as the tuple `(min, max)` of floats. | unit |
| FR-008-12 | Event | When `get_value` is called for an UNVERIFIED row whose `role` is `model_constant` or `parameter`, the module shall emit `minephys.knowledge.UnverifiedParameterWarning` (a `UserWarning` subclass) naming the row id and its citation key; rows of role `limit` and `conversion` shall not warn. | unit |
| FR-008-13 | Ubiquitous | `list_parameters()` without filters, `export()` and the rendered pages shall include every row, entry and term, UNVERIFIED ones included, each carrying its verification status. | unit |
| FR-008-14 | Ubiquitous | Every verified equation entry shall be referenced by at least one test through `@pytest.mark.knowledge("<equation id>")`, checked by the same repository check as the foundation's verified-row pinning (FR-000-21). | contract (repository) |
| FR-008-15 | Ubiquitous | `export()` shall return a JSON-serialisable mapping valid against `contracts/knowledge-export.schema.json` holding the package version, every table (title, licence) with its rows, every equation, glossary term and bibliography entry, and a summary of counts (totals, UNVERIFIED, per table and per role); `export_json()` shall serialise it deterministically (sorted keys, tables and rows sorted by id, bibliography by key, UTF-8, LF line ends, two-space indent, trailing newline, no timestamps). | unit + contract |
| FR-008-16 | Ubiquitous | `render_pages(out_dir)` shall write one Markdown page per table (`<table>.md`, share-alike tables included with their licence) plus `equations.md`, `bibliography.md` and `glossary.md`, deterministically; each page shall start with the counts of items and of UNVERIFIED items, label every UNVERIFIED item "UNVERIFIED", show every row's value or range, units, citation with DOI or URL, page, role, verification and symbol, and show the glossary in English and Spanish columns. | unit |
| FR-008-17 | Unwanted | If `render_pages`, `validate_tables` or `knowledge_changes` gets a directory argument that is not an existing directory, if the export command gets an output path that is an existing directory or whose parent does not exist, or if the CLI gets an unknown subcommand or option, then the function shall raise `minephys.InputError` (CLI: exit code 2) and write nothing; no function shall write a file whose name comes from knowledge data other than a table stem that passed FR-008-02. | unit (hostile) |
| FR-008-18 | Ubiquitous | `python -m minephys.knowledge` shall offer `validate [PATH]`, `export [--out FILE]` (stdout by default) and `render --out-dir DIR`, exiting 0 on success, 1 on validation errors (every error listed) and 2 on usage errors. | unit (CLI) |
| FR-008-19 | Ubiquitous | `validate_tables(path=None)` shall validate the packaged knowledge, or a user directory with the same layout, and return a report listing every error (not only the first) with the row, entry and UNVERIFIED counts. | unit |
| FR-008-20 | Ubiquitous | `knowledge_changes(old_dir, new_dir)` shall return the sorted ids of rows whose `value`, `range` or `verification` differ between the two layouts, including added and removed rows, and nothing else; the foundation's release check (FR-000-30) shall use it. | unit |
| FR-008-22 | Optional | Where `catalogue/equations.yaml` or `catalogue/glossary.yaml` is absent because no entry has been written yet, the loader shall treat that catalogue as empty (`equations()` / `glossary()` return an empty tuple, the export lists no entry of it); no knowledge table or catalogue file shall be shipped without ≥ 1 row or entry, so an empty file that is present is rejected (FR-008-02, FR-008-04, FR-008-06). | unit |
| FR-008-21 | Ubiquitous | The foundation's docs generator (FR-000-23, `tools/gen_knowledge_docs.py`) shall produce its pages through `render_pages`, so that the docs, the export and the API share one code path. | unit |

## 4. Correctness properties

Generators (Hypothesis, `property_tests` of `thresholds.yaml`): valid tables, entries and terms built from the rules
(ids, Unicode text with Spanish accents, finite floats including subnormals and ±1e300, rational strings, ranges);
invalid ones made by one mutation of a valid one (drop, rename or retype a field, non-finite number, `min > max`, wrong
enum literal, unknown key, `verified_on` on an UNVERIFIED row).

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-008-01 | Validator agreement: the pure-Python validator accepts a table, bibliography entry, equation or glossary document if and only if the corresponding JSON Schema of `contracts/` accepts it (cross-file rules of FR-008-05 excluded from the comparison). | valid and one-mutation-invalid documents | TC-0 (exact) |
| P-008-02 | Lossless round trip: writing a valid generated table to YAML, loading it and exporting it returns the same field values, floats bit-identical and rational strings unchanged. | valid generated tables | TC-0 |
| P-008-03 | Determinism and order invariance: `export_json()` and `render_pages` are byte-identical across repeated calls, across fresh interpreters with different `PYTHONHASHSEED`, and across any permutation of the rows inside a table and of the entries in `references.bib`. | permutations of packaged and generated files | TC-0 |
| P-008-04 | Counting conservation: the export summary equals the number of rows per status, table and role, and the number of "UNVERIFIED" labels in the rendered pages equals the number of UNVERIFIED rows plus UNVERIFIED equations. | packaged and generated knowledge | TC-0 |
| P-008-05 | Bibliography round trip: rendering parsed entries back to BibTeX and parsing again gives the same entries. | generated entries with nested braces and accents | TC-0 |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-008-01 | Importing `minephys.knowledge` reads no knowledge file (foundation FR-000-06); loading happens on first use. | 0 `open` audit events for `.yaml`/`.bib`/`.json` at import | unit (audit hook, subprocess) |
| NFR-008-02 | Loading and validating all packaged knowledge is fast enough for an interactive start; later calls hit the cache. | cold ≤ 0.5 s, warm ≤ 1 ms (median of 5, CI runner) | `tools/bench.py` reference entry |
| NFR-008-03 | The loader works from the installed wheel in Pyodide and in NVIDIA Kit. | the knowledge smoke tests pass (foundation FR-000-25, FR-000-26) | Pyodide job; Kit smoke (local) |
| NFR-008-04 | The built wheel contains the catalogue files in addition to the tables and bibliography of FR-000-24. | both catalogue files present | wheel-content test |
| NFR-008-05 | Runtime imports are the standard library, PyYAML and NumPy; `jsonschema` is used only in tests. | 0 other top-level modules imported | contract test (subprocess import audit) |
| SC-008-01 | Integrity of the packaged knowledge at every release. | `validate` reports 0 errors; 0 verified rows or equations without a `knowledge` marker | CI |
| SC-008-02 | Docs agree with code. | 0 differences reported by the generator's `--check` (FR-000-23) built on FR-008-21 | CI |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-008-01 | `src/minephys/knowledge/catalogue/equations.yaml` | `specs/008-knowledge/contracts/knowledge-equations.schema.json` (draft; promoted to `contracts/knowledge-equations.schema.json` by T-008-001) | module specs (maintainer) → loader, export, pages, PitStudio equation explorer |
| DC-008-02 | `src/minephys/knowledge/catalogue/glossary.yaml` | `specs/008-knowledge/contracts/knowledge-glossary.schema.json` (draft; promoted to `contracts/knowledge-glossary.schema.json` by T-008-001) | maintainer → export, pages, PitStudio glossary (EN/ES) |
| DC-008-03 | `python -m minephys.knowledge export` output | `specs/008-knowledge/contracts/knowledge-export.schema.json` (draft; promoted to `contracts/knowledge-export.schema.json` by T-008-001; references the foundation's `knowledge-table` and `bibliography-entry` schemas and DC-008-01/02) | `minephys` → PitStudio docs build and `/knowledge` route (pinned version) |

The tables and the bibliography follow the foundation's DC-000-02 (`contracts/knowledge-table.schema.json`) and
DC-000-03 (`contracts/bibliography-entry.schema.json`); this spec implements their validator and does not redefine them.

## 7. Edge cases and assumptions

**Equation rules** (DC-008-01). A mapping with `schema_version` (const 1), `title`, `licence` (`CC-BY-4.0`) and
`equations` (list, ≥ 1). Each entry: `id` (`^[a-z][a-z0-9_]*$`, unique), `title` (English), `domain` (one of
`haulage`, `blasting`, `geotech`, `bulk`, `comminution`, `environment`, `planning`), `latex` (non-empty), `symbols`
(list ≥ 1 of `{symbol, meaning, units}`), `function` (dotted path `minephys.<module>.<name>`, resolving to an exported
object), `citation` (bibliography key), `page`, `verification` (`verified` or `UNVERIFIED`), `verified_on`
(`YYYY-MM-DD`, exactly when verified), `rows` (optional list of table row ids), `notes` (optional). No other field.

**Glossary rules** (DC-008-02). A mapping with `schema_version` (const 1), `title`, `licence` and `terms` (list ≥ 1).
Each term: `id` (unique), `domain` (one of the seven or `general`), `term_en`, `term_es`, `definition_en`,
`definition_es` (non-empty, ≤ 1,000 characters each), `citation` (optional key), `see_also` (optional list of term
ids). No other field.

**BibTeX subset** (FR-008-03): `@type{key, field = {…} | "…" | digits, …}` with nested braces; `%` comments and blank
lines between entries; field names case-insensitive; UTF-8 text. `@string`, `@preamble` and `@comment` are not
supported, so macros cannot hide values.

**Hardened YAML** (FR-008-07): PyYAML's safe loader is extended because its defaults would hide errors (the last
duplicate key silently wins; aliases share objects and allow alias bombs).

**Assumptions and edge cases**

- The catalogues live under `knowledge/catalogue/` so that the foundation's table globs (`knowledge/*.yaml`,
  `knowledge/share-alike/*.yaml`) contain tables only.
- No knowledge file is shipped empty: a table needs ≥ 1 row (foundation data model) and a catalogue ≥ 1 entry; a
  catalogue file is created by the first module knowledge task that adds an entry, and until then the loader treats it
  as empty (FR-008-22). A domain without published constants therefore ships no table; the planning module (spec 007)
  is such a domain and appears in the catalogues only.
- `get_value` is the only access path for model defaults (foundation FR-000-19: no other literals in model code).
  Rows of role `limit` (validity bounds, unit tripwires) and `conversion` (exact definitions) do not warn when UNVERIFIED,
  because they gate warnings or are exact by definition; their status is still shown everywhere else.
- A verified row is pinned by any test carrying `@pytest.mark.knowledge("<id>")` (FR-000-21). Each module's knowledge
  task pins its verified rows with a contract test that compares the table value with the value printed in the source
  (transcribed into the test); worked-example tests add further pins.
- Values keep the units of their source; the export carries the units string and converts nothing.
- The export carries the package version (FR-000-27); PitStudio pins the version, so its drift check compares like
  with like.

## 8. Clarifications log

- Resolved (foundation alignment): the table and bibliography formats are the foundation's DC-000-02 and DC-000-03;
  this spec's first draft had defined its own row format (with `label`, `table` values, `range.default` and a
  `pinned_by` field) and is aligned: `quantity` replaces `label`, `role` and `verified_on` are added, multi-column
  published tables become one row per coefficient, range defaults are the caller's or the module's documented choice,
  and pins are `knowledge` test markers.
- Resolved: the docs generator (FR-000-23) and the changelog check (FR-000-30) are foundation requirements; this spec
  provides the functions they call (`render_pages`, `knowledge_changes`) instead of second copies of the checks.
- Resolved: the planned API names `load_table`, `get_parameter`, `list_tables`, `bibliography`, `validate_tables`,
  `glossary` are kept; `list_parameters`, `get_value`, `equations`, `export`, `export_json`, `render_pages`,
  `knowledge_changes`, `KnowledgeSchemaError` and `UnverifiedParameterWarning` are added.
- Resolved: PitStudio's knowledge page lists "equations" and "glossary EN/ES" as generated from `minephys`; the docs
  had no format for them, so DC-008-01 and DC-008-02 define it.
- Resolved: "UNVERIFIED rows must be surfaced, never hidden" is made testable by FR-008-12 (warning on use), FR-008-13
  (no default filtering), FR-008-16 (labels and counts) and P-008-04 (label conservation).
- Integration 2026-10-07: draft schemas written for DC-008-01, DC-008-02 and DC-008-03
  (`specs/008-knowledge/contracts/`, valid and hostile examples indexed in `examples/index.json`); the export
  references the foundation drafts (`knowledge-table.schema.json` for each table, `bibliography-entry.schema.json`
  for each entry) and this spec's `knowledge-equations.schema.json#/$defs/equation` and
  `knowledge-glossary.schema.json#/$defs/term`. Ambiguities resolved with the stricter reading: the `equations` and
  `terms` lists keep at least one entry as stated above, so the "empty-but-valid" catalogue headers of T-008-001
  need one seed entry each; the glossary `licence` is `CC-BY-4.0` (constitution principle 9) and its `id` follows the
  row-id pattern `^[a-z][a-z0-9_]*$`; symbol units follow the foundation's units rule (`1` for dimensionless); the
  optional `rows` and `see_also` lists are non-empty when present and hold unique ids; `term_en` and `term_es` are
  single-line and non-blank; caps chosen here: 500 equations, 64 symbols and 64 rows per equation, LaTeX 2,000
  characters, 1,000 terms, 16 `see_also` ids; the export holds exactly `version`, `tables`, `equations`, `glossary`,
  `bibliography` and `summary` (`rows` and `equations` as total and UNVERIFIED counts, `terms`, `references`,
  `per_table`, and `per_role` with all four roles), with no timestamp or other field.
- Integration 2026-10-07 (2): the "≥ 1 entry" rule stays. A table or catalogue file is shipped only when it has ≥ 1 row or entry (no
  empty files); an absent catalogue reads as empty (new FR-008-22, task T-008-016). This supersedes the "empty-but-
  valid catalogue headers" of T-008-001 and the "one seed entry each" note above: T-008-001 writes no catalogue file.

## 9. Changes (only for features that modify earlier behaviour)
### ADDED Requirements
(none — new module)
### MODIFIED Requirements
(none)
### REMOVED Requirements
(none)
