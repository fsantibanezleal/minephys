"""T-000-024 (NFR-000-08, NFR-000-09): CI gates (coverage, mutation tool, Hypothesis profiles, mypy strictness).

Expected deliverables:

* `pyproject.toml`:
  - `[tool.mypy]` with `disallow_untyped_defs = true` (NFR-000-09; CI already runs `mypy src`);
  - `[tool.coverage.run]` with `branch = true` and `source` naming `src`; `[tool.coverage.report]` with
    `fail_under` >= 100 * `coverage.branch_core_min` of `specs/000-foundation/thresholds.yaml` (90);
  - the dev dependency group contains `mutmut` (the tool the repository already ignores: `mutants/`,
    `.mutmut-cache`) and `diff-cover` (changed-lines coverage), both locked in `uv.lock`;
    `[tool.mutmut]` has `paths_to_mutate`;
  - `[tool.pytest]` has `pythonpath` containing `tests` and `addopts` containing `-p _hypothesis_profiles`.
* `tests/_hypothesis_profiles.py`: registers the Hypothesis profiles `dev` (50 examples), `ci`
  (`property_tests.ci_examples_per_test` = 200) and `release` (`property_tests.release_examples_per_test` = 2000), all
  with `deadline=None`, and loads the one named by the environment variable `HYPOTHESIS_PROFILE`; an unknown name is an
  error.
* `.github/workflows/ci.yml`: the test job sets `HYPOTHESIS_PROFILE: ci`, runs coverage with `--cov-branch` and
  invokes `diff-cover` with `--fail-under` equal to 100 * `coverage.changed_lines_min` (90).
* `tools/check_gates.py`, the numeric gate evaluator:

      python tools/check_gates.py [--thresholds FILE] [--branch-coverage X] [--changed-lines-coverage X]
                                  [--mutation-score X] [--hypothesis-examples N --profile ci|release]

  with fractions in [0, 1]. Exit 1 and a line with `FAIL` for: branch or changed-line coverage below its minimum,
  a mutation score below `mutation.numerical_core_fail_below`, examples below the profile's minimum; exit 0 with a line
  containing `warn` when the mutation score lies in [fail_below, numerical_core_min); exit 0 otherwise (`OK`). Values
  outside [0, 1], NaN or non-numbers are usage errors (exit 2, no traceback).

Oracle: the thresholds written in `specs/000-foundation/thresholds.yaml` (hand calculation) and the files above.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml
from _mini_repo import REPO_ROOT, run_tool

ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS = ROOT / "specs" / "000-foundation" / "thresholds.yaml"


def pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def thresholds() -> dict:
    return yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))


@pytest.mark.req("NFR-000-09")
@pytest.mark.oracle("hand-calculation", "NFR-000-09: mypy refuses untyped definitions")
def test_mypy_is_strict_about_untyped_definitions() -> None:
    cfg = pyproject()["tool"]["mypy"]
    assert cfg["disallow_untyped_defs"] is True
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "mypy src" in ci


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "the thresholds of the spec are the ones this test pins (ratchet: never lower)")
def test_thresholds_are_the_specified_ones() -> None:
    t = thresholds()
    assert t["coverage"]["branch_core_min"] >= 0.90
    assert t["coverage"]["changed_lines_min"] >= 0.90
    assert t["mutation"]["numerical_core_min"] >= 0.80
    assert t["mutation"]["numerical_core_fail_below"] >= 0.70
    assert t["property_tests"]["ci_examples_per_test"] >= 200
    assert t["property_tests"]["release_examples_per_test"] >= 2000


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "NFR-000-08: branch coverage gate equals the threshold")
def test_coverage_configuration_matches_the_thresholds() -> None:
    cfg = pyproject()["tool"]["coverage"]
    assert cfg["run"]["branch"] is True
    assert "src" in " ".join(cfg["run"]["source"])
    assert cfg["report"]["fail_under"] >= 100 * thresholds()["coverage"]["branch_core_min"]


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle(
    "hand-calculation", "NFR-000-08: a mutation tool is chosen and locked; diff-cover gates changed lines"
)
def test_mutation_and_changed_lines_tools_are_in_the_dev_group_and_locked() -> None:
    dev = " ".join(pyproject()["dependency-groups"]["dev"]).lower()
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    for tool in ("mutmut", "diff-cover"):
        assert tool in dev, f"{tool} missing from the dev dependency group"
        assert re.search(rf'name = "{tool}"', lock), f"{tool} is not locked in uv.lock"
    assert "paths_to_mutate" in pyproject()["tool"]["mutmut"]


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "CI wiring of the profile, branch coverage and the changed-lines gate")
def test_ci_wires_profile_coverage_and_diff_cover() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert re.search(r"HYPOTHESIS_PROFILE:\s*ci\b", text)
    assert "--cov-branch" in text
    t = thresholds()["coverage"]["changed_lines_min"]
    assert re.search(rf"diff-cover[^\n]*--fail-under[= ]{round(100 * t)}\b", text)


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "pytest loads the profile plugin from tests/ on every run")
def test_pytest_loads_the_profile_plugin() -> None:
    cfg = pyproject()["tool"]["pytest"]
    assert "tests" in cfg["pythonpath"]
    assert any(a == "-p" or a.startswith("-p") for a in cfg["addopts"])
    assert "_hypothesis_profiles" in " ".join(cfg["addopts"])


def profile_examples(profile: str | None) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "HYPOTHESIS_PROFILE"}
    if profile is not None:
        env["HYPOTHESIS_PROFILE"] = profile
    env["PYTHONPATH"] = str(ROOT / "tests") + os.pathsep + env.get("PYTHONPATH", "")
    code = (
        "import _hypothesis_profiles\n"
        "from hypothesis import settings\n"
        "s = settings()\n"
        "print(s.max_examples, s.deadline)\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120, check=False
    )


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "ci = 200 and release = 2000 examples per test, no deadline")
@pytest.mark.parametrize(("profile", "examples"), [("ci", 200), ("release", 2000), ("dev", 50)])
def test_hypothesis_profiles(profile: str, examples: int) -> None:
    assert (ROOT / "tests" / "_hypothesis_profiles.py").is_file(), "missing tests/_hypothesis_profiles.py"
    proc = profile_examples(profile)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.split() == [str(examples), "None"]


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle(
    "hand-calculation", "the profile counts come from thresholds.yaml, not from a second source of truth"
)
def test_profile_counts_equal_the_thresholds() -> None:
    t = thresholds()["property_tests"]
    assert profile_examples("ci").stdout.split()[0] == str(t["ci_examples_per_test"])
    assert profile_examples("release").stdout.split()[0] == str(t["release_examples_per_test"])


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "hostile: an unknown profile name is an error, never a silent default")
@pytest.mark.parametrize("name", ["nightly", "CI", "ci ", "../ci"])
def test_unknown_profile_is_an_error(name: str) -> None:
    assert (ROOT / "tests" / "_hypothesis_profiles.py").is_file(), "missing tests/_hypothesis_profiles.py"
    proc = profile_examples(name)
    assert proc.returncode != 0
    assert "nightly" in proc.stderr or name in proc.stderr or "profile" in proc.stderr.lower()


def gates(*args: str):
    assert (REPO_ROOT / "tools" / "check_gates.py").is_file(), "missing tools/check_gates.py"
    return run_tool("check_gates.py", *args)


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "NFR-000-08: coverage gates at 0.90, hand-picked on both sides")
@pytest.mark.parametrize(
    ("flag", "value", "code"),
    [
        ("--branch-coverage", "0.90", 0),
        ("--branch-coverage", "0.9001", 0),
        ("--branch-coverage", "1", 0),
        ("--branch-coverage", "0.8999", 1),
        ("--branch-coverage", "0", 1),
        ("--changed-lines-coverage", "0.90", 0),
        ("--changed-lines-coverage", "0.89", 1),
    ],
)
def test_coverage_gates(flag: str, value: str, code: int) -> None:
    proc = gates(flag, value)
    assert proc.returncode == code, proc.stdout + proc.stderr
    assert ("FAIL" in proc.stdout) is (code == 1)


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "mutation: >= 0.80 ok, [0.70, 0.80) warns, < 0.70 fails")
@pytest.mark.parametrize(
    ("score", "code", "word"),
    [
        ("0.80", 0, "OK"),
        ("0.95", 0, "OK"),
        ("0.75", 0, "warn"),
        ("0.70", 0, "warn"),
        ("0.6999", 1, "FAIL"),
        ("0", 1, "FAIL"),
    ],
)
def test_mutation_gate(score: str, code: int, word: str) -> None:
    proc = gates("--mutation-score", score)
    assert proc.returncode == code, proc.stdout + proc.stderr
    assert word in proc.stdout


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "Hypothesis examples per test: 200 in CI, 2000 at release")
@pytest.mark.parametrize(
    ("profile", "n", "code"),
    [("ci", 200, 0), ("ci", 199, 1), ("release", 2000, 0), ("release", 1999, 1), ("release", 200, 1), ("ci", 5000, 0)],
)
def test_hypothesis_examples_gate(profile: str, n: int, code: int) -> None:
    proc = gates("--hypothesis-examples", str(n), "--profile", profile)
    assert proc.returncode == code, proc.stdout + proc.stderr


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "the gate reads its limits from the thresholds file it is given")
def test_custom_thresholds_file(tmp_path: Path) -> None:
    custom = tmp_path / "t.yaml"
    custom.write_text(
        "coverage: {branch_core_min: 0.5, changed_lines_min: 0.5}\n"
        "mutation: {numerical_core_min: 0.5, numerical_core_fail_below: 0.25, other_min: 0.1}\n"
        "property_tests: {ci_examples_per_test: 10, release_examples_per_test: 20}\n",
        encoding="utf-8",
    )
    assert gates("--thresholds", str(custom), "--branch-coverage", "0.5").returncode == 0
    assert gates("--thresholds", str(custom), "--branch-coverage", "0.49").returncode == 1
    assert gates("--thresholds", str(custom), "--mutation-score", "0.3").returncode == 0
    assert gates("--thresholds", str(custom), "--hypothesis-examples", "20", "--profile", "release").returncode == 0


@pytest.mark.req("NFR-000-08")
@pytest.mark.oracle("hand-calculation", "hostile values are usage errors, not crashes")
@pytest.mark.parametrize(
    "args",
    [
        ["--branch-coverage", "nan"],
        ["--branch-coverage", "1.5"],
        ["--branch-coverage", "-0.1"],
        ["--branch-coverage", "high"],
        ["--mutation-score", "inf"],
        ["--hypothesis-examples", "10"],
        ["--hypothesis-examples", "ten", "--profile", "ci"],
        ["--hypothesis-examples", "10", "--profile", "nightly"],
        ["--thresholds", "no_such_file.yaml", "--branch-coverage", "0.9"],
    ],
)
def test_hostile_gate_arguments(args: list[str]) -> None:
    proc = gates(*args)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
