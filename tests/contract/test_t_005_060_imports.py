"""T-005-060 (NFR-005-01): `minephys.comminution` imports only the standard library, NumPy, PyYAML and `minephys`.

Method: a fresh interpreter imports `minephys.comminution`; the top-level modules it added to `sys.modules`, relative to a
bare interpreter started the same way, must all be standard-library modules (`sys.stdlib_module_names`), `numpy`, `yaml`
(and PyYAML's `_yaml` accelerator) or `minephys`. SciPy, networkx, pandas and jsonschema must be absent (NFR-005-01).
Oracle: hand-written allow-list (spec 005 NFR-005-01, foundation NFR-000-05).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SCRIPT = """
import json, sys
before = set(sys.modules)
import minephys.comminution
tops = sorted({m.split('.')[0] for m in set(sys.modules) - before})
print(json.dumps({"added": tops, "stdlib": sorted(sys.stdlib_module_names)}))
"""
ALLOWED = {"numpy", "yaml", "_yaml", "minephys"}
FORBIDDEN = {"scipy", "networkx", "pandas", "jsonschema", "ortools", "sympy", "numba", "torch"}


def _import_audit() -> tuple[set[str], set[str]]:
    proc = subprocess.run([sys.executable, "-c", SCRIPT], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert proc.returncode == 0, f"import minephys.comminution failed:\n{proc.stderr[-1500:]}"
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    return set(data["added"]), set(data["stdlib"])


@pytest.mark.req("NFR-005-01")
@pytest.mark.oracle("hand-calculation", "allow-list: standard library, numpy, yaml, minephys")
def test_nfr_005_01_only_allowed_top_level_modules_are_imported() -> None:
    added, stdlib = _import_audit()
    extra = {m for m in added if m not in stdlib and m not in ALLOWED}
    assert not extra, f"minephys.comminution imports modules outside the allow-list: {sorted(extra)}"


@pytest.mark.req("NFR-005-01")
def test_nfr_005_01_no_heavy_scientific_package_is_imported() -> None:
    added, _ = _import_audit()
    assert not (added & FORBIDDEN), sorted(added & FORBIDDEN)


@pytest.mark.req("NFR-005-01")
def test_nfr_005_01_source_does_not_mention_forbidden_imports() -> None:
    src = ROOT / "src" / "minephys" / "comminution"
    assert src.is_dir(), "missing src/minephys/comminution/"
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in FORBIDDEN:
            assert f"import {name}" not in text and f"from {name}" not in text, f"{path.name} imports {name}"
