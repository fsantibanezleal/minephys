# Contributing to minephys

Thanks for your interest. This is a research library maintained by one person; issues and pull requests are welcome.

## Set up

Run `scripts/bootstrap.ps1` (Windows) or `scripts/bootstrap.sh` (Linux/macOS). The scripts check that `uv` and `git`
are present (they never install system software for you), sync the development environment and run the tests. The
library itself needs only NumPy and PyYAML.

## How changes are made

1. **Spec first.** Behaviour is specified in `specs/NNN-*/spec.md` with requirement IDs (EARS). Open an issue or a
   spec change before code.
2. **Tests first.** Failing tests referencing the requirement IDs are committed and locked (`[red]`). The
   implementation then makes them pass (`[green]`). Expected values come from an independent oracle: a worked example
   in the cited source, an analytical result or a reference implementation.
3. **Cite every constant.** A new parameter goes into `src/minephys/knowledge/*.yaml` with:
   - its value or range and units;
   - its citation (DOI/URL and page) and verification status;
   - its entry in `references.bib`.
4. **Commits.** Use [Conventional Commits](https://www.conventionalcommits.org/) with the task id, e.g.
   `test(T-003-004): FR-003-01 failing worked example [red]`.
5. **Branches.** Work on `task/<slug>`, open a PR into `develop`, then a release PR into `main`.
6. **Before a PR**, run:
   - `uv run pytest -m "not gpu"`
   - `uv run ruff check .`
   - `uv run mypy src`
   - `uv run python tools/trace.py --check`
   - `uv run python tools/check_tdd.py`
   - `uv run python tools/check_repo.py`
   - `uv run python tools/check_docs.py`

## Licence of contributions

Inbound = outbound: contributions are accepted under the repository's licences (code Apache-2.0; docs and tables
CC-BY-4.0, with share-alike sources kept separate).

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
