"""T-000-022 (FR-000-26): the NVIDIA Kit smoke import and its "not run" report when Kit is absent.

FR-000-26 asks that, without Kit, the test reports "not run" instead of passing silently. A test file may not use a
skip marker in this repository, so the behaviour lives in a tool and is tested directly:

    python tools/kit_smoke.py [--kit-python PATH] [--wheel PATH] [--src PATH] [--target DIR] [--no-discover]

* The Kit interpreter is `--kit-python`, else the environment variable `MINEPHYS_KIT_PYTHON`, else (unless
  `--no-discover`) the default Kit install folders of the machine.
* No Kit interpreter found (or the given path does not exist): print a line that contains `not run` and `Kit`, run
  nothing and exit with status 3 (the "not run" status, distinct from failure 1).
* Otherwise: with `--wheel` (and `--target`, default a temporary folder on the interpreter's path) install the wheel
  with `<kit-python> -m pip install --no-deps --target`; with `--src PATH` put that source folder on the path instead
  (development mode); then run `tests/pyodide/smoke.py` with that interpreter. It prints `SMOKE OK <module>` per
  module and a final `SMOKE OK`; the tool echoes it and exits 0, or exits 1 naming the failing import or assertion.
  It also prints the interpreter's `major.minor` version (Kit embeds 3.12).

Tests marked `kit` need a real Kit installation and run locally only; the others use the current interpreter as a
stand-in "Kit" in development mode (`--src`).

Oracle: hand calculation (exit-status protocol above) and the worked values of the smoke script (spec 000 FR-000-26).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "kit_smoke.py"


def run(*args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    assert TOOL.is_file(), "missing tools/kit_smoke.py"
    env = {k: v for k, v in os.environ.items() if k != "MINEPHYS_KIT_PYTHON"}
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        env=env,
        check=False,
    )


@pytest.mark.req("FR-000-26")
@pytest.mark.oracle("hand-calculation", "FR-000-26: no Kit means 'not run' and status 3, never a silent pass")
def test_without_kit_the_tool_reports_not_run() -> None:
    proc = run("--no-discover")
    assert proc.returncode == 3, proc.stdout + proc.stderr
    out = (proc.stdout + proc.stderr).lower()
    assert "not run" in out
    assert "kit" in out
    assert "smoke ok" not in out


@pytest.mark.req("FR-000-26")
@pytest.mark.oracle("hand-calculation", "a --kit-python path that does not exist is the same 'not run' situation")
def test_a_missing_kit_interpreter_is_not_run(tmp_path: Path) -> None:
    proc = run("--no-discover", "--kit-python", str(tmp_path / "no-such-kit" / "python.exe"))
    assert proc.returncode == 3
    assert "not run" in (proc.stdout + proc.stderr).lower()
    env_proc = run("--no-discover", env_extra={"MINEPHYS_KIT_PYTHON": str(tmp_path / "nowhere")})
    assert env_proc.returncode == 3
    assert "not run" in (env_proc.stdout + env_proc.stderr).lower()


@pytest.mark.req("FR-000-26")
@pytest.mark.oracle(
    "hand-calculation", "a stand-in interpreter in development mode imports the package and runs the smoke"
)
def test_stand_in_interpreter_runs_the_smoke_subset() -> None:
    proc = run("--kit-python", sys.executable, "--src", str(ROOT / "src"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    for module in ("haulage", "blasting", "geotech", "bulk"):
        assert f"SMOKE OK {module}" in lines, module
    assert lines[-1].strip() == "SMOKE OK" or "SMOKE OK" in lines
    assert f"{sys.version_info.major}.{sys.version_info.minor}" in proc.stdout


@pytest.mark.req("FR-000-26")
@pytest.mark.oracle("hand-calculation", "a broken source tree makes the smoke fail with status 1 naming the import")
def test_a_failing_smoke_exits_one(tmp_path: Path) -> None:
    empty = tmp_path / "src"
    (empty / "minephys").mkdir(parents=True)
    (empty / "minephys" / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    proc = run("--kit-python", sys.executable, "--src", str(empty))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    out = proc.stdout + proc.stderr
    assert "minephys" in out
    assert "SMOKE OK haulage" not in out


@pytest.mark.kit
@pytest.mark.req("FR-000-26")
@pytest.mark.oracle("hand-calculation", "local machine: with Kit the smoke passes, without Kit the tool says 'not run'")
def test_on_this_machine_kit_passes_or_is_reported_not_run() -> None:
    proc = run()
    assert proc.returncode in (0, 3), proc.stdout + proc.stderr
    if proc.returncode == 3:
        assert "not run" in (proc.stdout + proc.stderr).lower()
    else:
        assert "SMOKE OK" in proc.stdout
