# AGENTS.md — how to work in minephys

Guide for AI coding agents (and humans) working in this repository. Keep it short; depth lives in `docs/` and
`specs/`.

## What this repo is

`minephys` is a pure-NumPy Python library of sourced, tested reference implementations of mining-engineering models,
with cited parameter tables (`src/minephys/knowledge/`). It has no web app, no data pipeline and no trained models. It
runs on CPython 3.12–3.14, inside Pyodide in the browser, and inside NVIDIA Kit.

Read `README.md`, `STRUCTURE.md`, `docs/README.md` and `specs/constitution.md` first.

## Commands

| Task | Command |
|---|---|
| Set up (Windows / Linux) | `scripts/bootstrap.ps1` / `scripts/bootstrap.sh` (checks uv + git, syncs the venv, runs the tests) |
| Tests | `uv run pytest -m "not gpu"` |
| Lint · format · types | `uv run ruff check .` · `uv run ruff format .` · `uv run mypy src` |
| Traceability | `uv run python tools/trace.py --check` |
| Test-first integrity | `uv run python tools/check_tdd.py` |
| Repo and docs hygiene | `uv run python tools/check_repo.py` · `uv run python tools/check_docs.py` |
| Build the wheel | `uv build` |

## Non-negotiable rules

1. **Spec before code.** Every behaviour has a requirement ID in `specs/NNN-*/spec.md` (EARS). Change the spec first.
2. **Acceptance-test-first.** For each task `T-NNN-xxx`:
   - write failing tests that reference its IDs (`@pytest.mark.req("FR-…")`);
   - lock them (`python tools/lock_tests.py specs/NNN-*/tests.lock <files>`);
   - commit `test(T-…): … [red]`;
   - implement without touching the locked tests, then commit `feat(T-…): … [green]`.
3. **Independent oracles.** Expected values come from worked examples in the primary source (with page), analytical
   results, reference implementations or hand calculation, never from running the code under test.
4. **Never weaken a test.** If a locked test is wrong, write it in `specs/test-change-requests.md` and stop the task.
5. **Every constant is cited.** Each knowledge-table row records:
   - its value or range, with units;
   - its citation and page;
   - its verification status;
   - the code symbol that uses it.

   Unverified rows are flagged and never presented as verified.
6. **Pure and portable.** The only runtime dependencies are NumPy and PyYAML. Adding a dependency is a spec change.
   Nothing may break Pyodide (no compiled extensions of our own, no threads, no filesystem writes at import).
7. **SI units at the API.** Inputs and outputs are SI unless a function name says otherwise. Units appear in every
   docstring.
8. **Small, verified steps.** Run the relevant tests before every commit. Use Conventional Commits with task and
   requirement IDs.
9. **No secrets, no machine paths, no files > 10 MB, no Git LFS** (`tools/check_repo.py`).
10. **Ask before installing software on the maintainer's machine.** Project-local installs (`uv sync`) are fine.

## Layout

See `STRUCTURE.md`:
- `src/minephys/` holds one sub-package per domain and `knowledge/`;
- the other top-level folders are `tests/`, `specs/`, `docs/`, `tools/`, `scripts/` and `.github/`.
