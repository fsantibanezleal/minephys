"""T-007-001 (DC-007-01): the planning entries of `knowledge/catalogue/equations.yaml` and the section 7 bibliography entries.

Expected deliverables (spec 007 sections 6 and 7):
- planning entries (domain `planning`) in `src/minephys/knowledge/catalogue/equations.yaml` (DC-008-01): block value, closure and
  its min-cut reduction, strip ratio, NPV and Lane cut-offs, each with `function` = `minephys.planning.<name>`, LaTeX, symbols with
  units, a citation key and a verification status;
- the bibliography keys of section 7 in `src/minephys/knowledge/references.bib`;
- NO `src/minephys/knowledge/planning.yaml`: the planning models have no published constants, and a knowledge table is shipped
  only with at least one row (foundation data model, spec 008 FR-008-22).

Oracle: hand-written expectations of spec 007 section 7 (sources and status). The entries whose source was not read (Lerchs and
Grossmann 1965, Lane 1964 and 1988) must be marked UNVERIFIED.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "src" / "minephys" / "knowledge"
EQUATIONS = KDIR / "catalogue" / "equations.yaml"
BIB = KDIR / "references.bib"

MODEL_FUNCTIONS = [
    "block_economic_value",
    "ultimate_pit_mincut",
    "strip_ratio",
    "npv",
    "lane_cutoff_grades",
]
UNREAD_KEYS = {"lerchs1965optimum", "lane1964choosing", "lane1988economic"}
EXPECTED_BIB: dict[str, tuple[str | None, str | None]] = {
    # key: (access class where the spec fixes it, DOI where one is printed)
    "picard1976closure": (None, "10.1287/mnsc.22.11.1268"),
    "lerchs1965optimum": ("bibliographic-only", None),
    "hochbaum2008pseudoflow": (None, "10.1287/opre.1080.0524"),
    "lane1964choosing": ("bibliographic-only", None),
    "lane1988economic": ("bibliographic-only", None),
    "cetin2013gridsearch": (None, None),
    "espinoza2013minelib": (None, "10.1007/s10479-012-1258-3"),
}


def _equations() -> list[dict[str, Any]]:
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml (the first entry of the catalogue, FR-008-22)"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    return [e for e in doc["equations"] if e.get("domain") == "planning"]


def _bib() -> dict[str, dict[str, str]]:
    assert BIB.is_file(), "missing src/minephys/knowledge/references.bib"
    out: dict[str, dict[str, str]] = {}
    for chunk in re.split(r"(?m)^@", BIB.read_text(encoding="utf-8"))[1:]:
        m = re.match(r"(\w+)\{([^,\s]+),", chunk)
        if m:
            out[m.group(2)] = {k.lower(): v.strip() for k, v in re.findall(r"(?m)^\s*(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", chunk)}
    return out


@pytest.mark.req("DC-007-01")
@pytest.mark.oracle("hand-calculation", "spec 007 section 6: block value, closure, min-cut reduction, strip ratio, NPV, Lane cut-offs")
def test_every_planning_model_has_an_equation_entry() -> None:
    entries = _equations()
    functions = {e["function"] for e in entries}
    wanted = {f"minephys.planning.{n}" for n in MODEL_FUNCTIONS}
    assert wanted <= functions, f"missing equation entries for {sorted(wanted - functions)}"
    for e in entries:
        assert e["latex"].strip() and e["symbols"], e["id"]
        assert e["verification"] in {"verified", "UNVERIFIED"}
        assert e["page"].strip()
        assert not e.get("rows"), "planning has no knowledge rows (spec 007 section 7)"


@pytest.mark.req("DC-007-01")
@pytest.mark.oracle("hand-calculation", "spec 007 section 7: unread originals stay UNVERIFIED")
def test_entries_citing_unread_sources_are_unverified() -> None:
    entries = _equations()
    assert entries, "no planning entry in the equations catalogue"
    for e in entries:
        if e["citation"] in UNREAD_KEYS:
            assert e["verification"] == "UNVERIFIED", e["id"]
            assert "verified_on" not in e
        if e["verification"] == "verified":
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e["verified_on"]))
    lane = next(e for e in entries if e["function"] == "minephys.planning.lane_cutoff_grades")
    assert lane["verification"] == "UNVERIFIED"  # derived forms, the originals were not read


@pytest.mark.req("DC-007-01")
def test_planning_ships_no_knowledge_table() -> None:
    assert (KDIR / "catalogue").is_dir(), "the knowledge package must exist before this check is meaningful"
    assert not (KDIR / "planning.yaml").exists(), "no published constants: planning.yaml must not be shipped (no empty files)"
    for path in KDIR.glob("*.yaml"):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert doc["table"] != "planning" and doc["rows"], f"{path.name}: every shipped table has at least one row"


@pytest.mark.req("DC-007-01")
def test_section7_bibliography_keys() -> None:
    bib = _bib()
    for key, (access, doi) in EXPECTED_BIB.items():
        assert key in bib, f"missing bibliography entry {key}"
        assert bib[key].get("doi") or bib[key].get("url"), f"{key}: DOI or URL required (DC-000-03)"
        if access:
            assert bib[key].get("access") == access, key
        if doi:
            assert bib[key]["doi"] == doi
    assert "saimm.co.za" in bib["cetin2013gridsearch"]["url"]


@pytest.mark.req("DC-007-01")
def test_equation_citations_resolve_in_the_bibliography() -> None:
    bib = _bib()
    for e in _equations():
        assert e["citation"] in bib, f"{e['id']}: citation {e['citation']} not in references.bib"
