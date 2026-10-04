# minephys

Sourced, tested reference implementations of mining-engineering models with cited parameter tables.

[![CI](https://github.com/fsantibanezleal/minephys/actions/workflows/ci.yml/badge.svg)](https://github.com/fsantibanezleal/minephys/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/fsantibanezleal/minephys)](https://github.com/fsantibanezleal/minephys/releases)
[![License](https://img.shields.io/github/license/fsantibanezleal/minephys)](LICENSE)

## What it is / is not
A small, pure-NumPy Python library of classical open-pit mining models — each one implemented from its primary
source, with the equation, its assumptions and its validity range documented, and every parameter value traceable to
a citation (source + page) in machine-readable tables.

It is **not** a mine-planning package, a simulator or a replacement for engineering judgement. It is a reference: the
same code runs in notebooks, data pipelines and the browser (via Pyodide), so that one model has one implementation.

**Status: pre-release.** The package layout, CI and contracts exist; the models are being written test-first.

## Planned modules

| Module | Models |
|---|---|
| `minephys.haulage` | Match factor, finite-source queueing / mean-value analysis, haul-road rolling resistance and energy (diesel, trolley, battery-electric) |
| `minephys.blasting` | Kuz-Ram / KCO fragmentation, Swebrec distribution, peak particle velocity, flyrock range |
| `minephys.geotech` | Limit-equilibrium slope stability (Bishop, Spencer), Hoek–Brown strength, Monte-Carlo probability of failure, inverse-velocity time-to-failure |
| `minephys.environment` | AP-42 haul-road dust emission factors, Gaussian plume dispersion |
| `minephys.comminution` | Bond and Morrell energy, population-balance grinding |
| `minephys.knowledge` | Parameter tables (YAML) with value or range, units and citation, plus a BibTeX bibliography |

## Install
Until the first release, install from the repository:

```bash
uv add "minephys @ git+https://github.com/fsantibanezleal/minephys"
```

After the first release it will be on PyPI (`pip install minephys`). Python 3.12–3.14; the only runtime dependencies
are NumPy and PyYAML.

## Develop

```bash
uv sync --all-groups
uv run pytest -m "not gpu"
uv run ruff check . && uv run mypy src
```

CI runs the tests on Python 3.12, 3.13 and 3.14, and again against the built wheel in a clean environment.

## Documentation
Theory and the API reference live in [`docs/`](docs/README.md). Specifications: [`specs/`](specs/).

## Used by
[PitStudio](https://github.com/fsantibanezleal/PitStudio) — a physical-AI simulation studio for open-pit mining —
uses these models in its pipelines and in its web explorer.

## Cite
See [`CITATION.cff`](CITATION.cff).

## Versioning · Changelog · Licence
`X.YY.ZZZ` releases ([CHANGELOG](CHANGELOG.md)). Code: Apache-2.0 ([LICENSE](LICENSE)); docs and parameter tables:
CC-BY-4.0; see [`REUSE.toml`](REUSE.toml). Author: Felipe A. Santibanez-Leal.
