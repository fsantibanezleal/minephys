# minephys — Constitution
Version: 2.0.0 · Ratified: 2026-10-04 · Last amended: 2026-10-06 (MAJOR: principles 1, 6, 7, 8 and 9 redefined for a
library; the application-template principles "Real, not demo", "Neutral contracts", "Static delivery", "Honesty" with
an access gate and dataset "Licence hygiene" are removed)

Invariants every change must respect. Conflicts: this file wins over plans and specs; amending it is a PR that bumps
its version (MAJOR = a principle removed or redefined) and lists the affected specs.

## Core principles (non-negotiable)
1. **Real, sourced models.**
   - Every model is implemented from its primary source, with its equation, assumptions and validity range written
     in its specification and in its docstring.
   - Every numerical constant a model uses lives in a knowledge-table row (`src/minephys/knowledge/*.yaml`) with its
     value or range, units, citation and page, verification status and the code symbol that uses it. Mathematical
     constants and exact unit definitions are the only literals allowed in model code.
   - A row is `verified` only when its value was read on the primary source and a test pins it. Every other row is
     `UNVERIFIED`, is flagged wherever it is shown, and is never used as a silent default for a site- or
     material-specific parameter (the caller must pass it).
   - Worked examples from the primary source, with page, are the preferred oracles. Where none is readable, the oracle
     is an analytical result or a hand calculation that does not depend on an unverified value.
   - Outside a model's validity range the library warns or raises, as its specification states; it never returns a
     silent extrapolation.
2. **Spec before code.** No behaviour without an approved requirement ID (`FR/NFR/SC/P/DC-NNN-xx`, EARS).
3. **Acceptance-test-first.** Every requirement-bearing task starts with committed, failing, locked tests that
   reference its IDs (`[red]`); the implementation (`[green]`) never modifies locked tests.
4. **Independent oracles.** Expected values come from analytical solutions, reference implementations, published
   values or hand calculation — never from running the code under test.
5. **Determinism & explicit tolerances.** Seeds, deterministic algorithms where available, pinned data checksums;
   numerical tolerances (rtol/atol per dtype) are stated and justified in the spec.
6. **Purity and portability.**
   - The only runtime dependencies are NumPy and PyYAML. Adding one is a MAJOR change to this constitution.
   - The package is pure Python (no compiled extension of its own) and runs unchanged on CPython 3.12–3.14, in
     Pyodide and inside NVIDIA Kit's embedded Python.
   - Importing any module performs no file, network or process I/O, starts no thread and mutates no global state;
     the knowledge tables are package data read lazily on first use.
   - Public functions are pure functions of their arguments. Randomness enters only through a caller-supplied seed or
     `numpy.random.Generator`.
7. **SI units at the API.**
   - Inputs and outputs are SI (dimensionless quantities as fractions, angles in radians) unless the function name
     says otherwise (`_cm`, `_deg`, `_pct`, `_in_s`, `_per_h`, …).
   - Every parameter and return value has its unit in the docstring.
   - Sources published in other units are stored in the tables as published, converted once at the function
     boundary, and every conversion is unit-tested.
8. **A stable public API and honest versions.**
   - The public API is what each package's `__all__` exports; everything else is private.
   - Releases are `X.YY.ZZZ`: a breaking change (removed or renamed public name, changed signature, changed default,
     changed units) bumps `X`; a feature bumps `YY`; a fix bumps `ZZZ`.
   - A public name or default is removed only after at least one `YY` release in which it emits a
     `DeprecationWarning` that names its replacement and the removal version.
   - A change to a knowledge value, range or verification status is a `CHANGELOG.md` entry that names the row, because
     it can change results downstream.
9. **Licence hygiene for code, tables and sources.**
   - Code is Apache-2.0. Documentation and knowledge tables are CC-BY-4.0, and every table declares its licence.
   - Values taken from share-alike sources live in separate table files under their own licence and never in a
     CC-BY-4.0 table.
   - Paywalled standards and books are cited; only the public form of their equations is implemented, and their text
     and tables are never reproduced.
   - The library ships no third-party data set; tables hold cited values, each traceable to its source.
10. **Simplicity.** Use frameworks directly; no abstraction without two concrete users; structural and behavioural
    changes in separate commits.

## Affected specifications (2.0.0)
- `000-foundation` is rewritten as the library-level foundation. Its application-template placeholder rows
  (`US-000-1`, `FR-000-01`…`FR-000-04`, `NFR-000-01`, `NFR-000-02`, `SC-000-01`, `DC-000-01`) are retired, never reused.
- `001-haulage`, `002-blasting`, `003-geotech`, `004-bulk`, `005-comminution`, `006-environment`, `007-planning` and
  `008-knowledge` are written under this version.

## Quality gates
Thresholds live in `specs/000-foundation/thresholds.yaml` and only ratchet upwards. CI is authoritative
(`tools/trace.py --check`, `tools/check_tdd.py --replay`, `tools/check_repo.py`, `tools/check_docs.py`, tests on
CPython 3.12–3.14, the tests against the built wheel, and the Pyodide smoke test).
