# Architecture

> How `minephys` is organised: one sub-package per domain, a knowledge loader, and a purity boundary (NumPy and PyYAML
> only) that keeps it importable in CPython, Pyodide and NVIDIA Kit. · Part of: [docs home](../README.md) · Related:
> [reference](../reference/README.md) · [decisions](decisions/README.md)

**Status: filled in the build phase.**

This section will hold the module layout under `src/minephys/`, the dependency rules between modules (domain modules
read `minephys.knowledge`, never each other's internals), the purity boundary and how it is tested, and the error and
validity-range policy. The planned modules are summarised in the [diagram](../assets/diagrams/minephys-modules.svg)
and in [reference](../reference/README.md).
