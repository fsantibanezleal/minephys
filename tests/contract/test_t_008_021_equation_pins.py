"""T-008-021 (FR-008-14): every verified equation entry is pinned by a `@pytest.mark.knowledge("<equation id>")` test.

Expected: the packaged equations catalogue (`src/minephys/knowledge/catalogue/equations.yaml`) lists each equation with its
`verification`; every entry whose `verification` is `verified` is referenced by at least one test through
`@pytest.mark.knowledge("<equation id>")` (the same marker that pins verified knowledge rows, FR-000-21), and every `knowledge` marker
that names an equation id names an existing one (a stale pin is an error). The check is a repository check: it scans the test tree
with the `ast` module (decorators, `pytestmark` assignments and `pytest.param(..., marks=...)` calls with a string literal first
argument) and does not import the tests. The foundation's `tools/check_knowledge.py` (T-000-014) is extended to the same rule; its
command line is owned by that task, so this test implements the rule directly.

Oracle: the catalogue file itself and the marker inventory of the test tree (hand-written rule of spec 008 FR-008-14).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "src" / "minephys" / "knowledge" / "catalogue" / "equations.yaml"
TABLES = ROOT / "src" / "minephys" / "knowledge"


def _equations() -> list[dict]:
    assert CATALOGUE.is_file(), (
        "missing knowledge/catalogue/equations.yaml (the first catalogue entry is written by a module knowledge task)"
    )
    doc = yaml.safe_load(CATALOGUE.read_text(encoding="utf-8"))
    return list(doc["equations"])


def _row_ids() -> set[str]:
    ids: set[str] = set()
    for path in [*TABLES.glob("*.yaml"), *TABLES.glob("share-alike/*.yaml")]:
        ids |= {r["id"] for r in yaml.safe_load(path.read_text(encoding="utf-8"))["rows"]}
    return ids


def knowledge_markers() -> set[str]:
    """Every string literal passed to a `knowledge(...)` marker in the test tree."""
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


@pytest.mark.req("FR-008-14")
@pytest.mark.oracle("hand-calculation", "FR-008-14: the marker inventory covers the verified equation ids")
def test_fr_008_14_every_verified_equation_is_pinned() -> None:
    equations = _equations()
    verified = sorted(e["id"] for e in equations if e["verification"] == "verified")
    pinned = knowledge_markers()
    missing = [i for i in verified if i not in pinned]
    assert not missing, f"verified equations without a @pytest.mark.knowledge pin: {missing}"


@pytest.mark.req("FR-008-14")
@pytest.mark.oracle("hand-calculation", "a pin that names no equation and no row is stale")
def test_fr_008_14_no_marker_names_an_unknown_equation_or_row() -> None:
    equation_ids = {e["id"] for e in _equations()}
    known = equation_ids | _row_ids()
    stale = sorted(m for m in knowledge_markers() if m not in known)
    assert not stale, f"knowledge markers naming nothing that exists: {stale}"


@pytest.mark.req("FR-008-14")
def test_fr_008_14_unverified_equations_need_no_pin_and_are_flagged() -> None:
    for e in _equations():
        if e["verification"] == "UNVERIFIED":
            assert "verified_on" not in e, e["id"]
        else:
            assert e["verification"] == "verified" and e["verified_on"], e["id"]
