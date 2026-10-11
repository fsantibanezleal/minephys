# Spec 000 — Foundation: minephys
Status: Clarified · Tier: L · Approved: —

The library-level specification, written from the approved solution plan (§13 companion package, §17 validation plan)
under constitution 2.0.0. Every module spec (`specs/NNN-*/`) is a child of this one and inherits its requirements,
error policy, tolerance classes and data contracts. Companion documents: [plan](plan.md), [tasks](tasks.md),
[research](research.md), [data model](data-model.md), [quickstart](quickstart.md).

## 1. Intent

`minephys` is a small, pure-NumPy Python library of **sourced, tested reference implementations of classical
open-pit mining models**, with machine-readable parameter tables in which every value carries its units, citation and
page, verification status and the code symbol that uses it. It answers one question for its users: *what does the
classical model from source X give for these inputs, and where does each number come from?* One model has one
implementation, and the same wheel runs in notebooks, data pipelines, the browser (Pyodide) and NVIDIA Kit.

**Who benefits:** the PitStudio pipelines, studio and browser explorer (which port the models to TypeScript and test
the ports against this library); the maintainer's other mining libraries; students and engineers who want an equation,
its source page and a worked example they can reproduce; reviewers who need every constant traceable.

**Modules** (one child spec each): haulage, blasting, geotech, bulk handling, comminution, environment, planning and
the knowledge tables (§9).

**Out of scope:**
- design, regulatory or safety-critical use (outputs are educational and reference-grade, valid only inside the ranges
  each model states);
- a mine-planning package, an optimiser for full block models, a discrete-event simulator or any trained model;
- proprietary data (OEM rimpull charts, vendor curves) and the text or tables of paywalled standards;
- "better than" comparisons between methods (they belong to the consumers that evaluate them);
- GPU code, compiled extensions, file or network I/O outside reading the package's own tables.

## 2. Users and user stories

| ID | Story | Priority |
|---|---|---|
| US-000-2 | As a PitStudio pipeline or studio developer, I want to import the same model functions in CPython 3.14 environments and in NVIDIA Kit's embedded Python 3.12, so that every stage computes a model with one implementation. | P1 |
| US-000-3 | As the PitStudio web app, I want to load the `minephys` wheel in Pyodide and to test my TypeScript ports against `minephys` outputs, so that the browser shows the same numbers as the pipeline. | P1 |
| US-000-4 | As the maintainer of other public mining libraries, I want to depend on `minephys` for physics and cited constants instead of copying them, so that a corrected value propagates everywhere. | P2 |
| US-000-5 | As a student or engineer, I want each function to document its equation, units, source page and validity range, and to reproduce the source's worked example, so that I can learn and check the model. | P1 |
| US-000-6 | As a reviewer or citer, I want every constant traceable to a citation and page with its verification status, and generated knowledge pages that flag every UNVERIFIED value, so that nothing is presented as more than it is. | P1 |
| US-000-7 | As a consumer pinning a release, I want `X.YY.ZZZ` versions, deprecation warnings before removals and a changelog entry for every changed value, so that upgrades never change results silently. | P2 |

## 3. Library-level requirements (EARS)

