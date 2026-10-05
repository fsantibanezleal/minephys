# Reference

> The planned public API of `minephys` (module by module, names only), the units convention, the format of the cited
> knowledge tables, compatibility with Pyodide and NVIDIA Kit, and the versioning scheme. · Part of:
> [docs home](../README.md) · Related: [theory](../theory/README.md) · [data contract](../data-contract/README.md) ·
> [guides](../guides/README.md)

## What and why

This page is the contract the implementation will be written against. The function names below are **planned**: they
come from the models listed in the [theory](../theory/README.md) skeleton, and their signatures, argument units,
validity checks and return types are fixed by the package's specifications before the tests are written. Nothing on
this page exists in `src/minephys/` yet (today `minephys/__init__.py` exports nothing).

## Planned API (names only)

| Module | Planned functions | Status |
|---|---|---|
| `minephys.haulage` | `grade_resistance`, `total_resistance`, `required_force`, `rimpull_limited_speed`, `retarder_limited_speed`, `loose_density`, `loading_passes`, `cycle_time`, `segment_energy`, `cycle_energy`, `fuel_use`, `co2_from_diesel`, `co2_from_electricity`, `trolley_cycle_energy`, `bev_cycle_energy`, `match_factor`, `mmc_queue`, `finite_source_queue`, `mean_value_analysis` | planned |
| `minephys.blasting` | `powder_factor`, `charge_per_hole`, `kuznetsov_x50`, `rock_factor`, `uniformity_index`, `rosin_rammler_passing`, `swebrec_passing`, `kco_distribution`, `ppv_scaled_distance`, `max_charge_per_delay`, `ppv_limit`, `flyrock_trajectory`, `flyrock_range_no_drag` | planned |
| `minephys.geotech` | `hoek_brown_parameters`, `hoek_brown_sigma1`, `equivalent_mohr_coulomb`, `bishop_simplified_fos`, `spencer_fos`, `probability_of_failure`, `voight_creep_series`, `inverse_velocity_ttf`, `bayesian_ttf`, `slope_radar_los` | planned |
| `minephys.bulk` | `beverloo_discharge`, `repose_cone_volume`, `repose_ridge_volume`, `cema_effective_tension`, `conveyor_power`, `gy_blending_variance` | planned |
| `minephys.comminution` | `bond_energy`, `morrell_energy`, `pbm_batch_grinding`, `flotation_first_order`, `klimpel_recovery`, `two_product_recovery` | planned |
| `minephys.environment` | `ap42_unpaved_emission_factor`, `precipitation_correction`, `gaussian_plume`, `line_source_plume`, `pasquill_sigmas`, `beer_lambert_transmittance`, `lidar_dust_return` | planned |
| `minephys.planning` | `block_economic_value`, `lane_cutoff_grades`, `ultimate_pit_mincut`, `nested_pits` | planned |
| `minephys.knowledge` | `load_table`, `get_parameter`, `list_tables`, `bibliography`, `validate_tables`, `glossary` | planned |

Planned design rules for every public function (fixed in the specifications):

- **Pure functions** of their arguments: no global state, no I/O except in `minephys.knowledge`, no randomness unless a
  seed or a NumPy `Generator` is passed in.
- **Array-friendly:** scalar or NumPy array inputs, broadcast where the model allows it.
- **Documented model card per function:** the equation, the symbol table with units, the primary source with page, the
  validity range, and the knowledge-table rows it reads by default.

## Units convention

SI at every function boundary. The table below is the planned convention; the specifications fix it per function.

| Quantity | Unit at the API | Notes |
|---|---|---|
| Length, distance, size | m (sizes of fragments and particles also in m) | Bond's law is published with sizes in µm; the function converts |
| Mass, payload | kg | tonnes only in derived rates (t/h) where the name says so |
| Time | s | rates per hour are named explicitly (`_per_h`) |
| Force, stress, pressure | N, Pa | rock strengths in Pa (not MPa) |
| Energy, power | J, W | specific comminution energy in J/kg; kWh/t helpers convert |
| Angle | rad | degrees only in helpers whose name says so |
| Grade, resistance | dimensionless fraction | percent only in helpers whose name says so |
| Concentration, emission | kg/m³, kg/m | AP-42 is published in lb per vehicle-mile; the function converts and documents it |
| Vibration | m/s | regulatory limits published in in/s are stored as published and converted |

