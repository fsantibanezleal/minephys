# Research 000 — decisions behind the library foundation
Spec: ./spec.md

The science of each model is in `docs/theory/README.md` and in the module specs (001–008). This page records the
library-level decisions, their evidence and the alternatives rejected.

## 1. Runtime dependencies and runtimes

| Decision | Evidence | Alternatives rejected |
|---|---|---|
| NumPy (≥ 2.0) and PyYAML (≥ 6.0) only | Both are in the Pyodide distribution; the consumer's measured Pyodide load set lists NumPy 2.96 MB and PyYAML 0.11 MB. Both install into Kit's embedded Python 3.12 | SciPy (adds tens of MB to the browser load set and is a heavy Kit install); pandas (same); `pint` or another units library (a third dependency; units are enforced by names, docstrings and tests instead); `numba` (no Pyodide support) |
| CPython 3.12–3.14 | `requires-python = ">=3.12"`; Kit's embedded Python is 3.12 (PyPI `omniverse-kit` 110.3 pins `==3.12.*`, docs reference page) | dropping 3.12 (breaks Kit) |
| Pure-Python wheel `py3-none-any` | one artefact for every runtime | compiled extensions (break Pyodide and need per-platform builds) |
| Pyodide smoke test in CI under Node 24 | the Pyodide npm package runs headless in Node; the consumer already self-hosts the same runtime | a browser-driven test (slower, needs a browser in CI) |

## 2. Error, warning and validity policy

- **Raise on non-finite inputs.** A browser or pipeline that receives NaN shows a blank chart or poisons an aggregate
  silently. Raising at the boundary names the argument and the element. Rejected: NumPy-style propagation; a
  `nan_policy` argument (complexity without a second user).
- **Warn outside the validity range, raise outside the physical domain.** Empirical models are routinely evaluated at
  the edge of their data (for example large haul trucks against AP-42's weight range); a warning keeps the result
  available and the extrapolation visible. Physical impossibilities (negative mass, an orifice smaller than the
  empty annulus) have no meaningful result and raise.
- **Unit tripwires.** Plain floats carry no units, so wrong units are caught by plausibility bounds stated per module
  (for example a grade above 0.3 as a fraction is almost certainly a percentage). Tripwires warn and say so; they are
  not presented as sourced validity limits.
- **Exceptions subclass the built-ins** (`ValueError`, `TypeError`, `RuntimeError`), so generic callers keep working.

## 3. Tolerance classes

Closed forms in this library are short chains of products, powers, logarithms and exponentials. For such chains the
relative forward error is bounded by roughly (number of operations) × (condition number) × 1.1e-16. With ≤ 100
operations and relative condition numbers ≤ 10 this is ≲ 1e-13, so TC-1 (rtol 1e-12) leaves a tenfold margin. Values
printed in sources carry their own rounding, so TC-2 uses half a unit of the last printed digit. Monte-Carlo checks
(TC-4) use 4 standard errors because the estimator's error is known in closed form and a fixed seed makes the test
deterministic. The ODE class (TC-5) is set by the step-halving behaviour of RK4 (global error ∝ Δt⁴).

## 4. Verification policy for constants

- A row becomes `verified` only after its value was read on the primary source (page recorded) and a test pins it.
- During specification (2026-10-06) the module writers tried to read each primary source with a fetch tool. Blocked
  or paywalled sources were skipped, never retried, and their rows stay `UNVERIFIED`. Each module spec's §7 lists the
  outcome per constant.
- Rows from paywalled standards (CEMA, ISO 5048) hold only the public equation form and never the standard's tables.

## 5. Versioning and API stability

- `X.YY.ZZZ` is computed by `tools/release.py` from Conventional Commits (breaking → `X`, feature → `YY`, other →
  `ZZZ`), as documented in `docs/reference/README.md`.
- An API snapshot (DC-000-04) makes "breaking" mechanical: a removed name, parameter or default is detectable without
  human judgement.
- A changed knowledge value is treated like a behaviour change, because downstream results change.

## 6. Open measurements (resolved in the build phase, not blocking)

| Item | How it is measured |
|---|---|
| Actual import time and wheel size | T-000-011, T-000-017 |
| Pyodide version in the CI job | pinned in the job; the spec only requires the 314.0.x series or newer |
| Latency of the iterative models at reference size | T-000-022 |