| ID | Pattern | Requirement | Verification |
|---|---|---|---|
| FR-000-05 | Ubiquitous | Every public function shall be a pure function of its arguments: identical arguments give bitwise-identical results, input arrays are never modified, no global state is read or written, and no I/O happens except `minephys.knowledge` reading the package's own data files. | property (P-000-02) + unit |
| FR-000-06 | Ubiquitous | Importing `minephys` or any public subpackage in a fresh interpreter shall raise no `open` audit event for a `.yaml`, `.bib` or `.json` file, no `socket.*`, `subprocess.Popen`, `os.system`, `os.posix_spawn` or `_thread.start_new_thread` audit event, and shall read no knowledge table (tables load lazily on first use). | unit (audit hook, subprocess) |
| FR-000-07 | Ubiquitous | Every public elementwise function shall accept Python real scalars, NumPy real scalars and NumPy arrays of any real dtype (upcast to float64), broadcast them by NumPy rules, and return `numpy.float64` when all inputs are scalars and a float64 `ndarray` of the broadcast shape otherwise. | property (P-000-01, P-000-03) |
| FR-000-08 | Ubiquitous | Every public function shall take and return SI units (dimensionless quantities as fractions, angles in radians, rates per second) unless its name ends with a unit suffix from the closed list of §8 (A2); its docstring shall state the unit of every parameter and of every returned quantity in square brackets (for example `mass : float [kg]`). | contract (docstring audit) |
| FR-000-09 | Ubiquitous | Every public model function's docstring shall contain the numpydoc sections `Parameters` and `Returns` and the model-card sections `Equation`, `Source` (BibTeX key and page), `Validity` and `Knowledge rows` (the row ids it reads by default, or `none`). | contract (docstring audit) |
| FR-000-10 | Unwanted | If a numerical argument is NaN or ±inf, or an array argument contains such an element (except an argument that its module spec allows to be `+inf`), then the function shall raise `minephys.InputError` whose `argument` attribute and message name the argument and, for arrays, the flat index of the first offending element. | hostile (Hypothesis) |
| FR-000-11 | Unwanted | If a numerical argument is not real-numeric (string, bytes, `None` where a number is required, complex, bool, object, datetime or timedelta dtype), or a flag or mask argument that its module spec declares boolean is not boolean, then the function shall raise `minephys.InputTypeError` naming the argument. | hostile |
| FR-000-12 | Unwanted | If array arguments cannot be broadcast together, or an argument does not have the rank its function requires (for example a 2-D array where per-slice 1-D arrays are required), then the function shall raise `minephys.InputError` naming the arguments and their shapes. | hostile |
| FR-000-13 | Unwanted | If an aggregate function (one that reduces over slices, segments, samples, stations or time) receives fewer elements than its specified minimum, or a count or size above its specified cap, then it shall raise `minephys.InputError` naming the argument, the received size and the bound; an elementwise function given empty arrays shall return an empty float64 array of the broadcast shape. | hostile |
| FR-000-14 | Unwanted | If a value lies outside the physical domain that its function's specification states (for example a negative mass, a fraction outside [0, 1], an angle outside its interval), then the function shall raise `minephys.InputError` naming the argument, the violated bound and the received value. | hostile |
| FR-000-15 | Unwanted | If a string option (model variant, standard, station type) is not one of its allowed values, then the function shall raise `minephys.InputError` listing the allowed values; matching is exact and case-sensitive. | hostile |
| FR-000-16 | Unwanted | If an input lies inside the physical domain but outside the validity range stated by the model's source, or trips a unit tripwire defined in a module spec, then the function shall emit `minephys.ValidityWarning` naming the argument, the received value or range and the bounds with their knowledge-row id (or `tripwire`), and shall still return the result, unless the module spec requires an error. | unit (`pytest.warns`) |
| FR-000-17 | Unwanted | If an iterative solver does not meet its tolerance within its iteration cap, then it shall raise `minephys.ConvergenceError` carrying `last_iterate`, `residual` and `iterations`, and shall never return an unconverged value. | hostile |
| FR-000-18 | Ubiquitous | Every function that samples shall take an `rng` argument (a `numpy.random.Generator` or an integer seed, with no default), shall draw only from it, and shall return bitwise-identical output for the same seed and NumPy version. | property (P-000-04) |
| FR-000-19 | Ubiquitous | Model code under `src/minephys/` shall contain no floating-point literal other than those in `tools/literal_allowlist.txt`, which may list only (each entry with a one-line reason): structural constants of a formula (0, 0.5, 1, 2, 3, 4 and other small exact integers or simple fractions), decimal SI prefixes, exact mathematical constants (π, e, √2 and their exact rational multiples, or literals equal to them to float64 rounding; `math.pi` and `math.e` are preferred), and numerical tolerances and tiny guards of the solvers (convergence tolerances, division-by-zero and underflow guards such as 1e-12); every physical or empirical constant (material property, regression coefficient, site factor, unit conversion, threshold) shall be read from a knowledge row and shall never be allowlisted. | contract (AST audit + allowlist review) |
| FR-000-20 | Ubiquitous | The library shall ship its knowledge tables and bibliography as package data conforming to DC-000-02 and DC-000-03, and the CI contract test shall report every violation with file, row id and field. | contract |
| FR-000-21 | Unwanted | If a knowledge row is `verified` but no test carries `@pytest.mark.knowledge("<row id>")`, or a row's `symbol` does not resolve to an exported object, or a row cites a BibTeX key absent from `references.bib`, then CI shall fail naming the row. | contract |
| FR-000-22 | Unwanted | If a model card lists under `Knowledge rows` a row whose role is `parameter` and whose verification is `UNVERIFIED`, then CI shall fail naming the function and the row, so that no unverified site or material value is a default. | contract |
| FR-000-23 | Event | When `tools/gen_knowledge_docs.py` runs, it shall write one page per table under `docs/reference/knowledge/` listing every row (id, value or range, units, citation with DOI or URL, page, verification, symbol) and marking each UNVERIFIED row; with `--check` it shall exit 1 if any committed page differs from the generated one. | unit + CI |
| FR-000-24 | Event | When the wheel is built, it shall be a `py3-none-any` wheel containing `py.typed`, every knowledge table and `references.bib`, and the test suite selected by `-m "not gpu and not pyodide and not kit"` shall pass against the installed wheel in a clean environment. | CI (wheel job) + contract |
| FR-000-25 | Optional | Where a Pyodide runtime is available (the version pinned in the CI job; 314.0.x at specification), the wheel shall install with `micropip` using only Pyodide's own NumPy and PyYAML packages, every public subpackage shall import, and the smoke subset (one worked-example oracle per module) shall pass. | pyodide (CI job) |
| FR-000-26 | Optional | Where an NVIDIA Kit installation is present on the machine, the package installed into a target folder on Kit's path shall import in Kit's embedded Python 3.12 and the smoke subset shall pass; if Kit is unavailable, then the test shall report "not run" (skipped with that reason) and the CPython 3.12 CI job stands as the evidence of interpreter compatibility. | kit (local only) |
| FR-000-27 | Ubiquitous | `minephys.__version__` shall equal the content of the `VERSION` file (`X.YY.ZZZ`) and shall normalise to the distribution metadata version (`X.Y.Z` with integer segments). | unit |
| FR-000-28 | Event | When a release is prepared, `tools/check_api.py` shall compare the public API (names, parameters, defaults) with the previous release's snapshot (DC-000-04) and shall fail if a name or parameter was removed or renamed, or a default or documented unit changed, without both an `X` bump and an earlier `CHANGELOG.md` deprecation entry for it. | unit (fixture snapshots) |
| FR-000-29 | Event | When a deprecated public name, parameter or default is used, the library shall emit one `DeprecationWarning` per call site naming the replacement and the removal version. | unit |
| FR-000-30 | Unwanted | If a knowledge row's value, range or verification differs from the previous release, then the release check shall fail unless the `Unreleased` section of `CHANGELOG.md` names the row id. | unit (fixture tables) |
| FR-000-31 | Ubiquitous | Every knowledge table shall declare an SPDX licence; a `CC-BY-4.0` table shall cite no bibliography entry marked share-alike; share-alike-derived rows shall live under `knowledge/share-alike/` with their own licence; and `REUSE.toml` shall annotate both folders. | contract |
| FR-000-32 | Ubiquitous | The package shall export from `minephys` the classes `InputError(ValueError)`, `InputTypeError(TypeError)`, `ValidityWarning(UserWarning)` and `ConvergenceError(RuntimeError)`, each with an `argument` attribute (`None` for `ConvergenceError`), plus `__version__` and the public subpackages. | unit |
| FR-000-33 | Ubiquitous | Every test whose expected value comes from an oracle shall carry `@pytest.mark.oracle(kind, reference)` with `kind` in {`analytical`, `worked-example`, `reference-implementation`, `hand-calculation`} and, for a worked example, a reference that names the BibTeX key and page. | contract |