Conversions happen at the function boundary, once, and each is unit-tested.

## Knowledge tables

Parameters live in `knowledge/*.yaml`, one file per domain, and sources in `knowledge/references.bib`. Each row:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | stable identifier, referenced by code |
| `value` or `range` | number, or `{min, max}` | the published value or range |
| `units` | string | units as published |
| `citation` | string | BibTeX key in `references.bib` (each entry carries a DOI or URL) |
| `page` | string | page, table, figure or equation in the source |
| `verification` | `verified` or `UNVERIFIED` | `verified` only when read on the primary source and pinned by a test |
| `symbol` | string | the code symbol that uses the value |
| `notes` | string, optional | validity range, conversion, caveats |

Example (illustrative):

```yaml
- id: swebrec_fit_quality
  value: 0.995
  units: r^2 (lower bound)
  citation: ouchterlony2005swebrec
  page: "abstract"
  verification: UNVERIFIED
  symbol: minephys.blasting.swebrec_passing
  notes: "reported fit quality over 2-3 orders of magnitude of size; pinned at specification"
```

```bibtex
@article{ouchterlony2005swebrec,
  author  = {Ouchterlony, Finn},
  title   = {The Swebrec function: linking fragmentation by blasting and crushing},
  journal = {Mining Technology},
  volume  = {114},
  number  = {1},
  pages   = {29--44},
  year    = {2005},
  doi     = {10.1179/037178405X44539}
}
```

The tables are schema-validated in CI; a row without `citation` and `page` fails. Consumers (for example PitStudio's
docs build) generate parameter, equation, bibliography and glossary pages from the tables and flag every
`UNVERIFIED` row.

## Compatibility

| Runtime | Support | How it is checked |
|---|---|---|
| CPython 3.12, 3.13, 3.14 | `requires-python = ">=3.12"` | CI test matrix on all three, plus the tests run against the built wheel in a clean environment (exists) |
| Pyodide (browser) | pure Python + NumPy + PyYAML, all available in Pyodide | a wheel smoke test in Pyodide (build phase) |
| NVIDIA Kit (embedded Python 3.12) | installed into a git-ignored target folder that the Kit extension adds to its path | a Kit smoke import (build phase) |

Runtime dependencies are **NumPy and PyYAML only**; anything heavier (SciPy, pandas, numba) is out by design, because
it would break the Pyodide and Kit targets.

## Versioning

- Releases are `X.YY.ZZZ` (tags `vX.YY.ZZZ`, `CHANGELOG.md`, `CITATION.cff`, `VERSION`); `pyproject.toml` carries the
  normalised `X.Y.Z` because Python versions compare release segments as integers. `tools/release.py` computes the next
  version from Conventional Commits: a breaking change bumps `X`, a feature `YY`, anything else `ZZZ`.
- Today the version is `0.00.000`. Until the first release, consumers depend on a git commit (PitStudio pins one in its
  `uv.lock`).
- The first release goes to TestPyPI and then PyPI through trusted publishing.
- A change to a parameter **value** or **verification status** is a documented change in `CHANGELOG.md`, because it can
  change results downstream.

## Assumptions and limits

- Names and signatures may still change during specification; this page is updated with them.
- The library is reference-grade and educational; it is not a design tool.

## References

1. Ouchterlony, F. (2005), "The Swebrec function: linking fragmentation by blasting and crushing", Mining Technology 114(1):29–44. https://doi.org/10.1179/037178405X44539
2. npm registry, `pyodide` latest — 314.0.7 at the time of writing. https://registry.npmjs.org/pyodide/latest
3. PyPI, `omniverse-kit` 110.3 — embedded Python `==3.12.*`. https://pypi.org/pypi/omniverse-kit/json
