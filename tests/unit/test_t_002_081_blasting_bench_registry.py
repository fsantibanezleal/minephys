"""T-002-081 (NFR-002-01, NFR-002-02): the blasting reference sizes are registered in `tools/bench.py`.

Uses the CLI of T-000-023 (`python tools/bench.py --list --json`). Required entries (spec 002 section 5):

* `blasting.flyrock_trajectory` at the reference case v0 = 40 m/s, 45 degrees, D = 0.1 m with the default step: kind
  `iterative`, budget 50 ms (NFR-002-01); the numbers 40 and 0.1 appear among the values of its `reference_size`;
* one `closed_form` entry (budget 1 ms, NFR-002-02) for every other function of the module on scalar inputs:
charge_per_hole,
  powder_factor, kuznetsov_x50, rock_factor, hardness_factor, rock_density_influence, uniformity_index,
  rosin_rammler_passing, rosin_rammler_size, swebrec_passing, swebrec_size, kco_undulation, kco_distribution,
  scaled_distance, ppv_scaled_distance, ppv_limit, max_charge_per_delay, flyrock_range_no_drag,
  flyrock_range_lundborg.

Every entry names a function that `minephys.blasting` exports. Oracle: hand calculation (the budgets and sizes
of the spec).
"""

from __future__ import annotations

import json

import minephys.blasting as blasting
import pytest
from _mini_repo import REPO_ROOT, run_tool

CLOSED_FORM = [
    "charge_per_hole",
    "powder_factor",
    "kuznetsov_x50",
    "rock_factor",
    "hardness_factor",
    "rock_density_influence",
    "uniformity_index",
    "rosin_rammler_passing",
    "rosin_rammler_size",
    "swebrec_passing",
    "swebrec_size",
    "kco_undulation",
    "kco_distribution",
    "scaled_distance",
    "ppv_scaled_distance",
    "ppv_limit",
    "max_charge_per_delay",
    "flyrock_range_no_drag",
    "flyrock_range_lundborg",
]


def registry() -> dict[str, dict]:
    assert (REPO_ROOT / "tools" / "bench.py").is_file(), "missing tools/bench.py"
    proc = run_tool("bench.py", "--list", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {c["name"]: c for c in json.loads(proc.stdout)}


@pytest.mark.req("NFR-002-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 NFR-002-01: flyrock_trajectory at v0 = 40 m/s, 45 degrees, D = 0.1 m, <= 50 ms"
)
def test_flyrock_trajectory_reference_case() -> None:
    case = registry()["blasting.flyrock_trajectory"]
    assert case["kind"] == "iterative"
    assert case["budget_ms"] == 50.0
    numbers = [v for v in case["reference_size"].values() if isinstance(v, int | float) and not isinstance(v, bool)]
    assert 40 in numbers
    assert 0.1 in numbers


@pytest.mark.req("NFR-002-02")
@pytest.mark.oracle("hand-calculation", "spec 002 NFR-002-02: every other function on scalar inputs <= 1 ms")
@pytest.mark.parametrize("function", CLOSED_FORM)
def test_closed_form_functions_are_registered(function: str) -> None:
    case = registry()[f"blasting.{function}"]
    assert case["kind"] == "closed_form"
    assert case["budget_ms"] == 1.0
    assert case["module"] == "blasting"
    assert case["function"] == function


@pytest.mark.req("NFR-002-01")
@pytest.mark.req("NFR-002-02")
@pytest.mark.oracle(
    "hand-calculation", "every blasting entry names an exported function and the runner can execute one"
)
def test_entries_name_exported_functions_and_run() -> None:
    cases = [c for c in registry().values() if c["module"] == "blasting"]
    assert len(cases) >= len(CLOSED_FORM) + 1
    exported = set(blasting.__all__)
    for c in cases:
        assert c["function"] in exported, c["name"]
    proc = run_tool("bench.py", "--run", "blasting.flyrock_trajectory", "--repeat", "3", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["name"] == "blasting.flyrock_trajectory"
    assert data["repeat"] == 3
    assert data["median_ms"] > 0.0
