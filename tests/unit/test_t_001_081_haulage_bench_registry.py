"""T-001-081 (NFR-001-01, NFR-001-02): the haulage reference sizes are registered in `tools/bench.py`.

Uses the CLI of T-000-023 (`python tools/bench.py --list --json`, one JSON case per registered benchmark with `name`,
`module`, `function`, `kind`, `reference_size`, `budget_ms`). Required entries (spec 001 section 5):

* `haulage.mean_value_analysis` at N = 200 customers and K = 10 stations, and `haulage.cycle_energy` at 1,000
segments,
  kind `iterative`, budget 50 ms (NFR-001-01); the numbers 200 and 10 (respectively 1000) appear among the values of
  their `reference_size`;
* one `closed_form` entry (budget 1 ms, NFR-001-02) for each closed-form function on scalar inputs:
  grade_resistance, total_resistance, required_force, retarder_limited_speed, loose_density, loading_passes,
  segment_travel_time, cycle_time, segment_energy, fuel_use, co2_from_diesel, co2_from_electricity, match_factor;
* entries (any kind) for rimpull_limited_speed, mmc_queue, finite_source_queue, bev_cycle_energy and
  trolley_cycle_energy.

Every entry names a function that `minephys.haulage` exports. Oracle: hand calculation (the budgets and sizes of the
specification).
"""

from __future__ import annotations

import json

import minephys.haulage as haulage
import pytest
from _mini_repo import REPO_ROOT, run_tool

CLOSED_FORM = [
    "grade_resistance",
    "total_resistance",
    "required_force",
    "retarder_limited_speed",
    "loose_density",
    "loading_passes",
    "segment_travel_time",
    "cycle_time",
    "segment_energy",
    "fuel_use",
    "co2_from_diesel",
    "co2_from_electricity",
    "match_factor",
]
OTHER = ["rimpull_limited_speed", "mmc_queue", "finite_source_queue", "bev_cycle_energy", "trolley_cycle_energy"]


def registry() -> dict[str, dict]:
    assert (REPO_ROOT / "tools" / "bench.py").is_file(), "missing tools/bench.py"
    proc = run_tool("bench.py", "--list", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {c["name"]: c for c in json.loads(proc.stdout)}


def numbers(case: dict) -> list[float]:
    return [v for v in case["reference_size"].values() if isinstance(v, int | float) and not isinstance(v, bool)]


@pytest.mark.req("NFR-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 NFR-001-01: MVA at N = 200, K = 10, <= 50 ms")
def test_mean_value_analysis_reference_size() -> None:
    case = registry()["haulage.mean_value_analysis"]
    assert case["kind"] == "iterative"
    assert case["budget_ms"] == 50.0
    assert 200 in numbers(case)
    assert 10 in numbers(case)


@pytest.mark.req("NFR-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 NFR-001-01: cycle_energy at 1,000 segments, <= 50 ms")
def test_cycle_energy_reference_size() -> None:
    case = registry()["haulage.cycle_energy"]
    assert case["kind"] == "iterative"
    assert case["budget_ms"] == 50.0
    assert 1000 in numbers(case)


@pytest.mark.req("NFR-001-02")
@pytest.mark.oracle("hand-calculation", "spec 001 NFR-001-02: closed-form scalar calls <= 1 ms")
@pytest.mark.parametrize("function", CLOSED_FORM)
def test_closed_form_functions_are_registered_with_a_one_millisecond_budget(function: str) -> None:
    case = registry()[f"haulage.{function}"]
    assert case["kind"] == "closed_form"
    assert case["budget_ms"] == 1.0
    assert case["module"] == "haulage"
    assert case["function"] == function


@pytest.mark.req("NFR-001-02")
@pytest.mark.oracle("hand-calculation", "the remaining haulage functions are registered too")
@pytest.mark.parametrize("function", OTHER)
def test_other_functions_are_registered(function: str) -> None:
    case = registry()[f"haulage.{function}"]
    assert case["budget_ms"] in (1.0, 50.0)
    assert case["kind"] in {"closed_form", "iterative", "sampling"}


@pytest.mark.req("NFR-001-01")
@pytest.mark.req("NFR-001-02")
@pytest.mark.oracle("hand-calculation", "every haulage entry names an exported function and the runner can execute it")
def test_entries_name_exported_functions_and_run() -> None:
    cases = [c for c in registry().values() if c["module"] == "haulage"]
    assert len(cases) >= len(CLOSED_FORM) + len(OTHER) + 2
    exported = set(haulage.__all__)
    for c in cases:
        assert c["function"] in exported, c["name"]
    proc = run_tool("bench.py", "--run", "haulage.mean_value_analysis", "--repeat", "3", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["name"] == "haulage.mean_value_analysis"
    assert data["repeat"] == 3
    assert data["median_ms"] > 0.0