## 4. Correctness properties

| ID | Property (for all …) | Input domain / generator | Tolerance |
|---|---|---|---|
| P-000-01 | For every public elementwise function f and broadcastable valid inputs, f(arrays)[i] equals f evaluated on the scalars at index i. | each module's valid-input strategy; arrays of 0–64 elements, ranks 0–2 | TC-6 |
| P-000-02 | For every public function and valid inputs, two calls return bitwise-identical results and leave every input array bitwise unchanged. | same | exact |
| P-000-03 | For every public function, float32 and integer inputs give bitwise the same result as the same values cast to float64 first. | values exactly representable in float32 | exact |
| P-000-04 | For every sampling function, the same integer seed, or a `Generator` created from it with `numpy.random.default_rng(seed)`, gives bitwise-identical output; two different seeds give different output when at least two samples are drawn. | seeds 0–2³²−1 | exact |
| P-000-05 | For every pair of unit-conversion helpers (rad↔deg, fraction↔percent, m/s↔in/s, m↔ft, kg↔lb, m³↔US gal, J↔kWh), a round trip returns the input. | float64 in [1e-6, 1e6] and their negatives | rtol 1e-15 |

**Tolerance classes** (child specs cite them by name):

| Class | Use | Tolerance | Justification |
|---|---|---|---|
| TC-0 | identities that are exact in IEEE arithmetic (counts, integer results, symmetric inputs) | exact | no rounding involved |
| TC-1 | a closed form against an independent float64 recomputation in the test | rtol 1e-12, atol 0 | these closed forms take ≤ 100 operations with relative condition numbers ≤ 10, so the forward error is ≲ 1e-13; ×10 margin. A module spec states a looser bound where a model is ill-conditioned |
| TC-2 | a value printed in a source or hand calculation to k significant figures | half a unit in the k-th significant figure | the printed value carries that rounding |
| TC-3 | an iterative solver against an independent solution | rtol 1e-9 | solvers stop at a relative step ≤ 1e-12; the remaining error is set by the problem's conditioning |
| TC-4 | a Monte-Carlo estimate against an exact value | 4 standard errors of the estimator | false-failure probability ≈ 6e-5 per check; seeds are fixed, so the check is deterministic |
| TC-5 | an ODE integration against an analytical limit | rtol 1e-6 | fixed-step RK4 at the default step has a global error ≲ 1e-8 on the specified trajectories; ×100 margin |
| TC-6 | vectorised against scalar evaluation | rtol 1e-14, atol 1e-14 × max\|f\| over the batch | NumPy's SIMD loops for `exp`, `log`, `pow` may differ from the scalar path by a few ulp |

