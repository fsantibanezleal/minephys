"""T-008-070 (SC-008-01): integrity of the packaged knowledge at every release, enforced by a CI step on every push.

Success criterion: `validate` reports 0 errors, and there are 0 verified rows or equations without a `knowledge` marker.
1. `python -m minephys.knowledge validate` run on the packaged knowledge exits 0 (the real package, no fixture) and lists no error.
2. Every packaged row with `verification: verified` (tables and share-alike tables) and every packaged equation with
   `verification: verified` is pinned by a literal `@pytest.mark.knowledge("<id>")` in the test tree (an `ast` scan of `tests/`, as in
   T-008-021): 0 unpinned verified rows or equations.
3. `.github/workflows/ci.yml` runs the validation: a step of a job that runs on `push` has a `run` command containing
   `python -m minephys.knowledge validate` (`uv run python -m minephys.knowledge validate` is accepted), and the workflow triggers on `push`.
4. Failure paths of the command: a fixture knowledge folder with a verified row that has no `verified_on` makes `validate PATH` exit 1
   (the exit code the CI step relies on), and a folder that does not exist exits 2.

Oracle: the exit-code contract of FR-008-18, the packaged files themselves and the workflow file (hand-written rules of spec 008).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "src" / "minephys" / "knowledge"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def _markers() -> set[str]:
    found: set[str] = set()
    for path in sorted((ROOT / "tests").rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "knowledge":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    found.add(node.args[0].value)
    return found


def _verified_ids() -> list[str]:
    ids: list[str] = []
    for path in [*KNOWLEDGE.glob("*.yaml"), *KNOWLEDGE.glob("share-alike/*.yaml")]:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        ids += [r["id"] for r in doc["rows"] if r["verification"] == "verified"]
    eq = KNOWLEDGE / "catalogue" / "equations.yaml"
    if eq.is_file():
        ids += [
            e["id"]
            for e in yaml.safe_load(eq.read_text(encoding="utf-8"))["equations"]
            if e["verification"] == "verified"
        ]
    return ids


@pytest.mark.req("SC-008-01")
@pytest.mark.oracle("hand-calculation", "validate on the packaged knowledge exits 0 (FR-008-18)")
def test_sc_008_01_validate_on_the_packaged_knowledge_exits_0() -> None:
    proc = fx.run_cli(["validate"])
    assert proc.returncode == 0, f"validate reported errors:\n{proc.stdout[-1500:]}{proc.stderr[-1500:]}"


@pytest.mark.req("SC-008-01")
@pytest.mark.oracle("hand-calculation", "0 verified rows or equations without a knowledge marker")
def test_sc_008_01_every_verified_row_and_equation_is_pinned() -> None:
    assert KNOWLEDGE.is_dir(), "missing src/minephys/knowledge/"
    verified = _verified_ids()
    assert verified, "the packaged knowledge has no verified row (the units table of the foundation has six)"
    pinned = _markers()
    missing = sorted(i for i in verified if i not in pinned)
    assert missing == [], f"verified rows or equations without a @pytest.mark.knowledge pin: {missing}"


def _ci_steps() -> list[dict[str, Any]]:
    assert CI.is_file(), "missing .github/workflows/ci.yml"
    doc = yaml.safe_load(CI.read_text(encoding="utf-8"))
    triggers = doc.get(True, doc.get("on"))  # YAML 1.1 reads the key `on` as True
    assert triggers is not None and "push" in (triggers if isinstance(triggers, (dict, list)) else [triggers]), (
        "the workflow must run on push"
    )
    steps: list[dict[str, Any]] = []
    for job in doc["jobs"].values():
        steps += [s for s in job.get("steps", []) if isinstance(s, dict)]
    return steps


@pytest.mark.req("SC-008-01")
@pytest.mark.oracle("hand-calculation", "the CI workflow runs `python -m minephys.knowledge validate`")
def test_sc_008_01_ci_runs_the_validation_step() -> None:
    runs = [str(s["run"]) for s in _ci_steps() if "run" in s]
    assert any("python -m minephys.knowledge validate" in r for r in runs), (
        "no CI step runs `python -m minephys.knowledge validate`"
    )


@pytest.mark.req("SC-008-01")
@pytest.mark.oracle("hand-calculation", "the validation step must be able to fail the build")
def test_sc_008_01_the_validation_step_is_not_ignored() -> None:
    for s in _ci_steps():
        if "minephys.knowledge validate" in str(s.get("run", "")):
            assert s.get("continue-on-error") in (None, False), "the validation step must not continue on error"
            assert "|| true" not in str(s["run"]) and "|| exit 0" not in str(s["run"])


@pytest.mark.req("SC-008-01")
@pytest.mark.oracle("hand-calculation", "exit 1 for invalid knowledge, 2 for a missing folder")
def test_sc_008_01_the_command_fails_the_build_on_bad_knowledge(tmp_path: Path) -> None:
    tables = fx.good_tables()
    del tables["blasting"]["rows"][0]["verified_on"]  # a verified row without its date
    bad = fx.write_tree(tmp_path / "bad", tables=tables)
    assert fx.run_cli(["validate", str(bad)]).returncode == 1
    assert fx.run_cli(["validate", str(tmp_path / "missing")]).returncode == 2
    good = fx.write_tree(tmp_path / "good")
    assert fx.run_cli(["validate", str(good)]).returncode == 0
