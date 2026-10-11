# Plan 004 — Bulk-handling models (`minephys.bulk`)
Spec: ./spec.md

## Summary
One sub-package `src/minephys/bulk/` with private modules `_flow.py` (Beverloo: FR-004-01, -02), `_stockpile.py`
(repose geometry: FR-004-03, -04), `_conveyor.py` (capacity, CEMA tension, power: FR-004-05…07) and `_sampling.py`
(Gy FSE and blending: FR-004-08, -09, -12). Validation through the foundation helpers (FR-004-10, -11); constants from
`bulk.yaml` (DC-004-01). Every function is a closed form, so the module is small and live in the browser.

## Technical context
Runtime: CPython 3.12–3.14, Pyodide, Kit (foundation) · NumPy + PyYAML only · no new dependency · target: wheel.

## Constitution check

| Principle | Pass? | Note / justification |
|---|---|---|
| 1 Real, sourced models | yes | no UNVERIFIED parameter is a default: `C`, `k`, the CEMA factors and Gy's factors are required inputs |
| 3 Acceptance-test-first | yes | each task is a `[red]`/`[green]` pair |
| 4 Independent oracles | yes | dimensional analysis (Beverloo 5/2), geometry, conservation (lift floor), the cgs ↔ SI identity, the AR(1) closed form vs its sum |
| 5 Determinism and tolerances | yes | no randomness; TC-1, TC-2, TC-0 |
| 6 Purity and portability | yes | pure NumPy |
| 7 SI units | yes | the CEMA equation is used in its dimensionally homogeneous SI form; tripwires catch mm, t/m³ and g/cm³ slips |
| 9 Licence hygiene | yes | no CEMA, ISO or DIN table is reproduced |

## Design

| Component | Requirements | Notes |
|---|---|---|
| `_flow.beverloo_discharge` | FR-004-01, -02 | `(D − k d)` checked > 0 before the power; exponent from the row as an exact rational |
| `_stockpile.repose_cone_height`, `repose_cone_volume`, `repose_ridge_volume` | FR-004-03, -04 | `tan φ` evaluated once |
| `_conveyor.conveyor_capacity`, `cema_effective_tension`, `conveyor_power` | FR-004-05…07 | sign branch for regenerative declines |
| `_sampling.gy_fundamental_sampling_error` | FR-004-08, -12 | `(1/M_S − 1/M_L)` computed as `(M_L − M_S)/(M_S M_L)` to avoid cancellation |
| `_sampling.gy_blending_variance`, `variance_reduction_ratio` | FR-004-09, -12 | closed form with `expm1`/`log1p` for `ρᴺ`; explicit sum when N ≤ 1,000 |

## Test strategy

| Requirement | Level | Oracle | Tool |
|---|---|---|---|
| FR-004-01 | unit | hand calculation (§7.4, inputs C = 0.56 and k = 1.5 passed explicitly) + analytical dimensional analysis (exponent 5/2: Q ∝ ρ_b √g D^{5/2}) | pytest |
| FR-004-02 | hostile | analytical (zero opening) | pytest |
| FR-004-03, FR-004-04 | unit | analytical geometry (cone volume = base area × height / 3; prism) + hand calculation (§7.4) | pytest |
| FR-004-05 | unit | analytical (continuity ṁ = ρ A V) | pytest |
| FR-004-06, FR-004-07 | unit | hand calculation (§7.4) + analytical conservation (lift floor, P-004-05) | pytest |
| FR-004-08 | unit | hand calculation (§7.4) + analytical unit identity cgs ↔ SI | pytest |
| FR-004-09 | unit | analytical (closed form vs explicit sum; ρ = 0 limit σ²/N) | pytest |
| FR-004-10, FR-004-12 | hostile | analytical (domain table §7.2) | Hypothesis + foundation contract suite |
| FR-004-11 | unit | hand-chosen inputs on each side of every tripwire | `pytest.warns` |
| P-004-01 … P-004-08 | property / metamorphic | invariants stated in the spec | Hypothesis |
| NFR-004-01 | release | measurement | `tools/bench.py` |

Tolerances: TC-1 throughout. Beverloo is ill-conditioned as `D → k d` (relative condition number `(5/2)·D/(D − k d)`);
the property generator keeps `D ≥ 1.1·k·d`, where the condition number is ≤ 27.5, still inside TC-1's margin.

## Risks and complexity tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Closed form plus explicit-sum fallback for blending | O(1) for N up to 10⁷ and exact agreement with the sum for small N | the explicit sum alone is O(N) and slow in the browser for large N |
