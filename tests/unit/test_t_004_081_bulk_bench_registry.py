"""T-004-081 (NFR-004-01): the bulk reference sizes are registered in `tools/bench.py`.

Uses the CLI of T-000-023 (`python tools/bench.py --list --json`). Required entries (spec 004 section 5): one
`closed_form` entry (budget 1 ms) for every function of the module on scalar inputs: beverloo_discharge,
repose_cone_height, repose_cone_volume, repose_ridge_volume, conveyor_capacity, cema_effective_tension,
conveyor_power, gy_fundamental_sampling_error, gy_blending_variance, variance_reduction_ratio. The blending
entries use N = 1e7 layers (the largest layer count, which must still cost O(1)): the number 10000000 appears
among the values of the `reference_size` of `bulk.gy_blending_variance` and `bulk.variance_reduction_ratio`.

Every entry names a function that `minephys.bulk` exports. Oracle: hand calculation (the budget and sizes of
the spec).
"""

from __future__ import annotations

import json

import minephys.bulk as bulk
import pytest
from _mini_repo import REPO_ROOT, run_tool

FUNCTIONS = [
    "beverloo_discharge",
    "repose_cone_height",
    "repose_cone_volume",
    "repose_ridge_volume",
    "conveyor_capacity",
    "cema_effective_tension",
    "conveyor_power",
    "gy_fundamental_sampling_error",
    "gy_blending_variance",
    "variance_reduction_ratio",
]


def registry() -> dict[str, dict]:
    assert (REPO_ROOT / "tools" / "bench.py").is_file(), "missing tools/bench.py"
    proc = run_tool("bench.py", "--list", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {c["name"]: c for c in json.loads(proc.stdout)}


@pytest.mark.req("NFR-004-01")
@pytest.mark.oracle("hand-calculation", "spec 004 NFR-004-01: every function of the module on scalar inputs <= 1 ms")
@pytest.mark.parametrize("function", FUNCTIONS)
def test_every_function_is_registered_as_closed_form(function: str) -> None:
    case = registry()[f"bulk.{function}"]
    assert case["kind"] == "closed_form"
    assert case["budget_ms"] == 1.0
    assert case["module"] == "bulk"
    assert case["function"] == function


@pytest.mark.req("NFR-004-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 FR-004-09: the blending closed form costs O(1) up to N = 1e7: the reference size is the largest N",
)
@pytest.mark.parametrize("function", ["gy_blending_variance", "variance_reduction_ratio"])
def test_blending_is_benchmarked_at_the_largest_layer_count(function: str) -> None:
    case = registry()[f"bulk.{function}"]
    numbers = [v for v in case["reference_size"].values() if isinstance(v, int | float) and not isinstance(v, bool)]
    assert 10_000_000 in numbers


@pytest.mark.req("NFR-004-01")
@pytest.mark.oracle("hand-calculation", "every bulk entry names an exported function and the runner can execute one")
def test_entries_name_exported_functions_and_run() -> None:
    cases = [c for c in registry().values() if c["module"] == "bulk"]
    assert len(cases) >= len(FUNCTIONS)
    exported = set(bulk.__all__)
    for c in cases:
        assert c["function"] in exported, c["name"]
    proc = run_tool("bench.py", "--run", "bulk.gy_blending_variance", "--repeat", "3", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["name"] == "bulk.gy_blending_variance"
    assert data["repeat"] == 3
    assert data["median_ms"] > 0.0