## 5. Non-functional requirements and success criteria

| ID | Statement | Threshold | Measured by |
|---|---|---|---|
| NFR-000-03 | Import time of all public subpackages (`python -X importtime`, self time of `minephys.*` modules only, NumPy and PyYAML excluded) | ≤ 100 ms, median of 5 fresh interpreters on the CI runner (CPython 3.14) | T-000-011 |
| NFR-000-04 | Wheel size | ≤ 1 MiB (1,048,576 bytes); target ≤ 512 KiB | CI wheel job (T-000-017) |
| NFR-000-05 | Runtime dependencies | wheel metadata `Requires-Dist` is exactly `numpy>=2.0` and `pyyaml>=6.0`; no runtime extras | T-000-017 |
| NFR-000-06 | Supported runtimes | tests green on CPython 3.12, 3.13 and 3.14 and on the built wheel; Pyodide smoke green (FR-000-25); Kit smoke run locally when Kit is present (FR-000-26) | CI matrix + pyodide job |
| NFR-000-07 | Evaluation latency on CPython 3.14 (CI runner, median of 20 calls) | closed-form scalar call ≤ 1 ms; iterative or sampling call at its specified reference size ≤ 50 ms (the live-lane budget of the consumers) | `tools/bench.py` (T-000-022), gating at release |
| NFR-000-08 | Test-quality gates | branch coverage of `src/minephys/` ≥ `coverage.branch_core_min`, changed lines ≥ `coverage.changed_lines_min`; mutation score of the numerical modules ≥ `mutation.numerical_core_min` (fail below `mutation.numerical_core_fail_below`); Hypothesis examples per property ≥ `property_tests.ci_examples_per_test` in CI and ≥ `property_tests.release_examples_per_test` at release (all keys in `thresholds.yaml`) | CI + T-000-090 |
| NFR-000-09 | Typing | every public function fully annotated; `mypy src` passes with `disallow_untyped_defs` | CI |
| SC-000-02 | Oracle coverage | 100 % of public model functions of specs 001–007 have ≥ 1 test marked `oracle(...)` with a non-`hand-calculation` kind or a documented reason why none exists; every numerical core has ≥ 3 metamorphic properties with tests | T-000-024 report at release |
| SC-000-03 | Knowledge honesty | 0 UNVERIFIED `parameter` rows used as defaults; 100 % of `verified` rows pinned by a test | FR-000-21/22 checks at release |
| SC-000-04 | Portability | the smoke subset passes on CPython 3.12, 3.13, 3.14, the built wheel and Pyodide at every release | CI at release |

