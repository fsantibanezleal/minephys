"""T-003-081 (NFR-003-01, NFR-003-02): the geotechnical reference sizes are registered in `tools/bench.py`.

Uses the CLI of T-000-023 (`python tools/bench.py --list --json`). Required entries (spec 003 section 5):

* `geotech.bishop_simplified_fos` and `geotech.spencer_fos` at 200 slices: kind `iterative`, budget 50 ms
(NFR-003-01);
  the number 200 appears among the values of the entry's `reference_size`;
* `geotech.monte_carlo_fos` (Bishop) with 10,000 samples on 50 slices: kind `sampling`, budget 50 ms; the
numbers 10000 and 50
  appear among the values of its `reference_size`;
* `geotech.bayesian_ttf` with 10,000 draws: kind `sampling`, budget 50 ms; the number 10000 appears among the
values of its
  `reference_size`;
* one `closed_form` entry (budget 1 ms, NFR-003-02) for every function of the module that takes scalar inputs:
  hoek_brown_parameters, hoek_brown_sigma1, hoek_brown_uniaxial_strength, hoek_brown_tensile_strength,
  hoek_brown_rock_mass_strength, equivalent_mohr_coulomb, sigma3_max, required_samples, los_phase, wrap_phase,
  los_from_phase, max_unambiguous_los_step.

Every entry names a function that `minephys.geotech` exports. Oracle: hand calculation (the budgets and sizes
of the spec).
"""

from __future__ import annotations

import json

import minephys.geotech as geotech
import pytest
from _mini_repo import REPO_ROOT, run_tool

CLOSED_FORM = [
    "hoek_brown_parameters",
    "hoek_brown_sigma1",
    "hoek_brown_uniaxial_strength",
    "hoek_brown_tensile_strength",
    "hoek_brown_rock_mass_strength",
    "equivalent_mohr_coulomb",
    "sigma3_max",
    "required_samples",
    "los_phase",
    "wrap_phase",
    "los_from_phase",
    "max_unambiguous_los_step",
]


def registry() -> dict[str, dict]:
    assert (REPO_ROOT / "tools" / "bench.py").is_file(), "missing tools/bench.py"
    proc = run_tool("bench.py", "--list", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {c["name"]: c for c in json.loads(proc.stdout)}


def numbers(case: dict) -> list[float]:
    return [v for v in case["reference_size"].values() if isinstance(v, int | float) and not isinstance(v, bool)]


@pytest.mark.req("NFR-003-01")
@pytest.mark.oracle("hand-calculation", "spec 003 NFR-003-01: Bishop and Spencer on 200 slices, <= 50 ms")
@pytest.mark.parametrize("function", ["bishop_simplified_fos", "spencer_fos"])
def test_slope_methods_at_200_slices(function: str) -> None:
    case = registry()[f"geotech.{function}"]
    assert case["kind"] == "iterative"
    assert case["budget_ms"] == 50.0
    assert case["module"] == "geotech"
    assert case["function"] == function
    assert 200 in numbers(case)


@pytest.mark.req("NFR-003-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 003 NFR-003-01: Monte-Carlo (Bishop) with 10,000 samples on 50 slices, <= 50 ms"
)
def test_monte_carlo_reference_case() -> None:
    case = registry()["geotech.monte_carlo_fos"]
    assert case["kind"] == "sampling"
    assert case["budget_ms"] == 50.0
    assert case["function"] == "monte_carlo_fos"
    nums = numbers(case)
    assert 10_000 in nums
    assert 50 in nums


@pytest.mark.req("NFR-003-01")
@pytest.mark.oracle("hand-calculation", "spec 003 NFR-003-01: bayesian_ttf with 10,000 draws, <= 50 ms")
def test_bayesian_reference_case() -> None:
    case = registry()["geotech.bayesian_ttf"]
    assert case["kind"] == "sampling"
    assert case["budget_ms"] == 50.0
    assert case["function"] == "bayesian_ttf"
    assert 10_000 in numbers(case)


@pytest.mark.req("NFR-003-02")
@pytest.mark.oracle("hand-calculation", "spec 003 NFR-003-02: closed-form functions on scalar inputs <= 1 ms")
@pytest.mark.parametrize("function", CLOSED_FORM)
def test_closed_form_functions_are_registered(function: str) -> None:
    case = registry()[f"geotech.{function}"]
    assert case["kind"] == "closed_form"
    assert case["budget_ms"] == 1.0
    assert case["module"] == "geotech"
    assert case["function"] == function


@pytest.mark.req("NFR-003-01")
@pytest.mark.req("NFR-003-02")
@pytest.mark.oracle("hand-calculation", "every geotech entry names an exported function and the runner can execute one")
def test_entries_name_exported_functions_and_run() -> None:
    cases = [c for c in registry().values() if c["module"] == "geotech"]
    assert len(cases) >= len(CLOSED_FORM) + 4
    exported = set(geotech.__all__)
    for c in cases:
        assert c["function"] in exported, c["name"]
    proc = run_tool("bench.py", "--run", "geotech.bishop_simplified_fos", "--repeat", "3", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["name"] == "geotech.bishop_simplified_fos"
    assert data["repeat"] == 3
    assert data["median_ms"] > 0.0
