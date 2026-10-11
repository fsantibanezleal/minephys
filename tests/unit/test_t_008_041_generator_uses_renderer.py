"""T-008-041 (FR-008-21, SC-008-02): the foundation docs generator produces its pages through `render_pages`.

Expected behaviour: `tools/gen_knowledge_docs.py` (foundation FR-000-23) calls `minephys.knowledge.render_pages` and has no second
Markdown renderer (it does not read the YAML itself); run as a script it writes the pages of `render_pages` into
`docs/reference/knowledge/` of the repository it sits in (the repository root is the parent of its `tools/` folder), byte for byte; with
`--check` it exits 0 when the committed pages equal the generated ones, exits 1 when a page differs or is missing, and then rewrites nothing;
if the knowledge is invalid it exits with a non-zero code and writes no page. SC-008-02: the committed pages in this repository agree with
`render_pages` of the packaged knowledge ("0 differences reported by the generator's --check").

The generator is exercised on a private copy of itself (`<tmp>/tools/gen_knowledge_docs.py`, working directory `<tmp>`), in a child
interpreter in which the packaged knowledge is replaced by the fixture knowledge (tests/_knowledge_fixtures.py), so that the generated pages
are compared with `render_pages` of the same fixture. Only the layout "root = parent of tools/" and the flag `--check` are assumed.

Oracle: byte equality with `render_pages` output (plan 008, FR-008-21 row), and the exit-code contract of FR-000-23.
"""

from __future__ import annotations

import ast
import importlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest

GENERATOR = fx.ROOT / "tools" / "gen_knowledge_docs.py"
COMMITTED = fx.ROOT / "docs" / "reference" / "knowledge"

CHILD = """
import os, runpy, sys
root = os.environ["GEN_ROOT"]
script = os.path.join(root, "tools", "gen_knowledge_docs.py")
os.chdir(root)

def gen(extra):
    sys.argv = [script] + extra
    try:
        runpy.run_path(script, run_name="__main__")
        return 0
    except SystemExit as e:
        return 0 if e.code in (None, 0) else (e.code if isinstance(e.code, int) else 1)

def read(d):
    return {p.name: p.read_bytes().decode("utf-8") for p in sorted(pathlib.Path(d).glob("*.md"))}

docs = pathlib.Path(root, "docs", "reference", "knowledge")
steps = {}
steps["generate"] = gen([])
steps["generated"] = read(docs)
ref = pathlib.Path(root, "ref_pages"); ref.mkdir()
K.render_pages(ref)
steps["rendered"] = read(ref)
steps["check_ok"] = gen(["--check"])
victim = docs / "haulage.md"
victim.write_text(victim.read_text(encoding="utf-8") + "\\nstale line\\n", encoding="utf-8", newline="\\n")
stale = read(docs)
steps["check_changed"] = gen(["--check"])
steps["unchanged_by_check"] = read(docs) == stale
victim.unlink()
steps["check_missing"] = gen(["--check"])
steps["missing_not_recreated_by_check"] = not victim.exists()
print(json.dumps(steps))
"""


def _prepare(tmp_path: Path) -> Path:
    root = tmp_path / "gen"
    (root / "tools").mkdir(parents=True)
    (root / "docs" / "reference" / "knowledge").mkdir(parents=True)
    shutil.copyfile(GENERATOR, root / "tools" / "gen_knowledge_docs.py")
    return root


