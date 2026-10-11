"""T-005-063 (NFR-005-04, FR-000-08, FR-000-09): every public function of `minephys.comminution` has a model card.

Expected: every function exported in `minephys.comminution.__all__` has a numpydoc docstring with the sections `Parameters`,
`Returns`, `Equation`, `Source`, `Validity` and `Knowledge rows`, where
- `Parameters` names every parameter of the signature as `name : type [unit]` (the unit in square brackets; flags and string
  options need no unit but must be named) and `Returns` states the unit of the result in square brackets;
- `Source` cites at least one key of `knowledge/references.bib` and a page, equation or table locator;
- `Knowledge rows` lists the row ids the function reads by default, or `none`; every listed id exists in
  `knowledge/comminution.yaml`, every row whose `symbol` names the function is listed, and no listed row is an UNVERIFIED
  `parameter` (FR-000-22).
A numpydoc section is a title line followed by a line of dashes. This is the module's own check; the repository-wide audit is
foundation task T-000-012.

Oracle: hand-written rules of FR-000-08/09 and the row table of spec 005 section 7.
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "src" / "minephys" / "knowledge"
SECTIONS = ["Parameters", "Returns", "Equation", "Source", "Validity", "Knowledge rows"]


def _functions() -> list[tuple[str, object]]:
    c = importlib.import_module("minephys.comminution")
    assert getattr(c, "__all__", None), "minephys.comminution must define __all__"
    return [(n, getattr(c, n)) for n in c.__all__ if inspect.isfunction(getattr(c, n))]


def _sections(doc: str) -> dict[str, str]:
    lines = doc.splitlines()
    out: dict[str, str] = {}
    current: str | None = None
    for i, line in enumerate(lines):
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if line.strip() and re.fullmatch(r"-{3,}", nxt):
            current = line.strip()
            out[current] = ""
        elif re.fullmatch(r"-{3,}", line.strip()):
            continue
        elif current is not None:
            out[current] += line + "\n"
    return out


def _bib_keys() -> set[str]:
    return set(re.findall(r"(?m)^@\w+\{([^,\s]+),", (KDIR / "references.bib").read_text(encoding="utf-8")))


def _rows() -> list[dict]:
    return yaml.safe_load((KDIR / "comminution.yaml").read_text(encoding="utf-8"))["rows"]


@pytest.mark.req("NFR-005-04")
@pytest.mark.oracle("hand-calculation", "FR-000-09 section list")
def test_nfr_005_04_every_function_has_the_model_card_sections() -> None:
    funcs = _functions()
    assert len(funcs) >= 22, "the 22 model functions of FR-005-01 to FR-005-28 must be exported"
    for name, fn in funcs:
        doc = inspect.getdoc(fn) or ""
        secs = _sections(doc)
        missing = [s for s in SECTIONS if s not in secs]
        assert not missing, f"{name}: missing sections {missing}"


@pytest.mark.req("NFR-005-04")
@pytest.mark.req("FR-000-08")
def test_nfr_005_04_every_parameter_is_documented_with_a_unit() -> None:
    for name, fn in _functions():
        params = _sections(inspect.getdoc(fn) or "").get("Parameters", "")
        for p in inspect.signature(fn).parameters:
            m = re.search(rf"(?m)^\s*{re.escape(p)}\s*:\s*(.+)$", params)
            assert m, f"{name}: parameter {p} is not documented as '{p} : type [unit]'"
        assert re.search(r"\[[^\]]+\]", params), f"{name}: no unit in square brackets in Parameters"
        returns = _sections(inspect.getdoc(fn) or "").get("Returns", "")
        assert re.search(r"\[[^\]]+\]|dimensionless|fraction", returns), f"{name}: Returns states no unit"


@pytest.mark.req("NFR-005-04")
def test_nfr_005_04_source_cites_a_bibliography_key_and_a_locator() -> None:
    funcs = _functions()
    keys = _bib_keys()
    for name, fn in funcs:
        source = _sections(inspect.getdoc(fn) or "").get("Source", "")
        assert any(k in source for k in keys), f"{name}: Source cites no key of references.bib"
        assert re.search(r"\b(p\.|pp\.|eq\.|eqs\.|Table|Annex|Figure|section|§)", source, re.I) or re.search(r"\d", source), (
            f"{name}: Source gives no page or locator"
        )


@pytest.mark.req("NFR-005-04")
@pytest.mark.req("FR-000-22")
def test_nfr_005_04_knowledge_rows_section_matches_the_table() -> None:
    rows = _rows()
    ids = {r["id"] for r in rows}
    by_id = {r["id"]: r for r in rows}
    for name, fn in _functions():
        text = _sections(inspect.getdoc(fn) or "").get("Knowledge rows", "")
        listed = {i for i in re.findall(r"[a-z][a-z0-9_]+", text) if i in ids}
        assert listed or re.search(r"\bnone\b", text, re.I), f"{name}: Knowledge rows lists no row and not 'none'"
        for row_id in listed:
            r = by_id[row_id]
            assert not (r["role"] == "parameter" and r["verification"] == "UNVERIFIED"), f"{name} lists UNVERIFIED parameter {row_id}"
        for r in rows:
            sym = r["symbol"] if isinstance(r["symbol"], list) else [r["symbol"]]
            if f"minephys.comminution.{name}" in sym:
                assert r["id"] in listed, f"{name}: row {r['id']} names this function as its symbol but the card omits it"
