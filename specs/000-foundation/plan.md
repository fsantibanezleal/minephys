# Plan 000 — Foundation: minephys
Spec: ./spec.md

## Summary
The foundation delivers what every module relies on: the exception and warning classes and the input-validation
helpers (FR-000-10…17, FR-000-32), the purity and import guarantees (FR-000-05, FR-000-06), the knowledge-table and
bibliography contracts with their honesty checks (DC-000-02, DC-000-03, FR-000-19…23, FR-000-31), the packaging and
runtime checks (FR-000-24…27, NFR-000-03…06) and the release checks (FR-000-28…30, DC-000-04). A shared contract
suite lets each module spec prove the cross-cutting properties (P-000-01…04) for its own functions.

## Technical context
Runtime: CPython 3.12–3.14, Pyodide (314.0.x series) and NVIDIA Kit's embedded Python 3.12 · runtime dependencies NumPy
≥ 2.0 and PyYAML ≥ 6.0 only · dev group: pytest, Hypothesis, pytest-cov, mypy, ruff, jsonschema (contract tests only)
and a mutation tool chosen and locked in T-000-023 · target: PyPI wheel `py3-none-any`; no GPU, no web app.

## Constitution check

| Principle | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | FR-000-19…22 make every constant a cited row and keep UNVERIFIED parameters out of defaults |
| 2 Spec before code | yes | every behaviour below has an ID |
| 3 Acceptance-test-first | yes | every task in `tasks.md` is a `[red]`/`[green]` pair with its own test file |
| 4 Independent oracles | yes | the contract tests check against the JSON Schemas (a reference implementation: `jsonschema`) and against fixtures written by hand; no expected value comes from the code under test |
| 5 Determinism and tolerances | yes | tolerance classes TC-0…TC-6 (spec §4); FR-000-18 for seeds |
| 6 Purity and portability | yes | FR-000-05, FR-000-06, FR-000-24, FR-000-25, NFR-000-05 |
| 7 SI units at the API | yes | FR-000-08, P-000-05, suffix list A2 |
| 8 Stable API and versions | yes | FR-000-27…30, DC-000-04 |
| 9 Licence hygiene | yes | FR-000-31 |
| 10 Simplicity | yes | one validation helper module and one contract suite; no plugin system |

## Design

| Component | Path | Requirements |
|---|---|---|
| Exceptions, warnings, `__version__` | `src/minephys/_errors.py`, `src/minephys/__init__.py` | FR-000-27, FR-000-32 |
| Input validation helpers (`as_float_array`, `check_finite`, `check_domain`, `check_option`, `check_size`, `warn_validity`) | `src/minephys/_validate.py` | FR-000-07, FR-000-10…16 |
| Solver helper (fixed-point and bracketed root with `ConvergenceError`) | `src/minephys/_solve.py` | FR-000-17 |
| Random-source helper (`as_generator(rng)`) | `src/minephys/_random.py` | FR-000-18 |
| Unit conversions (`units` table + helpers `deg_to_rad`, `pct_to_fraction`, …) | `src/minephys/units.py`, `knowledge/units.yaml` | P-000-05, A1, A2 |
| Deprecation helper | `src/minephys/_deprecate.py` | FR-000-29 |
| Schemas | `contracts/knowledge-table.schema.json`, `contracts/bibliography-entry.schema.json`, `contracts/api-snapshot.schema.json` | DC-000-02…04 |
| Honesty checks (literal audit, verified-row pinning, defaults audit, licence) | `tools/check_knowledge.py` | FR-000-19, FR-000-21, FR-000-22, FR-000-31 |
| Docs generator | `tools/gen_knowledge_docs.py` → `docs/reference/knowledge/*.md` | FR-000-23 |
| API snapshot and value-change checks | `tools/check_api.py`, `tools/release.py --check` | FR-000-28, FR-000-30 |
| Benchmark runner | `tools/bench.py` | NFR-000-07 |
| Contract suite used by every module | `tests/_contract_suite.py` (strategies, hostile generators, purity and vectorisation checks) | P-000-01…04 for each module |
| Pyodide runner | `tests/pyodide/run_smoke.mjs` + `tests/pyodide/smoke.py` | FR-000-25 |

Validation runs once per call at the function boundary; model code receives float64 arrays that are finite and
in-domain. Markers registered in `pyproject.toml`: `req`, `oracle`, `knowledge`, `gpu`, `slow`, `pyodide`, `kit`.

## Test strategy

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-000-05, P-000-02 | property | invariant (repeat call, input copy comparison) | Hypothesis |
| FR-000-06 | unit | analytical (audit-event log of a fresh interpreter must be empty for the listed events) | `sys.addaudithook`, subprocess |
| FR-000-07, P-000-01, P-000-03 | property | invariant (elementwise loop; float32 → float64 cast) | Hypothesis |
| FR-000-08, FR-000-09 | contract | hand-written rules (numpydoc section parse) | pytest |
| FR-000-10…15 | hostile | invariant (every generated hostile input must raise the named class with the right `argument`) | Hypothesis + `tests/_contract_suite.py` on fixture functions |
| FR-000-16 | unit | hand calculation (fixture function with a stated bound) | `pytest.warns` |
| FR-000-17 | unit | analytical (fixture iteration with a known divergent map) | pytest |
| FR-000-18, P-000-04 | property | invariant | Hypothesis |
| FR-000-19 | contract | hand-written allowlist | `ast` |
| FR-000-20, DC-000-02, DC-000-03 | contract | reference implementation (`jsonschema` 2020-12 validator) vs the pure-Python validator on fixtures | pytest |
| FR-000-21, FR-000-22, FR-000-31 | contract | hand-written fixture tables and test trees | pytest |
| FR-000-23 | unit | hand-written expected page for a fixture table | pytest |
| FR-000-24, NFR-000-04, NFR-000-05 | contract (wheel job) | analytical (zip listing, metadata) | `zipfile`, `importlib.metadata` |
| FR-000-25 | pyodide | worked-example oracles of the module specs (one per module) | Node 24 + Pyodide |
| FR-000-26 | kit | same smoke subset | local Kit, skip "not run" otherwise |
| FR-000-27 | unit | analytical (VERSION file and metadata) | pytest |
| FR-000-28, FR-000-29, DC-000-04 | unit | hand-written fixture snapshots | pytest |
| FR-000-30 | unit | hand-written fixture tables and changelogs | pytest |
| FR-000-33, SC-000-02 | contract | marker inventory over the test tree | pytest collection hook |
| P-000-05 | property | analytical (exact definitions: inch = 0.0254 m, pound = 0.45359237 kg, US gallon = 231 in³) | Hypothesis |
| NFR-000-03 | unit (slow) | measurement | `python -X importtime` |
| NFR-000-07 | release | measurement | `tools/bench.py` |
| NFR-000-08 | CI | measurement | pytest-cov, mutation tool, Hypothesis profile |
| NFR-000-09 | CI | measurement | mypy |

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Pure-Python validator next to JSON Schemas | the runtime may not depend on a schema engine (principle 6) | shipping `jsonschema` would add a runtime dependency |
| Contract suite shared by modules | the cross-cutting properties are the same for ~80 functions | per-module copies would drift |
| Pyodide job in CI | FR-000-25 must be evidence, not a claim | a manual browser check is not repeatable |
