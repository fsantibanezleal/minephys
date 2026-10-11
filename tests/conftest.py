"""Shared pytest configuration for the minephys test tree.

Registers the requirement-linking and oracle markers so that `--strict-markers` collects every test in the red phase
(T-000-002 registers the same markers in pyproject.toml; a test there checks that file independently).

Putting this directory on `sys.path` (pytest's rootdir conftest behaviour in the default import mode) makes the shared
test-support modules `_contract_suite` (T-000-010) and `_mini_repo` importable by their bare names from any test.
"""

from __future__ import annotations


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    for line in (
        "req(id): links a test to a requirement ID",
        "oracle(kind, reference): the source of the expected values "
        "(analytical, worked-example, reference-implementation, hand-calculation)",
        "knowledge(row_id): pins a verified knowledge-table row",
        "pyodide: needs the Pyodide runtime (CI job only)",
        "kit: needs an NVIDIA Kit installation (local only)",
    ):
        config.addinivalue_line("markers", line)
