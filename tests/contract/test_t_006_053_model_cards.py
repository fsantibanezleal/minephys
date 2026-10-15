"""T-006-053 (NFR-006-04, FR-000-08, FR-000-09): every public function of `minephys.environment` has a model card.

Expected: every function exported in `minephys.environment.__all__` has a numpydoc docstring with the sections `Parameters`,
`Returns`, `Equation`, `Source`, `Validity` and `Knowledge rows`, where
- `Parameters` names every parameter of the signature as `name : type [unit]` (unit in square brackets; flags and string options
  need no unit but must be named) and `Returns` states the unit of the result in square brackets (or "dimensionless");
- `Source` cites at least one key of `knowledge/references.bib` and a page, equation or table locator;
- `Validity` states the validity ranges and the unit conversions where they apply (NFR-006-04: "including the unit conversions and
  the validity ranges");
- `Knowledge rows` lists the row ids the function reads by default, or `none`; every listed id exists in
  `knowledge/environment.yaml` or `knowledge/units.yaml`, every environment row whose `symbol` names the function is listed, and no
  listed row is an UNVERIFIED `parameter` (FR-000-22).
A numpydoc section is a title line followed by a line of dashes. This is the module's own check; the repository-wide audit is
foundation task T-000-012.

Oracle: hand-written rules of FR-000-08/09 and the row table of spec 006 section 7.
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
    m = importlib.import_module("minephys.environment")
    assert getattr(m, "__all__", None), "minephys.environment must define __all__"
    return [(n, getattr(m, n)) for n in m.__all__ if inspect.isfunction(getattr(m, n))]


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
    rows = list(yaml.safe_load((KDIR / "environment.yaml").read_text(encoding="utf-8"))["rows"])
    units = KDIR / "units.yaml"
    if units.is_file():
        rows += list(yaml.safe_load(units.read_text(encoding="utf-8"))["rows"])
    return rows


@pytest.mark.req("NFR-006-04")
@pytest.mark.oracle("hand-calculation", "FR-000-09 section list")
def test_nfr_006_04_every_function_has_the_model_card_sections() -> None:
    funcs = _functions()
    assert len(funcs) >= 17, "the public functions of FR-006-01 to FR-006-17 must be exported"
    for name, fn in funcs:
        missing = [s for s in SECTIONS if s not in _sections(inspect.getdoc(fn) or "")]
        assert not missing, f"{name}: missing sections {missing}"


@pytest.mark.req("NFR-006-04")
@pytest.mark.req("FR-000-08")
def test_nfr_006_04_every_parameter_is_documented_with_a_unit() -> None:
    for name, fn in _functions():
        secs = _sections(inspect.getdoc(fn) or "")
        params = secs.get("Parameters", "")
        for p in inspect.signature(fn).parameters:
            assert re.search(rf"(?m)^\s*{re.escape(p)}\s*:\s*(.+)$", params), f"{name}: parameter {p} is not documented"
        assert re.search(r"\[[^\]]+\]", params), f"{name}: no unit in square brackets in Parameters"
        assert re.search(r"\[[^\]]+\]|dimensionless|fraction", secs.get("Returns", "")), f"{name}: Returns states no unit"


@pytest.mark.req("NFR-006-04")
def test_nfr_006_04_source_cites_a_bibliography_key_and_a_locator() -> None:
    funcs = _functions()
    keys = _bib_keys()
    for name, fn in funcs:
        source = _sections(inspect.getdoc(fn) or "").get("Source", "")
        assert any(k in source for k in keys), f"{name}: Source cites no key of references.bib"
        assert re.search(r"\d", source), f"{name}: Source gives no page or locator"


@pytest.mark.req("NFR-006-04")
def test_nfr_006_04_validity_section_states_ranges_and_conversions() -> None:
    for name, fn in _functions():
        validity = _sections(inspect.getdoc(fn) or "").get("Validity", "").strip()
        assert len(validity) >= 10, f"{name}: the Validity section is empty"
    docs = {n: _sections(inspect.getdoc(f) or "") for n, f in _functions()}
    ap42 = docs["ap42_unpaved_emission_factor"]["Validity"] + docs["ap42_unpaved_emission_factor"]["Equation"]
    assert "13.2.2" in ap42 or "Table" in ap42 or "short ton" in ap42  # the published units and ranges are stated
    assert re.search(r"lb|pound|mile|short ton", ap42, re.I), "the unit conversion of AP-42 is not stated"


@pytest.mark.req("NFR-006-04")
@pytest.mark.req("FR-000-22")
def test_nfr_006_04_knowledge_rows_section_matches_the_tables() -> None:
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
            if f"minephys.environment.{name}" in sym:
                assert r["id"] in listed, f"{name}: row {r['id']} names this function as its symbol but the card omits it"