## 6. Data contracts

| ID | Artifact | Schema | Producer → Consumer |
|---|---|---|---|
| DC-000-02 | knowledge tables `src/minephys/knowledge/*.yaml` and `src/minephys/knowledge/share-alike/*.yaml` | `specs/000-foundation/contracts/knowledge-table.schema.json` (draft; promoted to `contracts/knowledge-table.schema.json` by T-000-001) | module specs (maintainer) → model code, `minephys.knowledge`, docs generator, PitStudio knowledge pages and parameter browser |
| DC-000-03 | bibliography `src/minephys/knowledge/references.bib` (each parsed entry) | `specs/000-foundation/contracts/bibliography-entry.schema.json` (draft; promoted to `contracts/bibliography-entry.schema.json` by T-000-001) | maintainer → `minephys.knowledge`, docs generator, PitStudio bibliography |
| DC-000-04 | public API snapshot `docs/reference/api-snapshot.json` | `specs/000-foundation/contracts/api-snapshot.schema.json` (draft; promoted to `contracts/api-snapshot.schema.json` by T-000-001) | `tools/check_api.py` → release check |

The fields, enums and validation rules are in [data-model.md](data-model.md). The runtime validator in
`minephys.knowledge` is pure Python (NumPy and PyYAML only); the JSON Schema files are the neutral contract that CI
and other consumers use, and a contract test proves that both agree on valid and invalid fixtures.

## 7. Sources (summary — the full bibliography is `knowledge/references.bib`)

| Class | Examples | Licence / access | How the library uses them |
|---|---|---|---|
| Open-access papers | Mutinda et al. 2021 (KCO), Szendrei and Tose 2023 (flyrock), Carlà et al. 2017 (inverse velocity), Hoek and Brown 2019, Lindgren et al. 2022 (BEV) | CC BY or open access | equations, constants and worked examples, cited with page |
| Paywalled papers and standards | Kuznetsov 1973, Cunningham 1983/1987/2005, Ouchterlony 2005, Bishop 1955, Spencer 1967, Beverloo 1961, CEMA 7th ed., ISO 5048 | paywalled | cited; public equation forms only; values stay UNVERIFIED unless read on a readable primary copy |
| Government documents | US EPA GHG Emission Factors Hub 2025, 30 CFR § 816.67, USBM RI 8507 | public domain (US Government works) | constants and limits, converted to SI at the function boundary |
| Definitions | SI and NIST unit definitions | public | exact conversion factors (`units` table) |

Each module spec lists the sources it uses, the rows they feed and the verification status pinned at specification.

## 8. Risks and assumptions

- **A1 — standard gravity.** Models use standard gravity g₀ = 9.80665 m/s² (an exact defined value) from the `units`
  table, overridable by a `g` argument where gravity enters. Hand calculations printed with 9.81 differ by 0.034 %;
  test oracles are recomputed with 9.80665.
- **A2 — unit suffixes.** The closed list of name suffixes that override SI is: `_cm`, `_mm`, `_deg`, `_pct`, `_in_s`,
  `_ft`, `_lb`, `_per_h`, `_kwh`, `_t` (tonnes) and `_mpa`. Adding a suffix is a change to this spec.
- **A3 — error policy.** Non-finite inputs raise instead of propagating NaN, so that a browser or pipeline never shows
  a silent NaN. Domain violations raise; validity-range violations warn. Module specs may tighten a warning into an
  error, never the reverse.
- **A4 — Pyodide and Kit.** Pyodide ships NumPy and PyYAML in its distribution (the consumer's measured load set lists
  both). Kit's embedded Python is 3.12. Neither runtime is a CI dependency for Kit; Pyodide runs in a CI job under
  Node 24.
- **A5 — empirical models extrapolate badly.** Kuz-Ram, the PPV site law, Beverloo and the AP-42 factors are
  regressions; their validity ranges are knowledge rows and are enforced by FR-000-16.
- **A6 — transcription risk.** Several equation forms come from secondary sources; their rows stay UNVERIFIED with the
  secondary page in `notes`, and their tests use analytical or hand-calculated oracles that do not depend on the
  unverified value.
