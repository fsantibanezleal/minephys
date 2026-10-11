"""T-000-021 (FR-000-25, NFR-000-06): the Pyodide smoke job (Node 24, pinned Pyodide).

Expected deliverables:

* `tests/pyodide/run_smoke.mjs`: a Node script that loads the pinned Pyodide (314.0.x), loads Pyodide's own `numpy`
  and `pyyaml` packages, installs the wheel with `micropip` WITHOUT resolving dependencies (`deps=False`), runs
  `tests/pyodide/smoke.py` inside Pyodide and prints `SMOKE OK <module>` for every module and `SMOKE OK` at the end.
  Usage: `node tests/pyodide/run_smoke.mjs <path-to-wheel>`; exit status 0 only if every smoke check passed.
* `tests/pyodide/smoke.py`: imports every public subpackage and checks ONE worked-example value per module of this
  scope (spec 001 haulage 3.8239358 m/s, 002 blasting 0.29940630 m, 003 geotech mb = 1.676772, 004 bulk 106.28641 kg/s).
* `.github/workflows/ci.yml`: a job `pyodide` that uses Node 24 and a pinned `314.0.` Pyodide version and runs
  `pytest -m pyodide`; the wheel job runs the suite selected by `-m "not gpu and not pyodide and not kit"`.

The static tests run in the default suite; the runtime test is marked `pyodide` and runs in the CI job (it needs
Node 24 and the Pyodide npm package) against the wheel named by `MINEPHYS_WHEEL` or the newest `dist/*.whl`.

Oracle: analytical (the file contents and workflow fields demanded by FR-000-25) and the worked examples of the module
specs, copied here as printed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "pyodide" / "run_smoke.mjs"
SMOKE = ROOT / "tests" / "pyodide" / "smoke.py"
CI = ROOT / ".github" / "workflows" / "ci.yml"
SCOPE = {
    "haulage": "3.8239358",
    "blasting": "0.2994063",
    "geotech": "1.676772",
    "bulk": "106.28641",
}


def _text(path: Path) -> str:
    assert path.is_file(), f"missing {path.relative_to(ROOT).as_posix()}"
    return path.read_text(encoding="utf-8")


@pytest.mark.req("FR-000-25")
@pytest.mark.oracle("analytical", "FR-000-25: micropip with Pyodide's own NumPy and PyYAML")
def test_runner_installs_the_wheel_with_micropip_and_pyodides_own_packages() -> None:
    js = _text(RUNNER)
    assert "loadPyodide" in js
    assert "micropip" in js
    assert re.search(r"numpy", js)
    assert re.search(r"pyyaml", js, re.I)
    assert re.search(r"deps\s*[:=]\s*(false|False)", js), "the wheel must be installed with deps=False"
    assert "smoke.py" in js
    assert "SMOKE OK" in js


@pytest.mark.req("FR-000-25")
@pytest.mark.oracle("analytical", "FR-000-25: the smoke subset is one worked-example oracle per module")
def test_smoke_script_covers_every_module_of_the_scope() -> None:
    py = _text(SMOKE)
    for module, value in SCOPE.items():
        assert f"minephys.{module}" in py, module
        assert value in py, f"the smoke subset of {module} must pin its worked value {value}"
    assert py.count("assert") >= len(SCOPE)
    assert "SMOKE OK" in py or "SMOKE OK" in _text(RUNNER)


@pytest.mark.req("FR-000-25")
@pytest.mark.oracle("analytical", "FR-000-25: every public subpackage imports in the smoke run")
def test_smoke_script_imports_every_public_subpackage_found_on_disk() -> None:
    py = _text(SMOKE)
    pkg = ROOT / "src" / "minephys"
    subpackages = sorted(
        p.name for p in pkg.iterdir() if p.is_dir() and (p / "__init__.py").is_file() and not p.name.startswith("_")
    )
    assert set(SCOPE) <= set(subpackages), "the modules of this scope must exist before the smoke job can be green"
    for sub in subpackages:
        assert re.search(rf"minephys\.{sub}\b", py), f"smoke.py does not import minephys.{sub}"


def _ci() -> dict:
    return yaml.safe_load(_text(CI))


@pytest.mark.req("FR-000-25")
@pytest.mark.req("NFR-000-06")
@pytest.mark.oracle("analytical", "NFR-000-06: a CI job pins Node 24 and Pyodide 314.0.x")
def test_ci_has_a_pyodide_job_with_pinned_versions() -> None:
    jobs = _ci()["jobs"]
    assert "pyodide" in jobs, "no `pyodide` job in .github/workflows/ci.yml"
    text = yaml.safe_dump(jobs["pyodide"])
    assert re.search(r"node-version['\"]?:\s*['\"]?24", text), "Node 24 must be pinned"
    assert re.search(r"314\.0\.\d+", text), "Pyodide must be pinned to the 314.0.x series"
    assert "pytest" in text
    assert re.search(r"-m\s+['\"]?pyodide", text)


@pytest.mark.req("FR-000-24")
@pytest.mark.oracle(
    "analytical", "FR-000-24: the wheel job runs the suite selected by -m 'not gpu and not pyodide and not kit'"
)
def test_wheel_job_selects_the_portable_subset() -> None:
    steps = _ci()["jobs"]["wheel"]["steps"]
    runs = " ".join(str(s.get("run", "")) for s in steps)
    assert "not gpu and not pyodide and not kit" in runs
    assert "pytest" in runs


@pytest.mark.pyodide
@pytest.mark.req("FR-000-25")
@pytest.mark.req("NFR-000-06")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 section 7.4: rimpull_limited_speed(1.8e6, 400000, 0.12) = 3.8239358 m/s"
)
def test_smoke_runs_in_pyodide() -> None:
    assert RUNNER.is_file(), "missing tests/pyodide/run_smoke.mjs"
    node = shutil.which("node")
    assert node, "Node 24 is required for the Pyodide job"
    major = int(
        subprocess.run([node, "--version"], capture_output=True, text=True, check=True).stdout.strip()[1:].split(".")[0]
    )
    assert major == 24, f"Node 24 expected, found {major}"
    wheel = os.environ.get("MINEPHYS_WHEEL")
    if wheel is None:
        candidates = sorted((ROOT / "dist").glob("minephys-*.whl"), key=lambda p: p.stat().st_mtime)
        assert candidates, "build the wheel first (uv build --wheel) or set MINEPHYS_WHEEL"
        wheel = str(candidates[-1])
    proc = subprocess.run(
        [node, str(RUNNER), wheel], capture_output=True, text=True, encoding="utf-8", timeout=900, check=False
    )
    assert proc.returncode == 0, proc.stdout[-3000:] + proc.stderr[-3000:]
    for module in SCOPE:
        assert f"SMOKE OK {module}" in proc.stdout
    assert proc.stdout.strip().splitlines()[-1].strip() == "SMOKE OK"
