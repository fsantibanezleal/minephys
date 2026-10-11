"""T-000-023 (NFR-000-07): the benchmark runner `tools/bench.py` with a reference-size registry.

Expected CLI (all output JSON on stdout when `--json` is given):

    python tools/bench.py --list --json [--registry FILE]
        a JSON list of cases `{"name": "<module>.<function>", "module": str, "function": str,
        "kind": "closed_form" | "iterative" | "sampling", "reference_size": {...}, "budget_ms": number}`;
        names are unique; `budget_ms` is 1.0 for `closed_form` and 50.0 for `iterative` and `sampling`
        (NFR-000-07: closed-form scalar call <= 1 ms; iterative or sampling call at its reference size <= 50 ms).
    python tools/bench.py --run NAME [--repeat N] [--registry FILE] --json
        times NAME N times (default 20) after one warm-up call and prints
        `{"name", "repeat", "median_ms", "budget_ms", "passed"}`; `passed` is `median_ms <= budget_ms`.
    python tools/bench.py --check [--repeat N] [--registry FILE] --json
        runs every case; exit status 1 if any median exceeds its budget (the release gate), else 0.

`--registry FILE` replaces the built-in registry with a JSON document
`{"cases": [{"name", "callable": "<module>:<attribute>", "args": [...], "kwargs": {...}, "kind", "reference_size"}]}`
(used by the tests; the built-in registry is a Python list in `tools/bench.py` that each module spec extends).
Usage errors (unknown case, malformed registry, duplicate names, `--repeat` outside 1..100000, unknown kind) exit with
status 2 and a message naming the problem, never a traceback.

Oracle: hand calculation (budgets of NFR-000-07) and the known duration of `time.sleep` for the timer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _mini_repo import REPO_ROOT, run_tool

BUDGET = {"closed_form": 1.0, "iterative": 50.0, "sampling": 50.0}


def registry(tmp: Path, cases: list[dict]) -> Path:
    path = tmp / "registry.json"
    path.write_text(json.dumps({"cases": cases}), encoding="utf-8")
    return path


FAST = {"name": "fx.fast", "callable": "math:sqrt", "args": [2.0], "kind": "closed_form", "reference_size": {}}
SLOW_CLOSED = {
    "name": "fx.slow_closed",
    "callable": "time:sleep",
    "args": [0.05],
    "kind": "closed_form",
    "reference_size": {"n": 1},
}
SLOW_ITER = {
    "name": "fx.slow_iter",
    "callable": "time:sleep",
    "args": [0.12],
    "kind": "iterative",
    "reference_size": {"n": 200},
}
OK_ITER = {
    "name": "fx.ok_iter",
    "callable": "time:sleep",
    "args": [0.005],
    "kind": "sampling",
    "reference_size": {"n_draws": 10000},
}


def bench(*args: str):
    assert (REPO_ROOT / "tools" / "bench.py").is_file(), "missing tools/bench.py"
    return run_tool("bench.py", *args, "--json")


def one(**over: object) -> dict:
    base = {"name": "a.b", "callable": "math:sqrt", "args": [1.0], "kind": "closed_form", "reference_size": {}}
    return {**base, **over}


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "the registry lists names, kinds, reference sizes and the NFR-000-07 budgets")
def test_list_reports_the_registry_with_budgets(tmp_path: Path) -> None:
    reg = registry(tmp_path, [FAST, SLOW_ITER, OK_ITER])
    proc = bench("--list", "--registry", str(reg))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    cases = json.loads(proc.stdout)
    assert [c["name"] for c in cases] == ["fx.fast", "fx.slow_iter", "fx.ok_iter"]
    for c in cases:
        assert c["kind"] in BUDGET
        assert c["budget_ms"] == BUDGET[c["kind"]]
        assert isinstance(c["reference_size"], dict)
        assert c["module"] == c["name"].split(".")[0]
        assert c["function"] == c["name"].split(".", 1)[1]


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle(
    "hand-calculation", "the built-in registry is well formed: unique names, known kinds, right budgets"
)
def test_builtin_registry_is_well_formed() -> None:
    proc = bench("--list")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    cases = json.loads(proc.stdout)
    assert isinstance(cases, list)
    names = [c["name"] for c in cases]
    assert len(names) == len(set(names))
    for c in cases:
        assert c["kind"] in BUDGET
        assert c["budget_ms"] == BUDGET[c["kind"]]
        assert "." in c["name"]
        assert isinstance(c["reference_size"], dict)


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "time.sleep(0.05) takes about 50 ms; the median of 5 calls reflects it")
def test_run_times_a_known_duration(tmp_path: Path) -> None:
    reg = registry(tmp_path, [SLOW_CLOSED])
    proc = bench("--run", "fx.slow_closed", "--repeat", "5", "--registry", str(reg))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["name"] == "fx.slow_closed"
    assert data["repeat"] == 5
    assert 45.0 <= data["median_ms"] <= 120.0
    assert data["budget_ms"] == 1.0
    assert data["passed"] is False


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "a fast closed form is within its 1 ms budget")
def test_run_passes_a_fast_case(tmp_path: Path) -> None:
    reg = registry(tmp_path, [FAST])
    data = json.loads(bench("--run", "fx.fast", "--registry", str(reg)).stdout)
    assert data["repeat"] == 20, "the default is the median of 20 calls (NFR-000-07)"
    assert data["median_ms"] < 1.0
    assert data["passed"] is True


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "--check gates on the budgets: one slow case fails the release gate")
def test_check_gate(tmp_path: Path) -> None:
    good_dir = tmp_path / "g"
    good_dir.mkdir()
    good = registry(good_dir, [FAST, OK_ITER])
    ok = bench("--check", "--repeat", "3", "--registry", str(good))
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad_dir = tmp_path / "b"
    bad_dir.mkdir()
    bad = registry(bad_dir, [FAST, SLOW_ITER])
    failed = bench("--check", "--repeat", "3", "--registry", str(bad))
    assert failed.returncode == 1
    report = json.loads(failed.stdout)
    results = {r["name"]: r for r in report["results"]}
    assert results["fx.fast"]["passed"] is True
    assert results["fx.slow_iter"]["passed"] is False
    assert results["fx.slow_iter"]["median_ms"] > 50.0


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "hostile usage: every error is a status-2 message, not a traceback")
@pytest.mark.parametrize(
    "args",
    [
        ["--run", "no.such_case"],
        ["--run", "fx.fast", "--repeat", "0"],
        ["--run", "fx.fast", "--repeat", "-3"],
        ["--run", "fx.fast", "--repeat", "1000000000"],
        ["--run", "fx.fast", "--repeat", "many"],
        ["--run"],
        [],
    ],
)
def test_hostile_usage(tmp_path: Path, args: list[str]) -> None:
    reg = registry(tmp_path, [FAST])
    proc = bench(*args, "--registry", str(reg))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert (proc.stdout + proc.stderr).strip()


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "hostile registries are rejected with status 2")
@pytest.mark.parametrize(
    "document",
    [
        "{not json",
        '{"cases": "nope"}',
        '{"cases": [{"name": "a.b"}]}',
        json.dumps({"cases": [one(kind="huge")]}),
        json.dumps({"cases": [one(name="ab")]}),
        json.dumps({"cases": [one(), one(callable="math:floor")]}),
        json.dumps({"cases": [one(args="not a list")]}),
        "",
    ],
)
def test_hostile_registry(tmp_path: Path, document: str) -> None:
    path = tmp_path / "registry.json"
    path.write_text(document, encoding="utf-8")
    proc = bench("--list", "--registry", str(path))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr


@pytest.mark.req("NFR-000-07")
@pytest.mark.oracle("hand-calculation", "an unimportable callable is a status-2 usage error when the case is run")
def test_unimportable_callable_is_a_usage_error(tmp_path: Path) -> None:
    reg = registry(tmp_path, [one(name="x.y", callable="no_such_module_xyz:f")])
    proc = bench("--run", "x.y", "--registry", str(reg))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "no_such_module_xyz" in proc.stdout + proc.stderr
