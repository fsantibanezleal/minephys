# minephys documentation

> Documentation of `minephys`, a small pure-NumPy library of classical open-pit mining models — haulage, blasting,
> geotechnics, bulk handling, comminution, environment and planning — with machine-readable, cited parameter tables.
> · Related: [theory](theory/README.md) · [reference](reference/README.md) ·
> [repository README](../README.md)

## What and why

Mining-engineering models are usually scattered across spreadsheets, papers and proprietary tools, with parameter
values copied without their source. `minephys` collects the classical ones in one place, each implemented from its
primary source, with its equation, assumptions and validity range written down, and with every parameter value
traceable to a citation and page in a table that code and documentation both read. The same code runs in notebooks,
in data pipelines, inside NVIDIA Kit, and in the browser through Pyodide, so one model has one implementation.

**What it is not:** a mine-planning package, a simulator, or a replacement for engineering judgement and site testing.
Its outputs are educational and reference-grade, valid only inside the ranges each model states.

**Status: pre-release.** The package layout, CI and contracts exist; no model is implemented yet. Models are written
test-first, each pinned by a worked example from its primary source. This documentation is a skeleton: the
[theory](theory/README.md) and [reference](reference/README.md) sections describe the planned modules; the other
sections are orientation pages filled in the build phase.

![minephys modules](assets/diagrams/minephys-modules.svg)

*Seven planned domain modules read the cited knowledge tables and serve four runtimes: data pipelines, a simulation
studio, Kit extensions and the browser.*

## Map

| Section | What you find | Status |
|---|---|---|
| [theory/](theory/README.md) | The science per module: models, governing equations, primary sources, validity notes | skeleton (filled per model in the build phase) |
| [reference/](reference/README.md) | The planned API per module (function names), units convention, knowledge-table format, Pyodide and Kit compatibility, versioning | skeleton |
| [guides/](guides/README.md) | Install, use in a notebook, in Pyodide and in Kit | filled in the build phase |
| [methods/](methods/README.md) | One page per model: derivation, worked example, tests | filled in the build phase |
| [data-contract/](data-contract/README.md) | Schema of the knowledge tables and the bibliography | filled in the build phase |
| [frameworks/](frameworks/README.md) | The two runtime dependencies (NumPy, PyYAML) and the runtimes it is tested in | filled in the build phase |
| [architecture/](architecture/README.md) | Module layout and the purity boundary; decisions in [architecture/decisions/](architecture/decisions/README.md) | filled in the build phase |
| [assets/](assets/diagrams/README.md) | Diagrams and figures | one diagram so far |

## Conventions

- **Units:** SI at every function boundary; sources published in other units (US customary for AP-42 and US
  regulations) are converted explicitly, and the conversion is tested.
- **Sources:** every external number carries a DOI or URL, and every parameter row its citation and page. A value not
  yet checked against its primary page is marked **UNVERIFIED** and stays out of any headline result.
- **Purity:** runtime dependencies are NumPy and PyYAML only, so the wheel installs in Pyodide and inside Kit.
- **Validity:** each model documents the range its source supports; outside it, the result is not a claim.

## Used by

[PitStudio](https://github.com/fsantibanezleal/PitStudio), a physical-AI simulation studio for open-pit mining, uses
these models in its pipelines and its web explorer, and generates its knowledge pages (parameters, equations,
bibliography, glossary) from the `minephys` tables.

## Licence and citation

Code Apache-2.0; documentation and parameter tables CC-BY-4.0 (see `REUSE.toml`). Cite with `CITATION.cff`, and cite
the primary source of every parameter you use, as listed in its table row.