- **A7 — `units` table** (`knowledge/units.yaml`, role `conversion`, used by every module; decimal SI prefixes are
  allowed literals under FR-000-19 because they are exact definitions):

  | Row id | Value | Units | Citation, page | Verification |
  |---|---|---|---|---|
  | `standard_gravity` | 9.80665 | m/s² | NIST SP 811, Appendix B.8 ("acceleration of free fall, standard", exact) | verified (2026-10-07) |
  | `inch` | 0.0254 | m | NIST SP 811, Appendix B.8 (exact); NIST Handbook 44 (2026), Appendix C, p. 21 ("2.54 centimeters (exactly)") | verified (2026-10-07) |
  | `foot` | 0.3048 | m | NIST SP 811, Appendix B.8 (exact) | verified (2026-10-07) |
  | `pound` | 0.45359237 | kg | NIST Handbook 44 (2026), Appendix C, p. 17 (avoirdupois pound) | verified (2026-10-07) |
  | `us_gallon_cubic_inches` | 231 | in³ | NIST Handbook 44 (2026), Appendix C, p. 25 ("231 cubic inches (exactly)") | verified (2026-10-07) |
  | `kilowatt_hour` | 3.6e6 | J | NIST SP 811, Appendix B.8 (exact) | verified (2026-10-07) |

  Derived exactly in code: US gallon = 231 × 0.0254³ m³ = 3.785411784 × 10⁻³ m³; pound-force = 0.45359237 × 9.80665 N;
  in/s = 0.0254 m/s.
- **Risk — paywalled primaries.** Some constants may never become `verified`. The library still implements the model,
  flags the row and requires the caller to pass site or material values.

## 9. Module specifications (children)

| Spec | Module | Scope | Plan source |
|---|---|---|---|
| 001-haulage | `minephys.haulage` | resistances, rimpull and retarder speeds, loading passes, cycle time, segment and cycle energy, fuel and CO₂, trolley and battery-electric energy, match factor, M/M/c, finite-source queue, mean-value analysis | §13, §6 M1 M6 |
| 002-blasting | `minephys.blasting` | powder factor, Kuz-Ram (1983/1987 exponent by default, 2005 as an option), Rosin–Rammler, Swebrec, KCO, PPV scaled distance and 30 CFR § 816.67 limits, flyrock | §13, §6 M12 |
| 003-geotech | `minephys.geotech` | generalised Hoek–Brown and equivalent Mohr–Coulomb, Bishop and Spencer LEM, Monte-Carlo probability of failure, Voight creep and inverse velocity, Bayesian time to failure, GB-InSAR line-of-sight model | §13, §6 M13 M14 M23 |
| 004-bulk | `minephys.bulk` | Beverloo discharge, repose geometry, conveyor capacity and CEMA effective tension and power, Gy fundamental sampling error and bed-blending variance | §13, §6 M7 |
| 005-comminution | `minephys.comminution` | Bond, Morrell, population balance, flotation kinetics, two-product recovery | §13, §6 M17 |
| 006-environment | `minephys.environment` | AP-42 unpaved roads, Gaussian plume, Beer–Lambert dust attenuation for lidar | §13, §6 M16 M23 |
| 007-planning | `minephys.planning` | block value, Lane cut-off grades, min-cut ultimate pit (≥ 10⁵ blocks, minimal closure; NFR-007-06) | §13, §6 M18 |
| 008-knowledge | `minephys.knowledge` | loader, lookup, validator, bibliography and glossary API over DC-000-02 and DC-000-03 | §8, §13 |

## 10. Clarifications log

- **Resolved — template rows.** The application-template rows of the previous draft (web app, access gate, static
  delivery) do not apply to a library. They are retired in §11 and their IDs are never reused (constitution 2.0.0).
- **Resolved — NaN policy.** Raise `InputError` (FR-000-10) rather than propagate NaN (A3). `InputError` subclasses
  `ValueError`, so "raises `ValueError` naming the offending field" holds; wrong types raise `InputTypeError`, a
  `TypeError`, which is the Python convention.
- **Resolved — gravity.** The docs' worked examples use g = 9.81 m/s²; the library uses g₀ = 9.80665 m/s² (A1). The
  child specs recompute every oracle with g₀; the docs numbers remain valid to their printed precision within 0.034 %.
