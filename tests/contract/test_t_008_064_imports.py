"""T-008-064 (NFR-008-05): the runtime imports of `minephys.knowledge` are the standard library, PyYAML and NumPy; `jsonschema` is test-only.

Method: a fresh interpreter imports `minephys.knowledge`, then uses it (`validate_tables()`, `export_json()`, `list_parameters()`) so that
imports made lazily on first use are seen too; the top-level modules added to `sys.modules` relative to a bare interpreter must all be
standard-library modules (`sys.stdlib_module_names`), `numpy`, `yaml` (and PyYAML's `_yaml` accelerator), or `minephys`. `jsonschema`,
`referencing`, `rpds`, `attrs`, SciPy, pandas and similar must be absent, and no file under `src/minephys/knowledge/` may import them
(source scan, `ast`). The command line entry point (`python -m minephys.knowledge validate`) is held to the same list in a second
fresh interpreter run through `runpy`.

Oracle: hand-written allow-list (spec 008 NFR-008-05, foundation NFR-000-05).
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
import minephys.knowledge as K
K.validate_tables()
K.list_parameters()
K.export_json()
tops = sorted({m.split('.')[0] for m in set(sys.modules) - before})
print(json.dumps({"added": tops, "stdlib": sorted(sys.stdlib_module_names)}))
"""
CLI_SCRIPT = """
import json, runpy, sys
before = set(sys.modules)
sys.argv = ["minephys.knowledge", "validate"]
try:
    runpy.run_module("minephys.knowledge", run_name="__main__")
except SystemExit:
    pass
tops = sorted({m.split('.')[0] for m in set(sys.modules) - before})
print(json.dumps({"added": tops, "stdlib": sorted(sys.stdlib_module_names)}))
"""
ALLOWED = {"numpy", "yaml", "_yaml", "minephys"}
# PyYAML's compiled `_yaml` extension (Cython) registers the top-level runtime modules `cython_runtime` and `_cython_<version>`.
RUNTIME_INTERNALS = ("cython_runtime", "_cython_")
FORBIDDEN = {
    "jsonschema",
    "referencing",
    "rpds",
    "attr",
    "attrs",
    "scipy",
    "pandas",
    "sympy",
    "numba",
    "torch",
    "psutil",
    "networkx",
    "ortools",
    "bibtexparser",
    "pybtex",
    "ruamel",
    "toml",
    "tomli",
}


def _audit(script: str) -> tuple[set[str], set[str]]:
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=120,
    )
    assert proc.returncode == 0, f"the interpreter failed:\n{proc.stderr[-1500:]}"
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    return set(data["added"]), set(data["stdlib"])


@pytest.mark.req("NFR-008-05")
@pytest.mark.oracle("hand-calculation", "allow-list: standard library, numpy, yaml, minephys")
def test_nfr_008_05_only_allowed_top_level_modules_are_imported() -> None:
    added, stdlib = _audit(SCRIPT)
    assert "minephys" in added
    extra = {m for m in added if m not in stdlib and m not in ALLOWED and not m.startswith(RUNTIME_INTERNALS)}
    assert not extra, f"minephys.knowledge imports modules outside the allow-list: {sorted(extra)}"
    assert not (added & FORBIDDEN), sorted(added & FORBIDDEN)


@pytest.mark.req("NFR-008-05")
@pytest.mark.oracle("hand-calculation", "allow-list also holds for the command line entry point")
def test_nfr_008_05_the_command_line_entry_point_uses_the_same_modules() -> None:
    added, stdlib = _audit(CLI_SCRIPT)
    extra = {m for m in added if m not in stdlib and m not in ALLOWED and not m.startswith(RUNTIME_INTERNALS)}
    assert not extra, f"`python -m minephys.knowledge` imports modules outside the allow-list: {sorted(extra)}"


@pytest.mark.req("NFR-008-05")
@pytest.mark.oracle(
    "hand-calculation", "source scan: jsonschema and the other test-only tools are never imported by the package"
)
def test_nfr_008_05_source_never_imports_test_only_tools() -> None:
    src = ROOT / "src" / "minephys" / "knowledge"
    assert src.is_dir(), "missing src/minephys/knowledge/"
    files = list(src.rglob("*.py"))
    assert files, "no source file under src/minephys/knowledge/"
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


@pytest.mark.req("NFR-008-05")
def test_nfr_008_05_the_whole_source_tree_is_free_of_jsonschema() -> None:
    src = ROOT / "src"
    assert (src / "minephys" / "knowledge").is_dir()
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import jsonschema" not in text and "from jsonschema" not in text, f"{path} uses jsonschema"
