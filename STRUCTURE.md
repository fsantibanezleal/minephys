# Repository structure

`minephys` is a pure-NumPy library, so it uses the package layout: no web app, data pipeline, models or deployment.

| Area | Purpose | Status |
|---|---|---|
| `src/minephys/` | The library: one sub-package per domain (`haulage`, `blasting`, `geotech`, `bulk`, `comminution`, `environment`, `planning`) and `knowledge/` (cited parameter tables + bibliography + loader). Depends only on NumPy and PyYAML | active (models are added test-first in the build phase) |
| `tests/` | Unit, property, metamorphic, contract and parity tests; worked examples from primary sources are the oracles | active |
| `specs/` | Specifications: constitution, foundation, one spec per module, traceability | active |
| `docs/` | The wiki: theory, reference (API), methods, guides, data contract (knowledge-table schema), architecture and decisions | active (skeleton; filled per model) |
| `tools/` | Repository checks used by CI and hooks: traceability, test-first integrity, locked tests, repository and docs hygiene, release | active |
| `scripts/` | Local bootstrap (`bootstrap.ps1`, `bootstrap.sh`) | active |
| `.github/` | CI (checks, tests on Python 3.12–3.14, a test run against the built wheel), Dependabot, templates | active |

Releases go to PyPI (TestPyPI first) through trusted publishing; until the first release, consumers depend on a git
tag.