- **Resolved — schema location.** The neutral schemas live under `contracts/` (already annotated in `REUSE.toml`); the
  wheel ships the tables and the bibliography, not the schemas, because the runtime validator needs no JSON Schema
  engine.
- **Resolved — verification enum.** The docs define `verified` / `UNVERIFIED`; this spec keeps exactly these two
  values. A transcription read only on a secondary source stays `UNVERIFIED`, with the secondary page in `notes`.
- **Resolved — knowledge API.** The loader and lookup functions (`load_table`, `get_parameter`, `list_tables`,
  `bibliography`, `validate_tables`, `glossary`) are specified in 008-knowledge; this spec fixes only the data contract
  and the library-wide honesty checks.
- **Resolved — Tier L companions.** research, data model and quickstart are in this folder; the per-model theory is
  in `docs/theory/README.md` and the module specs.
- Integration 2026-10-07: FR-000-19 states what the literal allowlist may hold — structural constants, decimal SI
  prefixes, exact mathematical constants and numerical tolerances or tiny guards (e.g. 1e-12) — and that every
  physical or empirical constant still comes from a knowledge table.
- Integration 2026-10-07: draft schemas written for DC-000-02, DC-000-03 and DC-000-04
  (`specs/000-foundation/contracts/`, valid and hostile examples indexed in `examples/index.json`); ambiguities
  resolved with the stricter reading: patterns use the portable form (`[0-9]` for `\d`; the DOI suffix `\S+` becomes
  printable ASCII `[!-~]+`; versions `^[0-9]+\.[0-9]{2}\.[0-9]{3}$`); a `"p/q"` value needs a non-zero denominator;
  `title`, `quantity`, `page` and `units` are single-line, trimmed and non-blank; dimensionless units are written `1`
  only (`-`, `none`, `dimensionless`, `unitless`, `n/a` are rejected); caps chosen here: ids and keys 64 characters,
  text lines 200, units 64, notes 1,000, 1,000 rows per table, 32 symbols per row, bibliography title 500 and author
  list 2,000 characters; no `$schema` member at a document root, because the data model allows no other field; the
  bibliography `licence` is an allowlist of SPDX ids (`CC0-1.0` and the `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`,
  `CC-BY-SA-4.0`, `CC-BY-ND-4.0`, `CC-BY-NC-4.0`, `CC-BY-NC-SA-4.0`, `CC-BY-NC-ND-4.0` family), so that a misspelt
  licence cannot hide a share-alike source; every bibliography entry, `bibliographic-only` included, carries a DOI or
  a URL; URLs carry no user information; the API snapshot lists at least one object, requires `deprecated` (null when
  not deprecated), records `parameters` for functions only (forbidden on other kinds), names parameter kinds after
  Python's `inspect` kinds in snake case (`positional_only`, `positional_or_keyword`, `var_positional`,
  `keyword_only`, `var_keyword`), and writes `unit` without the brackets, or null for flags and options that have
  no bracketed unit.
- Integration 2026-10-07 (2): the data model states once that a knowledge table is shipped only when it has ≥ 1 row (no empty files);
  spec 008 applies the same rule to the catalogues (FR-008-22).

## 11. Changes

### REMOVED Requirements

| ID | Former content | Reason |
|---|---|---|
| ~~US-000-1~~ | application-template user story placeholder | not a library story (constitution 2.0.0) |
| ~~FR-000-01~~ | web app shows data source, licence and lane per result | no web app in this repository |
| ~~FR-000-02~~ | web app compute-tier fallback | no web app |
| ~~FR-000-03~~ | web app languages and themes | no web app |
| ~~FR-000-04~~ | web app access gate | no web app |
| ~~NFR-000-01~~ | initial JavaScript budget | no web app |
| ~~NFR-000-02~~ | web accessibility | no web app |
| ~~SC-000-01~~ | headline metric on held-out real data | no trained model in this repository |
| ~~DC-000-01~~ | web asset manifest | no web assets in this repository |

### ADDED Requirements
US-000-2…7, FR-000-05…33, P-000-01…05, NFR-000-03…09, SC-000-02…04, DC-000-02…04.

### MODIFIED Requirements
(none)
