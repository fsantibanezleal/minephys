"""T-007-050 (NFR-007-01): `minephys.planning` imports only the standard library, NumPy, PyYAML and `minephys`.

Method: a fresh interpreter imports `minephys.planning`; the top-level modules it added to `sys.modules`, relative to a bare
interpreter, must all be standard-library modules (`sys.stdlib_module_names`), `numpy`, `yaml` (and PyYAML's `_yaml` accelerator)
or `minephys`. `networkx`, OR-Tools, SciPy, pandas and jsonschema must be absent from the imports, and no file under
`src/minephys/planning/` may contain an import of `networkx` or `ortools` (source scan): they are test-only oracles.
Oracle: hand-written allow-list (spec 007 NFR-007-01, foundation NFR-000-05).
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SCRIPT = """
import json, sys
before = set(sys.modules)
import minephys.planning
tops = sorted({m.split('.')[0] for m in set(sys.modules) - before})
print(json.dumps({"added": tops, "stdlib": sorted(sys.stdlib_module_names)}))
"""
ALLOWED = {"numpy", "yaml", "_yaml", "minephys"}
FORBIDDEN = {"networkx", "ortools", "scipy", "pandas", "jsonschema", "sympy", "numba", "torch", "psutil"}


def _audit() -> tuple[set[str], set[str]]:
    proc = subprocess.run([sys.executable, "-c", SCRIPT], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert proc.returncode == 0, f"import minephys.planning failed:\n{proc.stderr[-1500:]}"
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    return set(data["added"]), set(data["stdlib"])


@pytest.mark.req("NFR-007-01")
@pytest.mark.oracle("hand-calculation", "allow-list: standard library, numpy, yaml, minephys")
def test_nfr_007_01_only_allowed_top_level_modules_are_imported() -> None:
    added, stdlib = _audit()
    extra = {m for m in added if m not in stdlib and m not in ALLOWED}
    assert not extra, f"minephys.planning imports modules outside the allow-list: {sorted(extra)}"
    assert not (added & FORBIDDEN), sorted(added & FORBIDDEN)


@pytest.mark.req("NFR-007-01")
@pytest.mark.oracle("hand-calculation", "source scan: networkx and OR-Tools are test-only oracles")
def test_nfr_007_01_source_never_imports_networkx_or_ortools() -> None:
    src = ROOT / "src" / "minephys" / "planning"
    assert src.is_dir(), "missing src/minephys/planning/"
    files = list(src.rglob("*.py"))
    assert files, "no source file under src/minephys/planning/"
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                assert name not in FORBIDDEN, f"{path.name} imports {name}"


@pytest.mark.req("NFR-007-01")
def test_nfr_007_01_the_whole_source_tree_is_free_of_the_test_only_oracles() -> None:
    src = ROOT / "src"
    assert (src / "minephys" / "planning").is_dir()
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import networkx" not in text and "from networkx" not in text, f"{path} uses networkx"
        assert "import ortools" not in text and "from ortools" not in text, f"{path} uses ortools"