def _calls_render_pages(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            if (isinstance(f, ast.Name) and f.id == "render_pages") or (
                isinstance(f, ast.Attribute) and f.attr == "render_pages"
            ):
                return True
    return False


@pytest.mark.req("FR-008-21")
@pytest.mark.oracle("hand-calculation", "the generator source calls render_pages and has no renderer of its own")
def test_fr_008_21_generator_source_calls_render_pages() -> None:
    assert GENERATOR.is_file(), "tools/gen_knowledge_docs.py is the foundation docs generator (FR-000-23)"
    source = GENERATOR.read_text(encoding="utf-8")
    assert _calls_render_pages(source), "the generator must call render_pages (one code path for docs, export and API)"
    imported = {a.name.split(".")[0] for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Import) for a in n.names}
    imported |= {(n.module or "").split(".")[0] for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
    assert "yaml" not in imported, (
        "the generator must not read the knowledge YAML itself (a second copy of the renderer)"
    )


@pytest.mark.req("FR-008-21")
@pytest.mark.oracle(
    "hand-calculation",
    "generated pages equal render_pages output byte for byte for the fixture knowledge; --check exit codes",
)
def test_fr_008_21_generated_pages_equal_render_pages_and_check_reports_differences(tmp_path: Path) -> None:
    root = _prepare(tmp_path)
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    got: dict[str, Any] = fx.run_api(base, "import pathlib\n" + CHILD, env={"GEN_ROOT": str(root)}, timeout=300)
    assert got["generate"] == 0
    assert set(got["rendered"]) == {
        "haulage.md",
        "blasting.md",
        "geotech_sa.md",
        "equations.md",
        "bibliography.md",
        "glossary.md",
    }
    assert got["generated"] == got["rendered"], "the generator's pages differ from render_pages output"
    assert got["check_ok"] == 0, "--check must pass when the pages are up to date"
    assert got["check_changed"] == 1, "--check must exit 1 when a committed page differs"
    assert got["unchanged_by_check"] is True, "--check must not rewrite pages"
    assert got["check_missing"] == 1, "--check must exit 1 when a generated page is missing"
    assert got["missing_not_recreated_by_check"] is True


@pytest.mark.req("FR-008-21")
@pytest.mark.oracle("hand-calculation", "invalid knowledge: non-zero exit, no page written")
def test_fr_008_21_generator_fails_on_invalid_knowledge_and_writes_nothing(tmp_path: Path) -> None:
    root = _prepare(tmp_path)
    bad = fx.good_tables()
    del bad["haulage"]["rows"][0]["citation"]
    base = fx.write_package_tree(tmp_path / "pkg", tables=bad)
    script = """
import os, runpy, sys
root = os.environ["GEN_ROOT"]
script = os.path.join(root, "tools", "gen_knowledge_docs.py")
os.chdir(root)
sys.argv = [script]
try:
    runpy.run_path(script, run_name="__main__")
    code = 0
except SystemExit as e:
    code = 0 if e.code in (None, 0) else (e.code if isinstance(e.code, int) else 1)
except BaseException as e:
    code = -1
print(json.dumps({"code": code, "pages": sorted(p.name for p in pathlib.Path(root, "docs", "reference", "knowledge").iterdir())}))
"""
    got = fx.run_api(base, "import pathlib\n" + script, env={"GEN_ROOT": str(root)}, timeout=300)
    assert got["code"] != 0, "an invalid knowledge must not generate docs"
    assert got["pages"] == [], "no page may be written from invalid knowledge"


@pytest.mark.req("SC-008-02")
@pytest.mark.oracle("hand-calculation", "the committed pages equal render_pages of the packaged knowledge")
def test_sc_008_02_committed_pages_agree_with_the_renderer(tmp_path: Path) -> None:
    k = importlib.import_module("minephys.knowledge")
    out = tmp_path / "rendered"
    out.mkdir()
    k.render_pages(out)
    rendered = {p.name: p.read_bytes() for p in sorted(out.glob("*.md"))}
    committed = {p.name: p.read_bytes() for p in sorted(COMMITTED.glob("*.md"))} if COMMITTED.is_dir() else {}
    assert rendered, "the packaged knowledge renders at least one page"
    assert committed.keys() == rendered.keys(), (sorted(committed), sorted(rendered))
    differing = [n for n in rendered if committed[n].replace(b"\r\n", b"\n") != rendered[n]]
    assert differing == [], f"committed pages differ from render_pages output: {differing}"


@pytest.mark.req("SC-008-02")
@pytest.mark.oracle("hand-calculation", "the generator's --check reports 0 differences on the repository")
def test_sc_008_02_generator_check_passes_on_the_repository() -> None:
    assert GENERATOR.is_file(), "tools/gen_knowledge_docs.py is missing"
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=fx.ROOT,
        timeout=180,
    )
    assert proc.returncode == 0, (
        f"--check reported differences (exit {proc.returncode}):\n{proc.stdout[-800:]}{proc.stderr[-800:]}"
    )
